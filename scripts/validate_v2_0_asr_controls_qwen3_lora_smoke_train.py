#!/usr/bin/env python3
"""Validate the Qwen3-ASR-1.7B LoRA smoke-train run record."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


RUN_ID = "v2_0_asr_controls_qwen3_1_7b_lora_r16_a32_smoke_train_2026_06_01"
RUN_DIR = Path("70_experiments/runs") / RUN_ID
LOCAL_DIR = Path("70_experiments/runtime_lanes/asr_controls/lora_training") / RUN_ID
REQUIRED_FILES = [
    "README.md",
    "training_smoke_summary.json",
    "training_smoke_status.tsv",
    "controlled_artifact_manifest.tsv",
    "leakage_and_claim_boundary.tsv",
    "gate_decision.json",
]
OPTIONAL_FILES = [
    "adapter_hash_manifest.tsv",
    "post_training_gate_summary.tsv",
]
ALLOWED_DECISIONS = {
    "lora_smoke_adapter_saved",
    "lora_smoke_adapter_reload_failed",
    "lora_smoke_training_resource_blocked",
    "lora_smoke_runtime_blocked",
    "lora_smoke_one_row_consequence_passed",
    "lora_smoke_one_row_consequence_failed",
    "lora_research_probe_stop",
    "promote_to_validation_consequence_check_only",
    "runtime_dependencies_available",
    "model_loaded",
    "lora_attached",
    "minimal_train_step_completed",
}
PROHIBITED_KEYS = {
    "audio_id",
    "source_audio_id",
    "reference_text",
    "target_text",
    "hypothesis_text",
    "source_audio_path",
    "local_path",
    "reviewer",
    "review_notes",
}
PROHIBITED_FIELDS = PROHIBITED_KEYS | {"audio_path", "local_audio_path", "adapter_path"}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def walk_json(value: object, path: Path, key_path: str = "") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in PROHIBITED_KEYS:
                fail(f"tracked json contains prohibited key {key_path}.{key}: {path}")
            walk_json(child, path, f"{key_path}.{key}" if key_path else key)
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            walk_json(child, path, f"{key_path}[{idx}]")


def scan_headers() -> None:
    for filename in REQUIRED_FILES + [name for name in OPTIONAL_FILES if (RUN_DIR / name).exists()]:
        path = RUN_DIR / filename
        if path.suffix == ".json":
            walk_json(json.loads(path.read_text(encoding="utf-8")), path)
        elif path.suffix == ".tsv":
            with path.open("r", encoding="utf-8", newline="") as handle:
                header = next(csv.reader(handle, delimiter="\t"), [])
            for field in header:
                if field in PROHIBITED_FIELDS:
                    fail(f"tracked tsv contains prohibited field {field}: {path}")


def require_ignored(path: Path) -> None:
    result = subprocess.run(["git", "check-ignore", "-q", str(path)], check=False)
    if result.returncode != 0:
        fail(f"expected ignored local artifact: {path}")


def main() -> None:
    if not RUN_DIR.exists():
        fail(f"missing run dir: {RUN_DIR}")
    for filename in REQUIRED_FILES:
        if not (RUN_DIR / filename).exists():
            fail(f"missing required file: {RUN_DIR / filename}")
    if not (LOCAL_DIR / "runtime_trace.local.json").exists():
        fail("missing local runtime trace")
    require_ignored(LOCAL_DIR)
    scan_headers()

    summary = json.loads((RUN_DIR / "training_smoke_summary.json").read_text(encoding="utf-8"))
    if summary.get("run_id") != RUN_ID:
        fail("summary run_id mismatch")
    if summary.get("model_id") != "Qwen/Qwen3-ASR-1.7B":
        fail("model_id mismatch")
    if summary.get("route_id") != "qwen3_asr_1_7b_r16_a32_research_probe":
        fail("route_id mismatch")
    if summary.get("lora_rank") != 16 or summary.get("lora_alpha") != 32:
        fail("rank/alpha mismatch")
    if summary.get("training_execution_started") is not True:
        fail("training execution must have started or attempted")
    if summary.get("larger_gate_policy") != "do_not_open_30_row_258_row_or_selected_300_from_this_run":
        fail("larger gate policy mismatch")
    if summary.get("claim_boundary") != "bounded_research_probe_lora_consequence_only_not_diagnostic_proven_promotion":
        fail("claim boundary mismatch")

    decision = summary.get("decision")
    if decision not in {
        "lora_smoke_training_resource_blocked",
        "lora_smoke_runtime_blocked",
        "lora_research_probe_stop",
        "promote_to_validation_consequence_check_only",
    }:
        fail(f"unexpected summary decision: {decision}")

    status_rows = read_tsv(RUN_DIR / "training_smoke_status.tsv")
    if not status_rows:
        fail("training_smoke_status.tsv must have rows")
    for row in status_rows:
        if row["decision_label"] not in ALLOWED_DECISIONS:
            fail(f"unexpected decision label: {row['decision_label']}")

    artifacts = read_tsv(RUN_DIR / "controlled_artifact_manifest.tsv")
    if len(artifacts) < 3:
        fail("controlled artifact manifest must record manifest, adapter, and runtime trace")
    for row in artifacts:
        if row["tracked_payload"] != "false":
            fail("controlled artifacts must not be tracked payloads")

    boundaries = {row["boundary_name"]: row for row in read_tsv(RUN_DIR / "leakage_and_claim_boundary.tsv")}
    if boundaries["fixed15_overlap"]["value"] != "15":
        fail("fixed15 overlap boundary must remain 15")
    if boundaries["fixed15_overlap"]["promotion_evaluation_allowed"] != "false":
        fail("fixed15 overlap must block promotion evaluation")
    if boundaries["larger_gate_policy"]["decision"] != "larger_gates_remain_closed":
        fail("larger gates must remain closed")

    gate = json.loads((RUN_DIR / "gate_decision.json").read_text(encoding="utf-8"))
    if gate.get("promotion_claim_allowed") is not False:
        fail("promotion claim must not be allowed")
    if gate.get("larger_gates_open") is not False:
        fail("larger gates must remain closed")

    if summary.get("adapter_saved") is True:
        if not (RUN_DIR / "adapter_hash_manifest.tsv").exists():
            fail("adapter_hash_manifest.tsv required when adapter exists")
        if not (LOCAL_DIR / "adapter").exists():
            fail("local adapter directory required when adapter exists")
        require_ignored(LOCAL_DIR / "adapter")
    else:
        if summary.get("post_training_gate_run") is True:
            fail("post-training gate cannot run without adapter")

    print("OK: Qwen3-ASR-1.7B LoRA smoke-train record is valid")


if __name__ == "__main__":
    main()

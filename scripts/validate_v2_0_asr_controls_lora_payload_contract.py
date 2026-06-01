#!/usr/bin/env python3
"""Validate the ASR-control LoRA payload contract and local privacy boundary."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


RUN_ID = "v2_0_asr_controls_lora_payload_contract_2026_06_01"
RUN_DIR = Path("70_experiments/runs") / RUN_ID
LOCAL_DIR = Path("70_experiments/runtime_lanes/asr_controls/lora_training") / RUN_ID
LOCAL_FILES = [
    "qwen3_asr_1_7b_lora_train.local.jsonl",
    "qwen3_asr_1_7b_lora_validation.local.jsonl",
    "qwen3_asr_1_7b_lora_test.local.jsonl",
]
REQUIRED_TRACKED_FILES = [
    "README.md",
    "aggregate_manifest_summary.tsv",
    "split_leakage_report.tsv",
    "controlled_artifact_manifest.tsv",
    "smoke_route.tsv",
    "normalization_policy.tsv",
    "payload_contract_summary.json",
]
PROHIBITED_TRACKED_JSON_KEYS = {
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
PROHIBITED_TRACKED_TSV_FIELDS = PROHIBITED_TRACKED_JSON_KEYS | {
    "audio_path",
    "local_audio_path",
    "adapter_path",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def require_ignored(path: Path) -> None:
    result = subprocess.run(
        ["git", "check-ignore", "-q", str(path)],
        check=False,
    )
    if result.returncode != 0:
        fail(f"local transcript-bearing file is not git-ignored: {path}")


def walk_json(value: object, path: Path, key_path: str = "") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            full_key = f"{key_path}.{key}" if key_path else key
            if key in PROHIBITED_TRACKED_JSON_KEYS:
                fail(f"tracked json contains prohibited key {full_key}: {path}")
            walk_json(child, path, full_key)
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            walk_json(child, path, f"{key_path}[{idx}]")


def scan_tracked_headers() -> None:
    for filename in REQUIRED_TRACKED_FILES:
        path = RUN_DIR / filename
        if not path.exists():
            fail(f"missing tracked contract file: {path}")
        if path.suffix == ".tsv":
            with path.open("r", encoding="utf-8", newline="") as handle:
                header = next(csv.reader(handle, delimiter="\t"), [])
            for field in header:
                if field in PROHIBITED_TRACKED_TSV_FIELDS:
                    fail(f"tracked tsv contains prohibited field {field}: {path}")
        elif path.suffix == ".json":
            walk_json(json.loads(path.read_text(encoding="utf-8")), path)


def main() -> None:
    scan_tracked_headers()
    for filename in LOCAL_FILES:
        path = LOCAL_DIR / filename
        if not path.exists():
            fail(f"missing local-only manifest: {path}")
        require_ignored(path)

    summary = json.loads((RUN_DIR / "payload_contract_summary.json").read_text(encoding="utf-8"))
    expected = {
        "run_id": RUN_ID,
        "model_id": "Qwen/Qwen3-ASR-1.7B",
        "route_id": "qwen3_asr_1_7b_r16_a32_research_probe",
        "route_type": "bounded_research_probe_lora",
        "lora_rank": 16,
        "lora_alpha": 32,
        "payload_rows": 15,
        "train_rows": 9,
        "validation_rows": 3,
        "test_rows": 3,
        "fixed15_baseline_overlap_count": 15,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            fail(f"summary mismatch for {key}: expected {value!r}, got {summary.get(key)!r}")
    if summary.get("training_execution_started") is not False:
        fail("training_execution_started must be false")
    if summary.get("diagnostic_promotion_claim") is not False:
        fail("diagnostic_promotion_claim must be false")
    if summary.get("research_probe_allowed") is not True:
        fail("research_probe_allowed must be true")
    if summary.get("promotion_evaluation_allowed") is not False:
        fail("promotion_evaluation_allowed must be false")

    aggregate = read_tsv(RUN_DIR / "aggregate_manifest_summary.tsv")
    aggregate_counts = {row["split"]: int(row["row_count"]) for row in aggregate}
    if aggregate_counts != {"train": 9, "validation": 3, "test": 3, "all": 15}:
        fail(f"aggregate counts mismatch: {aggregate_counts}")
    if any(row["text_payload_policy"] != "local_only_not_tracked" for row in aggregate):
        fail("aggregate manifest must keep text payload local-only")

    leakage = {row["check_name"]: row for row in read_tsv(RUN_DIR / "split_leakage_report.tsv")}
    for check_name in ["train_validation_overlap", "train_test_overlap", "validation_test_overlap"]:
        if int(leakage[check_name]["overlap_count"]) != 0:
            fail(f"{check_name} must have zero overlap")
    if int(leakage["fixed15_baseline_overlap"]["overlap_count"]) != 15:
        fail("fixed15_baseline_overlap must record known overlap count 15")
    if leakage["fixed15_baseline_overlap"]["promotion_evaluation_allowed"] != "false":
        fail("known fixed-15 overlap must block promotion evaluation")

    route = read_tsv(RUN_DIR / "smoke_route.tsv")
    if len(route) != 1:
        fail("expected exactly one smoke route")
    route_row = route[0]
    if route_row["rank"] != "16" or route_row["alpha"] != "32":
        fail("first route must be rank=16 alpha=32")
    if route_row["route_type"] != "bounded_research_probe_lora":
        fail("route must be bounded_research_probe_lora")
    if route_row["diagnostic_promotion_claim"] != "false":
        fail("route must not claim diagnostic-proven promotion")

    print("OK: ASR-control LoRA payload contract is valid")


if __name__ == "__main__":
    main()

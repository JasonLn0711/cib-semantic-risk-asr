#!/usr/bin/env python3
"""Validate the bounded LoRA feasibility start record."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


RUN_DIR = Path("70_experiments/runs/v2_0_multimodal_bounded_lora_feasibility_start_2026_06_01")
REQUIRED_FILES = {
    "README.md",
    "bounded_lora_feasibility_start_summary.json",
    "codex_goal_prompt.md",
    "lora_pretraining_gate.tsv",
    "lora_candidate_selection.tsv",
    "controlled_artifact_manifest.tsv",
}
PROHIBITED_KEYS = {
    "audio_id",
    "row_id",
    "sample_id",
    "reference_text",
    "transcript",
    "transcript_text",
    "hypothesis",
    "hypothesis_text",
    "local_audio_path",
    "raw_audio_path",
    "reviewer_notes",
    "cache_path",
    "output_text",
    "prompt",
    "audio_path",
    "path",
    "local_path",
}


def check_json_keys(value: Any, key_path: str = "root") -> list[str]:
    violations: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in PROHIBITED_KEYS:
                violations.append(f"{key_path}.{key}")
            violations.extend(check_json_keys(child, f"{key_path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            violations.extend(check_json_keys(child, f"{key_path}[{index}]"))
    return violations


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = reader.fieldnames or []
        prohibited = sorted(set(fields) & PROHIBITED_KEYS)
        if prohibited:
            raise SystemExit(f"prohibited_tsv_fields:{path.name}:{','.join(prohibited)}")
        return list(reader)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", nargs="?", type=Path, default=RUN_DIR)
    args = parser.parse_args()

    missing = sorted(name for name in REQUIRED_FILES if not (args.run_dir / name).exists())
    if missing:
        raise SystemExit(f"missing_required_files:{','.join(missing)}")
    summary = json.loads(
        (args.run_dir / "bounded_lora_feasibility_start_summary.json").read_text(encoding="utf-8")
    )
    violations = check_json_keys(summary)
    if violations:
        raise SystemExit(f"prohibited_json_keys:{','.join(violations)}")
    if summary.get("status") != "bounded_lora_feasibility_start_recorded_training_not_started":
        raise SystemExit("unexpected_status")
    if summary.get("training_question_locked") is not True:
        raise SystemExit("training_question_must_be_locked")
    if summary.get("training_execution_started") is not False:
        raise SystemExit("training_must_not_start_before_pretraining_gates")
    if summary.get("claim_boundary") != "fine_tuning_feasibility_start_not_training_result":
        raise SystemExit("claim_boundary_missing")
    if any(summary.get("privacy", {}).values()):
        raise SystemExit("privacy_boundary_failed")

    gates = read_tsv(args.run_dir / "lora_pretraining_gate.tsv")
    if len(gates) != 6:
        raise SystemExit("lora_pretraining_gate_must_have_six_rows")
    gate_status = {row["gate_name"]: row["status"] for row in gates}
    if gate_status.get("local_private_training_payload") != "blocked":
        raise SystemExit("payload_gate_must_be_blocked")
    if gate_status.get("training_execution") != "not_started":
        raise SystemExit("training_execution_must_be_not_started")

    candidates = read_tsv(args.run_dir / "lora_candidate_selection.tsv")
    if candidates[0]["model"] != "Step-Audio-2-mini":
        raise SystemExit("step_audio_must_be_first_lora_candidate")
    artifacts = read_tsv(args.run_dir / "controlled_artifact_manifest.tsv")
    if len(artifacts) != 2:
        raise SystemExit("controlled_artifact_manifest_must_have_two_rows")
    if any(row["tracked_payload"] != "false" for row in artifacts):
        raise SystemExit("future_payloads_must_not_be_tracked")
    print(f"bounded_lora_feasibility_start_ok {args.run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

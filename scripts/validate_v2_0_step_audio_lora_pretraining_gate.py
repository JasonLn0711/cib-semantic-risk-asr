#!/usr/bin/env python3
"""Validate Step-Audio bounded LoRA pretraining gate records."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


RUN_DIR = Path("70_experiments/runs/v2_0_multimodal_step_audio_lora_pretraining_gate_2026_06_01")
REQUIRED_FILES = {
    "README.md",
    "step_lora_pretraining_gate_summary.json",
    "lora_payload_manifest.tsv",
    "adapter_evaluator_contract.tsv",
    "pretraining_gate_status.tsv",
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
    "target_text",
    "source_audio_path",
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
    summary = json.loads((args.run_dir / "step_lora_pretraining_gate_summary.json").read_text(encoding="utf-8"))
    violations = check_json_keys(summary)
    if violations:
        raise SystemExit(f"prohibited_json_keys:{','.join(violations)}")
    if summary.get("status") != "step_audio_lora_pretraining_gate_ready_not_started":
        raise SystemExit("unexpected_status")
    if summary.get("payload_rows") != 4:
        raise SystemExit("payload_rows_must_be_4")
    if summary.get("negative_no_speech_rows") != 3:
        raise SystemExit("negative_no_speech_rows_must_be_3")
    if summary.get("positive_anchor_rows") != 1:
        raise SystemExit("positive_anchor_rows_must_be_1")
    if len(summary.get("payload_sha256", "")) != 64:
        raise SystemExit("payload_sha256_required")
    if summary.get("adapter_evaluator_contract_ready") is not True:
        raise SystemExit("adapter_contract_must_be_ready")
    if summary.get("training_execution_started") is not False:
        raise SystemExit("training_must_not_start_in_pretraining_gate")
    if any(summary.get("privacy", {}).values()):
        raise SystemExit("privacy_boundary_failed")

    payload_manifest = read_tsv(args.run_dir / "lora_payload_manifest.tsv")
    if len(payload_manifest) != 1:
        raise SystemExit("payload_manifest_must_have_one_row")
    if payload_manifest[0]["tracked_payload"] != "false":
        raise SystemExit("payload_must_not_be_tracked")
    contracts = read_tsv(args.run_dir / "adapter_evaluator_contract.tsv")
    if len(contracts) != 2:
        raise SystemExit("adapter_contract_must_have_two_rows")
    if any(row["contract_status"] != "ready" for row in contracts):
        raise SystemExit("all_adapter_contracts_must_be_ready")
    gates = read_tsv(args.run_dir / "pretraining_gate_status.tsv")
    if {row["gate_name"] for row in gates} != {
        "local_private_training_payload",
        "adapter_loading_evaluator_contract",
        "training_execution",
    }:
        raise SystemExit("pretraining_gate_set_mismatch")
    if next(row for row in gates if row["gate_name"] == "training_execution")["status"] != "ready_not_started":
        raise SystemExit("training_execution_must_be_ready_not_started")
    print(f"step_audio_lora_pretraining_gate_ok {args.run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

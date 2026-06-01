#!/usr/bin/env python3
"""Validate the aggregate-only repair-first design record for v2.0 Batch 1."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


RUN_DIR = Path("70_experiments/runs/v2_0_multimodal_batch1_repair_first_design_2026_06_01")
REQUIRED_FILES = {
    "README.md",
    "repair_first_design_summary.json",
    "model_repair_plan.tsv",
    "gate_sequence.tsv",
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

    summary = json.loads((args.run_dir / "repair_first_design_summary.json").read_text(encoding="utf-8"))
    violations = check_json_keys(summary)
    if violations:
        raise SystemExit(f"prohibited_json_keys:{','.join(violations)}")
    privacy = summary.get("privacy", {})
    if any(privacy.get(key) for key in privacy):
        raise SystemExit("privacy_boundary_failed")
    if summary.get("status") != "repair_first_design_recorded":
        raise SystemExit("unexpected_status")
    if int(summary.get("primary_model_rows", 0)) != 6:
        raise SystemExit("primary_model_rows_must_be_6")

    repair_rows = read_tsv(args.run_dir / "model_repair_plan.tsv")
    if len(repair_rows) != 6:
        raise SystemExit("repair_plan_row_count_must_be_6")
    expected_lanes = {"A", "B", "C", "D", "E", "F"}
    if {row["repair_lane"] for row in repair_rows} != expected_lanes:
        raise SystemExit("repair_lane_set_mismatch")

    gate_rows = read_tsv(args.run_dir / "gate_sequence.tsv")
    if len(gate_rows) != 10:
        raise SystemExit("gate_sequence_row_count_must_be_10")
    gate_orders = [int(row["gate_order"]) for row in gate_rows]
    if gate_orders != list(range(1, 11)):
        raise SystemExit("gate_order_must_be_1_to_10")

    print(f"multimodal_batch1_repair_first_design_ok {args.run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

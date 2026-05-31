#!/usr/bin/env python3
"""Validate aggregate-only Qwen2.5-Omni fixed 15-row transcript gate."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


RUN_DIR = Path("70_experiments/runs/v2_0_multimodal_batch1_qwen_fixed_15_row_transcript_gate_2026_06_01")
REQUIRED_FILES = {
    "README.md",
    "transcript_metric_summary.tsv",
    "behavior_taxonomy_summary.tsv",
    "locale_summary.tsv",
    "gate_summary.json",
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


def check_json_keys(obj: Any, path: str = "root") -> list[str]:
    violations: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in PROHIBITED_KEYS:
                violations.append(f"{path}.{key}")
            violations.extend(check_json_keys(value, f"{path}.{key}"))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            violations.extend(check_json_keys(value, f"{path}[{index}]"))
    return violations


def read_single_row(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = reader.fieldnames or []
        prohibited_fields = sorted(set(fields) & PROHIBITED_KEYS)
        if prohibited_fields:
            raise SystemExit(f"prohibited_tsv_fields:{path.name}:{','.join(prohibited_fields)}")
        rows = list(reader)
    if len(rows) != 1:
        raise SystemExit(f"{path.name}_must_have_one_aggregate_row")
    return rows[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", nargs="?", type=Path, default=RUN_DIR)
    args = parser.parse_args()

    missing = sorted(name for name in REQUIRED_FILES if not (args.run_dir / name).exists())
    if missing:
        raise SystemExit(f"missing_required_files:{','.join(missing)}")

    metric = read_single_row(args.run_dir / "transcript_metric_summary.tsv")
    behavior = read_single_row(args.run_dir / "behavior_taxonomy_summary.tsv")
    locale = read_single_row(args.run_dir / "locale_summary.tsv")
    summary = json.loads((args.run_dir / "gate_summary.json").read_text(encoding="utf-8"))
    violations = check_json_keys(summary)
    if violations:
        raise SystemExit(f"prohibited_json_keys:{','.join(violations)}")
    privacy = summary.get("privacy", {})
    if any(privacy.get(key) for key in privacy):
        raise SystemExit("privacy_boundary_failed")
    if summary.get("model_id") != "Qwen/Qwen2.5-Omni-7B":
        raise SystemExit("unexpected_model_id")
    if int(summary.get("rows", 0)) != 15 or int(metric.get("rows", 0)) != 15:
        raise SystemExit("fixed_15_row_count_mismatch")
    if int(behavior.get("output_rows", 0)) != 15:
        raise SystemExit("behavior_output_rows_mismatch")
    if locale.get("raw_scoring_after_opencc_repair") != "false":
        raise SystemExit("raw_scoring_must_not_use_opencc_repair")
    if summary.get("promotion_decision") not in {
        "promote_to_taiwan_utility_subgroup_audit",
        "do_not_promote",
    }:
        raise SystemExit("invalid_promotion_decision")
    print(f"qwen_fixed_15_row_transcript_gate_record_ok {args.run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

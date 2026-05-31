#!/usr/bin/env python3
"""Validate aggregate-only Qwen2.5-Omni sentinel-control records."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


REQUIRED_FILES = {
    "README.md",
    "runtime_environment_summary.tsv",
    "behavior_summary.tsv",
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "run_dir",
        nargs="?",
        type=Path,
        default=Path("70_experiments/runs/v2_0_multimodal_batch1_qwen_sentinel_controls_2026_06_01"),
    )
    args = parser.parse_args()

    missing = sorted(name for name in REQUIRED_FILES if not (args.run_dir / name).exists())
    if missing:
        raise SystemExit(f"missing required files: {', '.join(missing)}")

    for name in ["runtime_environment_summary.tsv", "behavior_summary.tsv"]:
        with (args.run_dir / name).open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            fields = reader.fieldnames or []
            prohibited_fields = sorted(set(fields) & PROHIBITED_KEYS)
            if prohibited_fields:
                raise SystemExit(f"prohibited TSV fields in {name}: {', '.join(prohibited_fields)}")
            rows = list(reader)
        if name == "behavior_summary.tsv" and len(rows) < 6:
            raise SystemExit("behavior_summary.tsv must contain at least six aggregate sentinel rows")

    summary = json.loads((args.run_dir / "gate_summary.json").read_text(encoding="utf-8"))
    violations = check_json_keys(summary)
    if violations:
        raise SystemExit(f"prohibited JSON keys: {', '.join(violations)}")
    privacy = summary.get("privacy", {})
    if any(privacy.get(key) for key in privacy):
        raise SystemExit("privacy boundary is not aggregate-safe")
    if summary.get("model_id") != "Qwen/Qwen2.5-Omni-7B":
        raise SystemExit("unexpected model_id")
    if summary.get("sentinel_rows", 0) < 6:
        raise SystemExit("sentinel_rows must be at least six")
    print(f"qwen_sentinel_controls_record_ok {args.run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

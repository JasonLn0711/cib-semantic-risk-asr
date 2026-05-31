#!/usr/bin/env python3
"""Validate aggregate-only Gate A manifest preflight records."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


REQUIRED_FILES = {
    "README.md",
    "manifest_preflight_summary.tsv",
    "manifest_preflight_summary.json",
}

EXPECTED_MANIFEST_IDS = {
    "one_row_smoke",
    "sentinel_negative_control",
    "fixed_15_row_multimodal",
    "human_reviewed_30_row_cds",
    "promoted_258_row",
    "selected_300_multimodal",
}

PROHIBITED_KEYS = {
    "audio_id",
    "row_id",
    "sample_id",
    "transcript",
    "transcript_text",
    "hypothesis",
    "hypothesis_text",
    "local_audio_path",
    "raw_audio_path",
    "reviewer_notes",
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
        default=Path("70_experiments/runs/v2_0_multimodal_batch1_manifest_preflight_2026_05_31"),
    )
    args = parser.parse_args()

    missing = sorted(name for name in REQUIRED_FILES if not (args.run_dir / name).exists())
    if missing:
        raise SystemExit(f"missing required files: {', '.join(missing)}")

    with (args.run_dir / "manifest_preflight_summary.tsv").open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = reader.fieldnames or []
        prohibited_fields = sorted(set(fields) & PROHIBITED_KEYS)
        if prohibited_fields:
            raise SystemExit(f"prohibited TSV fields: {', '.join(prohibited_fields)}")
        rows = list(reader)

    ids = {row["manifest_id"] for row in rows}
    if ids != EXPECTED_MANIFEST_IDS:
        raise SystemExit(f"manifest id mismatch: {sorted(ids)}")

    for row in rows:
        if row["field_names_tracked"] != "false":
            raise SystemExit(f"field names tracked for {row['manifest_id']}")

    summary = json.loads((args.run_dir / "manifest_preflight_summary.json").read_text(encoding="utf-8"))
    violations = check_json_keys(summary)
    if violations:
        raise SystemExit(f"prohibited JSON keys: {', '.join(violations)}")
    privacy = summary.get("privacy", {})
    if any(privacy.get(key) for key in privacy):
        raise SystemExit("privacy boundary is not aggregate-safe")

    print(f"manifest_preflight_record_ok {args.run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate aggregate-only MOSS-Audio-4B sentinel repair records."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


RUN_DIR = Path("70_experiments/runs/v2_0_multimodal_batch1_moss_audio_4b_sentinel_repair_2026_06_01")
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
    summary = json.loads((args.run_dir / "gate_summary.json").read_text(encoding="utf-8"))
    violations = check_json_keys(summary)
    if violations:
        raise SystemExit(f"prohibited_json_keys:{','.join(violations)}")
    privacy = summary.get("privacy", {})
    if any(privacy.get(key) for key in privacy):
        raise SystemExit("privacy_boundary_failed")
    if summary.get("model_id") != "OpenMOSS-Team/MOSS-Audio-4B-Instruct":
        raise SystemExit("unexpected_model_id")
    if summary.get("status") not in {
        "moss_audio_4b_sentinel_repair_complete",
        "moss_audio_4b_sentinel_repair_failed",
    }:
        raise SystemExit("unexpected_status")
    behavior = read_tsv(args.run_dir / "behavior_summary.tsv")
    if summary.get("status") == "moss_audio_4b_sentinel_repair_complete" and len(behavior) != 6:
        raise SystemExit("behavior_summary_must_have_6_rows_for_complete_run")
    read_tsv(args.run_dir / "runtime_environment_summary.tsv")
    print(f"moss_audio_4b_sentinel_repair_record_ok {args.run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

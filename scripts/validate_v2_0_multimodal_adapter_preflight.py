#!/usr/bin/env python3
"""Validate aggregate-only v2.0 multimodal adapter preflight records."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


REQUIRED_FILES = {"README.md", "adapter_preflight.tsv", "adapter_preflight_summary.json"}
EXPECTED_MODELS = {
    "Qwen/Qwen2.5-Omni-7B",
    "stepfun-ai/Step-Audio-2-mini",
    "OpenMOSS-Team/MOSS-Audio-4B-Instruct",
    "openbmb/MiniCPM-o-4_5",
    "moonshotai/Kimi-Audio-7B-Instruct",
    "OpenMOSS-Team/MOSS-Audio-8B-Instruct",
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
    "cache_path",
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
        default=Path("70_experiments/runs/v2_0_multimodal_batch1_adapter_preflight_2026_05_31"),
    )
    args = parser.parse_args()

    missing = sorted(name for name in REQUIRED_FILES if not (args.run_dir / name).exists())
    if missing:
        raise SystemExit(f"missing required files: {', '.join(missing)}")

    with (args.run_dir / "adapter_preflight.tsv").open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = reader.fieldnames or []
        prohibited_fields = sorted(set(fields) & PROHIBITED_KEYS)
        if prohibited_fields:
            raise SystemExit(f"prohibited TSV fields: {', '.join(prohibited_fields)}")
        rows = list(reader)

    models = {row["model_id"] for row in rows}
    if models != EXPECTED_MODELS:
        raise SystemExit(f"model set mismatch: {sorted(models)}")
    for row in rows:
        if row["manifest_field_names_tracked"] != "false":
            raise SystemExit(f"manifest field names tracked for {row['model_id']}")
        if row["weights_downloaded_by_this_run"] != "false":
            raise SystemExit(f"weights downloaded by preflight for {row['model_id']}")
        if row["model_inference_run"] != "false":
            raise SystemExit(f"inference run during preflight for {row['model_id']}")

    summary = json.loads((args.run_dir / "adapter_preflight_summary.json").read_text(encoding="utf-8"))
    violations = check_json_keys(summary)
    if violations:
        raise SystemExit(f"prohibited JSON keys: {', '.join(violations)}")
    privacy = summary.get("privacy", {})
    if any(privacy.get(key) for key in privacy):
        raise SystemExit("privacy boundary is not aggregate-safe")
    if summary.get("model_inference_run") is not False:
        raise SystemExit("adapter preflight unexpectedly ran inference")

    print(f"adapter_preflight_record_ok {args.run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

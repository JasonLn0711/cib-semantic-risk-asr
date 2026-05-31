#!/usr/bin/env python3
"""Validate v2.0 multimodal runtime-smoke aggregate run records."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


EXPECTED_MODELS = {
    "Qwen/Qwen2.5-Omni-7B",
    "stepfun-ai/Step-Audio-2-mini",
    "OpenMOSS-Team/MOSS-Audio-4B-Instruct",
    "openbmb/MiniCPM-o-4_5",
    "moonshotai/Kimi-Audio-7B-Instruct",
    "OpenMOSS-Team/MOSS-Audio-8B-Instruct",
}

REQUIRED_FILES = {
    "runtime_environment_summary.tsv",
    "behavior_summary.tsv",
    "gate_summary.json",
    "README.md",
}

PROHIBITED_FIELDS = {
    "audio_id",
    "row_id",
    "sample_id",
    "transcript_text",
    "hypothesis_text",
    "local_audio_path",
    "raw_audio_path",
    "reviewer_notes",
}


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = reader.fieldnames or []
        rows = list(reader)
    return fieldnames, rows


def check_no_prohibited_keys(obj: Any, path: str = "root") -> list[str]:
    violations: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in PROHIBITED_FIELDS:
                violations.append(f"{path}.{key}")
            violations.extend(check_no_prohibited_keys(value, f"{path}.{key}"))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            violations.extend(check_no_prohibited_keys(value, f"{path}[{index}]"))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "run_dir",
        type=Path,
        nargs="?",
        default=Path("70_experiments/runs/v2_0_multimodal_batch1_runtime_smoke_preflight_2026_05_31"),
    )
    args = parser.parse_args()

    run_dir = args.run_dir
    missing = sorted(name for name in REQUIRED_FILES if not (run_dir / name).exists())
    if missing:
        raise SystemExit(f"missing required files: {', '.join(missing)}")

    env_fields, env_rows = read_tsv(run_dir / "runtime_environment_summary.tsv")
    behavior_fields, behavior_rows = read_tsv(run_dir / "behavior_summary.tsv")

    for name, fields in {
        "runtime_environment_summary.tsv": env_fields,
        "behavior_summary.tsv": behavior_fields,
    }.items():
        prohibited = sorted(set(fields) & PROHIBITED_FIELDS)
        if prohibited:
            raise SystemExit(f"{name} contains prohibited fields: {', '.join(prohibited)}")

    env_models = {row["model_id"] for row in env_rows}
    behavior_models = {row["model_id"] for row in behavior_rows}
    if env_models != EXPECTED_MODELS:
        raise SystemExit(f"runtime_environment_summary model set mismatch: {sorted(env_models)}")
    if behavior_models != EXPECTED_MODELS:
        raise SystemExit(f"behavior_summary model set mismatch: {sorted(behavior_models)}")

    summary = json.loads((run_dir / "gate_summary.json").read_text(encoding="utf-8"))
    violations = check_no_prohibited_keys(summary)
    if violations:
        raise SystemExit(f"gate_summary contains prohibited keys: {', '.join(violations)}")

    privacy = summary.get("privacy", {})
    if any(privacy.get(key) for key in privacy):
        raise SystemExit("privacy boundary is not aggregate-safe")

    if summary.get("status") not in {"scaffolding_ready_no_inference", "runtime_smoke_complete"}:
        raise SystemExit(f"unexpected status: {summary.get('status')}")

    print(f"runtime_smoke_record_ok {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

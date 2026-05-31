#!/usr/bin/env python3
"""Validate aggregate-only Qwen2.5-Omni runtime-lane preparation records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_FILES = {"README.md", "qwen_runtime_lane_summary.json"}
PROHIBITED_KEYS = {
    "audio_id",
    "row_id",
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
        default=Path("70_experiments/runs/v2_0_multimodal_batch1_qwen_runtime_lane_2026_05_31"),
    )
    args = parser.parse_args()

    missing = sorted(name for name in REQUIRED_FILES if not (args.run_dir / name).exists())
    if missing:
        raise SystemExit(f"missing required files: {', '.join(missing)}")
    summary = json.loads((args.run_dir / "qwen_runtime_lane_summary.json").read_text(encoding="utf-8"))
    violations = check_json_keys(summary)
    if violations:
        raise SystemExit(f"prohibited JSON keys: {', '.join(violations)}")
    privacy = summary.get("privacy", {})
    if any(privacy.get(key) for key in privacy):
        raise SystemExit("privacy boundary is not aggregate-safe")
    for key in ["repo_venv_modified_by_this_run", "package_install_run", "model_weights_downloaded_by_this_run", "model_inference_run"]:
        if summary.get(key) is not False:
            raise SystemExit(f"{key} must be false")
    if summary.get("model_id") != "Qwen/Qwen2.5-Omni-7B":
        raise SystemExit("unexpected model_id")
    print(f"qwen_runtime_lane_record_ok {args.run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

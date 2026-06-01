#!/usr/bin/env python3
"""Validate the v2.0 multimodal all-new-experiments completion plan record."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


RUN_DIR = Path("70_experiments/runs/v2_0_multimodal_all_new_experiments_completion_plan_2026_06_01")
REQUIRED_FILES = {
    "README.md",
    "completion_plan_summary.json",
    "remaining_phase_plan.tsv",
    "codex_goal_prompt.md",
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

    summary = json.loads((args.run_dir / "completion_plan_summary.json").read_text(encoding="utf-8"))
    violations = check_json_keys(summary)
    if violations:
        raise SystemExit(f"prohibited_json_keys:{','.join(violations)}")
    privacy = summary.get("privacy", {})
    if any(privacy.get(key) for key in privacy):
        raise SystemExit("privacy_boundary_failed")
    if summary.get("status") != "complete_remaining_plan_recorded":
        raise SystemExit("unexpected_status")
    if int(summary.get("total_planned_phases", 0)) != 16:
        raise SystemExit("total_planned_phases_must_be_16")

    rows = read_tsv(args.run_dir / "remaining_phase_plan.tsv")
    if len(rows) != 16:
        raise SystemExit("remaining_phase_plan_must_have_16_rows")
    orders = [int(row["phase_order"]) for row in rows]
    if orders != list(range(1, 17)):
        raise SystemExit("phase_order_must_be_1_to_16")

    prompt = (args.run_dir / "codex_goal_prompt.md").read_text(encoding="utf-8")
    required_phrases = [
        "Raw audio is never tracked in Git",
        "run Qwen2.5-Omni OpenCC",
        "run selected-300 only for stable, licensed",
        "commit logical slices separately",
    ]
    for phrase in required_phrases:
        if phrase not in prompt:
            raise SystemExit(f"missing_prompt_phrase:{phrase}")

    print(f"multimodal_all_new_experiments_completion_plan_ok {args.run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

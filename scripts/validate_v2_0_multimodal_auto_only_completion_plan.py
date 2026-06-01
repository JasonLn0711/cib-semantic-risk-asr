#!/usr/bin/env python3
"""Validate the v2.0 multimodal auto-only completion plan."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


RUN_DIR = Path("70_experiments/runs/v2_0_multimodal_auto_only_completion_plan_2026_06_01")
REQUIRED_FILES = {
    "README.md",
    "auto_only_completion_summary.json",
    "auto_only_steps.tsv",
    "codex_goal_prompt.md",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", nargs="?", type=Path, default=RUN_DIR)
    args = parser.parse_args()
    missing = sorted(name for name in REQUIRED_FILES if not (args.run_dir / name).exists())
    if missing:
        raise SystemExit(f"missing_required_files:{','.join(missing)}")
    summary = json.loads((args.run_dir / "auto_only_completion_summary.json").read_text(encoding="utf-8"))
    if summary.get("status") != "auto_only_completion_plan_recorded":
        raise SystemExit("unexpected_status")
    if summary.get("human_review_allowed") is not False:
        raise SystemExit("human_review_allowed_must_be_false")
    if any(summary.get("privacy", {}).values()):
        raise SystemExit("privacy_boundary_failed")
    with (args.run_dir / "auto_only_steps.tsv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if len(rows) != 8:
        raise SystemExit("auto_only_steps_must_have_8_rows")
    if [int(row["step_order"]) for row in rows] != list(range(1, 9)):
        raise SystemExit("step_order_must_be_1_to_8")
    prompt = (args.run_dir / "codex_goal_prompt.md").read_text(encoding="utf-8")
    for phrase in [
        "Do not implement human semantic-damage review",
        "automatic semantic-damage proxy",
        "auto_only_no_winner_stop",
        "Do not advance to larger gates",
    ]:
        if phrase not in prompt:
            raise SystemExit(f"missing_prompt_phrase:{phrase}")
    print(f"multimodal_auto_only_completion_plan_ok {args.run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

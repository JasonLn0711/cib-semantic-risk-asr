#!/usr/bin/env python3
"""Validate the v2.0 multimodal remaining completion plan."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


RUN_DIR = Path("70_experiments/runs/v2_0_multimodal_remaining_completion_plan_2026_06_01")
REQUIRED_FILES = {
    "README.md",
    "remaining_completion_summary.json",
    "remaining_steps.tsv",
    "codex_goal_prompt.md",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", nargs="?", type=Path, default=RUN_DIR)
    args = parser.parse_args()
    missing = sorted(name for name in REQUIRED_FILES if not (args.run_dir / name).exists())
    if missing:
        raise SystemExit(f"missing_required_files:{','.join(missing)}")

    summary = json.loads((args.run_dir / "remaining_completion_summary.json").read_text(encoding="utf-8"))
    if summary.get("status") != "remaining_completion_plan_recorded_after_repair_chain_closeout":
        raise SystemExit("unexpected_status")
    if any(summary.get("privacy", {}).values()):
        raise SystemExit("privacy_boundary_failed")
    if summary.get("automatic_large_gate_status") != "blocked":
        raise SystemExit("automatic_large_gate_status_must_be_blocked")

    with (args.run_dir / "remaining_steps.tsv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if len(rows) != 10:
        raise SystemExit("remaining_steps_must_have_10_rows")
    if [int(row["step_order"]) for row in rows] != list(range(1, 11)):
        raise SystemExit("step_order_must_be_1_to_10")

    prompt = (args.run_dir / "codex_goal_prompt.md").read_text(encoding="utf-8")
    for phrase in [
        "Raw audio is never tracked in Git",
        "Qwen repaired-pipeline human semantic-damage review",
        "final no-winner stop record",
        "commit logical slices separately",
    ]:
        if phrase not in prompt:
            raise SystemExit(f"missing_prompt_phrase:{phrase}")
    print(f"multimodal_remaining_completion_plan_ok {args.run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

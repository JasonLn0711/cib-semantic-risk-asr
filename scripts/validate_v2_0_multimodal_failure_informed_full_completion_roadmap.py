#!/usr/bin/env python3
"""Validate the v2.0 failure-informed full completion roadmap record."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


RUN_DIR = Path(
    "70_experiments/runs/"
    "v2_0_multimodal_failure_informed_full_completion_roadmap_2026_06_01"
)

REQUIRED_FILES = [
    "README.md",
    "failure_to_action_matrix.tsv",
    "full_completion_steps.tsv",
    "roadmap_summary.json",
    "codex_goal_prompt.md",
]

PROHIBITED_PATTERNS = [
    "\taudio_path\t",
    "\tlocal_audio_path\t",
    "\treference_text\t",
    "\thypothesis\t",
    "\tmodel_output\t",
    "\trepaired_text\t",
    "\treviewer_note\t",
    "\texpert_note\t",
    "\tcache_path\t",
    "\tadapter_path\t",
]


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if not RUN_DIR.exists():
        fail(f"missing run dir: {RUN_DIR}")

    for filename in REQUIRED_FILES:
        path = RUN_DIR / filename
        if not path.exists():
            fail(f"missing required file: {path}")

    combined = "\n".join((RUN_DIR / filename).read_text(encoding="utf-8") for filename in REQUIRED_FILES)
    lower = combined.lower()
    padded = "\n" + lower.replace("\n", "\t\n\t") + "\n"
    for pattern in PROHIBITED_PATTERNS:
        if pattern in padded:
            fail(f"prohibited pattern found: {pattern}")

    steps = read_tsv(RUN_DIR / "full_completion_steps.tsv")
    matrix = read_tsv(RUN_DIR / "failure_to_action_matrix.tsv")
    if len(steps) != 17:
        fail(f"expected 17 phases, found {len(steps)}")
    if len(matrix) < 6:
        fail(f"expected at least 6 failure-action rows, found {len(matrix)}")

    phase_ids = [int(row["phase_id"]) for row in steps]
    if phase_ids != list(range(17)):
        fail(f"phase ids are not contiguous 0..16: {phase_ids}")
    if steps[8]["status"] != "next":
        fail("phase 8 must be the next gate")
    if steps[8]["phase_name"] != "guarded_fixed_15":
        fail("phase 8 must be guarded_fixed_15")

    summary = json.loads((RUN_DIR / "roadmap_summary.json").read_text(encoding="utf-8"))
    if summary.get("human_review_policy") != "no_additional_human_review":
        fail("human review policy is not locked")
    if summary.get("current_next_gate") != "guarded_fixed_15_transcript_and_zh_tw_locale":
        fail("summary next gate mismatch")
    if summary.get("next_phase_id") != 8:
        fail("summary next_phase_id must be 8")
    if len(summary.get("guarded_fixed_15_candidates", [])) != 3:
        fail("expected exactly three guarded fixed-15 candidates")
    privacy = summary.get("privacy_boundary", {})
    forbidden_true = [
        key
        for key, value in privacy.items()
        if key != "repo_safe_aggregate_records_tracked" and value is not False
    ]
    if forbidden_true:
        fail(f"privacy boundary has forbidden true values: {forbidden_true}")
    if privacy.get("repo_safe_aggregate_records_tracked") is not True:
        fail("repo_safe_aggregate_records_tracked must be true")

    print("OK: v2.0 failure-informed full completion roadmap is valid")


if __name__ == "__main__":
    main()

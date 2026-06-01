#!/usr/bin/env python3
"""Validate the v2.0 multimodal repair-chain completion audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


RUN_DIR = Path("70_experiments/runs/v2_0_multimodal_repair_chain_completion_audit_2026_06_01")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", nargs="?", type=Path, default=RUN_DIR)
    args = parser.parse_args()
    for name in ["README.md", "completion_audit_summary.json"]:
        if not (args.run_dir / name).exists():
            raise SystemExit(f"missing_required_file:{name}")
    summary = json.loads((args.run_dir / "completion_audit_summary.json").read_text(encoding="utf-8"))
    if summary.get("status") != "automated_repair_chain_complete_no_behavior_clean_survivor":
        raise SystemExit("unexpected_status")
    if int(summary.get("completed_phases", 0)) < 9:
        raise SystemExit("completed_phases_must_cover_1_to_9")
    if summary.get("behavior_clean_repaired_sentinel_survivors") != 0:
        raise SystemExit("unexpected_behavior_clean_survivor")
    if any(summary.get("privacy", {}).values()):
        raise SystemExit("privacy_boundary_failed")
    blocked = set(summary.get("blocked_larger_phases", []))
    required = {
        "repaired_fixed_15_raw_and_locale_gate",
        "taiwan_utility_subgroup_audit",
        "human_reviewed_30_row_cds_gate",
        "promoted_258_row_split",
        "selected_300_high_stakes",
    }
    if not required.issubset(blocked):
        raise SystemExit("missing_blocked_larger_phase")
    print(f"multimodal_repair_chain_completion_audit_ok {args.run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

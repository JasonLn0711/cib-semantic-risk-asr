#!/usr/bin/env python3
"""Validate aggregate-only MOSS-Audio-8B resource repair audit."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


RUN_DIR = Path("70_experiments/runs/v2_0_multimodal_batch1_moss_audio_8b_resource_repair_2026_06_01")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", nargs="?", type=Path, default=RUN_DIR)
    args = parser.parse_args()
    for name in ["README.md", "resource_repair_summary.json", "resource_probe.tsv"]:
        if not (args.run_dir / name).exists():
            raise SystemExit(f"missing_required_file:{name}")
    summary = json.loads((args.run_dir / "resource_repair_summary.json").read_text(encoding="utf-8"))
    if summary.get("model_id") != "OpenMOSS-Team/MOSS-Audio-8B-Instruct":
        raise SystemExit("unexpected_model_id")
    if any(summary.get("privacy", {}).values()):
        raise SystemExit("privacy_boundary_failed")
    if summary.get("promotion_decision") != "blocked_runtime_resource":
        raise SystemExit("unexpected_promotion_decision")
    with (args.run_dir / "resource_probe.tsv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if len(rows) != 1:
        raise SystemExit("probe_tsv_must_have_one_row")
    print(f"moss_audio_8b_resource_repair_record_ok {args.run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

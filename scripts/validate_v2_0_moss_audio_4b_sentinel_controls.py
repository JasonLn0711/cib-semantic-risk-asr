#!/usr/bin/env python3
"""Validate aggregate-only MOSS-Audio-4B sentinel-control records."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from validate_v2_0_qwen_omni_sentinel_controls import PROHIBITED_KEYS, check_json_keys


RUN_DIR = Path("70_experiments/runs/v2_0_multimodal_batch1_moss_audio_4b_sentinel_controls_2026_06_01")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", nargs="?", type=Path, default=RUN_DIR)
    args = parser.parse_args()
    for name in ["README.md", "runtime_environment_summary.tsv", "behavior_summary.tsv", "gate_summary.json"]:
        if not (args.run_dir / name).exists():
            raise SystemExit(f"missing_required_file:{name}")
    for name in ["runtime_environment_summary.tsv", "behavior_summary.tsv"]:
        with (args.run_dir / name).open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            fields = reader.fieldnames or []
            prohibited_fields = sorted(set(fields) & PROHIBITED_KEYS)
            if prohibited_fields:
                raise SystemExit(f"prohibited_tsv_fields:{name}:{','.join(prohibited_fields)}")
            rows = list(reader)
        if name == "behavior_summary.tsv" and len(rows) < 6:
            raise SystemExit("behavior_summary_must_have_six_sentinel_rows")
    summary = json.loads((args.run_dir / "gate_summary.json").read_text(encoding="utf-8"))
    if summary.get("model_id") != "OpenMOSS-Team/MOSS-Audio-4B-Instruct":
        raise SystemExit("unexpected_model_id")
    if summary.get("sentinel_rows", 0) < 6:
        raise SystemExit("sentinel_rows_must_be_at_least_six")
    if summary.get("promotion_decision") not in {"promote_to_15_row_candidate_pool", "do_not_promote"}:
        raise SystemExit("invalid_promotion_decision")
    if check_json_keys(summary):
        raise SystemExit("prohibited_json_key_present")
    privacy = summary.get("privacy", {})
    if any(privacy.get(key) for key in privacy):
        raise SystemExit("privacy_boundary_failed")
    print(f"moss_audio_4b_sentinel_controls_record_ok {args.run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

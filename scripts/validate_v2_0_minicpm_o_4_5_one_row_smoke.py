#!/usr/bin/env python3
"""Validate aggregate-only MiniCPM-o 4.5 one-row smoke record."""

from __future__ import annotations

import csv
import json
from pathlib import Path


RUN_DIR = Path("70_experiments/runs/v2_0_multimodal_batch1_minicpm_o_4_5_one_row_smoke_2026_06_01")
REQUIRED_PRIVACY_FALSE = [
    "raw_audio_tracked",
    "row_ids_tracked",
    "transcripts_tracked",
    "hypotheses_tracked",
    "reviewer_notes_tracked",
    "local_paths_tracked",
    "transcript_bearing_runtime_logs_tracked",
    "model_cache_paths_tracked",
]


def main() -> int:
    summary_path = RUN_DIR / "gate_summary.json"
    behavior_path = RUN_DIR / "behavior_summary.tsv"
    runtime_path = RUN_DIR / "runtime_environment_summary.tsv"
    readme_path = RUN_DIR / "README.md"
    for path in [summary_path, behavior_path, runtime_path, readme_path]:
        if not path.exists():
            raise SystemExit(f"missing_required_file:{path}")

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if summary.get("model_id") != "openbmb/MiniCPM-o-4_5":
        raise SystemExit("unexpected_model_id")
    if summary.get("smoke_status") != "completed":
        raise SystemExit("minicpm_o_4_5_smoke_not_completed")
    if summary.get("quantization_policy") != "4bit_nf4_bfloat16_compute":
        raise SystemExit("missing_quantization_boundary")
    if summary.get("valid_text_outputs") != 1:
        raise SystemExit("minicpm_o_4_5_missing_valid_text_output")
    if summary.get("promotion_decision") not in {"promote_to_sentinel", "do_not_promote"}:
        raise SystemExit("invalid_promotion_decision")
    privacy = summary.get("privacy", {})
    for key in REQUIRED_PRIVACY_FALSE:
        if privacy.get(key) is not False:
            raise SystemExit(f"privacy_boundary_failed:{key}")

    with behavior_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if len(rows) != 1:
        raise SystemExit("behavior_row_count_not_one")
    row = rows[0]
    if row.get("raw_transcript_like_outputs") not in {"0", "1"}:
        raise SystemExit("invalid_raw_transcript_like_outputs")
    if row.get("quantization_policy") != "4bit_nf4_bfloat16_compute":
        raise SystemExit("behavior_missing_quantization_boundary")
    if row.get("promotion_decision") != summary.get("promotion_decision"):
        raise SystemExit("promotion_decision_mismatch")
    print(f"minicpm_o_4_5_one_row_smoke_record_ok {RUN_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

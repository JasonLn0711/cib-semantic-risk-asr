#!/usr/bin/env python3
"""Validate aggregate-only Kimi-Audio one-row smoke record."""

from __future__ import annotations

import csv
import json
from pathlib import Path


RUN_DIR = Path("70_experiments/runs/v2_0_multimodal_batch1_kimi_audio_one_row_smoke_2026_06_01")
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
    if summary.get("model_id") != "moonshotai/Kimi-Audio-7B-Instruct":
        raise SystemExit("unexpected_model_id")
    if summary.get("public_model_label") != "Kimi-Audio-7B-Instruct":
        raise SystemExit("missing_public_model_label")
    if summary.get("hf_widget_parameter_marker") != "10B params":
        raise SystemExit("missing_size_boundary_marker")
    if summary.get("smoke_status") == "completed":
        if summary.get("valid_text_outputs") != 1:
            raise SystemExit("kimi_audio_missing_valid_text_output")
        if summary.get("promotion_decision") not in {"promote_to_sentinel", "do_not_promote"}:
            raise SystemExit("invalid_completed_promotion_decision")
    elif str(summary.get("smoke_status", "")).startswith("failed:"):
        if summary.get("promotion_decision") != "blocked_runtime_dependency":
            raise SystemExit("failed_kimi_audio_gate_must_be_runtime_blocked")
        if not str(summary.get("failure_mode", "")).startswith(("runtime_dependency_error:", "resource_error:", "runtime_error:")):
            raise SystemExit("failed_kimi_audio_gate_missing_classified_failure_mode")
    else:
        raise SystemExit("invalid_smoke_status")
    privacy = summary.get("privacy", {})
    for key in REQUIRED_PRIVACY_FALSE:
        if privacy.get(key) is not False:
            raise SystemExit(f"privacy_boundary_failed:{key}")

    with behavior_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if len(rows) != 1:
        raise SystemExit("behavior_row_count_not_one")
    row = rows[0]
    if row.get("promotion_decision") != summary.get("promotion_decision"):
        raise SystemExit("promotion_decision_mismatch")
    if row.get("raw_transcript_like_outputs") not in {"0", "1"}:
        raise SystemExit("invalid_raw_transcript_like_outputs")
    print(f"kimi_audio_one_row_smoke_record_ok {RUN_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

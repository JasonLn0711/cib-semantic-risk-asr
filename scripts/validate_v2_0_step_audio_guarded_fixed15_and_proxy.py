#!/usr/bin/env python3
"""Validate Step-Audio guarded fixed-15 and semantic proxy records."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


FIXED_DIR = Path("70_experiments/runs/v2_0_multimodal_step_audio_guarded_fixed_15_2026_06_01")
PROXY_DIR = Path("70_experiments/runs/v2_0_multimodal_step_audio_guarded_auto_semantic_proxy_2026_06_01")
STOP_DIR = Path("70_experiments/runs/v2_0_multimodal_guarded_route_no_winner_stop_2026_06_01")

PROHIBITED_FIELDS = {
    "audio_path",
    "local_audio_path",
    "reference_text",
    "hypothesis",
    "hypothesis_text",
    "model_output",
    "repaired_text",
    "reviewer_note",
    "expert_note",
    "local_path",
    "cache_path",
    "adapter_path",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def assert_no_sensitive_headers(path: Path) -> None:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        header = next(reader)
    overlap = PROHIBITED_FIELDS.intersection(header)
    if overlap:
        fail(f"sensitive header(s) in {path}: {sorted(overlap)}")


def main() -> None:
    for directory in [FIXED_DIR, PROXY_DIR, STOP_DIR]:
        if not directory.exists():
            fail(f"missing directory: {directory}")

    fixed_summary = json.loads((FIXED_DIR / "gate_summary.json").read_text(encoding="utf-8"))
    if fixed_summary["rows"] != 15:
        fail("fixed-15 summary does not record 15 rows")
    if fixed_summary["guard_no_speech_rows"] + fixed_summary["pass_to_model_rows"] != 15:
        fail("guard application counts do not sum to 15")
    if fixed_summary["claim_boundary"] != "deterministic_deployment_repair_not_raw_model_capability":
        fail("fixed-15 claim boundary mismatch")
    if fixed_summary["privacy"]["raw_audio_tracked"] is not False:
        fail("fixed-15 privacy boundary broken")

    fixed_metric = read_tsv(FIXED_DIR / "transcript_metric_summary.tsv")[0]
    if fixed_metric["promotion_decision"] != "promote_to_semantic_damage_proxy":
        fail("Step fixed-15 should promote only to semantic proxy")
    if float(fixed_metric["valid_output_rate"]) < 95.0:
        fail("Step fixed-15 valid output rate below gate")

    proxy_summary = json.loads((PROXY_DIR / "auto_semantic_proxy_summary.json").read_text(encoding="utf-8"))
    if proxy_summary["rows"] != 15:
        fail("proxy summary does not record 15 rows")
    if proxy_summary["decision"] != "guarded_route_no_winner_stop":
        fail("proxy decision should stop Step guarded route")
    if proxy_summary["semantic_damage_blocker_rows"] <= 0:
        fail("proxy blocker rows must be positive for no-winner stop")

    proxy_blockers = read_tsv(PROXY_DIR / "proxy_blocker_summary.tsv")[0]
    required_blockers = [
        "cer_worsening_or_high_error_rows",
        "wer_worsening_or_high_error_rows",
        "new_hallucination_proxy_rows",
        "critical_term_or_proper_noun_change_rows",
        "abbreviation_change_rows",
        "suspicious_length_ratio_rows",
        "empty_output_change_rows",
        "locale_residual_rows",
        "payload_pairing_blocker_rows",
        "low_overlap_rows",
    ]
    for name in required_blockers:
        if name not in proxy_blockers:
            fail(f"missing proxy blocker field: {name}")

    stop_summary = json.loads((STOP_DIR / "partial_stop_summary.json").read_text(encoding="utf-8"))
    if stop_summary["final_closeout_ready"] is not False:
        fail("partial stop must not claim final closeout")
    if len(stop_summary["remaining_guarded_candidates"]) != 2:
        fail("partial stop must preserve two remaining guarded candidates")

    for directory in [FIXED_DIR, PROXY_DIR, STOP_DIR]:
        for path in directory.glob("*.tsv"):
            assert_no_sensitive_headers(path)
            rows = path.read_text(encoding="utf-8").splitlines()
            widths = {len(row.split("\t")) for row in rows if row}
            if len(widths) != 1:
                fail(f"ragged TSV: {path}")

    print("OK: Step-Audio guarded fixed-15 and semantic proxy records are valid")


if __name__ == "__main__":
    main()

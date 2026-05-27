#!/usr/bin/env python3
"""Build fixed-budget recovery frontier from human-reviewed labels.

The input audit sheet is local-only. The output is aggregate-only and reports
what happens when the top-scoring model assessments are conservatively routed
at fixed trigger budgets.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[2]
RECOVERY_DIR = REPO_ROOT / "80_semantic_risk_asr" / "recovery"
ANNOTATION_DIR = REPO_ROOT / "80_semantic_risk_asr" / "annotation"
for import_path in (RECOVERY_DIR, ANNOTATION_DIR):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

import evaluate_human_reviewed_recovery_policies as human_recovery  # noqa: E402
import evaluate_recovery_policies as recovery  # noqa: E402


DEFAULT_AUDIT_SHEET = (
    REPO_ROOT
    / "70_experiments"
    / "runs"
    / "janus_300_high_stakes_human_audit_selection_2026_05_25"
    / "artifacts"
    / "human_risk_atom_audit_sheet.tsv"
)
DEFAULT_OUTPUT = (
    REPO_ROOT
    / "70_experiments"
    / "runs"
    / "janus_300_high_stakes_recovery_human_reviewed_2026_05_26"
    / "fixed_budget_recovery_frontier.tsv"
)
DEFAULT_BUDGETS = [0.10, 0.20, 0.30, 0.40]
SCORE_METRICS = ["sres_total", "ceis"]
SENSITIVE_TOKENS = {
    "audio_id",
    "sample_id",
    "reference_text",
    "hypothesis_text",
    "asr_hypotheses_json",
    "reviewer_model_assessments_json",
    "reviewer_notes",
    "reviewer_verified_transcript",
}


def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0].keys()) if rows else [],
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def assert_safe(rows: list[dict[str, Any]]) -> None:
    text = json.dumps(rows, ensure_ascii=False)
    for token in SENSITIVE_TOKENS:
        if token in text:
            raise ValueError(f"sensitive token leaked into fixed-budget frontier: {token}")


def sample_score(sample: recovery.SampleSignals, metric: str) -> float:
    if metric == "sres_total":
        return float(sample.sres_total)
    if metric == "ceis":
        return float(sample.ceis)
    raise ValueError(f"unknown score metric: {metric}")


def eligible(sample: recovery.SampleSignals, metric: str) -> bool:
    score = sample_score(sample, metric)
    if score <= 0:
        return False
    if metric == "ceis":
        return sample.ceis_risk_atom_type in recovery.FINITE_GRAMMAR_ATOMS
    return True


def policy_rows_for_budget(
    samples: list[recovery.SampleSignals],
    *,
    metric: str,
    requested_trigger_count: int,
) -> tuple[list[dict[str, Any]], int, float | str]:
    ranked = sorted(
        enumerate(samples),
        key=lambda item: (-sample_score(item[1], metric), item[0]),
    )
    triggered_indexes: set[int] = set()
    score_cutoff: float | str = ""
    for index, sample in ranked:
        if len(triggered_indexes) >= requested_trigger_count:
            break
        if not eligible(sample, metric):
            continue
        triggered_indexes.add(index)
        score_cutoff = sample_score(sample, metric)

    rows: list[dict[str, Any]] = []
    for index, sample in enumerate(samples):
        triggered = index in triggered_indexes
        final_label = (
            recovery.conservative_high_risk_label(sample.asr_label)
            if triggered
            else sample.asr_label
        )
        rows.append(
            {
                "policy": f"{metric}_fixed_budget_conservative_replay",
                "reference_label": sample.reference_label,
                "asr_label": sample.asr_label,
                "final_label": final_label,
                "triggered": triggered,
                "machine_abstained": False,
                "recovery_action": "fixed_budget_conservative_escalation"
                if triggered
                else "none",
                "asr_run_id": sample.asr_run_id,
            }
        )
    return rows, len(triggered_indexes), score_cutoff


def build_frontier(samples: list[recovery.SampleSignals], budgets: list[float]) -> list[dict[str, Any]]:
    baseline_rows = [
        {
            "policy": "no_recovery",
            "reference_label": sample.reference_label,
            "asr_label": sample.asr_label,
            "final_label": sample.asr_label,
            "triggered": False,
            "machine_abstained": False,
            "recovery_action": "none",
            "asr_run_id": sample.asr_run_id,
        }
        for sample in samples
    ]
    baseline = recovery.summarize_policy(baseline_rows)
    baseline_severe = int(baseline["high_risk_missed_count"]) + int(
        baseline["critical_miss_count"]
    )

    output_rows: list[dict[str, Any]] = []
    for metric in SCORE_METRICS:
        eligible_count = sum(1 for sample in samples if eligible(sample, metric))
        for budget in budgets:
            requested = round(len(samples) * budget)
            replay_rows, triggered_count, cutoff = policy_rows_for_budget(
                samples,
                metric=metric,
                requested_trigger_count=requested,
            )
            summary = recovery.summarize_policy(replay_rows, baseline)
            severe_remaining = int(summary["high_risk_missed_count"]) + int(
                summary["critical_miss_count"]
            )
            severe_eliminated = baseline_severe - severe_remaining
            output_rows.append(
                {
                    "score_metric": metric,
                    "budget_target_rate": f"{budget:.4f}",
                    "model_assessments": len(samples),
                    "eligible_trigger_count": eligible_count,
                    "requested_trigger_count": requested,
                    "triggered_count": triggered_count,
                    "observed_budget_rate": f"{triggered_count / len(samples):.4f}"
                    if samples
                    else "0.0000",
                    "score_cutoff": cutoff,
                    "unsafe_downrouting_count": summary["unsafe_downrouting_count"],
                    "high_risk_missed_count": summary["high_risk_missed_count"],
                    "critical_miss_count": summary["critical_miss_count"],
                    "severe_missed_count": severe_remaining,
                    "severe_misses_eliminated_vs_no_recovery": severe_eliminated,
                    "non_severe_trigger_count": max(triggered_count - severe_eliminated, 0),
                    "triggers_per_severe_miss_eliminated": round(
                        triggered_count / severe_eliminated,
                        4,
                    )
                    if severe_eliminated
                    else "n/a",
                    "threshold_type": "fixed_budget_ranked_replay",
                    "replay_mode": "aggregate_human_reviewed_conservative_replay",
                    "privacy_boundary": "aggregate counts only",
                }
            )
    assert_safe(output_rows)
    return output_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-sheet", type=Path, default=DEFAULT_AUDIT_SHEET)
    parser.add_argument("--output-tsv", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--budgets",
        default=",".join(str(value) for value in DEFAULT_BUDGETS),
        help="Comma-separated fixed trigger budget rates.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    budgets = [float(value.strip()) for value in args.budgets.split(",") if value.strip()]
    _fieldnames, rows = human_recovery.read_tsv(args.audit_sheet)
    samples, metadata = human_recovery.build_samples(rows)
    frontier = build_frontier(samples, budgets)
    write_tsv(args.output_tsv, frontier)
    print(
        {
            "ok": True,
            "reviewed_rows": metadata.get("reviewed_row_count", 0),
            "sample_count": len(samples),
            "output_tsv": str(args.output_tsv),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

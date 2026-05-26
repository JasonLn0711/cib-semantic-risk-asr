#!/usr/bin/env python3
"""Row-clustered uncertainty for human-reviewed recovery policy replay."""

from __future__ import annotations

import argparse
import csv
import random
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


DEFAULT_AUDIT_SHEET = (
    REPO_ROOT
    / "70_experiments"
    / "runs"
    / "janus_300_high_stakes_human_audit_selection_2026_05_25"
    / "artifacts"
    / "human_risk_atom_audit_sheet.tsv"
)
DEFAULT_OUTPUT_DIR = (
    REPO_ROOT
    / "70_experiments"
    / "runs"
    / "janus_300_high_stakes_recovery_human_reviewed_2026_05_26"
)
POLICIES = [
    "no_recovery",
    "confidence_only_trigger",
    "sres_triggered_recovery",
    "ceis_triggered_conservative_action",
    "ceis_ensemble_arbitration",
]
STAT_FIELDS = [
    "unsafe_downrouting_count",
    "unsafe_downrouting_rate",
    "high_risk_missed_count",
    "critical_miss_count",
    "severe_missed_count",
    "triggered_count",
    "recovery_budget_rate",
    "machine_abstention_count",
    "exact_recovered_error_count",
]
SENSITIVE_FIELDS = {
    "audio_id",
    "sample_id",
    "reference_text",
    "hypothesis_text",
    "asr_hypotheses_json",
    "reviewer_model_assessments_json",
    "reviewer_notes",
    "reviewer_verified_transcript",
}


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def assert_safe_rows(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        for field in SENSITIVE_FIELDS:
            if field in row:
                raise ValueError(f"sensitive field leaked into aggregate output: {field}")


def clustered_samples(audit_rows: list[dict[str, str]]) -> dict[int, list[Any]]:
    clusters: dict[int, list[Any]] = {}
    for cluster_index, audit_row in enumerate(audit_rows, start=1):
        samples, _metadata = human_recovery.build_samples([audit_row])
        clusters[cluster_index] = samples
    return clusters


def summarize(samples: list[Any], args: argparse.Namespace) -> dict[str, dict[str, Any]]:
    summaries, _details = human_recovery.evaluate_samples(
        samples,
        confidence_threshold=args.confidence_threshold,
        sres_threshold=args.sres_threshold,
        ceis_threshold=args.ceis_threshold,
        ensemble_mode=args.ensemble_mode,
    )
    for summary in summaries.values():
        summary["severe_missed_count"] = int(summary.get("high_risk_missed_count", 0)) + int(
            summary.get("critical_miss_count", 0)
        )
    return summaries


def bootstrap_ci(
    clusters: dict[int, list[Any]],
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    rng = random.Random(args.seed)
    cluster_ids = sorted(clusters)
    all_samples = [sample for cluster_id in cluster_ids for sample in clusters[cluster_id]]
    point = summarize(all_samples, args)
    distributions: dict[str, dict[str, list[float]]] = {
        policy: {field: [] for field in STAT_FIELDS} for policy in POLICIES
    }

    for _ in range(args.iterations):
        sampled = []
        for sampled_id in (rng.choice(cluster_ids) for _ in cluster_ids):
            sampled.extend(clusters[sampled_id])
        summaries = summarize(sampled, args)
        for policy in POLICIES:
            summary = summaries.get(policy, {})
            for field in STAT_FIELDS:
                distributions[policy][field].append(float(summary.get(field, 0)))

    rows: list[dict[str, Any]] = []
    for policy in POLICIES:
        result: dict[str, Any] = {
            "policy": policy,
            "cluster_unit": "audio_row",
            "cluster_count": len(cluster_ids),
            "model_assessments": point[policy].get("rows", 0),
            "bootstrap_iterations": args.iterations,
            "confidence_threshold": args.confidence_threshold,
            "sres_threshold": args.sres_threshold,
            "ceis_threshold": args.ceis_threshold,
            "ensemble_mode": args.ensemble_mode,
        }
        for field in STAT_FIELDS:
            values = distributions[policy][field]
            result[f"point_{field}"] = point[policy].get(field, "")
            result[f"{field}_median"] = round(quantile(values, 0.5), 4)
            result[f"{field}_ci_low"] = round(quantile(values, 0.025), 4)
            result[f"{field}_ci_high"] = round(quantile(values, 0.975), 4)
        rows.append(result)
    assert_safe_rows(rows)
    return rows


def leave_one_row_out(clusters: dict[int, list[Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    cluster_ids = sorted(clusters)
    rows: list[dict[str, Any]] = []
    for omitted_id in cluster_ids:
        samples = [
            sample
            for cluster_id in cluster_ids
            if cluster_id != omitted_id
            for sample in clusters[cluster_id]
        ]
        summaries = summarize(samples, args)
        for policy in POLICIES:
            summary = summaries[policy]
            rows.append(
                {
                    "omitted_review_row_index": omitted_id,
                    "remaining_clusters": len(cluster_ids) - 1,
                    "policy": policy,
                    "model_assessments": summary.get("rows", 0),
                    "unsafe_downrouting_count": summary.get("unsafe_downrouting_count", 0),
                    "high_risk_missed_count": summary.get("high_risk_missed_count", 0),
                    "critical_miss_count": summary.get("critical_miss_count", 0),
                    "severe_missed_count": summary.get("severe_missed_count", 0),
                    "triggered_count": summary.get("triggered_count", 0),
                    "recovery_budget_rate": summary.get("recovery_budget_rate", 0),
                    "machine_abstention_count": summary.get("machine_abstention_count", 0),
                    "exact_recovered_error_count": summary.get("exact_recovered_error_count", 0),
                }
            )
    assert_safe_rows(rows)
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-sheet", type=Path, default=DEFAULT_AUDIT_SHEET)
    parser.add_argument(
        "--output-ci-tsv",
        type=Path,
        default=DEFAULT_OUTPUT_DIR / "policy_comparison_clustered_ci.tsv",
    )
    parser.add_argument(
        "--output-loo-tsv",
        type=Path,
        default=DEFAULT_OUTPUT_DIR / "policy_comparison_leave_one_row_out.tsv",
    )
    parser.add_argument("--iterations", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20260526)
    parser.add_argument("--confidence-threshold", type=float, default=0.70)
    parser.add_argument("--sres-threshold", type=float, default=20.0)
    parser.add_argument("--ceis-threshold", type=float, default=5.0)
    parser.add_argument("--ensemble-mode", choices=("priority", "max"), default="priority")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    _fieldnames, audit_rows = human_recovery.read_tsv(args.audit_sheet)
    clusters = clustered_samples(audit_rows)
    ci_rows = bootstrap_ci(clusters, args)
    loo_rows = leave_one_row_out(clusters, args)
    write_tsv(args.output_ci_tsv, ci_rows, list(ci_rows[0].keys()) if ci_rows else [])
    write_tsv(args.output_loo_tsv, loo_rows, list(loo_rows[0].keys()) if loo_rows else [])
    print(
        {
            "ok": True,
            "cluster_count": len(clusters),
            "bootstrap_iterations": args.iterations,
            "output_ci_tsv": str(args.output_ci_tsv),
            "output_loo_tsv": str(args.output_loo_tsv),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

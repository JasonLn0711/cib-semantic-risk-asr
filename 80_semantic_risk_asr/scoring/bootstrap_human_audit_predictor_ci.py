#!/usr/bin/env python3
"""Row-clustered uncertainty for human-audit predictor metrics.

The input audit sheet is local-only and may contain transcripts. Outputs are
aggregate-only and must not contain audio IDs, sample IDs, transcript text,
hypotheses, or reviewer notes.
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[2]
ANNOTATION_DIR = REPO_ROOT / "80_semantic_risk_asr" / "annotation"
if str(ANNOTATION_DIR) not in sys.path:
    sys.path.insert(0, str(ANNOTATION_DIR))

import analyze_human_audit_predictors as predictors  # noqa: E402


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
    / "janus_300_high_stakes_human_audit_selection_2026_05_25"
)
STAT_FIELDS = [
    "auc",
    "best_threshold",
    "best_f1",
    "precision",
    "recall",
    "true_positive",
    "false_positive",
    "false_negative",
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


def numeric(value: Any) -> float | None:
    if value == "" or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def assert_safe_rows(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        for field in SENSITIVE_FIELDS:
            if field in row:
                raise ValueError(f"sensitive field leaked into aggregate output: {field}")


def clustered_model_rows(audit_rows: list[dict[str, str]]) -> dict[int, list[dict[str, Any]]]:
    clusters: dict[int, list[dict[str, Any]]] = {}
    for cluster_index, audit_row in enumerate(audit_rows, start=1):
        model_rows, _counters = predictors.extract_model_rows([audit_row])
        for model_row in model_rows:
            model_row["_cluster_index"] = cluster_index
        clusters[cluster_index] = model_rows
    return clusters


def overall_rows(model_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in predictors.predictor_rows(model_rows)
        if row["scope"] == "overall" and row["asr_run_id"] == "ALL"
    ]


def row_key(row: dict[str, Any]) -> tuple[str, str]:
    return str(row["target"]), str(row["metric"])


def bootstrap_ci(
    clusters: dict[int, list[dict[str, Any]]],
    *,
    iterations: int,
    seed: int,
) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    cluster_ids = sorted(clusters)
    all_model_rows = [model_row for cluster_id in cluster_ids for model_row in clusters[cluster_id]]
    points = {row_key(row): row for row in overall_rows(all_model_rows)}
    distributions: dict[tuple[str, str], dict[str, list[float]]] = {
        key: {field: [] for field in STAT_FIELDS} for key in points
    }

    for _ in range(iterations):
        sampled_rows: list[dict[str, Any]] = []
        for sampled_id in (rng.choice(cluster_ids) for _ in cluster_ids):
            sampled_rows.extend(clusters[sampled_id])
        for row in overall_rows(sampled_rows):
            key = row_key(row)
            if key not in distributions:
                continue
            for field in STAT_FIELDS:
                value = numeric(row.get(field))
                if value is not None:
                    distributions[key][field].append(value)

    output_rows: list[dict[str, Any]] = []
    for key, point in sorted(points.items()):
        target, metric = key
        labels = [
            int(row[target])
            for row in all_model_rows
            if row.get("reviewed")
        ]
        result: dict[str, Any] = {
            "scope": "overall",
            "target": target,
            "metric": metric,
            "cluster_unit": "audio_row",
            "cluster_count": len(cluster_ids),
            "reviewed_model_assessments": point["reviewed_model_samples"],
            "positive_model_assessments": sum(labels),
            "threshold_type": "retrospective_best_threshold_on_scoped_audit_set",
            "bootstrap_iterations": iterations,
        }
        for field in STAT_FIELDS:
            values = distributions[key][field]
            result[f"point_{field}"] = point.get(field, "")
            result[f"{field}_median"] = round(quantile(values, 0.5), 4)
            result[f"{field}_ci_low"] = round(quantile(values, 0.025), 4)
            result[f"{field}_ci_high"] = round(quantile(values, 0.975), 4)
            result[f"{field}_valid_iterations"] = len(values)
        output_rows.append(result)
    assert_safe_rows(output_rows)
    return output_rows


def leave_one_row_out(clusters: dict[int, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    cluster_ids = sorted(clusters)
    output_rows: list[dict[str, Any]] = []
    for omitted_id in cluster_ids:
        rows = [
            model_row
            for cluster_id in cluster_ids
            if cluster_id != omitted_id
            for model_row in clusters[cluster_id]
        ]
        for row in overall_rows(rows):
            output_rows.append(
                {
                    "omitted_review_row_index": omitted_id,
                    "remaining_clusters": len(cluster_ids) - 1,
                    "scope": "overall",
                    "target": row["target"],
                    "metric": row["metric"],
                    "reviewed_model_assessments": row["reviewed_model_samples"],
                    "positive_model_assessments": row["positive_rows"],
                    "auc": row["auc"],
                    "best_threshold": row["best_threshold"],
                    "best_f1": row["best_f1"],
                    "precision": row["precision"],
                    "recall": row["recall"],
                    "true_positive": row["true_positive"],
                    "false_positive": row["false_positive"],
                    "false_negative": row["false_negative"],
                }
            )
    assert_safe_rows(output_rows)
    return output_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-sheet", type=Path, default=DEFAULT_AUDIT_SHEET)
    parser.add_argument(
        "--output-ci-tsv",
        type=Path,
        default=DEFAULT_OUTPUT_DIR / "human_audit_predictor_clustered_ci.tsv",
    )
    parser.add_argument(
        "--output-loo-tsv",
        type=Path,
        default=DEFAULT_OUTPUT_DIR / "human_audit_predictor_leave_one_row_out.tsv",
    )
    parser.add_argument("--iterations", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20260526)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    audit_rows = predictors.read_tsv(args.audit_sheet)
    clusters = clustered_model_rows(audit_rows)
    ci_rows = bootstrap_ci(clusters, iterations=args.iterations, seed=args.seed)
    loo_rows = leave_one_row_out(clusters)
    ci_fields = list(ci_rows[0].keys()) if ci_rows else []
    loo_fields = list(loo_rows[0].keys()) if loo_rows else []
    write_tsv(args.output_ci_tsv, ci_rows, ci_fields)
    write_tsv(args.output_loo_tsv, loo_rows, loo_fields)
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

#!/usr/bin/env python3
"""Analyze metric predictors against human-reviewed audit labels.

Input audit sheets are local-only and may contain transcripts. Outputs are
aggregate-only and safe to track.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PREDICTOR_FIELDS = ["wer", "cer", "sres_total", "ceis_max"]
TARGET_FIELDS = ["human_decision_change_yes", "human_decision_change_yes_or_uncertain"]
VALID_DECISION_CHANGE = {"yes", "no", "uncertain"}
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


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def as_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_json_field(value: str) -> Any:
    if not value.strip():
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def assessment_reviewed(item: dict[str, Any]) -> bool:
    return all(
        str(item.get(field, "")).strip()
        for field in [
            "reviewer_would_asr_error_change_decision",
            "reviewer_critical_atoms",
            "reviewer_expected_safe_action",
            "reviewer_annotation_confidence",
        ]
    )


def auc_roc(scores: list[float], labels: list[int]) -> float | None:
    positives = [score for score, label in zip(scores, labels) if label == 1]
    negatives = [score for score, label in zip(scores, labels) if label == 0]
    if not positives or not negatives:
        return None
    wins = 0.0
    comparisons = 0
    for positive in positives:
        for negative in negatives:
            comparisons += 1
            if positive > negative:
                wins += 1.0
            elif positive == negative:
                wins += 0.5
    return round(wins / comparisons, 4)


def threshold_metrics(scores: list[float], labels: list[int]) -> dict[str, Any]:
    if not scores:
        return {
            "best_threshold": "",
            "best_f1": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "true_positive": 0,
            "false_positive": 0,
            "false_negative": 0,
        }

    best = {
        "best_threshold": sorted(set(scores))[0],
        "best_f1": -1.0,
        "precision": 0.0,
        "recall": 0.0,
        "true_positive": 0,
        "false_positive": 0,
        "false_negative": 0,
    }
    for threshold in sorted(set(scores)):
        true_positive = false_positive = false_negative = 0
        for score, label in zip(scores, labels):
            predicted = score >= threshold
            actual = label == 1
            if predicted and actual:
                true_positive += 1
            elif predicted and not actual:
                false_positive += 1
            elif not predicted and actual:
                false_negative += 1
        precision = (
            true_positive / (true_positive + false_positive)
            if true_positive + false_positive
            else 0.0
        )
        recall = (
            true_positive / (true_positive + false_negative)
            if true_positive + false_negative
            else 0.0
        )
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )
        better = f1 > best["best_f1"]
        if f1 == best["best_f1"]:
            better = recall > best["recall"] or (
                recall == best["recall"] and threshold < best["best_threshold"]
            )
        if better:
            best = {
                "best_threshold": round(threshold, 4),
                "best_f1": round(f1, 4),
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "true_positive": true_positive,
                "false_positive": false_positive,
                "false_negative": false_negative,
            }
    return best


def extract_model_rows(audit_rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], Counter[str]]:
    result: list[dict[str, Any]] = []
    counters: Counter[str] = Counter()
    for row in audit_rows:
        hypotheses = parse_json_field(row.get("asr_hypotheses_json", ""))
        assessments = parse_json_field(row.get("reviewer_model_assessments_json", ""))
        if not isinstance(hypotheses, list):
            counters["invalid_asr_hypotheses_json"] += 1
            continue
        if not isinstance(assessments, list):
            counters["missing_or_invalid_reviewer_model_assessments_json"] += 1
            assessments = []

        assessment_by_run = {
            str(item.get("asr_run_id", "")): item
            for item in assessments
            if isinstance(item, dict) and item.get("asr_run_id")
        }
        for hypothesis in hypotheses:
            if not isinstance(hypothesis, dict):
                counters["invalid_hypothesis_item"] += 1
                continue
            run_id = str(hypothesis.get("asr_run_id", "") or "unknown")
            assessment = assessment_by_run.get(run_id, {})
            decision_change = str(
                assessment.get("reviewer_would_asr_error_change_decision", "")
            ).strip()
            if decision_change and decision_change not in VALID_DECISION_CHANGE:
                counters["invalid_decision_change_value"] += 1
            reviewed = assessment_reviewed(assessment)
            if reviewed:
                counters["reviewed_model_assessments"] += 1
            else:
                counters["pending_model_assessments"] += 1
            result.append(
                {
                    "asr_run_id": run_id,
                    "wer": as_float(hypothesis.get("wer")),
                    "cer": as_float(hypothesis.get("cer")),
                    "sres_total": as_float(hypothesis.get("sres_total")),
                    "ceis_max": as_float(hypothesis.get("ceis_max")),
                    "reviewed": reviewed,
                    "decision_change": decision_change,
                    "human_decision_change_yes": int(reviewed and decision_change == "yes"),
                    "human_decision_change_yes_or_uncertain": int(
                        reviewed and decision_change in {"yes", "uncertain"}
                    ),
                    "uncertain": int(reviewed and decision_change == "uncertain"),
                }
            )
    counters["model_assessments"] = len(result)
    return result, counters


def predictor_rows(model_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reviewed_rows = [row for row in model_rows if row["reviewed"]]
    scopes: list[tuple[str, str, list[dict[str, Any]]]] = [("overall", "ALL", reviewed_rows)]
    by_run: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in reviewed_rows:
        by_run[str(row["asr_run_id"])].append(row)
    scopes.extend(("asr_run", run, rows) for run, rows in sorted(by_run.items()))

    rows: list[dict[str, Any]] = []
    for scope, asr_run_id, scoped_rows in scopes:
        for target in TARGET_FIELDS:
            labels = [int(row[target]) for row in scoped_rows]
            positives = sum(labels)
            for metric in PREDICTOR_FIELDS:
                scores = [float(row.get(metric, 0.0)) for row in scoped_rows]
                auc = auc_roc(scores, labels)
                rows.append(
                    {
                        "scope": scope,
                        "asr_run_id": asr_run_id,
                        "target": target,
                        "metric": metric,
                        "reviewed_model_samples": len(scoped_rows),
                        "positive_rows": positives,
                        "positive_rate": round(positives / len(scoped_rows), 4)
                        if scoped_rows
                        else 0.0,
                        "auc": "" if auc is None else auc,
                        **threshold_metrics(scores, labels),
                    }
                )
    return rows


def model_summary_rows(model_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in model_rows:
        grouped[str(row["asr_run_id"])].append(row)
    result = []
    for run_id, rows in sorted(grouped.items()):
        reviewed_rows = [row for row in rows if row["reviewed"]]
        result.append(
            {
                "asr_run_id": run_id,
                "model_assessments": len(rows),
                "reviewed_model_assessments": len(reviewed_rows),
                "pending_model_assessments": len(rows) - len(reviewed_rows),
                "human_decision_change_yes_count": sum(
                    int(row["human_decision_change_yes"]) for row in reviewed_rows
                ),
                "human_decision_change_yes_or_uncertain_count": sum(
                    int(row["human_decision_change_yes_or_uncertain"])
                    for row in reviewed_rows
                ),
                "human_uncertain_count": sum(int(row["uncertain"]) for row in reviewed_rows),
            }
        )
    return result


def assert_aggregate_safe(payload: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    for field in SENSITIVE_FIELDS:
        if field in text:
            raise ValueError(f"sensitive field name leaked into predictor summary: {field}")
    for row in rows:
        for field in SENSITIVE_FIELDS:
            if field in row:
                raise ValueError(f"sensitive field present in aggregate row: {field}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-sheet", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started = time.time()
    audit_rows = read_tsv(args.audit_sheet)
    model_rows, counters = extract_model_rows(audit_rows)
    comparison = predictor_rows(model_rows)
    model_summary = model_summary_rows(model_rows)
    status = "review_complete" if counters["pending_model_assessments"] == 0 else "review_pending"
    if counters["reviewed_model_assessments"] and counters["pending_model_assessments"]:
        status = "partial_review"
    if counters["invalid_decision_change_value"]:
        status = "review_needs_cleanup"

    payload = {
        "ok": True,
        "status": status,
        "input_boundary": "local transcript-bearing audit sheet; do not commit input",
        "output_boundary": "aggregate-only; no audio IDs, sample IDs, transcripts, hypotheses, or reviewer notes",
        "audit_rows": len(audit_rows),
        "model_assessments": counters["model_assessments"],
        "reviewed_model_assessments": counters["reviewed_model_assessments"],
        "pending_model_assessments": counters["pending_model_assessments"],
        "warning_counts": {
            key: value
            for key, value in sorted(counters.items())
            if key
            not in {
                "model_assessments",
                "reviewed_model_assessments",
                "pending_model_assessments",
            }
            and value
        },
        "notes": [
            "Predictor metrics are computed only over reviewed model-level assessments.",
            "Uncertain decisions are excluded from the yes-only target and included in the yes-or-uncertain target.",
        ],
        "wall_time_seconds": round(time.time() - started, 4),
    }
    assert_aggregate_safe(payload, comparison + model_summary)
    write_json(args.output_dir / "human_audit_predictor_summary.json", payload)
    write_tsv(
        args.output_dir / "human_audit_predictor_comparison.tsv",
        comparison,
        [
            "scope",
            "asr_run_id",
            "target",
            "metric",
            "reviewed_model_samples",
            "positive_rows",
            "positive_rate",
            "auc",
            "best_threshold",
            "best_f1",
            "precision",
            "recall",
            "true_positive",
            "false_positive",
            "false_negative",
        ],
    )
    write_tsv(
        args.output_dir / "human_audit_predictor_model_summary.tsv",
        model_summary,
        [
            "asr_run_id",
            "model_assessments",
            "reviewed_model_assessments",
            "pending_model_assessments",
            "human_decision_change_yes_count",
            "human_decision_change_yes_or_uncertain_count",
            "human_uncertain_count",
        ],
    )
    print(
        json.dumps(
            {
                "ok": True,
                "status": status,
                "model_assessments": counters["model_assessments"],
                "reviewed_model_assessments": counters["reviewed_model_assessments"],
                "pending_model_assessments": counters["pending_model_assessments"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

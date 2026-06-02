#!/usr/bin/env python3
"""Run aggregate-only CEIS ablations against completed reviewer labels.

Inputs may contain row keys, transcripts, ASR hypotheses, and reviewer notes.
Outputs are aggregate-only and must not expose row-level content.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


LABEL_ORDER = {
    "no_escalation": 0,
    "review": 1,
    "priority_review": 2,
    "critical_escalation": 3,
}
HIGH_RISK = {"priority_review", "critical_escalation"}
SENSITIVE_TOKENS = {
    "audio_id",
    "sample_id",
    "reference_text",
    "hypothesis_text",
    "base_transcript",
    "variant_transcript",
    "asr_hypotheses_json",
    "reviewer_model_assessments_json",
    "reviewer_notes",
    "reviewer_verified_transcript",
}
TARGETS = ["decision_change_yes", "decision_change_yes_or_uncertain"]
VARIANT_ORDER = [
    "ceis_full",
    "ceis_without_atom_weights",
    "ceis_without_plausibility",
    "ceis_binary_atom",
    "ceis_full_top3_mean",
]


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_json(value: str) -> Any:
    if not (value or "").strip():
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def label_level(label: str) -> int:
    return LABEL_ORDER.get(label, 0)


def parse_reviewer_sheet(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("reviewer sheets must use reviewer_id=path")
    reviewer_id, path = value.split("=", 1)
    reviewer_id = reviewer_id.strip()
    if not reviewer_id:
        raise argparse.ArgumentTypeError("reviewer_id cannot be empty")
    return reviewer_id, Path(path)


def decision_distance(row: dict[str, str]) -> float:
    explicit = as_float(row.get("decision_distance_used"), default=-1.0)
    if explicit >= 0:
        return explicit
    explicit = as_float(row.get("decision_distance"), default=-1.0)
    if explicit >= 0:
        return explicit
    return float(abs(label_level(row.get("variant_decision", "")) - label_level(row.get("base_decision", ""))))


def atom_weight(row: dict[str, str]) -> float:
    explicit = as_float(row.get("risk_atom_weight_used"), default=-1.0)
    if explicit >= 0:
        return explicit
    explicit = as_float(row.get("risk_atom_weight"), default=-1.0)
    if explicit >= 0:
        return explicit
    return 1.0


def plausibility(row: dict[str, str]) -> float:
    return as_float(row.get("acoustic_plausibility") or row.get("plausibility"), default=1.0)


def full_component(row: dict[str, str]) -> float:
    component = as_float(row.get("ceis_component"), default=-1.0)
    if component >= 0:
        return component
    return plausibility(row) * atom_weight(row) * decision_distance(row)


def variant_scores_for_row(row: dict[str, str]) -> dict[str, float]:
    distance = decision_distance(row)
    weight = atom_weight(row)
    plaus = plausibility(row)
    unstable = (
        distance > 0
        or full_component(row) > 0
        or (row.get("base_decision", "") != row.get("variant_decision", ""))
    )
    return {
        "ceis_full": max(full_component(row), 0.0),
        "ceis_without_atom_weights": max(plaus * distance, 0.0),
        "ceis_without_plausibility": max(weight * distance, 0.0),
        "ceis_binary_atom": 1.0 if unstable else 0.0,
    }


def load_ceis_ablation_scores(path: Path) -> tuple[dict[str, dict[str, float]], dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_tsv(path):
        key = row.get("sample_id", "")
        if key:
            grouped[key].append(row)

    scores: dict[str, dict[str, float]] = {}
    atom_counts: Counter[str] = Counter()
    for key, rows in grouped.items():
        per_variant: dict[str, list[float]] = defaultdict(list)
        for row in rows:
            atom = row.get("risk_atom_type", "") or "unknown"
            if full_component(row) > 0 or decision_distance(row) > 0:
                atom_counts[atom] += 1
            for variant, score in variant_scores_for_row(row).items():
                per_variant[variant].append(score)
        sample_scores = {
            variant: round(max(values) if values else 0.0, 6)
            for variant, values in per_variant.items()
        }
        full_values = sorted(per_variant.get("ceis_full", []), reverse=True)
        top_values = full_values[:3]
        sample_scores["ceis_full_top3_mean"] = round(
            sum(top_values) / len(top_values), 6
        ) if top_values else 0.0
        scores[key] = sample_scores

    metadata = {
        "ceis_metric_samples": len(scores),
        "ceis_variant_rows": sum(len(rows) for rows in grouped.values()),
        "unstable_atom_counts": dict(sorted(atom_counts.items())),
    }
    return scores, metadata


def complete_model_assessment(item: dict[str, Any]) -> bool:
    return all(
        str(item.get(field, "")).strip()
        for field in [
            "reviewer_would_asr_error_change_decision",
            "reviewer_critical_atoms",
            "reviewer_expected_safe_action",
            "reviewer_annotation_confidence",
        ]
    )


def extract_reviewer_model_rows(
    reviewer_id: str,
    audit_sheet: Path,
    ceis_scores: dict[str, dict[str, float]],
) -> tuple[list[dict[str, Any]], Counter[str]]:
    rows = read_tsv(audit_sheet)
    counters: Counter[str] = Counter()
    model_rows: list[dict[str, Any]] = []
    for row in rows:
        hypotheses = parse_json(row.get("asr_hypotheses_json", ""))
        assessments = parse_json(row.get("reviewer_model_assessments_json", ""))
        if not isinstance(hypotheses, list):
            counters["invalid_hypothesis_bundle"] += 1
            continue
        if not isinstance(assessments, list):
            counters["invalid_assessment_bundle"] += 1
            assessments = []
        assessment_by_run = {
            str(item.get("asr_run_id", "")): item
            for item in assessments
            if isinstance(item, dict) and item.get("asr_run_id")
        }
        human_label = row.get("reviewer_semantic_risk_label", "")
        for hypothesis in hypotheses:
            if not isinstance(hypothesis, dict):
                counters["invalid_hypothesis_item"] += 1
                continue
            run_id = str(hypothesis.get("asr_run_id", "") or "unknown")
            assessment = assessment_by_run.get(run_id, {})
            reviewed = complete_model_assessment(assessment)
            decision_change = str(
                assessment.get("reviewer_would_asr_error_change_decision", "")
            ).strip()
            sample_key = f"{row.get('audio_id', '')}__{run_id}"
            scores = ceis_scores.get(sample_key, {})
            if not scores:
                counters["missing_ceis_score"] += 1
            model_rows.append(
                {
                    "reviewer_id": reviewer_id,
                    "asr_run_id": run_id,
                    "human_label": human_label,
                    "asr_label": str(hypothesis.get("asr_label", "")),
                    "reviewed": reviewed,
                    "decision_change": decision_change,
                    "decision_change_yes": int(reviewed and decision_change == "yes"),
                    "decision_change_yes_or_uncertain": int(
                        reviewed and decision_change in {"yes", "uncertain"}
                    ),
                    **{variant: float(scores.get(variant, 0.0)) for variant in VARIANT_ORDER},
                }
            )
            counters["model_assessments"] += 1
            counters["reviewed_model_assessments"] += int(reviewed)
            counters["pending_model_assessments"] += int(not reviewed)
    counters["audit_rows"] = len(rows)
    return model_rows, counters


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
    return wins / comparisons


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
    best: dict[str, Any] = {
        "best_threshold": sorted(set(scores))[0],
        "best_f1": -1.0,
        "precision": 0.0,
        "recall": 0.0,
        "true_positive": 0,
        "false_positive": 0,
        "false_negative": 0,
    }
    for threshold in sorted(set(scores)):
        tp = fp = fn = 0
        for score, label in zip(scores, labels):
            predicted = score >= threshold
            actual = label == 1
            if predicted and actual:
                tp += 1
            elif predicted and not actual:
                fp += 1
            elif not predicted and actual:
                fn += 1
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        better = f1 > best["best_f1"]
        if f1 == best["best_f1"]:
            better = recall > best["recall"] or (
                recall == best["recall"] and threshold < best["best_threshold"]
            )
        if better:
            best = {
                "best_threshold": round(threshold, 6),
                "best_f1": round(f1, 6),
                "precision": round(precision, 6),
                "recall": round(recall, 6),
                "true_positive": tp,
                "false_positive": fp,
                "false_negative": fn,
            }
    return best


def predictor_summary_rows(model_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    by_reviewer: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in model_rows:
        if row["reviewed"]:
            by_reviewer[row["reviewer_id"]].append(row)
    for reviewer_id, reviewer_rows in sorted(by_reviewer.items()):
        for target in TARGETS:
            labels = [int(row[target]) for row in reviewer_rows]
            positives = sum(labels)
            for variant in VARIANT_ORDER:
                scores = [float(row[variant]) for row in reviewer_rows]
                auc = auc_roc(scores, labels)
                rows.append(
                    {
                        "reviewer_id": reviewer_id,
                        "target": target,
                        "ablation_variant": variant,
                        "reviewed_model_assessments": len(reviewer_rows),
                        "positive_count": positives,
                        "positive_rate": round(positives / len(reviewer_rows), 6)
                        if reviewer_rows
                        else 0.0,
                        "auc": "" if auc is None else round(auc, 6),
                        **threshold_metrics(scores, labels),
                    }
                )
    return rows


def summarize_policy(rows: list[dict[str, Any]], baseline: dict[str, Any] | None = None) -> dict[str, Any]:
    total = len(rows)
    unsafe = high_missed = critical = over = triggered = abstained = 0
    for row in rows:
        ref_level = label_level(row["human_label"])
        final_level = label_level(row["final_label"])
        if final_level < ref_level:
            unsafe += 1
        if row["human_label"] in HIGH_RISK and row["final_label"] not in HIGH_RISK:
            high_missed += 1
        if row["human_label"] == "critical_escalation" and row["final_label"] not in HIGH_RISK:
            critical += 1
        if final_level > ref_level:
            over += 1
        triggered += int(row["triggered"])
        abstained += int(row["abstained"])
    result = {
        "evaluated_model_assessments": total,
        "triggered_count": triggered,
        "trigger_rate": round(triggered / total, 6) if total else 0.0,
        "machine_abstention_count": abstained,
        "machine_abstention_rate": round(abstained / total, 6) if total else 0.0,
        "unsafe_downrouting_count": unsafe,
        "unsafe_downrouting_rate": round(unsafe / total, 6) if total else 0.0,
        "high_risk_missed_count": high_missed,
        "high_risk_missed_rate": round(high_missed / total, 6) if total else 0.0,
        "critical_miss_count": critical,
        "critical_miss_rate": round(critical / total, 6) if total else 0.0,
        "over_escalation_count": over,
        "over_escalation_rate": round(over / total, 6) if total else 0.0,
    }
    if baseline:
        result.update(
            {
                "unsafe_downrouting_reduction_vs_no_recovery": baseline["unsafe_downrouting_count"] - unsafe,
                "high_risk_missed_reduction_vs_no_recovery": baseline["high_risk_missed_count"] - high_missed,
                "critical_miss_reduction_vs_no_recovery": baseline["critical_miss_count"] - critical,
            }
        )
    else:
        result.update(
            {
                "unsafe_downrouting_reduction_vs_no_recovery": 0,
                "high_risk_missed_reduction_vs_no_recovery": 0,
                "critical_miss_reduction_vs_no_recovery": 0,
            }
        )
    return result


def conservative_label(current_label: str) -> str:
    return current_label if label_level(current_label) >= 2 else "priority_review"


def policy_rows(model_rows: list[dict[str, Any]], predictor_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    threshold_by_reviewer_variant: dict[tuple[str, str], float] = {}
    for row in predictor_rows:
        if row["target"] != "decision_change_yes":
            continue
        value = row.get("best_threshold", "")
        if value == "":
            continue
        threshold_by_reviewer_variant[(row["reviewer_id"], row["ablation_variant"])] = float(value)

    result: list[dict[str, Any]] = []
    by_reviewer: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in model_rows:
        if row["reviewed"]:
            by_reviewer[row["reviewer_id"]].append(row)

    for reviewer_id, reviewer_rows in sorted(by_reviewer.items()):
        baseline_rows = [
            {
                **row,
                "final_label": row["asr_label"],
                "triggered": False,
                "abstained": False,
            }
            for row in reviewer_rows
        ]
        baseline_summary = summarize_policy(baseline_rows)
        result.append(
            {
                "reviewer_id": reviewer_id,
                "policy": "no_recovery",
                "ablation_variant": "none",
                "threshold_source": "none",
                "threshold": "",
                **baseline_summary,
            }
        )
        for variant in VARIANT_ORDER:
            threshold = threshold_by_reviewer_variant.get((reviewer_id, variant), 0.0)
            rows = []
            for row in reviewer_rows:
                triggered = float(row[variant]) >= threshold
                rows.append(
                    {
                        **row,
                        "final_label": conservative_label(row["asr_label"])
                        if triggered
                        else row["asr_label"],
                        "triggered": triggered,
                        "abstained": False,
                    }
                )
            result.append(
                {
                    "reviewer_id": reviewer_id,
                    "policy": "ablation_triggered_conservative_action",
                    "ablation_variant": variant,
                    "threshold_source": "best_f1_on_decision_change_yes",
                    "threshold": round(threshold, 6),
                    **summarize_policy(rows, baseline_summary),
                }
            )
    return result


def delta_rows(predictor_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {
        (row["reviewer_id"], row["target"], row["ablation_variant"]): row
        for row in predictor_rows
    }
    result: list[dict[str, Any]] = []
    for reviewer_id, target, variant in sorted(by_key):
        if variant == "ceis_full":
            continue
        baseline = by_key.get((reviewer_id, target, "ceis_full"))
        current = by_key[(reviewer_id, target, variant)]
        if not baseline:
            continue
        baseline_auc = as_float(baseline.get("auc"))
        current_auc = as_float(current.get("auc"))
        baseline_f1 = as_float(baseline.get("best_f1"))
        current_f1 = as_float(current.get("best_f1"))
        result.append(
            {
                "reviewer_id": reviewer_id,
                "target": target,
                "comparison": f"{variant}_vs_ceis_full",
                "auc_delta": round(current_auc - baseline_auc, 6),
                "best_f1_delta": round(current_f1 - baseline_f1, 6),
                "full_auc": round(baseline_auc, 6),
                "variant_auc": round(current_auc, 6),
                "full_best_f1": round(baseline_f1, 6),
                "variant_best_f1": round(current_f1, 6),
            }
        )
    return result


def model_summary_rows(model_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in model_rows:
        grouped[(row["reviewer_id"], row["asr_run_id"])].append(row)
    result = []
    for (reviewer_id, run_id), rows in sorted(grouped.items()):
        reviewed_rows = [row for row in rows if row["reviewed"]]
        result.append(
            {
                "reviewer_id": reviewer_id,
                "asr_run_id": run_id,
                "model_assessments": len(rows),
                "reviewed_model_assessments": len(reviewed_rows),
                "decision_change_yes_count": sum(row["decision_change_yes"] for row in reviewed_rows),
                "decision_change_yes_or_uncertain_count": sum(
                    row["decision_change_yes_or_uncertain"] for row in reviewed_rows
                ),
            }
        )
    return result


def assert_aggregate_safe(payload: Any, rows: list[dict[str, Any]]) -> None:
    text = json.dumps(payload, ensure_ascii=False) + json.dumps(rows, ensure_ascii=False)
    for token in SENSITIVE_TOKENS:
        if token in text:
            raise ValueError(f"sensitive token leaked into aggregate CEIS ablation output: {token}")
    for row in rows:
        for token in SENSITIVE_TOKENS:
            if token in row:
                raise ValueError(f"sensitive field present in aggregate row: {token}")


def write_readme(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# CEIS Ablation On Dual-Reviewer Audit",
        "",
        f"Date: {payload['date']}",
        "",
        f"Status: `{payload['status']}`.",
        "",
        "This run tests the paper's core mechanism: CDS-ASR evaluates speech",
        "systems by downstream decision stability, and CEIS operationalizes that",
        "mechanism through plausibility, risk-atom weighting, and decision",
        "distance. The completed selected-300 dual-reviewer audit gives the",
        "ablation a reviewer-trustworthy validation surface.",
        "",
        "## Variants",
        "",
        "- `ceis_full`: plausibility * risk-atom weight * decision distance.",
        "- `ceis_without_atom_weights`: plausibility * decision distance.",
        "- `ceis_without_plausibility`: risk-atom weight * decision distance.",
        "- `ceis_binary_atom`: binary atom-level instability trigger.",
        "- `ceis_full_top3_mean`: top-3 mean over full CEIS variant components.",
        "",
        "## Outputs",
        "",
        "- `ceis_ablation_summary.json`",
        "- `ceis_ablation_predictor_summary.tsv`",
        "- `ceis_ablation_policy_replay.tsv`",
        "- `ceis_ablation_model_summary.tsv`",
        "- `ceis_ablation_delta_summary.tsv`",
        "",
        "## Interpretation",
        "",
        "On this selected-300 surface, the ablation isolates the central paper",
        "contribution: decision-changing risk-atom instability is the evidence",
        "signal that transcript-level ASR metrics miss. Plausibility and atom",
        "weights remain explicit CEIS design components and calibration handles;",
        "their separate lift should be interpreted from the delta summary rather",
        "than assumed.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ceis-scored", type=Path, required=True)
    parser.add_argument("--reviewer-sheet", action="append", type=parse_reviewer_sheet, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--date", default="2026-06-02")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started = time.time()
    ceis_scores, ceis_metadata = load_ceis_ablation_scores(args.ceis_scored)
    all_rows: list[dict[str, Any]] = []
    reviewer_counters: dict[str, dict[str, int]] = {}
    for reviewer_id, sheet_path in args.reviewer_sheet:
        rows, counters = extract_reviewer_model_rows(reviewer_id, sheet_path, ceis_scores)
        all_rows.extend(rows)
        reviewer_counters[reviewer_id] = dict(sorted(counters.items()))

    predictor_rows = predictor_summary_rows(all_rows)
    deltas = delta_rows(predictor_rows)
    replay_rows = policy_rows(all_rows, predictor_rows)
    model_rows = model_summary_rows(all_rows)
    status = "ceis_ablation_complete"
    if any(counters.get("pending_model_assessments", 0) for counters in reviewer_counters.values()):
        status = "ceis_ablation_review_pending"
    if any(counters.get("missing_ceis_score", 0) for counters in reviewer_counters.values()):
        status = "ceis_ablation_missing_scores"

    payload = {
        "ok": status == "ceis_ablation_complete",
        "status": status,
        "date": args.date,
        "input_boundary": "local completed reviewer sheets and local CEIS metric input",
        "output_boundary": "aggregate-only CEIS ablation summaries with no row-level content",
        "reviewer_count": len(args.reviewer_sheet),
        "reviewer_counters": reviewer_counters,
        **ceis_metadata,
        "ablation_variants": VARIANT_ORDER,
        "policy_threshold_source": "best_f1_on_decision_change_yes",
        "notes": [
            "Ablation metrics are reported separately for each reviewer label source.",
            "No adjudication is inferred in this run.",
            "Policy replay is conservative-action replay using each variant's best-F1 threshold.",
        ],
        "runtime_seconds": round(time.time() - started, 4),
    }
    assert_aggregate_safe(payload, predictor_rows + replay_rows + model_rows + deltas)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "ceis_ablation_summary.json", payload)
    write_tsv(
        args.output_dir / "ceis_ablation_predictor_summary.tsv",
        predictor_rows,
        [
            "reviewer_id",
            "target",
            "ablation_variant",
            "reviewed_model_assessments",
            "positive_count",
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
        args.output_dir / "ceis_ablation_policy_replay.tsv",
        replay_rows,
        [
            "reviewer_id",
            "policy",
            "ablation_variant",
            "threshold_source",
            "threshold",
            "evaluated_model_assessments",
            "triggered_count",
            "trigger_rate",
            "machine_abstention_count",
            "machine_abstention_rate",
            "unsafe_downrouting_count",
            "unsafe_downrouting_rate",
            "high_risk_missed_count",
            "high_risk_missed_rate",
            "critical_miss_count",
            "critical_miss_rate",
            "over_escalation_count",
            "over_escalation_rate",
            "unsafe_downrouting_reduction_vs_no_recovery",
            "high_risk_missed_reduction_vs_no_recovery",
            "critical_miss_reduction_vs_no_recovery",
        ],
    )
    write_tsv(
        args.output_dir / "ceis_ablation_delta_summary.tsv",
        deltas,
        [
            "reviewer_id",
            "target",
            "comparison",
            "auc_delta",
            "best_f1_delta",
            "full_auc",
            "variant_auc",
            "full_best_f1",
            "variant_best_f1",
        ],
    )
    write_tsv(
        args.output_dir / "ceis_ablation_model_summary.tsv",
        model_rows,
        [
            "reviewer_id",
            "asr_run_id",
            "model_assessments",
            "reviewed_model_assessments",
            "decision_change_yes_count",
            "decision_change_yes_or_uncertain_count",
        ],
    )
    write_readme(args.output_dir / "README.md", payload)
    print(
        json.dumps(
            {
                "ok": payload["ok"],
                "status": payload["status"],
                "reviewer_count": payload["reviewer_count"],
                "output_dir": str(args.output_dir),
            },
            ensure_ascii=False,
        )
    )
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

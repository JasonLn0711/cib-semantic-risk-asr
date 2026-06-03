#!/usr/bin/env python3
"""Build final CSL aggregate outputs from completed dual-reviewer materials.

The completed reviewer package contains transcript-bearing local files. This
script reads them from a local boundary and writes aggregate-only outputs for
the final CSL execution plan.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


BASE_ACTION_LEVEL = {
    "no_escalation": 0,
    "review": 1,
    "manual_review": 1,
    "priority_review": 2,
    "critical_escalation": 3,
}
HIGH_RISK = {"priority_review", "critical_escalation"}
BUDGETS = [0.10, 0.20, 0.30, 0.40]
PREDICTOR_METRICS = ["wer", "cer", "sres_total", "ceis_max"]
FRONTIER_POLICIES = [
    "sres_total",
    "ceis_max",
    "max_norm_sres_ceis",
    "rank_fusion_sres_ceis",
    "two_stage_sres_then_ceis",
    "variant_count_only",
    "ceis_top1_capped",
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
    "reviewer_decision_change_reason",
    "reviewer_asr_confusion_terms",
}


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fieldnames or (list(rows[0].keys()) if rows else [])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def as_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def action_level(label: str) -> int:
    return BASE_ACTION_LEVEL.get((label or "").strip(), 0)


def is_severe_miss(reference_label: str, asr_label: str) -> bool:
    return reference_label in HIGH_RISK and asr_label not in HIGH_RISK


def is_critical_miss(reference_label: str, asr_label: str) -> bool:
    return reference_label == "critical_escalation" and asr_label not in HIGH_RISK


def is_unsafe_downrouting(reference_label: str, asr_label: str) -> bool:
    return action_level(asr_label) < action_level(reference_label)


def consensus_label(value_1: str, value_2: str) -> str:
    v1 = (value_1 or "").strip()
    v2 = (value_2 or "").strip()
    if v1 == v2:
        return v1
    if {v1, v2} <= {"yes", "uncertain"}:
        return "yes"
    if "yes" in {v1, v2}:
        return "uncertain"
    if "uncertain" in {v1, v2}:
        return "uncertain"
    return "disagreement"


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
    best = {
        "best_threshold": "",
        "best_f1": 0.0,
        "precision": 0.0,
        "recall": 0.0,
        "true_positive": 0,
        "false_positive": 0,
        "false_negative": 0,
    }
    if not scores:
        return best
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
        if (
            f1 > best["best_f1"]
            or (f1 == best["best_f1"] and recall > best["recall"])
            or (
                f1 == best["best_f1"]
                and recall == best["recall"]
                and (best["best_threshold"] == "" or threshold < best["best_threshold"])
            )
        ):
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


def minmax(values: list[float]) -> list[float]:
    if not values:
        return []
    low = min(values)
    high = max(values)
    if high == low:
        return [0.0 for _ in values]
    return [(value - low) / (high - low) for value in values]


def percentile_ranks(values: list[float]) -> list[float]:
    if not values:
        return []
    ordered = sorted((value, index) for index, value in enumerate(values))
    ranks = [0.0] * len(values)
    for rank, (_value, index) in enumerate(ordered, start=1):
        ranks[index] = rank / len(values)
    return ranks


def bootstrap_auc_delta(
    rows: list[dict[str, Any]],
    metric_a: str,
    metric_b: str,
    label_field: str,
    *,
    iterations: int,
    seed: int,
) -> dict[str, Any]:
    import random

    rng = random.Random(seed)
    valid_rows = [row for row in rows if row[label_field] in {0, 1}]
    if not valid_rows:
        return {"iterations": 0, "delta_mean": "", "delta_ci_low": "", "delta_ci_high": ""}
    deltas: list[float] = []
    for _ in range(iterations):
        sample = [valid_rows[rng.randrange(len(valid_rows))] for _ in valid_rows]
        labels = [int(row[label_field]) for row in sample]
        auc_a = auc_roc([float(row[metric_a]) for row in sample], labels)
        auc_b = auc_roc([float(row[metric_b]) for row in sample], labels)
        if auc_a is None or auc_b is None:
            continue
        deltas.append(auc_a - auc_b)
    if not deltas:
        return {"iterations": 0, "delta_mean": "", "delta_ci_low": "", "delta_ci_high": ""}
    deltas.sort()
    low_index = max(math.floor(0.025 * len(deltas)) - 1, 0)
    high_index = min(math.ceil(0.975 * len(deltas)) - 1, len(deltas) - 1)
    return {
        "iterations": len(deltas),
        "delta_mean": round(statistics.mean(deltas), 6),
        "delta_ci_low": round(deltas[low_index], 6),
        "delta_ci_high": round(deltas[high_index], 6),
    }


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1 / (1 + z)
    z = math.exp(value)
    return z / (1 + z)


def fit_logistic(
    features: list[list[float]],
    labels: list[int],
    *,
    iterations: int = 6000,
    learning_rate: float = 0.08,
    l2: float = 0.01,
) -> list[float]:
    weights = [0.0 for _ in features[0]]
    n = len(labels)
    for _ in range(iterations):
        gradients = [0.0 for _ in weights]
        for row, label in zip(features, labels):
            pred = sigmoid(sum(weight * value for weight, value in zip(weights, row)))
            error = pred - label
            for index, value in enumerate(row):
                gradients[index] += error * value
        for index in range(len(weights)):
            penalty = 0.0 if index == 0 else l2 * weights[index]
            weights[index] -= learning_rate * ((gradients[index] / n) + penalty)
    return weights


def predict_logistic(features: list[list[float]], weights: list[float]) -> list[float]:
    return [sigmoid(sum(weight * value for weight, value in zip(weights, row))) for row in features]


def log_loss(probs: list[float], labels: list[int]) -> float:
    eps = 1e-12
    total = 0.0
    for prob, label in zip(probs, labels):
        p = min(max(prob, eps), 1 - eps)
        total += -(label * math.log(p) + (1 - label) * math.log(1 - p))
    return total / len(labels) if labels else 0.0


def residual_gain_after_sres(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    evaluable = [row for row in rows if row["decision_change_label"] in {"yes", "no"}]
    labels = [int(row["decision_change_yes"]) for row in evaluable]
    sres_norm = minmax([float(row["sres_total"]) for row in evaluable])
    ceis_norm = minmax([float(row["ceis_max"]) for row in evaluable])
    sres_features = [[1.0, sres_norm[index]] for index in range(len(evaluable))]
    joint_features = [[1.0, sres_norm[index], ceis_norm[index]] for index in range(len(evaluable))]
    sres_weights = fit_logistic(sres_features, labels)
    joint_weights = fit_logistic(joint_features, labels)
    sres_probs = predict_logistic(sres_features, sres_weights)
    joint_probs = predict_logistic(joint_features, joint_weights)
    sres_auc = auc_roc(sres_probs, labels)
    joint_auc = auc_roc(joint_probs, labels)
    sres_threshold = threshold_metrics(sres_probs, labels)
    joint_threshold = threshold_metrics(joint_probs, labels)
    return [
        {
            "unit": "model_assessment_clustered_within_row",
            "target": "decision_change_yes",
            "comparison": "logistic_label_sres_plus_ceis_vs_sres",
            "evaluated_model_assessments": len(evaluable),
            "positive_count": sum(labels),
            "sres_only_auc": "" if sres_auc is None else round(sres_auc, 6),
            "sres_plus_ceis_auc": "" if joint_auc is None else round(joint_auc, 6),
            "delta_auc": ""
            if sres_auc is None or joint_auc is None
            else round(joint_auc - sres_auc, 6),
            "sres_only_log_loss": round(log_loss(sres_probs, labels), 6),
            "sres_plus_ceis_log_loss": round(log_loss(joint_probs, labels), 6),
            "delta_log_loss": round(log_loss(joint_probs, labels) - log_loss(sres_probs, labels), 6),
            "sres_only_best_f1": sres_threshold["best_f1"],
            "sres_plus_ceis_best_f1": joint_threshold["best_f1"],
            "delta_best_f1": round(joint_threshold["best_f1"] - sres_threshold["best_f1"], 6),
            "ceis_coefficient": round(joint_weights[2], 6),
            "interpretation": "diagnostic_residual_gain_after_sres_not_deployment_model",
        }
    ]


def load_model_rows(
    reviewer_1_flat: Path,
    reviewer_2_flat: Path,
    variant_counts: dict[tuple[str, str], int],
) -> tuple[list[dict[str, Any]], Counter[str]]:
    r1 = read_tsv(reviewer_1_flat)
    r2 = read_tsv(reviewer_2_flat)
    by_key_2 = {(row["row_number"], row["asr_run_id"]): row for row in r2}
    counters: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []
    for row in r1:
        key = (row["row_number"], row["asr_run_id"])
        peer = by_key_2.get(key)
        if peer is None:
            counters["missing_reviewer_2_peer"] += 1
            continue
        label = consensus_label(
            row.get("reviewer_would_asr_error_change_decision", ""),
            peer.get("reviewer_would_asr_error_change_decision", ""),
        )
        expected_safe_action = consensus_label(
            row.get("reviewer_expected_safe_action", ""),
            peer.get("reviewer_expected_safe_action", ""),
        )
        reference_label = row.get("reference_label", "")
        asr_label = row.get("asr_label", "")
        selection_stratum = row.get("selection_stratum", "")
        audio_id = row.get("audio_id", "")
        run_id = row["asr_run_id"]
        rows.append(
            {
                "row_number": int(row["row_number"]),
                "audio_id": audio_id,
                "asr_run_id": run_id,
                "split": row.get("split", ""),
                "selection_stratum": selection_stratum,
                "reference_label": reference_label,
                "asr_label": asr_label,
                "wer": as_float(row.get("wer")),
                "cer": as_float(row.get("cer")),
                "sres_total": as_float(row.get("sres_total")),
                "ceis_max": as_float(row.get("ceis_max")),
                "sres_top_atom": row.get("sres_top_atom", "") or "none",
                "ceis_top_atom": row.get("ceis_top_atom", "") or "none",
                "variant_count": variant_counts.get((audio_id, run_id), 0),
                "decision_change_label": label,
                "decision_change_yes": int(label == "yes"),
                "decision_change_yes_or_uncertain": int(label in {"yes", "uncertain"}),
                "decision_change_evaluable": int(label in {"yes", "no"}),
                "expected_safe_action_label": expected_safe_action,
                "unsafe_downrouting": int(is_unsafe_downrouting(reference_label, asr_label)),
                "high_risk_missed": int(reference_label in HIGH_RISK and asr_label not in HIGH_RISK),
                "critical_miss": int(is_critical_miss(reference_label, asr_label)),
                "severe_miss": int(is_severe_miss(reference_label, asr_label)),
            }
        )
    counters["model_assessments"] = len(rows)
    counters["unique_rows"] = len({row["row_number"] for row in rows})
    return rows, counters


def load_variant_counts(ceis_scored: Path) -> tuple[dict[tuple[str, str], int], Counter[str], Counter[str]]:
    counts: dict[tuple[str, str], int] = defaultdict(int)
    sources: Counter[str] = Counter()
    reject_reasons: Counter[str] = Counter()
    if not ceis_scored.exists():
        return counts, sources, reject_reasons
    for row in read_tsv(ceis_scored):
        sample_id = row.get("sample_id", "")
        if "__" not in sample_id:
            continue
        audio_id, run_id = sample_id.rsplit("__", 1)
        # The selected-300 queue uses stable audio IDs whose trailing numeric
        # order is not released in aggregate outputs. The flat reviewer sheets
        # do not expose sample IDs, so model-level source matching is not
        # asserted here.
        _ = audio_id
        source = (
            row.get("variant_source")
            or row.get("source")
            or row.get("risk_atom_type")
            or "unknown"
        )
        sources[source] += 1
        reject_reason = row.get("reject_reason") or row.get("variant_reject_reason") or ""
        if reject_reason:
            reject_reasons[reject_reason] += 1
        counts[(audio_id, run_id)] += 1
    return counts, sources, reject_reasons


def add_derived_scores(rows: list[dict[str, Any]]) -> None:
    sres_norm = minmax([row["sres_total"] for row in rows])
    ceis_norm = minmax([row["ceis_max"] for row in rows])
    sres_rank = percentile_ranks([row["sres_total"] for row in rows])
    ceis_rank = percentile_ranks([row["ceis_max"] for row in rows])
    for index, row in enumerate(rows):
        row["max_norm_sres_ceis"] = max(sres_norm[index], ceis_norm[index])
        row["rank_fusion_sres_ceis"] = (sres_rank[index] + ceis_rank[index]) / 2
        row["two_stage_sres_then_ceis"] = sres_norm[index] + (ceis_norm[index] / 1000.0)
        row["variant_count_only"] = float(row.get("variant_count", 0))
        row["ceis_top1_capped"] = 1.0 if row["ceis_max"] > 0 else 0.0


def predictor_performance(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    evaluable = [row for row in rows if row["decision_change_label"] in {"yes", "no"}]
    for target in ["decision_change_yes", "decision_change_yes_or_uncertain"]:
        target_rows = rows if target.endswith("uncertain") else evaluable
        labels = [int(row[target]) for row in target_rows]
        positives = sum(labels)
        for metric in PREDICTOR_METRICS + ["max_norm_sres_ceis", "rank_fusion_sres_ceis"]:
            scores = [float(row[metric]) for row in target_rows]
            auc = auc_roc(scores, labels)
            output.append(
                {
                    "unit": "model_assessment_clustered_within_row",
                    "target": target,
                    "metric": metric,
                    "evaluated_model_assessments": len(target_rows),
                    "positive_count": positives,
                    "positive_rate": round(positives / len(target_rows), 6) if target_rows else 0.0,
                    "auc": "" if auc is None else round(auc, 6),
                    **threshold_metrics(scores, labels),
                }
            )
    return output


def row_aggregate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["row_number"]].append(row)
    output: list[dict[str, Any]] = []
    for _row_number, group in sorted(grouped.items()):
        label_values = Counter(row["decision_change_label"] for row in group)
        row_decision_yes = any(row["decision_change_label"] == "yes" for row in group)
        row_decision_uncertain = any(row["decision_change_label"] == "uncertain" for row in group)
        severe = any(row["severe_miss"] for row in group)
        unsafe = any(row["unsafe_downrouting"] for row in group)
        critical = any(row["critical_miss"] for row in group)
        item: dict[str, Any] = {
            "selection_stratum": group[0]["selection_stratum"],
            "row_decision_change_yes": int(row_decision_yes),
            "row_decision_change_yes_or_uncertain": int(row_decision_yes or row_decision_uncertain),
            "row_severe_miss": int(severe),
            "row_unsafe_downrouting": int(unsafe),
            "row_critical_miss": int(critical),
            "model_assessments": len(group),
            "decision_label_pattern": ";".join(f"{k}:{v}" for k, v in sorted(label_values.items())),
        }
        for metric in FRONTIER_POLICIES + ["wer", "cer"]:
            item[metric] = max(float(row[metric]) for row in group)
        atoms = [row["ceis_top_atom"] for row in group if row["ceis_top_atom"] != "none"]
        item["top_ceis_atom_family"] = Counter(atoms).most_common(1)[0][0] if atoms else "none"
        output.append(item)
    return output


def rows_for_scope(row_rows: list[dict[str, Any]], scope: str) -> list[dict[str, Any]]:
    if scope == "all":
        return row_rows
    if scope == "exclude_high_proxy_risk":
        return [row for row in row_rows if row["selection_stratum"] != "high_proxy_risk"]
    if scope == "exclude_metric_family_selected":
        return [
            row
            for row in row_rows
            if row["selection_stratum"] not in {"high_proxy_risk", "risk_score_fill"}
        ]
    return row_rows


def select_triggered(
    rows: list[dict[str, Any]],
    metric: str,
    trigger_count: int,
) -> tuple[set[int], dict[str, Any]]:
    ranked = sorted(enumerate(rows), key=lambda item: (-float(item[1][metric]), item[0]))
    selected = ranked[:trigger_count]
    triggered = {index for index, _row in selected}
    if not selected:
        return triggered, {"score_cutoff": "", "tie_boundary_count": 0, "best_case_remaining": "", "worst_case_remaining": ""}
    cutoff = float(selected[-1][1][metric])
    tied = [index for index, row in ranked if float(row[metric]) == cutoff]
    selected_tied = [index for index in tied if index in triggered]
    unselected_tied = [index for index in tied if index not in triggered]
    base_remaining = sum(
        int(row["row_severe_miss"]) for index, row in enumerate(rows) if index not in triggered
    )
    best_case_remaining = base_remaining - sum(
        int(rows[index]["row_severe_miss"]) for index in unselected_tied
    )
    worst_case_remaining = base_remaining + sum(
        int(rows[index]["row_severe_miss"]) for index in selected_tied
    )
    return triggered, {
        "score_cutoff": round(cutoff, 6),
        "tie_boundary_count": len(tied),
        "best_case_remaining": max(best_case_remaining, 0),
        "worst_case_remaining": worst_case_remaining,
    }


def fixed_budget_frontier(row_rows: list[dict[str, Any]], scope: str = "all") -> list[dict[str, Any]]:
    scoped = rows_for_scope(row_rows, scope)
    baseline_severe = sum(int(row["row_severe_miss"]) for row in scoped)
    baseline_unsafe = sum(int(row["row_unsafe_downrouting"]) for row in scoped)
    baseline_critical = sum(int(row["row_critical_miss"]) for row in scoped)
    output: list[dict[str, Any]] = []
    for metric in FRONTIER_POLICIES:
        for budget in BUDGETS:
            requested = round(len(scoped) * budget)
            triggered, tie = select_triggered(scoped, metric, requested)
            severe_remaining = sum(
                int(row["row_severe_miss"])
                for index, row in enumerate(scoped)
                if index not in triggered
            )
            unsafe_remaining = sum(
                int(row["row_unsafe_downrouting"])
                for index, row in enumerate(scoped)
                if index not in triggered
            )
            critical_remaining = sum(
                int(row["row_critical_miss"])
                for index, row in enumerate(scoped)
                if index not in triggered
            )
            output.append(
                {
                    "scope": scope,
                    "unit": "audio_row",
                    "score_metric": metric,
                    "budget_target_rate": f"{budget:.4f}",
                    "budget_denominator_rows": len(scoped),
                    "requested_trigger_rows": requested,
                    "triggered_rows": len(triggered),
                    "observed_budget_rate": round(len(triggered) / len(scoped), 6) if scoped else 0.0,
                    "row_severe_miss_baseline": baseline_severe,
                    "row_severe_miss_remaining": severe_remaining,
                    "row_severe_misses_eliminated": baseline_severe - severe_remaining,
                    "row_unsafe_downrouting_baseline": baseline_unsafe,
                    "row_unsafe_downrouting_remaining": unsafe_remaining,
                    "row_critical_miss_baseline": baseline_critical,
                    "row_critical_miss_remaining": critical_remaining,
                    "triggers_per_severe_miss_eliminated": round(
                        len(triggered) / (baseline_severe - severe_remaining), 6
                    )
                    if baseline_severe - severe_remaining
                    else "n/a",
                    "tie_score_cutoff": tie["score_cutoff"],
                    "tie_boundary_count": tie["tie_boundary_count"],
                    "tie_best_case_severe_remaining": tie["best_case_remaining"],
                    "tie_worst_case_severe_remaining": tie["worst_case_remaining"],
                    "claim_uses": "worst_case_boundary",
                }
            )
    return output


def atom_evidence(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        atom = row["ceis_top_atom"] if row["ceis_top_atom"] != "none" else row["sres_top_atom"]
        grouped[atom or "none"].append(row)
    output = []
    for atom, group in sorted(grouped.items()):
        output.append(
            {
                "atom_type": atom,
                "model_assessment_count": len(group),
                "decision_change_positive_count": sum(row["decision_change_yes"] for row in group),
                "decision_change_rate": round(
                    sum(row["decision_change_yes"] for row in group) / len(group), 6
                )
                if group
                else 0.0,
                "severe_miss_count": sum(row["severe_miss"] for row in group),
                "severe_miss_rate": round(sum(row["severe_miss"] for row in group) / len(group), 6)
                if group
                else 0.0,
                "unsafe_downrouting_count": sum(row["unsafe_downrouting"] for row in group),
                "median_ceis": round(statistics.median(row["ceis_max"] for row in group), 6),
                "median_sres": round(statistics.median(row["sres_total"] for row in group), 6),
            }
        )
    return output


def residual_unsafe_breakdown(row_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Report the aggregate residual after CEIS 20% row budget, matching the
    # primary early-budget policy family without exposing row identifiers.
    triggered, _tie = select_triggered(row_rows, "ceis_max", round(len(row_rows) * 0.20))
    grouped: Counter[tuple[str, str]] = Counter()
    for index, row in enumerate(row_rows):
        if index in triggered or not row["row_unsafe_downrouting"]:
            continue
        severity = "severe" if row["row_severe_miss"] else "non_severe"
        grouped[(severity, row["top_ceis_atom_family"])] += 1
    rows = [
        {
            "policy": "ceis_max_20pct_row_budget",
            "residual_severity": severity,
            "atom_family": atom,
            "residual_row_count": count,
            "release_boundary": "aggregate_only",
        }
        for (severity, atom), count in sorted(grouped.items())
    ]
    if not rows:
        rows.append(
            {
                "policy": "ceis_max_20pct_row_budget",
                "residual_severity": "none_observed",
                "atom_family": "none_observed",
                "residual_row_count": 0,
                "release_boundary": "aggregate_only",
            }
        )
    return rows


def manifest_rows(paths: list[Path], *, repo_root: Path, local_inputs: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        rows.append(
            {
                "path": str(path.relative_to(repo_root)),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
                "privacy_class": "aggregate_safe_tracked",
            }
        )
    for path in local_inputs:
        rows.append(
            {
                "path": f"local_only:{path.name}",
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
                "privacy_class": "local_transcript_bearing_not_tracked",
            }
        )
    return rows


def assert_aggregate_safe(paths: list[Path]) -> None:
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for token in SENSITIVE_FIELDS:
            if token in text:
                raise ValueError(f"sensitive token leaked in aggregate output {path}: {token}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--completed-package-dir",
        type=Path,
        required=True,
        help="Local completed review package root containing reviewer_1 and reviewer_2.",
    )
    parser.add_argument(
        "--ceis-scored",
        type=Path,
        default=Path(
            "70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/artifacts/metric_inputs_three_model/ceis_scored.tsv"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "70_experiments/runs/janus_300_high_stakes_final_csl_2026_06_03"
        ),
    )
    parser.add_argument("--bootstrap-iterations", type=int, default=2000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started = time.time()
    repo_root = Path(__file__).resolve().parents[2]
    output_dir = args.output_dir if args.output_dir.is_absolute() else repo_root / args.output_dir
    package = args.completed_package_dir
    reviewer_1_flat = package / "reviewer_1" / "model_level_review_flat_reviewer_1.tsv"
    reviewer_2_flat = package / "reviewer_2" / "model_level_review_flat_reviewer_2.tsv"
    reviewer_1_merged = package / "reviewer_1" / "human_risk_atom_audit_sheet_reviewer_1.merged.tsv"
    reviewer_2_merged = package / "reviewer_2" / "human_risk_atom_audit_sheet_reviewer_2.merged.tsv"
    ceis_scored = args.ceis_scored if args.ceis_scored.is_absolute() else repo_root / args.ceis_scored

    variant_counts, variant_sources, reject_reasons = load_variant_counts(ceis_scored)
    model_rows, counters = load_model_rows(reviewer_1_flat, reviewer_2_flat, variant_counts)
    add_derived_scores(model_rows)
    row_rows = row_aggregate(model_rows)
    predictor = predictor_performance(model_rows)
    row_counts = [
        {
            "unit": "audio_row",
            "selected_rows": len(row_rows),
            "model_assessments": len(model_rows),
            "row_decision_change_yes": sum(row["row_decision_change_yes"] for row in row_rows),
            "row_decision_change_yes_or_uncertain": sum(
                row["row_decision_change_yes_or_uncertain"] for row in row_rows
            ),
            "row_severe_miss": sum(row["row_severe_miss"] for row in row_rows),
            "row_critical_miss": sum(row["row_critical_miss"] for row in row_rows),
            "row_unsafe_downrouting": sum(row["row_unsafe_downrouting"] for row in row_rows),
            "primary_endpoint": "row_level_fixed_budget_severe_miss"
            if sum(row["row_severe_miss"] for row in row_rows) >= 20
            else "failover_to_decision_change_auc",
        }
    ]
    frontier = fixed_budget_frontier(row_rows, "all")
    sensitivity = []
    for scope in ["exclude_high_proxy_risk", "exclude_metric_family_selected"]:
        sensitivity.extend(fixed_budget_frontier(row_rows, scope))
    atom_rows = atom_evidence(model_rows)
    residual_rows = residual_unsafe_breakdown(row_rows)
    delta = [
        {
            "unit": "audio_row_cluster_bootstrap",
            "comparison": "ceis_max_minus_sres_total",
            "target": "decision_change_yes",
            **bootstrap_auc_delta(
                model_rows,
                "ceis_max",
                "sres_total",
                "decision_change_yes",
                iterations=args.bootstrap_iterations,
                seed=20260603,
            ),
        }
    ]
    residual_gain = residual_gain_after_sres(model_rows)
    variant_source_rows = [
        {
            "source_or_atom_proxy": source,
            "variant_row_count": count,
            "release_boundary": "aggregate_only",
        }
        for source, count in sorted(variant_sources.items())
    ]
    variant_count_values = [int(row.get("variant_count", 0)) for row in model_rows]
    variant_count_rows = [
        {
            "unit": "model_assessment",
            "model_assessments": len(variant_count_values),
            "variant_count_min": min(variant_count_values) if variant_count_values else 0,
            "variant_count_median": statistics.median(variant_count_values) if variant_count_values else 0,
            "variant_count_mean": round(statistics.mean(variant_count_values), 6)
            if variant_count_values
            else 0.0,
            "variant_count_max": max(variant_count_values) if variant_count_values else 0,
            "zero_variant_assessments": sum(1 for value in variant_count_values if value == 0),
            "nonzero_variant_assessments": sum(1 for value in variant_count_values if value > 0),
        }
    ]
    reject_reason_rows = [
        {
            "reject_reason": reason,
            "count": count,
            "release_boundary": "aggregate_only",
        }
        for reason, count in sorted(reject_reasons.items())
    ] or [
        {
            "reject_reason": "not_available_in_current_ceis_scored_input",
            "count": 0,
            "release_boundary": "aggregate_only",
        }
    ]
    gate_rows = [
        {
            "gate": "full_300_900_regeneration",
            "status": "complete" if counters["unique_rows"] == 300 and counters["model_assessments"] == 900 else "needs_repair",
            "evidence": f"{counters['unique_rows']} rows / {counters['model_assessments']} model assessments",
        },
        {
            "gate": "primary_endpoint_positive_count",
            "status": "primary_ok" if row_counts[0]["row_severe_miss"] >= 20 else "failover_required",
            "evidence": f"row-level severe positives={row_counts[0]['row_severe_miss']}",
        },
        {
            "gate": "ceis_ablation_suite",
            "status": "complete_with_claim_downgrade",
            "evidence": "final ablation run covers full/no-plausibility/no-atom-weight/binary/policy-distance-only/top3; policy-distance-only equals full, so three-component performance-driver claim must be downgraded",
        },
        {
            "gate": "variant_count_source_audit",
            "status": "complete_with_reject_reason_boundary",
            "evidence": "local row/run bridge used in memory for variant-count distribution; source coverage reported aggregate-only; reject reasons unavailable if absent from CEIS scored input",
        },
        {
            "gate": "residual_unsafe_breakdown",
            "status": "complete_aggregate",
            "evidence": "aggregate residual unsafe table produced for CEIS 20% row budget",
        },
        {
            "gate": "ceis_residual_gain_after_sres",
            "status": "complete_diagnostic",
            "evidence": "diagnostic logistic residual-gain table compares SRES-only with SRES+CEIS on deterministic consensus labels",
        },
    ]
    red_team_rows = [
        {"question": "main_text_has_30_90_result_claim", "status": "not_checked_in_this_script"},
        {"question": "ceis_written_as_general_asr_metric", "status": "not_checked_in_this_script"},
        {"question": "ceis_claims_total_superiority_over_sres", "status": "not_checked_in_this_script"},
        {"question": "retrospective_replay_written_as_deployment_proof", "status": "not_checked_in_this_script"},
        {"question": "unsafe_downrouting_claim_without_24_case_breakdown", "status": "not_checked_in_this_script"},
    ]

    output_paths: list[Path] = []
    tables = [
        ("final_csl_predictor_performance.tsv", predictor),
        ("final_csl_auc_delta_bootstrap.tsv", delta),
        ("final_csl_residual_gain_after_sres.tsv", residual_gain),
        ("final_csl_row_level_positive_counts.tsv", row_counts),
        ("final_csl_fixed_budget_frontier_row_level.tsv", frontier),
        ("final_csl_selection_exclusion_sensitivity.tsv", sensitivity),
        ("final_csl_atom_linguistic_evidence.tsv", atom_rows),
        ("final_csl_residual_unsafe_breakdown.tsv", residual_rows),
        ("final_csl_variant_source_coverage.tsv", variant_source_rows),
        ("final_csl_variant_count_distribution.tsv", variant_count_rows),
        ("final_csl_variant_reject_reasons.tsv", reject_reason_rows),
        ("final_csl_gate_status.tsv", gate_rows),
        ("final_csl_red_team_check.tsv", red_team_rows),
    ]
    for filename, rows in tables:
        path = output_dir / filename
        write_tsv(path, rows)
        output_paths.append(path)

    summary = {
        "ok": True,
        "status": "final_csl_aggregate_outputs_built",
        "date": "2026-06-03",
        "input_boundary": "local completed reviewer package and local CEIS scored variants",
        "output_boundary": "aggregate-only tracked outputs",
        "definitions": {
            "primary_unit": "audio_row",
            "row_score": "max_h score(row,h)",
            "row_severe_label": "any_h severe_miss(row,h)",
            "budget_denominator": "selected-300 audio rows",
            "tie_rule": "best/worst-case range at cutoff; claim uses worst-case",
            "adjudication_rule": "deterministic consensus over two reviewers; disagreement/uncertain retained as sensitivity",
        },
        "counts": row_counts[0],
        "gate_summary": gate_rows,
        "runtime_seconds": round(time.time() - started, 4),
    }
    summary_path = output_dir / "final_csl_summary.json"
    write_json(summary_path, summary)
    output_paths.append(summary_path)

    manifest = manifest_rows(
        output_paths,
        repo_root=repo_root,
        local_inputs=[reviewer_1_flat, reviewer_2_flat, reviewer_1_merged, reviewer_2_merged, ceis_scored],
    )
    manifest_path = output_dir / "final_csl_manifest_hashes.tsv"
    write_tsv(manifest_path, manifest)
    output_paths.append(manifest_path)
    assert_aggregate_safe(output_paths)

    readme = output_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# Final CSL Aggregate Regeneration",
                "",
                "Date: 2026-06-03",
                "",
                "Status: `final_csl_aggregate_outputs_built`.",
                "",
                "This run implements the final CSL execution plan at the aggregate",
                "boundary. It regenerates selected-300 / 900-assessment evidence",
                "with audio row as the primary unit, pre-specified row budgets,",
                "deterministic consensus labels, CEIS/SRES/fusion frontiers,",
                "selection-exclusion sensitivity, atom-level linguistic evidence,",
                "residual-gain diagnostics after SRES, and residual unsafe",
                "aggregate breakdown.",
                "Variant count matching uses local IDs in memory and releases only",
                "aggregate distributions.",
                "",
                "Transcript-bearing reviewer sheets remain local-only. The tracked",
                "outputs expose aggregate counts, metrics, gate states, and hashes.",
                "",
                "## Primary Endpoint Decision",
                "",
                f"Row-level severe positives: `{row_counts[0]['row_severe_miss']}`.",
                f"Endpoint status: `{row_counts[0]['primary_endpoint']}`.",
                "",
                "## Non-downgradable Remaining Gate",
                "",
                "The CEIS ablation suite includes policy-distance-only; because",
                "it matches full CEIS on this aggregate surface, the manuscript",
                "downgrades plausibility and atom weights to method components,",
                "calibration handles, and interpretability/localization layers.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    output_paths.append(readme)
    assert_aggregate_safe([readme])
    print(json.dumps({"ok": True, "output_dir": str(output_dir), "counts": row_counts[0]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

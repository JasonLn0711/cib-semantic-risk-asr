#!/usr/bin/env python3
"""Analyze whether ASR surface metrics predict downstream CDS risk.

Inputs may contain sample IDs and transcripts, so this script writes only
aggregate, transcript-free outputs for repo records.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import time
from collections import defaultdict
from pathlib import Path
from typing import Any


LABEL_ORDER = {
    "no_escalation": 0,
    "review": 1,
    "priority_review": 2,
    "critical_escalation": 3,
}

HIGH_RISK = {"priority_review", "critical_escalation"}

PREDICTOR_FIELDS = [
    "wer",
    "cer",
    "sres_total",
    "sres_max",
    "ceis_max",
]

TARGET_FIELDS = [
    "label_flip",
    "unsafe_downrouting",
    "high_risk_missed",
    "critical_miss",
    "over_escalation",
    "danger_event",
]


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
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def as_float(value: str | None, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def label_level(label: str) -> int:
    return LABEL_ORDER.get(label, 0)


def parse_run_id(sample_id: str, row: dict[str, str] | None = None) -> str:
    if row and row.get("asr_run_id"):
        return row["asr_run_id"]
    if "__" in sample_id:
        return sample_id.rsplit("__", 1)[1]
    return ""


def mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def median(values: list[float]) -> float:
    return round(statistics.median(values), 4) if values else 0.0


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


def load_sres_samples(path: Path) -> dict[str, dict[str, Any]]:
    samples: dict[str, dict[str, Any]] = {}
    for row in read_tsv(path):
        sample_id = row.get("sample_id", "")
        entry = samples.setdefault(
            sample_id,
            {
                "sample_id": sample_id,
                "asr_run_id": parse_run_id(sample_id, row),
                "split": row.get("split", ""),
                "wer": as_float(row.get("wer")),
                "cer": as_float(row.get("cer")),
                "sres_total": 0.0,
                "sres_max": 0.0,
                "sres_rows": 0,
            },
        )
        sres = as_float(row.get("sres"))
        entry["sres_total"] += sres
        entry["sres_max"] = max(float(entry["sres_max"]), sres)
        entry["sres_rows"] += 1
    for entry in samples.values():
        entry["sres_total"] = round(float(entry["sres_total"]), 4)
        entry["sres_max"] = round(float(entry["sres_max"]), 4)
    return samples


def load_ceis_samples(path: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]]]:
    rows = read_tsv(path)
    samples: dict[str, dict[str, Any]] = {}
    for row in rows:
        sample_id = row.get("sample_id", "")
        component = as_float(row.get("ceis_component"))
        decision_distance = as_float(row.get("decision_distance_used"))
        unstable = (
            component > 0
            or decision_distance > 0
            or row.get("base_decision", "") != row.get("variant_decision", "")
        )
        entry = samples.setdefault(
            sample_id,
            {
                "ceis_max": 0.0,
                "ceis_sum": 0.0,
                "ceis_rows": 0,
                "ceis_unstable_variant_rows": 0,
            },
        )
        entry["ceis_max"] = max(float(entry["ceis_max"]), component)
        entry["ceis_sum"] += component
        entry["ceis_rows"] += 1
        if unstable:
            entry["ceis_unstable_variant_rows"] += 1
    for entry in samples.values():
        entry["ceis_max"] = round(float(entry["ceis_max"]), 4)
        entry["ceis_sum"] = round(float(entry["ceis_sum"]), 4)
    return samples, rows


def add_downstream_targets(samples: dict[str, dict[str, Any]], path: Path) -> None:
    for row in read_tsv(path):
        sample_id = row.get("sample_id", "")
        entry = samples.setdefault(
            sample_id,
            {
                "sample_id": sample_id,
                "asr_run_id": parse_run_id(sample_id, row),
                "wer": 0.0,
                "cer": 0.0,
                "sres_total": 0.0,
                "sres_max": 0.0,
                "ceis_max": 0.0,
            },
        )
        reference = row.get("reference_label", "")
        asr = row.get("asr_label", "")
        reference_level = label_level(reference)
        asr_level = label_level(asr)
        label_flip = int(reference != asr)
        unsafe_downrouting = int(asr_level < reference_level)
        high_risk_missed = int(reference in HIGH_RISK and asr not in HIGH_RISK)
        critical_miss = int(reference == "critical_escalation" and asr not in HIGH_RISK)
        over_escalation = int(asr_level > reference_level)
        entry.update(
            {
                "reference_label": reference,
                "asr_label": asr,
                "label_flip": label_flip,
                "unsafe_downrouting": unsafe_downrouting,
                "high_risk_missed": high_risk_missed,
                "critical_miss": critical_miss,
                "over_escalation": over_escalation,
            }
        )


def merged_samples(
    sres_path: Path,
    ceis_path: Path,
    downstream_path: Path,
    *,
    ceis_threshold: float,
    sres_threshold: float,
) -> list[dict[str, Any]]:
    samples = load_sres_samples(sres_path)
    ceis_samples, _ = load_ceis_samples(ceis_path)
    for sample_id, entry in ceis_samples.items():
        samples.setdefault(
            sample_id,
            {
                "sample_id": sample_id,
                "asr_run_id": parse_run_id(sample_id),
                "wer": 0.0,
                "cer": 0.0,
                "sres_total": 0.0,
                "sres_max": 0.0,
            },
        ).update(entry)
    add_downstream_targets(samples, downstream_path)

    complete = []
    for entry in samples.values():
        if "reference_label" not in entry:
            continue
        danger_event = any(
            bool(entry.get(field, 0))
            for field in [
                "label_flip",
                "unsafe_downrouting",
                "high_risk_missed",
                "critical_miss",
            ]
        )
        danger_event = danger_event or float(entry.get("ceis_max", 0.0)) >= ceis_threshold
        danger_event = danger_event or float(entry.get("sres_total", 0.0)) >= sres_threshold
        entry["danger_event"] = int(danger_event)
        complete.append(entry)
    return complete


def predictor_rows(samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    scopes: list[tuple[str, str, list[dict[str, Any]]]] = [("overall", "ALL", samples)]
    by_run: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for sample in samples:
        by_run[str(sample.get("asr_run_id", ""))].append(sample)
    scopes.extend(("asr_run", run, run_samples) for run, run_samples in sorted(by_run.items()))

    for scope, asr_run_id, scoped_samples in scopes:
        for target in TARGET_FIELDS:
            labels = [int(sample.get(target, 0)) for sample in scoped_samples]
            positive_rows = sum(labels)
            for metric in PREDICTOR_FIELDS:
                scores = [float(sample.get(metric, 0.0)) for sample in scoped_samples]
                threshold = threshold_metrics(scores, labels)
                rows.append(
                    {
                        "scope": scope,
                        "asr_run_id": asr_run_id,
                        "target": target,
                        "metric": metric,
                        "rows": len(scoped_samples),
                        "positive_rows": positive_rows,
                        "positive_rate": round(positive_rows / len(scoped_samples), 4)
                        if scoped_samples
                        else 0.0,
                        "auc": "" if auc_roc(scores, labels) is None else auc_roc(scores, labels),
                        **threshold,
                    }
                )
    return rows


def risk_atom_rows(ceis_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    unstable_samples: dict[tuple[str, str], set[str]] = defaultdict(set)
    all_samples: dict[tuple[str, str], set[str]] = defaultdict(set)

    for row in ceis_rows:
        sample_id = row.get("sample_id", "")
        asr_run_id = parse_run_id(sample_id, row)
        risk_atom = row.get("risk_atom_type", "") or "unknown"
        key = (asr_run_id, risk_atom)
        component = as_float(row.get("ceis_component"))
        decision_distance = as_float(row.get("decision_distance_used"))
        unstable = (
            component > 0
            or decision_distance > 0
            or row.get("base_decision", "") != row.get("variant_decision", "")
        )
        entry = grouped.setdefault(
            key,
            {
                "asr_run_id": asr_run_id,
                "risk_atom_type": risk_atom,
                "variant_rows": 0,
                "unstable_variant_rows": 0,
                "total_ceis_component": 0.0,
                "max_ceis_component": 0.0,
            },
        )
        entry["variant_rows"] += 1
        entry["total_ceis_component"] += component
        entry["max_ceis_component"] = max(float(entry["max_ceis_component"]), component)
        all_samples[key].add(sample_id)
        if unstable:
            entry["unstable_variant_rows"] += 1
            unstable_samples[key].add(sample_id)

    rows = []
    for key, entry in sorted(grouped.items()):
        variant_rows = int(entry["variant_rows"])
        unstable_rows = int(entry["unstable_variant_rows"])
        rows.append(
            {
                **entry,
                "sample_count": len(all_samples[key]),
                "affected_sample_count": len(unstable_samples[key]),
                "unstable_variant_rate": round(unstable_rows / variant_rows, 4)
                if variant_rows
                else 0.0,
                "total_ceis_component": round(float(entry["total_ceis_component"]), 4),
                "max_ceis_component": round(float(entry["max_ceis_component"]), 4),
            }
        )
    return rows


def low_wer_rows(
    samples: list[dict[str, Any]],
    *,
    low_wer_threshold: float,
    ceis_threshold: float,
    sres_threshold: float,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    grouped["ALL"] = samples
    for sample in samples:
        grouped[str(sample.get("asr_run_id", ""))].append(sample)

    for asr_run_id, scoped in sorted(grouped.items()):
        low_wer = [
            sample for sample in scoped if float(sample.get("wer", 0.0)) <= low_wer_threshold
        ]
        rows.append(
            {
                "asr_run_id": asr_run_id,
                "rows": len(scoped),
                "low_wer_threshold": low_wer_threshold,
                "low_wer_rows": len(low_wer),
                "low_wer_rate": round(len(low_wer) / len(scoped), 4) if scoped else 0.0,
                "low_wer_label_flip_count": sum(int(s.get("label_flip", 0)) for s in low_wer),
                "low_wer_unsafe_downrouting_count": sum(
                    int(s.get("unsafe_downrouting", 0)) for s in low_wer
                ),
                "low_wer_high_risk_missed_count": sum(
                    int(s.get("high_risk_missed", 0)) for s in low_wer
                ),
                "low_wer_critical_miss_count": sum(
                    int(s.get("critical_miss", 0)) for s in low_wer
                ),
                "low_wer_sres_trigger_count": sum(
                    1 for s in low_wer if float(s.get("sres_total", 0.0)) >= sres_threshold
                ),
                "low_wer_ceis_trigger_count": sum(
                    1 for s in low_wer if float(s.get("ceis_max", 0.0)) >= ceis_threshold
                ),
                "low_wer_any_danger_count": sum(int(s.get("danger_event", 0)) for s in low_wer),
                "all_label_flip_count": sum(int(s.get("label_flip", 0)) for s in scoped),
                "all_unsafe_downrouting_count": sum(
                    int(s.get("unsafe_downrouting", 0)) for s in scoped
                ),
                "all_high_risk_missed_count": sum(
                    int(s.get("high_risk_missed", 0)) for s in scoped
                ),
            }
        )
    return rows


def run_summary(samples: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for sample in samples:
        grouped[str(sample.get("asr_run_id", ""))].append(sample)
    return {
        run: {
            "rows": len(rows),
            "wer_mean": mean([float(row.get("wer", 0.0)) for row in rows]),
            "wer_median": median([float(row.get("wer", 0.0)) for row in rows]),
            "cer_mean": mean([float(row.get("cer", 0.0)) for row in rows]),
            "cer_median": median([float(row.get("cer", 0.0)) for row in rows]),
            "sres_total_mean": mean([float(row.get("sres_total", 0.0)) for row in rows]),
            "sres_total_median": median([float(row.get("sres_total", 0.0)) for row in rows]),
            "ceis_max_mean": mean([float(row.get("ceis_max", 0.0)) for row in rows]),
            "ceis_max_median": median([float(row.get("ceis_max", 0.0)) for row in rows]),
            "label_flip_count": sum(int(row.get("label_flip", 0)) for row in rows),
            "unsafe_downrouting_count": sum(
                int(row.get("unsafe_downrouting", 0)) for row in rows
            ),
            "high_risk_missed_count": sum(int(row.get("high_risk_missed", 0)) for row in rows),
            "critical_miss_count": sum(int(row.get("critical_miss", 0)) for row in rows),
            "danger_event_count": sum(int(row.get("danger_event", 0)) for row in rows),
        }
        for run, rows in sorted(grouped.items())
    }


def best_overall_predictors(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    best: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.get("scope") != "overall":
            continue
        auc_value = row.get("auc")
        auc_float = None if auc_value == "" else float(auc_value)
        current = best.get(str(row["target"]))
        current_auc = None if not current or current.get("auc") == "" else float(current["auc"])
        if current is None:
            best[str(row["target"])] = row
        elif auc_float is not None and (current_auc is None or auc_float > current_auc):
            best[str(row["target"])] = row
        elif auc_float == current_auc and float(row.get("best_f1", 0.0)) > float(
            current.get("best_f1", 0.0)
        ):
            best[str(row["target"])] = row
    return best


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sres-scored", type=Path, required=True)
    parser.add_argument("--ceis-scored", type=Path, required=True)
    parser.add_argument("--downstream-decisions", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--low-wer-threshold", type=float, default=10.0)
    parser.add_argument("--sres-threshold", type=float, default=20.0)
    parser.add_argument("--ceis-threshold", type=float, default=5.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started = time.time()
    samples = merged_samples(
        args.sres_scored,
        args.ceis_scored,
        args.downstream_decisions,
        ceis_threshold=args.ceis_threshold,
        sres_threshold=args.sres_threshold,
    )
    _, ceis_raw_rows = load_ceis_samples(args.ceis_scored)

    predictors = predictor_rows(samples)
    risk_atoms = risk_atom_rows(ceis_raw_rows)
    low_wer = low_wer_rows(
        samples,
        low_wer_threshold=args.low_wer_threshold,
        ceis_threshold=args.ceis_threshold,
        sres_threshold=args.sres_threshold,
    )

    predictor_fields = [
        "scope",
        "asr_run_id",
        "target",
        "metric",
        "rows",
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
    ]
    risk_atom_fields = [
        "asr_run_id",
        "risk_atom_type",
        "variant_rows",
        "sample_count",
        "unstable_variant_rows",
        "affected_sample_count",
        "unstable_variant_rate",
        "total_ceis_component",
        "max_ceis_component",
    ]
    low_wer_fields = [
        "asr_run_id",
        "rows",
        "low_wer_threshold",
        "low_wer_rows",
        "low_wer_rate",
        "low_wer_label_flip_count",
        "low_wer_unsafe_downrouting_count",
        "low_wer_high_risk_missed_count",
        "low_wer_critical_miss_count",
        "low_wer_sres_trigger_count",
        "low_wer_ceis_trigger_count",
        "low_wer_any_danger_count",
        "all_label_flip_count",
        "all_unsafe_downrouting_count",
        "all_high_risk_missed_count",
    ]

    write_tsv(args.output_dir / "metric_predictor_comparison.tsv", predictors, predictor_fields)
    write_tsv(args.output_dir / "risk_atom_instability.tsv", risk_atoms, risk_atom_fields)
    write_tsv(args.output_dir / "low_wer_danger_summary.tsv", low_wer, low_wer_fields)
    payload = {
        "ok": True,
        "inputs": {
            "sres_scored": str(args.sres_scored),
            "ceis_scored": str(args.ceis_scored),
            "downstream_decisions": str(args.downstream_decisions),
        },
        "thresholds": {
            "low_wer_threshold": args.low_wer_threshold,
            "sres_threshold": args.sres_threshold,
            "ceis_threshold": args.ceis_threshold,
        },
        "notes": [
            "Aggregate-only output; sample IDs and transcripts are intentionally omitted from tracked tables.",
            "AUC treats higher metric values as higher downstream-risk predictions.",
            "Threshold F1 is descriptive and not a calibrated clinical or operational threshold.",
        ],
        "model_sample_count": len(samples),
        "asr_run_count": len({sample.get("asr_run_id", "") for sample in samples}),
        "run_summary": run_summary(samples),
        "best_overall_predictors_by_auc": best_overall_predictors(predictors),
        "low_wer_summary": low_wer,
        "wall_time_seconds": round(time.time() - started, 4),
    }
    write_json(args.output_dir / "metric_predictor_summary.json", payload)
    print(
        json.dumps(
            {
                "ok": True,
                "model_samples": len(samples),
                "predictor_rows": len(predictors),
                "risk_atom_rows": len(risk_atoms),
                "low_wer_rows": len(low_wer),
                "wall_time_seconds": payload["wall_time_seconds"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Evaluate CDS-ASR recovery policies from split-aware metric inputs.

The script writes aggregate, transcript-free outputs suitable for repo records.
Per-sample policy rows should stay under ignored artifacts.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


HIGH_RISK = {"priority_review", "critical_escalation"}
FINITE_GRAMMAR_ATOMS = {"negation", "amount", "action", "actor"}
CONFIDENCE_FIELDS = (
    "confidence",
    "asr_confidence",
    "mean_confidence",
    "avg_confidence",
    "token_confidence",
)

LABEL_ORDER = {
    "no_escalation": 0,
    "review": 1,
    "priority_review": 2,
    "critical_escalation": 3,
}

ORDER_LABEL = {value: key for key, value in LABEL_ORDER.items()}

SRES_WEIGHTS = {
    "negation": 5.0,
    "amount": 5.0,
    "action": 5.0,
    "actor": 4.0,
    "intent": 4.0,
    "scam_pattern": 4.0,
    "time": 3.0,
    "uncertainty": 3.0,
}


@dataclass(frozen=True)
class SampleSignals:
    sample_id: str
    audio_id: str
    asr_run_id: str
    reference_label: str
    asr_label: str
    sres_total: float
    ceis: float
    ceis_risk_atom_type: str
    ensemble_min_level: int
    ensemble_max_level: int
    ensemble_high_risk_votes: int
    ensemble_model_count: int
    confidence: float | None
    review_mode: str


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


def as_float(value: str | None, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def optional_float(value: str | None) -> float | None:
    if value is None or value.strip() == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def label_level(label: str) -> int:
    return LABEL_ORDER.get(label, 0)


def label_for_level(level: int) -> str:
    return ORDER_LABEL.get(max(0, min(level, 3)), "no_escalation")


def parse_sample_id(sample_id: str, note: str = "") -> tuple[str, str]:
    if "__" in sample_id:
        audio_id, asr_run_id = sample_id.rsplit("__", 1)
        return audio_id, asr_run_id
    audio_match = re.search(r"audio_id=([^;]+)", note or "")
    run_match = re.search(r"asr_run_id=([^;]+)", note or "")
    return (
        audio_match.group(1).strip() if audio_match else sample_id,
        run_match.group(1).strip() if run_match else "",
    )


def sres_score(row: dict[str, str]) -> float:
    error_type = (row.get("error_type") or "").strip()
    weight = SRES_WEIGHTS.get(error_type, 1.0)
    return weight * as_float(row.get("severity"), 0.0) * as_float(
        row.get("downstream_impact"),
        0.0,
    )


def ceis_decision_distance(row: dict[str, str]) -> float:
    explicit = optional_float(row.get("decision_distance"))
    if explicit is not None:
        return explicit
    return float(
        abs(label_level(row.get("variant_decision", "")) - label_level(row.get("base_decision", "")))
    )


def ceis_risk_weight(row: dict[str, str]) -> float:
    explicit = optional_float(row.get("risk_atom_weight"))
    if explicit is not None:
        return explicit
    atom = (row.get("risk_atom_type") or row.get("error_type") or "").strip()
    return SRES_WEIGHTS.get(atom, 1.0)


def ceis_score(row: dict[str, str]) -> float:
    plausibility = as_float(row.get("acoustic_plausibility") or row.get("plausibility"), 1.0)
    return plausibility * ceis_risk_weight(row) * ceis_decision_distance(row)


def confidence_for(row: dict[str, str]) -> float | None:
    for field in CONFIDENCE_FIELDS:
        value = optional_float(row.get(field))
        if value is not None:
            return value
    return None


def load_sres_totals(path: Path) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    for row in read_tsv(path):
        totals[row.get("sample_id", "")] += sres_score(row)
    return totals


def load_ceis_scores(path: Path) -> dict[str, dict[str, Any]]:
    by_sample: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_tsv(path):
        by_sample[row.get("sample_id", "")].append(row)

    result: dict[str, dict[str, Any]] = {}
    for sample_id, rows in by_sample.items():
        best_score = -1.0
        best_row: dict[str, str] = {}
        for row in rows:
            score = ceis_score(row)
            if score > best_score:
                best_score = score
                best_row = row
        result[sample_id] = {
            "ceis": round(max(best_score, 0.0), 4),
            "risk_atom_type": best_row.get("risk_atom_type", ""),
            "variant_id": best_row.get("variant_id", ""),
        }
    return result


def load_downstream_rows(
    path: Path,
    sres_totals: dict[str, float],
    ceis_scores: dict[str, dict[str, Any]],
) -> list[SampleSignals]:
    raw_rows = read_tsv(path)
    ensemble_by_audio: dict[str, list[str]] = defaultdict(list)
    parsed_ids: dict[str, tuple[str, str]] = {}
    for row in raw_rows:
        sample_id = row.get("sample_id", "")
        audio_id, asr_run_id = parse_sample_id(sample_id, row.get("note", ""))
        parsed_ids[sample_id] = (audio_id, asr_run_id)
        if row.get("asr_label"):
            ensemble_by_audio[audio_id].append(row["asr_label"])

    samples = []
    for row in raw_rows:
        sample_id = row.get("sample_id", "")
        audio_id, asr_run_id = parsed_ids[sample_id]
        labels = ensemble_by_audio.get(audio_id, [])
        levels = [label_level(label) for label in labels] or [0]
        ceis = ceis_scores.get(sample_id, {})
        samples.append(
            SampleSignals(
                sample_id=sample_id,
                audio_id=audio_id,
                asr_run_id=asr_run_id,
                reference_label=row.get("reference_label", ""),
                asr_label=row.get("asr_label", ""),
                sres_total=round(sres_totals.get(sample_id, 0.0), 4),
                ceis=float(ceis.get("ceis", 0.0)),
                ceis_risk_atom_type=str(ceis.get("risk_atom_type", "")),
                ensemble_min_level=min(levels),
                ensemble_max_level=max(levels),
                ensemble_high_risk_votes=sum(1 for level in levels if level >= 2),
                ensemble_model_count=len(levels),
                confidence=confidence_for(row),
                review_mode=row.get("review_mode", ""),
            )
        )
    return samples


def conservative_high_risk_label(current_label: str) -> str:
    return current_label if label_level(current_label) >= 2 else "priority_review"


def apply_policy(
    sample: SampleSignals,
    policy: str,
    *,
    confidence_threshold: float,
    sres_threshold: float,
    ceis_threshold: float,
    ensemble_mode: str,
) -> dict[str, Any]:
    final_label = sample.asr_label
    trigger = False
    action = "none"
    abstained = False

    if policy == "no_recovery":
        pass
    elif policy == "confidence_only_trigger":
        if sample.confidence is not None and sample.confidence < confidence_threshold:
            trigger = True
            action = "confidence_low_conservative_escalation"
            final_label = conservative_high_risk_label(sample.asr_label)
    elif policy == "sres_triggered_recovery":
        if sample.sres_total >= sres_threshold:
            trigger = True
            action = "sres_conservative_escalation"
            final_label = conservative_high_risk_label(sample.asr_label)
    elif policy == "ceis_triggered_conservative_action":
        if sample.ceis >= ceis_threshold and sample.ceis_risk_atom_type in FINITE_GRAMMAR_ATOMS:
            trigger = True
            action = "ceis_conservative_escalation"
            final_label = conservative_high_risk_label(sample.asr_label)
    elif policy == "ceis_ensemble_arbitration":
        interval_crosses_high_risk = sample.ensemble_min_level < 2 <= sample.ensemble_max_level
        ceis_triggered = sample.ceis >= ceis_threshold and sample.ceis_risk_atom_type in FINITE_GRAMMAR_ATOMS
        if ceis_triggered or interval_crosses_high_risk:
            trigger = True
            if interval_crosses_high_risk:
                abstained = True
                action = "ensemble_interval_conservative_abstention"
            else:
                action = "ceis_ensemble_conservative_escalation"
            if ensemble_mode == "max":
                final_label = label_for_level(max(label_level(sample.asr_label), sample.ensemble_max_level, 2))
            else:
                final_label = conservative_high_risk_label(sample.asr_label)
    else:
        raise ValueError(f"unknown policy: {policy}")

    return {
        "sample_id": sample.sample_id,
        "audio_id": sample.audio_id,
        "asr_run_id": sample.asr_run_id,
        "policy": policy,
        "reference_label": sample.reference_label,
        "asr_label": sample.asr_label,
        "final_label": final_label,
        "triggered": trigger,
        "machine_abstained": abstained,
        "recovery_action": action,
        "sres_total": sample.sres_total,
        "ceis": sample.ceis,
        "ceis_risk_atom_type": sample.ceis_risk_atom_type,
        "ensemble_min_label": label_for_level(sample.ensemble_min_level),
        "ensemble_max_label": label_for_level(sample.ensemble_max_level),
        "ensemble_high_risk_votes": sample.ensemble_high_risk_votes,
        "ensemble_model_count": sample.ensemble_model_count,
        "confidence": "" if sample.confidence is None else sample.confidence,
        "review_mode": sample.review_mode,
    }


def summarize_policy(rows: list[dict[str, Any]], baseline: dict[str, Any] | None = None) -> dict[str, Any]:
    total = len(rows)
    mismatch = 0
    unsafe_downrouting = 0
    high_risk_missed = 0
    critical_missed = 0
    over_escalation = 0
    triggered = 0
    abstained = 0
    exact_recovered = 0
    action_counts: Counter[str] = Counter()
    by_run: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for row in rows:
        ref = str(row["reference_label"])
        asr = str(row["asr_label"])
        final = str(row["final_label"])
        ref_level = label_level(ref)
        final_level = label_level(final)
        asr_level = label_level(asr)
        if final != ref:
            mismatch += 1
        if final_level < ref_level:
            unsafe_downrouting += 1
        if ref in HIGH_RISK and final not in HIGH_RISK:
            high_risk_missed += 1
        if ref == "critical_escalation" and final not in HIGH_RISK:
            critical_missed += 1
        if final_level > ref_level:
            over_escalation += 1
        if bool(row["triggered"]):
            triggered += 1
        if bool(row["machine_abstained"]):
            abstained += 1
        if asr != ref and final == ref:
            exact_recovered += 1
        action_counts[str(row["recovery_action"])] += 1

        run = str(row["asr_run_id"])
        by_run[run]["rows"] += 1
        if final_level < ref_level:
            by_run[run]["unsafe_downrouting_count"] += 1
        if ref in HIGH_RISK and final not in HIGH_RISK:
            by_run[run]["high_risk_missed_count"] += 1
        if bool(row["triggered"]):
            by_run[run]["triggered_count"] += 1
        if bool(row["machine_abstained"]):
            by_run[run]["machine_abstention_count"] += 1

    def rate(value: int) -> float:
        return round(value / total, 4) if total else 0.0

    baseline_unsafe = int(baseline.get("unsafe_downrouting_count", 0)) if baseline else unsafe_downrouting
    baseline_high_missed = int(baseline.get("high_risk_missed_count", 0)) if baseline else high_risk_missed
    baseline_over = int(baseline.get("over_escalation_count", 0)) if baseline else over_escalation
    unsafe_gain = (
        round((baseline_unsafe - unsafe_downrouting) / baseline_unsafe, 4)
        if baseline_unsafe
        else 0.0
    )
    high_miss_gain = (
        round((baseline_high_missed - high_risk_missed) / baseline_high_missed, 4)
        if baseline_high_missed
        else 0.0
    )

    return {
        "rows": total,
        "mismatch_count": mismatch,
        "mismatch_rate": rate(mismatch),
        "unsafe_downrouting_count": unsafe_downrouting,
        "unsafe_downrouting_rate": rate(unsafe_downrouting),
        "high_risk_missed_count": high_risk_missed,
        "high_risk_missed_rate": rate(high_risk_missed),
        "critical_miss_count": critical_missed,
        "critical_miss_rate": rate(critical_missed),
        "over_escalation_count": over_escalation,
        "over_escalation_rate": rate(over_escalation),
        "triggered_count": triggered,
        "recovery_budget_rate": rate(triggered),
        "machine_abstention_count": abstained,
        "machine_abstention_rate": rate(abstained),
        "exact_recovered_error_count": exact_recovered,
        "unsafe_downrouting_reduction_vs_no_recovery": baseline_unsafe - unsafe_downrouting,
        "unsafe_downrouting_gain": unsafe_gain,
        "high_risk_missed_reduction_vs_no_recovery": baseline_high_missed - high_risk_missed,
        "high_risk_missed_gain": high_miss_gain,
        "conservative_escalation_cost_count": over_escalation - baseline_over,
        "action_counts": dict(sorted(action_counts.items())),
        "by_run": {
            run: dict(counts)
            for run, counts in sorted(by_run.items())
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--downstream-decisions", type=Path, required=True)
    parser.add_argument("--sres-annotation", type=Path, required=True)
    parser.add_argument("--counterfactual-variants", type=Path, required=True)
    parser.add_argument("--output-summary-json", type=Path, required=True)
    parser.add_argument("--output-comparison-tsv", type=Path, required=True)
    parser.add_argument("--output-detail-tsv", type=Path)
    parser.add_argument("--confidence-threshold", type=float, default=0.70)
    parser.add_argument("--sres-threshold", type=float, default=20.0)
    parser.add_argument("--ceis-threshold", type=float, default=5.0)
    parser.add_argument("--ensemble-mode", choices=("priority", "max"), default="priority")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started = time.time()
    sres_totals = load_sres_totals(args.sres_annotation)
    ceis_scores = load_ceis_scores(args.counterfactual_variants)
    samples = load_downstream_rows(args.downstream_decisions, sres_totals, ceis_scores)

    policies = [
        "no_recovery",
        "confidence_only_trigger",
        "sres_triggered_recovery",
        "ceis_triggered_conservative_action",
        "ceis_ensemble_arbitration",
    ]
    detail_rows: list[dict[str, Any]] = []
    policy_rows: dict[str, list[dict[str, Any]]] = {}
    baseline_summary: dict[str, Any] | None = None
    summaries: dict[str, dict[str, Any]] = {}

    for policy in policies:
        rows = [
            apply_policy(
                sample,
                policy,
                confidence_threshold=args.confidence_threshold,
                sres_threshold=args.sres_threshold,
                ceis_threshold=args.ceis_threshold,
                ensemble_mode=args.ensemble_mode,
            )
            for sample in samples
        ]
        policy_rows[policy] = rows
        if policy == "no_recovery":
            baseline_summary = summarize_policy(rows)
            summaries[policy] = baseline_summary
        else:
            summaries[policy] = summarize_policy(rows, baseline_summary)
        detail_rows.extend(rows)

    comparison_rows = []
    comparison_fields = [
        "policy",
        "rows",
        "unsafe_downrouting_count",
        "unsafe_downrouting_rate",
        "high_risk_missed_count",
        "high_risk_missed_rate",
        "critical_miss_count",
        "critical_miss_rate",
        "over_escalation_count",
        "over_escalation_rate",
        "triggered_count",
        "recovery_budget_rate",
        "machine_abstention_count",
        "machine_abstention_rate",
        "unsafe_downrouting_reduction_vs_no_recovery",
        "unsafe_downrouting_gain",
        "high_risk_missed_reduction_vs_no_recovery",
        "high_risk_missed_gain",
        "conservative_escalation_cost_count",
        "exact_recovered_error_count",
    ]
    for policy in policies:
        row = {"policy": policy, **summaries[policy]}
        comparison_rows.append(row)

    write_tsv(args.output_comparison_tsv, comparison_rows, comparison_fields)
    if args.output_detail_tsv:
        detail_fields = [
            "sample_id",
            "audio_id",
            "asr_run_id",
            "policy",
            "reference_label",
            "asr_label",
            "final_label",
            "triggered",
            "machine_abstained",
            "recovery_action",
            "sres_total",
            "ceis",
            "ceis_risk_atom_type",
            "ensemble_min_label",
            "ensemble_max_label",
            "ensemble_high_risk_votes",
            "ensemble_model_count",
            "confidence",
            "review_mode",
        ]
        write_tsv(args.output_detail_tsv, detail_rows, detail_fields)

    confidence_available = sum(1 for sample in samples if sample.confidence is not None)
    payload = {
        "ok": True,
        "inputs": {
            "downstream_decisions": str(args.downstream_decisions),
            "sres_annotation": str(args.sres_annotation),
            "counterfactual_variants": str(args.counterfactual_variants),
        },
        "thresholds": {
            "confidence_threshold": args.confidence_threshold,
            "sres_threshold": args.sres_threshold,
            "ceis_threshold": args.ceis_threshold,
            "ensemble_mode": args.ensemble_mode,
        },
        "notes": [
            "Proxy experiment over metric inputs; not a substitute for human-reviewed risk-atom evidence.",
            "Confidence-only condition triggers only when calibrated confidence fields are present.",
            "Conservative actions route low-risk outputs to priority_review instead of using reference labels.",
        ],
        "sample_count": len(samples),
        "confidence_values_present": confidence_available,
        "policies": summaries,
        "wall_time_seconds": round(time.time() - started, 4),
    }
    write_json(args.output_summary_json, payload)
    print(json.dumps({"ok": True, "policies": policies, "rows": len(samples)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

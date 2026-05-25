#!/usr/bin/env python3
"""Compute Counterfactual Escalation Instability Score (CEIS)."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


DEFAULT_WEIGHTS = {
    "negation": 5.0,
    "amount": 5.0,
    "action": 5.0,
    "actor": 4.0,
    "intent": 4.0,
    "scam_pattern": 4.0,
    "time": 3.0,
    "uncertainty": 3.0,
}

LABEL_ORDER = {
    "no_escalation": 0,
    "review": 1,
    "priority_review": 2,
    "critical_escalation": 3,
}


def as_float(value: str | None, default: float = 0.0) -> float:
    if value is None:
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


def decision_distance(row: dict[str, str]) -> float:
    explicit = optional_float(row.get("decision_distance"))
    if explicit is not None:
        return explicit

    base = (row.get("base_decision") or "").strip()
    variant = (row.get("variant_decision") or "").strip()
    if base not in LABEL_ORDER or variant not in LABEL_ORDER:
        return 0.0
    return float(abs(LABEL_ORDER[variant] - LABEL_ORDER[base]))


def risk_weight(row: dict[str, str]) -> float:
    explicit = optional_float(row.get("risk_atom_weight"))
    if explicit is not None:
        return explicit

    atom = (row.get("risk_atom_type") or row.get("error_type") or "").strip()
    return DEFAULT_WEIGHTS.get(atom, 1.0)


def score_row(row: dict[str, str]) -> float:
    plausibility = as_float(
        row.get("acoustic_plausibility") or row.get("plausibility"),
        default=1.0,
    )
    return plausibility * risk_weight(row) * decision_distance(row)


def summarize(rows: list[dict[str, str]]) -> dict[str, Any]:
    by_sample: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_sample[row.get("sample_id", "unknown")].append(row)

    sample_scores = {}
    for sample_id, sample_rows in by_sample.items():
        scored = [(as_float(row.get("ceis_component")), row) for row in sample_rows]
        max_score, max_row = max(scored, key=lambda item: item[0])
        sample_scores[sample_id] = {
            "ceis": round(max_score, 4),
            "max_variant_id": max_row.get("variant_id", ""),
            "risk_atom_type": max_row.get("risk_atom_type", ""),
            "base_decision": max_row.get("base_decision", ""),
            "variant_decision": max_row.get("variant_decision", ""),
        }

    ceis_values = [entry["ceis"] for entry in sample_scores.values()]
    return {
        "variant_rows": len(rows),
        "samples": len(sample_scores),
        "unstable_samples": sum(1 for value in ceis_values if value > 0),
        "max_ceis": round(max(ceis_values), 4) if ceis_values else 0.0,
        "mean_ceis": round(sum(ceis_values) / len(ceis_values), 4)
        if ceis_values
        else 0.0,
        "by_sample": sample_scores,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("variants_tsv", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-tsv", type=Path)
    args = parser.parse_args()

    with args.variants_tsv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))

    for row in rows:
        row["decision_distance_used"] = f"{decision_distance(row):.3f}"
        row["risk_atom_weight_used"] = f"{risk_weight(row):.3f}"
        row["ceis_component"] = f"{score_row(row):.3f}"

    output = {"summary": summarize(rows), "rows": rows}
    text = json.dumps(output, ensure_ascii=False, indent=2)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)

    if args.output_tsv:
        args.output_tsv.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(rows[0].keys()) if rows else []
        with args.output_tsv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

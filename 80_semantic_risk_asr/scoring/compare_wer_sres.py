#!/usr/bin/env python3
"""Compare WER/CER and SRES against downstream failure labels."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def as_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def as_failure(row: dict[str, str]) -> int:
    value = (row.get("downstream_failure") or row.get("failure") or "").strip().lower()
    if value in {"1", "true", "yes", "y", "failed", "failure"}:
        return 1
    impact = as_float(row.get("downstream_impact", "0"))
    return 1 if impact >= 2 else 0


def threshold_metrics(rows: list[dict[str, str]], field: str) -> dict[str, float]:
    scores = sorted({as_float(row.get(field, "0")) for row in rows})
    if not scores:
        return {"best_f1": 0.0, "threshold": 0.0, "precision": 0.0, "recall": 0.0}

    best = {"best_f1": -1.0, "threshold": scores[0], "precision": 0.0, "recall": 0.0}
    for threshold in scores:
        tp = fp = fn = 0
        for row in rows:
            pred = as_float(row.get(field, "0")) >= threshold
            truth = as_failure(row) == 1
            if pred and truth:
                tp += 1
            elif pred and not truth:
                fp += 1
            elif not pred and truth:
                fn += 1
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        if f1 > best["best_f1"]:
            best = {
                "best_f1": round(f1, 4),
                "threshold": round(threshold, 4),
                "precision": round(precision, 4),
                "recall": round(recall, 4),
            }
    return best


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("scored_tsv", type=Path)
    parser.add_argument("--fields", nargs="+", default=["wer", "cer", "sres"])
    args = parser.parse_args()

    with args.scored_tsv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))

    result = {
        "rows": len(rows),
        "failure_rows": sum(as_failure(row) for row in rows),
        "metrics": {field: threshold_metrics(rows, field) for field in args.fields},
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Compute Semantic Risk Error Score (SRES) from an annotation TSV."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


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


def as_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def score_row(row: dict[str, str]) -> float:
    error_type = row.get("error_type", "").strip()
    weight = DEFAULT_WEIGHTS.get(error_type, 1.0)
    severity = as_float(row.get("severity", "0"))
    downstream_impact = as_float(row.get("downstream_impact", "0"))
    return weight * severity * downstream_impact


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("annotation_tsv", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-tsv", type=Path)
    args = parser.parse_args()

    rows: list[dict[str, str]] = []
    totals_by_type: dict[str, float] = defaultdict(float)
    counts_by_type: dict[str, int] = defaultdict(int)

    with args.annotation_tsv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            sres = score_row(row)
            row["sres"] = f"{sres:.3f}"
            rows.append(row)
            error_type = row.get("error_type", "").strip() or "unknown"
            totals_by_type[error_type] += sres
            counts_by_type[error_type] += 1

    total_sres = sum(as_float(row["sres"]) for row in rows)
    summary = {
        "rows": len(rows),
        "total_sres": round(total_sres, 3),
        "mean_sres": round(total_sres / len(rows), 3) if rows else 0.0,
        "by_error_type": {
            key: {
                "count": counts_by_type[key],
                "total_sres": round(value, 3),
                "mean_sres": round(value / counts_by_type[key], 3),
            }
            for key, value in sorted(totals_by_type.items())
        },
    }

    output = {"summary": summary, "rows": rows}
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

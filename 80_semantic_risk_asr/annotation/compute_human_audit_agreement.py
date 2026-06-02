#!/usr/bin/env python3
"""Compute aggregate-only reviewer agreement for human audit sheets.

Inputs may contain audio IDs, transcripts, hypotheses, and reviewer notes.
Outputs intentionally report only aggregate counts and agreement statistics.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_FIELDS = [
    "reviewer_would_asr_error_change_decision",
    "reviewer_semantic_risk_label",
    "reviewer_expected_safe_action",
    "reviewer_annotation_confidence",
]

SENSITIVE_FIELDS = {
    "audio_id",
    "sample_id",
    "reference_text",
    "hypothesis_text",
    "asr_hypotheses_json",
    "reviewer_model_assessments_json",
    "reviewer_verified_transcript",
    "reviewer_notes",
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


def parse_reviewer_sheet(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("reviewer sheets must be reviewer_id=path")
    reviewer_id, path = value.split("=", 1)
    reviewer_id = reviewer_id.strip()
    if not reviewer_id:
        raise argparse.ArgumentTypeError("reviewer_id cannot be empty")
    return reviewer_id, Path(path)


def normalize(value: str) -> str:
    return (value or "").strip()


def load_reviewers(
    reviewer_sheets: list[tuple[str, Path]],
    *,
    key_field: str,
) -> dict[str, dict[str, dict[str, str]]]:
    reviewers: dict[str, dict[str, dict[str, str]]] = {}
    for reviewer_id, path in reviewer_sheets:
        rows = read_tsv(path)
        by_key: dict[str, dict[str, str]] = {}
        for row in rows:
            key = normalize(row.get(key_field, ""))
            if key:
                by_key[key] = row
        reviewers[reviewer_id] = by_key
    return reviewers


def common_keys(reviewers: dict[str, dict[str, dict[str, str]]]) -> list[str]:
    key_sets = [set(rows) for rows in reviewers.values()]
    if not key_sets:
        return []
    return sorted(set.intersection(*key_sets))


def cohen_kappa(pairs: list[tuple[str, str]]) -> dict[str, Any]:
    pairs = [(a, b) for a, b in pairs if a and b]
    n = len(pairs)
    if n == 0:
        return {"n_items": 0, "observed_agreement": "", "expected_agreement": "", "kappa": ""}
    observed = sum(a == b for a, b in pairs) / n
    labels = sorted({label for pair in pairs for label in pair})
    left = Counter(a for a, _ in pairs)
    right = Counter(b for _, b in pairs)
    expected = sum((left[label] / n) * (right[label] / n) for label in labels)
    kappa = "" if expected == 1 else (observed - expected) / (1 - expected)
    return {
        "n_items": n,
        "observed_agreement": round(observed, 6),
        "expected_agreement": round(expected, 6),
        "kappa": "" if kappa == "" else round(kappa, 6),
    }


def fleiss_kappa(label_sets: list[list[str]]) -> dict[str, Any]:
    complete = [labels for labels in label_sets if labels and all(labels)]
    if not complete:
        return {"n_items": 0, "n_reviewers": 0, "observed_agreement": "", "expected_agreement": "", "kappa": ""}
    reviewer_counts = {len(labels) for labels in complete}
    if len(reviewer_counts) != 1:
        raise ValueError("Fleiss kappa requires the same number of reviewer labels per item")
    n_reviewers = reviewer_counts.pop()
    if n_reviewers < 2:
        return {"n_items": 0, "n_reviewers": n_reviewers, "observed_agreement": "", "expected_agreement": "", "kappa": ""}
    labels = sorted({label for row in complete for label in row})
    item_agreements = []
    label_totals: Counter[str] = Counter()
    for row in complete:
        counts = Counter(row)
        label_totals.update(counts)
        item_agreements.append(
            sum(count * (count - 1) for count in counts.values())
            / (n_reviewers * (n_reviewers - 1))
        )
    observed = sum(item_agreements) / len(item_agreements)
    total_labels = len(complete) * n_reviewers
    expected = sum((label_totals[label] / total_labels) ** 2 for label in labels)
    kappa = "" if expected == 1 else (observed - expected) / (1 - expected)
    return {
        "n_items": len(complete),
        "n_reviewers": n_reviewers,
        "observed_agreement": round(observed, 6),
        "expected_agreement": round(expected, 6),
        "kappa": "" if kappa == "" else round(kappa, 6),
    }


def assert_aggregate_safe(payload: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    serialized = json.dumps(payload, ensure_ascii=False) + json.dumps(rows, ensure_ascii=False)
    for field in SENSITIVE_FIELDS:
        if field in serialized:
            raise ValueError(f"sensitive field name leaked into agreement output: {field}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviewer-sheet", action="append", type=parse_reviewer_sheet, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--key-field", default="audio_id")
    parser.add_argument("--fields", default=",".join(DEFAULT_FIELDS))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started = time.time()
    fields = [field.strip() for field in args.fields.split(",") if field.strip()]
    reviewers = load_reviewers(args.reviewer_sheet, key_field=args.key_field)
    reviewer_ids = sorted(reviewers)
    keys = common_keys(reviewers)

    rows: list[dict[str, Any]] = []
    for field in fields:
        labels_by_key = [
            [normalize(reviewers[reviewer_id][key].get(field, "")) for reviewer_id in reviewer_ids]
            for key in keys
        ]
        complete = [labels for labels in labels_by_key if all(labels)]
        result: dict[str, Any] = {
            "field_name": field,
            "common_items": len(keys),
            "complete_items": len(complete),
            "reviewer_count": len(reviewer_ids),
        }
        if len(reviewer_ids) == 2:
            pairs = [(labels[0], labels[1]) for labels in labels_by_key]
            result.update({f"cohen_{key}": value for key, value in cohen_kappa(pairs).items()})
        if len(reviewer_ids) >= 2:
            result.update({f"fleiss_{key}": value for key, value in fleiss_kappa(labels_by_key).items()})
        rows.append(result)

    payload = {
        "ok": True,
        "status": "agreement_computed" if rows else "agreement_no_fields",
        "input_boundary": "local reviewer sheets; do not commit transcript-bearing inputs",
        "output_boundary": "aggregate-only agreement statistics; no row keys, transcripts, hypotheses, or reviewer notes",
        "reviewer_count": len(reviewer_ids),
        "field_count": len(fields),
        "common_item_count": len(keys),
        "wall_time_seconds": round(time.time() - started, 4),
    }
    assert_aggregate_safe(payload, rows)
    write_json(args.output_dir / "human_audit_reviewer_agreement_summary.json", payload)
    write_tsv(
        args.output_dir / "human_audit_reviewer_agreement.tsv",
        rows,
        [
            "field_name",
            "common_items",
            "complete_items",
            "reviewer_count",
            "cohen_n_items",
            "cohen_observed_agreement",
            "cohen_expected_agreement",
            "cohen_kappa",
            "fleiss_n_items",
            "fleiss_n_reviewers",
            "fleiss_observed_agreement",
            "fleiss_expected_agreement",
            "fleiss_kappa",
        ],
    )
    print(json.dumps({"ok": True, "status": payload["status"], "common_items": len(keys)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

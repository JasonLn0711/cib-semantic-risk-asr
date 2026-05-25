#!/usr/bin/env python3
"""Audit completion status for the current selected-300 review batch."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
ANNOTATION_DIR = SCRIPT_PATH.parent
REPO_ROOT = SCRIPT_PATH.parents[2]
if str(ANNOTATION_DIR) not in sys.path:
    sys.path.insert(0, str(ANNOTATION_DIR))

import validate_human_risk_atom_audit as validation  # noqa: E402
from prepare_human_audit_review_batch import (  # noqa: E402
    REFERENCE_TRANSCRIPT_POLICY,
    REMAINING_REVIEW_SCOPE,
    assert_tracked_safe,
    iter_model_assessments,
    missing_model_field_counts,
    missing_row_fields,
    model_counts,
    repo_relative,
)


DEFAULT_RUN_DIR = (
    REPO_ROOT
    / "70_experiments"
    / "runs"
    / "janus_300_high_stakes_human_audit_selection_2026_05_25"
)
DEFAULT_AUDIT_SHEET = DEFAULT_RUN_DIR / "artifacts" / "human_risk_atom_audit_sheet.tsv"
DEFAULT_BATCH_SUMMARY = DEFAULT_RUN_DIR / "human_audit_next_review_batch_summary.json"
SUMMARY_NAME = "human_audit_current_review_batch_status_summary.json"
ROWS_NAME = "human_audit_current_review_batch_status_rows.tsv"


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), list(reader)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_batch(summary_path: Path) -> dict[str, Any]:
    payload = read_json(summary_path)
    row_numbers = payload.get("row_numbers", [])
    if not isinstance(row_numbers, list) or not all(isinstance(item, int) for item in row_numbers):
        raise ValueError("batch summary row_numbers must be a list of integers")
    return payload


def summarize_row(row_number: int, row: dict[str, str], expected_stratum: str) -> dict[str, Any]:
    total_models, reviewed_models, pending_models = model_counts(row)
    missing_models = missing_model_field_counts(row)
    stratum = row.get("selection_stratum", "") or "unknown"
    return {
        "row_number": row_number,
        "selection_stratum": stratum,
        "expected_selection_stratum": expected_stratum,
        "selection_stratum_matches": stratum == expected_stratum,
        "row_review_complete": validation.row_review_complete(row),
        "missing_row_fields": ",".join(missing_row_fields(row)),
        "model_assessments": total_models,
        "reviewed_model_assessments": reviewed_models,
        "pending_model_assessments": pending_models,
        "missing_model_field_counts": ",".join(
            f"{field}={count}" for field, count in sorted(missing_models.items())
        ),
        "model_run_ids": ",".join(
            sorted(str(item.get("asr_run_id", "") or "unknown") for item in iter_model_assessments(row))
        ),
    }


def batch_status(
    *,
    validation_ok: bool,
    invalid_row_numbers: list[int],
    stratum_mismatch_rows: list[int],
    reviewed_rows: int,
    rows_in_batch: int,
    reviewed_model_assessments: int,
    model_assessments: int,
) -> str:
    if not validation_ok:
        return "validation_failed"
    if invalid_row_numbers or stratum_mismatch_rows:
        return "batch_invalid"
    if reviewed_rows == rows_in_batch and reviewed_model_assessments == model_assessments:
        return "batch_complete"
    if reviewed_rows or reviewed_model_assessments:
        return "batch_partial"
    return "batch_pending"


def audit_batch_status(
    *,
    audit_sheet: Path,
    batch_summary: Path,
    output_dir: Path,
    expected_rows: int | None,
    repo_root: Path,
) -> dict[str, Any]:
    started = time.time()
    batch_payload = load_batch(batch_summary)
    expected_stratum = str(batch_payload.get("selection_stratum", "") or "")
    row_numbers = [int(item) for item in batch_payload["row_numbers"]]
    fieldnames, rows = read_tsv(audit_sheet)
    validation_payload = validation.validate_rows(
        fieldnames,
        rows,
        require_complete=False,
        expected_rows=expected_rows,
    )

    invalid_row_numbers = [
        row_number for row_number in row_numbers if row_number < 1 or row_number > len(rows)
    ]
    row_summaries = []
    for row_number in row_numbers:
        if row_number in invalid_row_numbers:
            continue
        row_summaries.append(summarize_row(row_number, rows[row_number - 1], expected_stratum))

    stratum_mismatch_rows = [
        int(item["row_number"]) for item in row_summaries if not item["selection_stratum_matches"]
    ]
    reviewed_rows = sum(1 for item in row_summaries if item["row_review_complete"])
    model_assessments = sum(int(item["model_assessments"]) for item in row_summaries)
    reviewed_model_assessments = sum(
        int(item["reviewed_model_assessments"]) for item in row_summaries
    )
    pending_rows = len(row_summaries) - reviewed_rows
    pending_model_assessments = model_assessments - reviewed_model_assessments
    missing_row_field_counts: Counter[str] = Counter()
    missing_model_field_counts_total: Counter[str] = Counter()
    for item in row_summaries:
        for field in str(item["missing_row_fields"]).split(","):
            if field:
                missing_row_field_counts[field] += 1
        for pair in str(item["missing_model_field_counts"]).split(","):
            if not pair:
                continue
            field, _, value = pair.partition("=")
            if field and value.isdigit():
                missing_model_field_counts_total[field] += int(value)

    status = batch_status(
        validation_ok=bool(validation_payload["ok"]),
        invalid_row_numbers=invalid_row_numbers,
        stratum_mismatch_rows=stratum_mismatch_rows,
        reviewed_rows=reviewed_rows,
        rows_in_batch=len(row_summaries),
        reviewed_model_assessments=reviewed_model_assessments,
        model_assessments=model_assessments,
    )
    summary_path = output_dir / SUMMARY_NAME
    rows_path = output_dir / ROWS_NAME
    summary = {
        "ok": validation_payload["ok"] and status != "batch_invalid",
        "status": status,
        "batch_ready_for_refresh": status == "batch_complete",
        "input_boundary": "local ignored audit sheet plus tracked batch summary",
        "output_boundary": "aggregate-only batch completion status; no private row keys or transcript text",
        "reference_transcript_policy": REFERENCE_TRANSCRIPT_POLICY,
        "remaining_review_scope": REMAINING_REVIEW_SCOPE,
        "selection_stratum": expected_stratum,
        "row_numbers": row_numbers,
        "rows_in_batch": len(row_summaries),
        "reviewed_rows_in_batch": reviewed_rows,
        "pending_rows_in_batch": pending_rows,
        "model_assessments_in_batch": model_assessments,
        "reviewed_model_assessments_in_batch": reviewed_model_assessments,
        "pending_model_assessments_in_batch": pending_model_assessments,
        "invalid_row_numbers": invalid_row_numbers,
        "stratum_mismatch_rows": stratum_mismatch_rows,
        "missing_row_field_counts": dict(sorted(missing_row_field_counts.items())),
        "missing_model_field_counts": dict(sorted(missing_model_field_counts_total.items())),
        "source_batch_summary": repo_relative(batch_summary, repo_root=repo_root),
        "local_packet_path": batch_payload.get("local_packet_path", ""),
        "tracked_rows_path": repo_relative(rows_path, repo_root=repo_root),
        "next_action": (
            "Complete all row fields and per-model assessments for this batch, "
            "then rerun this status audit before refreshing aggregate evidence."
            if status != "batch_complete"
            else "Run refresh_human_audit_evidence.py, then prepare or audit the next review batch."
        ),
        "runtime_seconds": round(time.time() - started, 4),
    }
    fieldnames_out = [
        "row_number",
        "selection_stratum",
        "expected_selection_stratum",
        "selection_stratum_matches",
        "row_review_complete",
        "missing_row_fields",
        "model_assessments",
        "reviewed_model_assessments",
        "pending_model_assessments",
        "missing_model_field_counts",
        "model_run_ids",
    ]
    assert_tracked_safe(summary)
    assert_tracked_safe(row_summaries)
    write_json(summary_path, summary)
    write_tsv(rows_path, row_summaries, fieldnames_out)
    return {
        **summary,
        "tracked_summary_path": repo_relative(summary_path, repo_root=repo_root),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-sheet", type=Path, default=DEFAULT_AUDIT_SHEET)
    parser.add_argument("--batch-summary", type=Path, default=DEFAULT_BATCH_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--expected-rows", type=int, default=30)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = audit_batch_status(
        audit_sheet=args.audit_sheet,
        batch_summary=args.batch_summary,
        output_dir=args.output_dir,
        expected_rows=args.expected_rows,
        repo_root=REPO_ROOT,
    )
    print(
        json.dumps(
            {
                "ok": payload["ok"],
                "status": payload["status"],
                "batch_ready_for_refresh": payload["batch_ready_for_refresh"],
                "selection_stratum": payload["selection_stratum"],
                "reviewed_rows_in_batch": payload["reviewed_rows_in_batch"],
                "pending_rows_in_batch": payload["pending_rows_in_batch"],
                "reviewed_model_assessments_in_batch": payload[
                    "reviewed_model_assessments_in_batch"
                ],
                "pending_model_assessments_in_batch": payload[
                    "pending_model_assessments_in_batch"
                ],
                "tracked_summary_path": payload["tracked_summary_path"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

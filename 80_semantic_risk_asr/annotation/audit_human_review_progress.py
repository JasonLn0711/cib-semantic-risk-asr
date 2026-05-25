#!/usr/bin/env python3
"""Summarize local human-audit review progress without leaking row content."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
ANNOTATION_DIR = SCRIPT_PATH.parent
REPO_ROOT = SCRIPT_PATH.parents[2]
if str(ANNOTATION_DIR) not in sys.path:
    sys.path.insert(0, str(ANNOTATION_DIR))

import validate_human_risk_atom_audit as validation  # noqa: E402


DEFAULT_RUN_DIR = (
    REPO_ROOT
    / "70_experiments"
    / "runs"
    / "janus_300_high_stakes_human_audit_selection_2026_05_25"
)
DEFAULT_AUDIT_SHEET = DEFAULT_RUN_DIR / "artifacts" / "human_risk_atom_audit_sheet.tsv"
SUMMARY_NAME = "human_audit_progress_summary.json"
STRATA_NAME = "human_audit_progress_by_stratum.tsv"
MODEL_NAME = "human_audit_progress_by_model.tsv"
RECOMMENDED_BATCH_NAME = "human_audit_review_batches.tsv"

ROW_REVIEW_FIELDS = validation.ROW_REVIEW_FIELDS
MODEL_REVIEW_FIELDS = validation.MODEL_REVIEW_FIELDS
STRATUM_PRIORITY = {
    "critical_or_high_risk_missed": 0,
    "unsafe_downrouting": 1,
    "high_proxy_risk": 2,
    "model_disagreement": 3,
    "risk_score_fill": 4,
    "clean_control": 5,
}
SENSITIVE_TOKENS = (
    "audio_id",
    "sample_id",
    "reference_text",
    "hypothesis_text",
    "asr_hypotheses_json",
    "reviewer_model_assessments_json",
    "reviewer_notes",
    "reviewer_verified_transcript",
    "PRIVATE_",
)
REFERENCE_TRANSCRIPT_POLICY = (
    "Reference transcripts are treated as already human-reviewed ground truth "
    "for WER/CER scoring; do not route duplicate transcript review."
)
REMAINING_REVIEW_SCOPE = (
    "Progress counts cover selected-300 risk-atom, decision-change, expected "
    "safe action, confidence, and per-model assessment fields only."
)


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
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def parse_json_field(value: str) -> Any:
    if not value.strip():
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def model_assessment_reviewed(item: dict[str, Any]) -> bool:
    return all(str(item.get(field, "")).strip() for field in MODEL_REVIEW_FIELDS)


def missing_row_fields(row: dict[str, str]) -> list[str]:
    return [field for field in ROW_REVIEW_FIELDS if not (row.get(field) or "").strip()]


def missing_model_fields(item: dict[str, Any]) -> list[str]:
    return [field for field in MODEL_REVIEW_FIELDS if not str(item.get(field, "")).strip()]


def iter_model_assessments(row: dict[str, str]) -> list[dict[str, Any]]:
    value = parse_json_field(row.get("reviewer_model_assessments_json", ""))
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def completion_rate(reviewed: int, total: int) -> float:
    return round(reviewed / total, 4) if total else 0.0


def stratum_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_stratum: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in rows:
        stratum = row.get("selection_stratum", "") or "unknown"
        row_reviewed = validation.row_review_complete(row)
        by_stratum[stratum]["audit_rows"] += 1
        by_stratum[stratum]["reviewed_rows"] += int(row_reviewed)
        by_stratum[stratum]["pending_rows"] += int(not row_reviewed)
        for item in iter_model_assessments(row):
            by_stratum[stratum]["model_assessments"] += 1
            reviewed = model_assessment_reviewed(item)
            by_stratum[stratum]["reviewed_model_assessments"] += int(reviewed)
            by_stratum[stratum]["pending_model_assessments"] += int(not reviewed)
    result = []
    for stratum, counts in sorted(
        by_stratum.items(),
        key=lambda item: (STRATUM_PRIORITY.get(item[0], 99), item[0]),
    ):
        result.append(
            {
                "selection_stratum": stratum,
                "audit_rows": counts["audit_rows"],
                "reviewed_rows": counts["reviewed_rows"],
                "pending_rows": counts["pending_rows"],
                "row_completion_rate": completion_rate(
                    counts["reviewed_rows"],
                    counts["audit_rows"],
                ),
                "model_assessments": counts["model_assessments"],
                "reviewed_model_assessments": counts["reviewed_model_assessments"],
                "pending_model_assessments": counts["pending_model_assessments"],
                "model_completion_rate": completion_rate(
                    counts["reviewed_model_assessments"],
                    counts["model_assessments"],
                ),
            }
        )
    return result


def model_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_model: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in rows:
        for item in iter_model_assessments(row):
            run_id = str(item.get("asr_run_id", "") or "unknown")
            by_model[run_id]["model_assessments"] += 1
            reviewed = model_assessment_reviewed(item)
            by_model[run_id]["reviewed_model_assessments"] += int(reviewed)
            by_model[run_id]["pending_model_assessments"] += int(not reviewed)
    result = []
    for run_id, counts in sorted(by_model.items()):
        result.append(
            {
                "asr_run_id": run_id,
                "model_assessments": counts["model_assessments"],
                "reviewed_model_assessments": counts["reviewed_model_assessments"],
                "pending_model_assessments": counts["pending_model_assessments"],
                "model_completion_rate": completion_rate(
                    counts["reviewed_model_assessments"],
                    counts["model_assessments"],
                ),
            }
        )
    return result


def recommended_batches(strata: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, item in enumerate(strata, start=1):
        if int(item["pending_rows"]) == 0 and int(item["pending_model_assessments"]) == 0:
            continue
        rows.append(
            {
                "batch_order": index,
                "selection_stratum": item["selection_stratum"],
                "pending_rows": item["pending_rows"],
                "pending_model_assessments": item["pending_model_assessments"],
                "primary_reason": reason_for_stratum(str(item["selection_stratum"])),
                "completion_gate": "row fields plus all model-level assessments for rows in this stratum",
            }
        )
    return rows


def reason_for_stratum(stratum: str) -> str:
    return {
        "critical_or_high_risk_missed": "highest paper-safety risk; resolves missed critical/high-risk cases first",
        "unsafe_downrouting": "directly targets dangerous de-escalation claims",
        "high_proxy_risk": "checks whether proxy SRES/CEIS risk is human-confirmed",
        "model_disagreement": "supports model-comparison claims without relying on row-level labels alone",
        "risk_score_fill": "fills residual high-score evidence coverage",
        "clean_control": "provides negative/control rows for reviewer calibration",
    }.get(stratum, "unrecognized stratum; review after named strata")


def build_progress(fieldnames: list[str], rows: list[dict[str, str]], expected_rows: int | None) -> dict[str, Any]:
    validation_payload = validation.validate_rows(
        fieldnames,
        rows,
        require_complete=False,
        expected_rows=expected_rows,
    )
    row_missing = Counter()
    model_missing = Counter()
    invalid_model_bundle_rows = 0
    for row in rows:
        row_missing.update(missing_row_fields(row))
        assessments = parse_json_field(row.get("reviewer_model_assessments_json", ""))
        if not isinstance(assessments, list):
            invalid_model_bundle_rows += 1
            continue
        for item in assessments:
            if isinstance(item, dict):
                model_missing.update(missing_model_fields(item))

    strata = stratum_rows(rows)
    models = model_rows(rows)
    batches = recommended_batches(strata)
    payload = {
        "ok": validation_payload["ok"],
        "status": validation_payload["status"],
        "input_boundary": "local transcript-bearing audit sheet; do not commit input",
        "output_boundary": "aggregate-only progress counts; no private row keys or transcript text",
        "expected_rows": expected_rows if expected_rows is not None else "",
        "audit_rows": validation_payload["audit_rows"],
        "reviewed_rows": validation_payload["reviewed_rows"],
        "pending_rows": validation_payload["pending_rows"],
        "row_completion_rate": completion_rate(
            validation_payload["reviewed_rows"],
            validation_payload["audit_rows"],
        ),
        "model_assessments": validation_payload["model_assessments"],
        "reviewed_model_assessments": validation_payload["reviewed_model_assessments"],
        "pending_model_assessments": validation_payload["pending_model_assessments"],
        "model_completion_rate": completion_rate(
            validation_payload["reviewed_model_assessments"],
            validation_payload["model_assessments"],
        ),
        "validation_error_counts": validation_payload["error_counts"],
        "validation_warning_counts": validation_payload["warning_counts"],
        "reference_transcript_policy": REFERENCE_TRANSCRIPT_POLICY,
        "remaining_review_scope": REMAINING_REVIEW_SCOPE,
        "missing_row_review_field_counts": dict(sorted(row_missing.items())),
        "missing_model_review_field_counts": dict(sorted(model_missing.items())),
        "invalid_model_bundle_rows": invalid_model_bundle_rows,
        "pending_by_selection_stratum": {
            item["selection_stratum"]: item["pending_rows"]
            for item in strata
            if int(item["pending_rows"])
        },
        "pending_model_assessments_by_run_id": {
            item["asr_run_id"]: item["pending_model_assessments"]
            for item in models
            if int(item["pending_model_assessments"])
        },
        "recommended_batch_count": len(batches),
        "first_principle_decision": (
            "Reviewer time is the current scarce resource for risk/decision "
            "labels, not for duplicate transcript review. Review high-safety-risk "
            "strata first, then refresh aggregate evidence before making "
            "paper-grade CDS-ASR claims."
        ),
        "next_action": (
            "Review critical/high-risk missed and unsafe-downrouting strata first, "
            "fill risk-atom, decision-change, expected-action, confidence, and "
            "model-level fields, then run refresh_human_audit_evidence.py "
            "--require-complete."
        ),
    }
    assert_progress_safe(payload, strata + models + batches)
    return {
        "summary": payload,
        "strata": strata,
        "models": models,
        "batches": batches,
    }


def assert_progress_safe(payload: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    for token in SENSITIVE_TOKENS:
        if token in text:
            raise ValueError(f"sensitive token leaked into progress summary: {token}")
    for row in rows:
        for token in SENSITIVE_TOKENS:
            if token in row:
                raise ValueError(f"sensitive token present in progress row: {token}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-sheet", type=Path, default=DEFAULT_AUDIT_SHEET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--expected-rows", type=int, default=30)
    return parser.parse_args()


def main() -> int:
    started = time.time()
    args = parse_args()
    fieldnames, rows = read_tsv(args.audit_sheet)
    progress = build_progress(fieldnames, rows, args.expected_rows)
    summary = progress["summary"]
    summary["runtime_seconds"] = round(time.time() - started, 4)
    assert_progress_safe(summary, progress["strata"] + progress["models"] + progress["batches"])
    write_json(args.output_dir / SUMMARY_NAME, summary)
    write_tsv(
        args.output_dir / STRATA_NAME,
        progress["strata"],
        [
            "selection_stratum",
            "audit_rows",
            "reviewed_rows",
            "pending_rows",
            "row_completion_rate",
            "model_assessments",
            "reviewed_model_assessments",
            "pending_model_assessments",
            "model_completion_rate",
        ],
    )
    write_tsv(
        args.output_dir / MODEL_NAME,
        progress["models"],
        [
            "asr_run_id",
            "model_assessments",
            "reviewed_model_assessments",
            "pending_model_assessments",
            "model_completion_rate",
        ],
    )
    write_tsv(
        args.output_dir / RECOMMENDED_BATCH_NAME,
        progress["batches"],
        [
            "batch_order",
            "selection_stratum",
            "pending_rows",
            "pending_model_assessments",
            "primary_reason",
            "completion_gate",
        ],
    )
    print(
        json.dumps(
            {
                "ok": summary["ok"],
                "status": summary["status"],
                "reviewed_rows": summary["reviewed_rows"],
                "pending_rows": summary["pending_rows"],
                "reviewed_model_assessments": summary["reviewed_model_assessments"],
                "pending_model_assessments": summary["pending_model_assessments"],
                "recommended_batch_count": summary["recommended_batch_count"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

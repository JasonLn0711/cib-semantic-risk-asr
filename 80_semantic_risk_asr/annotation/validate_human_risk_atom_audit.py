#!/usr/bin/env python3
"""Validate a local human risk-atom audit sheet.

The audit sheet is local-only and can contain transcripts. This validator emits
aggregate-only JSON suitable for tracked run records.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any


REQUIRED_COLUMNS = [
    "audio_id",
    "split",
    "selection_stratum",
    "reference_label",
    "reference_text",
    "asr_hypotheses_json",
    "risk_signal_json",
    "reviewer_semantic_risk_label",
    "reviewer_risk_atoms",
    "reviewer_critical_atoms",
    "reviewer_asr_confusion_terms",
    "reviewer_would_asr_error_change_decision",
    "reviewer_decision_change_reason",
    "reviewer_expected_safe_action",
    "reviewer_annotation_confidence",
    "reviewer_model_assessments_json",
]

ROW_REVIEW_FIELDS = [
    "reviewer_semantic_risk_label",
    "reviewer_risk_atoms",
    "reviewer_critical_atoms",
    "reviewer_asr_confusion_terms",
    "reviewer_would_asr_error_change_decision",
    "reviewer_decision_change_reason",
    "reviewer_expected_safe_action",
    "reviewer_annotation_confidence",
]

MODEL_REVIEW_FIELDS = [
    "reviewer_would_asr_error_change_decision",
    "reviewer_critical_atoms",
    "reviewer_expected_safe_action",
    "reviewer_annotation_confidence",
]

VALID_LABELS = {"no_escalation", "review", "priority_review", "critical_escalation"}
VALID_DECISION_CHANGE = {"yes", "no", "uncertain"}
VALID_CONFIDENCE = {"high", "medium", "low"}
VALID_SAFE_ACTION = {
    "none",
    "manual_review",
    "priority_review",
    "critical_escalation",
    "conservative_machine_action",
    "abstain",
}
VALID_ATOMS = {
    "negation",
    "amount",
    "action",
    "actor",
    "intent",
    "time",
    "uncertainty",
    "scam_pattern",
}

SENSITIVE_FIELDS = {
    "audio_id",
    "sample_id",
    "reference_text",
    "hypothesis_text",
    "asr_hypotheses_json",
    "reviewer_model_assessments_json",
    "reviewer_notes",
    "reviewer_verified_transcript",
}


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


def parse_json_field(value: str) -> Any:
    if not value.strip():
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def split_atoms(value: str) -> list[str]:
    atoms = []
    for item in value.replace(";", ",").replace("|", ",").split(","):
        atom = item.strip()
        if atom and atom.lower() != "none":
            atoms.append(atom)
    return atoms


def atom_set(value: str) -> set[str]:
    return set(split_atoms(value))


def row_review_complete(row: dict[str, str]) -> bool:
    return all((row.get(field) or "").strip() for field in ROW_REVIEW_FIELDS)


def model_review_complete(item: dict[str, Any]) -> bool:
    return all(str(item.get(field, "")).strip() for field in MODEL_REVIEW_FIELDS)


def count_invalid_atoms(value: str) -> int:
    return sum(1 for atom in split_atoms(value) if atom not in VALID_ATOMS)


def row_review_consistency_errors(row: dict[str, str]) -> Counter[str]:
    errors: Counter[str] = Counter()
    risk_atoms = atom_set(row.get("reviewer_risk_atoms", ""))
    critical_atoms = atom_set(row.get("reviewer_critical_atoms", ""))
    unknown_critical_atoms = critical_atoms - risk_atoms
    if unknown_critical_atoms:
        errors["critical_atom_not_in_risk_atoms"] += len(unknown_critical_atoms)

    decision_change = row.get("reviewer_would_asr_error_change_decision", "")
    safe_action = row.get("reviewer_expected_safe_action", "")
    if decision_change == "yes" and safe_action == "none":
        errors["decision_change_yes_requires_non_none_safe_action"] += 1
    if decision_change == "yes" and not critical_atoms:
        errors["decision_change_yes_requires_critical_atom"] += 1
    return errors


def model_review_consistency_errors(
    item: dict[str, Any],
    *,
    row_risk_atoms: set[str],
) -> Counter[str]:
    errors: Counter[str] = Counter()
    critical_atoms = atom_set(str(item.get("reviewer_critical_atoms", "")))
    unknown_critical_atoms = critical_atoms - row_risk_atoms
    if unknown_critical_atoms:
        errors["model_critical_atom_not_in_row_risk_atoms"] += len(unknown_critical_atoms)

    decision_change = str(item.get("reviewer_would_asr_error_change_decision", ""))
    safe_action = str(item.get("reviewer_expected_safe_action", ""))
    if decision_change == "yes" and safe_action == "none":
        errors["model_decision_change_yes_requires_non_none_safe_action"] += 1
    if decision_change == "yes" and not critical_atoms:
        errors["model_decision_change_yes_requires_critical_atom"] += 1
    return errors


def status_for(
    *,
    errors: Counter[str],
    reviewed_rows: int,
    total_rows: int,
    reviewed_model_assessments: int,
    model_assessments: int,
) -> str:
    if errors:
        return "validation_failed"
    if reviewed_rows == total_rows and reviewed_model_assessments == model_assessments:
        return "review_complete"
    if reviewed_rows or reviewed_model_assessments:
        return "partial_review"
    return "review_pending"


def validate_rows(
    fieldnames: list[str],
    rows: list[dict[str, str]],
    *,
    require_complete: bool,
    expected_rows: int | None = None,
) -> dict[str, Any]:
    errors: Counter[str] = Counter()
    warnings: Counter[str] = Counter()
    audio_seen: set[str] = set()
    reviewed_rows = 0
    model_assessments = 0
    reviewed_model_assessments = 0

    for column in REQUIRED_COLUMNS:
        if column not in fieldnames:
            errors["missing_required_column"] += 1

    if expected_rows is not None and len(rows) != expected_rows:
        errors["unexpected_audit_row_count"] += 1

    for row in rows:
        audio_id = row.get("audio_id", "")
        if not audio_id:
            errors["missing_private_row_key"] += 1
        if audio_id in audio_seen:
            errors["duplicate_private_row_key"] += 1
        if audio_id:
            audio_seen.add(audio_id)

        hypotheses = parse_json_field(row.get("asr_hypotheses_json", ""))
        assessments = parse_json_field(row.get("reviewer_model_assessments_json", ""))
        if not isinstance(hypotheses, list):
            errors["invalid_hypothesis_bundle_json"] += 1
            hypotheses = []
        if not isinstance(assessments, list):
            errors["invalid_model_review_bundle_json"] += 1
            assessments = []

        hypothesis_run_ids = {
            str(item.get("asr_run_id", ""))
            for item in hypotheses
            if isinstance(item, dict) and item.get("asr_run_id")
        }
        assessment_run_ids = {
            str(item.get("asr_run_id", ""))
            for item in assessments
            if isinstance(item, dict) and item.get("asr_run_id")
        }
        if hypothesis_run_ids != assessment_run_ids:
            errors["model_assessment_run_id_mismatch"] += 1

        if row_review_complete(row):
            reviewed_rows += 1
            if row.get("reviewer_semantic_risk_label", "") not in VALID_LABELS:
                errors["invalid_reviewer_semantic_risk_label"] += 1
            if row.get("reviewer_would_asr_error_change_decision", "") not in VALID_DECISION_CHANGE:
                errors["invalid_reviewer_would_asr_error_change_decision"] += 1
            if row.get("reviewer_expected_safe_action", "") not in VALID_SAFE_ACTION:
                errors["invalid_reviewer_expected_safe_action"] += 1
            if row.get("reviewer_annotation_confidence", "") not in VALID_CONFIDENCE:
                errors["invalid_reviewer_annotation_confidence"] += 1
            errors["invalid_reviewer_risk_atom"] += count_invalid_atoms(row.get("reviewer_risk_atoms", ""))
            errors["invalid_reviewer_critical_atom"] += count_invalid_atoms(
                row.get("reviewer_critical_atoms", "")
            )
            errors.update(row_review_consistency_errors(row))
        else:
            warnings["pending_row_review"] += 1
            if require_complete:
                errors["incomplete_row_review"] += 1

        row_risk_atoms = atom_set(row.get("reviewer_risk_atoms", ""))
        model_assessments += len(assessments)
        for item in assessments:
            if not isinstance(item, dict):
                errors["invalid_model_assessment_item"] += 1
                continue
            if model_review_complete(item):
                reviewed_model_assessments += 1
                if item.get("reviewer_would_asr_error_change_decision", "") not in VALID_DECISION_CHANGE:
                    errors["invalid_model_decision_change"] += 1
                if item.get("reviewer_expected_safe_action", "") not in VALID_SAFE_ACTION:
                    errors["invalid_model_expected_safe_action"] += 1
                if item.get("reviewer_annotation_confidence", "") not in VALID_CONFIDENCE:
                    errors["invalid_model_annotation_confidence"] += 1
                errors["invalid_model_critical_atom"] += count_invalid_atoms(
                    str(item.get("reviewer_critical_atoms", ""))
                )
                errors.update(
                    model_review_consistency_errors(
                        item,
                        row_risk_atoms=row_risk_atoms,
                    )
                )
            else:
                warnings["pending_model_review"] += 1
                if require_complete:
                    errors["incomplete_model_review"] += 1

    errors = Counter({key: value for key, value in errors.items() if value})
    warnings = Counter({key: value for key, value in warnings.items() if value})
    status = status_for(
        errors=errors,
        reviewed_rows=reviewed_rows,
        total_rows=len(rows),
        reviewed_model_assessments=reviewed_model_assessments,
        model_assessments=model_assessments,
    )
    return {
        "ok": not errors,
        "status": status,
        "require_complete": require_complete,
        "expected_rows": expected_rows if expected_rows is not None else "",
        "audit_rows": len(rows),
        "reviewed_rows": reviewed_rows,
        "pending_rows": len(rows) - reviewed_rows,
        "model_assessments": model_assessments,
        "reviewed_model_assessments": reviewed_model_assessments,
        "pending_model_assessments": model_assessments - reviewed_model_assessments,
        "error_counts": dict(sorted(errors.items())),
        "warning_counts": dict(sorted(warnings.items())),
    }


def assert_aggregate_safe(payload: dict[str, Any]) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    for field in SENSITIVE_FIELDS:
        if field in text:
            raise ValueError(f"sensitive field name leaked into validation summary: {field}")
    if "PRIVATE_" in text:
        raise ValueError("private fixture content leaked into validation summary")


def validation_count_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for severity, group_name in (("error", "error_counts"), ("warning", "warning_counts")):
        counts = payload.get(group_name, {})
        if isinstance(counts, dict):
            for check, count in sorted(counts.items()):
                rows.append({"severity": severity, "check": check, "count": count})
    if not rows:
        rows.append({"severity": "info", "check": "schema_and_completion_gate", "count": 0})
    rows.extend(
        [
            {"severity": "info", "check": "audit_rows", "count": payload["audit_rows"]},
            {"severity": "info", "check": "reviewed_rows", "count": payload["reviewed_rows"]},
            {"severity": "info", "check": "pending_rows", "count": payload["pending_rows"]},
            {
                "severity": "info",
                "check": "model_assessments",
                "count": payload["model_assessments"],
            },
            {
                "severity": "info",
                "check": "reviewed_model_assessments",
                "count": payload["reviewed_model_assessments"],
            },
            {
                "severity": "info",
                "check": "pending_model_assessments",
                "count": payload["pending_model_assessments"],
            },
        ]
    )
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-sheet", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--counts-tsv", type=Path)
    parser.add_argument("--expected-rows", type=int)
    parser.add_argument("--require-complete", action="store_true")
    return parser.parse_args()


def main() -> int:
    started = time.time()
    args = parse_args()
    fieldnames, rows = read_tsv(args.audit_sheet)
    payload = validate_rows(
        fieldnames,
        rows,
        require_complete=args.require_complete,
        expected_rows=args.expected_rows,
    )
    payload["input_boundary"] = "local transcript-bearing audit sheet; do not commit input"
    payload["output_boundary"] = "aggregate-only validation counts"
    payload["runtime_seconds"] = round(time.time() - started, 4)
    assert_aggregate_safe(payload)
    output_json = args.output_json
    counts_tsv = args.counts_tsv
    if args.output_dir:
        output_json = output_json or args.output_dir / "human_audit_validation_summary.json"
        counts_tsv = counts_tsv or args.output_dir / "human_audit_validation_counts.tsv"
    if output_json:
        write_json(output_json, payload)
    if counts_tsv:
        write_tsv(
            counts_tsv,
            validation_count_rows(payload),
            ["severity", "check", "count"],
        )
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

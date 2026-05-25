#!/usr/bin/env python3
"""Create and apply local selected-300 batch response TSVs."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
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
DEFAULT_RESPONSE_DIR = DEFAULT_RUN_DIR / "artifacts" / "review_responses"
TEMPLATE_SUMMARY_NAME = "human_audit_batch_response_template_summary.json"
APPLY_SUMMARY_NAME = "human_audit_batch_response_apply_summary.json"

ROW_RESPONSE_FIELDS = [
    "reviewer_semantic_risk_label",
    "reviewer_risk_atoms",
    "reviewer_critical_atoms",
    "reviewer_asr_confusion_terms",
    "reviewer_would_asr_error_change_decision",
    "reviewer_decision_change_reason",
    "reviewer_expected_safe_action",
    "reviewer_annotation_confidence",
    "reviewer_notes",
]
MODEL_RESPONSE_FIELDS = [
    "model_reviewer_would_asr_error_change_decision",
    "model_reviewer_critical_atoms",
    "model_reviewer_expected_safe_action",
    "model_reviewer_annotation_confidence",
]
TEMPLATE_FIELDS = [
    "row_number",
    "selection_stratum",
    "asr_run_id",
    *ROW_RESPONSE_FIELDS,
    *MODEL_RESPONSE_FIELDS,
]
MODEL_FIELD_MAP = {
    "model_reviewer_would_asr_error_change_decision": "reviewer_would_asr_error_change_decision",
    "model_reviewer_critical_atoms": "reviewer_critical_atoms",
    "model_reviewer_expected_safe_action": "reviewer_expected_safe_action",
    "model_reviewer_annotation_confidence": "reviewer_annotation_confidence",
}


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), list(reader)


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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def now_label() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def parse_batch_row_numbers(batch_payload: dict[str, Any]) -> list[int]:
    row_numbers = batch_payload.get("row_numbers", [])
    if not isinstance(row_numbers, list) or not all(isinstance(item, int) for item in row_numbers):
        raise ValueError("batch summary row_numbers must be a list of integers")
    return [int(item) for item in row_numbers]


def selected_rows(
    rows: list[dict[str, str]],
    row_numbers: list[int],
) -> list[tuple[int, dict[str, str]]]:
    selected = []
    for row_number in row_numbers:
        if row_number < 1 or row_number > len(rows):
            raise ValueError(f"batch row number out of range: {row_number}")
        selected.append((row_number, rows[row_number - 1]))
    return selected


def make_template_rows(
    audit_rows: list[dict[str, str]],
    batch_payload: dict[str, Any],
) -> list[dict[str, str]]:
    row_numbers = parse_batch_row_numbers(batch_payload)
    result = []
    for row_number, row in selected_rows(audit_rows, row_numbers):
        for item in iter_model_assessments(row):
            run_id = str(item.get("asr_run_id", ""))
            if not run_id:
                continue
            result.append(
                {
                    "row_number": str(row_number),
                    "selection_stratum": row.get("selection_stratum", ""),
                    "asr_run_id": run_id,
                }
            )
    return result


def template_filename(batch_payload: dict[str, Any]) -> str:
    timestamp = now_label().replace(":", "").replace("+", "_")
    stratum = str(batch_payload.get("selection_stratum", "") or "batch")
    return f"{timestamp}_{stratum}_response_template.tsv"


def prepare_response_template(
    *,
    audit_sheet: Path,
    batch_summary: Path,
    output_dir: Path,
    response_dir: Path,
    expected_rows: int | None,
    repo_root: Path,
) -> dict[str, Any]:
    started = time.time()
    fieldnames, audit_rows = read_tsv(audit_sheet)
    validation_payload = validation.validate_rows(
        fieldnames,
        audit_rows,
        require_complete=False,
        expected_rows=expected_rows,
    )
    batch_payload = read_json(batch_summary)
    template_rows = make_template_rows(audit_rows, batch_payload)
    response_path = response_dir / template_filename(batch_payload)
    write_tsv(response_path, template_rows, TEMPLATE_FIELDS)
    row_numbers = parse_batch_row_numbers(batch_payload)
    summary = {
        "ok": validation_payload["ok"],
        "status": "response_template_prepared",
        "created_at": now_label(),
        "input_boundary": "local ignored audit sheet plus tracked batch summary",
        "output_boundary": "tracked summary only; editable response TSV is local ignored",
        "reference_transcript_policy": REFERENCE_TRANSCRIPT_POLICY,
        "remaining_review_scope": REMAINING_REVIEW_SCOPE,
        "selection_stratum": batch_payload.get("selection_stratum", ""),
        "row_numbers": row_numbers,
        "rows_in_batch": len(row_numbers),
        "response_rows": len(template_rows),
        "model_assessments_in_template": len(template_rows),
        "template_column_count": len(TEMPLATE_FIELDS),
        "local_response_template_path": repo_relative(response_path, repo_root=repo_root),
        "source_batch_summary": repo_relative(batch_summary, repo_root=repo_root),
        "next_action": (
            "Fill the local response TSV with reviewer decisions, then dry-run "
            "apply_human_audit_batch_response.py --response-sheet before using --write."
        ),
        "runtime_seconds": round(time.time() - started, 4),
    }
    assert_tracked_safe(summary)
    write_json(output_dir / TEMPLATE_SUMMARY_NAME, summary)
    return summary


def split_atoms(value: str) -> list[str]:
    atoms = []
    for item in value.replace(";", ",").replace("|", ",").split(","):
        atom = item.strip()
        if atom and atom.lower() != "none":
            atoms.append(atom)
    return atoms


def invalid_atoms(value: str) -> list[str]:
    return [atom for atom in split_atoms(value) if atom not in validation.VALID_ATOMS]


def complete_fields(row: dict[str, str], fields: list[str]) -> bool:
    return all((row.get(field) or "").strip() for field in fields)


def row_response_complete(rows: list[dict[str, str]]) -> bool:
    if not rows:
        return False
    return complete_fields(rows[0], ROW_RESPONSE_FIELDS[:-1])


def model_response_complete(row: dict[str, str]) -> bool:
    return complete_fields(row, MODEL_RESPONSE_FIELDS)


def row_consistency_errors(rows: list[dict[str, str]]) -> Counter[str]:
    errors: Counter[str] = Counter()
    if not rows:
        return errors
    for field in ROW_RESPONSE_FIELDS:
        values = {(row.get(field) or "").strip() for row in rows}
        if len(values) > 1:
            errors[f"inconsistent_{field}"] += 1
    return errors


def validate_response_values(rows: list[dict[str, str]]) -> Counter[str]:
    errors: Counter[str] = Counter()
    for row in rows:
        label = row.get("reviewer_semantic_risk_label", "").strip()
        if label and label not in validation.VALID_LABELS:
            errors["invalid_reviewer_semantic_risk_label"] += 1
        decision_change = row.get("reviewer_would_asr_error_change_decision", "").strip()
        if decision_change and decision_change not in validation.VALID_DECISION_CHANGE:
            errors["invalid_reviewer_would_asr_error_change_decision"] += 1
        safe_action = row.get("reviewer_expected_safe_action", "").strip()
        if safe_action and safe_action not in validation.VALID_SAFE_ACTION:
            errors["invalid_reviewer_expected_safe_action"] += 1
        confidence = row.get("reviewer_annotation_confidence", "").strip()
        if confidence and confidence not in validation.VALID_CONFIDENCE:
            errors["invalid_reviewer_annotation_confidence"] += 1
        errors["invalid_reviewer_risk_atom"] += len(invalid_atoms(row.get("reviewer_risk_atoms", "")))
        errors["invalid_reviewer_critical_atom"] += len(
            invalid_atoms(row.get("reviewer_critical_atoms", ""))
        )
        model_decision = row.get("model_reviewer_would_asr_error_change_decision", "").strip()
        if model_decision and model_decision not in validation.VALID_DECISION_CHANGE:
            errors["invalid_model_decision_change"] += 1
        model_safe_action = row.get("model_reviewer_expected_safe_action", "").strip()
        if model_safe_action and model_safe_action not in validation.VALID_SAFE_ACTION:
            errors["invalid_model_expected_safe_action"] += 1
        model_confidence = row.get("model_reviewer_annotation_confidence", "").strip()
        if model_confidence and model_confidence not in validation.VALID_CONFIDENCE:
            errors["invalid_model_annotation_confidence"] += 1
        errors["invalid_model_critical_atom"] += len(
            invalid_atoms(row.get("model_reviewer_critical_atoms", ""))
        )
    return Counter({key: value for key, value in errors.items() if value})


def group_response_rows(rows: list[dict[str, str]]) -> dict[int, list[dict[str, str]]]:
    grouped: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        raw = (row.get("row_number") or "").strip()
        if not raw.isdigit():
            grouped[-1].append(row)
            continue
        grouped[int(raw)].append(row)
    return grouped


def response_status(
    *,
    errors: Counter[str],
    reviewed_rows: int,
    rows_in_batch: int,
    reviewed_model_assessments: int,
    model_assessments: int,
) -> str:
    if errors:
        return "response_invalid"
    if reviewed_rows == rows_in_batch and reviewed_model_assessments == model_assessments:
        return "response_complete"
    if reviewed_rows or reviewed_model_assessments:
        return "response_partial"
    return "response_pending"


def backup_sheet(path: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"{path.stem}.batch_response.{timestamp}{path.suffix}"
    shutil.copy2(path, backup_path)
    return backup_path


def apply_responses_to_audit(
    *,
    audit_rows: list[dict[str, str]],
    grouped_response_rows: dict[int, list[dict[str, str]]],
) -> None:
    for row_number, responses in grouped_response_rows.items():
        audit_row = audit_rows[row_number - 1]
        row_response = responses[0]
        for field in ROW_RESPONSE_FIELDS:
            value = row_response.get(field)
            if value is not None:
                audit_row[field] = value
        model_updates = {
            response["asr_run_id"]: {
                target: response.get(source, "")
                for source, target in MODEL_FIELD_MAP.items()
            }
            for response in responses
        }
        updated = []
        for item in iter_model_assessments(audit_row):
            run_id = str(item.get("asr_run_id", ""))
            if run_id in model_updates:
                item = {**item, **model_updates[run_id]}
            updated.append(item)
        audit_row["reviewer_model_assessments_json"] = json.dumps(updated, ensure_ascii=False)


def write_audit_sheet(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    write_tsv(path, rows, fieldnames)


def validate_response_shape(
    *,
    response_fieldnames: list[str],
    response_rows: list[dict[str, str]],
    audit_rows: list[dict[str, str]],
    batch_payload: dict[str, Any],
) -> tuple[Counter[str], dict[int, list[dict[str, str]]], list[int]]:
    errors: Counter[str] = Counter()
    for field in TEMPLATE_FIELDS:
        if field not in response_fieldnames:
            errors["missing_response_column"] += 1
    grouped = group_response_rows(response_rows)
    if -1 in grouped:
        errors["invalid_response_row_number"] += len(grouped[-1])
    row_numbers = parse_batch_row_numbers(batch_payload)
    missing_rows = sorted(set(row_numbers) - set(grouped))
    extra_rows = sorted(set(grouped) - set(row_numbers) - {-1})
    errors["missing_batch_response_row"] += len(missing_rows)
    errors["extra_response_row_number"] += len(extra_rows)
    expected_stratum = str(batch_payload.get("selection_stratum", "") or "")
    for row_number in row_numbers:
        if row_number < 1 or row_number > len(audit_rows):
            errors["batch_row_number_out_of_range"] += 1
            continue
        responses = grouped.get(row_number, [])
        audit_model_ids = {
            str(item.get("asr_run_id", ""))
            for item in iter_model_assessments(audit_rows[row_number - 1])
            if item.get("asr_run_id")
        }
        response_model_ids = {
            str(response.get("asr_run_id", ""))
            for response in responses
            if response.get("asr_run_id")
        }
        if audit_rows[row_number - 1].get("selection_stratum", "") != expected_stratum:
            errors["batch_stratum_mismatch"] += 1
        if audit_model_ids != response_model_ids:
            errors["model_response_run_id_mismatch"] += 1
        errors.update(row_consistency_errors(responses))
    return Counter({key: value for key, value in errors.items() if value}), grouped, row_numbers


def apply_response_sheet(
    *,
    audit_sheet: Path,
    response_sheet: Path,
    batch_summary: Path,
    output_dir: Path,
    expected_rows: int | None,
    repo_root: Path,
    write: bool,
    require_complete: bool = False,
) -> dict[str, Any]:
    started = time.time()
    audit_fieldnames, audit_rows = read_tsv(audit_sheet)
    response_fieldnames, response_rows = read_tsv(response_sheet)
    batch_payload = read_json(batch_summary)
    shape_errors, grouped, row_numbers = validate_response_shape(
        response_fieldnames=response_fieldnames,
        response_rows=response_rows,
        audit_rows=audit_rows,
        batch_payload=batch_payload,
    )
    value_errors = validate_response_values(response_rows)
    errors = shape_errors + value_errors
    reviewed_rows = sum(
        1
        for row_number in row_numbers
        if row_response_complete(grouped.get(row_number, []))
    )
    reviewed_models = sum(1 for row in response_rows if model_response_complete(row))
    model_assessments = len(response_rows)
    status = response_status(
        errors=errors,
        reviewed_rows=reviewed_rows,
        rows_in_batch=len(row_numbers),
        reviewed_model_assessments=reviewed_models,
        model_assessments=model_assessments,
    )
    if require_complete and status != "response_complete":
        errors["incomplete_response"] += 1
    backup_path = ""
    if write:
        if status != "response_complete":
            errors["write_requires_response_complete"] += 1
            status = "response_invalid"
        else:
            backup_path = repo_relative(backup_sheet(audit_sheet), repo_root=repo_root)
            apply_responses_to_audit(audit_rows=audit_rows, grouped_response_rows=grouped)
            write_audit_sheet(audit_sheet, audit_fieldnames, audit_rows)
            audit_validation = validation.validate_rows(
                audit_fieldnames,
                audit_rows,
                require_complete=False,
                expected_rows=expected_rows,
            )
            if not audit_validation["ok"]:
                errors.update(Counter(audit_validation["error_counts"]))
                status = "response_invalid"
    pending_rows = len(row_numbers) - reviewed_rows
    pending_models = model_assessments - reviewed_models
    summary = {
        "ok": not errors,
        "status": status,
        "mode": "write" if write else "dry_run",
        "require_complete": require_complete,
        "input_boundary": "local ignored audit sheet plus local ignored response TSV",
        "output_boundary": "aggregate-only apply status; no private row keys or transcript text",
        "reference_transcript_policy": REFERENCE_TRANSCRIPT_POLICY,
        "remaining_review_scope": REMAINING_REVIEW_SCOPE,
        "selection_stratum": batch_payload.get("selection_stratum", ""),
        "row_numbers": row_numbers,
        "rows_in_batch": len(row_numbers),
        "reviewed_rows_in_response": reviewed_rows,
        "pending_rows_in_response": pending_rows,
        "model_assessments_in_response": model_assessments,
        "reviewed_model_assessments_in_response": reviewed_models,
        "pending_model_assessments_in_response": pending_models,
        "error_counts": dict(sorted(errors.items())),
        "backup_path": backup_path,
        "response_sheet_path": repo_relative(response_sheet, repo_root=repo_root),
        "source_batch_summary": repo_relative(batch_summary, repo_root=repo_root),
        "next_action": (
            "Fill all required row and model fields in the response TSV, rerun "
            "dry-run with --require-complete, then apply with --write once "
            "status is response_complete."
            if status != "response_complete"
            else "Rerun audit_human_review_batch_status.py; if batch_complete, refresh aggregate evidence."
        ),
        "runtime_seconds": round(time.time() - started, 4),
    }
    assert_tracked_safe(summary)
    write_json(output_dir / APPLY_SUMMARY_NAME, summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-sheet", type=Path, default=DEFAULT_AUDIT_SHEET)
    parser.add_argument("--batch-summary", type=Path, default=DEFAULT_BATCH_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--response-dir", type=Path, default=DEFAULT_RESPONSE_DIR)
    parser.add_argument("--response-sheet", type=Path)
    parser.add_argument("--write-template", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument("--expected-rows", type=int, default=30)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.write_template:
        payload = prepare_response_template(
            audit_sheet=args.audit_sheet,
            batch_summary=args.batch_summary,
            output_dir=args.output_dir,
            response_dir=args.response_dir,
            expected_rows=args.expected_rows,
            repo_root=REPO_ROOT,
        )
        print(
            json.dumps(
                {
                    "ok": payload["ok"],
                    "status": payload["status"],
                    "local_response_template_path": payload["local_response_template_path"],
                    "response_rows": payload["response_rows"],
                },
                ensure_ascii=False,
            )
        )
        return 0 if payload["ok"] else 1
    if not args.response_sheet:
        raise SystemExit("use --write-template or provide --response-sheet")
    payload = apply_response_sheet(
        audit_sheet=args.audit_sheet,
        response_sheet=args.response_sheet,
        batch_summary=args.batch_summary,
        output_dir=args.output_dir,
        expected_rows=args.expected_rows,
        repo_root=REPO_ROOT,
        write=args.write,
        require_complete=args.require_complete,
    )
    print(
        json.dumps(
            {
                "ok": payload["ok"],
                "status": payload["status"],
                "mode": payload["mode"],
                "reviewed_rows_in_response": payload["reviewed_rows_in_response"],
                "pending_rows_in_response": payload["pending_rows_in_response"],
                "reviewed_model_assessments_in_response": payload[
                    "reviewed_model_assessments_in_response"
                ],
                "pending_model_assessments_in_response": payload[
                    "pending_model_assessments_in_response"
                ],
            },
            ensure_ascii=False,
        )
    )
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

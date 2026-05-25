#!/usr/bin/env python3
"""Local helper for filling the selected human risk-atom audit sheet.

The input/output TSV is local-only and may contain transcripts. This script is
for reviewer workflow only; tracked outputs should still come from the
aggregate validators and summarizers.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from validate_human_risk_atom_audit import (
    VALID_ATOMS,
    VALID_CONFIDENCE,
    VALID_DECISION_CHANGE,
    VALID_LABELS,
    VALID_SAFE_ACTION,
    row_review_complete,
    validate_rows,
)


ROW_UPDATE_FIELDS = {
    "reviewer_verified_transcript": "verified_transcript",
    "reviewer_semantic_risk_label": "semantic_risk_label",
    "reviewer_risk_atoms": "risk_atoms",
    "reviewer_critical_atoms": "critical_atoms",
    "reviewer_asr_confusion_terms": "asr_confusion_terms",
    "reviewer_would_asr_error_change_decision": "decision_change",
    "reviewer_decision_change_reason": "decision_change_reason",
    "reviewer_expected_safe_action": "expected_safe_action",
    "reviewer_annotation_confidence": "confidence",
    "reviewer_notes": "notes",
}


def read_sheet(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), list(reader)


def write_sheet(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
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
    return json.loads(value)


def split_atoms(value: str) -> list[str]:
    return [
        atom.strip()
        for atom in value.replace("|", ",").replace(";", ",").split(",")
        if atom.strip() and atom.strip().lower() != "none"
    ]


def validate_atom_string(value: str, field_name: str) -> None:
    invalid = [atom for atom in split_atoms(value) if atom not in VALID_ATOMS]
    if invalid:
        raise ValueError(f"{field_name} contains invalid atoms: {', '.join(invalid)}")


def parse_model_review(value: str) -> dict[str, str]:
    parts = value.split(":", 4)
    if len(parts) != 5:
        raise ValueError(
            "--model-review must be asr_run_id:decision_change:critical_atoms:"
            "expected_safe_action:confidence"
        )
    asr_run_id, decision_change, critical_atoms, expected_safe_action, confidence = [
        part.strip() for part in parts
    ]
    if not asr_run_id:
        raise ValueError("model review asr_run_id is required")
    if decision_change not in VALID_DECISION_CHANGE:
        raise ValueError(f"invalid model decision_change: {decision_change}")
    if expected_safe_action not in VALID_SAFE_ACTION:
        raise ValueError(f"invalid model expected_safe_action: {expected_safe_action}")
    if confidence not in VALID_CONFIDENCE:
        raise ValueError(f"invalid model confidence: {confidence}")
    validate_atom_string(critical_atoms, "model critical_atoms")
    return {
        "asr_run_id": asr_run_id,
        "reviewer_would_asr_error_change_decision": decision_change,
        "reviewer_critical_atoms": critical_atoms,
        "reviewer_expected_safe_action": expected_safe_action,
        "reviewer_annotation_confidence": confidence,
    }


def select_row(
    rows: list[dict[str, str]],
    *,
    row_number: int | None,
    audio_id: str | None,
) -> tuple[int, dict[str, str]]:
    if row_number is None and not audio_id:
        raise ValueError("provide --row-number or --audio-id")
    if row_number is not None:
        index = row_number - 1
        if index < 0 or index >= len(rows):
            raise ValueError(f"row number out of range: {row_number}")
        return index, rows[index]
    matches = [
        (index, row)
        for index, row in enumerate(rows)
        if row.get("audio_id", "") == audio_id
    ]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one row for provided audio id, found {len(matches)}")
    return matches[0]


def pending_summary(rows: list[dict[str, str]]) -> dict[str, Any]:
    pending_numbers = [
        index + 1
        for index, row in enumerate(rows)
        if not row_review_complete(row)
    ]
    by_stratum: Counter[str] = Counter(
        row.get("selection_stratum", "") or "unknown"
        for row in rows
        if not row_review_complete(row)
    )
    return {
        "audit_rows": len(rows),
        "pending_rows": len(pending_numbers),
        "pending_row_numbers": pending_numbers,
        "pending_by_selection_stratum": dict(sorted(by_stratum.items())),
    }


def show_row(row_number: int, row: dict[str, str]) -> dict[str, Any]:
    hypotheses = parse_json_field(row.get("asr_hypotheses_json", "")) or []
    assessments = parse_json_field(row.get("reviewer_model_assessments_json", "")) or []
    return {
        "privacy_notice": "local transcript-bearing output; do not commit or paste externally",
        "row_number": row_number,
        "audio_id": row.get("audio_id", ""),
        "selection_stratum": row.get("selection_stratum", ""),
        "reference_label": row.get("reference_label", ""),
        "reference_text": row.get("reference_text", ""),
        "risk_signal_json": row.get("risk_signal_json", ""),
        "asr_hypotheses": hypotheses,
        "reviewer_model_assessments": assessments,
    }


def update_row_from_args(row: dict[str, str], args: argparse.Namespace) -> bool:
    changed = False
    for field, arg_name in ROW_UPDATE_FIELDS.items():
        value = getattr(args, arg_name)
        if value is None:
            continue
        row[field] = value
        changed = True
    if args.model_review:
        assessments = parse_json_field(row.get("reviewer_model_assessments_json", ""))
        if not isinstance(assessments, list):
            raise ValueError("reviewer_model_assessments_json is not a list")
        reviews = {item["asr_run_id"]: item for item in map(parse_model_review, args.model_review)}
        updated_run_ids: set[str] = set()
        updated_assessments = []
        for item in assessments:
            if not isinstance(item, dict):
                raise ValueError("model assessment item is not an object")
            run_id = str(item.get("asr_run_id", ""))
            if run_id in reviews:
                item = {**item, **reviews[run_id]}
                updated_run_ids.add(run_id)
            updated_assessments.append(item)
        missing = sorted(set(reviews) - updated_run_ids)
        if missing:
            raise ValueError(f"model review run id not found in row: {', '.join(missing)}")
        row["reviewer_model_assessments_json"] = json.dumps(
            updated_assessments,
            ensure_ascii=False,
        )
        changed = True
    return changed


def validate_row_args(args: argparse.Namespace) -> None:
    if args.semantic_risk_label and args.semantic_risk_label not in VALID_LABELS:
        raise ValueError(f"invalid semantic risk label: {args.semantic_risk_label}")
    if args.decision_change and args.decision_change not in VALID_DECISION_CHANGE:
        raise ValueError(f"invalid decision change: {args.decision_change}")
    if args.expected_safe_action and args.expected_safe_action not in VALID_SAFE_ACTION:
        raise ValueError(f"invalid expected safe action: {args.expected_safe_action}")
    if args.confidence and args.confidence not in VALID_CONFIDENCE:
        raise ValueError(f"invalid confidence: {args.confidence}")
    if args.risk_atoms:
        validate_atom_string(args.risk_atoms, "risk_atoms")
    if args.critical_atoms:
        validate_atom_string(args.critical_atoms, "critical_atoms")


def backup_sheet(path: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"{path.stem}.{timestamp}{path.suffix}"
    shutil.copy2(path, backup_path)
    return backup_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-sheet", type=Path, required=True)
    parser.add_argument("--row-number", type=int)
    parser.add_argument("--audio-id")
    parser.add_argument("--list-pending", action="store_true")
    parser.add_argument("--show-row", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--expected-rows", type=int)
    parser.add_argument("--verified-transcript")
    parser.add_argument("--semantic-risk-label", choices=sorted(VALID_LABELS))
    parser.add_argument("--risk-atoms")
    parser.add_argument("--critical-atoms")
    parser.add_argument("--asr-confusion-terms")
    parser.add_argument("--decision-change", choices=sorted(VALID_DECISION_CHANGE))
    parser.add_argument("--decision-change-reason")
    parser.add_argument("--expected-safe-action", choices=sorted(VALID_SAFE_ACTION))
    parser.add_argument("--confidence", choices=sorted(VALID_CONFIDENCE))
    parser.add_argument("--notes")
    parser.add_argument(
        "--model-review",
        action="append",
        default=[],
        help=(
            "Repeatable as asr_run_id:decision_change:critical_atoms:"
            "expected_safe_action:confidence"
        ),
    )
    return parser.parse_args()


def main() -> int:
    started = time.time()
    args = parse_args()
    fieldnames, rows = read_sheet(args.audit_sheet)

    if args.list_pending:
        print(json.dumps(pending_summary(rows), ensure_ascii=False, indent=2))
        return 0

    index, row = select_row(rows, row_number=args.row_number, audio_id=args.audio_id)
    if args.show_row:
        print(json.dumps(show_row(index + 1, row), ensure_ascii=False, indent=2))
        return 0

    validate_row_args(args)
    changed = update_row_from_args(row, args)
    if not changed:
        raise SystemExit("no review fields were provided; use --list-pending or --show-row")

    backup_path = ""
    if args.write:
        backup_path = str(backup_sheet(args.audit_sheet))
        write_sheet(args.audit_sheet, fieldnames, rows)

    validation = validate_rows(
        fieldnames,
        rows,
        require_complete=False,
        expected_rows=args.expected_rows,
    )
    result = {
        "ok": validation["ok"],
        "mode": "write" if args.write else "dry_run",
        "row_number": index + 1,
        "changed": changed,
        "backup_path": backup_path,
        "validation_status": validation["status"],
        "reviewed_rows": validation["reviewed_rows"],
        "pending_rows": validation["pending_rows"],
        "reviewed_model_assessments": validation["reviewed_model_assessments"],
        "pending_model_assessments": validation["pending_model_assessments"],
        "error_counts": validation["error_counts"],
        "warning_counts": validation["warning_counts"],
        "runtime_seconds": round(time.time() - started, 4),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if validation["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

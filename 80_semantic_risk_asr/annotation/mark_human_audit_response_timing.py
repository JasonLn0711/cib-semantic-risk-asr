#!/usr/bin/env python3
"""Mark local selected-300 response timing without touching reviewer labels."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
ANNOTATION_DIR = SCRIPT_PATH.parent
REPO_ROOT = SCRIPT_PATH.parents[2]
if str(ANNOTATION_DIR) not in sys.path:
    sys.path.insert(0, str(ANNOTATION_DIR))

from apply_human_audit_batch_response import (  # noqa: E402
    DEFAULT_RUN_DIR,
    REVIEW_TIMING_FIELDS,
    parse_optional_elapsed,
    parse_optional_timestamp,
    review_timing_summary,
    validate_review_timing_values,
)
from prepare_human_audit_review_batch import (  # noqa: E402
    REFERENCE_TRANSCRIPT_POLICY,
    REMAINING_REVIEW_SCOPE,
    assert_tracked_safe,
    repo_relative,
)


DEFAULT_RESPONSE_SHEET = (
    DEFAULT_RUN_DIR
    / "artifacts"
    / "review_responses"
    / "2026-05-25T220915_0800_critical_or_high_risk_missed_response_template.tsv"
)
SUMMARY_NAME = "human_audit_response_timing_summary.json"
LOG_NAME = "human_audit_response_timing_log.tsv"
LOG_FIELDS = [
    "recorded_at",
    "ok",
    "status",
    "mode",
    "action",
    "row_number",
    "force",
    "rows_in_response",
    "rows_with_timing",
    "rows_missing_timing",
    "proposed_started_at",
    "proposed_finished_at",
    "proposed_elapsed_seconds",
    "error_keys",
    "response_sheet_path",
]


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


def append_tsv(path: Path, row: dict[str, Any], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
        )
        if write_header:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now_label() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def grouped_by_row_number(rows: list[dict[str, str]]) -> dict[int, list[dict[str, str]]]:
    grouped: dict[int, list[dict[str, str]]] = {}
    for row in rows:
        try:
            row_number = int(str(row.get("row_number", "")).strip())
        except ValueError:
            continue
        grouped.setdefault(row_number, []).append(row)
    return grouped


def require_timing_fields(fieldnames: list[str]) -> list[str]:
    return [field for field in REVIEW_TIMING_FIELDS if field not in fieldnames]


def first_value(rows: list[dict[str, str]], field: str) -> str:
    for row in rows:
        value = str(row.get(field, "")).strip()
        if value:
            return value
    return ""


def row_timing_values(rows: list[dict[str, str]]) -> dict[str, str]:
    return {field: first_value(rows, field) for field in REVIEW_TIMING_FIELDS}


def row_timing_inconsistencies(rows: list[dict[str, str]]) -> list[str]:
    inconsistent = []
    for field in REVIEW_TIMING_FIELDS:
        values = {str(row.get(field, "")).strip() for row in rows}
        if len(values) > 1:
            inconsistent.append(field)
    return inconsistent


def format_elapsed(seconds: float) -> str:
    if seconds.is_integer():
        return str(int(seconds))
    return str(round(seconds, 4))


def parse_elapsed_argument(value: str | None) -> tuple[float | None, str]:
    if value is None:
        return None, ""
    try:
        elapsed = parse_optional_elapsed(value)
    except ValueError:
        return None, "invalid_elapsed_argument"
    if elapsed is None or elapsed < 0 or not math.isfinite(elapsed):
        return None, "invalid_elapsed_argument"
    return elapsed, ""


def validate_timestamp_argument(value: str | None, key: str) -> str:
    if value is None:
        return ""
    try:
        parse_optional_timestamp(value)
    except ValueError:
        return f"invalid_{key}"
    return ""


def compute_elapsed(
    *,
    started_at: str,
    finished_at: str,
    explicit_elapsed: float | None,
) -> tuple[str, str]:
    if explicit_elapsed is not None:
        return format_elapsed(explicit_elapsed), ""
    if not started_at or not finished_at:
        return "", ""
    try:
        started = parse_optional_timestamp(started_at)
        finished = parse_optional_timestamp(finished_at)
    except ValueError:
        return "", "invalid_timestamp_for_elapsed"
    if started is None or finished is None:
        return "", ""
    try:
        if finished < started:
            return "", "review_finished_before_started"
        return format_elapsed((finished - started).total_seconds()), ""
    except TypeError:
        return "", "invalid_review_timestamp_timezone_mix"


def build_proposed_timing(
    *,
    existing: dict[str, str],
    mark_start: bool,
    mark_finish: bool,
    started_at: str | None,
    finished_at: str | None,
    elapsed_seconds: str | None,
    force: bool,
) -> tuple[dict[str, str], Counter[str]]:
    errors: Counter[str] = Counter()
    proposed = dict(existing)
    explicit_elapsed, elapsed_error = parse_elapsed_argument(elapsed_seconds)
    if elapsed_error:
        errors[elapsed_error] += 1
    for value, key in ((started_at, "started_at"), (finished_at, "finished_at")):
        if error := validate_timestamp_argument(value, key):
            errors[error] += 1

    if mark_start or started_at:
        if existing["review_started_at"] and not force and started_at:
            errors["review_started_at_exists"] += 1
        elif not existing["review_started_at"] or force or started_at:
            proposed["review_started_at"] = started_at or now_label()

    if mark_finish or finished_at:
        if existing["review_finished_at"] and not force and finished_at:
            errors["review_finished_at_exists"] += 1
        elif not existing["review_finished_at"] or force or finished_at:
            proposed["review_finished_at"] = finished_at or now_label()

    if elapsed_seconds is not None:
        if existing["review_elapsed_seconds"] and not force:
            errors["review_elapsed_seconds_exists"] += 1
        elif explicit_elapsed is not None:
            proposed["review_elapsed_seconds"] = format_elapsed(explicit_elapsed)
    elif mark_finish or finished_at:
        elapsed, error = compute_elapsed(
            started_at=proposed["review_started_at"],
            finished_at=proposed["review_finished_at"],
            explicit_elapsed=None,
        )
        if error:
            errors[error] += 1
        elif elapsed and (not existing["review_elapsed_seconds"] or force):
            proposed["review_elapsed_seconds"] = elapsed

    if (mark_finish or finished_at) and not (
        proposed["review_elapsed_seconds"]
        or (proposed["review_started_at"] and proposed["review_finished_at"])
    ):
        errors["finish_requires_started_or_elapsed"] += 1
    return proposed, errors


def apply_timing_to_rows(rows: list[dict[str, str]], timing: dict[str, str]) -> None:
    for row in rows:
        for field in REVIEW_TIMING_FIELDS:
            row[field] = timing.get(field, "")


def timing_log_row(payload: dict[str, Any]) -> dict[str, Any]:
    errors = payload.get("error_counts")
    if not isinstance(errors, dict):
        errors = {}
    proposed = payload.get("proposed_timing")
    if not isinstance(proposed, dict):
        proposed = {}
    timing = payload.get("review_timing")
    if not isinstance(timing, dict):
        timing = {}
    return {
        "recorded_at": payload.get("recorded_at", ""),
        "ok": payload.get("ok", ""),
        "status": payload.get("status", ""),
        "mode": payload.get("mode", ""),
        "action": payload.get("action", ""),
        "row_number": payload.get("row_number", ""),
        "force": payload.get("force", ""),
        "rows_in_response": payload.get("rows_in_response", ""),
        "rows_with_timing": timing.get("rows_with_timing", ""),
        "rows_missing_timing": timing.get("rows_missing_timing", ""),
        "proposed_started_at": proposed.get("review_started_at", ""),
        "proposed_finished_at": proposed.get("review_finished_at", ""),
        "proposed_elapsed_seconds": proposed.get("review_elapsed_seconds", ""),
        "error_keys": ",".join(sorted(errors)),
        "response_sheet_path": payload.get("response_sheet_path", ""),
    }


def mark_response_timing(
    *,
    response_sheet: Path,
    row_number: int,
    output_dir: Path,
    summary_json: Path,
    log_tsv: Path,
    mark_start: bool,
    mark_finish: bool,
    started_at: str | None,
    finished_at: str | None,
    elapsed_seconds: str | None,
    force: bool,
    write: bool,
    repo_root: Path,
) -> dict[str, Any]:
    started = time.time()
    recorded_at = now_label()
    fieldnames, rows = read_tsv(response_sheet)
    grouped = grouped_by_row_number(rows)
    row_numbers = sorted(grouped)
    errors: Counter[str] = Counter()
    if missing := require_timing_fields(fieldnames):
        errors["missing_timing_columns"] += len(missing)
    if row_number not in grouped:
        errors["row_number_not_found"] += 1
        selected_rows: list[dict[str, str]] = []
    else:
        selected_rows = grouped[row_number]
    if not any([mark_start, mark_finish, started_at, finished_at, elapsed_seconds is not None]):
        errors["no_timing_action_requested"] += 1

    existing = row_timing_values(selected_rows) if selected_rows else {field: "" for field in REVIEW_TIMING_FIELDS}
    for field in row_timing_inconsistencies(selected_rows):
        errors[f"inconsistent_{field}"] += 1
    proposed = dict(existing)
    if selected_rows and not errors:
        proposed, timing_errors = build_proposed_timing(
            existing=existing,
            mark_start=mark_start,
            mark_finish=mark_finish,
            started_at=started_at,
            finished_at=finished_at,
            elapsed_seconds=elapsed_seconds,
            force=force,
        )
        errors.update(timing_errors)

    preview_rows = [dict(row) for row in rows]
    if selected_rows and not errors:
        preview_grouped = grouped_by_row_number(preview_rows)
        apply_timing_to_rows(preview_grouped[row_number], proposed)
    timing_errors = validate_review_timing_values(grouped_by_row_number(preview_rows), row_numbers)
    errors.update(timing_errors)
    timing = review_timing_summary(grouped_by_row_number(preview_rows), row_numbers, required=True)

    changed = selected_rows and proposed != existing
    if errors:
        status = "timing_update_invalid"
    elif not changed:
        status = "timing_unchanged"
    elif write:
        status = "timing_written"
    else:
        status = "timing_dry_run_ready"

    backup_path = ""
    if write and changed and not errors:
        backup_path = repo_relative(response_sheet.with_suffix(response_sheet.suffix + ".bak"), repo_root=repo_root)
        response_sheet.with_suffix(response_sheet.suffix + ".bak").write_text(
            response_sheet.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        write_tsv(response_sheet, preview_rows, fieldnames)

    action_parts = []
    if mark_start or started_at:
        action_parts.append("start")
    if mark_finish or finished_at:
        action_parts.append("finish")
    if elapsed_seconds is not None:
        action_parts.append("elapsed")
    payload = {
        "ok": not errors,
        "status": status,
        "mode": "write" if write else "dry_run",
        "recorded_at": recorded_at,
        "action": "+".join(action_parts),
        "input_boundary": "local ignored response TSV only",
        "output_boundary": "aggregate-only timing summary/log; no transcript text, hypotheses, or reviewer notes",
        "reference_transcript_policy": REFERENCE_TRANSCRIPT_POLICY,
        "remaining_review_scope": REMAINING_REVIEW_SCOPE,
        "row_number": row_number,
        "force": force,
        "rows_in_response": len(rows),
        "model_response_rows_for_row": len(selected_rows),
        "existing_timing": existing,
        "proposed_timing": proposed,
        "changed": bool(changed),
        "write": write,
        "review_timing": timing,
        "error_counts": dict(sorted(errors.items())),
        "response_sheet_path": repo_relative(response_sheet, repo_root=repo_root),
        "backup_path": backup_path,
        "next_action": (
            "Continue filling reviewer row/model fields, then run the session-gated strict dry-run with --require-complete --require-timing."
            if not errors
            else "Fix timing input errors and rerun this timing helper before strict closeout."
        ),
        "runtime_seconds": round(time.time() - started, 4),
    }
    assert_tracked_safe(payload)
    write_json(summary_json, payload)
    append_tsv(log_tsv, timing_log_row(payload), LOG_FIELDS)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--response-sheet", type=Path, default=DEFAULT_RESPONSE_SHEET)
    parser.add_argument("--row-number", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--summary-json", type=Path)
    parser.add_argument("--log-tsv", type=Path)
    parser.add_argument("--mark-start", action="store_true")
    parser.add_argument("--mark-finish", action="store_true")
    parser.add_argument("--started-at")
    parser.add_argument("--finished-at")
    parser.add_argument("--elapsed-seconds")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--write", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary_json = args.summary_json or args.output_dir / SUMMARY_NAME
    log_tsv = args.log_tsv or args.output_dir / LOG_NAME
    payload = mark_response_timing(
        response_sheet=args.response_sheet,
        row_number=args.row_number,
        output_dir=args.output_dir,
        summary_json=summary_json,
        log_tsv=log_tsv,
        mark_start=args.mark_start,
        mark_finish=args.mark_finish,
        started_at=args.started_at,
        finished_at=args.finished_at,
        elapsed_seconds=args.elapsed_seconds,
        force=args.force,
        write=args.write,
        repo_root=REPO_ROOT,
    )
    print(
        json.dumps(
            {
                "ok": payload["ok"],
                "status": payload["status"],
                "row_number": payload["row_number"],
                "rows_with_timing": payload["review_timing"]["rows_with_timing"],
                "rows_missing_timing": payload["review_timing"]["rows_missing_timing"],
                "output_summary": str(summary_json),
            },
            ensure_ascii=False,
        )
    )
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

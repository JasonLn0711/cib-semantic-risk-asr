#!/usr/bin/env python3
"""Audit aggregate operation records for the selected-300 human-review gate."""

from __future__ import annotations

import argparse
import csv
import json
import shlex
import sys
import time
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
ANNOTATION_DIR = SCRIPT_PATH.parent
REPO_ROOT = SCRIPT_PATH.parents[2]
if str(ANNOTATION_DIR) not in sys.path:
    sys.path.insert(0, str(ANNOTATION_DIR))

from prepare_human_audit_review_batch import (  # noqa: E402
    REFERENCE_TRANSCRIPT_POLICY,
    REMAINING_REVIEW_SCOPE,
    repo_relative,
)


DEFAULT_RUN_DIR = (
    REPO_ROOT
    / "70_experiments"
    / "runs"
    / "janus_300_high_stakes_human_audit_selection_2026_05_25"
)
SUMMARY_NAME = "human_audit_operation_record_summary.json"
TSV_NAME = "human_audit_operation_record_audit.tsv"
LOCAL_ROW_ACCESS_LOG_NAME = "human_audit_local_row_access_log.tsv"

LOG_SPECS = {
    "review_batch": "human_audit_review_batch_log.tsv",
    "preflight": "human_audit_reviewer_preflight_log.tsv",
    "session_start": "human_audit_reviewer_session_start_log.tsv",
    "strict_apply": "human_audit_batch_response_apply_log.tsv",
    "timing_helper": "human_audit_response_timing_log.tsv",
    "post_review_sequence": "human_audit_post_review_sequence_log.tsv",
}
TSV_FIELDS = [
    "operation_log_id",
    "log_path",
    "exists",
    "row_count",
    "latest_recorded_at",
    "latest_status",
    "latest_mode",
    "alignment_status",
    "alignment_note",
]
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


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TSV_FIELDS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in TSV_FIELDS})


def assert_aggregate_safe(payload: Any) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    for token in SENSITIVE_TOKENS:
        if token in text:
            raise ValueError("sensitive field token leaked into operation-record audit")


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def text_int(value: Any) -> int | None:
    try:
        return int(str(value).strip())
    except ValueError:
        return None


def csv_values(value: Any) -> list[str]:
    return [item.strip() for item in str(value).split(",") if item.strip()]


def command_arg(command: str, flag: str) -> str:
    try:
        parts = shlex.split(command)
    except ValueError:
        parts = command.split()
    for index, part in enumerate(parts):
        if part == flag and index + 1 < len(parts):
            return parts[index + 1]
    return ""


def resolve_repo_path(value: str, *, repo_root: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return repo_root / path


def expected_context(run_dir: Path) -> dict[str, Any]:
    session = read_json(run_dir / "human_audit_reviewer_session_start_summary.json")
    refresh = read_json(run_dir / "human_audit_refresh_summary.json")
    work_order = read_json(run_dir / "human_audit_review_work_order_summary.json")
    packet = session.get("current_packet") if isinstance(session.get("current_packet"), dict) else {}
    response = session.get("current_response") if isinstance(session.get("current_response"), dict) else {}
    next_operation = work_order.get("next_reviewer_operation")
    next_operation = next_operation if isinstance(next_operation, dict) else {}
    current_step = next_operation.get("current_step")
    current_step = current_step if isinstance(current_step, dict) else {}
    row_numbers = packet.get("row_numbers") if isinstance(packet.get("row_numbers"), list) else []
    return {
        "selection_stratum": packet.get("selection_stratum", "critical_or_high_risk_missed"),
        "row_numbers": [str(row) for row in row_numbers],
        "rows_in_batch": text_int(packet.get("rows_in_batch")) or 6,
        "model_assessments_in_batch": text_int(packet.get("model_assessments_in_batch")) or 18,
        "pending_rows_in_batch": text_int(session.get("pending_rows_in_batch")) or 6,
        "pending_model_assessments_in_batch": text_int(
            session.get("pending_model_assessments_in_batch")
        )
        or 18,
        "rows_missing_timing": text_int(session.get("rows_missing_timing")) or 6,
        "latest_apply_status": session.get("latest_apply_status", "response_pending"),
        "response_sheet_rows": text_int(response.get("response_sheet_rows")) or 18,
        "selected_300_pending_rows": text_int(refresh.get("pending_rows")) or 30,
        "selected_300_pending_model_assessments": text_int(
            refresh.get("pending_model_assessments")
        )
        or 90,
        "next_row_number": str(current_step.get("row_number", "1")),
        "next_work_order_id": current_step.get("work_order_id", ""),
    }


def next_local_row_access_log_status(
    *,
    run_dir: Path,
    repo_root: Path,
    next_operation: dict[str, Any],
) -> dict[str, Any]:
    local_step = next_operation.get("next_local_row_step")
    local_step = local_step if isinstance(local_step, dict) else {}
    command = str(local_step.get("command", ""))
    row_number = str(local_step.get("row_number", ""))
    access_log_arg = command_arg(command, "--access-log")
    access_log_path = resolve_repo_path(access_log_arg, repo_root=repo_root) if access_log_arg else (
        run_dir / LOCAL_ROW_ACCESS_LOG_NAME
    )
    route_ok = (
        local_step.get("step_type") == "open_local_row"
        and "review_human_risk_atom_audit.py" in command
        and "--show-row" in command
        and "--access-log" in command
        and bool(access_log_arg)
    )
    status = "planned_not_yet_recorded"
    latest_row_number = ""
    latest_access_status = ""
    latest_operation = ""
    latest_recorded_at = ""
    row_matches_next_operation = False
    safe = True
    if access_log_path.exists():
        rows = read_tsv(access_log_path)
        latest = rows[-1] if rows else {}
        try:
            assert_aggregate_safe({"latest": latest})
        except ValueError:
            safe = False
        latest_row_number = latest.get("row_number", "")
        latest_access_status = latest.get("access_status", "")
        latest_operation = latest.get("operation", "")
        latest_recorded_at = latest.get("recorded_at", "")
        row_matches_next_operation = latest_row_number == row_number
        status = "recorded" if rows and safe else "record_drift"

    payload = {
        "path": repo_relative(access_log_path, repo_root=repo_root),
        "route_ok": route_ok,
        "status": status,
        "next_row_number": row_number,
        "latest_row_number": latest_row_number,
        "latest_operation": latest_operation,
        "latest_access_status": latest_access_status,
        "latest_recorded_at": latest_recorded_at,
        "row_matches_next_operation": row_matches_next_operation,
    }
    assert_aggregate_safe(payload)
    return payload


def status_field(row: dict[str, str]) -> str:
    return row.get("status", "") or row.get("ok", "")


def mode_field(row: dict[str, str]) -> str:
    return row.get("mode", "") or row.get("action", "")


def align_log(log_id: str, latest: dict[str, str], ctx: dict[str, Any]) -> tuple[bool, str]:
    rows = ctx["rows_in_batch"]
    models = ctx["model_assessments_in_batch"]
    pending_rows = ctx["pending_rows_in_batch"]
    pending_models = ctx["pending_model_assessments_in_batch"]
    missing_timing = ctx["rows_missing_timing"]
    stratum = ctx["selection_stratum"]
    row_numbers = ctx["row_numbers"]
    next_row = ctx["next_row_number"]

    if log_id == "review_batch":
        ok = (
            latest.get("status") == "batch_prepared"
            and latest.get("selection_stratum") == stratum
            and text_int(latest.get("rows_in_batch")) == rows
            and (not row_numbers or csv_values(latest.get("row_numbers")) == row_numbers)
        )
        return ok, "batch prepared for current packet rows" if ok else "review batch log drift"
    if log_id == "preflight":
        ok = (
            truthy(latest.get("ok"))
            and latest.get("status") == "review_session_ready"
            and latest.get("handoff_freshness_status") == "handoff_fresh"
            and latest.get("latest_apply_status") == "response_pending"
            and text_int(latest.get("rows_in_batch")) == rows
            and text_int(latest.get("model_assessments_in_batch")) == models
            and truthy(latest.get("local_packet_exists"))
            and truthy(latest.get("local_response_template_exists"))
        )
        return ok, "preflight records ready local packet/template" if ok else "preflight log drift"
    if log_id == "session_start":
        ok = (
            truthy(latest.get("ok"))
            and latest.get("status") == "reviewer_session_started"
            and latest.get("preflight_status") == "review_session_ready"
            and latest.get("rubric_status") == "rubric_ready"
            and latest.get("checklist_status") == "reviewer_action_ready"
            and text_int(latest.get("rows_in_batch")) == rows
            and text_int(latest.get("pending_rows_in_batch")) == pending_rows
            and text_int(latest.get("model_assessments_in_batch")) == models
            and text_int(latest.get("pending_model_assessments_in_batch")) == pending_models
            and text_int(latest.get("rows_missing_timing")) == missing_timing
            and latest.get("latest_apply_status") == "response_pending"
        )
        return ok, "session start records current pending packet" if ok else "session-start log drift"
    if log_id == "strict_apply":
        error_keys = set(csv_values(latest.get("error_keys")))
        ok = (
            latest.get("status") == "response_pending"
            and latest.get("mode") == "dry_run"
            and truthy(latest.get("require_complete"))
            and truthy(latest.get("require_timing"))
            and text_int(latest.get("rows_in_batch")) == rows
            and text_int(latest.get("pending_rows_in_response")) == pending_rows
            and text_int(latest.get("pending_model_assessments_in_response")) == pending_models
            and text_int(latest.get("rows_missing_timing")) == missing_timing
            and {"incomplete_response", "missing_review_timing"}.issubset(error_keys)
        )
        return ok, "strict apply dry-run records current blockers" if ok else "strict-apply log drift"
    if log_id == "timing_helper":
        ok = (
            latest.get("status") in {"timing_dry_run_ready", "timing_written"}
            and latest.get("mode") in {"dry_run", "write"}
            and latest.get("row_number") == next_row
            and latest.get("action") != ""
            and text_int(latest.get("rows_in_response")) == ctx["response_sheet_rows"]
        )
        return ok, "timing helper log records the next row timing operation" if ok else "timing log drift"
    if log_id == "post_review_sequence":
        blocker_keys = set(csv_values(latest.get("blocker_keys")))
        ok = (
            latest.get("mode") == "plan_only"
            and latest.get("status") == "post_review_sequence_blocked"
            and text_int(latest.get("executed_step_count")) == 0
            and "strict_dry_run" in blocker_keys
            and "strict_human_reviewed_recovery" in blocker_keys
        )
        return ok, "sequence log records blocked plan-only state" if ok else "sequence log drift"
    return False, "unknown operation log"


def operation_record_row(
    *,
    run_dir: Path,
    repo_root: Path,
    log_id: str,
    relative_path: str,
    ctx: dict[str, Any],
) -> dict[str, Any]:
    path = run_dir / relative_path
    if not path.exists():
        return {
            "operation_log_id": log_id,
            "log_path": repo_relative(path, repo_root=repo_root),
            "exists": False,
            "row_count": 0,
            "latest_recorded_at": "",
            "latest_status": "",
            "latest_mode": "",
            "alignment_status": "fail",
            "alignment_note": "required operation log missing",
        }
    rows = read_tsv(path)
    latest = rows[-1] if rows else {}
    safe = True
    try:
        assert_aggregate_safe({"latest": latest})
    except ValueError:
        safe = False
    aligned, note = align_log(log_id, latest, ctx) if rows else (False, "operation log empty")
    passed = bool(rows) and safe and aligned
    return {
        "operation_log_id": log_id,
        "log_path": repo_relative(path, repo_root=repo_root),
        "exists": True,
        "row_count": len(rows),
        "latest_recorded_at": latest.get("recorded_at", latest.get("created_at", "")),
        "latest_status": status_field(latest),
        "latest_mode": mode_field(latest),
        "alignment_status": "pass" if passed else "fail",
        "alignment_note": note if safe else "sensitive field token found in latest log row",
    }


def build_operation_record_audit(
    *,
    run_dir: Path,
    repo_root: Path = REPO_ROOT,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    started = time.time()
    ctx = expected_context(run_dir)
    rows = [
        operation_record_row(
            run_dir=run_dir,
            repo_root=repo_root,
            log_id=log_id,
            relative_path=relative_path,
            ctx=ctx,
        )
        for log_id, relative_path in LOG_SPECS.items()
    ]
    failed = [row for row in rows if row.get("alignment_status") != "pass"]
    work_order = read_json(run_dir / "human_audit_review_work_order_summary.json")
    next_operation = work_order.get("next_reviewer_operation")
    next_operation = next_operation if isinstance(next_operation, dict) else {}
    access_log_status = next_local_row_access_log_status(
        run_dir=run_dir,
        repo_root=repo_root,
        next_operation=next_operation,
    )
    payload = {
        "ok": not failed,
        "status": "operation_records_ready" if not failed else "operation_records_drift",
        "input_boundary": "tracked aggregate summaries and append-only operation logs only",
        "output_boundary": "aggregate-only operation-record audit; no transcripts, hypotheses, or reviewer notes",
        "reference_transcript_policy": REFERENCE_TRANSCRIPT_POLICY,
        "remaining_review_scope": REMAINING_REVIEW_SCOPE,
        "required_operation_log_count": len(LOG_SPECS),
        "passed_operation_record_count": len(rows) - len(failed),
        "failed_operation_record_count": len(failed),
        "failed_operation_records": [
            {
                "operation_log_id": row["operation_log_id"],
                "alignment_note": row["alignment_note"],
            }
            for row in failed
        ],
        "current_packet": {
            "selection_stratum": ctx["selection_stratum"],
            "row_numbers": ctx["row_numbers"],
            "rows_in_batch": ctx["rows_in_batch"],
            "model_assessments_in_batch": ctx["model_assessments_in_batch"],
            "pending_rows_in_batch": ctx["pending_rows_in_batch"],
            "pending_model_assessments_in_batch": ctx["pending_model_assessments_in_batch"],
            "rows_missing_timing": ctx["rows_missing_timing"],
        },
        "next_reviewer_operation": next_operation,
        "next_local_row_access_log": access_log_status,
        "operation_records": rows,
        "runtime_seconds": round(time.time() - started, 4),
        "next_action": (
            "Continue from next_reviewer_operation; keep row-open output local-only "
            "and rerun this audit after each reviewer-session operation."
        ),
    }
    assert_aggregate_safe(payload)
    return payload, rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-tsv", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_json = args.output_json or args.run_dir / SUMMARY_NAME
    output_tsv = args.output_tsv or args.run_dir / TSV_NAME
    payload, rows = build_operation_record_audit(
        run_dir=args.run_dir,
        repo_root=args.repo_root,
    )
    write_json(output_json, payload)
    write_tsv(output_tsv, rows)
    print(
        json.dumps(
            {
                "ok": payload["ok"],
                "status": payload["status"],
                "passed_operation_record_count": payload["passed_operation_record_count"],
                "failed_operation_record_count": payload["failed_operation_record_count"],
                "output_summary": str(output_json),
            },
            ensure_ascii=False,
        )
    )
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

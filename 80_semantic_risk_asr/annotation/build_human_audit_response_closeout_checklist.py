#!/usr/bin/env python3
"""Build a repo-safe closeout checklist for the current response TSV."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
ANNOTATION_DIR = SCRIPT_PATH.parent
REPO_ROOT = SCRIPT_PATH.parents[2]
if str(ANNOTATION_DIR) not in sys.path:
    sys.path.insert(0, str(ANNOTATION_DIR))

from apply_human_audit_batch_response import (  # noqa: E402
    APPLY_LOG_SUMMARY_NAME,
    APPLY_SUMMARY_NAME,
)
from build_human_audit_reviewer_action_checklist import (  # noqa: E402
    CHECKLIST_SUMMARY_NAME,
)
from build_human_audit_reviewer_handoff import (  # noqa: E402
    DEFAULT_RUN_DIR,
    HANDOFF_SUMMARY_NAME,
)
from prepare_human_audit_review_batch import (  # noqa: E402
    REFERENCE_TRANSCRIPT_POLICY,
    REMAINING_REVIEW_SCOPE,
    assert_tracked_safe,
    repo_relative,
)
from start_human_audit_review_session import (  # noqa: E402
    SESSION_START_SUMMARY_NAME,
)


CLOSEOUT_SUMMARY_NAME = "human_audit_response_closeout_summary.json"
CLOSEOUT_TSV_NAME = "human_audit_response_closeout_checklist.tsv"
RESPONSE_GAP_TSV_NAME = "human_audit_response_gap_checklist.tsv"
RESPONSE_ACTION_ITEMS_TSV_NAME = "human_audit_response_action_items.tsv"


def read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = ["step_id", "action", "status", "evidence", "next_action"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def tsv_value(value: Any) -> Any:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return ",".join(str(item) for item in value)
    return value


def command_for_row(commands: dict[str, Any], key: str, row_number: Any) -> str:
    command_map = commands.get(key)
    if not isinstance(command_map, dict):
        return ""
    return str(command_map.get(str(row_number), "") or "")


def write_gap_tsv(
    path: Path,
    rows: list[dict[str, Any]],
    *,
    timing_commands: dict[str, Any] | None = None,
) -> None:
    fieldnames = [
        "row_number",
        "has_gap",
        "row_response_complete",
        "row_fields_missing_count",
        "missing_row_fields",
        "model_assessments_expected_count",
        "model_assessments_complete_count",
        "model_assessments_missing_count",
        "model_fields_missing_count",
        "missing_model_fields",
        "review_timing_complete",
        "review_timing_missing",
        "timing_start_write_command",
        "timing_finish_write_command",
    ]
    timing_commands = timing_commands or {}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            row_number = row.get("row_number", "")
            output = {field: tsv_value(row.get(field, "")) for field in fieldnames}
            output["timing_start_write_command"] = command_for_row(
                timing_commands,
                "timing_start_write_by_row",
                row_number,
            )
            output["timing_finish_write_command"] = command_for_row(
                timing_commands,
                "timing_finish_write_by_row",
                row_number,
            )
            writer.writerow(output)


def build_action_items(
    rows: list[dict[str, Any]],
    *,
    timing_commands: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    timing_commands = timing_commands or {}
    action_items: list[dict[str, Any]] = []
    for row in rows:
        row_number = row.get("row_number", "")
        for field_name in row.get("missing_row_fields", []):
            action_items.append(
                {
                    "action_id": f"row-{row_number}:row_field:{field_name}",
                    "row_number": row_number,
                    "action_scope": "row_field",
                    "model_assessment_slot": "",
                    "field_name": field_name,
                    "status": "pending",
                    "reviewer_action": "fill row-level response field in local response TSV",
                    "timing_start_write_command": "not_applicable",
                    "timing_finish_write_command": "not_applicable",
                }
            )
        missing_model_count = int(row.get("model_assessments_missing_count") or 0)
        for slot in range(1, missing_model_count + 1):
            for field_name in row.get("missing_model_fields", []):
                action_items.append(
                    {
                        "action_id": f"row-{row_number}:model_slot-{slot}:{field_name}",
                        "row_number": row_number,
                        "action_scope": "model_assessment_field",
                        "model_assessment_slot": slot,
                        "field_name": field_name,
                        "status": "pending",
                        "reviewer_action": (
                            "fill field for the corresponding model row in local response TSV"
                        ),
                        "timing_start_write_command": "not_applicable",
                        "timing_finish_write_command": "not_applicable",
                    }
                )
        if row.get("review_timing_missing"):
            action_items.append(
                {
                    "action_id": f"row-{row_number}:review_timing",
                    "row_number": row_number,
                    "action_scope": "review_timing",
                    "model_assessment_slot": "",
                    "field_name": "review_timing",
                    "status": "pending",
                    "reviewer_action": (
                        "record review_started_at/review_finished_at or review_elapsed_seconds"
                    ),
                    "timing_start_write_command": command_for_row(
                        timing_commands,
                        "timing_start_write_by_row",
                        row_number,
                    ),
                    "timing_finish_write_command": command_for_row(
                        timing_commands,
                        "timing_finish_write_by_row",
                        row_number,
                    ),
                }
            )
    return action_items


def action_item_overview(action_items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "total_action_items": len(action_items),
        "row_field_action_items": sum(
            1 for item in action_items if item.get("action_scope") == "row_field"
        ),
        "model_field_action_items": sum(
            1 for item in action_items if item.get("action_scope") == "model_assessment_field"
        ),
        "timing_action_items": sum(
            1 for item in action_items if item.get("action_scope") == "review_timing"
        ),
    }


def write_action_items_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "action_id",
        "row_number",
        "action_scope",
        "model_assessment_slot",
        "field_name",
        "status",
        "reviewer_action",
        "timing_start_write_command",
        "timing_finish_write_command",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: tsv_value(row.get(field, "")) for field in fieldnames})


def bool_status(condition: bool) -> str:
    return "ready" if condition else "blocked"


def error_keys(payload: dict[str, Any]) -> list[str]:
    errors = payload.get("error_counts")
    if not isinstance(errors, dict):
        return []
    return sorted(key for key, value in errors.items() if int(value or 0) > 0)


def session_gate_from_apply(apply_summary: dict[str, Any]) -> dict[str, Any]:
    gate = apply_summary.get("session_start_gate")
    return gate if isinstance(gate, dict) else {}


def build_closeout(
    *,
    run_dir: Path,
    apply_summary_path: Path,
    apply_log_summary_path: Path,
    session_start_summary_path: Path,
    action_checklist_summary_path: Path,
    handoff_summary_path: Path,
    repo_root: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    started = time.time()
    apply_summary = read_json_if_exists(apply_summary_path)
    apply_log_summary = read_json_if_exists(apply_log_summary_path)
    session_start = read_json_if_exists(session_start_summary_path)
    action_checklist = read_json_if_exists(action_checklist_summary_path)
    handoff = read_json_if_exists(handoff_summary_path)
    commands = handoff.get("commands") if isinstance(handoff.get("commands"), dict) else {}
    apply_errors = error_keys(apply_summary)
    session_gate = session_gate_from_apply(apply_summary)

    session_ready = bool(session_start.get("ok")) and session_start.get("status") in {
        "reviewer_session_started",
        "reviewer_response_complete_ready_to_write",
    }
    strict_dry_run_ran = (
        apply_summary.get("require_complete") is True
        and apply_summary.get("require_timing") is True
    )
    session_gate_ready = bool(session_gate.get("ok")) and session_gate.get("required") is True
    review_timing = (
        apply_summary.get("review_timing")
        if isinstance(apply_summary.get("review_timing"), dict)
        else {}
    )
    response_gap_overview = (
        apply_summary.get("response_gap_overview")
        if isinstance(apply_summary.get("response_gap_overview"), dict)
        else {}
    )
    response_gap_rows = (
        apply_summary.get("response_gap_summary_by_row")
        if isinstance(apply_summary.get("response_gap_summary_by_row"), list)
        else []
    )
    response_gap_timing_commands = {
        "timing_start_write_by_row": commands.get("timing_start_write_by_row", {}),
        "timing_finish_write_by_row": commands.get("timing_finish_write_by_row", {}),
    }
    response_action_items = build_action_items(
        response_gap_rows,
        timing_commands=response_gap_timing_commands,
    )
    rows_missing_timing = int(review_timing.get("rows_missing_timing") or 0)
    review_timing_complete = rows_missing_timing == 0
    response_complete = (
        apply_summary.get("ok") is True
        and apply_summary.get("status") == "response_complete"
        and review_timing_complete
        and not apply_errors
    )
    action_ready = bool(action_checklist.get("ok")) and action_checklist.get("status") in {
        "reviewer_action_ready",
        "response_complete_ready_to_write",
    }
    closeout_ready = session_ready and strict_dry_run_ran and session_gate_ready and response_complete

    rows = [
        {
            "step_id": "1",
            "action": "confirm reviewer session start gate",
            "status": bool_status(session_ready),
            "evidence": (
                f"session_status={session_start.get('status', '')}; "
                f"session_ok={session_start.get('ok', '')}"
            ),
            "next_action": "rerun start_human_audit_review_session.py if blocked",
        },
        {
            "step_id": "2",
            "action": "confirm strict dry-run was session-gated",
            "status": bool_status(strict_dry_run_ran and session_gate_ready),
            "evidence": (
                f"require_complete={apply_summary.get('require_complete', '')}; "
                f"require_timing={apply_summary.get('require_timing', '')}; "
                f"session_gate_ok={session_gate.get('ok', '')}; "
                f"rows_match={session_gate.get('row_numbers_match', '')}; "
                f"stratum_match={session_gate.get('selection_stratum_match', '')}"
            ),
            "next_action": commands.get("strict_dry_run", ""),
        },
        {
            "step_id": "3",
            "action": "confirm row-level response completion",
            "status": "complete" if int(apply_summary.get("pending_rows_in_response") or 0) == 0 else "pending",
            "evidence": (
                f"reviewed_rows={apply_summary.get('reviewed_rows_in_response', '')}; "
                f"pending_rows={apply_summary.get('pending_rows_in_response', '')}; "
                f"rows_with_row_field_gaps={response_gap_overview.get('rows_with_row_field_gaps', '')}"
            ),
            "next_action": "fill required row-level risk and decision fields in the local response TSV; use response_gap_summary_by_row for row-number-only gaps",
        },
        {
            "step_id": "4",
            "action": "confirm model-level response completion",
            "status": (
                "complete"
                if int(apply_summary.get("pending_model_assessments_in_response") or 0) == 0
                else "pending"
            ),
            "evidence": (
                f"reviewed_model_assessments={apply_summary.get('reviewed_model_assessments_in_response', '')}; "
                f"pending_model_assessments={apply_summary.get('pending_model_assessments_in_response', '')}; "
                f"rows_with_model_assessment_gaps={response_gap_overview.get('rows_with_model_assessment_gaps', '')}"
            ),
            "next_action": "fill every per-model decision-change and safe-action assessment",
        },
        {
            "step_id": "5",
            "action": "confirm required review timing completion",
            "status": "complete" if review_timing_complete else "pending",
            "evidence": (
                f"rows_with_timing={review_timing.get('rows_with_timing', '')}; "
                f"rows_missing_timing={rows_missing_timing}; "
                f"rows_with_timing_gaps={response_gap_overview.get('rows_with_timing_gaps', '')}"
            ),
            "next_action": "fill review_started_at/review_finished_at or review_elapsed_seconds and rerun strict dry-run",
        },
        {
            "step_id": "6",
            "action": "confirm strict dry-run response status",
            "status": "complete" if response_complete else "blocked",
            "evidence": (
                f"apply_status={apply_summary.get('status', '')}; "
                f"apply_ok={apply_summary.get('ok', '')}; "
                f"error_keys={','.join(apply_errors)}"
            ),
            "next_action": "rerun strict dry-run until response_complete",
        },
        {
            "step_id": "7",
            "action": "write, refresh, and prepare next batch",
            "status": "ready" if closeout_ready else "blocked_until_response_complete",
            "evidence": f"closeout_ready={closeout_ready}",
            "next_action": commands.get("write_refresh_prepare_next", ""),
        },
    ]

    blocker_keys: list[str] = []
    if not session_ready:
        blocker_keys.append("session_start_not_ready")
    if not strict_dry_run_ran:
        blocker_keys.append("strict_dry_run_missing_or_missing_timing_gate")
    if not session_gate_ready:
        blocker_keys.append("session_start_gate_not_ready")
    if not action_ready:
        blocker_keys.append("reviewer_action_not_ready")
    if not review_timing_complete:
        blocker_keys.append("review_timing_not_complete")
    if not response_complete:
        blocker_keys.append("response_not_complete")
    for key in apply_errors:
        if key not in blocker_keys:
            blocker_keys.append(key)

    status = "response_complete_ready_to_write" if closeout_ready else "response_closeout_blocked"
    payload = {
        "ok": closeout_ready,
        "status": status,
        "input_boundary": "tracked aggregate response/session summaries only",
        "output_boundary": "aggregate-only response closeout checklist; no row keys or transcript text",
        "reference_transcript_policy": REFERENCE_TRANSCRIPT_POLICY,
        "remaining_review_scope": REMAINING_REVIEW_SCOPE,
        "selection_stratum": apply_summary.get("selection_stratum", ""),
        "rows_in_batch": apply_summary.get("rows_in_batch", ""),
        "reviewed_rows_in_response": apply_summary.get("reviewed_rows_in_response", ""),
        "pending_rows_in_response": apply_summary.get("pending_rows_in_response", ""),
        "reviewed_model_assessments_in_response": apply_summary.get(
            "reviewed_model_assessments_in_response",
            "",
        ),
        "pending_model_assessments_in_response": apply_summary.get(
            "pending_model_assessments_in_response",
            "",
        ),
        "latest_apply_status": apply_summary.get("status", ""),
        "require_timing": apply_summary.get("require_timing", ""),
        "review_timing": review_timing,
        "response_gap_overview": response_gap_overview,
        "response_gap_summary_by_row": response_gap_rows,
        "response_gap_timing_commands": response_gap_timing_commands,
        "response_action_item_overview": action_item_overview(response_action_items),
        "response_action_items": response_action_items,
        "session_start_gate": session_gate,
        "apply_error_keys": apply_errors,
        "blocker_keys": blocker_keys,
        "apply_log_status": apply_log_summary.get("status", ""),
        "apply_log_entries": apply_log_summary.get("apply_log_entries", ""),
        "checklist_status": action_checklist.get("status", ""),
        "checklist": rows,
        "paper_ready_impact": (
            "No paper-readiness change. This closeout only permits response write/refresh "
            "after the current response TSV passes the session-gated strict dry-run."
        ),
        "next_concrete_action": (
            "Run the write/refresh/prepare-next command."
            if closeout_ready
            else "Fill missing local response TSV fields, rerun the session-gated strict dry-run, then rerun this closeout checklist."
        ),
        "tracked_outputs": {
            "closeout_summary": repo_relative(run_dir / CLOSEOUT_SUMMARY_NAME, repo_root=repo_root),
            "closeout_tsv": repo_relative(run_dir / CLOSEOUT_TSV_NAME, repo_root=repo_root),
            "response_gap_tsv": repo_relative(
                run_dir / RESPONSE_GAP_TSV_NAME,
                repo_root=repo_root,
            ),
            "response_action_items_tsv": repo_relative(
                run_dir / RESPONSE_ACTION_ITEMS_TSV_NAME,
                repo_root=repo_root,
            ),
            "apply_summary": repo_relative(apply_summary_path, repo_root=repo_root),
            "session_start_summary": repo_relative(
                session_start_summary_path,
                repo_root=repo_root,
            ),
        },
        "runtime_seconds": round(time.time() - started, 4),
    }
    assert_tracked_safe(payload)
    assert_tracked_safe(rows)
    return payload, rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--apply-summary", type=Path)
    parser.add_argument("--apply-log-summary", type=Path)
    parser.add_argument("--session-start-summary", type=Path)
    parser.add_argument("--action-checklist-summary", type=Path)
    parser.add_argument("--handoff-summary", type=Path)
    parser.add_argument("--summary-json", type=Path)
    parser.add_argument("--output-tsv", type=Path)
    parser.add_argument("--gap-output-tsv", type=Path)
    parser.add_argument("--action-items-output-tsv", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    apply_summary = args.apply_summary or args.run_dir / APPLY_SUMMARY_NAME
    apply_log_summary = args.apply_log_summary or args.run_dir / APPLY_LOG_SUMMARY_NAME
    session_start_summary = args.session_start_summary or args.run_dir / SESSION_START_SUMMARY_NAME
    action_checklist_summary = (
        args.action_checklist_summary or args.run_dir / CHECKLIST_SUMMARY_NAME
    )
    handoff_summary = args.handoff_summary or args.run_dir / HANDOFF_SUMMARY_NAME
    summary_json = args.summary_json or args.run_dir / CLOSEOUT_SUMMARY_NAME
    output_tsv = args.output_tsv or args.run_dir / CLOSEOUT_TSV_NAME
    gap_output_tsv = args.gap_output_tsv or args.run_dir / RESPONSE_GAP_TSV_NAME
    action_items_output_tsv = (
        args.action_items_output_tsv or args.run_dir / RESPONSE_ACTION_ITEMS_TSV_NAME
    )
    payload, rows = build_closeout(
        run_dir=args.run_dir,
        apply_summary_path=apply_summary,
        apply_log_summary_path=apply_log_summary,
        session_start_summary_path=session_start_summary,
        action_checklist_summary_path=action_checklist_summary,
        handoff_summary_path=handoff_summary,
        repo_root=REPO_ROOT,
    )
    write_json(summary_json, payload)
    write_tsv(output_tsv, rows)
    write_gap_tsv(
        gap_output_tsv,
        payload["response_gap_summary_by_row"],
        timing_commands=payload["response_gap_timing_commands"],
    )
    write_action_items_tsv(action_items_output_tsv, payload["response_action_items"])
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

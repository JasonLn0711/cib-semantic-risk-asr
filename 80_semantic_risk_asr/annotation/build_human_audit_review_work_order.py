#!/usr/bin/env python3
"""Build a repo-safe row-by-row work order for the current human-audit response."""

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

from prepare_human_audit_review_batch import (  # noqa: E402
    DEFAULT_AUDIT_SHEET,
    REFERENCE_TRANSCRIPT_POLICY,
    REMAINING_REVIEW_SCOPE,
    repo_relative,
)


WORK_ORDER_SUMMARY_NAME = "human_audit_review_work_order_summary.json"
WORK_ORDER_TSV_NAME = "human_audit_review_work_order.tsv"
LOCAL_ROW_ACCESS_LOG_NAME = "human_audit_local_row_access_log.tsv"
DEFAULT_RUN_DIR = (
    REPO_ROOT
    / "70_experiments"
    / "runs"
    / "janus_300_high_stakes_human_audit_selection_2026_05_25"
)
CLOSEOUT_SUMMARY_NAME = "human_audit_response_closeout_summary.json"
RESPONSE_ACTION_ITEMS_TSV_NAME = "human_audit_response_action_items.tsv"
HANDOFF_SUMMARY_NAME = "human_audit_reviewer_handoff_summary.json"
SESSION_START_SUMMARY_NAME = "human_audit_reviewer_session_start_summary.json"
POST_REVIEW_SEQUENCE_COMMAND = (
    ".venv/bin/python "
    "80_semantic_risk_asr/annotation/run_post_review_evidence_sequence.py "
    "--execute --allow-blocked-summary"
)

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

TSV_FIELDS = [
    "work_order_id",
    "row_number",
    "step_order",
    "step_type",
    "status",
    "pending_action_items",
    "reviewer_instruction",
    "command",
    "completion_signal",
    "privacy_boundary",
]


def read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_tsv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
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


def assert_work_order_safe(payload: Any) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    for token in SENSITIVE_TOKENS:
        if token in text:
            raise ValueError(f"sensitive field token in work order: {token}")


def row_sort_key(value: Any) -> tuple[int, str]:
    text = str(value)
    try:
        return (int(text), text)
    except ValueError:
        return (10**9, text)


def group_actions(action_items: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for item in action_items:
        row_number = str(item.get("row_number", "")).strip()
        if not row_number:
            continue
        row = grouped.setdefault(
            row_number,
            {
                "row_field_items": [],
                "model_field_items": [],
                "timing_items": [],
            },
        )
        scope = item.get("action_scope", "")
        if scope == "row_field":
            row["row_field_items"].append(item)
        elif scope == "model_assessment_field":
            row["model_field_items"].append(item)
        elif scope == "review_timing":
            row["timing_items"].append(item)
    return grouped


def unique_csv(values: list[str]) -> str:
    return ",".join(sorted({value for value in values if value}, key=row_sort_key))


def action_fields(items: list[dict[str, str]]) -> str:
    return unique_csv([item.get("field_name", "") for item in items])


def local_row_access_log_path(audit_sheet: Path) -> Path:
    if audit_sheet.parent.name == "artifacts":
        return audit_sheet.parent.parent / LOCAL_ROW_ACCESS_LOG_NAME
    return audit_sheet.parent / LOCAL_ROW_ACCESS_LOG_NAME


def local_show_row_command(audit_sheet: Path, row_number: str, *, repo_root: Path) -> str:
    audit_sheet_rel = repo_relative(audit_sheet, repo_root=repo_root)
    access_log_rel = repo_relative(local_row_access_log_path(audit_sheet), repo_root=repo_root)
    return (
        ".venv/bin/python "
        "80_semantic_risk_asr/annotation/review_human_risk_atom_audit.py "
        f"--audit-sheet {audit_sheet_rel} --row-number {row_number} --show-row "
        f"--access-log {access_log_rel}"
    )


def build_row_work_order(
    grouped_actions: dict[str, dict[str, Any]],
    *,
    audit_sheet: Path,
    handoff: dict[str, Any],
    repo_root: Path,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    commands = handoff.get("commands") if isinstance(handoff.get("commands"), dict) else {}
    for row_number in sorted(grouped_actions, key=row_sort_key):
        groups = grouped_actions[row_number]
        row_items = groups["row_field_items"]
        model_items = groups["model_field_items"]
        timing_items = groups["timing_items"]
        timing_item = timing_items[0] if timing_items else {}
        start_command = timing_item.get("timing_start_write_command") or (
            commands.get("timing_start_write_by_row", {}).get(row_number, "")
            if isinstance(commands.get("timing_start_write_by_row"), dict)
            else ""
        )
        finish_command = timing_item.get("timing_finish_write_command") or (
            commands.get("timing_finish_write_by_row", {}).get(row_number, "")
            if isinstance(commands.get("timing_finish_write_by_row"), dict)
            else ""
        )
        row_field_names = action_fields(row_items)
        model_field_names = action_fields(model_items)
        model_slots = unique_csv([item.get("model_assessment_slot", "") for item in model_items])
        rows.extend(
            [
                {
                    "work_order_id": f"row-{row_number}:01-mark-timing-start",
                    "row_number": row_number,
                    "step_order": "01",
                    "step_type": "mark_timing_start",
                    "status": "pending" if timing_items else "not_applicable",
                    "pending_action_items": len(timing_items),
                    "reviewer_instruction": "start timing immediately before opening local row content",
                    "command": start_command or "not_applicable",
                    "completion_signal": "review_started_at is present for every model row in this selected row",
                    "privacy_boundary": "tracked command only; local response TSV remains ignored",
                },
                {
                    "work_order_id": f"row-{row_number}:02-open-local-row",
                    "row_number": row_number,
                    "step_order": "02",
                    "step_type": "open_local_row",
                    "status": "local_only_required",
                    "pending_action_items": 0,
                    "reviewer_instruction": "inspect transcript-bearing row locally only",
                    "command": local_show_row_command(audit_sheet, row_number, repo_root=repo_root),
                    "completion_signal": "reviewer has inspected the local row without copying content into git",
                    "privacy_boundary": "command output is transcript-bearing and must stay local-only",
                },
                {
                    "work_order_id": f"row-{row_number}:03-fill-row-fields",
                    "row_number": row_number,
                    "step_order": "03",
                    "step_type": "fill_row_fields",
                    "status": "pending" if row_items else "complete",
                    "pending_action_items": len(row_items),
                    "reviewer_instruction": (
                        f"fill row-level fields in local response TSV: {row_field_names}"
                    ),
                    "command": "manual local response TSV entry",
                    "completion_signal": "row_response_complete becomes true in strict dry-run",
                    "privacy_boundary": "field names are tracked; reviewer values stay local until aggregate refresh",
                },
                {
                    "work_order_id": f"row-{row_number}:04-fill-model-fields",
                    "row_number": row_number,
                    "step_order": "04",
                    "step_type": "fill_model_fields",
                    "status": "pending" if model_items else "complete",
                    "pending_action_items": len(model_items),
                    "reviewer_instruction": (
                        "fill model-level fields in local response TSV "
                        f"for slots {model_slots}: {model_field_names}"
                    ),
                    "command": "manual local response TSV entry",
                    "completion_signal": "model_assessments_missing_count becomes 0 in strict dry-run",
                    "privacy_boundary": "field names and slot numbers are tracked; model judgements stay local until aggregate refresh",
                },
                {
                    "work_order_id": f"row-{row_number}:05-mark-timing-finish",
                    "row_number": row_number,
                    "step_order": "05",
                    "step_type": "mark_timing_finish",
                    "status": "pending" if timing_items else "not_applicable",
                    "pending_action_items": len(timing_items),
                    "reviewer_instruction": "finish timing immediately after row/model fields are filled",
                    "command": finish_command or "not_applicable",
                    "completion_signal": "review_finished_at or review_elapsed_seconds is present for this selected row",
                    "privacy_boundary": "tracked command only; local response TSV remains ignored",
                },
            ]
        )
    return rows


def build_packet_work_order(handoff: dict[str, Any]) -> list[dict[str, Any]]:
    commands = handoff.get("commands") if isinstance(handoff.get("commands"), dict) else {}
    return [
        {
            "work_order_id": "packet:06-strict-dry-run",
            "row_number": "packet",
            "step_order": "06",
            "step_type": "strict_dry_run",
            "status": "blocked_until_rows_complete",
            "pending_action_items": "all",
            "reviewer_instruction": "run only after every row/model/timing item is filled",
            "command": commands.get("strict_dry_run", ""),
            "completion_signal": "apply status is response_complete",
            "privacy_boundary": "aggregate-only apply summary/log are tracked",
        },
        {
            "work_order_id": "packet:07-response-closeout",
            "row_number": "packet",
            "step_order": "07",
            "step_type": "response_closeout",
            "status": "blocked_until_response_complete",
            "pending_action_items": "all",
            "reviewer_instruction": "rerun closeout after strict dry-run passes",
            "command": (
                ".venv/bin/python "
                "80_semantic_risk_asr/annotation/build_human_audit_response_closeout_checklist.py"
            ),
            "completion_signal": "closeout status is response_complete_ready_to_write",
            "privacy_boundary": "closeout is aggregate-only",
        },
        {
            "work_order_id": "packet:08-post-review-sequence-execute",
            "row_number": "packet",
            "step_order": "08",
            "step_type": "post_review_sequence_execute",
            "status": "blocked_until_closeout_ready",
            "pending_action_items": "post_closeout",
            "reviewer_instruction": (
                "execute the strict post-review sequence so write/refresh, "
                "human-reviewed recovery, post-review checklist, and objective audit stay ordered"
            ),
            "command": POST_REVIEW_SEQUENCE_COMMAND,
            "completion_signal": "post-review sequence summary records executed_step_count and stopped_step",
            "privacy_boundary": "sequence writes aggregate summaries/logs; local response TSV remains ignored",
        },
    ]


def public_step_fields(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "work_order_id": row.get("work_order_id", ""),
        "row_number": row.get("row_number", ""),
        "step_order": row.get("step_order", ""),
        "step_type": row.get("step_type", ""),
        "status": row.get("status", ""),
        "command": row.get("command", ""),
        "completion_signal": row.get("completion_signal", ""),
        "privacy_boundary": row.get("privacy_boundary", ""),
    }


def summarize_next_reviewer_operation(rows: list[dict[str, Any]]) -> dict[str, Any]:
    pending_statuses = {"pending", "local_only_required"}
    row_steps = [
        row
        for row in rows
        if row.get("row_number") != "packet"
        and str(row.get("status", "")) in pending_statuses
    ]
    if not row_steps:
        return {
            "status": "no_pending_row_steps",
            "current_step": {},
            "next_local_row_step": {},
        }

    current = row_steps[0]
    row_number = str(current.get("row_number", ""))
    local_open = next(
        (
            row
            for row in row_steps
            if str(row.get("row_number", "")) == row_number
            and row.get("step_type") == "open_local_row"
        ),
        {},
    )
    return {
        "status": "reviewer_operation_ready",
        "current_step": public_step_fields(current),
        "next_local_row_step": public_step_fields(local_open) if local_open else {},
        "note": (
            "Run current_step first. If current_step is mark_timing_start, then open "
            "next_local_row_step locally; command output is transcript-bearing and must "
            "not be copied into tracked files."
        ),
    }


def build_work_order(
    *,
    run_dir: Path,
    action_items_tsv: Path,
    closeout_summary_path: Path,
    handoff_summary_path: Path,
    session_start_summary_path: Path,
    audit_sheet: Path,
    repo_root: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    action_items = read_tsv_rows(action_items_tsv)
    closeout = read_json_if_exists(closeout_summary_path)
    handoff = read_json_if_exists(handoff_summary_path)
    session_start = read_json_if_exists(session_start_summary_path)
    grouped = group_actions(action_items)
    row_rows = build_row_work_order(grouped, audit_sheet=audit_sheet, handoff=handoff, repo_root=repo_root)
    packet_rows = build_packet_work_order(handoff)
    rows = row_rows + packet_rows
    overview = {
        "row_count": len(grouped),
        "row_work_order_steps": len(row_rows),
        "packet_work_order_steps": len(packet_rows),
        "total_work_order_steps": len(rows),
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
    closeout_overview = closeout.get("response_action_item_overview")
    closeout_overview = closeout_overview if isinstance(closeout_overview, dict) else {}
    row_numbers = sorted(grouped, key=row_sort_key)
    ok = (
        bool(action_items)
        and bool(handoff.get("ok"))
        and session_start.get("status") == "reviewer_session_started"
        and int(closeout_overview.get("total_action_items") or 0) == overview["total_action_items"]
    )
    payload = {
        "ok": ok,
        "status": "review_work_order_ready" if ok else "review_work_order_blocked",
        "input_boundary": "tracked aggregate closeout/action/handoff/session summaries only",
        "output_boundary": "aggregate-only work order; no audio IDs, transcripts, hypotheses, or reviewer notes",
        "reference_transcript_policy": REFERENCE_TRANSCRIPT_POLICY,
        "remaining_review_scope": REMAINING_REVIEW_SCOPE,
        "selection_stratum": closeout.get("selection_stratum", ""),
        "row_numbers": [int(row) if str(row).isdigit() else row for row in row_numbers],
        "review_work_order_overview": overview,
        "closeout_action_item_overview": closeout_overview,
        "session_start_status": session_start.get("status", ""),
        "handoff_status": handoff.get("status", ""),
        "handoff_freshness_status": handoff.get("freshness_status", ""),
        "next_reviewer_operation": summarize_next_reviewer_operation(rows),
        "tracked_outputs": {
            "review_work_order_summary": repo_relative(
                run_dir / WORK_ORDER_SUMMARY_NAME,
                repo_root=repo_root,
            ),
            "review_work_order_tsv": repo_relative(
                run_dir / WORK_ORDER_TSV_NAME,
                repo_root=repo_root,
            ),
            "response_action_items_tsv": repo_relative(action_items_tsv, repo_root=repo_root),
            "closeout_summary": repo_relative(closeout_summary_path, repo_root=repo_root),
        },
        "next_concrete_action": (
            "Use the work-order TSV during local review: start timing, inspect one local row, "
            "fill row/model fields, finish timing, then run strict dry-run, closeout, and "
            "the post-review sequence runner."
        ),
    }
    assert_work_order_safe({"payload": payload, "rows": rows})
    return payload, rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--action-items-tsv", type=Path)
    parser.add_argument("--closeout-summary", type=Path)
    parser.add_argument("--handoff-summary", type=Path)
    parser.add_argument("--session-start-summary", type=Path)
    parser.add_argument("--audit-sheet", type=Path, default=DEFAULT_AUDIT_SHEET)
    parser.add_argument("--summary-json", type=Path)
    parser.add_argument("--output-tsv", type=Path)
    return parser.parse_args()


def main() -> int:
    started = time.time()
    args = parse_args()
    action_items_tsv = args.action_items_tsv or args.run_dir / RESPONSE_ACTION_ITEMS_TSV_NAME
    closeout_summary = args.closeout_summary or args.run_dir / CLOSEOUT_SUMMARY_NAME
    handoff_summary = args.handoff_summary or args.run_dir / HANDOFF_SUMMARY_NAME
    session_start_summary = args.session_start_summary or args.run_dir / SESSION_START_SUMMARY_NAME
    payload, rows = build_work_order(
        run_dir=args.run_dir,
        action_items_tsv=action_items_tsv,
        closeout_summary_path=closeout_summary,
        handoff_summary_path=handoff_summary,
        session_start_summary_path=session_start_summary,
        audit_sheet=args.audit_sheet,
        repo_root=REPO_ROOT,
    )
    payload["runtime_seconds"] = round(time.time() - started, 4)
    assert_work_order_safe({"payload": payload, "rows": rows})
    summary_json = args.summary_json or args.run_dir / WORK_ORDER_SUMMARY_NAME
    output_tsv = args.output_tsv or args.run_dir / WORK_ORDER_TSV_NAME
    write_json(summary_json, payload)
    write_tsv(output_tsv, rows)
    print(
        json.dumps(
            {
                "ok": payload["ok"],
                "status": payload["status"],
                "row_count": payload["review_work_order_overview"]["row_count"],
                "total_work_order_steps": payload["review_work_order_overview"][
                    "total_work_order_steps"
                ],
                "output_json": str(summary_json),
                "output_tsv": str(output_tsv),
            },
            ensure_ascii=False,
        )
    )
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

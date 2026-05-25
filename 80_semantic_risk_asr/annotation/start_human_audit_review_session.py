#!/usr/bin/env python3
"""Start a selected-300 reviewer session with repo-safe aggregate gates."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
ANNOTATION_DIR = SCRIPT_PATH.parent
REPO_ROOT = SCRIPT_PATH.parents[2]
if str(ANNOTATION_DIR) not in sys.path:
    sys.path.insert(0, str(ANNOTATION_DIR))

from build_human_audit_reviewer_action_checklist import (  # noqa: E402
    CHECKLIST_SUMMARY_NAME,
    CHECKLIST_TSV_NAME,
    build_checklist,
    write_tsv as write_checklist_tsv,
)
from build_human_audit_reviewer_handoff import (  # noqa: E402
    DEFAULT_APPLY_LOG_SUMMARY,
    DEFAULT_APPLY_SUMMARY,
    DEFAULT_AUDIT_SHEET,
    DEFAULT_BATCH_STATUS,
    DEFAULT_BATCH_SUMMARY,
    DEFAULT_RUN_DIR,
    DEFAULT_TEMPLATE_SUMMARY,
    HANDOFF_SUMMARY_NAME,
    build_handoff,
    write_json as write_handoff_json,
)
from build_human_audit_reviewer_rubric import (  # noqa: E402
    RUBRIC_SUMMARY_NAME,
    VALUE_CONTRACT_TSV_NAME,
    build_rubric,
    write_tsv as write_rubric_tsv,
)
from preflight_human_audit_review_session import (  # noqa: E402
    PREFLIGHT_SUMMARY_NAME,
    run_preflight,
)
from prepare_human_audit_review_batch import (  # noqa: E402
    REFERENCE_TRANSCRIPT_POLICY,
    REMAINING_REVIEW_SCOPE,
    assert_tracked_safe,
    repo_relative,
)


DEFAULT_READINESS_DIR = (
    REPO_ROOT / "70_experiments" / "runs" / "postdoc_evidence_chain_2026_05_25"
)
SESSION_START_SUMMARY_NAME = "human_audit_reviewer_session_start_summary.json"
SESSION_START_LOG_NAME = "human_audit_reviewer_session_start_log.tsv"
SESSION_START_LOG_FIELDS = [
    "recorded_at",
    "ok",
    "status",
    "handoff_status",
    "preflight_status",
    "rubric_status",
    "checklist_status",
    "selection_stratum",
    "rows_in_batch",
    "pending_rows_in_batch",
    "model_assessments_in_batch",
    "pending_model_assessments_in_batch",
    "rows_missing_timing",
    "latest_apply_status",
    "error_keys",
    "session_summary",
]


def now_label() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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


def session_status(
    *,
    handoff: dict[str, Any],
    preflight: dict[str, Any],
    rubric: dict[str, Any],
    checklist: dict[str, Any],
) -> tuple[bool, str, list[str]]:
    errors: list[str] = []
    if not handoff.get("ok"):
        errors.append("handoff_not_ready")
    if not preflight.get("ok"):
        errors.append("preflight_not_ready")
    if not rubric.get("ok") or rubric.get("status") != "rubric_ready":
        errors.append("rubric_not_ready")
    if not checklist.get("ok"):
        errors.append("checklist_not_ready")

    ok = not errors
    if ok and checklist.get("status") == "response_complete_ready_to_write":
        return ok, "reviewer_response_complete_ready_to_write", errors
    if ok:
        return ok, "reviewer_session_started", errors
    return ok, "reviewer_session_blocked", errors


def build_session_payload(
    *,
    run_dir: Path,
    handoff: dict[str, Any],
    preflight: dict[str, Any],
    rubric: dict[str, Any],
    checklist: dict[str, Any],
    repo_root: Path,
    started: float,
) -> dict[str, Any]:
    ok, status, errors = session_status(
        handoff=handoff,
        preflight=preflight,
        rubric=rubric,
        checklist=checklist,
    )
    packet = handoff.get("current_packet") if isinstance(handoff.get("current_packet"), dict) else {}
    response = (
        handoff.get("current_response") if isinstance(handoff.get("current_response"), dict) else {}
    )
    commands = handoff.get("commands") if isinstance(handoff.get("commands"), dict) else {}
    payload = {
        "ok": ok,
        "status": status,
        "recorded_at": now_label(),
        "input_boundary": "tracked aggregate summaries plus local path existence checks only",
        "output_boundary": "aggregate-only reviewer session start; no row keys or transcript text",
        "reference_transcript_policy": REFERENCE_TRANSCRIPT_POLICY,
        "remaining_review_scope": REMAINING_REVIEW_SCOPE,
        "operation_sequence": [
            {
                "step": "refresh reviewer handoff",
                "status": handoff.get("status", ""),
                "ok": handoff.get("ok", ""),
            },
            {
                "step": "record preflight",
                "status": preflight.get("status", ""),
                "ok": preflight.get("ok", ""),
            },
            {
                "step": "refresh reviewer value contract",
                "status": rubric.get("status", ""),
                "ok": rubric.get("ok", ""),
            },
            {
                "step": "refresh reviewer action checklist",
                "status": checklist.get("status", ""),
                "ok": checklist.get("ok", ""),
            },
        ],
        "current_packet": {
            "selection_stratum": checklist.get(
                "selection_stratum",
                packet.get("selection_stratum", ""),
            ),
            "row_numbers": checklist.get("row_numbers", packet.get("row_numbers", [])),
            "rows_in_batch": checklist.get("rows_in_batch", packet.get("rows_in_batch", "")),
            "model_assessments_in_batch": checklist.get(
                "model_assessments_in_batch",
                packet.get("model_assessments_in_batch", ""),
            ),
            "local_packet_path": packet.get("local_packet_path", ""),
        },
        "current_response": {
            "local_response_template_path": response.get("local_response_template_path", ""),
            "response_sheet_rows": checklist.get(
                "response_sheet_rows",
                response.get("response_rows", ""),
            ),
            "template_column_count": checklist.get(
                "response_template_column_count",
                response.get("template_column_count", ""),
            ),
            "required_timing_fields": checklist.get(
                "required_timing_fields",
                response.get("required_timing_fields", []),
            ),
            "optional_timing_fields": checklist.get(
                "optional_timing_fields",
                response.get("optional_timing_fields", []),
            ),
        },
        "current_gate": {
            "rubric_status": rubric.get("status", ""),
            "validator_constants_match": rubric.get("validator_constants_match", ""),
            "checklist_status": checklist.get("status", ""),
            "pending_rows_in_batch": checklist.get("pending_rows_in_batch", ""),
            "pending_model_assessments_in_batch": checklist.get(
                "pending_model_assessments_in_batch",
                "",
            ),
            "rows_missing_timing": checklist.get("rows_missing_timing", ""),
            "latest_apply_status": checklist.get("latest_apply_status", ""),
            "apply_log_status": checklist.get("apply_log_status", ""),
            "apply_log_entries": checklist.get("apply_log_entries", ""),
            "blocker_keys": checklist.get("blocker_keys", []),
        },
        "error_keys": errors,
        "reviewer_next_actions": [
            "Open the local packet only in the local workspace; it is transcript-bearing.",
            "Fill the local response TSV row-level fields and every model-level assessment.",
            "Use timing_start_write_by_row and timing_finish_write_by_row to record per-row review timing when helper commands are preferred.",
            "Run strict_dry_run until latest_apply_status is response_complete.",
            "Run write_refresh_prepare_next only after the strict dry-run is complete.",
        ],
        "commands": {
            "strict_dry_run": commands.get("strict_dry_run", ""),
            "write_refresh_prepare_next": commands.get("write_refresh_prepare_next", ""),
            "batch_status_audit": commands.get("batch_status_audit", ""),
            "timing_start_write_by_row": commands.get("timing_start_write_by_row", {}),
            "timing_finish_write_by_row": commands.get("timing_finish_write_by_row", {}),
        },
        "paper_ready_impact": (
            "No paper-readiness change. This starts the reviewer workflow, but the selected-300 "
            "human review remains pending until required row-level fields, per-model "
            "assessments, and per-row timing are completed."
        ),
        "tracked_outputs": {
            "session_start_summary": repo_relative(
                run_dir / SESSION_START_SUMMARY_NAME,
                repo_root=repo_root,
            ),
            "session_start_log": repo_relative(
                run_dir / SESSION_START_LOG_NAME,
                repo_root=repo_root,
            ),
            "handoff_summary": repo_relative(run_dir / HANDOFF_SUMMARY_NAME, repo_root=repo_root),
            "preflight_summary": repo_relative(
                run_dir / PREFLIGHT_SUMMARY_NAME,
                repo_root=repo_root,
            ),
            "rubric_summary": repo_relative(run_dir / RUBRIC_SUMMARY_NAME, repo_root=repo_root),
            "value_contract_tsv": repo_relative(
                run_dir / VALUE_CONTRACT_TSV_NAME,
                repo_root=repo_root,
            ),
            "checklist_summary": repo_relative(
                run_dir / CHECKLIST_SUMMARY_NAME,
                repo_root=repo_root,
            ),
            "checklist_tsv": repo_relative(run_dir / CHECKLIST_TSV_NAME, repo_root=repo_root),
        },
        "runtime_seconds": round(time.time() - started, 4),
    }
    assert_tracked_safe(payload)
    return payload


def session_log_row(payload: dict[str, Any]) -> dict[str, Any]:
    packet = payload.get("current_packet") if isinstance(payload.get("current_packet"), dict) else {}
    gate = payload.get("current_gate") if isinstance(payload.get("current_gate"), dict) else {}
    outputs = payload.get("tracked_outputs") if isinstance(payload.get("tracked_outputs"), dict) else {}
    sequence = payload.get("operation_sequence")
    if not isinstance(sequence, list):
        sequence = []
    status_by_step = {
        str(item.get("step", "")): item.get("status", "")
        for item in sequence
        if isinstance(item, dict)
    }
    row = {
        "recorded_at": payload.get("recorded_at", ""),
        "ok": payload.get("ok", ""),
        "status": payload.get("status", ""),
        "handoff_status": status_by_step.get("refresh reviewer handoff", ""),
        "preflight_status": status_by_step.get("record preflight", ""),
        "rubric_status": gate.get("rubric_status", ""),
        "checklist_status": gate.get("checklist_status", ""),
        "selection_stratum": packet.get("selection_stratum", ""),
        "rows_in_batch": packet.get("rows_in_batch", ""),
        "pending_rows_in_batch": gate.get("pending_rows_in_batch", ""),
        "model_assessments_in_batch": packet.get("model_assessments_in_batch", ""),
        "pending_model_assessments_in_batch": gate.get(
            "pending_model_assessments_in_batch",
            "",
        ),
        "rows_missing_timing": gate.get("rows_missing_timing", ""),
        "latest_apply_status": gate.get("latest_apply_status", ""),
        "error_keys": ",".join(payload.get("error_keys", [])),
        "session_summary": outputs.get("session_start_summary", ""),
    }
    assert_tracked_safe(row)
    return row


def start_session(
    *,
    run_dir: Path,
    audit_sheet: Path,
    batch_summary_path: Path,
    batch_status_path: Path,
    template_summary_path: Path,
    apply_summary_path: Path,
    apply_log_summary_path: Path,
    readiness_output_dir: Path,
    expected_rows: int,
    repo_root: Path,
) -> dict[str, Any]:
    started = time.time()
    handoff_summary_path = run_dir / HANDOFF_SUMMARY_NAME
    preflight_summary_path = run_dir / PREFLIGHT_SUMMARY_NAME
    rubric_summary_path = run_dir / RUBRIC_SUMMARY_NAME
    checklist_summary_path = run_dir / CHECKLIST_SUMMARY_NAME
    checklist_tsv_path = run_dir / CHECKLIST_TSV_NAME
    session_summary_path = run_dir / SESSION_START_SUMMARY_NAME
    session_log_path = run_dir / SESSION_START_LOG_NAME

    handoff = build_handoff(
        run_dir=run_dir,
        audit_sheet=audit_sheet,
        batch_summary_path=batch_summary_path,
        batch_status_path=batch_status_path,
        template_summary_path=template_summary_path,
        apply_summary_path=apply_summary_path,
        apply_log_summary_path=apply_log_summary_path,
        readiness_output_dir=readiness_output_dir,
        expected_rows=expected_rows,
        repo_root=repo_root,
    )
    write_handoff_json(handoff_summary_path, handoff)

    preflight = run_preflight(
        run_dir=run_dir,
        handoff_summary_path=handoff_summary_path,
        batch_summary_path=batch_summary_path,
        batch_status_path=batch_status_path,
        template_summary_path=template_summary_path,
        apply_summary_path=apply_summary_path,
        apply_log_summary_path=apply_log_summary_path,
        repo_root=repo_root,
    )

    rubric, rubric_rows = build_rubric(
        run_dir=run_dir,
        action_checklist_summary=checklist_summary_path,
        repo_root=repo_root,
    )
    write_json(rubric_summary_path, rubric)
    write_rubric_tsv(run_dir / VALUE_CONTRACT_TSV_NAME, rubric_rows)

    checklist, checklist_rows = build_checklist(
        run_dir=run_dir,
        handoff_summary_path=handoff_summary_path,
        preflight_summary_path=preflight_summary_path,
        batch_summary_path=batch_summary_path,
        batch_status_path=batch_status_path,
        template_summary_path=template_summary_path,
        apply_summary_path=apply_summary_path,
        apply_log_summary_path=apply_log_summary_path,
        rubric_summary_path=rubric_summary_path,
        repo_root=repo_root,
    )
    write_json(checklist_summary_path, checklist)
    write_checklist_tsv(
        checklist_tsv_path,
        checklist_rows,
        ["step_id", "action", "status", "evidence", "next_action"],
    )

    # Refresh the value contract after the checklist so its current action gate
    # mirrors the latest start-session state.
    rubric, rubric_rows = build_rubric(
        run_dir=run_dir,
        action_checklist_summary=checklist_summary_path,
        repo_root=repo_root,
    )
    write_json(rubric_summary_path, rubric)
    write_rubric_tsv(run_dir / VALUE_CONTRACT_TSV_NAME, rubric_rows)

    payload = build_session_payload(
        run_dir=run_dir,
        handoff=handoff,
        preflight=preflight,
        rubric=rubric,
        checklist=checklist,
        repo_root=repo_root,
        started=started,
    )
    write_json(session_summary_path, payload)
    append_tsv(session_log_path, session_log_row(payload), SESSION_START_LOG_FIELDS)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--audit-sheet", type=Path, default=DEFAULT_AUDIT_SHEET)
    parser.add_argument("--batch-summary", type=Path, default=DEFAULT_BATCH_SUMMARY)
    parser.add_argument("--batch-status", type=Path, default=DEFAULT_BATCH_STATUS)
    parser.add_argument("--template-summary", type=Path, default=DEFAULT_TEMPLATE_SUMMARY)
    parser.add_argument("--apply-summary", type=Path, default=DEFAULT_APPLY_SUMMARY)
    parser.add_argument("--apply-log-summary", type=Path, default=DEFAULT_APPLY_LOG_SUMMARY)
    parser.add_argument("--readiness-output-dir", type=Path, default=DEFAULT_READINESS_DIR)
    parser.add_argument("--expected-rows", type=int, default=30)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = start_session(
        run_dir=args.run_dir,
        audit_sheet=args.audit_sheet,
        batch_summary_path=args.batch_summary,
        batch_status_path=args.batch_status,
        template_summary_path=args.template_summary,
        apply_summary_path=args.apply_summary,
        apply_log_summary_path=args.apply_log_summary,
        readiness_output_dir=args.readiness_output_dir,
        expected_rows=args.expected_rows,
        repo_root=REPO_ROOT,
    )
    print(
        json.dumps(
            {
                "ok": payload["ok"],
                "status": payload["status"],
                "selection_stratum": payload["current_packet"]["selection_stratum"],
                "rows_in_batch": payload["current_packet"]["rows_in_batch"],
                "pending_rows_in_batch": payload["current_gate"]["pending_rows_in_batch"],
                "pending_model_assessments_in_batch": payload["current_gate"][
                    "pending_model_assessments_in_batch"
                ],
                "latest_apply_status": payload["current_gate"]["latest_apply_status"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

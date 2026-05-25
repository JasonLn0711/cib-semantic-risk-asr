#!/usr/bin/env python3
"""Build a repo-safe action checklist for the current human-audit batch."""

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

from build_human_audit_reviewer_handoff import (  # noqa: E402
    DEFAULT_APPLY_LOG_SUMMARY,
    DEFAULT_APPLY_SUMMARY,
    DEFAULT_BATCH_STATUS,
    DEFAULT_BATCH_SUMMARY,
    DEFAULT_RUN_DIR,
    DEFAULT_TEMPLATE_SUMMARY,
    HANDOFF_SUMMARY_NAME,
)
from preflight_human_audit_review_session import PREFLIGHT_SUMMARY_NAME  # noqa: E402
from prepare_human_audit_review_batch import (  # noqa: E402
    REFERENCE_TRANSCRIPT_POLICY,
    REMAINING_REVIEW_SCOPE,
    assert_tracked_safe,
    repo_relative,
)


CHECKLIST_SUMMARY_NAME = "human_audit_reviewer_action_checklist_summary.json"
CHECKLIST_TSV_NAME = "human_audit_reviewer_action_checklist.tsv"
RUBRIC_SUMMARY_NAME = "human_audit_reviewer_rubric_summary.json"


def read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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


def resolve_repo_path(value: str, *, repo_root: Path) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return repo_root / path


def status_for(condition: bool, *, ready: str = "ready", blocked: str = "blocked") -> str:
    return ready if condition else blocked


def pending_status(pending: int, total: int) -> str:
    if total == 0:
        return "not_applicable"
    return "complete" if pending == 0 else "pending"


def first_present(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "":
            return value
    return ""


def current_paths_exist(handoff: dict[str, Any], *, repo_root: Path) -> dict[str, bool]:
    packet = handoff.get("current_packet") if isinstance(handoff.get("current_packet"), dict) else {}
    response = (
        handoff.get("current_response") if isinstance(handoff.get("current_response"), dict) else {}
    )
    packet_path = resolve_repo_path(str(packet.get("local_packet_path") or ""), repo_root=repo_root)
    response_path = resolve_repo_path(
        str(response.get("local_response_template_path") or ""),
        repo_root=repo_root,
    )
    return {
        "local_packet_exists": bool(packet_path and packet_path.exists()),
        "local_response_template_exists": bool(response_path and response_path.exists()),
    }


def build_checklist(
    *,
    run_dir: Path,
    handoff_summary_path: Path,
    preflight_summary_path: Path,
    batch_summary_path: Path,
    batch_status_path: Path,
    template_summary_path: Path,
    apply_summary_path: Path,
    apply_log_summary_path: Path,
    rubric_summary_path: Path,
    repo_root: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    started = time.time()
    handoff = read_json_if_exists(handoff_summary_path)
    preflight = read_json_if_exists(preflight_summary_path)
    batch_summary = read_json_if_exists(batch_summary_path)
    batch_status = read_json_if_exists(batch_status_path)
    template_summary = read_json_if_exists(template_summary_path)
    apply_summary = read_json_if_exists(apply_summary_path)
    apply_log_summary = read_json_if_exists(apply_log_summary_path)
    rubric_summary = read_json_if_exists(rubric_summary_path)

    packet = handoff.get("current_packet") if isinstance(handoff.get("current_packet"), dict) else {}
    response = (
        handoff.get("current_response") if isinstance(handoff.get("current_response"), dict) else {}
    )
    gate = handoff.get("current_gate") if isinstance(handoff.get("current_gate"), dict) else {}
    commands = handoff.get("commands") if isinstance(handoff.get("commands"), dict) else {}
    latest_apply = (
        apply_log_summary.get("latest") if isinstance(apply_log_summary.get("latest"), dict) else {}
    )
    path_checks = current_paths_exist(handoff, repo_root=repo_root)

    rows_in_batch = int(
        first_present(packet.get("rows_in_batch"), batch_summary.get("rows_in_batch"), 0)
    )
    model_assessments_in_batch = int(
        first_present(
            packet.get("model_assessments_in_batch"),
            batch_status.get("model_assessments_in_batch"),
            0,
        )
    )
    pending_rows = int(
        first_present(
            apply_summary.get("pending_rows_in_response"),
            gate.get("pending_rows_in_batch"),
            batch_status.get("pending_rows_in_batch"),
            0,
        )
    )
    pending_model_assessments = int(
        first_present(
            apply_summary.get("pending_model_assessments_in_response"),
            gate.get("pending_model_assessments_in_batch"),
            batch_status.get("pending_model_assessments_in_batch"),
            0,
        )
    )
    timing = (
        apply_summary.get("review_timing")
        if isinstance(apply_summary.get("review_timing"), dict)
        else {}
    )
    rows_missing_timing = int(
        first_present(
            timing.get("rows_missing_timing"),
            latest_apply.get("rows_missing_timing"),
            gate.get("rows_missing_timing"),
            0,
        )
    )
    latest_apply_status = str(
        first_present(
            apply_summary.get("status"),
            latest_apply.get("status"),
            gate.get("latest_apply_status"),
        )
    )
    response_complete = latest_apply_status == "response_complete"
    handoff_ready = bool(handoff.get("ok")) and handoff.get("freshness_status") == "fresh"
    preflight_ready = bool(preflight.get("ok")) and preflight.get("status") == "review_session_ready"
    rubric_ready = bool(rubric_summary.get("ok")) and rubric_summary.get("status") == "rubric_ready"
    local_paths_ready = all(path_checks.values())
    action_ready = handoff_ready and preflight_ready and rubric_ready and local_paths_ready

    rows = [
        {
            "step_id": "1",
            "action": "confirm aggregate handoff freshness",
            "status": status_for(handoff_ready),
            "evidence": (
                f"handoff_status={handoff.get('status', '')}; "
                f"freshness={handoff.get('freshness_status', '')}"
            ),
            "next_action": "rerun handoff with --check-existing before reviewer work",
        },
        {
            "step_id": "2",
            "action": "confirm local packet and response TSV exist",
            "status": status_for(local_paths_ready),
            "evidence": (
                f"local_packet_exists={path_checks['local_packet_exists']}; "
                f"local_response_template_exists={path_checks['local_response_template_exists']}"
            ),
            "next_action": "prepare or regenerate the local packet/template if missing",
        },
        {
            "step_id": "3",
            "action": "record reviewer session preflight",
            "status": status_for(preflight_ready),
            "evidence": (
                f"preflight_status={preflight.get('status', '')}; "
                f"recorded_at={preflight.get('recorded_at', '')}"
            ),
            "next_action": "rerun preflight before opening local review files",
        },
        {
            "step_id": "3b",
            "action": "confirm reviewer value contract",
            "status": status_for(rubric_ready),
            "evidence": (
                f"rubric_status={rubric_summary.get('status', '')}; "
                f"constants_match={rubric_summary.get('validator_constants_match', '')}"
            ),
            "next_action": "rerun reviewer rubric builder before filling response TSV",
        },
        {
            "step_id": "4",
            "action": "fill row-level risk and decision fields in local response TSV",
            "status": pending_status(pending_rows, rows_in_batch),
            "evidence": f"pending_rows={pending_rows}; rows_in_batch={rows_in_batch}",
            "next_action": (
                "complete row-level required fields; do not re-review ground-truth transcripts"
            ),
        },
        {
            "step_id": "5",
            "action": "fill per-model assessment fields in local response TSV",
            "status": pending_status(pending_model_assessments, model_assessments_in_batch),
            "evidence": (
                f"pending_model_assessments={pending_model_assessments}; "
                f"model_assessments_in_batch={model_assessments_in_batch}"
            ),
            "next_action": "complete model-level decision-change and safe-action assessments",
        },
        {
            "step_id": "6",
            "action": "fill optional review-time fields when available",
            "status": (
                "optional_complete"
                if rows_missing_timing == 0 and rows_in_batch
                else "optional_pending"
            ),
            "evidence": f"rows_missing_timing={rows_missing_timing}; rows_in_batch={rows_in_batch}",
            "next_action": (
                "fill review_started_at/review_finished_at/review_elapsed_seconds when available"
            ),
        },
        {
            "step_id": "7",
            "action": "run strict response dry-run",
            "status": "complete" if response_complete else "pending",
            "evidence": (
                f"latest_apply_status={latest_apply_status}; "
                f"latest_error_keys={gate.get('latest_error_keys', '')}"
            ),
            "next_action": commands.get("strict_dry_run", ""),
        },
        {
            "step_id": "8",
            "action": "write, refresh, and prepare next batch",
            "status": "ready" if response_complete else "blocked_until_response_complete",
            "evidence": f"latest_apply_status={latest_apply_status}",
            "next_action": commands.get("write_refresh_prepare_next", ""),
        },
    ]

    blocker_keys: list[str] = []
    if not handoff_ready:
        blocker_keys.append("handoff_not_ready")
    if not preflight_ready:
        blocker_keys.append("preflight_not_ready")
    if not rubric_ready:
        blocker_keys.append("rubric_not_ready")
    if not local_paths_ready:
        blocker_keys.append("local_review_artifacts_missing")
    status = "reviewer_action_ready" if action_ready else "reviewer_action_blocked"
    if action_ready and response_complete:
        status = "response_complete_ready_to_write"

    payload = {
        "ok": action_ready,
        "status": status,
        "input_boundary": "tracked aggregate summaries plus local path existence checks only",
        "output_boundary": "aggregate-only reviewer action checklist; no row keys or transcript text",
        "reference_transcript_policy": REFERENCE_TRANSCRIPT_POLICY,
        "remaining_review_scope": REMAINING_REVIEW_SCOPE,
        "selection_stratum": packet.get(
            "selection_stratum",
            batch_summary.get("selection_stratum", ""),
        ),
        "row_numbers": packet.get("row_numbers", batch_summary.get("row_numbers", [])),
        "rows_in_batch": rows_in_batch,
        "model_assessments_in_batch": model_assessments_in_batch,
        "pending_rows_in_batch": pending_rows,
        "pending_model_assessments_in_batch": pending_model_assessments,
        "rows_missing_timing": rows_missing_timing,
        "latest_apply_status": latest_apply_status,
        "response_sheet_rows": response.get(
            "response_rows",
            template_summary.get("response_rows", ""),
        ),
        "response_template_column_count": response.get(
            "template_column_count",
            template_summary.get("template_column_count", ""),
        ),
        "optional_timing_fields": response.get(
            "optional_timing_fields",
            template_summary.get("optional_timing_fields", []),
        ),
        "handoff_summary": repo_relative(handoff_summary_path, repo_root=repo_root),
        "preflight_summary": repo_relative(preflight_summary_path, repo_root=repo_root),
        "rubric_summary": repo_relative(rubric_summary_path, repo_root=repo_root),
        "rubric_status": rubric_summary.get("status", ""),
        "apply_log_status": apply_log_summary.get("status", ""),
        "apply_log_entries": apply_log_summary.get("apply_log_entries", ""),
        "blocker_keys": blocker_keys,
        "checklist": rows,
        "paper_ready_impact": (
            "No paper-readiness change. The selected-300 human review remains pending "
            "until required row-level fields and per-model assessments are completed."
        ),
        "next_concrete_action": (
            "Fill the local response TSV for the current packet, including required "
            "row-level and per-model fields, then rerun the strict dry-run."
            if action_ready and not response_complete
            else "Resolve blocker keys before reviewer work."
        ),
        "tracked_outputs": {
            "checklist_summary": repo_relative(run_dir / CHECKLIST_SUMMARY_NAME, repo_root=repo_root),
            "checklist_tsv": repo_relative(run_dir / CHECKLIST_TSV_NAME, repo_root=repo_root),
        },
        "runtime_seconds": round(time.time() - started, 4),
    }
    assert_tracked_safe(payload)
    return payload, rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--handoff-summary", type=Path)
    parser.add_argument("--preflight-summary", type=Path)
    parser.add_argument("--batch-summary", type=Path, default=DEFAULT_BATCH_SUMMARY)
    parser.add_argument("--batch-status", type=Path, default=DEFAULT_BATCH_STATUS)
    parser.add_argument("--template-summary", type=Path, default=DEFAULT_TEMPLATE_SUMMARY)
    parser.add_argument("--apply-summary", type=Path, default=DEFAULT_APPLY_SUMMARY)
    parser.add_argument("--apply-log-summary", type=Path, default=DEFAULT_APPLY_LOG_SUMMARY)
    parser.add_argument("--rubric-summary", type=Path)
    parser.add_argument("--summary-json", type=Path)
    parser.add_argument("--output-tsv", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    handoff_summary = args.handoff_summary or args.run_dir / HANDOFF_SUMMARY_NAME
    preflight_summary = args.preflight_summary or args.run_dir / PREFLIGHT_SUMMARY_NAME
    rubric_summary = args.rubric_summary or args.run_dir / RUBRIC_SUMMARY_NAME
    summary_json = args.summary_json or args.run_dir / CHECKLIST_SUMMARY_NAME
    output_tsv = args.output_tsv or args.run_dir / CHECKLIST_TSV_NAME
    payload, rows = build_checklist(
        run_dir=args.run_dir,
        handoff_summary_path=handoff_summary,
        preflight_summary_path=preflight_summary,
        batch_summary_path=args.batch_summary,
        batch_status_path=args.batch_status,
        template_summary_path=args.template_summary,
        apply_summary_path=args.apply_summary,
        apply_log_summary_path=args.apply_log_summary,
        rubric_summary_path=rubric_summary,
        repo_root=REPO_ROOT,
    )
    write_json(summary_json, payload)
    write_tsv(
        output_tsv,
        rows,
        ["step_id", "action", "status", "evidence", "next_action"],
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

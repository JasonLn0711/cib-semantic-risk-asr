#!/usr/bin/env python3
"""Record a repo-safe preflight before a selected-300 human review session."""

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

from build_human_audit_reviewer_handoff import (  # noqa: E402
    DEFAULT_APPLY_LOG_SUMMARY,
    DEFAULT_APPLY_SUMMARY,
    DEFAULT_BATCH_STATUS,
    DEFAULT_BATCH_SUMMARY,
    DEFAULT_RUN_DIR,
    DEFAULT_TEMPLATE_SUMMARY,
    HANDOFF_SUMMARY_NAME,
    check_existing_handoff,
)
from prepare_human_audit_review_batch import (  # noqa: E402
    REFERENCE_TRANSCRIPT_POLICY,
    REMAINING_REVIEW_SCOPE,
    assert_tracked_safe,
    repo_relative,
)


PREFLIGHT_SUMMARY_NAME = "human_audit_reviewer_preflight_summary.json"
PREFLIGHT_LOG_NAME = "human_audit_reviewer_preflight_log.tsv"
PREFLIGHT_LOG_FIELDS = [
    "recorded_at",
    "ok",
    "status",
    "handoff_freshness_status",
    "handoff_status",
    "latest_apply_status",
    "selection_stratum",
    "rows_in_batch",
    "model_assessments_in_batch",
    "local_packet_exists",
    "local_response_template_exists",
    "error_keys",
    "handoff_summary",
]


def now_label() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def resolve_repo_path(value: str, *, repo_root: Path) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return repo_root / path


def preflight_status(errors: list[str]) -> str:
    return "review_session_ready" if not errors else "review_session_not_ready"


def build_preflight(
    *,
    run_dir: Path,
    handoff_summary_path: Path,
    batch_summary_path: Path,
    batch_status_path: Path,
    template_summary_path: Path,
    apply_summary_path: Path,
    apply_log_summary_path: Path,
    repo_root: Path,
) -> dict[str, Any]:
    started = time.time()
    errors: list[str] = []
    freshness = check_existing_handoff(
        handoff_summary_path=handoff_summary_path,
        batch_summary_path=batch_summary_path,
        batch_status_path=batch_status_path,
        template_summary_path=template_summary_path,
        apply_summary_path=apply_summary_path,
        apply_log_summary_path=apply_log_summary_path,
        repo_root=repo_root,
    )
    if not freshness["ok"]:
        errors.append("handoff_not_fresh")
    handoff = read_json(handoff_summary_path) if handoff_summary_path.exists() else {}
    packet = handoff.get("current_packet") if isinstance(handoff.get("current_packet"), dict) else {}
    response = (
        handoff.get("current_response") if isinstance(handoff.get("current_response"), dict) else {}
    )
    gate = handoff.get("current_gate") if isinstance(handoff.get("current_gate"), dict) else {}

    local_packet_path = str(packet.get("local_packet_path") or "")
    local_response_path = str(response.get("local_response_template_path") or "")
    packet_path = resolve_repo_path(local_packet_path, repo_root=repo_root)
    response_path = resolve_repo_path(local_response_path, repo_root=repo_root)
    local_packet_exists = bool(packet_path and packet_path.exists())
    local_response_exists = bool(response_path and response_path.exists())
    if not local_packet_exists:
        errors.append("local_packet_missing")
    if not local_response_exists:
        errors.append("local_response_template_missing")

    allowed_handoff_statuses = {
        "reviewer_input_pending",
        "response_complete_ready_to_write",
        "batch_ready_for_refresh",
    }
    handoff_status = str(handoff.get("status") or "")
    if handoff_status not in allowed_handoff_statuses:
        errors.append("unexpected_handoff_status")

    payload = {
        "ok": not errors,
        "status": preflight_status(errors),
        "recorded_at": now_label(),
        "input_boundary": "tracked aggregate handoff plus local path existence checks only",
        "output_boundary": "aggregate-only review-session preflight; no row keys or transcript text",
        "reference_transcript_policy": REFERENCE_TRANSCRIPT_POLICY,
        "remaining_review_scope": REMAINING_REVIEW_SCOPE,
        "handoff_freshness": {
            "ok": freshness["ok"],
            "status": freshness["status"],
            "freshness_status": freshness["freshness_status"],
            "stale_sources": freshness["stale_sources"],
            "missing_sources": freshness["missing_sources"],
            "handoff_status": freshness.get("handoff_status", ""),
            "latest_apply_status": freshness.get("latest_apply_status", ""),
        },
        "current_packet": {
            "selection_stratum": packet.get("selection_stratum", ""),
            "row_numbers": packet.get("row_numbers", []),
            "rows_in_batch": packet.get("rows_in_batch", ""),
            "model_assessments_in_batch": packet.get("model_assessments_in_batch", ""),
            "local_packet_path": local_packet_path,
            "local_packet_exists": local_packet_exists,
        },
        "current_response": {
            "local_response_template_path": local_response_path,
            "local_response_template_exists": local_response_exists,
            "response_rows": response.get("response_rows", ""),
            "template_column_count": response.get("template_column_count", ""),
            "required_timing_fields": response.get(
                "required_timing_fields",
                response.get("optional_timing_fields", []),
            ),
            "optional_timing_fields": response.get("optional_timing_fields", []),
        },
        "current_gate": {
            "batch_status": gate.get("batch_status", ""),
            "latest_apply_status": gate.get("latest_apply_status", ""),
            "reviewed_rows_in_batch": gate.get("reviewed_rows_in_batch", ""),
            "pending_rows_in_batch": gate.get("pending_rows_in_batch", ""),
            "reviewed_model_assessments_in_batch": gate.get(
                "reviewed_model_assessments_in_batch",
                "",
            ),
            "pending_model_assessments_in_batch": gate.get(
                "pending_model_assessments_in_batch",
                "",
            ),
            "rows_with_timing": gate.get("rows_with_timing", ""),
            "rows_missing_timing": gate.get("rows_missing_timing", ""),
        },
        "error_keys": errors,
        "next_action": (
            "Open the local packet and response TSV in the local workspace, fill "
            "risk/decision/model fields plus required timing fields, then run the "
            "strict response dry-run."
            if not errors
            else "Regenerate the handoff or local review artifacts, then rerun this preflight."
        ),
        "tracked_outputs": {
            "preflight_summary": repo_relative(
                run_dir / PREFLIGHT_SUMMARY_NAME,
                repo_root=repo_root,
            ),
            "preflight_log": repo_relative(run_dir / PREFLIGHT_LOG_NAME, repo_root=repo_root),
            "handoff_summary": repo_relative(handoff_summary_path, repo_root=repo_root),
        },
        "runtime_seconds": round(time.time() - started, 4),
    }
    assert_tracked_safe(payload)
    return payload


def preflight_log_row(payload: dict[str, Any]) -> dict[str, Any]:
    freshness = payload.get("handoff_freshness")
    if not isinstance(freshness, dict):
        freshness = {}
    packet = payload.get("current_packet")
    if not isinstance(packet, dict):
        packet = {}
    response = payload.get("current_response")
    if not isinstance(response, dict):
        response = {}
    gate = payload.get("current_gate")
    if not isinstance(gate, dict):
        gate = {}
    tracked = payload.get("tracked_outputs")
    if not isinstance(tracked, dict):
        tracked = {}
    return {
        "recorded_at": payload.get("recorded_at", ""),
        "ok": payload.get("ok", ""),
        "status": payload.get("status", ""),
        "handoff_freshness_status": freshness.get("status", ""),
        "handoff_status": freshness.get("handoff_status", ""),
        "latest_apply_status": gate.get("latest_apply_status", ""),
        "selection_stratum": packet.get("selection_stratum", ""),
        "rows_in_batch": packet.get("rows_in_batch", ""),
        "model_assessments_in_batch": packet.get("model_assessments_in_batch", ""),
        "local_packet_exists": packet.get("local_packet_exists", ""),
        "local_response_template_exists": response.get("local_response_template_exists", ""),
        "error_keys": ",".join(payload.get("error_keys", [])),
        "handoff_summary": tracked.get("handoff_summary", ""),
    }


def run_preflight(
    *,
    run_dir: Path,
    handoff_summary_path: Path,
    batch_summary_path: Path,
    batch_status_path: Path,
    template_summary_path: Path,
    apply_summary_path: Path,
    apply_log_summary_path: Path,
    repo_root: Path,
) -> dict[str, Any]:
    payload = build_preflight(
        run_dir=run_dir,
        handoff_summary_path=handoff_summary_path,
        batch_summary_path=batch_summary_path,
        batch_status_path=batch_status_path,
        template_summary_path=template_summary_path,
        apply_summary_path=apply_summary_path,
        apply_log_summary_path=apply_log_summary_path,
        repo_root=repo_root,
    )
    log_row = preflight_log_row(payload)
    assert_tracked_safe(log_row)
    append_tsv(run_dir / PREFLIGHT_LOG_NAME, log_row, PREFLIGHT_LOG_FIELDS)
    write_json(run_dir / PREFLIGHT_SUMMARY_NAME, payload)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--handoff-summary", type=Path)
    parser.add_argument("--batch-summary", type=Path, default=DEFAULT_BATCH_SUMMARY)
    parser.add_argument("--batch-status", type=Path, default=DEFAULT_BATCH_STATUS)
    parser.add_argument("--template-summary", type=Path, default=DEFAULT_TEMPLATE_SUMMARY)
    parser.add_argument("--apply-summary", type=Path, default=DEFAULT_APPLY_SUMMARY)
    parser.add_argument("--apply-log-summary", type=Path, default=DEFAULT_APPLY_LOG_SUMMARY)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    handoff_summary_path = args.handoff_summary or args.run_dir / HANDOFF_SUMMARY_NAME
    payload = run_preflight(
        run_dir=args.run_dir,
        handoff_summary_path=handoff_summary_path,
        batch_summary_path=args.batch_summary,
        batch_status_path=args.batch_status,
        template_summary_path=args.template_summary,
        apply_summary_path=args.apply_summary,
        apply_log_summary_path=args.apply_log_summary,
        repo_root=REPO_ROOT,
    )
    print(
        json.dumps(
            {
                "ok": payload["ok"],
                "status": payload["status"],
                "handoff_freshness_status": payload["handoff_freshness"]["status"],
                "selection_stratum": payload["current_packet"]["selection_stratum"],
                "rows_in_batch": payload["current_packet"]["rows_in_batch"],
                "local_packet_exists": payload["current_packet"]["local_packet_exists"],
                "local_response_template_exists": payload["current_response"][
                    "local_response_template_exists"
                ],
            },
            ensure_ascii=False,
        )
    )
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

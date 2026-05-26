#!/usr/bin/env python3
"""Run or record the strict post-review evidence sequence.

The selected-300 response TSV and audit sheet are local-only. This script
records only aggregate command order, status, exit codes, and gate summaries.
"""

from __future__ import annotations

import argparse
import csv
import json
import shlex
import subprocess
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

from prepare_human_audit_review_batch import (  # noqa: E402
    REFERENCE_TRANSCRIPT_POLICY,
    REMAINING_REVIEW_SCOPE,
    assert_tracked_safe,
    repo_relative,
)


DEFAULT_RUN_DIR = (
    REPO_ROOT
    / "70_experiments"
    / "runs"
    / "janus_300_high_stakes_human_audit_selection_2026_05_25"
)
DEFAULT_READINESS_DIR = (
    REPO_ROOT / "70_experiments" / "runs" / "postdoc_evidence_chain_2026_05_25"
)
DEFAULT_HUMAN_RECOVERY_DIR = (
    REPO_ROOT
    / "70_experiments"
    / "runs"
    / "janus_300_high_stakes_recovery_human_reviewed_2026_05_26"
)

SEQUENCE_SUMMARY_NAME = "human_audit_post_review_sequence_summary.json"
SEQUENCE_TSV_NAME = "human_audit_post_review_sequence.tsv"
SEQUENCE_LOG_NAME = "human_audit_post_review_sequence_log.tsv"
CLOSEOUT_SUMMARY_NAME = "human_audit_response_closeout_summary.json"
REFRESH_SUMMARY_NAME = "human_audit_refresh_summary.json"
POST_REVIEW_SUMMARY_NAME = "human_audit_post_review_evidence_summary.json"
HUMAN_RECOVERY_SUMMARY_NAME = "summary.json"
OBJECTIVE_SUMMARY_NAME = "postdoc_objective_requirements_summary.json"

SEQUENCE_TSV_FIELDS = [
    "step_order",
    "step_type",
    "status",
    "command",
    "success_condition",
    "observed_status",
    "exit_code",
    "next_action",
    "privacy_boundary",
]
SEQUENCE_LOG_FIELDS = [
    "recorded_at",
    "mode",
    "ok",
    "status",
    "executed_step_count",
    "stopped_step",
    "blocker_keys",
    "output_summary",
]


def now_label() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


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
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def append_tsv(path: Path, row: dict[str, Any], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        if write_header:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in fieldnames})


def checklist_next_action(summary: dict[str, Any], step_id: str) -> str:
    checklist = summary.get("checklist")
    if not isinstance(checklist, list):
        return ""
    for item in checklist:
        if isinstance(item, dict) and str(item.get("step_id", "")) == step_id:
            return str(item.get("next_action", ""))
    return ""


def command(parts: list[str]) -> str:
    return " ".join(parts)


def human_recovery_ready(payload: dict[str, Any]) -> bool:
    return (
        payload.get("ok") is True
        and payload.get("evidence_mode") == "human_reviewed"
        and isinstance(payload.get("policies"), dict)
        and len(payload.get("policies", {})) >= 5
    )


def refresh_complete(payload: dict[str, Any]) -> bool:
    return (
        payload.get("status") == "review_complete"
        and int(payload.get("pending_rows") or 0) == 0
        and int(payload.get("pending_model_assessments") or 0) == 0
    )


def closeout_ready(payload: dict[str, Any]) -> bool:
    return payload.get("ok") is True and payload.get("status") == "response_complete_ready_to_write"


def post_review_ready(payload: dict[str, Any]) -> bool:
    return payload.get("ok") is True and payload.get("status") == "post_review_evidence_ready"


def objective_ready(payload: dict[str, Any]) -> bool:
    return payload.get("ok") is True and payload.get("objective_requirements_ready") is True


def make_sequence_rows(
    *,
    closeout: dict[str, Any],
    refresh: dict[str, Any],
    human_recovery: dict[str, Any],
    post_review: dict[str, Any],
    objective: dict[str, Any],
) -> list[dict[str, Any]]:
    closeout_ok = closeout_ready(closeout)
    refresh_ok = refresh_complete(refresh)
    recovery_ok = human_recovery_ready(human_recovery)
    post_review_ok = post_review_ready(post_review)
    objective_ok = objective_ready(objective)
    strict_dry_run = checklist_next_action(closeout, "2")
    write_refresh = checklist_next_action(closeout, "7")
    return [
        {
            "step_order": 1,
            "step_type": "strict_dry_run",
            "status": "ready" if closeout_ok else "blocked_until_response_fields_complete",
            "command": strict_dry_run,
            "success_condition": "apply summary status is response_complete",
            "observed_status": closeout.get("status", ""),
            "next_action": "rerun strict dry-run after row/model/timing fields are filled",
            "privacy_boundary": "aggregate-only apply summary/log are tracked",
        },
        {
            "step_order": 2,
            "step_type": "response_closeout",
            "status": "ready" if closeout_ok else "blocked_until_strict_dry_run_complete",
            "command": command(
                [".venv/bin/python", "80_semantic_risk_asr/annotation/build_human_audit_response_closeout_checklist.py"]
            ),
            "success_condition": "closeout status is response_complete_ready_to_write",
            "observed_status": closeout.get("status", ""),
            "next_action": "rerun closeout after strict dry-run passes",
            "privacy_boundary": "aggregate-only closeout summary/checklist are tracked",
        },
        {
            "step_order": 3,
            "step_type": "write_refresh_prepare_next",
            "status": "ready" if closeout_ok else "blocked_until_response_closeout_ready",
            "command": write_refresh,
            "success_condition": "local audit sheet written and aggregate refresh runs",
            "observed_status": refresh.get("status", ""),
            "next_action": "write local response only after closeout is ready",
            "privacy_boundary": "write touches ignored local sheet; tracked outputs remain aggregate-only",
        },
        {
            "step_order": 4,
            "step_type": "human_audit_refresh",
            "status": "ready" if refresh_ok else "blocked_until_write_refresh_complete",
            "command": command(
                [".venv/bin/python", "80_semantic_risk_asr/annotation/refresh_human_audit_evidence.py"]
            ),
            "success_condition": "refresh status is review_complete and pending counts are zero",
            "observed_status": refresh.get("status", ""),
            "next_action": "refresh after each write; continue batches while review_pending",
            "privacy_boundary": "aggregate-only refresh outputs are tracked",
        },
        {
            "step_order": 5,
            "step_type": "strict_human_reviewed_recovery",
            "status": "ready" if recovery_ok else "blocked_until_review_complete",
            "command": command(
                [".venv/bin/python", "80_semantic_risk_asr/recovery/evaluate_human_reviewed_recovery_policies.py"]
            ),
            "success_condition": "human recovery evidence_mode is human_reviewed with five policies",
            "observed_status": human_recovery.get("status", ""),
            "next_action": "run only after all selected-300 row/model/timing review is complete",
            "privacy_boundary": "aggregate-only recovery summary/comparison are tracked",
        },
        {
            "step_order": 6,
            "step_type": "post_review_checklist",
            "status": "ready" if recovery_ok else "blocked_until_human_recovery_ready",
            "command": command(
                [".venv/bin/python", "80_semantic_risk_asr/annotation/build_post_review_evidence_checklist.py"]
            ),
            "success_condition": "post-review evidence status is post_review_evidence_ready",
            "observed_status": post_review.get("status", ""),
            "next_action": "rerun checklist after strict human-reviewed recovery passes",
            "privacy_boundary": "aggregate-only paper-claim gate is tracked",
        },
        {
            "step_order": 7,
            "step_type": "objective_requirements_audit",
            "status": "ready" if objective_ok else "blocked_until_post_review_ready",
            "command": command(
                [".venv/bin/python", "80_semantic_risk_asr/scoring/audit_postdoc_objective_requirements.py"]
            ),
            "success_condition": "objective_requirements_ready is true",
            "observed_status": str(objective.get("objective_requirements_ready", "")),
            "next_action": "rerun objective audit before declaring goal complete",
            "privacy_boundary": "aggregate-only objective audit is tracked",
        },
    ]


def blocker_keys_from_rows(rows: list[dict[str, Any]]) -> list[str]:
    blockers = []
    for row in rows:
        if str(row.get("status", "")).startswith("blocked"):
            blockers.append(str(row.get("step_type", "")))
    return blockers


def run_command(command_text: str, *, repo_root: Path) -> int:
    if not command_text:
        return 1
    result = subprocess.run(
        shlex.split(command_text),
        cwd=repo_root,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return int(result.returncode)


def execute_sequence(
    *,
    rows: list[dict[str, Any]],
    repo_root: Path,
    closeout_summary_path: Path,
    refresh_summary_path: Path,
    human_recovery_summary_path: Path,
    post_review_summary_path: Path,
    objective_summary_path: Path,
) -> tuple[list[dict[str, Any]], str]:
    executed_rows: list[dict[str, Any]] = []
    stopped_step = ""
    for row in rows:
        step_type = str(row.get("step_type", ""))
        if step_type in {"strict_dry_run", "response_closeout", "write_refresh_prepare_next"}:
            if str(row.get("status", "")).startswith("blocked"):
                stopped_step = step_type
                break
        elif step_type == "strict_human_reviewed_recovery":
            if not refresh_complete(read_json_if_exists(refresh_summary_path)):
                stopped_step = step_type
                break
        elif step_type == "post_review_checklist":
            if not human_recovery_ready(read_json_if_exists(human_recovery_summary_path)):
                stopped_step = step_type
                break
        elif step_type == "objective_requirements_audit":
            if not post_review_ready(read_json_if_exists(post_review_summary_path)):
                stopped_step = step_type
                break

        exit_code = run_command(str(row.get("command", "")), repo_root=repo_root)
        row = {**row, "exit_code": exit_code}
        executed_rows.append(row)
        if exit_code != 0:
            if not (
                step_type == "human_audit_refresh"
                and refresh_complete(read_json_if_exists(refresh_summary_path))
            ):
                stopped_step = step_type
                break

        if step_type == "response_closeout" and not closeout_ready(read_json_if_exists(closeout_summary_path)):
            stopped_step = step_type
            break
        if step_type == "human_audit_refresh" and not refresh_complete(read_json_if_exists(refresh_summary_path)):
            stopped_step = step_type
            break
        if step_type == "strict_human_reviewed_recovery" and not human_recovery_ready(
            read_json_if_exists(human_recovery_summary_path)
        ):
            stopped_step = step_type
            break
        if step_type == "post_review_checklist" and not post_review_ready(read_json_if_exists(post_review_summary_path)):
            stopped_step = step_type
            break
        if step_type == "objective_requirements_audit" and not objective_ready(
            read_json_if_exists(objective_summary_path)
        ):
            stopped_step = step_type
            break
    return executed_rows, stopped_step


def build_sequence(
    *,
    run_dir: Path,
    readiness_dir: Path,
    human_recovery_dir: Path,
    closeout_summary_path: Path,
    refresh_summary_path: Path,
    human_recovery_summary_path: Path,
    post_review_summary_path: Path,
    objective_summary_path: Path,
    repo_root: Path,
    execute: bool,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    started = time.time()
    closeout = read_json_if_exists(closeout_summary_path)
    refresh = read_json_if_exists(refresh_summary_path)
    human_recovery = read_json_if_exists(human_recovery_summary_path)
    post_review = read_json_if_exists(post_review_summary_path)
    objective = read_json_if_exists(objective_summary_path)
    rows = make_sequence_rows(
        closeout=closeout,
        refresh=refresh,
        human_recovery=human_recovery,
        post_review=post_review,
        objective=objective,
    )
    executed_rows: list[dict[str, Any]] = []
    stopped_step = ""
    if execute:
        executed_rows, stopped_step = execute_sequence(
            rows=rows,
            repo_root=repo_root,
            closeout_summary_path=closeout_summary_path,
            refresh_summary_path=refresh_summary_path,
            human_recovery_summary_path=human_recovery_summary_path,
            post_review_summary_path=post_review_summary_path,
            objective_summary_path=objective_summary_path,
        )
        closeout = read_json_if_exists(closeout_summary_path)
        refresh = read_json_if_exists(refresh_summary_path)
        human_recovery = read_json_if_exists(human_recovery_summary_path)
        post_review = read_json_if_exists(post_review_summary_path)
        objective = read_json_if_exists(objective_summary_path)
        rows = make_sequence_rows(
            closeout=closeout,
            refresh=refresh,
            human_recovery=human_recovery,
            post_review=post_review,
            objective=objective,
        )
    blockers = blocker_keys_from_rows(rows)
    all_ready = not blockers and objective_ready(objective)
    ready_to_execute = closeout_ready(closeout) and not all_ready
    if all_ready:
        status = "post_review_sequence_complete"
    elif ready_to_execute:
        status = "post_review_sequence_ready_to_execute"
    else:
        status = "post_review_sequence_blocked"
    payload = {
        "ok": all_ready,
        "status": status,
        "mode": "execute" if execute else "plan_only",
        "input_boundary": "tracked aggregate closeout, refresh, recovery, checklist, and objective summaries",
        "output_boundary": "aggregate-only post-review sequence status; no row keys or transcript text",
        "reference_transcript_policy": REFERENCE_TRANSCRIPT_POLICY,
        "remaining_review_scope": REMAINING_REVIEW_SCOPE,
        "closeout_ready": closeout_ready(closeout),
        "refresh_complete": refresh_complete(refresh),
        "human_recovery_ready": human_recovery_ready(human_recovery),
        "post_review_ready": post_review_ready(post_review),
        "objective_requirements_ready": objective_ready(objective),
        "blocker_keys": blockers,
        "executed_step_count": len(executed_rows),
        "stopped_step": stopped_step,
        "execute_safety_policy": (
            "In --execute mode, stop before any blocked strict_dry_run, "
            "response_closeout, write_refresh_prepare_next, strict_human_reviewed_recovery, "
            "post_review_checklist, or objective_requirements_audit step; record "
            "executed_step_count and stopped_step in the aggregate summary/log."
        ),
        "sequence": rows,
        "tracked_outputs": {
            "summary": repo_relative(run_dir / SEQUENCE_SUMMARY_NAME, repo_root=repo_root),
            "sequence_tsv": repo_relative(run_dir / SEQUENCE_TSV_NAME, repo_root=repo_root),
            "sequence_log": repo_relative(run_dir / SEQUENCE_LOG_NAME, repo_root=repo_root),
            "readiness_dir": repo_relative(readiness_dir, repo_root=repo_root),
            "human_recovery_dir": repo_relative(human_recovery_dir, repo_root=repo_root),
        },
        "next_concrete_action": (
            "Complete selected-300 response closeout first, then rerun this sequence with --execute."
            if not closeout_ready(closeout)
            else (
                "Run this sequence with --execute; it will stop at the first still-pending aggregate gate."
                if not all_ready
                else "All post-review sequence gates are complete; rerun objective audit before final claim review."
            )
        ),
        "runtime_seconds": round(time.time() - started, 4),
    }
    assert_tracked_safe(payload)
    assert_tracked_safe(rows)
    return payload, rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--readiness-dir", type=Path, default=DEFAULT_READINESS_DIR)
    parser.add_argument("--human-recovery-dir", type=Path, default=DEFAULT_HUMAN_RECOVERY_DIR)
    parser.add_argument("--closeout-summary", type=Path)
    parser.add_argument("--refresh-summary", type=Path)
    parser.add_argument("--human-recovery-summary", type=Path)
    parser.add_argument("--post-review-summary", type=Path)
    parser.add_argument("--objective-summary", type=Path)
    parser.add_argument("--summary-json", type=Path)
    parser.add_argument("--output-tsv", type=Path)
    parser.add_argument("--log-tsv", type=Path)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--allow-blocked-summary", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    closeout_summary = args.closeout_summary or args.run_dir / CLOSEOUT_SUMMARY_NAME
    refresh_summary = args.refresh_summary or args.run_dir / REFRESH_SUMMARY_NAME
    human_recovery_summary = args.human_recovery_summary or args.human_recovery_dir / HUMAN_RECOVERY_SUMMARY_NAME
    post_review_summary = args.post_review_summary or args.run_dir / POST_REVIEW_SUMMARY_NAME
    objective_summary = args.objective_summary or args.readiness_dir / OBJECTIVE_SUMMARY_NAME
    summary_json = args.summary_json or args.run_dir / SEQUENCE_SUMMARY_NAME
    output_tsv = args.output_tsv or args.run_dir / SEQUENCE_TSV_NAME
    log_tsv = args.log_tsv or args.run_dir / SEQUENCE_LOG_NAME
    payload, rows = build_sequence(
        run_dir=args.run_dir,
        readiness_dir=args.readiness_dir,
        human_recovery_dir=args.human_recovery_dir,
        closeout_summary_path=closeout_summary,
        refresh_summary_path=refresh_summary,
        human_recovery_summary_path=human_recovery_summary,
        post_review_summary_path=post_review_summary,
        objective_summary_path=objective_summary,
        repo_root=REPO_ROOT,
        execute=args.execute,
    )
    write_json(summary_json, payload)
    write_tsv(output_tsv, rows, SEQUENCE_TSV_FIELDS)
    append_tsv(
        log_tsv,
        {
            "recorded_at": now_label(),
            "mode": payload["mode"],
            "ok": payload["ok"],
            "status": payload["status"],
            "executed_step_count": payload["executed_step_count"],
            "stopped_step": payload["stopped_step"],
            "blocker_keys": ",".join(payload["blocker_keys"]),
            "output_summary": repo_relative(summary_json, repo_root=REPO_ROOT),
        },
        SEQUENCE_LOG_FIELDS,
    )
    print(
        json.dumps(
            {
                "ok": payload["ok"],
                "status": payload["status"],
                "mode": payload["mode"],
                "executed_step_count": payload["executed_step_count"],
                "blocker_keys": payload["blocker_keys"],
                "output_summary": str(summary_json),
            },
            ensure_ascii=False,
        )
    )
    return 0 if payload["ok"] or args.allow_blocked_summary else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build a repo-safe checklist for post-review evidence refresh."""

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

from build_human_audit_response_closeout_checklist import (  # noqa: E402
    CLOSEOUT_SUMMARY_NAME,
)
from build_human_audit_reviewer_handoff import DEFAULT_RUN_DIR  # noqa: E402
from prepare_human_audit_review_batch import (  # noqa: E402
    REFERENCE_TRANSCRIPT_POLICY,
    REMAINING_REVIEW_SCOPE,
    assert_tracked_safe,
    repo_relative,
)


DEFAULT_READINESS_DIR = (
    REPO_ROOT / "70_experiments" / "runs" / "postdoc_evidence_chain_2026_05_25"
)
DEFAULT_RECOVERY_SUMMARY = (
    REPO_ROOT
    / "70_experiments"
    / "runs"
    / "janus_300_high_stakes_recovery_proxy_2026_05_25"
    / "summary.json"
)
DEFAULT_HUMAN_RECOVERY_SUMMARY = (
    REPO_ROOT
    / "70_experiments"
    / "runs"
    / "janus_300_high_stakes_recovery_human_reviewed_2026_05_26"
    / "summary.json"
)
POST_REVIEW_SUMMARY_NAME = "human_audit_post_review_evidence_summary.json"
POST_REVIEW_TSV_NAME = "human_audit_post_review_evidence_checklist.tsv"
REFRESH_SUMMARY_NAME = "human_audit_refresh_summary.json"
PREDICTOR_SUMMARY_NAME = "human_audit_predictor_summary.json"
READINESS_SUMMARY_NAME = "evidence_chain_readiness_summary.json"
PUBLISHABLE_SUMMARY_NAME = "publishable_evidence_completion_summary.json"
CONSEQUENCE_SUMMARY_NAME = "consequence_evidence_matrix_summary.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = ["step_id", "evidence_gate", "status", "paper_claim_status", "evidence", "next_action"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def bool_status(condition: bool, *, ready: str = "ready", blocked: str = "blocked") -> str:
    return ready if condition else blocked


def command(parts: list[str]) -> str:
    return " ".join(parts)


def checklist_next_action(summary: dict[str, Any], step_id: str) -> str:
    checklist = summary.get("checklist")
    if not isinstance(checklist, list):
        return ""
    for item in checklist:
        if isinstance(item, dict) and str(item.get("step_id", "")) == step_id:
            return str(item.get("next_action", ""))
    return ""


def build_command_plan(
    *,
    closeout: dict[str, Any],
    closeout_ready: bool,
    refresh_complete: bool,
    recovery_ready: bool,
    paper_ready: bool,
    publishable_ready: bool,
    consequence_ready: bool,
) -> dict[str, Any]:
    commands = {
        "human_audit_refresh": command(
            [
                ".venv/bin/python",
                "80_semantic_risk_asr/annotation/refresh_human_audit_evidence.py",
            ]
        ),
        "strict_human_reviewed_recovery": command(
            [
                ".venv/bin/python",
                "80_semantic_risk_asr/recovery/evaluate_human_reviewed_recovery_policies.py",
            ]
        ),
        "post_review_checklist": command(
            [
                ".venv/bin/python",
                "80_semantic_risk_asr/annotation/build_post_review_evidence_checklist.py",
            ]
        ),
        "objective_requirements_audit": command(
            [
                ".venv/bin/python",
                "80_semantic_risk_asr/scoring/audit_postdoc_objective_requirements.py",
            ]
        ),
    }
    closeout_commands = {
        "strict_dry_run": checklist_next_action(closeout, "2"),
        "write_refresh_prepare_next": checklist_next_action(closeout, "7"),
    }
    if not closeout_ready:
        first_action = "complete_response_closeout"
    elif not refresh_complete:
        first_action = "run_human_audit_refresh"
    elif not recovery_ready:
        first_action = "run_strict_human_reviewed_recovery"
    elif not (paper_ready and publishable_ready and consequence_ready):
        first_action = "rerun_paper_facing_audits"
    else:
        first_action = "ready_for_paper_claim_review"

    return {
        "purpose": (
            "Exact post-review command order after the local selected-300 "
            "response TSV has human row/model/timing fields filled."
        ),
        "current_first_action": first_action,
        "closeout_commands": closeout_commands,
        "post_write_order": [
            {
                "order": 1,
                "gate": "human_audit_refresh",
                "command_key": "human_audit_refresh",
                "command": commands["human_audit_refresh"],
                "success_condition": "human_audit_refresh_summary.status == review_complete",
            },
            {
                "order": 2,
                "gate": "strict_human_reviewed_recovery",
                "command_key": "strict_human_reviewed_recovery",
                "command": commands["strict_human_reviewed_recovery"],
                "success_condition": "summary.evidence_mode == human_reviewed and five policies emitted",
            },
            {
                "order": 3,
                "gate": "post_review_checklist",
                "command_key": "post_review_checklist",
                "command": commands["post_review_checklist"],
                "success_condition": "human_audit_post_review_evidence_summary.status == post_review_evidence_ready",
            },
            {
                "order": 4,
                "gate": "objective_requirements_audit",
                "command_key": "objective_requirements_audit",
                "command": commands["objective_requirements_audit"],
                "success_condition": "postdoc_objective_requirements_summary.objective_requirements_ready == true",
            },
        ],
    }


def recovery_proxy_available(summary: dict[str, Any]) -> bool:
    policies = summary.get("policies")
    if not isinstance(policies, dict):
        return False
    required = {
        "no_recovery",
        "confidence_only_trigger",
        "sres_triggered_recovery",
        "ceis_triggered_conservative_action",
        "ceis_ensemble_arbitration",
    }
    return bool(summary.get("ok")) and required.issubset(set(policies))


def recovery_human_ready(summary: dict[str, Any]) -> bool:
    if not recovery_proxy_available(summary):
        return False
    return (
        summary.get("evidence_mode") == "human_reviewed"
        or summary.get("human_reviewed") is True
        or summary.get("review_status") == "human_reviewed_complete"
    )


def build_post_review_checklist(
    *,
    run_dir: Path,
    readiness_dir: Path,
    closeout_summary_path: Path,
    refresh_summary_path: Path,
    predictor_summary_path: Path,
    readiness_summary_path: Path,
    publishable_summary_path: Path,
    consequence_summary_path: Path,
    recovery_summary_path: Path,
    human_recovery_summary_path: Path,
    repo_root: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    started = time.time()
    closeout = read_json(closeout_summary_path)
    refresh = read_json(refresh_summary_path)
    predictor = read_json(predictor_summary_path)
    readiness = read_json(readiness_summary_path)
    publishable = read_json(publishable_summary_path)
    consequence = read_json(consequence_summary_path)
    recovery = read_json(recovery_summary_path)
    human_recovery = read_json(human_recovery_summary_path)
    closeout_timing = (
        closeout.get("review_timing")
        if isinstance(closeout.get("review_timing"), dict)
        else {}
    )

    closeout_ready = closeout.get("ok") is True and closeout.get("status") == "response_complete_ready_to_write"
    refresh_complete = (
        refresh.get("status") == "review_complete"
        and int(refresh.get("pending_rows") or 0) == 0
        and int(refresh.get("pending_model_assessments") or 0) == 0
    )
    predictor_complete = (
        predictor.get("ok") is True
        and predictor.get("status") == "review_complete"
        and int(predictor.get("pending_model_assessments") or 0) == 0
    )
    paper_ready = readiness.get("ok") is True and readiness.get("paper_ready") is True
    publishable_ready = publishable.get("ok") is True and publishable.get("publishable_ready") is True
    consequence_ready = consequence.get("ok") is True and consequence.get("paper_claims_ready") is True
    recovery_proxy = recovery_proxy_available(recovery)
    recovery_ready = recovery_human_ready(human_recovery)
    all_ready = (
        closeout_ready
        and refresh_complete
        and predictor_complete
        and paper_ready
        and publishable_ready
        and consequence_ready
        and recovery_ready
    )

    rows = [
        {
            "step_id": "1",
            "evidence_gate": "response closeout write readiness",
            "status": bool_status(closeout_ready),
            "paper_claim_status": "not paper-ready" if not closeout_ready else "write-ready",
            "evidence": (
                f"closeout_status={closeout.get('status', '')}; "
                f"pending_rows={closeout.get('pending_rows_in_response', '')}; "
                f"pending_model_assessments={closeout.get('pending_model_assessments_in_response', '')}; "
                f"require_timing={closeout.get('require_timing', '')}; "
                f"rows_missing_timing={closeout_timing.get('rows_missing_timing', '')}"
            ),
            "next_action": (
                "fill the local response TSV row/model fields plus per-row timing, "
                "rerun session-gated strict dry-run with --require-complete "
                "--require-timing, then closeout"
            ),
        },
        {
            "step_id": "2",
            "evidence_gate": "post-write aggregate refresh",
            "status": bool_status(refresh_complete),
            "paper_claim_status": "review-pending" if not refresh_complete else "human-review refreshed",
            "evidence": (
                f"refresh_status={refresh.get('status', '')}; "
                f"pending_rows={refresh.get('pending_rows', '')}; "
                f"pending_model_assessments={refresh.get('pending_model_assessments', '')}"
            ),
            "next_action": "run apply response with --write --refresh-after-write, then require refresh review_complete",
        },
        {
            "step_id": "3",
            "evidence_gate": "human-reviewed predictor refresh",
            "status": bool_status(predictor_complete),
            "paper_claim_status": "proxy-only" if not predictor_complete else "human-reviewed predictor evidence",
            "evidence": (
                f"predictor_status={predictor.get('status', '')}; "
                f"pending_model_assessments={predictor.get('pending_model_assessments', '')}"
            ),
            "next_action": "refresh human-audit predictor outputs after selected rows are reviewed",
        },
        {
            "step_id": "4",
            "evidence_gate": "evidence-chain readiness",
            "status": bool_status(paper_ready),
            "paper_claim_status": "not paper-ready" if not paper_ready else "paper-ready",
            "evidence": f"paper_ready={readiness.get('paper_ready', '')}",
            "next_action": "run check_evidence_chain_readiness.py after human refresh",
        },
        {
            "step_id": "5",
            "evidence_gate": "publishable objective completion",
            "status": bool_status(publishable_ready),
            "paper_claim_status": "not publishable-ready" if not publishable_ready else "publishable-ready",
            "evidence": f"publishable_ready={publishable.get('publishable_ready', '')}",
            "next_action": "run audit_publishable_evidence_chain.py after human refresh",
        },
        {
            "step_id": "6",
            "evidence_gate": "consequence claim matrix",
            "status": bool_status(consequence_ready),
            "paper_claim_status": "claims blocked or proxy" if not consequence_ready else "paper claims ready",
            "evidence": (
                f"paper_claims_ready={consequence.get('paper_claims_ready', '')}; "
                f"status_counts={json.dumps(consequence.get('status_counts', {}), sort_keys=True)}"
            ),
            "next_action": "rerun build_consequence_evidence_matrix.py after human refresh",
        },
        {
            "step_id": "7",
            "evidence_gate": "recovery policy evidence",
            "status": (
                "human_reviewed_ready"
                if recovery_ready
                else ("proxy_only" if recovery_proxy else "blocked")
            ),
            "paper_claim_status": (
                "human-reviewed recovery evidence"
                if recovery_ready
                else ("proxy-only until human review" if recovery_proxy else "missing")
            ),
            "evidence": (
                f"recovery_ok={recovery.get('ok', '')}; "
                f"proxy_policy_count={len(recovery.get('policies', {}) if isinstance(recovery.get('policies'), dict) else {})}; "
                f"human_recovery_status={human_recovery.get('status', '')}; "
                f"human_evidence_mode={human_recovery.get('evidence_mode', '')}; "
                f"human_policy_count={len(human_recovery.get('policies', {}) if isinstance(human_recovery.get('policies'), dict) else {})}"
            ),
            "next_action": "rerun recovery policy evaluation after human-reviewed labels are available",
        },
    ]

    blocker_keys: list[str] = []
    if not closeout_ready:
        blocker_keys.append("response_closeout_not_ready")
    if not refresh_complete:
        blocker_keys.append("human_refresh_not_complete")
    if not predictor_complete:
        blocker_keys.append("human_predictor_not_complete")
    if not paper_ready:
        blocker_keys.append("paper_ready_false")
    if not publishable_ready:
        blocker_keys.append("publishable_ready_false")
    if not consequence_ready:
        blocker_keys.append("consequence_paper_claims_not_ready")
    if not recovery_ready and recovery_proxy:
        blocker_keys.append("recovery_proxy_only")
    elif not recovery_proxy:
        blocker_keys.append("recovery_proxy_missing")

    status = "post_review_evidence_ready" if all_ready else "post_review_evidence_blocked"
    review_scope = (
        "Selected-300 risk, decision, expected safe action, confidence, "
        "per-model fields, and per-row review timing are complete; remaining "
        "work is proxy-to-paper claim resolution."
        if refresh_complete
        else REMAINING_REVIEW_SCOPE
    )
    payload = {
        "ok": all_ready,
        "status": status,
        "input_boundary": "tracked aggregate summaries only",
        "output_boundary": "aggregate-only post-review evidence checklist; no row keys or transcript text",
        "reference_transcript_policy": REFERENCE_TRANSCRIPT_POLICY,
        "remaining_review_scope": review_scope,
        "closeout_ready": closeout_ready,
        "closeout_require_timing": closeout.get("require_timing", ""),
        "closeout_review_timing": closeout_timing,
        "refresh_complete": refresh_complete,
        "predictor_complete": predictor_complete,
        "paper_ready": paper_ready,
        "publishable_ready": publishable_ready,
        "consequence_ready": consequence_ready,
        "recovery_proxy_available": recovery_proxy,
        "recovery_human_ready": recovery_ready,
        "human_recovery_status": human_recovery.get("status", "missing"),
        "human_recovery_evidence_mode": human_recovery.get("evidence_mode", ""),
        "blocker_keys": blocker_keys,
        "post_review_command_plan": build_command_plan(
            closeout=closeout,
            closeout_ready=closeout_ready,
            refresh_complete=refresh_complete,
            recovery_ready=recovery_ready,
            paper_ready=paper_ready,
            publishable_ready=publishable_ready,
            consequence_ready=consequence_ready,
        ),
        "checklist": rows,
        "paper_ready_impact": (
            "No paper-readiness change. This checklist records the gates that must pass "
            "after reviewer response write/refresh before proxy claims can be promoted."
        ),
        "next_concrete_action": (
            "Complete the response closeout gate first: fill row/model/timing "
            "fields, rerun the session-gated strict dry-run with "
            "--require-complete --require-timing, then write/refresh and "
            "rerun this checklist."
            if not closeout_ready
            else "Run post-write refresh and paper-facing audits until every gate is ready."
        ),
        "tracked_outputs": {
            "summary": repo_relative(run_dir / POST_REVIEW_SUMMARY_NAME, repo_root=repo_root),
            "checklist_tsv": repo_relative(run_dir / POST_REVIEW_TSV_NAME, repo_root=repo_root),
            "readiness_dir": repo_relative(readiness_dir, repo_root=repo_root),
            "recovery_proxy_summary": repo_relative(recovery_summary_path, repo_root=repo_root),
            "recovery_human_summary": repo_relative(human_recovery_summary_path, repo_root=repo_root),
        },
        "runtime_seconds": round(time.time() - started, 4),
    }
    assert_tracked_safe(payload)
    assert_tracked_safe(rows)
    return payload, rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--readiness-dir", type=Path, default=DEFAULT_READINESS_DIR)
    parser.add_argument("--closeout-summary", type=Path)
    parser.add_argument("--refresh-summary", type=Path)
    parser.add_argument("--predictor-summary", type=Path)
    parser.add_argument("--readiness-summary", type=Path)
    parser.add_argument("--publishable-summary", type=Path)
    parser.add_argument("--consequence-summary", type=Path)
    parser.add_argument("--recovery-summary", type=Path, default=DEFAULT_RECOVERY_SUMMARY)
    parser.add_argument("--human-recovery-summary", type=Path, default=DEFAULT_HUMAN_RECOVERY_SUMMARY)
    parser.add_argument("--summary-json", type=Path)
    parser.add_argument("--output-tsv", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    closeout_summary = args.closeout_summary or args.run_dir / CLOSEOUT_SUMMARY_NAME
    refresh_summary = args.refresh_summary or args.run_dir / REFRESH_SUMMARY_NAME
    predictor_summary = args.predictor_summary or args.run_dir / PREDICTOR_SUMMARY_NAME
    readiness_summary = args.readiness_summary or args.readiness_dir / READINESS_SUMMARY_NAME
    publishable_summary = args.publishable_summary or args.readiness_dir / PUBLISHABLE_SUMMARY_NAME
    consequence_summary = args.consequence_summary or args.readiness_dir / CONSEQUENCE_SUMMARY_NAME
    summary_json = args.summary_json or args.run_dir / POST_REVIEW_SUMMARY_NAME
    output_tsv = args.output_tsv or args.run_dir / POST_REVIEW_TSV_NAME
    payload, rows = build_post_review_checklist(
        run_dir=args.run_dir,
        readiness_dir=args.readiness_dir,
        closeout_summary_path=closeout_summary,
        refresh_summary_path=refresh_summary,
        predictor_summary_path=predictor_summary,
        readiness_summary_path=readiness_summary,
        publishable_summary_path=publishable_summary,
        consequence_summary_path=consequence_summary,
        recovery_summary_path=args.recovery_summary,
        human_recovery_summary_path=args.human_recovery_summary,
        repo_root=REPO_ROOT,
    )
    write_json(summary_json, payload)
    write_tsv(output_tsv, rows)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

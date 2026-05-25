from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "scoring"))

from audit_postdoc_roadmap_completion import (  # noqa: E402
    assert_roadmap_safe,
    build_roadmap_audit_from_payloads,
)


def completion_row(objective_id: str, status: str, paper_status: str = "") -> dict[str, str]:
    return {
        "objective_id": objective_id,
        "objective": f"objective {objective_id}",
        "status": status,
        "paper_claim_status": paper_status,
        "evidence": "tracked aggregate evidence",
        "result": "aggregate result",
        "blocking_dependency": "" if status == "completed" else "review dependency",
        "next_action": "next action",
    }


def base_completion() -> dict:
    return {
        "publishable_ready": False,
        "completion_rows": [
            completion_row("0", "completed", "provenance evidence"),
            completion_row("1", "completed", "engineering gate only"),
            completion_row("2", "completed", "engineering gate only"),
            completion_row("3", "completed", "pilot evidence"),
            completion_row("4", "proxy_completed", "proxy evidence"),
            completion_row("5", "review_pending", "not paper-ready"),
            completion_row("6", "proxy_completed", "proxy evidence"),
        ],
    }


def test_roadmap_audit_blocks_current_proxy_and_review_pending_state() -> None:
    payload = build_roadmap_audit_from_payloads(
        readiness={"paper_ready": False},
        completion=base_completion(),
        consequence={"paper_claims_ready": False},
        post_review={
            "ok": False,
            "status": "post_review_evidence_blocked",
            "closeout_ready": False,
            "refresh_complete": False,
            "predictor_complete": False,
            "publishable_ready": False,
            "consequence_ready": False,
            "recovery_human_ready": False,
            "blocker_keys": ["response_closeout_not_ready", "recovery_proxy_only"],
            "next_concrete_action": "complete response closeout",
        },
        human_refresh={
            "ok": True,
            "status": "review_pending",
            "audit_rows": 30,
            "reviewed_rows": 0,
            "model_assessments": 90,
            "reviewed_model_assessments": 0,
            "pending_rows": 30,
            "pending_model_assessments": 90,
        },
        human_predictor={"status": "review_pending"},
        response_closeout={
            "status": "response_closeout_blocked",
            "rows_in_batch": 6,
            "pending_rows_in_response": 6,
            "reviewed_model_assessments_in_response": 0,
            "pending_model_assessments_in_response": 18,
            "latest_apply_status": "response_pending",
        },
        candidate_summary={
            "ok": True,
            "strict_locale_policy": "Taiwan Traditional Chinese",
            "promotion_decision": "No candidate should be promoted.",
            "blocked_or_stopped": [{"run_id": "qwen", "status": "timeout"}],
        },
    )

    assert payload["ok"] is True
    assert payload["roadmap_complete"] is False
    assert payload["publishable_ready"] is False
    assert payload["blocking_gate"] == "selected_300_human_review_and_post_review_refresh"
    assert payload["current_review_counts"]["selected_300_rows_reviewed"] == 0
    assert payload["current_review_counts"]["current_packet_model_assessments_pending"] == 18
    assert payload["candidate_gate"]["blocked_or_stopped_count"] == 1
    assert payload["status_counts"]["blocked"] == 1
    assert_roadmap_safe(payload)


def test_roadmap_audit_can_mark_all_requirements_complete() -> None:
    completion = {
        "publishable_ready": True,
        "completion_rows": [
            completion_row(str(index), "completed", "ready")
            for index in range(7)
        ],
    }
    payload = build_roadmap_audit_from_payloads(
        readiness={"paper_ready": True},
        completion=completion,
        consequence={"paper_claims_ready": True},
        post_review={
            "ok": True,
            "status": "post_review_evidence_ready",
            "blocker_keys": [],
        },
        human_refresh={
            "ok": True,
            "status": "review_complete",
            "audit_rows": 30,
            "reviewed_rows": 30,
            "pending_rows": 0,
            "model_assessments": 90,
            "reviewed_model_assessments": 90,
            "pending_model_assessments": 0,
        },
        human_predictor={"status": "review_complete"},
        response_closeout={
            "status": "response_complete_ready_to_write",
            "rows_in_batch": 6,
            "pending_rows_in_response": 0,
            "reviewed_model_assessments_in_response": 18,
            "pending_model_assessments_in_response": 0,
        },
        candidate_summary={"ok": True},
    )

    assert payload["roadmap_complete"] is True
    assert payload["blocking_gate"] == "none"
    assert payload["post_review_evidence_ready"] is True
    assert payload["status_counts"] == {"completed": 8}


def test_recovery_proxy_keeps_roadmap_incomplete_even_when_review_counts_are_done() -> None:
    completion = {
        "publishable_ready": True,
        "completion_rows": [
            completion_row(str(index), "completed", "ready")
            for index in range(6)
        ]
        + [completion_row("6", "proxy_completed", "proxy evidence")],
    }
    payload = build_roadmap_audit_from_payloads(
        readiness={"paper_ready": True},
        completion=completion,
        consequence={"paper_claims_ready": False},
        post_review={
            "ok": False,
            "status": "post_review_evidence_blocked",
            "closeout_ready": True,
            "refresh_complete": True,
            "predictor_complete": True,
            "publishable_ready": True,
            "consequence_ready": False,
            "recovery_human_ready": False,
            "blocker_keys": ["recovery_proxy_only"],
        },
        human_refresh={
            "ok": True,
            "status": "review_complete",
            "audit_rows": 30,
            "reviewed_rows": 30,
            "pending_rows": 0,
            "model_assessments": 90,
            "reviewed_model_assessments": 90,
            "pending_model_assessments": 0,
        },
        human_predictor={"status": "review_complete"},
        response_closeout={
            "rows_in_batch": 6,
            "pending_rows_in_response": 0,
            "reviewed_model_assessments_in_response": 18,
            "pending_model_assessments_in_response": 0,
        },
        candidate_summary={"ok": True},
    )

    assert payload["roadmap_complete"] is False
    assert payload["consequence_paper_claims_ready"] is False
    assert payload["status_counts"]["proxy_completed"] == 1
    assert payload["status_counts"]["blocked"] == 1


def test_roadmap_safety_rejects_sensitive_field_names() -> None:
    try:
        assert_roadmap_safe({"bad": "hypothesis_text"})
    except ValueError as exc:
        assert "sensitive token" in str(exc)
    else:
        raise AssertionError("sensitive field token did not fail")

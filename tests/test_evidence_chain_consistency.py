from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "scoring"))

from audit_evidence_chain_consistency import (  # noqa: E402
    SUMMARY_SPECS,
    assert_aggregate_safe,
    build_consistency_audit,
)


TRANSCRIPT_POLICY = (
    "Reference transcripts are already human-reviewed ground truth for WER/CER "
    "scoring; this packet does not ask for duplicate transcript review."
)
REVIEW_SCOPE = (
    "The packet asks reviewers to complete risk atoms, decision-change labels, "
    "expected safe action, confidence, per-model assessment fields, and "
    "per-row review timing."
)


def write_summary(root: Path, name: str, payload: dict) -> None:
    path = root / SUMMARY_SPECS[name]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def base_summary(**extra: object) -> dict:
    payload = {
        "ok": True,
        "reference_transcript_policy": TRANSCRIPT_POLICY,
        "remaining_review_scope": REVIEW_SCOPE,
    }
    payload.update(extra)
    return payload


def write_consistent_fixture(root: Path) -> None:
    write_summary(
        root,
        "readiness",
        base_summary(
            paper_ready=False,
            next_decision="Complete per-row timing and run --require-timing.",
            reviewer_action_gate={
                "status": "reviewer_action_ready",
                "rows_in_batch": 6,
                "pending_rows_in_batch": 6,
                "model_assessments_in_batch": 18,
                "pending_model_assessments_in_batch": 18,
                "rows_missing_timing": 6,
            },
        ),
    )
    write_summary(
        root,
        "publishable",
        base_summary(
            publishable_ready=False,
            blocking_or_proxy_items=[{"objective_id": "5"}],
            next_decision="Complete timing, then run --require-timing.",
        ),
    )
    write_summary(
        root,
        "consequence",
        base_summary(
            paper_claims_ready=False,
            blocking_or_proxy_items=[{"consequence_id": "C5"}],
            next_decision="Complete risk/decision/model/timing review, then run --require-complete --require-timing.",
        ),
    )
    write_summary(
        root,
        "roadmap",
        base_summary(
            paper_ready=False,
            publishable_ready=False,
            roadmap_complete=False,
            next_decision="Close row/model/timing gate with --require-timing.",
        ),
    )
    write_summary(
        root,
        "refresh",
        base_summary(
            status="review_pending",
            publishable_ready=False,
            next_action="Complete per-row timing with --require-timing.",
        ),
    )
    write_summary(
        root,
        "post_review",
        base_summary(
            ok=False,
            status="post_review_evidence_blocked",
            paper_ready=False,
            publishable_ready=False,
        ),
    )
    write_summary(
        root,
        "closeout",
        base_summary(
            ok=False,
            status="response_closeout_blocked",
            require_timing=True,
            review_timing={"rows_missing_timing": 6},
        ),
    )
    write_summary(
        root,
        "apply",
        base_summary(
            ok=False,
            status="response_pending",
            require_timing=True,
            review_timing={"rows_missing_timing": 6},
            next_action="Rerun dry-run with --require-timing.",
        ),
    )
    write_summary(
        root,
        "handoff",
        base_summary(
            status="reviewer_input_pending",
            freshness_status="fresh",
            current_gate={
                "latest_apply_status": "response_pending",
                "pending_rows_in_batch": 6,
                "pending_model_assessments_in_batch": 18,
                "rows_missing_timing": 6,
            },
        ),
    )
    write_summary(
        root,
        "candidate_recheck",
        {
            "ok": True,
            "promotion_decision": "No requested ASR/Gemma candidate should be promoted.",
            "bounded_probes": [
                {"status": "timeout_before_inference"},
                {"status": "blocked_local_transformers_multimodal_class_missing"},
            ],
        },
    )


def test_consistency_audit_passes_current_blocked_but_aligned_state(tmp_path: Path) -> None:
    write_consistent_fixture(tmp_path)
    payload = build_consistency_audit(tmp_path)

    assert payload["ok"] is True
    assert payload["status_counts"] == {"pass": 12}
    assert not payload["failed_checks"]
    assert_aggregate_safe(payload)


def test_consistency_audit_fails_stale_remaining_scope(tmp_path: Path) -> None:
    write_consistent_fixture(tmp_path)
    stale = base_summary(
        ok=False,
        status="response_pending",
        require_timing=True,
        review_timing={"rows_missing_timing": 6},
        next_action="Rerun dry-run with --require-timing.",
        remaining_review_scope=(
            "The packet asks reviewers to complete risk atoms, decision-change "
            "labels, expected safe action, confidence, and per-model assessment fields."
        ),
    )
    write_summary(tmp_path, "apply", stale)

    payload = build_consistency_audit(tmp_path)

    assert payload["ok"] is False
    assert any(item["check_id"] == "C020" for item in payload["failed_checks"])


def test_consistency_audit_rejects_paper_ready_while_review_pending(tmp_path: Path) -> None:
    write_consistent_fixture(tmp_path)
    write_summary(
        tmp_path,
        "publishable",
        base_summary(
            publishable_ready=True,
            blocking_or_proxy_items=[],
            next_decision="Complete timing, then run --require-timing.",
        ),
    )

    payload = build_consistency_audit(tmp_path)

    assert payload["ok"] is False
    failed_ids = {item["check_id"] for item in payload["failed_checks"]}
    assert "C040" in failed_ids
    assert "C050" in failed_ids


def test_consistency_audit_fails_stale_reviewer_handoff(tmp_path: Path) -> None:
    write_consistent_fixture(tmp_path)
    write_summary(
        tmp_path,
        "handoff",
        base_summary(
            status="reviewer_input_pending",
            freshness_status="stale",
            current_gate={
                "latest_apply_status": "response_pending",
                "pending_rows_in_batch": 6,
                "pending_model_assessments_in_batch": 18,
                "rows_missing_timing": 6,
            },
        ),
    )

    payload = build_consistency_audit(tmp_path)

    assert payload["ok"] is False
    assert any(item["check_id"] == "C065" for item in payload["failed_checks"])


def test_consistency_safety_rejects_raw_field_tokens() -> None:
    try:
        assert_aggregate_safe({"bad": "hypothesis_text"})
    except ValueError as exc:
        assert "sensitive field token" in str(exc)
    else:
        raise AssertionError("sensitive field token did not fail")

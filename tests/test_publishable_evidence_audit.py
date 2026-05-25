from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "scoring"))

from audit_publishable_evidence_chain import (  # noqa: E402
    assert_completion_safe,
    objective_rows_from_payloads,
)


def readiness_row(requirement: str, status: str) -> dict[str, str]:
    return {
        "phase": "x",
        "requirement": requirement,
        "status": status,
        "paper_claim_status": "",
        "evidence": "",
        "result": "",
        "next_action": "",
    }


def base_readiness() -> dict:
    return {
        "reviewer_action_gate": {
            "available": True,
            "ok": True,
            "status": "reviewer_action_ready",
            "selection_stratum": "critical_or_high_risk_missed",
            "rows_in_batch": 6,
            "pending_rows_in_batch": 6,
            "model_assessments_in_batch": 18,
            "pending_model_assessments_in_batch": 18,
            "latest_apply_status": "response_pending",
        },
        "readiness_rows": [
            readiness_row("migration and best-model selection checkpoint", "completed"),
            readiness_row("legacy-best load smoke tests", "completed"),
            readiness_row(
                "legacy best models join the fixed 15-row hypothesis contract",
                "completed",
            ),
            readiness_row("CDS-ASR bridge over 15-row legacy-best hypotheses", "completed"),
            readiness_row(
                "canonical 258-row six-model comparison with decision-risk metrics",
                "proxy_completed",
            ),
            readiness_row("selected-300 high-stakes CDS-ASR main experiment proxy", "proxy_completed"),
            readiness_row(
                "WER/CER/SRES/CEIS predictor comparison on selected-300",
                "proxy_completed",
            ),
            readiness_row("five-condition recovery experiment", "proxy_completed"),
            readiness_row("selected-300 human risk-atom audit completion", "review_pending"),
        ]
    }


def test_objective_audit_keeps_proxy_and_human_review_separate() -> None:
    rows = objective_rows_from_payloads(
        readiness_payload=base_readiness(),
        human_refresh={
            "ok": True,
            "status": "review_pending",
            "audit_rows": 30,
            "reviewed_rows": 0,
            "model_assessments": 90,
            "reviewed_model_assessments": 0,
        },
        human_predictor={
            "ok": True,
            "status": "review_pending",
            "pending_model_assessments": 90,
        },
    )
    by_id = {row["objective_id"]: row for row in rows}

    assert by_id["0"]["status"] == "completed"
    assert by_id["4"]["status"] == "proxy_completed"
    assert by_id["5"]["status"] == "review_pending"
    assert by_id["6"]["status"] == "proxy_completed"
    assert "selected-300 risk-atom" in by_id["5"]["blocking_dependency"]
    assert "not transcript ground truth" in by_id["5"]["next_action"]
    assert "reviewer_action_ready" in by_id["5"]["result"]
    assert_completion_safe({"completion_rows": rows})


def test_objective_five_requires_reviewed_predictor_outputs() -> None:
    readiness = base_readiness()
    for row in readiness["readiness_rows"]:
        if row["requirement"] == "selected-300 human risk-atom audit completion":
            row["status"] = "completed"
    rows = objective_rows_from_payloads(
        readiness_payload=readiness,
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
        human_predictor={
            "ok": True,
            "status": "review_pending",
            "pending_model_assessments": 90,
        },
    )
    by_id = {row["objective_id"]: row for row in rows}

    assert by_id["5"]["status"] == "review_pending"
    assert by_id["5"]["paper_claim_status"] == "not paper-ready"


def test_completion_audit_requires_consequence_claim_readiness() -> None:
    from audit_publishable_evidence_chain import build_completion_audit_from_payloads

    readiness = base_readiness()
    for row in readiness["readiness_rows"]:
        if row["requirement"] in {
            "canonical 258-row six-model comparison with decision-risk metrics",
            "selected-300 high-stakes CDS-ASR main experiment proxy",
            "WER/CER/SRES/CEIS predictor comparison on selected-300",
            "five-condition recovery experiment",
            "selected-300 human risk-atom audit completion",
        }:
            row["status"] = "completed"
    payload = build_completion_audit_from_payloads(
        readiness_payload=readiness,
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
        human_predictor={
            "ok": True,
            "status": "review_complete",
            "pending_model_assessments": 0,
        },
        consequence_matrix={
            "ok": True,
            "paper_claims_ready": False,
            "status_counts": {"review_pending": 1},
            "blocking_or_proxy_items": [{"consequence_id": "C6"}],
        },
    )

    assert payload["objective_requirements_ready"] is True
    assert payload["publishable_ready"] is False
    assert payload["reviewer_action_gate"]["status"] == "reviewer_action_ready"
    assert payload["consequence_matrix_alignment"]["paper_claims_ready"] is False
    assert payload["consequence_matrix_alignment"]["blocking_or_proxy_items"] == 1


def test_completion_safety_rejects_private_tokens() -> None:
    try:
        assert_completion_safe({"bad": "reference_text"})
    except ValueError as exc:
        assert "sensitive token" in str(exc)
    else:
        raise AssertionError("private token did not fail")

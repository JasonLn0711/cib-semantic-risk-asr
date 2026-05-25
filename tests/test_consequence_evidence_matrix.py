from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "scoring"))

from build_consequence_evidence_matrix import (  # noqa: E402
    assert_matrix_safe,
    consequence_rows_from_payloads,
)


def test_consequence_matrix_separates_proxy_from_human_ready_claims() -> None:
    rows = consequence_rows_from_payloads(
        journal_compliance={"paper_reporting_compliant": True},
        metric_predictor_summary={
            "ok": True,
            "low_wer_summary": [
                {
                    "asr_run_id": "ALL",
                    "rows": 900,
                    "low_wer_rows": 180,
                    "low_wer_threshold": 10,
                    "low_wer_any_danger_count": 2,
                }
            ],
            "run_summary": {
                "breeze_asr25_partial_encoder_high_stakes_300": {
                    "danger_event_count": 7,
                    "unsafe_downrouting_count": 4,
                    "high_risk_missed_count": 1,
                },
                "breeze_asr25_lora_high_stakes_300": {
                    "danger_event_count": 12,
                },
                "breeze_asr25_base_high_stakes_300": {
                    "danger_event_count": 30,
                },
            },
        },
        metric_predictor_rows=[
            {
                "scope": "overall",
                "asr_run_id": "ALL",
                "target": "unsafe_downrouting",
                "metric": "wer",
                "auc": "0.76",
            },
            {
                "scope": "overall",
                "asr_run_id": "ALL",
                "target": "unsafe_downrouting",
                "metric": "cer",
                "auc": "0.77",
            },
            {
                "scope": "overall",
                "asr_run_id": "ALL",
                "target": "unsafe_downrouting",
                "metric": "ceis_max",
                "auc": "0.99",
            },
        ],
        recovery_summary={
            "ok": True,
            "policies": {
                "no_recovery": {
                    "high_risk_missed_count": 6,
                    "critical_miss_count": 1,
                },
                "ceis_triggered_conservative_action": {
                    "high_risk_missed_count": 0,
                    "critical_miss_count": 0,
                    "recovery_budget_rate": 0.04,
                },
                "ceis_ensemble_arbitration": {
                    "machine_abstention_count": 18,
                },
            },
        },
        split_rows=[
            {
                "run_id": "breeze_asr25_partial_encoder_legacy_best_test_split",
                "unsafe_downrouting_count": "7",
                "high_risk_missed_count": "4",
            },
            {
                "run_id": "breeze_asr25_lora_legacy_best_test_split",
                "unsafe_downrouting_count": "10",
                "high_risk_missed_count": "7",
            },
        ],
        human_refresh={
            "ok": True,
            "status": "review_pending",
            "reviewed_rows": 0,
            "audit_rows": 30,
            "reviewed_model_assessments": 0,
            "model_assessments": 90,
            "pending_rows": 30,
            "pending_model_assessments": 90,
        },
        preflight={"ok": True, "status": "review_session_ready"},
        completion_audit={
            "publishable_ready": False,
            "status_counts": {"completed": 4, "proxy_completed": 2, "review_pending": 1},
        },
    )

    by_id = {row["consequence_id"]: row for row in rows}
    assert by_id["C0"]["status"] == "completed"
    assert by_id["C1"]["status"] == "proxy_completed"
    assert by_id["C5"]["status"] == "review_pending"
    assert by_id["C6"]["paper_claim_status"] == "not paper-ready"
    assert "selected-300" in by_id["C5"]["blocking_dependency"]
    assert_matrix_safe(rows)


def test_consequence_matrix_rejects_sensitive_field_names() -> None:
    try:
        assert_matrix_safe({"bad": "audio_id"})
    except ValueError:
        return
    raise AssertionError("expected sensitive field-name rejection")


def test_consequence_matrix_rows_do_not_leak_transcript_fields() -> None:
    rows = consequence_rows_from_payloads(
        journal_compliance={"paper_reporting_compliant": False},
        metric_predictor_summary={},
        metric_predictor_rows=[],
        recovery_summary={},
        split_rows=[],
        human_refresh={},
        preflight={},
        completion_audit={},
    )

    serialized = json.dumps(rows, ensure_ascii=False)
    assert "reference_text" not in serialized
    assert "hypothesis_text" not in serialized
    assert "reviewer_notes" not in serialized

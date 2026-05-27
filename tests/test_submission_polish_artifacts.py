from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "scoring"))

from build_counterfactual_variant_coverage_summary import build_summary  # noqa: E402
from build_fixed_budget_recovery_frontier import build_frontier  # noqa: E402

sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "recovery"))
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "annotation"))
import evaluate_human_reviewed_recovery_policies as human_recovery  # noqa: E402


FIELDS = [
    "audio_id",
    "split",
    "selection_stratum",
    "selection_reason",
    "reference_label",
    "reference_text",
    "asr_hypotheses_json",
    "risk_signal_json",
    "reviewer_verified_transcript",
    "reviewer_semantic_risk_label",
    "reviewer_risk_atoms",
    "reviewer_critical_atoms",
    "reviewer_asr_confusion_terms",
    "reviewer_would_asr_error_change_decision",
    "reviewer_decision_change_reason",
    "reviewer_expected_safe_action",
    "reviewer_annotation_confidence",
    "reviewer_model_assessments_json",
    "reviewer_notes",
]


def reviewed_row(
    private_id: str,
    *,
    reference_label: str = "priority_review",
    asr_label: str = "no_escalation",
    sres_total: float = 30.0,
    ceis: float = 6.0,
    ceis_top_atom: str = "negation",
    decision_change: str = "yes",
) -> dict[str, str]:
    hypotheses = [
        {
            "asr_run_id": "run_a",
            "hypothesis_text": "PRIVATE_HYP",
            "asr_label": asr_label,
            "wer": 30.0,
            "cer": 12.0,
            "sres_total": sres_total,
            "sres_top_atom": ceis_top_atom,
            "ceis_max": ceis,
            "ceis_top_atom": ceis_top_atom,
        }
    ]
    assessments = [
        {
            "asr_run_id": "run_a",
            "reviewer_would_asr_error_change_decision": decision_change,
            "reviewer_critical_atoms": ceis_top_atom,
            "reviewer_expected_safe_action": "priority_review",
            "reviewer_annotation_confidence": "high",
        }
    ]
    return {
        "audio_id": private_id,
        "split": "high_stakes_300",
        "selection_stratum": "high_proxy_risk",
        "selection_reason": "PRIVATE_REASON",
        "reference_label": reference_label,
        "reference_text": "PRIVATE_REFERENCE",
        "asr_hypotheses_json": json.dumps(hypotheses),
        "risk_signal_json": json.dumps(
            {
                "top_risk_atoms": [ceis_top_atom],
                "flags": {"model_disagreement": True, "high_proxy_risk": True},
            }
        ),
        "reviewer_verified_transcript": "",
        "reviewer_semantic_risk_label": reference_label,
        "reviewer_risk_atoms": ceis_top_atom,
        "reviewer_critical_atoms": ceis_top_atom,
        "reviewer_asr_confusion_terms": ceis_top_atom,
        "reviewer_would_asr_error_change_decision": decision_change,
        "reviewer_decision_change_reason": "PRIVATE_REASON",
        "reviewer_expected_safe_action": "priority_review",
        "reviewer_annotation_confidence": "high",
        "reviewer_model_assessments_json": json.dumps(assessments),
        "reviewer_notes": "PRIVATE_NOTE",
    }


def test_variant_coverage_summary_is_aggregate_safe() -> None:
    summary = build_summary(
        [
            reviewed_row("private_audio_1", ceis_top_atom="negation"),
            reviewed_row(
                "private_audio_2",
                reference_label="no_escalation",
                asr_label="no_escalation",
                sres_total=0,
                ceis=0,
                ceis_top_atom="amount",
                decision_change="no",
            ),
        ]
    )

    assert summary["coverage_status"] == "aggregate_proxy_coverage_complete"
    assert summary["total_assessments"] == 2
    assert summary["variants_by_atom_negation"] == 1
    assert summary["variants_by_atom_amount"] == 1
    serialized = json.dumps(summary, ensure_ascii=False)
    assert "PRIVATE_" not in serialized
    assert "hypothesis_text" not in serialized
    assert "reference_text" not in serialized


def test_fixed_budget_frontier_is_aggregate_safe() -> None:
    samples, _metadata = human_recovery.build_samples(
        [
            reviewed_row("private_audio_1", sres_total=30, ceis=6),
            reviewed_row(
                "private_audio_2",
                reference_label="no_escalation",
                asr_label="no_escalation",
                sres_total=0,
                ceis=0,
                decision_change="no",
            ),
        ]
    )
    rows = build_frontier(samples, [0.5])

    assert rows
    assert {row["score_metric"] for row in rows} == {"sres_total", "ceis"}
    serialized = json.dumps(rows, ensure_ascii=False)
    assert "PRIVATE_" not in serialized
    assert "audio_id" not in serialized
    assert "sample_id" not in serialized

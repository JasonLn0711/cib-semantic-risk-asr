from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "annotation"))

from audit_human_review_progress import build_progress  # noqa: E402


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


def row_for(stratum: str, *, reviewed: bool, model_reviewed: bool) -> dict[str, str]:
    assessment = {
        "asr_run_id": "run_a",
        "reviewer_would_asr_error_change_decision": "yes" if model_reviewed else "",
        "reviewer_critical_atoms": "negation" if model_reviewed else "",
        "reviewer_expected_safe_action": "priority_review" if model_reviewed else "",
        "reviewer_annotation_confidence": "high" if model_reviewed else "",
    }
    row = {
        "audio_id": f"private_{stratum}",
        "split": "test",
        "selection_stratum": stratum,
        "selection_reason": "private",
        "reference_label": "priority_review",
        "reference_text": "PRIVATE_REFERENCE",
        "asr_hypotheses_json": json.dumps(
            [{"asr_run_id": "run_a", "hypothesis_text": "PRIVATE_HYP"}],
            ensure_ascii=False,
        ),
        "risk_signal_json": "{}",
        "reviewer_verified_transcript": "",
        "reviewer_semantic_risk_label": "",
        "reviewer_risk_atoms": "",
        "reviewer_critical_atoms": "",
        "reviewer_asr_confusion_terms": "",
        "reviewer_would_asr_error_change_decision": "",
        "reviewer_decision_change_reason": "",
        "reviewer_expected_safe_action": "",
        "reviewer_annotation_confidence": "",
        "reviewer_model_assessments_json": json.dumps([assessment], ensure_ascii=False),
        "reviewer_notes": "PRIVATE_NOTE",
    }
    if reviewed:
        row.update(
            {
                "reviewer_semantic_risk_label": "priority_review",
                "reviewer_risk_atoms": "negation",
                "reviewer_critical_atoms": "negation",
                "reviewer_asr_confusion_terms": "negation",
                "reviewer_would_asr_error_change_decision": "yes",
                "reviewer_decision_change_reason": "routing changed",
                "reviewer_expected_safe_action": "priority_review",
                "reviewer_annotation_confidence": "high",
            }
        )
    return row


def test_progress_summary_is_aggregate_safe_and_prioritized() -> None:
    progress = build_progress(
        FIELDS,
        [
            row_for("clean_control", reviewed=False, model_reviewed=False),
            row_for("critical_or_high_risk_missed", reviewed=True, model_reviewed=True),
            row_for("unsafe_downrouting", reviewed=False, model_reviewed=True),
        ],
        expected_rows=3,
    )
    summary = progress["summary"]
    strata = progress["strata"]
    batches = progress["batches"]

    assert summary["ok"] is True
    assert summary["status"] == "partial_review"
    assert summary["reviewed_rows"] == 1
    assert summary["pending_rows"] == 2
    assert summary["reviewed_model_assessments"] == 2
    assert summary["pending_model_assessments"] == 1
    assert strata[0]["selection_stratum"] == "critical_or_high_risk_missed"
    assert batches[0]["selection_stratum"] == "unsafe_downrouting"
    text = json.dumps(summary, ensure_ascii=False) + json.dumps(strata + progress["models"] + batches)
    assert "PRIVATE_" not in text
    assert "reference_text" not in text
    assert "hypothesis_text" not in text


def test_progress_model_counts_by_run_id() -> None:
    progress = build_progress(
        FIELDS,
        [row_for("unsafe_downrouting", reviewed=False, model_reviewed=False)],
        expected_rows=1,
    )
    model = progress["models"][0]

    assert model["asr_run_id"] == "run_a"
    assert model["model_assessments"] == 1
    assert model["pending_model_assessments"] == 1
    assert progress["summary"]["pending_model_assessments_by_run_id"] == {"run_a": 1}

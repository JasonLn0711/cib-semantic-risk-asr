from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "recovery"))

from evaluate_human_reviewed_recovery_policies import (  # noqa: E402
    assert_summary_safe,
    build_human_reviewed_recovery,
)


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


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    lines = ["\t".join(FIELDS)]
    for row in rows:
        lines.append("\t".join(row.get(field, "") for field in FIELDS))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def reviewed_row(
    audio_id: str,
    *,
    reference_label: str,
    run_a_label: str,
    run_a_decision_change: str,
    run_a_sres: float,
    run_a_ceis: float,
) -> dict[str, str]:
    hypotheses = [
        {
            "asr_run_id": "run_a",
            "hypothesis_text": "PRIVATE_HYP_A",
            "asr_label": run_a_label,
            "wer": 30.0 if run_a_decision_change == "yes" else 2.0,
            "cer": 12.0 if run_a_decision_change == "yes" else 1.0,
            "sres_total": run_a_sres,
            "sres_top_atom": "negation",
            "ceis_max": run_a_ceis,
            "ceis_top_atom": "negation",
        },
        {
            "asr_run_id": "run_b",
            "hypothesis_text": "PRIVATE_HYP_B",
            "asr_label": reference_label,
            "wer": 1.0,
            "cer": 0.5,
            "sres_total": 0.0,
            "sres_top_atom": "",
            "ceis_max": 0.0,
            "ceis_top_atom": "",
        },
    ]
    assessments = [
        {
            "asr_run_id": "run_a",
            "reviewer_would_asr_error_change_decision": run_a_decision_change,
            "reviewer_critical_atoms": "negation" if run_a_decision_change == "yes" else "none",
            "reviewer_expected_safe_action": "priority_review"
            if run_a_decision_change == "yes"
            else "none",
            "reviewer_annotation_confidence": "high",
        },
        {
            "asr_run_id": "run_b",
            "reviewer_would_asr_error_change_decision": "no",
            "reviewer_critical_atoms": "none",
            "reviewer_expected_safe_action": "none",
            "reviewer_annotation_confidence": "high",
        },
    ]
    return {
        "audio_id": audio_id,
        "split": "high_stakes_300",
        "selection_stratum": "unsafe_downrouting",
        "selection_reason": "PRIVATE_REASON",
        "reference_label": reference_label,
        "reference_text": "PRIVATE_REFERENCE",
        "asr_hypotheses_json": json.dumps(hypotheses, ensure_ascii=False),
        "risk_signal_json": "{}",
        "reviewer_verified_transcript": "",
        "reviewer_semantic_risk_label": reference_label,
        "reviewer_risk_atoms": "negation",
        "reviewer_critical_atoms": "negation" if run_a_decision_change == "yes" else "none",
        "reviewer_asr_confusion_terms": "negation",
        "reviewer_would_asr_error_change_decision": run_a_decision_change,
        "reviewer_decision_change_reason": "routing",
        "reviewer_expected_safe_action": "priority_review"
        if run_a_decision_change == "yes"
        else "none",
        "reviewer_annotation_confidence": "high",
        "reviewer_model_assessments_json": json.dumps(assessments, ensure_ascii=False),
        "reviewer_notes": "PRIVATE_NOTE",
    }


def test_human_reviewed_recovery_requires_completed_review(tmp_path: Path) -> None:
    sheet = tmp_path / "audit.tsv"
    row = reviewed_row(
        "private_audio_1",
        reference_label="priority_review",
        run_a_label="no_escalation",
        run_a_decision_change="yes",
        run_a_sres=30.0,
        run_a_ceis=6.0,
    )
    row["reviewer_semantic_risk_label"] = ""
    write_rows(sheet, [row])

    payload, detail_rows, exit_code = build_human_reviewed_recovery(
        audit_sheet=sheet,
        expected_rows=1,
        allow_pending_summary=True,
        confidence_threshold=0.7,
        sres_threshold=20.0,
        ceis_threshold=5.0,
        ensemble_mode="priority",
    )

    assert exit_code == 0
    assert payload["ok"] is False
    assert payload["status"] in {"review_pending", "partial_review"}
    assert payload["evidence_mode"] == "human_reviewed_pending"
    assert payload["blocker_keys"] == ["human_review_incomplete"]
    assert detail_rows == []
    assert_summary_safe(payload)


def test_human_reviewed_recovery_produces_policy_summary(tmp_path: Path) -> None:
    sheet = tmp_path / "audit.tsv"
    write_rows(
        sheet,
        [
            reviewed_row(
                "private_audio_1",
                reference_label="priority_review",
                run_a_label="no_escalation",
                run_a_decision_change="yes",
                run_a_sres=30.0,
                run_a_ceis=6.0,
            ),
            reviewed_row(
                "private_audio_2",
                reference_label="no_escalation",
                run_a_label="no_escalation",
                run_a_decision_change="no",
                run_a_sres=0.0,
                run_a_ceis=0.0,
            ),
        ],
    )

    payload, detail_rows, exit_code = build_human_reviewed_recovery(
        audit_sheet=sheet,
        expected_rows=2,
        allow_pending_summary=False,
        confidence_threshold=0.7,
        sres_threshold=20.0,
        ceis_threshold=5.0,
        ensemble_mode="priority",
    )

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["status"] == "human_reviewed_complete"
    assert payload["evidence_mode"] == "human_reviewed"
    assert payload["human_reviewed"] is True
    assert payload["reviewed_rows"] == 2
    assert payload["sample_count"] == 4
    assert payload["human_reviewed_model_samples"] == 4
    assert payload["policies"]["no_recovery"]["high_risk_missed_count"] == 1
    assert (
        payload["policies"]["ceis_triggered_conservative_action"]["high_risk_missed_count"]
        == 0
    )
    assert (
        payload["policies"]["ceis_triggered_conservative_action"]["high_risk_missed_gain"]
        == 1.0
    )
    assert detail_rows
    assert_summary_safe(payload)
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "PRIVATE_" not in serialized
    assert "reference_text" not in serialized
    assert "hypothesis_text" not in serialized

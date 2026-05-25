from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "annotation"))

from summarize_human_risk_atom_audit import (  # noqa: E402
    assert_aggregate_safe,
    read_tsv,
    summarize_completion,
    summarize_human_atoms,
    summarize_model_proxy_coverage,
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


def base_row(**overrides: str) -> dict[str, str]:
    row = {
        "audio_id": "audio_private_001",
        "split": "test",
        "selection_stratum": "unsafe_downrouting",
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
        "reviewer_model_assessments_json": json.dumps(
            [
                {
                    "asr_run_id": "run_a",
                    "reviewer_would_asr_error_change_decision": "",
                    "reviewer_critical_atoms": "",
                    "reviewer_expected_safe_action": "",
                    "reviewer_annotation_confidence": "",
                }
            ],
            ensure_ascii=False,
        ),
        "reviewer_notes": "",
    }
    row.update(overrides)
    return row


def test_unreviewed_sheet_is_pending(tmp_path: Path) -> None:
    sheet = tmp_path / "audit.tsv"
    write_rows(sheet, [base_row()])
    rows = read_tsv(sheet)

    summary = summarize_completion(rows)

    assert summary["status"] == "review_pending"
    assert summary["reviewed_rows"] == 0
    assert summary["model_assessments"] == 1
    assert summary["pending_model_assessments"] == 1
    assert summary["missing_required_field_counts"]["reviewer_semantic_risk_label"] == 1


def test_reviewed_summary_is_aggregate_safe(tmp_path: Path) -> None:
    sheet = tmp_path / "audit.tsv"
    write_rows(
        sheet,
        [
            base_row(
                reviewer_semantic_risk_label="priority_review",
                reviewer_risk_atoms="negation,amount",
                reviewer_critical_atoms="negation",
                reviewer_asr_confusion_terms="negation dropped",
                reviewer_would_asr_error_change_decision="yes",
                reviewer_decision_change_reason="changes escalation",
                reviewer_expected_safe_action="priority_review",
                reviewer_annotation_confidence="high",
                reviewer_model_assessments_json=json.dumps(
                    [
                        {
                            "asr_run_id": "run_a",
                            "reviewer_would_asr_error_change_decision": "yes",
                            "reviewer_critical_atoms": "negation",
                            "reviewer_expected_safe_action": "priority_review",
                            "reviewer_annotation_confidence": "high",
                        }
                    ],
                    ensure_ascii=False,
                ),
                reviewer_notes="PRIVATE_NOTE",
            )
        ],
    )
    rows = read_tsv(sheet)

    summary = summarize_completion(rows)
    atom_rows = summarize_human_atoms(rows)
    model_rows = summarize_model_proxy_coverage(rows)
    payload = {"ok": True, **summary}
    assert_aggregate_safe(payload, atom_rows + model_rows)

    assert summary["status"] == "review_complete"
    assert atom_rows == [
        {
            "risk_atom_type": "amount",
            "reviewed_row_count": 1,
            "critical_atom_row_count": 0,
            "decision_change_yes_count": 0,
        },
        {
            "risk_atom_type": "negation",
            "reviewed_row_count": 1,
            "critical_atom_row_count": 1,
            "decision_change_yes_count": 1,
        },
    ]
    assert model_rows[0]["asr_run_id"] == "run_a"
    assert model_rows[0]["model_assessments"] == 1
    assert model_rows[0]["reviewed_model_samples"] == 1
    assert model_rows[0]["human_decision_change_yes_rows"] == 1

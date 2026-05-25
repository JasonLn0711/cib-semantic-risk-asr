from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "annotation"))

from validate_human_risk_atom_audit import (  # noqa: E402
    assert_aggregate_safe,
    read_tsv,
    validate_rows,
    validation_count_rows,
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
        "reviewer_notes": "PRIVATE_NOTE",
    }
    row.update(overrides)
    return row


def test_pending_sheet_is_valid_but_not_complete(tmp_path: Path) -> None:
    sheet = tmp_path / "audit.tsv"
    write_rows(sheet, [base_row()])
    fieldnames, rows = read_tsv(sheet)

    payload = validate_rows(fieldnames, rows, require_complete=False, expected_rows=1)
    require_complete_payload = validate_rows(
        fieldnames,
        rows,
        require_complete=True,
        expected_rows=1,
    )
    assert_aggregate_safe(payload)

    assert payload["ok"] is True
    assert payload["status"] == "review_pending"
    assert payload["pending_rows"] == 1
    assert payload["pending_model_assessments"] == 1
    assert require_complete_payload["ok"] is False
    assert require_complete_payload["error_counts"]["incomplete_row_review"] == 1
    assert require_complete_payload["error_counts"]["incomplete_model_review"] == 1


def test_completed_sheet_passes_completion_gate(tmp_path: Path) -> None:
    sheet = tmp_path / "audit.tsv"
    write_rows(
        sheet,
        [
            base_row(
                reviewer_semantic_risk_label="priority_review",
                reviewer_risk_atoms="negation",
                reviewer_critical_atoms="negation",
                reviewer_asr_confusion_terms="negation dropped",
                reviewer_would_asr_error_change_decision="yes",
                reviewer_decision_change_reason="routing changed",
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
            )
        ],
    )
    fieldnames, rows = read_tsv(sheet)

    payload = validate_rows(fieldnames, rows, require_complete=True, expected_rows=1)
    counts = validation_count_rows(payload)
    assert_aggregate_safe(payload)

    assert payload["ok"] is True
    assert payload["status"] == "review_complete"
    assert payload["reviewed_rows"] == 1
    assert payload["reviewed_model_assessments"] == 1
    assert any(row["check"] == "schema_and_completion_gate" for row in counts)


def test_mismatched_model_assessment_run_id_fails_without_sensitive_leak(tmp_path: Path) -> None:
    sheet = tmp_path / "audit.tsv"
    write_rows(
        sheet,
        [
            base_row(
                reviewer_model_assessments_json=json.dumps(
                    [
                        {
                            "asr_run_id": "run_b",
                            "reviewer_would_asr_error_change_decision": "",
                            "reviewer_critical_atoms": "",
                            "reviewer_expected_safe_action": "",
                            "reviewer_annotation_confidence": "",
                        }
                    ],
                    ensure_ascii=False,
                )
            )
        ],
    )
    fieldnames, rows = read_tsv(sheet)

    payload = validate_rows(fieldnames, rows, require_complete=False, expected_rows=1)
    assert_aggregate_safe(payload)

    assert payload["ok"] is False
    assert payload["status"] == "validation_failed"
    assert payload["error_counts"]["model_assessment_run_id_mismatch"] == 1
    assert "PRIVATE_" not in json.dumps(payload, ensure_ascii=False)

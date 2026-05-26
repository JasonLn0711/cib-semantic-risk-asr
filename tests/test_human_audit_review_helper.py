from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "annotation"))

from review_human_risk_atom_audit import (  # noqa: E402
    ACCESS_LOG_FIELDS,
    access_log_row,
    append_tsv,
    default_access_log_path,
    parse_model_review,
    pending_summary,
    read_sheet,
    select_row,
    update_row_from_args,
    write_sheet,
)
from validate_human_risk_atom_audit import validate_rows  # noqa: E402


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


def review_args(**overrides: object) -> argparse.Namespace:
    values: dict[str, object] = {
        "verified_transcript": None,
        "semantic_risk_label": "priority_review",
        "risk_atoms": "negation,amount",
        "critical_atoms": "negation",
        "asr_confusion_terms": "negation dropped",
        "decision_change": "yes",
        "decision_change_reason": "routing changed",
        "expected_safe_action": "priority_review",
        "confidence": "high",
        "notes": "PRIVATE_REVIEWER_NOTE",
        "model_review": [
            "run_a:yes:negation:priority_review:high",
        ],
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def test_pending_summary_has_no_private_text(tmp_path: Path) -> None:
    sheet = tmp_path / "audit.tsv"
    write_rows(sheet, [base_row()])
    _fieldnames, rows = read_sheet(sheet)

    payload = pending_summary(rows)
    text = json.dumps(payload, ensure_ascii=False)

    assert payload["audit_rows"] == 1
    assert payload["pending_rows"] == 1
    assert payload["pending_row_numbers"] == [1]
    assert "unsafe_downrouting" in payload["pending_by_selection_stratum"]
    assert "PRIVATE_" not in text
    assert "audio_private_001" not in text


def test_show_row_access_log_is_repo_safe(tmp_path: Path) -> None:
    sheet = tmp_path / "run" / "artifacts" / "audit.tsv"
    sheet.parent.mkdir(parents=True, exist_ok=True)
    write_rows(sheet, [base_row()])
    _fieldnames, rows = read_sheet(sheet)

    access_log = default_access_log_path(sheet)
    payload = access_log_row(1, rows[0], audit_sheet=sheet, repo_root=tmp_path)
    append_tsv(access_log, payload, ACCESS_LOG_FIELDS)
    text = access_log.read_text(encoding="utf-8")

    assert access_log == tmp_path / "run" / "human_audit_local_row_access_log.tsv"
    assert payload["operation"] == "show_local_row"
    assert payload["row_number"] == 1
    assert payload["selection_stratum"] == "unsafe_downrouting"
    assert payload["reference_label"] == "priority_review"
    assert payload["asr_hypothesis_count"] == 1
    assert payload["model_assessment_count"] == 1
    assert "PRIVATE_" not in text
    assert "audio_private_001" not in text
    assert "audio_id" not in text
    assert "reference_text" not in text
    assert "hypothesis_text" not in text
    assert "reviewer_notes" not in text


def test_update_row_dry_run_completes_in_memory_without_writing(tmp_path: Path) -> None:
    sheet = tmp_path / "audit.tsv"
    write_rows(sheet, [base_row()])
    original_text = sheet.read_text(encoding="utf-8")
    fieldnames, rows = read_sheet(sheet)
    index, row = select_row(rows, row_number=1, audio_id=None)

    changed = update_row_from_args(row, review_args())
    payload = validate_rows(fieldnames, rows, require_complete=True, expected_rows=1)

    assert index == 0
    assert changed is True
    assert payload["ok"] is True
    assert payload["status"] == "review_complete"
    assert payload["reviewed_model_assessments"] == 1
    assert sheet.read_text(encoding="utf-8") == original_text


def test_write_sheet_persists_completed_review(tmp_path: Path) -> None:
    sheet = tmp_path / "audit.tsv"
    write_rows(sheet, [base_row()])
    fieldnames, rows = read_sheet(sheet)
    _index, row = select_row(rows, row_number=1, audio_id=None)

    update_row_from_args(row, review_args())
    write_sheet(sheet, fieldnames, rows)
    written_fieldnames, written_rows = read_sheet(sheet)
    payload = validate_rows(
        written_fieldnames,
        written_rows,
        require_complete=True,
        expected_rows=1,
    )

    assert payload["ok"] is True
    assert payload["reviewed_rows"] == 1
    assert payload["reviewed_model_assessments"] == 1
    assert "PRIVATE_REVIEWER_NOTE" in sheet.read_text(encoding="utf-8")


def test_missing_model_review_run_id_fails(tmp_path: Path) -> None:
    sheet = tmp_path / "audit.tsv"
    write_rows(sheet, [base_row()])
    _fieldnames, rows = read_sheet(sheet)
    _index, row = select_row(rows, row_number=1, audio_id=None)

    try:
        update_row_from_args(
            row,
            review_args(model_review=["missing_run:no:none:manual_review:medium"]),
        )
    except ValueError as exc:
        assert "model review run id not found" in str(exc)
    else:
        raise AssertionError("missing model run id did not fail")


def test_parse_model_review_rejects_invalid_atom() -> None:
    try:
        parse_model_review("run_a:yes:not_an_atom:priority_review:high")
    except ValueError as exc:
        assert "invalid atoms" in str(exc)
    else:
        raise AssertionError("invalid atom did not fail")

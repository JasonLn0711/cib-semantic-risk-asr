from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "annotation"))

from audit_human_review_batch_status import audit_batch_status  # noqa: E402


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


def row_for(stratum: str, *, reviewed: bool = False, model_reviewed: bool = False) -> dict[str, str]:
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


def write_sheet(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def write_batch(path: Path, row_numbers: list[int], stratum: str = "critical_or_high_risk_missed") -> None:
    path.write_text(
        json.dumps(
            {
                "selection_stratum": stratum,
                "row_numbers": row_numbers,
                "local_packet_path": "run/artifacts/review_batches/local.md",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def run_status(tmp_path: Path, rows: list[dict[str, str]], row_numbers: list[int]) -> dict:
    sheet = tmp_path / "audit.tsv"
    batch = tmp_path / "batch.json"
    write_sheet(sheet, rows)
    write_batch(batch, row_numbers)
    return audit_batch_status(
        audit_sheet=sheet,
        batch_summary=batch,
        output_dir=tmp_path,
        expected_rows=len(rows),
        repo_root=tmp_path,
    )


def test_batch_status_pending_is_aggregate_safe(tmp_path: Path) -> None:
    payload = run_status(
        tmp_path,
        [row_for("critical_or_high_risk_missed"), row_for("clean_control")],
        [1],
    )

    assert payload["ok"] is True
    assert payload["status"] == "batch_pending"
    assert payload["batch_ready_for_refresh"] is False
    assert payload["pending_rows_in_batch"] == 1
    assert payload["pending_model_assessments_in_batch"] == 1
    tracked_text = (
        (tmp_path / "human_audit_current_review_batch_status_summary.json").read_text(
            encoding="utf-8"
        )
        + (tmp_path / "human_audit_current_review_batch_status_rows.tsv").read_text(
            encoding="utf-8"
        )
    )
    assert "PRIVATE_" not in tracked_text
    assert "reference_text" not in tracked_text
    assert "hypothesis_text" not in tracked_text


def test_batch_status_complete_when_row_and_model_fields_done(tmp_path: Path) -> None:
    payload = run_status(
        tmp_path,
        [row_for("critical_or_high_risk_missed", reviewed=True, model_reviewed=True)],
        [1],
    )

    assert payload["status"] == "batch_complete"
    assert payload["batch_ready_for_refresh"] is True
    assert payload["reviewed_rows_in_batch"] == 1
    assert payload["reviewed_model_assessments_in_batch"] == 1


def test_batch_status_detects_stratum_mismatch(tmp_path: Path) -> None:
    payload = run_status(tmp_path, [row_for("clean_control")], [1])

    assert payload["ok"] is False
    assert payload["status"] == "batch_invalid"
    assert payload["stratum_mismatch_rows"] == [1]

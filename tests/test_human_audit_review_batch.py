from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "annotation"))

from prepare_human_audit_review_batch import prepare_batch  # noqa: E402


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
    model_assessments = []
    for run_id in ("run_a", "run_b", "run_c"):
        model_assessments.append(
            {
                "asr_run_id": run_id,
                "reviewer_would_asr_error_change_decision": "yes" if model_reviewed else "",
                "reviewer_critical_atoms": "negation" if model_reviewed else "",
                "reviewer_expected_safe_action": "priority_review" if model_reviewed else "",
                "reviewer_annotation_confidence": "high" if model_reviewed else "",
            }
        )
    row = {
        "audio_id": f"private_{stratum}",
        "split": "test",
        "selection_stratum": stratum,
        "selection_reason": "private reason",
        "reference_label": "priority_review",
        "reference_text": "PRIVATE_REFERENCE",
        "asr_hypotheses_json": json.dumps(
            [
                {"asr_run_id": "run_a", "hypothesis_text": "PRIVATE_A"},
                {"asr_run_id": "run_b", "hypothesis_text": "PRIVATE_B"},
                {"asr_run_id": "run_c", "hypothesis_text": "PRIVATE_C"},
            ],
            ensure_ascii=False,
        ),
        "risk_signal_json": json.dumps({"private": "PRIVATE_SIGNAL"}, ensure_ascii=False),
        "reviewer_verified_transcript": "",
        "reviewer_semantic_risk_label": "",
        "reviewer_risk_atoms": "",
        "reviewer_critical_atoms": "",
        "reviewer_asr_confusion_terms": "",
        "reviewer_would_asr_error_change_decision": "",
        "reviewer_decision_change_reason": "",
        "reviewer_expected_safe_action": "",
        "reviewer_annotation_confidence": "",
        "reviewer_model_assessments_json": json.dumps(model_assessments, ensure_ascii=False),
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


def test_prepare_next_batch_writes_safe_tracked_records_and_local_packet(tmp_path: Path) -> None:
    sheet = tmp_path / "run" / "artifacts" / "audit.tsv"
    output_dir = tmp_path / "run"
    packet_dir = output_dir / "artifacts" / "review_batches"
    write_sheet(
        sheet,
        [
            row_for("clean_control"),
            row_for("critical_or_high_risk_missed"),
            row_for("unsafe_downrouting"),
        ],
    )

    payload = prepare_batch(
        audit_sheet=sheet,
        output_dir=output_dir,
        local_packet_dir=packet_dir,
        selection_stratum=None,
        expected_rows=3,
        repo_root=tmp_path,
    )

    assert payload["ok"] is True
    assert payload["selection_stratum"] == "critical_or_high_risk_missed"
    assert payload["rows_in_batch"] == 1
    summary_path = output_dir / "human_audit_next_review_batch_summary.json"
    rows_path = output_dir / "human_audit_next_review_batch_rows.tsv"
    log_path = output_dir / "human_audit_review_batch_log.tsv"
    assert summary_path.exists()
    assert rows_path.exists()
    assert log_path.exists()
    assert (tmp_path / payload["local_packet_path"]).exists()

    tracked_text = (
        summary_path.read_text(encoding="utf-8")
        + rows_path.read_text(encoding="utf-8")
        + log_path.read_text(encoding="utf-8")
    )
    assert "PRIVATE_" not in tracked_text
    assert "reference_text" not in tracked_text
    assert "hypothesis_text" not in tracked_text
    assert "reviewer_model_assessments_json" not in tracked_text
    assert "PRIVATE_REFERENCE" in (tmp_path / payload["local_packet_path"]).read_text(
        encoding="utf-8"
    )


def test_prepare_requested_completed_stratum_fails(tmp_path: Path) -> None:
    sheet = tmp_path / "audit.tsv"
    write_sheet(sheet, [row_for("clean_control", reviewed=True, model_reviewed=True)])

    try:
        prepare_batch(
            audit_sheet=sheet,
            output_dir=tmp_path,
            local_packet_dir=tmp_path / "artifacts",
            selection_stratum="clean_control",
            expected_rows=1,
            repo_root=tmp_path,
        )
    except ValueError as exc:
        assert "no pending rows" in str(exc)
    else:
        raise AssertionError("completed stratum did not fail")

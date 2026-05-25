from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "annotation"))

from apply_human_audit_batch_response import (  # noqa: E402
    APPLY_LOG_FIELDS,
    APPLY_LOG_NAME,
    APPLY_LOG_SUMMARY_NAME,
    REVIEW_TIMING_FIELDS,
    TEMPLATE_FIELDS,
    apply_response_sheet,
    apply_response_sheet_workflow,
    prepare_response_template,
)
from validate_human_risk_atom_audit import read_tsv, validate_rows  # noqa: E402


AUDIT_FIELDS = [
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


def audit_row() -> dict[str, str]:
    return {
        "audio_id": "private_audio",
        "split": "test",
        "selection_stratum": "critical_or_high_risk_missed",
        "selection_reason": "private reason",
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


def load_readiness_fixture_writer():
    path = REPO_ROOT / "tests" / "test_evidence_chain_readiness.py"
    spec = importlib.util.spec_from_file_location("test_evidence_chain_readiness", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.write_minimal_tree


def write_tsv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_batch(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "selection_stratum": "critical_or_high_risk_missed",
                "row_numbers": [1],
                "local_packet_path": "run/artifacts/review_batches/local.md",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def write_session_start(path: Path, *, row_numbers: list[int] | None = None) -> None:
    path.write_text(
        json.dumps(
            {
                "ok": True,
                "status": "reviewer_session_started",
                "current_packet": {
                    "selection_stratum": "critical_or_high_risk_missed",
                    "row_numbers": row_numbers or [1],
                    "rows_in_batch": len(row_numbers or [1]),
                    "model_assessments_in_batch": len(row_numbers or [1]),
                },
                "current_gate": {
                    "rubric_status": "rubric_ready",
                    "checklist_status": "reviewer_action_ready",
                    "latest_apply_status": "response_pending",
                    "blocker_keys": [],
                },
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def complete_response_row() -> dict[str, str]:
    return {
        "row_number": "1",
        "selection_stratum": "critical_or_high_risk_missed",
        "asr_run_id": "run_a",
        "reviewer_semantic_risk_label": "priority_review",
        "reviewer_risk_atoms": "negation",
        "reviewer_critical_atoms": "negation",
        "reviewer_asr_confusion_terms": "negation dropped",
        "reviewer_would_asr_error_change_decision": "yes",
        "reviewer_decision_change_reason": "routing changed",
        "reviewer_expected_safe_action": "priority_review",
        "reviewer_annotation_confidence": "high",
        "reviewer_notes": "",
        "model_reviewer_would_asr_error_change_decision": "yes",
        "model_reviewer_critical_atoms": "negation",
        "model_reviewer_expected_safe_action": "priority_review",
        "model_reviewer_annotation_confidence": "high",
    }


def complete_response_row_with_timing() -> dict[str, str]:
    row = complete_response_row()
    row.update(
        {
            "review_started_at": "2026-05-25T21:30:00+08:00",
            "review_finished_at": "2026-05-25T21:31:30+08:00",
            "review_elapsed_seconds": "90",
        }
    )
    return row


def pending_audit_row(index: int) -> dict[str, str]:
    row = audit_row()
    row["audio_id"] = f"private_audio_{index:03d}"
    row["selection_stratum"] = "clean_control"
    return row


def test_prepare_response_template_tracks_only_safe_summary(tmp_path: Path) -> None:
    audit_sheet = tmp_path / "artifacts" / "audit.tsv"
    batch_summary = tmp_path / "batch.json"
    response_dir = tmp_path / "artifacts" / "responses"
    write_tsv(audit_sheet, [audit_row()], AUDIT_FIELDS)
    write_batch(batch_summary)

    payload = prepare_response_template(
        audit_sheet=audit_sheet,
        batch_summary=batch_summary,
        output_dir=tmp_path,
        response_dir=response_dir,
        expected_rows=1,
        repo_root=tmp_path,
    )

    assert payload["ok"] is True
    assert payload["status"] == "response_template_prepared"
    assert payload["response_rows"] == 1
    assert payload["template_column_count"] == len(TEMPLATE_FIELDS)
    _fieldnames, template_rows = read_tsv(tmp_path / payload["local_response_template_path"])
    assert all(field in _fieldnames for field in REVIEW_TIMING_FIELDS)
    assert template_rows[0]["review_elapsed_seconds"] == ""
    tracked = (tmp_path / "human_audit_batch_response_template_summary.json").read_text(
        encoding="utf-8"
    )
    assert "PRIVATE_" not in tracked
    assert "reference_text" not in tracked
    assert "reviewer_notes" not in tracked
    assert (tmp_path / payload["local_response_template_path"]).exists()


def test_blank_response_dry_run_is_pending_and_safe(tmp_path: Path) -> None:
    audit_sheet = tmp_path / "audit.tsv"
    batch_summary = tmp_path / "batch.json"
    response_sheet = tmp_path / "response.tsv"
    write_tsv(audit_sheet, [audit_row()], AUDIT_FIELDS)
    write_batch(batch_summary)
    write_tsv(
        response_sheet,
        [
            {
                "row_number": "1",
                "selection_stratum": "critical_or_high_risk_missed",
                "asr_run_id": "run_a",
            }
        ],
        TEMPLATE_FIELDS,
    )

    payload = apply_response_sheet(
        audit_sheet=audit_sheet,
        response_sheet=response_sheet,
        batch_summary=batch_summary,
        output_dir=tmp_path,
        expected_rows=1,
        repo_root=tmp_path,
        write=False,
    )

    assert payload["ok"] is True
    assert payload["status"] == "response_pending"
    assert payload["pending_rows_in_response"] == 1
    tracked = (tmp_path / "human_audit_batch_response_apply_summary.json").read_text(
        encoding="utf-8"
    )
    assert "PRIVATE_" not in tracked
    assert "reference_text" not in tracked


def test_require_complete_fails_blank_response_without_writing(tmp_path: Path) -> None:
    audit_sheet = tmp_path / "audit.tsv"
    batch_summary = tmp_path / "batch.json"
    response_sheet = tmp_path / "response.tsv"
    write_tsv(audit_sheet, [audit_row()], AUDIT_FIELDS)
    write_batch(batch_summary)
    write_tsv(
        response_sheet,
        [
            {
                "row_number": "1",
                "selection_stratum": "critical_or_high_risk_missed",
                "asr_run_id": "run_a",
            }
        ],
        TEMPLATE_FIELDS,
    )
    before = audit_sheet.read_text(encoding="utf-8")

    payload = apply_response_sheet(
        audit_sheet=audit_sheet,
        response_sheet=response_sheet,
        batch_summary=batch_summary,
        output_dir=tmp_path,
        expected_rows=1,
        repo_root=tmp_path,
        write=False,
        require_complete=True,
    )

    assert payload["ok"] is False
    assert payload["status"] == "response_pending"
    assert payload["mode"] == "dry_run"
    assert payload["require_complete"] is True
    assert payload["error_counts"] == {"incomplete_response": 1}
    assert audit_sheet.read_text(encoding="utf-8") == before
    tracked = (tmp_path / "human_audit_batch_response_apply_summary.json").read_text(
        encoding="utf-8"
    )
    assert "PRIVATE_" not in tracked
    assert "reference_text" not in tracked


def test_require_complete_passes_complete_dry_run(tmp_path: Path) -> None:
    audit_sheet = tmp_path / "audit.tsv"
    batch_summary = tmp_path / "batch.json"
    response_sheet = tmp_path / "response.tsv"
    write_tsv(audit_sheet, [audit_row()], AUDIT_FIELDS)
    write_batch(batch_summary)
    write_tsv(response_sheet, [complete_response_row()], TEMPLATE_FIELDS)

    payload = apply_response_sheet(
        audit_sheet=audit_sheet,
        response_sheet=response_sheet,
        batch_summary=batch_summary,
        output_dir=tmp_path,
        expected_rows=1,
        repo_root=tmp_path,
        write=False,
        require_complete=True,
    )

    assert payload["ok"] is True
    assert payload["status"] == "response_complete"
    assert payload["mode"] == "dry_run"
    assert payload["require_complete"] is True
    assert payload["review_timing"]["rows_with_timing"] == 0
    assert payload["review_timing"]["rows_missing_timing"] == 1
    assert payload["error_counts"] == {}


def test_require_complete_rejects_inconsistent_response_decisions(tmp_path: Path) -> None:
    audit_sheet = tmp_path / "audit.tsv"
    batch_summary = tmp_path / "batch.json"
    response_sheet = tmp_path / "response.tsv"
    write_tsv(audit_sheet, [audit_row()], AUDIT_FIELDS)
    write_batch(batch_summary)
    response = complete_response_row()
    response.update(
        {
            "reviewer_risk_atoms": "amount",
            "reviewer_critical_atoms": "negation",
            "reviewer_expected_safe_action": "none",
            "model_reviewer_critical_atoms": "negation",
            "model_reviewer_expected_safe_action": "none",
        }
    )
    write_tsv(response_sheet, [response], TEMPLATE_FIELDS)

    payload = apply_response_sheet(
        audit_sheet=audit_sheet,
        response_sheet=response_sheet,
        batch_summary=batch_summary,
        output_dir=tmp_path,
        expected_rows=1,
        repo_root=tmp_path,
        write=False,
        require_complete=True,
    )

    assert payload["ok"] is False
    assert payload["status"] == "response_invalid"
    assert payload["error_counts"]["critical_atom_not_in_risk_atoms"] == 1
    assert payload["error_counts"]["decision_change_yes_requires_non_none_safe_action"] == 1
    assert payload["error_counts"]["model_critical_atom_not_in_row_risk_atoms"] == 1
    assert (
        payload["error_counts"]["model_decision_change_yes_requires_non_none_safe_action"]
        == 1
    )


def test_require_session_start_gate_blocks_complete_dry_run_when_missing(
    tmp_path: Path,
) -> None:
    audit_sheet = tmp_path / "audit.tsv"
    batch_summary = tmp_path / "batch.json"
    response_sheet = tmp_path / "response.tsv"
    write_tsv(audit_sheet, [audit_row()], AUDIT_FIELDS)
    write_batch(batch_summary)
    write_tsv(response_sheet, [complete_response_row()], TEMPLATE_FIELDS)

    payload = apply_response_sheet(
        audit_sheet=audit_sheet,
        response_sheet=response_sheet,
        batch_summary=batch_summary,
        output_dir=tmp_path,
        expected_rows=1,
        repo_root=tmp_path,
        write=False,
        require_complete=True,
        session_start_summary=tmp_path / "missing_session_start.json",
        require_session_start=True,
    )

    assert payload["ok"] is False
    assert payload["status"] == "response_invalid"
    assert payload["session_start_gate"]["status"] == "missing"
    assert payload["error_counts"] == {"session_start_missing": 1}


def test_require_session_start_gate_passes_matching_complete_dry_run(
    tmp_path: Path,
) -> None:
    audit_sheet = tmp_path / "audit.tsv"
    batch_summary = tmp_path / "batch.json"
    response_sheet = tmp_path / "response.tsv"
    session_start = tmp_path / "human_audit_reviewer_session_start_summary.json"
    write_tsv(audit_sheet, [audit_row()], AUDIT_FIELDS)
    write_batch(batch_summary)
    write_tsv(response_sheet, [complete_response_row()], TEMPLATE_FIELDS)
    write_session_start(session_start)

    payload = apply_response_sheet(
        audit_sheet=audit_sheet,
        response_sheet=response_sheet,
        batch_summary=batch_summary,
        output_dir=tmp_path,
        expected_rows=1,
        repo_root=tmp_path,
        write=False,
        require_complete=True,
        session_start_summary=session_start,
        require_session_start=True,
    )

    assert payload["ok"] is True
    assert payload["status"] == "response_complete"
    assert payload["session_start_gate"]["ok"] is True
    assert payload["session_start_gate"]["row_numbers_match"] is True
    assert payload["session_start_gate"]["selection_stratum_match"] is True


def test_write_requires_session_start_gate_when_requested(tmp_path: Path) -> None:
    audit_sheet = tmp_path / "audit.tsv"
    batch_summary = tmp_path / "batch.json"
    response_sheet = tmp_path / "response.tsv"
    write_tsv(audit_sheet, [audit_row()], AUDIT_FIELDS)
    write_batch(batch_summary)
    write_tsv(response_sheet, [complete_response_row()], TEMPLATE_FIELDS)
    before = audit_sheet.read_text(encoding="utf-8")

    payload = apply_response_sheet(
        audit_sheet=audit_sheet,
        response_sheet=response_sheet,
        batch_summary=batch_summary,
        output_dir=tmp_path,
        expected_rows=1,
        repo_root=tmp_path,
        write=True,
        require_complete=True,
        session_start_summary=tmp_path / "missing_session_start.json",
        require_session_start=True,
    )

    assert payload["ok"] is False
    assert payload["status"] == "response_invalid"
    assert payload["error_counts"] == {
        "session_start_missing": 1,
        "write_requires_valid_preconditions": 1,
    }
    assert audit_sheet.read_text(encoding="utf-8") == before


def test_write_passes_with_matching_session_start_gate(tmp_path: Path) -> None:
    audit_sheet = tmp_path / "audit.tsv"
    batch_summary = tmp_path / "batch.json"
    response_sheet = tmp_path / "response.tsv"
    session_start = tmp_path / "human_audit_reviewer_session_start_summary.json"
    write_tsv(audit_sheet, [audit_row()], AUDIT_FIELDS)
    write_batch(batch_summary)
    write_tsv(response_sheet, [complete_response_row()], TEMPLATE_FIELDS)
    write_session_start(session_start)

    payload = apply_response_sheet(
        audit_sheet=audit_sheet,
        response_sheet=response_sheet,
        batch_summary=batch_summary,
        output_dir=tmp_path,
        expected_rows=1,
        repo_root=tmp_path,
        write=True,
        require_complete=True,
        session_start_summary=session_start,
        require_session_start=True,
    )
    fieldnames, rows = read_tsv(audit_sheet)
    validation_payload = validate_rows(fieldnames, rows, require_complete=True, expected_rows=1)

    assert payload["ok"] is True
    assert payload["status"] == "response_complete"
    assert payload["session_start_gate"]["ok"] is True
    assert validation_payload["ok"] is True


def test_legacy_response_without_timing_columns_still_passes(tmp_path: Path) -> None:
    audit_sheet = tmp_path / "audit.tsv"
    batch_summary = tmp_path / "batch.json"
    response_sheet = tmp_path / "response.tsv"
    write_tsv(audit_sheet, [audit_row()], AUDIT_FIELDS)
    write_batch(batch_summary)
    legacy_fields = [field for field in TEMPLATE_FIELDS if field not in REVIEW_TIMING_FIELDS]
    write_tsv(response_sheet, [complete_response_row()], legacy_fields)

    payload = apply_response_sheet(
        audit_sheet=audit_sheet,
        response_sheet=response_sheet,
        batch_summary=batch_summary,
        output_dir=tmp_path,
        expected_rows=1,
        repo_root=tmp_path,
        write=False,
        require_complete=True,
    )

    assert payload["ok"] is True
    assert payload["status"] == "response_complete"
    assert payload["review_timing"]["rows_missing_timing"] == 1


def test_review_timing_is_aggregated_without_becoming_required(tmp_path: Path) -> None:
    audit_sheet = tmp_path / "audit.tsv"
    batch_summary = tmp_path / "batch.json"
    response_sheet = tmp_path / "response.tsv"
    write_tsv(audit_sheet, [audit_row()], AUDIT_FIELDS)
    write_batch(batch_summary)
    write_tsv(response_sheet, [complete_response_row_with_timing()], TEMPLATE_FIELDS)

    payload = apply_response_sheet(
        audit_sheet=audit_sheet,
        response_sheet=response_sheet,
        batch_summary=batch_summary,
        output_dir=tmp_path,
        expected_rows=1,
        repo_root=tmp_path,
        write=False,
        require_complete=True,
    )

    assert payload["ok"] is True
    assert payload["review_timing"]["rows_with_timing"] == 1
    assert payload["review_timing"]["rows_missing_timing"] == 0
    assert payload["review_timing"]["total_review_elapsed_seconds"] == 90.0
    tracked = (tmp_path / "human_audit_batch_response_apply_summary.json").read_text(
        encoding="utf-8"
    )
    assert "PRIVATE_" not in tracked
    assert "reference_text" not in tracked


def test_require_timing_rejects_complete_response_without_timing(tmp_path: Path) -> None:
    audit_sheet = tmp_path / "audit.tsv"
    batch_summary = tmp_path / "batch.json"
    response_sheet = tmp_path / "response.tsv"
    write_tsv(audit_sheet, [audit_row()], AUDIT_FIELDS)
    write_batch(batch_summary)
    write_tsv(response_sheet, [complete_response_row()], TEMPLATE_FIELDS)

    payload = apply_response_sheet(
        audit_sheet=audit_sheet,
        response_sheet=response_sheet,
        batch_summary=batch_summary,
        output_dir=tmp_path,
        expected_rows=1,
        repo_root=tmp_path,
        write=False,
        require_complete=True,
        require_timing=True,
    )

    assert payload["ok"] is False
    assert payload["status"] == "response_invalid"
    assert payload["require_timing"] is True
    assert payload["review_timing"]["timing_requirement"] == "required"
    assert payload["error_counts"] == {"missing_review_timing": 1}


def test_require_timing_passes_complete_response_with_timing(tmp_path: Path) -> None:
    audit_sheet = tmp_path / "audit.tsv"
    batch_summary = tmp_path / "batch.json"
    response_sheet = tmp_path / "response.tsv"
    write_tsv(audit_sheet, [audit_row()], AUDIT_FIELDS)
    write_batch(batch_summary)
    write_tsv(response_sheet, [complete_response_row_with_timing()], TEMPLATE_FIELDS)

    payload = apply_response_sheet(
        audit_sheet=audit_sheet,
        response_sheet=response_sheet,
        batch_summary=batch_summary,
        output_dir=tmp_path,
        expected_rows=1,
        repo_root=tmp_path,
        write=False,
        require_complete=True,
        require_timing=True,
    )

    assert payload["ok"] is True
    assert payload["status"] == "response_complete"
    assert payload["require_timing"] is True
    assert payload["review_timing"]["rows_missing_timing"] == 0
    assert payload["error_counts"] == {}


def test_apply_log_schema_migrates_when_require_timing_is_added(tmp_path: Path) -> None:
    audit_sheet = tmp_path / "audit.tsv"
    batch_summary = tmp_path / "batch.json"
    response_sheet = tmp_path / "response.tsv"
    write_tsv(audit_sheet, [audit_row()], AUDIT_FIELDS)
    write_batch(batch_summary)
    write_tsv(response_sheet, [complete_response_row_with_timing()], TEMPLATE_FIELDS)
    legacy_log_fields = [field for field in APPLY_LOG_FIELDS if field != "require_timing"]
    write_tsv(
        tmp_path / APPLY_LOG_NAME,
        [
            {
                "recorded_at": "2026-05-25T22:16:17+08:00",
                "ok": "False",
                "status": "response_pending",
                "mode": "dry_run",
                "require_complete": "True",
                "error_count_total": "1",
                "error_keys": "incomplete_response",
            }
        ],
        legacy_log_fields,
    )

    payload = apply_response_sheet_workflow(
        audit_sheet=audit_sheet,
        response_sheet=response_sheet,
        batch_summary=batch_summary,
        output_dir=tmp_path,
        readiness_output_dir=tmp_path / "readiness",
        local_packet_dir=tmp_path / "artifacts" / "review_batches",
        response_dir=tmp_path / "artifacts" / "review_responses",
        expected_rows=1,
        repo_root=tmp_path,
        write=False,
        require_complete=True,
        require_timing=True,
    )
    log_fieldnames, log_rows = read_tsv(tmp_path / APPLY_LOG_NAME)
    log_summary = json.loads((tmp_path / APPLY_LOG_SUMMARY_NAME).read_text(encoding="utf-8"))

    assert payload["ok"] is True
    assert log_fieldnames == APPLY_LOG_FIELDS
    assert len(log_rows) == 2
    assert log_rows[-1]["require_timing"] == "True"
    assert log_summary["ok"] is True
    assert log_summary["missing_log_columns"] == []


def test_invalid_review_timing_fails_value_validation(tmp_path: Path) -> None:
    audit_sheet = tmp_path / "audit.tsv"
    batch_summary = tmp_path / "batch.json"
    response_sheet = tmp_path / "response.tsv"
    response_row = complete_response_row()
    response_row["review_elapsed_seconds"] = "-1"
    write_tsv(audit_sheet, [audit_row()], AUDIT_FIELDS)
    write_batch(batch_summary)
    write_tsv(response_sheet, [response_row], TEMPLATE_FIELDS)

    payload = apply_response_sheet(
        audit_sheet=audit_sheet,
        response_sheet=response_sheet,
        batch_summary=batch_summary,
        output_dir=tmp_path,
        expected_rows=1,
        repo_root=tmp_path,
        write=False,
        require_complete=True,
    )

    assert payload["ok"] is False
    assert payload["status"] == "response_invalid"
    assert payload["error_counts"]["invalid_review_elapsed_seconds"] == 1


def test_complete_response_write_updates_audit_sheet(tmp_path: Path) -> None:
    audit_sheet = tmp_path / "audit.tsv"
    batch_summary = tmp_path / "batch.json"
    response_sheet = tmp_path / "response.tsv"
    write_tsv(audit_sheet, [audit_row()], AUDIT_FIELDS)
    write_batch(batch_summary)
    write_tsv(response_sheet, [complete_response_row()], TEMPLATE_FIELDS)

    payload = apply_response_sheet(
        audit_sheet=audit_sheet,
        response_sheet=response_sheet,
        batch_summary=batch_summary,
        output_dir=tmp_path,
        expected_rows=1,
        repo_root=tmp_path,
        write=True,
    )
    fieldnames, rows = read_tsv(audit_sheet)
    validation_payload = validate_rows(fieldnames, rows, require_complete=True, expected_rows=1)

    assert payload["ok"] is True
    assert payload["status"] == "response_complete"
    assert payload["mode"] == "write"
    assert validation_payload["ok"] is True
    assert validation_payload["status"] == "review_complete"


def test_write_can_refresh_batch_status_and_aggregate_outputs(tmp_path: Path) -> None:
    load_readiness_fixture_writer()(tmp_path)
    run_dir = (
        tmp_path
        / "70_experiments"
        / "runs"
        / "janus_300_high_stakes_human_audit_selection_2026_05_25"
    )
    readiness_dir = tmp_path / "70_experiments" / "runs" / "postdoc_evidence_chain_2026_05_25"
    audit_sheet = run_dir / "artifacts" / "audit.tsv"
    batch_summary = run_dir / "batch.json"
    response_sheet = run_dir / "artifacts" / "response.tsv"
    rows = [audit_row()] + [pending_audit_row(index) for index in range(2, 31)]
    write_tsv(audit_sheet, rows, AUDIT_FIELDS)
    write_batch(batch_summary)
    write_tsv(response_sheet, [complete_response_row()], TEMPLATE_FIELDS)

    payload = apply_response_sheet_workflow(
        audit_sheet=audit_sheet,
        response_sheet=response_sheet,
        batch_summary=batch_summary,
        output_dir=run_dir,
        readiness_output_dir=readiness_dir,
        local_packet_dir=run_dir / "artifacts" / "review_batches",
        response_dir=run_dir / "artifacts" / "review_responses",
        expected_rows=30,
        repo_root=tmp_path,
        write=True,
        require_complete=True,
        refresh_after_write=True,
        prepare_next_after_write=True,
    )

    assert payload["ok"] is True
    assert payload["status"] == "response_complete"
    assert payload["post_write_batch_status"] == "batch_complete"
    assert payload["post_write_refresh_ran"] is True
    assert payload["post_write_refresh_status"] == "partial_review"
    assert payload["post_write_refresh_ok"] is True
    assert payload["post_write_paper_ready"] is False
    assert payload["post_write_publishable_ready"] is False
    assert payload["post_write_next_batch_prepared"] is True
    assert payload["post_write_next_selection_stratum"] == "clean_control"
    assert payload["post_write_next_rows_in_batch"] == 29
    assert payload["post_write_next_response_template_path"]
    assert (run_dir / "human_audit_current_review_batch_status_summary.json").exists()
    assert (run_dir / "human_audit_refresh_summary.json").exists()
    assert (run_dir / "human_audit_next_review_batch_summary.json").exists()
    assert (run_dir / "human_audit_batch_response_template_summary.json").exists()
    assert (run_dir / APPLY_LOG_NAME).exists()
    assert (run_dir / APPLY_LOG_SUMMARY_NAME).exists()
    assert (readiness_dir / "publishable_evidence_completion_summary.json").exists()
    _log_fieldnames, log_rows = read_tsv(run_dir / APPLY_LOG_NAME)
    assert len(log_rows) == 1
    assert log_rows[0]["status"] == "response_complete"
    assert log_rows[0]["post_write_refresh_ran"] == "True"
    assert log_rows[0]["post_write_next_batch_prepared"] == "True"
    assert log_rows[0]["rows_missing_timing"] == "1"
    log_summary = json.loads((run_dir / APPLY_LOG_SUMMARY_NAME).read_text(encoding="utf-8"))
    assert log_summary["ok"] is True
    assert log_summary["status"] == "apply_log_valid"
    assert log_summary["apply_log_entries"] == 1
    assert log_summary["latest"]["status"] == "response_complete"
    assert log_summary["latest"]["rows_missing_timing"] == 1
    tracked = (run_dir / "human_audit_batch_response_apply_summary.json").read_text(
        encoding="utf-8"
    )
    assert "PRIVATE_" not in tracked
    assert "reference_text" not in tracked
    log_text = (run_dir / APPLY_LOG_NAME).read_text(encoding="utf-8")
    assert "PRIVATE_" not in log_text
    assert "reference_text" not in log_text
    assert "PRIVATE_" not in json.dumps(log_summary, ensure_ascii=False)
    assert "reference_text" not in json.dumps(log_summary, ensure_ascii=False)

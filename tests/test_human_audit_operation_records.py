from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "annotation"))
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "scoring"))
sys.path.insert(0, str(REPO_ROOT / "tests"))

from audit_human_audit_operation_records import (  # noqa: E402
    LOCAL_ROW_ACCESS_LOG_FIELDS,
    SUMMARY_NAME,
    TSV_NAME,
    build_operation_record_audit,
    write_json,
    write_tsv,
)
from audit_evidence_chain_consistency import SUMMARY_SPECS  # noqa: E402
from test_evidence_chain_consistency import write_consistent_fixture  # noqa: E402


def test_operation_record_audit_passes_current_pending_fixture(tmp_path: Path) -> None:
    write_consistent_fixture(tmp_path)
    run_dir = tmp_path / Path(SUMMARY_SPECS["work_order"]).parent

    payload, rows = build_operation_record_audit(run_dir=run_dir, repo_root=tmp_path)

    assert payload["ok"] is True
    assert payload["status"] == "operation_records_ready"
    assert payload["required_operation_log_count"] == 6
    assert payload["passed_operation_record_count"] == 6
    assert payload["failed_operation_record_count"] == 0
    assert payload["current_packet"]["rows_in_batch"] == 6
    assert payload["current_packet"]["rows_missing_timing"] == 6
    assert payload["next_reviewer_operation"]["current_step"]["work_order_id"] == (
        "row-1:01-mark-timing-start"
    )
    assert payload["next_local_row_access_log"]["route_ok"] is True
    assert payload["next_local_row_access_log"]["status"] == "planned_not_yet_recorded"
    assert payload["next_local_row_access_log"]["exists"] is False
    assert payload["next_local_row_access_log"]["row_count"] == 0
    assert payload["next_local_row_access_log"]["required_fields_present"] is False
    assert payload["next_local_row_access_log"]["latest_record_ok"] is False
    assert payload["next_local_row_access_log"]["path"].endswith(
        "human_audit_local_row_access_log.tsv"
    )
    assert {row["operation_log_id"] for row in rows} == {
        "review_batch",
        "preflight",
        "session_start",
        "strict_apply",
        "timing_helper",
        "post_review_sequence",
    }

    write_json(run_dir / SUMMARY_NAME, payload)
    write_tsv(run_dir / TSV_NAME, rows)
    assert (run_dir / SUMMARY_NAME).exists()
    assert (run_dir / TSV_NAME).exists()


def test_operation_record_audit_accepts_recorded_access_log_for_next_row(
    tmp_path: Path,
) -> None:
    write_consistent_fixture(tmp_path)
    run_dir = tmp_path / Path(SUMMARY_SPECS["work_order"]).parent
    access_log = run_dir / "human_audit_local_row_access_log.tsv"
    access_log.write_text(
        "\t".join(LOCAL_ROW_ACCESS_LOG_FIELDS)
        + "\n"
        + "\t".join(
            [
                "2026-05-26T09:30:00",
                "show_local_row",
                "1",
                "critical_or_high_risk_missed",
                "priority_review",
                "3",
                "3",
                "shown",
                "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/human_risk_atom_audit_sheet.tsv",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    payload, _rows = build_operation_record_audit(run_dir=run_dir, repo_root=tmp_path)

    access_status = payload["next_local_row_access_log"]
    assert access_status["status"] == "recorded"
    assert access_status["exists"] is True
    assert access_status["row_count"] == 1
    assert access_status["required_fields_present"] is True
    assert access_status["latest_record_ok"] is True
    assert access_status["row_matches_next_operation"] is True
    assert access_status["latest_operation"] == "show_local_row"
    assert access_status["latest_access_status"] == "shown"


def test_operation_record_audit_fails_missing_required_log(tmp_path: Path) -> None:
    write_consistent_fixture(tmp_path)
    run_dir = tmp_path / Path(SUMMARY_SPECS["work_order"]).parent
    (run_dir / "human_audit_batch_response_apply_log.tsv").unlink()

    payload, rows = build_operation_record_audit(run_dir=run_dir, repo_root=tmp_path)

    assert payload["ok"] is False
    assert payload["status"] == "operation_records_drift"
    assert payload["failed_operation_record_count"] == 1
    failed = [row for row in rows if row["alignment_status"] == "fail"]
    assert failed[0]["operation_log_id"] == "strict_apply"

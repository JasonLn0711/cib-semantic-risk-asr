from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "annotation"))

from build_human_audit_reviewer_action_checklist import build_checklist  # noqa: E402
from build_human_audit_reviewer_handoff import build_handoff  # noqa: E402
from test_human_audit_reviewer_preflight import write_current_handoff  # noqa: E402


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_rubric(run_dir: Path) -> None:
    write_json(
        run_dir / "human_audit_reviewer_rubric_summary.json",
        {
            "ok": True,
            "status": "rubric_ready",
            "validator_constants_match": True,
        },
    )


def test_action_checklist_marks_ready_but_review_pending(tmp_path: Path) -> None:
    run_dir, paths = write_current_handoff(tmp_path)
    preflight = {
        "ok": True,
        "status": "review_session_ready",
        "recorded_at": "2026-05-25T22:47:48+08:00",
    }
    write_json(run_dir / "human_audit_reviewer_preflight_summary.json", preflight)
    write_rubric(run_dir)

    payload, rows = build_checklist(
        run_dir=run_dir,
        handoff_summary_path=run_dir / "human_audit_reviewer_handoff_summary.json",
        preflight_summary_path=run_dir / "human_audit_reviewer_preflight_summary.json",
        batch_summary_path=paths["batch_summary"],
        batch_status_path=paths["batch_status"],
        template_summary_path=paths["template_summary"],
        apply_summary_path=paths["apply_summary"],
        apply_log_summary_path=paths["apply_log_summary"],
        rubric_summary_path=run_dir / "human_audit_reviewer_rubric_summary.json",
        repo_root=tmp_path,
    )

    assert payload["ok"] is True
    assert payload["status"] == "reviewer_action_ready"
    assert payload["pending_rows_in_batch"] == 2
    assert payload["pending_model_assessments_in_batch"] == 6
    assert "mark_human_audit_response_timing.py" in payload["timing_helper_commands"]["timing_start_write"]
    assert sorted(payload["timing_helper_commands"]["timing_start_write_by_row"]) == ["1", "2"]
    assert "--row-number 2" in payload["timing_helper_commands"]["timing_finish_write_by_row"]["2"]
    status_by_step = {row["step_id"]: row["status"] for row in rows}
    assert status_by_step["3b"] == "ready"
    assert status_by_step["4"] == "pending"
    assert status_by_step["5"] == "pending"
    assert status_by_step["8"] == "blocked_until_response_complete"
    step_6 = next(row for row in rows if row["step_id"] == "6")
    assert "helper_rows=1,2" in step_6["next_action"]
    assert "timing_start_write_by_row/timing_finish_write_by_row" in step_6["next_action"]
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "PRIVATE_" not in serialized
    assert "reference_text" not in serialized
    assert "hypothesis_text" not in serialized


def test_action_checklist_blocks_missing_preflight(tmp_path: Path) -> None:
    run_dir, paths = write_current_handoff(tmp_path)
    write_rubric(run_dir)

    payload, rows = build_checklist(
        run_dir=run_dir,
        handoff_summary_path=run_dir / "human_audit_reviewer_handoff_summary.json",
        preflight_summary_path=run_dir / "human_audit_reviewer_preflight_summary.json",
        batch_summary_path=paths["batch_summary"],
        batch_status_path=paths["batch_status"],
        template_summary_path=paths["template_summary"],
        apply_summary_path=paths["apply_summary"],
        apply_log_summary_path=paths["apply_log_summary"],
        rubric_summary_path=run_dir / "human_audit_reviewer_rubric_summary.json",
        repo_root=tmp_path,
    )

    assert payload["ok"] is False
    assert payload["status"] == "reviewer_action_blocked"
    assert payload["blocker_keys"] == ["preflight_not_ready"]
    status_by_step = {row["step_id"]: row["status"] for row in rows}
    assert status_by_step["3"] == "blocked"


def test_action_checklist_marks_write_ready_after_response_complete(tmp_path: Path) -> None:
    run_dir, paths = write_current_handoff(tmp_path)
    write_json(
        paths["batch_status"],
        {
            "ok": True,
            "status": "batch_pending",
            "batch_ready_for_refresh": False,
            "reviewed_rows_in_batch": 2,
            "pending_rows_in_batch": 0,
            "model_assessments_in_batch": 6,
            "reviewed_model_assessments_in_batch": 6,
            "pending_model_assessments_in_batch": 0,
        },
    )
    write_json(
        paths["apply_summary"],
        {
            "ok": True,
            "status": "response_complete",
            "reviewed_rows_in_response": 2,
            "pending_rows_in_response": 0,
            "reviewed_model_assessments_in_response": 6,
            "pending_model_assessments_in_response": 0,
            "review_timing": {"rows_with_timing": 2, "rows_missing_timing": 0},
        },
    )
    handoff = build_handoff(
        run_dir=run_dir,
        audit_sheet=run_dir / "artifacts" / "audit.tsv",
        batch_summary_path=paths["batch_summary"],
        batch_status_path=paths["batch_status"],
        template_summary_path=paths["template_summary"],
        apply_summary_path=paths["apply_summary"],
        apply_log_summary_path=paths["apply_log_summary"],
        readiness_output_dir=tmp_path / "readiness",
        expected_rows=30,
        repo_root=tmp_path,
    )
    write_json(run_dir / "human_audit_reviewer_handoff_summary.json", handoff)
    write_json(
        run_dir / "human_audit_reviewer_preflight_summary.json",
        {"ok": True, "status": "review_session_ready"},
    )
    write_rubric(run_dir)

    payload, rows = build_checklist(
        run_dir=run_dir,
        handoff_summary_path=run_dir / "human_audit_reviewer_handoff_summary.json",
        preflight_summary_path=run_dir / "human_audit_reviewer_preflight_summary.json",
        batch_summary_path=paths["batch_summary"],
        batch_status_path=paths["batch_status"],
        template_summary_path=paths["template_summary"],
        apply_summary_path=paths["apply_summary"],
        apply_log_summary_path=paths["apply_log_summary"],
        rubric_summary_path=run_dir / "human_audit_reviewer_rubric_summary.json",
        repo_root=tmp_path,
    )

    assert payload["status"] == "response_complete_ready_to_write"
    status_by_step = {row["step_id"]: row["status"] for row in rows}
    assert status_by_step["7"] == "complete"
    assert status_by_step["8"] == "ready"


def test_action_checklist_blocks_missing_rubric(tmp_path: Path) -> None:
    run_dir, paths = write_current_handoff(tmp_path)
    write_json(
        run_dir / "human_audit_reviewer_preflight_summary.json",
        {"ok": True, "status": "review_session_ready"},
    )

    payload, rows = build_checklist(
        run_dir=run_dir,
        handoff_summary_path=run_dir / "human_audit_reviewer_handoff_summary.json",
        preflight_summary_path=run_dir / "human_audit_reviewer_preflight_summary.json",
        batch_summary_path=paths["batch_summary"],
        batch_status_path=paths["batch_status"],
        template_summary_path=paths["template_summary"],
        apply_summary_path=paths["apply_summary"],
        apply_log_summary_path=paths["apply_log_summary"],
        rubric_summary_path=run_dir / "human_audit_reviewer_rubric_summary.json",
        repo_root=tmp_path,
    )

    assert payload["ok"] is False
    assert payload["status"] == "reviewer_action_blocked"
    assert payload["blocker_keys"] == ["rubric_not_ready"]
    status_by_step = {row["step_id"]: row["status"] for row in rows}
    assert status_by_step["3b"] == "blocked"

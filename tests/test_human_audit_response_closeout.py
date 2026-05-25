from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "annotation"))

from build_human_audit_response_closeout_checklist import (  # noqa: E402
    RESPONSE_GAP_TSV_NAME,
    build_closeout,
    write_gap_tsv,
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_closeout_inputs(
    run_dir: Path,
    *,
    response_complete: bool,
    session_gate_ok: bool = True,
) -> dict[str, Path]:
    apply_summary = run_dir / "human_audit_batch_response_apply_summary.json"
    apply_log_summary = run_dir / "human_audit_batch_response_apply_log_summary.json"
    session_start = run_dir / "human_audit_reviewer_session_start_summary.json"
    action_checklist = run_dir / "human_audit_reviewer_action_checklist_summary.json"
    handoff = run_dir / "human_audit_reviewer_handoff_summary.json"
    pending_rows = 0 if response_complete else 2
    pending_models = 0 if response_complete else 6
    status = "response_complete" if response_complete else "response_pending"
    write_json(
        apply_summary,
        {
            "ok": response_complete,
            "status": status,
            "mode": "dry_run",
            "require_complete": True,
            "require_timing": True,
            "selection_stratum": "critical_or_high_risk_missed",
            "rows_in_batch": 2,
            "reviewed_rows_in_response": 2 - pending_rows,
            "pending_rows_in_response": pending_rows,
            "reviewed_model_assessments_in_response": 6 - pending_models,
            "pending_model_assessments_in_response": pending_models,
            "session_start_gate": {
                "required": True,
                "ok": session_gate_ok,
                "status": "reviewer_session_started" if session_gate_ok else "missing",
                "row_numbers_match": session_gate_ok,
                "selection_stratum_match": session_gate_ok,
                "rubric_status": "rubric_ready" if session_gate_ok else "",
                "checklist_status": "reviewer_action_ready" if session_gate_ok else "",
                "blocker_keys": [],
            },
            "review_timing": {
                "rows_with_timing": 2 if response_complete else 0,
                "rows_missing_timing": 0 if response_complete else 2,
            },
            "response_gap_overview": {
                "rows_reported": 2,
                "rows_with_any_gap": 0 if response_complete else 2,
                "rows_with_row_field_gaps": 0 if response_complete else 2,
                "rows_with_model_assessment_gaps": 0 if response_complete else 2,
                "rows_with_timing_gaps": 0 if response_complete else 2,
                "total_row_fields_missing": 0 if response_complete else 16,
                "total_model_assessments_missing": 0 if response_complete else 6,
                "total_model_fields_missing": 0 if response_complete else 24,
            },
            "response_gap_summary_by_row": [
                {
                    "row_number": 1,
                    "has_gap": not response_complete,
                    "row_response_complete": response_complete,
                    "row_fields_missing_count": 0 if response_complete else 8,
                    "missing_row_fields": [] if response_complete else ["reviewer_risk_atoms"],
                    "model_assessments_expected_count": 3,
                    "model_assessments_complete_count": 3 if response_complete else 0,
                    "model_assessments_missing_count": 0 if response_complete else 3,
                    "model_fields_missing_count": 0 if response_complete else 12,
                    "missing_model_fields": [] if response_complete else ["model_reviewer_critical_atoms"],
                    "review_timing_complete": response_complete,
                    "review_timing_missing": not response_complete,
                },
                {
                    "row_number": 2,
                    "has_gap": not response_complete,
                    "row_response_complete": response_complete,
                    "row_fields_missing_count": 0 if response_complete else 8,
                    "missing_row_fields": [] if response_complete else ["reviewer_risk_atoms"],
                    "model_assessments_expected_count": 3,
                    "model_assessments_complete_count": 3 if response_complete else 0,
                    "model_assessments_missing_count": 0 if response_complete else 3,
                    "model_fields_missing_count": 0 if response_complete else 12,
                    "missing_model_fields": [] if response_complete else ["model_reviewer_critical_atoms"],
                    "review_timing_complete": response_complete,
                    "review_timing_missing": not response_complete,
                },
            ],
            "error_counts": {} if response_complete else {"incomplete_response": 1},
        },
    )
    write_json(
        apply_log_summary,
        {"ok": True, "status": "apply_log_valid", "apply_log_entries": 3},
    )
    write_json(
        session_start,
        {"ok": True, "status": "reviewer_session_started"},
    )
    write_json(
        action_checklist,
        {"ok": True, "status": "reviewer_action_ready"},
    )
    write_json(
        handoff,
        {
            "ok": True,
            "commands": {
                "strict_dry_run": "strict command",
                "write_refresh_prepare_next": "write command",
                "timing_start_write_by_row": {
                    "1": "mark_human_audit_response_timing.py --row-number 1 --mark-start --write",
                    "2": "mark_human_audit_response_timing.py --row-number 2 --mark-start --write",
                },
                "timing_finish_write_by_row": {
                    "1": "mark_human_audit_response_timing.py --row-number 1 --mark-finish --write",
                    "2": "mark_human_audit_response_timing.py --row-number 2 --mark-finish --write",
                },
            },
        },
    )
    return {
        "apply_summary": apply_summary,
        "apply_log_summary": apply_log_summary,
        "session_start": session_start,
        "action_checklist": action_checklist,
        "handoff": handoff,
    }


def test_closeout_blocks_pending_response_without_private_content(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    paths = write_closeout_inputs(run_dir, response_complete=False)

    payload, rows = build_closeout(
        run_dir=run_dir,
        apply_summary_path=paths["apply_summary"],
        apply_log_summary_path=paths["apply_log_summary"],
        session_start_summary_path=paths["session_start"],
        action_checklist_summary_path=paths["action_checklist"],
        handoff_summary_path=paths["handoff"],
        repo_root=tmp_path,
    )

    assert payload["ok"] is False
    assert payload["status"] == "response_closeout_blocked"
    assert payload["session_start_gate"]["ok"] is True
    assert payload["pending_rows_in_response"] == 2
    assert payload["pending_model_assessments_in_response"] == 6
    assert payload["response_gap_overview"]["rows_with_any_gap"] == 2
    assert payload["response_gap_summary_by_row"][0]["row_number"] == 1
    assert payload["response_gap_summary_by_row"][0]["has_gap"] is True
    assert "timing_start_write_by_row" in payload["response_gap_timing_commands"]
    assert payload["tracked_outputs"]["response_gap_tsv"].endswith(RESPONSE_GAP_TSV_NAME)
    assert "response_not_complete" in payload["blocker_keys"]
    assert "incomplete_response" in payload["blocker_keys"]
    status_by_step = {row["step_id"]: row["status"] for row in rows}
    assert status_by_step["7"] == "blocked_until_response_complete"
    serialized = json.dumps({"payload": payload, "rows": rows}, ensure_ascii=False)
    assert "PRIVATE_" not in serialized
    assert "reference_text" not in serialized
    assert "hypothesis_text" not in serialized


def test_write_gap_tsv_is_row_number_only_and_safe(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    paths = write_closeout_inputs(run_dir, response_complete=False)

    payload, _rows = build_closeout(
        run_dir=run_dir,
        apply_summary_path=paths["apply_summary"],
        apply_log_summary_path=paths["apply_log_summary"],
        session_start_summary_path=paths["session_start"],
        action_checklist_summary_path=paths["action_checklist"],
        handoff_summary_path=paths["handoff"],
        repo_root=tmp_path,
    )
    output_tsv = run_dir / RESPONSE_GAP_TSV_NAME
    write_gap_tsv(
        output_tsv,
        payload["response_gap_summary_by_row"],
        timing_commands=payload["response_gap_timing_commands"],
    )

    text = output_tsv.read_text(encoding="utf-8")
    assert text.splitlines()[0] == (
        "row_number\thas_gap\trow_response_complete\t"
        "row_fields_missing_count\tmissing_row_fields\t"
        "model_assessments_expected_count\tmodel_assessments_complete_count\t"
        "model_assessments_missing_count\tmodel_fields_missing_count\t"
        "missing_model_fields\treview_timing_complete\treview_timing_missing\t"
        "timing_start_write_command\ttiming_finish_write_command"
    )
    assert (
        "1\ttrue\tfalse\t8\treviewer_risk_atoms\t3\t0\t3\t12\t"
        "model_reviewer_critical_atoms\tfalse\ttrue\t"
        "mark_human_audit_response_timing.py --row-number 1 --mark-start --write\t"
        "mark_human_audit_response_timing.py --row-number 1 --mark-finish --write"
    ) in text
    assert (
        "2\ttrue\tfalse\t8\treviewer_risk_atoms\t3\t0\t3\t12\t"
        "model_reviewer_critical_atoms\tfalse\ttrue\t"
        "mark_human_audit_response_timing.py --row-number 2 --mark-start --write\t"
        "mark_human_audit_response_timing.py --row-number 2 --mark-finish --write"
    ) in text
    assert "PRIVATE_" not in text
    assert "audio_id" not in text
    assert "sample_id" not in text
    assert "reference_text" not in text
    assert "hypothesis_text" not in text
    assert "asr_hypotheses_json" not in text
    assert "reviewer_model_assessments_json" not in text
    assert "reviewer_notes" not in text
    assert "reviewer_verified_transcript" not in text


def test_closeout_marks_complete_response_ready_to_write(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    paths = write_closeout_inputs(run_dir, response_complete=True)

    payload, rows = build_closeout(
        run_dir=run_dir,
        apply_summary_path=paths["apply_summary"],
        apply_log_summary_path=paths["apply_log_summary"],
        session_start_summary_path=paths["session_start"],
        action_checklist_summary_path=paths["action_checklist"],
        handoff_summary_path=paths["handoff"],
        repo_root=tmp_path,
    )

    assert payload["ok"] is True
    assert payload["status"] == "response_complete_ready_to_write"
    assert payload["next_concrete_action"] == "Run the write/refresh/prepare-next command."
    status_by_step = {row["step_id"]: row["status"] for row in rows}
    assert status_by_step["3"] == "complete"
    assert status_by_step["4"] == "complete"
    assert status_by_step["5"] == "complete"
    assert status_by_step["7"] == "ready"


def test_closeout_blocks_complete_response_without_review_timing(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    paths = write_closeout_inputs(run_dir, response_complete=True)
    apply_summary = json.loads(paths["apply_summary"].read_text(encoding="utf-8"))
    apply_summary["ok"] = False
    apply_summary["status"] = "response_invalid"
    apply_summary["review_timing"] = {"rows_with_timing": 1, "rows_missing_timing": 1}
    apply_summary["error_counts"] = {"missing_review_timing": 1}
    write_json(paths["apply_summary"], apply_summary)

    payload, rows = build_closeout(
        run_dir=run_dir,
        apply_summary_path=paths["apply_summary"],
        apply_log_summary_path=paths["apply_log_summary"],
        session_start_summary_path=paths["session_start"],
        action_checklist_summary_path=paths["action_checklist"],
        handoff_summary_path=paths["handoff"],
        repo_root=tmp_path,
    )

    assert payload["ok"] is False
    assert "review_timing_not_complete" in payload["blocker_keys"]
    assert "missing_review_timing" in payload["blocker_keys"]
    status_by_step = {row["step_id"]: row["status"] for row in rows}
    assert status_by_step["5"] == "pending"


def test_closeout_blocks_session_gate_mismatch(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    paths = write_closeout_inputs(run_dir, response_complete=True, session_gate_ok=False)

    payload, _rows = build_closeout(
        run_dir=run_dir,
        apply_summary_path=paths["apply_summary"],
        apply_log_summary_path=paths["apply_log_summary"],
        session_start_summary_path=paths["session_start"],
        action_checklist_summary_path=paths["action_checklist"],
        handoff_summary_path=paths["handoff"],
        repo_root=tmp_path,
    )

    assert payload["ok"] is False
    assert payload["status"] == "response_closeout_blocked"
    assert "session_start_gate_not_ready" in payload["blocker_keys"]

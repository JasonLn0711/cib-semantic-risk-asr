from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "annotation"))

from build_human_audit_response_closeout_checklist import build_closeout  # noqa: E402


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
    assert "response_not_complete" in payload["blocker_keys"]
    assert "incomplete_response" in payload["blocker_keys"]
    status_by_step = {row["step_id"]: row["status"] for row in rows}
    assert status_by_step["6"] == "blocked_until_response_complete"
    serialized = json.dumps({"payload": payload, "rows": rows}, ensure_ascii=False)
    assert "PRIVATE_" not in serialized
    assert "reference_text" not in serialized
    assert "hypothesis_text" not in serialized


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
    assert status_by_step["6"] == "ready"


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

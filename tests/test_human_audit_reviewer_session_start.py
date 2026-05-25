from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "annotation"))
sys.path.insert(0, str(REPO_ROOT / "tests"))

from start_human_audit_review_session import start_session  # noqa: E402
from test_human_audit_reviewer_preflight import write_current_handoff  # noqa: E402


def test_session_start_refreshes_all_reviewer_gates_without_private_content(
    tmp_path: Path,
) -> None:
    run_dir, paths = write_current_handoff(tmp_path)

    payload = start_session(
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

    assert payload["ok"] is True
    assert payload["status"] == "reviewer_session_started"
    assert payload["current_gate"]["rubric_status"] == "rubric_ready"
    assert payload["current_gate"]["checklist_status"] == "reviewer_action_ready"
    assert payload["current_gate"]["pending_rows_in_batch"] == 2
    assert payload["current_gate"]["pending_model_assessments_in_batch"] == 6
    assert payload["current_gate"]["latest_apply_status"] == "response_pending"
    assert "--row-number 1" in payload["commands"]["timing_start_write"]
    assert "--row-number 1" in payload["commands"]["timing_finish_write"]
    assert sorted(payload["commands"]["timing_start_write_by_row"]) == ["1", "2"]
    assert "--row-number 2" in payload["commands"]["timing_finish_write_by_row"]["2"]
    assert (run_dir / "human_audit_reviewer_session_start_summary.json").exists()
    assert (run_dir / "human_audit_reviewer_session_start_log.tsv").exists()
    assert (run_dir / "human_audit_reviewer_handoff_summary.json").exists()
    assert (run_dir / "human_audit_reviewer_preflight_summary.json").exists()
    assert (run_dir / "human_audit_reviewer_rubric_summary.json").exists()
    assert (run_dir / "human_audit_reviewer_action_checklist_summary.json").exists()
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "PRIVATE_" not in serialized
    assert "reference_text" not in serialized
    assert "hypothesis_text" not in serialized
    assert "reviewer_notes" not in serialized


def test_session_start_blocks_missing_local_review_artifact(tmp_path: Path) -> None:
    run_dir, paths = write_current_handoff(tmp_path)
    (tmp_path / "run" / "artifacts" / "review_responses" / "response.tsv").unlink()

    payload = start_session(
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

    assert payload["ok"] is False
    assert payload["status"] == "reviewer_session_blocked"
    assert payload["error_keys"] == ["preflight_not_ready", "checklist_not_ready"]
    assert "local_review_artifacts_missing" in payload["current_gate"]["blocker_keys"]
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "reference_text" not in serialized
    assert "hypothesis_text" not in serialized

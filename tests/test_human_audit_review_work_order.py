from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tests"))
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "annotation"))

from build_human_audit_review_work_order import (  # noqa: E402
    WORK_ORDER_TSV_NAME,
    build_work_order,
    write_tsv,
)
from test_human_audit_response_closeout import write_closeout_inputs  # noqa: E402


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_action_items(path: Path) -> None:
    fieldnames = [
        "action_id",
        "row_number",
        "action_scope",
        "model_assessment_slot",
        "field_name",
        "status",
        "reviewer_action",
        "timing_start_write_command",
        "timing_finish_write_command",
    ]
    rows = [
        {
            "action_id": "row-1:row_field:reviewer_risk_atoms",
            "row_number": "1",
            "action_scope": "row_field",
            "model_assessment_slot": "",
            "field_name": "reviewer_risk_atoms",
            "status": "pending",
            "reviewer_action": "fill row-level response field in local response TSV",
            "timing_start_write_command": "not_applicable",
            "timing_finish_write_command": "not_applicable",
        },
        {
            "action_id": "row-1:model_slot-1:model_reviewer_critical_atoms",
            "row_number": "1",
            "action_scope": "model_assessment_field",
            "model_assessment_slot": "1",
            "field_name": "model_reviewer_critical_atoms",
            "status": "pending",
            "reviewer_action": "fill field for the corresponding model row in local response TSV",
            "timing_start_write_command": "not_applicable",
            "timing_finish_write_command": "not_applicable",
        },
        {
            "action_id": "row-1:review_timing",
            "row_number": "1",
            "action_scope": "review_timing",
            "model_assessment_slot": "",
            "field_name": "review_timing",
            "status": "pending",
            "reviewer_action": "record review timing",
            "timing_start_write_command": "mark_human_audit_response_timing.py --row-number 1 --mark-start --write",
            "timing_finish_write_command": "mark_human_audit_response_timing.py --row-number 1 --mark-finish --write",
        },
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_review_work_order_builds_safe_row_and_packet_steps(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    paths = write_closeout_inputs(run_dir, response_complete=False)
    closeout_path = run_dir / "human_audit_response_closeout_summary.json"
    closeout = {
        "selection_stratum": "critical_or_high_risk_missed",
        "response_action_item_overview": {
            "total_action_items": 3,
            "row_field_action_items": 1,
            "model_field_action_items": 1,
            "timing_action_items": 1,
        },
    }
    write_json(closeout_path, closeout)
    action_items_path = run_dir / "human_audit_response_action_items.tsv"
    write_action_items(action_items_path)

    payload, rows = build_work_order(
        run_dir=run_dir,
        action_items_tsv=action_items_path,
        closeout_summary_path=closeout_path,
        handoff_summary_path=paths["handoff"],
        session_start_summary_path=paths["session_start"],
        audit_sheet=run_dir / "artifacts" / "human_risk_atom_audit_sheet.tsv",
        repo_root=tmp_path,
    )

    assert payload["ok"] is True
    assert payload["status"] == "review_work_order_ready"
    assert payload["review_work_order_overview"] == {
        "row_count": 1,
        "row_work_order_steps": 5,
        "packet_work_order_steps": 5,
        "total_work_order_steps": 10,
        "total_action_items": 3,
        "row_field_action_items": 1,
        "model_field_action_items": 1,
        "timing_action_items": 1,
    }
    by_step = {row["step_type"]: row for row in rows}
    assert by_step["mark_timing_start"]["status"] == "pending"
    assert by_step["open_local_row"]["status"] == "local_only_required"
    assert "--show-row" in by_step["open_local_row"]["command"]
    assert by_step["fill_row_fields"]["pending_action_items"] == 1
    assert by_step["fill_model_fields"]["pending_action_items"] == 1
    assert by_step["strict_dry_run"]["row_number"] == "packet"
    serialized = json.dumps({"payload": payload, "rows": rows}, ensure_ascii=False)
    assert "PRIVATE_" not in serialized
    assert "reference_text" not in serialized
    assert "hypothesis_text" not in serialized
    assert "audio_id" not in serialized


def test_write_review_work_order_tsv_has_stable_header(tmp_path: Path) -> None:
    output = tmp_path / WORK_ORDER_TSV_NAME
    rows = [
        {
            "work_order_id": "packet:06-strict-dry-run",
            "row_number": "packet",
            "step_order": "06",
            "step_type": "strict_dry_run",
            "status": "blocked_until_rows_complete",
            "pending_action_items": "all",
            "reviewer_instruction": "run strict dry-run",
            "command": "strict command",
            "completion_signal": "response_complete",
            "privacy_boundary": "aggregate-only",
        }
    ]
    write_tsv(output, rows)

    text = output.read_text(encoding="utf-8")
    assert text.splitlines()[0] == (
        "work_order_id\trow_number\tstep_order\tstep_type\tstatus\t"
        "pending_action_items\treviewer_instruction\tcommand\t"
        "completion_signal\tprivacy_boundary"
    )
    assert "packet:06-strict-dry-run\tpacket\t06\tstrict_dry_run" in text

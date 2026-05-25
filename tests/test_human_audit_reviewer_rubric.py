from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "annotation"))

from build_human_audit_reviewer_rubric import build_rubric  # noqa: E402
from prepare_human_audit_review_batch import assert_tracked_safe  # noqa: E402
from validate_human_risk_atom_audit import (  # noqa: E402
    VALID_ATOMS,
    VALID_CONFIDENCE,
    VALID_DECISION_CHANGE,
    VALID_LABELS,
    VALID_SAFE_ACTION,
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_rubric_matches_validator_constants_and_current_gate(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    write_json(
        run_dir / "human_audit_reviewer_action_checklist_summary.json",
        {
            "ok": True,
            "status": "reviewer_action_ready",
            "selection_stratum": "critical_or_high_risk_missed",
            "rows_in_batch": 6,
            "pending_rows_in_batch": 6,
            "model_assessments_in_batch": 18,
            "pending_model_assessments_in_batch": 18,
            "rows_missing_timing": 6,
            "latest_apply_status": "response_pending",
        },
    )

    payload, rows = build_rubric(
        run_dir=run_dir,
        action_checklist_summary=run_dir / "human_audit_reviewer_action_checklist_summary.json",
        repo_root=tmp_path,
    )
    by_category = {}
    for row in rows:
        by_category.setdefault(row["category"], set()).add(row["value"])

    assert payload["ok"] is True
    assert payload["status"] == "rubric_ready"
    assert payload["validator_constants_match"] is True
    assert payload["current_reviewer_action_gate"]["status"] == "reviewer_action_ready"
    assert payload["current_reviewer_action_gate"]["pending_rows_in_batch"] == 6
    assert by_category["row_risk_label"] == VALID_LABELS
    assert by_category["decision_change"] == VALID_DECISION_CHANGE
    assert by_category["safe_action"] == VALID_SAFE_ACTION
    assert by_category["confidence"] == VALID_CONFIDENCE
    assert by_category["risk_atom"] == VALID_ATOMS
    assert_tracked_safe(payload)
    assert_tracked_safe(rows)


def test_rubric_handles_missing_action_gate_without_private_leak(tmp_path: Path) -> None:
    payload, rows = build_rubric(
        run_dir=tmp_path / "run",
        action_checklist_summary=tmp_path / "run" / "missing.json",
        repo_root=tmp_path,
    )

    assert payload["ok"] is True
    assert payload["current_reviewer_action_gate"]["available"] is False
    assert payload["current_reviewer_action_gate"]["status"] == "missing"
    serialized = json.dumps({"payload": payload, "rows": rows}, ensure_ascii=False)
    assert "reference_text" not in serialized
    assert "hypothesis_text" not in serialized
    assert "reviewer_model_assessments_json" not in serialized
    assert "reviewer_notes" not in serialized


def test_rubric_safe_value_contract_contains_expected_roles(tmp_path: Path) -> None:
    payload, rows = build_rubric(
        run_dir=tmp_path / "run",
        action_checklist_summary=tmp_path / "run" / "missing.json",
        repo_root=tmp_path,
    )

    roles = {row["paper_evidence_role"] for row in rows}
    assert "row-level human risk target" in roles
    assert "decision-stability target" in roles
    assert "recovery-policy target" in roles
    assert payload["required_review_surface"]["row_level_required_decision_fields"] == 8
    assert payload["required_review_surface"]["model_level_required_decision_fields"] == 4
    assert payload["required_review_surface"]["required_timing_fields"] == 3

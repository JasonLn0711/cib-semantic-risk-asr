from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "annotation"))

from build_human_audit_reviewer_handoff import (  # noqa: E402
    check_existing_handoff,
    build_handoff,
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_handoff_inputs(run_dir: Path) -> dict[str, Path]:
    batch_summary = run_dir / "human_audit_next_review_batch_summary.json"
    batch_status = run_dir / "human_audit_current_review_batch_status_summary.json"
    template_summary = run_dir / "human_audit_batch_response_template_summary.json"
    apply_summary = run_dir / "human_audit_batch_response_apply_summary.json"
    apply_log_summary = run_dir / "human_audit_batch_response_apply_log_summary.json"
    write_json(
        batch_summary,
        {
            "selection_stratum": "critical_or_high_risk_missed",
            "row_numbers": [1, 2],
            "rows_in_batch": 2,
            "local_packet_path": "run/artifacts/review_batches/local.md",
        },
    )
    write_json(
        batch_status,
        {
            "ok": True,
            "status": "batch_pending",
            "batch_ready_for_refresh": False,
            "reviewed_rows_in_batch": 0,
            "pending_rows_in_batch": 2,
            "model_assessments_in_batch": 6,
            "reviewed_model_assessments_in_batch": 0,
            "pending_model_assessments_in_batch": 6,
        },
    )
    write_json(
        template_summary,
        {
            "ok": True,
            "response_rows": 6,
            "template_column_count": 19,
            "local_response_template_path": "run/artifacts/review_responses/response.tsv",
        },
    )
    write_json(
        apply_summary,
        {
            "ok": False,
            "status": "response_pending",
            "error_counts": {"incomplete_response": 1},
            "review_timing": {"rows_with_timing": 0, "rows_missing_timing": 2},
        },
    )
    write_json(
        apply_log_summary,
        {
            "ok": True,
            "status": "apply_log_valid",
            "apply_log_entries": 1,
            "status_counts": {"response_pending": 1},
            "error_key_counts": {"incomplete_response": 1},
            "latest": {
                "recorded_at": "2026-05-25T22:22:30+08:00",
                "ok": "False",
                "status": "response_pending",
                "mode": "dry_run",
                "require_complete": "True",
                "error_keys": "incomplete_response",
                "rows_with_timing": 0,
                "rows_missing_timing": 2,
            },
        },
    )
    return {
        "batch_summary": batch_summary,
        "batch_status": batch_status,
        "template_summary": template_summary,
        "apply_summary": apply_summary,
        "apply_log_summary": apply_log_summary,
    }


def test_handoff_collects_current_reviewer_gate_without_private_content(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    paths = write_handoff_inputs(run_dir)
    payload = build_handoff(
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
    assert payload["status"] == "reviewer_input_pending"
    assert payload["current_packet"]["row_numbers"] == [1, 2]
    assert payload["freshness_status"] == "fresh"
    assert payload["source_digests"]["batch_summary"]["status"] == "present"
    assert payload["source_digests"]["batch_summary"]["sha256"]
    assert payload["current_response"]["template_column_count"] == 19
    assert payload["current_gate"]["latest_apply_status"] == "response_pending"
    assert payload["current_gate"]["latest_error_keys"] == "incomplete_response"
    assert payload["apply_log"]["entries"] == 1
    assert "--require-complete" in payload["commands"]["strict_dry_run"]
    assert "--require-timing" in payload["commands"]["strict_dry_run"]
    assert "--require-timing" in payload["commands"]["write_refresh_prepare_next"]
    assert "--write" in payload["commands"]["write_refresh_prepare_next"]
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "PRIVATE_" not in serialized
    assert "reference_text" not in serialized
    assert "hypothesis_text" not in serialized


def test_handoff_records_source_digests_and_checks_freshness(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    paths = write_handoff_inputs(run_dir)
    handoff_path = run_dir / "human_audit_reviewer_handoff_summary.json"
    payload = build_handoff(
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
    write_json(handoff_path, payload)

    fresh = check_existing_handoff(
        handoff_summary_path=handoff_path,
        batch_summary_path=paths["batch_summary"],
        batch_status_path=paths["batch_status"],
        template_summary_path=paths["template_summary"],
        apply_summary_path=paths["apply_summary"],
        apply_log_summary_path=paths["apply_log_summary"],
        repo_root=tmp_path,
    )

    assert fresh["ok"] is True
    assert fresh["status"] == "handoff_fresh"
    assert fresh["stale_sources"] == []
    assert fresh["missing_sources"] == []

    write_json(
        paths["batch_status"],
        {
            "ok": True,
            "status": "batch_pending",
            "batch_ready_for_refresh": False,
            "reviewed_rows_in_batch": 1,
            "pending_rows_in_batch": 1,
            "model_assessments_in_batch": 6,
            "reviewed_model_assessments_in_batch": 3,
            "pending_model_assessments_in_batch": 3,
        },
    )
    stale = check_existing_handoff(
        handoff_summary_path=handoff_path,
        batch_summary_path=paths["batch_summary"],
        batch_status_path=paths["batch_status"],
        template_summary_path=paths["template_summary"],
        apply_summary_path=paths["apply_summary"],
        apply_log_summary_path=paths["apply_log_summary"],
        repo_root=tmp_path,
    )

    assert stale["ok"] is False
    assert stale["status"] == "handoff_stale"
    assert stale["stale_sources"] == ["batch_status"]
    serialized = json.dumps(stale, ensure_ascii=False)
    assert "PRIVATE_" not in serialized
    assert "reference_text" not in serialized
    assert "hypothesis_text" not in serialized


def test_handoff_reports_missing_inputs(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    payload = build_handoff(
        run_dir=run_dir,
        audit_sheet=run_dir / "artifacts" / "audit.tsv",
        batch_summary_path=run_dir / "missing_batch.json",
        batch_status_path=run_dir / "missing_status.json",
        template_summary_path=run_dir / "missing_template.json",
        apply_summary_path=run_dir / "missing_apply.json",
        apply_log_summary_path=run_dir / "missing_log_summary.json",
        readiness_output_dir=tmp_path / "readiness",
        expected_rows=30,
        repo_root=tmp_path,
    )

    assert payload["ok"] is False
    assert payload["status"] == "reviewer_handoff_missing_inputs"
    assert sorted(payload["missing_inputs"]) == [
        "apply_log_summary",
        "apply_summary",
        "batch_status",
        "batch_summary",
        "template_summary",
    ]

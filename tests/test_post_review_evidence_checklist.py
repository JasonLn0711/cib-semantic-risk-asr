from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "annotation"))

from build_post_review_evidence_checklist import build_post_review_checklist  # noqa: E402


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_inputs(tmp_path: Path, *, ready: bool, human_recovery: bool = False) -> dict[str, Path]:
    run_dir = tmp_path / "run"
    readiness_dir = tmp_path / "readiness"
    closeout = run_dir / "human_audit_response_closeout_summary.json"
    refresh = run_dir / "human_audit_refresh_summary.json"
    predictor = run_dir / "human_audit_predictor_summary.json"
    readiness = readiness_dir / "evidence_chain_readiness_summary.json"
    publishable = readiness_dir / "publishable_evidence_completion_summary.json"
    consequence = readiness_dir / "consequence_evidence_matrix_summary.json"
    recovery = tmp_path / "recovery" / "summary.json"
    human_recovery_summary = tmp_path / "human_recovery" / "summary.json"
    write_json(
        closeout,
        {
            "ok": ready,
            "status": "response_complete_ready_to_write" if ready else "response_closeout_blocked",
            "pending_rows_in_response": 0 if ready else 2,
            "pending_model_assessments_in_response": 0 if ready else 6,
            "require_timing": True,
            "review_timing": {
                "rows_with_timing": 1 if ready else 0,
                "rows_missing_timing": 0 if ready else 1,
            },
        },
    )
    write_json(
        refresh,
        {
            "ok": True,
            "status": "review_complete" if ready else "review_pending",
            "pending_rows": 0 if ready else 30,
            "pending_model_assessments": 0 if ready else 90,
        },
    )
    write_json(
        predictor,
        {
            "ok": True,
            "status": "review_complete" if ready else "review_pending",
            "pending_model_assessments": 0 if ready else 90,
        },
    )
    write_json(readiness, {"ok": True, "paper_ready": ready})
    write_json(publishable, {"ok": True, "publishable_ready": ready})
    write_json(
        consequence,
        {
            "ok": True,
            "paper_claims_ready": ready,
            "status_counts": {"completed": 7} if ready else {"review_pending": 2},
        },
    )
    write_json(
        recovery,
        {
            "ok": True,
            "evidence_mode": "proxy",
            "policies": {
                "no_recovery": {},
                "confidence_only_trigger": {},
                "sres_triggered_recovery": {},
                "ceis_triggered_conservative_action": {},
                "ceis_ensemble_arbitration": {},
            },
        },
    )
    if human_recovery:
        write_json(
            human_recovery_summary,
            {
                "ok": True,
                "status": "human_reviewed_complete",
                "evidence_mode": "human_reviewed",
                "human_reviewed": True,
                "review_status": "human_reviewed_complete",
                "policies": {
                    "no_recovery": {},
                    "confidence_only_trigger": {},
                    "sres_triggered_recovery": {},
                    "ceis_triggered_conservative_action": {},
                    "ceis_ensemble_arbitration": {},
                },
            },
        )
    return {
        "run_dir": run_dir,
        "readiness_dir": readiness_dir,
        "closeout": closeout,
        "refresh": refresh,
        "predictor": predictor,
        "readiness": readiness,
        "publishable": publishable,
        "consequence": consequence,
        "recovery": recovery,
        "human_recovery": human_recovery_summary,
    }


def test_post_review_checklist_blocks_until_closeout_and_refresh_complete(tmp_path: Path) -> None:
    paths = write_inputs(tmp_path, ready=False)

    payload, rows = build_post_review_checklist(
        run_dir=paths["run_dir"],
        readiness_dir=paths["readiness_dir"],
        closeout_summary_path=paths["closeout"],
        refresh_summary_path=paths["refresh"],
        predictor_summary_path=paths["predictor"],
        readiness_summary_path=paths["readiness"],
        publishable_summary_path=paths["publishable"],
        consequence_summary_path=paths["consequence"],
        recovery_summary_path=paths["recovery"],
        human_recovery_summary_path=paths["human_recovery"],
        repo_root=tmp_path,
    )

    assert payload["ok"] is False
    assert payload["status"] == "post_review_evidence_blocked"
    assert "response_closeout_not_ready" in payload["blocker_keys"]
    assert "human_refresh_not_complete" in payload["blocker_keys"]
    assert "recovery_proxy_only" in payload["blocker_keys"]
    assert payload["closeout_require_timing"] is True
    assert payload["closeout_review_timing"]["rows_missing_timing"] == 1
    status_by_step = {row["step_id"]: row["status"] for row in rows}
    assert status_by_step["1"] == "blocked"
    assert status_by_step["7"] == "proxy_only"
    step_1 = next(row for row in rows if row["step_id"] == "1")
    assert "rows_missing_timing=1" in step_1["evidence"]
    assert "--require-timing" in step_1["next_action"]
    serialized = json.dumps({"payload": payload, "rows": rows}, ensure_ascii=False)
    assert "PRIVATE_" not in serialized
    assert "reference_text" not in serialized
    assert "hypothesis_text" not in serialized


def test_post_review_checklist_marks_all_gates_ready(tmp_path: Path) -> None:
    paths = write_inputs(tmp_path, ready=True, human_recovery=True)

    payload, rows = build_post_review_checklist(
        run_dir=paths["run_dir"],
        readiness_dir=paths["readiness_dir"],
        closeout_summary_path=paths["closeout"],
        refresh_summary_path=paths["refresh"],
        predictor_summary_path=paths["predictor"],
        readiness_summary_path=paths["readiness"],
        publishable_summary_path=paths["publishable"],
        consequence_summary_path=paths["consequence"],
        recovery_summary_path=paths["recovery"],
        human_recovery_summary_path=paths["human_recovery"],
        repo_root=tmp_path,
    )

    assert payload["ok"] is True
    assert payload["status"] == "post_review_evidence_ready"
    assert payload["blocker_keys"] == []
    assert payload["closeout_review_timing"]["rows_missing_timing"] == 0
    status_by_step = {row["step_id"]: row["status"] for row in rows}
    assert status_by_step["1"] == "ready"
    assert status_by_step["6"] == "ready"
    assert status_by_step["7"] == "human_reviewed_ready"


def test_post_review_checklist_blocks_proxy_recovery_even_when_other_gates_ready(
    tmp_path: Path,
) -> None:
    paths = write_inputs(tmp_path, ready=True, human_recovery=False)

    payload, rows = build_post_review_checklist(
        run_dir=paths["run_dir"],
        readiness_dir=paths["readiness_dir"],
        closeout_summary_path=paths["closeout"],
        refresh_summary_path=paths["refresh"],
        predictor_summary_path=paths["predictor"],
        readiness_summary_path=paths["readiness"],
        publishable_summary_path=paths["publishable"],
        consequence_summary_path=paths["consequence"],
        recovery_summary_path=paths["recovery"],
        human_recovery_summary_path=paths["human_recovery"],
        repo_root=tmp_path,
    )

    assert payload["ok"] is False
    assert payload["status"] == "post_review_evidence_blocked"
    assert payload["recovery_proxy_available"] is True
    assert payload["recovery_human_ready"] is False
    assert payload["blocker_keys"] == ["recovery_proxy_only"]
    status_by_step = {row["step_id"]: row["status"] for row in rows}
    assert status_by_step["7"] == "proxy_only"

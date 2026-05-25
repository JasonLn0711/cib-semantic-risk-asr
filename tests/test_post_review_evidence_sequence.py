from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "annotation"))

from run_post_review_evidence_sequence import (  # noqa: E402
    SEQUENCE_TSV_FIELDS,
    build_sequence,
    write_tsv,
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_inputs(tmp_path: Path, *, closeout_ready: bool, all_ready: bool = False) -> dict[str, Path]:
    run_dir = tmp_path / "run"
    readiness_dir = tmp_path / "readiness"
    human_recovery_dir = tmp_path / "human_recovery"
    closeout = run_dir / "human_audit_response_closeout_summary.json"
    refresh = run_dir / "human_audit_refresh_summary.json"
    human_recovery = human_recovery_dir / "summary.json"
    post_review = run_dir / "human_audit_post_review_evidence_summary.json"
    objective = readiness_dir / "postdoc_objective_requirements_summary.json"
    write_json(
        closeout,
        {
            "ok": closeout_ready,
            "status": "response_complete_ready_to_write" if closeout_ready else "response_closeout_blocked",
            "checklist": [
                {
                    "step_id": "2",
                    "next_action": "apply_human_audit_batch_response.py --require-complete --require-timing",
                },
                {
                    "step_id": "7",
                    "next_action": "apply_human_audit_batch_response.py --write --refresh-after-write --require-complete --require-timing",
                },
            ],
        },
    )
    write_json(
        refresh,
        {
            "ok": all_ready,
            "status": "review_complete" if all_ready else "review_pending",
            "pending_rows": 0 if all_ready else 30,
            "pending_model_assessments": 0 if all_ready else 90,
        },
    )
    write_json(
        human_recovery,
        {
            "ok": all_ready,
            "status": "human_reviewed_complete" if all_ready else "review_pending",
            "evidence_mode": "human_reviewed" if all_ready else "human_reviewed_pending",
            "policies": {
                "no_recovery": {},
                "confidence_only_trigger": {},
                "sres_triggered_recovery": {},
                "ceis_triggered_conservative_action": {},
                "ceis_ensemble_arbitration": {},
            }
            if all_ready
            else {},
        },
    )
    write_json(
        post_review,
        {
            "ok": all_ready,
            "status": "post_review_evidence_ready" if all_ready else "post_review_evidence_blocked",
        },
    )
    write_json(
        objective,
        {"ok": all_ready, "objective_requirements_ready": all_ready},
    )
    return {
        "run_dir": run_dir,
        "readiness_dir": readiness_dir,
        "human_recovery_dir": human_recovery_dir,
        "closeout": closeout,
        "refresh": refresh,
        "human_recovery": human_recovery,
        "post_review": post_review,
        "objective": objective,
    }


def build_from_paths(paths: dict[str, Path], *, execute: bool = False) -> tuple[dict, list[dict]]:
    return build_sequence(
        run_dir=paths["run_dir"],
        readiness_dir=paths["readiness_dir"],
        human_recovery_dir=paths["human_recovery_dir"],
        closeout_summary_path=paths["closeout"],
        refresh_summary_path=paths["refresh"],
        human_recovery_summary_path=paths["human_recovery"],
        post_review_summary_path=paths["post_review"],
        objective_summary_path=paths["objective"],
        repo_root=paths["run_dir"].parents[0],
        execute=execute,
    )


def test_post_review_sequence_blocks_before_closeout(tmp_path: Path) -> None:
    paths = write_inputs(tmp_path, closeout_ready=False)

    payload, rows = build_from_paths(paths)

    assert payload["ok"] is False
    assert payload["status"] == "post_review_sequence_blocked"
    assert payload["executed_step_count"] == 0
    assert payload["blocker_keys"][0] == "strict_dry_run"
    assert [row["step_type"] for row in rows] == [
        "strict_dry_run",
        "response_closeout",
        "write_refresh_prepare_next",
        "human_audit_refresh",
        "strict_human_reviewed_recovery",
        "post_review_checklist",
        "objective_requirements_audit",
    ]
    serialized = json.dumps({"payload": payload, "rows": rows}, ensure_ascii=False)
    assert "PRIVATE_" not in serialized
    assert "reference_text" not in serialized
    assert "hypothesis_text" not in serialized
    assert "stop before any blocked" in payload["execute_safety_policy"]


def test_post_review_sequence_execute_stops_before_blocked_closeout(
    tmp_path: Path,
) -> None:
    paths = write_inputs(tmp_path, closeout_ready=False)

    payload, rows = build_from_paths(paths, execute=True)

    assert payload["ok"] is False
    assert payload["mode"] == "execute"
    assert payload["status"] == "post_review_sequence_blocked"
    assert payload["executed_step_count"] == 0
    assert payload["stopped_step"] == "strict_dry_run"
    assert rows[0]["status"] == "blocked_until_response_fields_complete"
    assert all("exit_code" not in row for row in rows)


def test_post_review_sequence_reports_ready_to_execute_after_closeout(tmp_path: Path) -> None:
    paths = write_inputs(tmp_path, closeout_ready=True, all_ready=False)

    payload, rows = build_from_paths(paths)

    assert payload["ok"] is False
    assert payload["status"] == "post_review_sequence_ready_to_execute"
    assert rows[0]["status"] == "ready"
    assert rows[4]["status"] == "blocked_until_review_complete"


def test_post_review_sequence_marks_complete_when_all_gates_ready(tmp_path: Path) -> None:
    paths = write_inputs(tmp_path, closeout_ready=True, all_ready=True)

    payload, rows = build_from_paths(paths)

    assert payload["ok"] is True
    assert payload["status"] == "post_review_sequence_complete"
    assert payload["blocker_keys"] == []
    assert all(row["status"] == "ready" for row in rows)


def test_post_review_sequence_tsv_header_is_stable(tmp_path: Path) -> None:
    output = tmp_path / "sequence.tsv"
    write_tsv(
        output,
        [
            {
                "step_order": 1,
                "step_type": "strict_dry_run",
                "status": "blocked_until_response_fields_complete",
                "command": "apply_human_audit_batch_response.py",
                "success_condition": "response_complete",
                "observed_status": "response_pending",
                "exit_code": "",
                "next_action": "fill fields",
                "privacy_boundary": "aggregate-only",
            }
        ],
        SEQUENCE_TSV_FIELDS,
    )

    assert output.read_text(encoding="utf-8").splitlines()[0] == "\t".join(SEQUENCE_TSV_FIELDS)

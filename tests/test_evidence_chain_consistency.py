from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "scoring"))

from audit_evidence_chain_consistency import (  # noqa: E402
    RESPONSE_GAP_TSV_RELATIVE,
    SUMMARY_SPECS,
    assert_aggregate_safe,
    build_consistency_audit,
)


TRANSCRIPT_POLICY = (
    "Reference transcripts are already human-reviewed ground truth for WER/CER "
    "scoring; this packet does not ask for duplicate transcript review."
)
REVIEW_SCOPE = (
    "The packet asks reviewers to complete risk atoms, decision-change labels, "
    "expected safe action, confidence, per-model assessment fields, and "
    "per-row review timing."
)
ROW_NUMBERS = [1, 2, 3, 4, 5, 6]


def write_summary(root: Path, name: str, payload: dict) -> None:
    path = root / SUMMARY_SPECS[name]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def write_gap_tsv_fixture(root: Path, row_numbers: list[int] = ROW_NUMBERS) -> None:
    path = root / RESPONSE_GAP_TSV_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    header = [
        "row_number",
        "has_gap",
        "row_response_complete",
        "row_fields_missing_count",
        "missing_row_fields",
        "model_assessments_expected_count",
        "model_assessments_complete_count",
        "model_assessments_missing_count",
        "model_fields_missing_count",
        "missing_model_fields",
        "review_timing_complete",
        "review_timing_missing",
        "timing_start_write_command",
        "timing_finish_write_command",
    ]
    lines = ["\t".join(header)]
    commands = timing_commands(row_numbers)
    for row_number in row_numbers:
        lines.append(
            "\t".join(
                [
                    str(row_number),
                    "true",
                    "false",
                    "8",
                    "reviewer_risk_atoms",
                    "3",
                    "0",
                    "3",
                    "12",
                    "model_reviewer_critical_atoms",
                    "false",
                    "true",
                    commands["timing_start_write_by_row"][str(row_number)],
                    commands["timing_finish_write_by_row"][str(row_number)],
                ]
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def base_summary(**extra: object) -> dict:
    payload = {
        "ok": True,
        "reference_transcript_policy": TRANSCRIPT_POLICY,
        "remaining_review_scope": REVIEW_SCOPE,
    }
    payload.update(extra)
    return payload


def timing_commands(row_numbers: list[int] = ROW_NUMBERS) -> dict:
    start_by_row = {
        str(row_number): (
            "mark_human_audit_response_timing.py --row-number "
            f"{row_number} --mark-start --write"
        )
        for row_number in row_numbers
    }
    finish_by_row = {
        str(row_number): (
            "mark_human_audit_response_timing.py --row-number "
            f"{row_number} --mark-finish --write"
        )
        for row_number in row_numbers
    }
    return {
        "timing_start_write": start_by_row[str(row_numbers[0])],
        "timing_finish_write": finish_by_row[str(row_numbers[0])],
        "timing_start_write_by_row": start_by_row,
        "timing_finish_write_by_row": finish_by_row,
    }


def write_consistent_fixture(root: Path) -> None:
    write_summary(
        root,
        "readiness",
        base_summary(
            paper_ready=False,
            next_decision="Complete per-row timing and run --require-timing.",
            reviewer_action_gate={
                "status": "reviewer_action_ready",
                "rows_in_batch": 6,
                "pending_rows_in_batch": 6,
                "model_assessments_in_batch": 18,
                "pending_model_assessments_in_batch": 18,
                "rows_missing_timing": 6,
            },
        ),
    )
    write_summary(
        root,
        "publishable",
        base_summary(
            publishable_ready=False,
            blocking_or_proxy_items=[{"objective_id": "5"}],
            next_decision="Complete timing, then run --require-timing.",
        ),
    )
    write_summary(
        root,
        "consequence",
        base_summary(
            paper_claims_ready=False,
            blocking_or_proxy_items=[{"consequence_id": "C5"}],
            next_decision="Complete risk/decision/model/timing review, then run --require-complete --require-timing.",
        ),
    )
    write_summary(
        root,
        "roadmap",
        base_summary(
            paper_ready=False,
            publishable_ready=False,
            roadmap_complete=False,
            next_decision="Close row/model/timing gate with --require-timing.",
        ),
    )
    write_summary(
        root,
        "refresh",
        base_summary(
            status="review_pending",
            publishable_ready=False,
            next_action="Complete per-row timing with --require-timing.",
        ),
    )
    write_summary(
        root,
        "post_review",
        base_summary(
            ok=False,
            status="post_review_evidence_blocked",
            paper_ready=False,
            publishable_ready=False,
            post_review_command_plan={
                "current_first_action": "complete_response_closeout",
                "closeout_commands": {
                    "strict_dry_run": (
                        "apply_human_audit_batch_response.py --require-complete "
                        "--require-timing --require-session-start-gate"
                    ),
                    "write_refresh_prepare_next": (
                        "apply_human_audit_batch_response.py --write "
                        "--refresh-after-write --prepare-next-after-write "
                        "--require-complete --require-timing "
                        "--require-session-start-gate"
                    ),
                },
                "post_write_order": [
                    {
                        "gate": "human_audit_refresh",
                        "command": "refresh_human_audit_evidence.py",
                    },
                    {
                        "gate": "strict_human_reviewed_recovery",
                        "command": "evaluate_human_reviewed_recovery_policies.py",
                    },
                    {
                        "gate": "post_review_checklist",
                        "command": "build_post_review_evidence_checklist.py",
                    },
                    {
                        "gate": "objective_requirements_audit",
                        "command": "audit_postdoc_objective_requirements.py",
                    },
                ],
            },
        ),
    )
    write_summary(
        root,
        "closeout",
        base_summary(
            ok=False,
            status="response_closeout_blocked",
            require_timing=True,
            review_timing={"rows_missing_timing": 6},
            response_gap_summary_by_row=[
                {"row_number": row_number}
                for row_number in ROW_NUMBERS
            ],
            checklist=[
                {
                    "step_id": "2",
                    "next_action": (
                        "apply_human_audit_batch_response.py --require-complete "
                        "--require-timing --require-session-start-gate"
                    ),
                },
                {
                    "step_id": "7",
                    "next_action": (
                        "apply_human_audit_batch_response.py --write "
                        "--refresh-after-write --prepare-next-after-write "
                        "--require-complete --require-timing "
                        "--require-session-start-gate"
                    ),
                },
            ],
        ),
    )
    write_summary(
        root,
        "apply",
        base_summary(
            ok=False,
            status="response_pending",
            require_timing=True,
            review_timing={"rows_missing_timing": 6},
            next_action="Rerun dry-run with --require-timing.",
        ),
    )
    write_summary(
        root,
        "handoff",
        base_summary(
            status="reviewer_input_pending",
            freshness_status="fresh",
            current_packet={"row_numbers": ROW_NUMBERS},
            current_gate={
                "latest_apply_status": "response_pending",
                "pending_rows_in_batch": 6,
                "pending_model_assessments_in_batch": 18,
                "rows_missing_timing": 6,
            },
            commands=timing_commands(),
        ),
    )
    write_summary(
        root,
        "action_checklist",
        base_summary(
            status="reviewer_action_ready",
            rows_in_batch=6,
            pending_rows_in_batch=6,
            model_assessments_in_batch=18,
            pending_model_assessments_in_batch=18,
            rows_missing_timing=6,
            timing_helper_commands=timing_commands(),
        ),
    )
    write_summary(
        root,
        "session_start",
        base_summary(
            status="reviewer_session_started",
            current_packet={"row_numbers": ROW_NUMBERS},
            commands=timing_commands(),
        ),
    )
    write_summary(
        root,
        "candidate_recheck",
        {
            "ok": True,
            "promotion_decision": "No requested ASR/Gemma candidate should be promoted.",
            "bounded_probes": [
                {"status": "timeout_before_inference"},
                {"status": "blocked_local_transformers_multimodal_class_missing"},
            ],
        },
    )
    write_gap_tsv_fixture(root)


def test_consistency_audit_passes_current_blocked_but_aligned_state(tmp_path: Path) -> None:
    write_consistent_fixture(tmp_path)
    payload = build_consistency_audit(tmp_path)

    assert payload["ok"] is True
    assert payload["status_counts"] == {"pass": 15}
    assert not payload["failed_checks"]
    assert_aggregate_safe(payload)


def test_consistency_audit_fails_stale_remaining_scope(tmp_path: Path) -> None:
    write_consistent_fixture(tmp_path)
    stale = base_summary(
        ok=False,
        status="response_pending",
        require_timing=True,
        review_timing={"rows_missing_timing": 6},
        next_action="Rerun dry-run with --require-timing.",
        remaining_review_scope=(
            "The packet asks reviewers to complete risk atoms, decision-change "
            "labels, expected safe action, confidence, and per-model assessment fields."
        ),
    )
    write_summary(tmp_path, "apply", stale)

    payload = build_consistency_audit(tmp_path)

    assert payload["ok"] is False
    assert any(item["check_id"] == "C020" for item in payload["failed_checks"])


def test_consistency_audit_rejects_paper_ready_while_review_pending(tmp_path: Path) -> None:
    write_consistent_fixture(tmp_path)
    write_summary(
        tmp_path,
        "publishable",
        base_summary(
            publishable_ready=True,
            blocking_or_proxy_items=[],
            next_decision="Complete timing, then run --require-timing.",
        ),
    )

    payload = build_consistency_audit(tmp_path)

    assert payload["ok"] is False
    failed_ids = {item["check_id"] for item in payload["failed_checks"]}
    assert "C040" in failed_ids
    assert "C050" in failed_ids


def test_consistency_audit_fails_stale_reviewer_handoff(tmp_path: Path) -> None:
    write_consistent_fixture(tmp_path)
    write_summary(
        tmp_path,
        "handoff",
        base_summary(
            status="reviewer_input_pending",
            freshness_status="stale",
            current_gate={
                "latest_apply_status": "response_pending",
                "pending_rows_in_batch": 6,
                "pending_model_assessments_in_batch": 18,
                "rows_missing_timing": 6,
            },
        ),
    )

    payload = build_consistency_audit(tmp_path)

    assert payload["ok"] is False
    assert any(item["check_id"] == "C065" for item in payload["failed_checks"])


def test_consistency_audit_rejects_pending_recovery_command_plan(tmp_path: Path) -> None:
    write_consistent_fixture(tmp_path)
    post_review_path = tmp_path / SUMMARY_SPECS["post_review"]
    post_review = json.loads(post_review_path.read_text(encoding="utf-8"))
    post_review["post_review_command_plan"]["post_write_order"][1]["command"] = (
        "evaluate_human_reviewed_recovery_policies.py --allow-pending-summary"
    )
    post_review_path.write_text(json.dumps(post_review, ensure_ascii=False), encoding="utf-8")

    payload = build_consistency_audit(tmp_path)

    assert payload["ok"] is False
    assert any(item["check_id"] == "C066" for item in payload["failed_checks"])


def test_consistency_audit_fails_incomplete_per_row_timing_commands(tmp_path: Path) -> None:
    write_consistent_fixture(tmp_path)
    action_path = tmp_path / SUMMARY_SPECS["action_checklist"]
    action = json.loads(action_path.read_text(encoding="utf-8"))
    del action["timing_helper_commands"]["timing_start_write_by_row"]["6"]
    action_path.write_text(json.dumps(action, ensure_ascii=False), encoding="utf-8")

    payload = build_consistency_audit(tmp_path)

    assert payload["ok"] is False
    assert any(item["check_id"] == "C067" for item in payload["failed_checks"])


def test_consistency_audit_fails_gap_tsv_timing_command_drift(tmp_path: Path) -> None:
    write_consistent_fixture(tmp_path)
    gap_path = tmp_path / RESPONSE_GAP_TSV_RELATIVE
    text = gap_path.read_text(encoding="utf-8")
    gap_path.write_text(
        text.replace("--row-number 6 --mark-finish", "--row-number 999 --mark-finish"),
        encoding="utf-8",
    )

    payload = build_consistency_audit(tmp_path)

    assert payload["ok"] is False
    assert any(item["check_id"] == "C068" for item in payload["failed_checks"])


def test_consistency_safety_rejects_raw_field_tokens() -> None:
    try:
        assert_aggregate_safe({"bad": "hypothesis_text"})
    except ValueError as exc:
        assert "sensitive field token" in str(exc)
    else:
        raise AssertionError("sensitive field token did not fail")

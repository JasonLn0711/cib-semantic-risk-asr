from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "scoring"))

from audit_evidence_chain_consistency import (  # noqa: E402
    POST_REVIEW_SEQUENCE_TSV_RELATIVE,
    RESPONSE_ACTION_ITEMS_TSV_RELATIVE,
    RESPONSE_GAP_TSV_RELATIVE,
    REVIEW_WORK_ORDER_TSV_RELATIVE,
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


def write_action_items_tsv_fixture(root: Path, row_numbers: list[int] = ROW_NUMBERS) -> None:
    path = root / RESPONSE_ACTION_ITEMS_TSV_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    header = [
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
    row_fields = [
        "reviewer_semantic_risk_label",
        "reviewer_risk_atoms",
        "reviewer_critical_atoms",
        "reviewer_asr_confusion_terms",
        "reviewer_would_asr_error_change_decision",
        "reviewer_decision_change_reason",
        "reviewer_expected_safe_action",
        "reviewer_annotation_confidence",
    ]
    model_fields = [
        "model_reviewer_annotation_confidence",
        "model_reviewer_critical_atoms",
        "model_reviewer_expected_safe_action",
        "model_reviewer_would_asr_error_change_decision",
    ]
    commands = timing_commands(row_numbers)
    lines = ["\t".join(header)]
    for row_number in row_numbers:
        for field_name in row_fields:
            lines.append(
                "\t".join(
                    [
                        f"row-{row_number}:row_field:{field_name}",
                        str(row_number),
                        "row_field",
                        "",
                        field_name,
                        "pending",
                        "fill row-level response field in local response TSV",
                        "",
                        "",
                    ]
                )
            )
        for slot in range(1, 4):
            for field_name in model_fields:
                lines.append(
                    "\t".join(
                        [
                            f"row-{row_number}:model_slot-{slot}:{field_name}",
                            str(row_number),
                            "model_assessment_field",
                            str(slot),
                            field_name,
                            "pending",
                            "fill field for the corresponding model row in local response TSV",
                            "",
                            "",
                        ]
                    )
                )
        lines.append(
            "\t".join(
                [
                    f"row-{row_number}:review_timing",
                    str(row_number),
                    "review_timing",
                    "",
                    "review_timing",
                    "pending",
                    "record review_started_at/review_finished_at or review_elapsed_seconds",
                    commands["timing_start_write_by_row"][str(row_number)],
                    commands["timing_finish_write_by_row"][str(row_number)],
                ]
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_work_order_tsv_fixture(root: Path, row_numbers: list[int] = ROW_NUMBERS) -> None:
    path = root / REVIEW_WORK_ORDER_TSV_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    header = [
        "work_order_id",
        "row_number",
        "step_order",
        "step_type",
        "status",
        "pending_action_items",
        "reviewer_instruction",
        "command",
        "completion_signal",
        "privacy_boundary",
    ]
    row_steps = [
        ("01", "mark_timing_start"),
        ("02", "open_local_row"),
        ("03", "fill_row_fields"),
        ("04", "fill_model_fields"),
        ("05", "mark_timing_finish"),
    ]
    packet_steps = [
        ("06", "strict_dry_run"),
        ("07", "response_closeout"),
        ("08", "post_review_sequence_execute"),
    ]
    lines = ["\t".join(header)]
    for row_number in row_numbers:
        for step_order, step_type in row_steps:
            lines.append(
                "\t".join(
                    [
                        f"row-{row_number}:{step_order}-{step_type}",
                        str(row_number),
                        step_order,
                        step_type,
                        "pending",
                        "1",
                        "review local response fields",
                        "local-only command",
                        "aggregate signal",
                        "aggregate-only",
                    ]
                )
            )
    for step_order, step_type in packet_steps:
        if step_type == "strict_dry_run":
            command = (
                "apply_human_audit_batch_response.py --require-complete "
                "--require-timing --require-session-start-gate"
            )
        elif step_type == "post_review_sequence_execute":
            command = "run_post_review_evidence_sequence.py --execute"
        else:
            command = "aggregate command"
        lines.append(
            "\t".join(
                [
                    f"packet:{step_order}-{step_type}",
                    "packet",
                    step_order,
                    step_type,
                    "blocked_until_rows_complete",
                    "all",
                    "run packet closeout step",
                    command,
                    "aggregate signal",
                    "aggregate-only",
                ]
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_post_review_sequence_tsv_fixture(root: Path) -> None:
    path = root / POST_REVIEW_SEQUENCE_TSV_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    header = [
        "step_order",
        "step_type",
        "status",
        "command",
        "success_condition",
        "observed_status",
        "exit_code",
        "next_action",
        "privacy_boundary",
    ]
    steps = [
        (
            "1",
            "strict_dry_run",
            "blocked_until_response_fields_complete",
            "apply_human_audit_batch_response.py --require-complete --require-timing --require-session-start-gate",
        ),
        ("2", "response_closeout", "blocked_until_strict_dry_run_complete", "build_human_audit_response_closeout_checklist.py"),
        ("3", "write_refresh_prepare_next", "blocked_until_response_closeout_ready", "apply_human_audit_batch_response.py --write --refresh-after-write --prepare-next-after-write --require-complete --require-timing"),
        ("4", "human_audit_refresh", "blocked_until_write_refresh_complete", "refresh_human_audit_evidence.py"),
        ("5", "strict_human_reviewed_recovery", "blocked_until_review_complete", "evaluate_human_reviewed_recovery_policies.py"),
        ("6", "post_review_checklist", "blocked_until_human_recovery_ready", "build_post_review_evidence_checklist.py"),
        ("7", "objective_requirements_audit", "blocked_until_post_review_ready", "audit_postdoc_objective_requirements.py"),
    ]
    lines = ["\t".join(header)]
    for step_order, step_type, status, command in steps:
        lines.append(
            "\t".join(
                [
                    step_order,
                    step_type,
                    status,
                    command,
                    "aggregate success condition",
                    "pending",
                    "",
                    "next aggregate action",
                    "aggregate-only",
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
            response_action_item_overview={
                "total_action_items": 126,
                "row_field_action_items": 48,
                "model_field_action_items": 72,
                "timing_action_items": 6,
            },
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
        "work_order",
        base_summary(
            status="review_work_order_ready",
            review_work_order_overview={
                "row_count": 6,
                "row_work_order_steps": 30,
                "packet_work_order_steps": 3,
                "total_work_order_steps": 33,
                "total_action_items": 126,
                "row_field_action_items": 48,
                "model_field_action_items": 72,
                "timing_action_items": 6,
            },
        ),
    )
    write_summary(
        root,
        "post_review_sequence",
        base_summary(
            ok=False,
            status="post_review_sequence_blocked",
            mode="plan_only",
            closeout_ready=False,
            refresh_complete=False,
            human_recovery_ready=False,
            post_review_ready=False,
            objective_requirements_ready=False,
            blocker_keys=[
                "strict_dry_run",
                "response_closeout",
                "write_refresh_prepare_next",
                "human_audit_refresh",
                "strict_human_reviewed_recovery",
                "post_review_checklist",
                "objective_requirements_audit",
            ],
            executed_step_count=0,
            execute_safety_policy=(
                "In --execute mode, stop before any blocked strict_dry_run, "
                "response_closeout, write_refresh_prepare_next, "
                "strict_human_reviewed_recovery, post_review_checklist, or "
                "objective_requirements_audit step; record executed_step_count "
                "and stopped_step in the aggregate summary/log."
            ),
        ),
    )
    write_summary(
        root,
        "objective",
        base_summary(
            objective_requirements_ready=False,
            status_counts={"satisfied": 8, "proxy_satisfied": 5, "review_pending": 2},
            requirement_rows=[
                {
                    "requirement_id": "6.3",
                    "status": "review_pending",
                    "paper_claim_status": "not paper-ready",
                    "evidence": (
                        "human_audit_post_review_evidence_summary.json; "
                        "human_audit_post_review_sequence_summary.json"
                    ),
                    "result": (
                        "recovery_human_ready=False; "
                        "post_review_sequence_status=post_review_sequence_blocked; "
                        "post_review_sequence_ok=False; "
                        "post_review_sequence_executed_step_count=0"
                    ),
                    "next_action": (
                        "After selected-300 response closeout is ready, run "
                        "run_post_review_evidence_sequence.py --execute so "
                        "write/refresh, strict human-reviewed recovery, post-review "
                        "checklist, and objective audit execute in order."
                    ),
                }
            ],
            next_decision=(
                "Do not declare the postdoc objective complete. Complete selected-300 "
                "row/model/timing review, run strict closeout, then execute "
                "run_post_review_evidence_sequence.py --execute so write/refresh, "
                "human predictor refresh, strict human-reviewed recovery, post-review "
                "checklist, and objective audit happen in order."
            ),
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
    write_action_items_tsv_fixture(root)
    write_work_order_tsv_fixture(root)
    write_post_review_sequence_tsv_fixture(root)


def test_consistency_audit_passes_current_blocked_but_aligned_state(tmp_path: Path) -> None:
    write_consistent_fixture(tmp_path)
    payload = build_consistency_audit(tmp_path)

    assert payload["ok"] is True
    assert payload["status_counts"] == {"pass": 23}
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


def test_consistency_audit_fails_response_action_item_count_drift(tmp_path: Path) -> None:
    write_consistent_fixture(tmp_path)
    action_path = tmp_path / RESPONSE_ACTION_ITEMS_TSV_RELATIVE
    lines = action_path.read_text(encoding="utf-8").splitlines()
    action_path.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")

    payload = build_consistency_audit(tmp_path)

    assert payload["ok"] is False
    assert any(item["check_id"] == "C069" for item in payload["failed_checks"])


def test_consistency_audit_fails_review_work_order_row_drift(tmp_path: Path) -> None:
    write_consistent_fixture(tmp_path)
    work_order_path = tmp_path / REVIEW_WORK_ORDER_TSV_RELATIVE
    lines = work_order_path.read_text(encoding="utf-8").splitlines()
    work_order_path.write_text(
        "\n".join([line for line in lines if not line.startswith("row-6:")]) + "\n",
        encoding="utf-8",
    )

    payload = build_consistency_audit(tmp_path)

    assert payload["ok"] is False
    assert any(item["check_id"] == "C071" for item in payload["failed_checks"])


def test_consistency_audit_fails_review_work_order_unsafe_dry_run(
    tmp_path: Path,
) -> None:
    write_consistent_fixture(tmp_path)
    work_order_path = tmp_path / REVIEW_WORK_ORDER_TSV_RELATIVE
    work_order_path.write_text(
        work_order_path.read_text(encoding="utf-8").replace(
            "--require-session-start-gate",
            "--write",
        ),
        encoding="utf-8",
    )

    payload = build_consistency_audit(tmp_path)

    assert payload["ok"] is False
    assert any(item["check_id"] == "C075" for item in payload["failed_checks"])


def test_consistency_audit_fails_review_work_order_missing_sequence_route(
    tmp_path: Path,
) -> None:
    write_consistent_fixture(tmp_path)
    work_order_path = tmp_path / REVIEW_WORK_ORDER_TSV_RELATIVE
    work_order_path.write_text(
        work_order_path.read_text(encoding="utf-8").replace(
            "run_post_review_evidence_sequence.py --execute",
            "build_post_review_evidence_checklist.py",
        ),
        encoding="utf-8",
    )

    payload = build_consistency_audit(tmp_path)

    assert payload["ok"] is False
    assert any(item["check_id"] == "C074" for item in payload["failed_checks"])


def test_consistency_audit_fails_post_review_sequence_allows_pending_recovery(
    tmp_path: Path,
) -> None:
    write_consistent_fixture(tmp_path)
    sequence_path = tmp_path / POST_REVIEW_SEQUENCE_TSV_RELATIVE
    sequence_path.write_text(
        sequence_path.read_text(encoding="utf-8").replace(
            "evaluate_human_reviewed_recovery_policies.py",
            "evaluate_human_reviewed_recovery_policies.py --allow-pending-summary",
        ),
        encoding="utf-8",
    )

    payload = build_consistency_audit(tmp_path)

    assert payload["ok"] is False
    assert any(item["check_id"] == "C072" for item in payload["failed_checks"])


def test_consistency_audit_fails_post_review_sequence_unsafe_dry_run(
    tmp_path: Path,
) -> None:
    write_consistent_fixture(tmp_path)
    sequence_path = tmp_path / POST_REVIEW_SEQUENCE_TSV_RELATIVE
    sequence_path.write_text(
        sequence_path.read_text(encoding="utf-8").replace(
            "--require-session-start-gate",
            "--write",
        ),
        encoding="utf-8",
    )

    payload = build_consistency_audit(tmp_path)

    assert payload["ok"] is False
    assert any(item["check_id"] == "C076" for item in payload["failed_checks"])


def test_consistency_audit_fails_post_review_sequence_missing_execute_safety(
    tmp_path: Path,
) -> None:
    write_consistent_fixture(tmp_path)
    sequence_path = tmp_path / SUMMARY_SPECS["post_review_sequence"]
    sequence = json.loads(sequence_path.read_text(encoding="utf-8"))
    sequence["execute_safety_policy"] = ""
    sequence_path.write_text(json.dumps(sequence, ensure_ascii=False), encoding="utf-8")

    payload = build_consistency_audit(tmp_path)

    assert payload["ok"] is False
    assert any(item["check_id"] == "C077" for item in payload["failed_checks"])


def test_consistency_audit_fails_objective_missing_sequence_route(
    tmp_path: Path,
) -> None:
    write_consistent_fixture(tmp_path)
    objective_path = tmp_path / SUMMARY_SPECS["objective"]
    objective = json.loads(objective_path.read_text(encoding="utf-8"))
    objective["requirement_rows"][0]["result"] = "recovery_human_ready=False"
    objective["next_decision"] = "Rerun objective audit after recovery."
    objective_path.write_text(json.dumps(objective, ensure_ascii=False), encoding="utf-8")

    payload = build_consistency_audit(tmp_path)

    assert payload["ok"] is False
    assert any(item["check_id"] == "C073" for item in payload["failed_checks"])


def test_consistency_safety_rejects_raw_field_tokens() -> None:
    try:
        assert_aggregate_safe({"bad": "hypothesis_text"})
    except ValueError as exc:
        assert "sensitive field token" in str(exc)
    else:
        raise AssertionError("sensitive field token did not fail")

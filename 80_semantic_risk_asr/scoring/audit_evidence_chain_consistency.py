#!/usr/bin/env python3
"""Audit cross-summary consistency for the CDS-ASR evidence chain.

This checker guards against evidence-chain drift after many aggregate summaries
are refreshed independently. It intentionally reads only tracked aggregate
records and writes only aggregate-safe pass/fail rows.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = (
    REPO_ROOT / "70_experiments" / "runs" / "postdoc_evidence_chain_2026_05_25"
)
SUMMARY_NAME = "evidence_chain_consistency_summary.json"
TSV_NAME = "evidence_chain_consistency.tsv"
RESPONSE_GAP_TSV_RELATIVE = (
    "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/"
    "human_audit_response_gap_checklist.tsv"
)
RESPONSE_ACTION_ITEMS_TSV_RELATIVE = (
    "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/"
    "human_audit_response_action_items.tsv"
)
REVIEW_WORK_ORDER_TSV_RELATIVE = (
    "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/"
    "human_audit_review_work_order.tsv"
)
POST_REVIEW_SEQUENCE_TSV_RELATIVE = (
    "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/"
    "human_audit_post_review_sequence.tsv"
)

SENSITIVE_TOKENS = (
    "audio_id",
    "sample_id",
    "reference_text",
    "hypothesis_text",
    "asr_hypotheses_json",
    "reviewer_model_assessments_json",
    "reviewer_notes",
    "reviewer_verified_transcript",
    "PRIVATE_",
)

REQUIRED_SCOPE_TERMS = (
    "risk",
    "decision",
    "expected safe action",
    "confidence",
    "per-model",
    "per-row review timing",
)

SUMMARY_SPECS = {
    "readiness": (
        "70_experiments/runs/postdoc_evidence_chain_2026_05_25/"
        "evidence_chain_readiness_summary.json"
    ),
    "publishable": (
        "70_experiments/runs/postdoc_evidence_chain_2026_05_25/"
        "publishable_evidence_completion_summary.json"
    ),
    "consequence": (
        "70_experiments/runs/postdoc_evidence_chain_2026_05_25/"
        "consequence_evidence_matrix_summary.json"
    ),
    "roadmap": (
        "70_experiments/runs/postdoc_evidence_chain_2026_05_25/"
        "postdoc_roadmap_completion_summary.json"
    ),
    "refresh": (
        "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/"
        "human_audit_refresh_summary.json"
    ),
    "post_review": (
        "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/"
        "human_audit_post_review_evidence_summary.json"
    ),
    "closeout": (
        "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/"
        "human_audit_response_closeout_summary.json"
    ),
    "apply": (
        "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/"
        "human_audit_batch_response_apply_summary.json"
    ),
    "handoff": (
        "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/"
        "human_audit_reviewer_handoff_summary.json"
    ),
    "action_checklist": (
        "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/"
        "human_audit_reviewer_action_checklist_summary.json"
    ),
    "session_start": (
        "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/"
        "human_audit_reviewer_session_start_summary.json"
    ),
    "work_order": (
        "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/"
        "human_audit_review_work_order_summary.json"
    ),
    "post_review_sequence": (
        "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/"
        "human_audit_post_review_sequence_summary.json"
    ),
    "candidate_recheck": (
        "70_experiments/runs/asr_candidate_current_recheck_2026_05_26/"
        "summary.json"
    ),
}

TSV_FIELDS = [
    "check_id",
    "invariant",
    "status",
    "evidence",
    "result",
    "next_action",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TSV_FIELDS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in TSV_FIELDS})


def read_tsv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def assert_aggregate_safe(payload: Any) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    for token in SENSITIVE_TOKENS:
        if token in text:
            raise ValueError("sensitive field token leaked into consistency audit")


def check_row(
    *,
    check_id: str,
    invariant: str,
    passed: bool,
    evidence: str,
    result: str,
    next_action: str,
) -> dict[str, str]:
    return {
        "check_id": check_id,
        "invariant": invariant,
        "status": "pass" if passed else "fail",
        "evidence": evidence,
        "result": result,
        "next_action": next_action,
    }


def load_summaries(root: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]]]:
    payloads: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, str]] = []
    missing: list[str] = []
    parse_errors: list[str] = []
    for name, relative in SUMMARY_SPECS.items():
        path = root / relative
        if not path.exists():
            missing.append(name)
            continue
        try:
            payloads[name] = read_json(path)
        except json.JSONDecodeError:
            parse_errors.append(name)

    passed = not missing and not parse_errors
    rows.append(
        check_row(
            check_id="C001",
            invariant="required aggregate summaries exist and are parseable",
            passed=passed,
            evidence="; ".join(SUMMARY_SPECS.values()),
            result=(
                "all required summaries loaded"
                if passed
                else f"missing={','.join(missing) or 'none'}; parse_errors={','.join(parse_errors) or 'none'}"
            ),
            next_action="Regenerate missing or invalid aggregate summaries before publishing evidence-chain claims.",
        )
    )
    return payloads, rows


def text_has_all_terms(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return all(term.lower() in lowered for term in terms)


def add_policy_checks(payloads: dict[str, dict[str, Any]], rows: list[dict[str, str]]) -> None:
    policy_names = [
        "readiness",
        "publishable",
        "consequence",
        "roadmap",
        "refresh",
        "post_review",
        "closeout",
        "apply",
        "handoff",
        "action_checklist",
        "session_start",
    ]
    transcript_failures = [
        name
        for name in policy_names
        if not (
            "human-reviewed" in str(payloads.get(name, {}).get("reference_transcript_policy", "")).lower()
            and "wer/cer" in str(payloads.get(name, {}).get("reference_transcript_policy", "")).lower()
            and (
                "do not route duplicate" in str(payloads.get(name, {}).get("reference_transcript_policy", "")).lower()
                or "does not ask" in str(payloads.get(name, {}).get("reference_transcript_policy", "")).lower()
            )
        )
    ]
    rows.append(
        check_row(
            check_id="C010",
            invariant="transcript ground truth policy is not reopened",
            passed=not transcript_failures,
            evidence="reference_transcript_policy fields across aggregate summaries",
            result=(
                "all summaries keep transcript ground truth as already reviewed"
                if not transcript_failures
                else f"policy drift in {','.join(transcript_failures)}"
            ),
            next_action="Refresh the stale summaries from source constants before routing reviewer work.",
        )
    )

    scope_failures = [
        name
        for name in policy_names
        if not text_has_all_terms(
            str(payloads.get(name, {}).get("remaining_review_scope", "")),
            REQUIRED_SCOPE_TERMS,
        )
    ]
    rows.append(
        check_row(
            check_id="C020",
            invariant="remaining selected-300 review scope includes row/model/timing fields",
            passed=not scope_failures,
            evidence="remaining_review_scope fields across aggregate summaries",
            result=(
                "all summaries name risk, decision, expected action, confidence, per-model fields, and per-row timing"
                if not scope_failures
                else f"scope drift in {','.join(scope_failures)}"
            ),
            next_action="Rerun the stale aggregate generator and do not proceed to write/refresh while scope is inconsistent.",
        )
    )


def add_timing_checks(payloads: dict[str, dict[str, Any]], rows: list[dict[str, str]]) -> None:
    apply = payloads.get("apply", {})
    apply_timing = apply.get("review_timing", {})
    apply_passed = (
        apply.get("require_timing") is True
        and apply_timing.get("rows_missing_timing", -1) == 6
        and "--require-timing" in str(apply.get("next_action", ""))
    )
    rows.append(
        check_row(
            check_id="C030",
            invariant="strict response apply gate requires timing",
            passed=apply_passed,
            evidence=SUMMARY_SPECS["apply"],
            result=(
                "apply dry-run records require_timing=true and 6 timing rows pending"
                if apply_passed
                else "apply dry-run timing requirement is stale or incomplete"
            ),
            next_action="Run the session-gated strict response dry-run with --require-complete --require-timing.",
        )
    )

    closeout = payloads.get("closeout", {})
    closeout_timing = closeout.get("review_timing", {})
    closeout_passed = (
        closeout.get("require_timing") is True
        and closeout.get("status") == "response_closeout_blocked"
        and closeout_timing.get("rows_missing_timing", -1) == 6
    )
    rows.append(
        check_row(
            check_id="C031",
            invariant="response closeout blocks on missing timing",
            passed=closeout_passed,
            evidence=SUMMARY_SPECS["closeout"],
            result=(
                "closeout blocks write/refresh while 6 timing rows are missing"
                if closeout_passed
                else "closeout timing blocker is not aligned with current packet state"
            ),
            next_action="Keep write/refresh blocked until timing coverage is complete.",
        )
    )

    high_level = {
        "readiness": str(payloads.get("readiness", {}).get("next_decision", "")),
        "publishable": str(payloads.get("publishable", {}).get("next_decision", "")),
        "consequence": str(payloads.get("consequence", {}).get("next_decision", "")),
        "roadmap": str(payloads.get("roadmap", {}).get("next_decision", "")),
        "refresh": str(payloads.get("refresh", {}).get("next_action", "")),
    }
    next_action_failures = [
        name
        for name, text in high_level.items()
        if "timing" not in text.lower() or "--require-timing" not in text
    ]
    rows.append(
        check_row(
            check_id="C032",
            invariant="top-level next actions route through the timing gate",
            passed=not next_action_failures,
            evidence="readiness/publishable/consequence/roadmap/refresh next action fields",
            result=(
                "all top-level next actions mention timing and --require-timing"
                if not next_action_failures
                else f"timing next-action drift in {','.join(next_action_failures)}"
            ),
            next_action="Refresh top-level summaries so reviewers cannot bypass timing closeout.",
        )
    )


def add_readiness_checks(payloads: dict[str, dict[str, Any]], rows: list[dict[str, str]]) -> None:
    refresh = payloads.get("refresh", {})
    readiness = payloads.get("readiness", {})
    publishable = payloads.get("publishable", {})
    consequence = payloads.get("consequence", {})
    roadmap = payloads.get("roadmap", {})
    post_review = payloads.get("post_review", {})
    closeout = payloads.get("closeout", {})

    review_pending = refresh.get("status") == "review_pending"
    not_ready = (
        readiness.get("paper_ready") is False
        and publishable.get("publishable_ready") is False
        and consequence.get("paper_claims_ready") is False
        and roadmap.get("roadmap_complete") is False
        and post_review.get("status") == "post_review_evidence_blocked"
        and closeout.get("status") == "response_closeout_blocked"
    )
    rows.append(
        check_row(
            check_id="C040",
            invariant="review-pending state cannot be paper-ready",
            passed=bool(review_pending and not_ready),
            evidence="readiness, publishable, consequence, roadmap, post-review, closeout summaries",
            result=(
                "selected-300 review is pending and every paper-facing gate remains closed"
                if review_pending and not_ready
                else "at least one paper-facing gate conflicts with pending selected-300 review"
            ),
            next_action="Keep claims proxy-only until response closeout, write, refresh, predictor, and recovery are complete.",
        )
    )

    proxy_passed = (
        publishable.get("publishable_ready") is False
        and consequence.get("paper_claims_ready") is False
        and len(publishable.get("blocking_or_proxy_items", [])) > 0
        and len(consequence.get("blocking_or_proxy_items", [])) > 0
    )
    rows.append(
        check_row(
            check_id="C050",
            invariant="proxy evidence is not promoted to paper claims",
            passed=proxy_passed,
            evidence="publishable_evidence_completion_summary and consequence_evidence_matrix_summary",
            result=(
                "blocking/proxy items remain explicit while publishable and consequence gates are closed"
                if proxy_passed
                else "proxy evidence may be over-promoted or missing blocker detail"
            ),
            next_action="Keep 258-row/300-row proxy results as engineering evidence until human labels refresh them.",
        )
    )

    action_gate = readiness.get("reviewer_action_gate", {})
    action_passed = (
        action_gate.get("status") == "reviewer_action_ready"
        and action_gate.get("rows_in_batch") == 6
        and action_gate.get("pending_rows_in_batch") == 6
        and action_gate.get("model_assessments_in_batch") == 18
        and action_gate.get("pending_model_assessments_in_batch") == 18
        and action_gate.get("rows_missing_timing") == 6
    )
    rows.append(
        check_row(
            check_id="C060",
            invariant="current reviewer action packet remains ready but unfilled",
            passed=action_passed,
            evidence=SUMMARY_SPECS["readiness"],
            result=(
                "current packet has 6 rows, 18 model assessments, and 6 timing rows pending"
                if action_passed
                else "reviewer action packet counts drifted from expected selected batch"
            ),
            next_action="Fill only local response fields and timing; do not reopen transcript review.",
        )
    )

    handoff = payloads.get("handoff", {})
    handoff_gate = (
        handoff.get("current_gate")
        if isinstance(handoff.get("current_gate"), dict)
        else {}
    )
    handoff_passed = (
        handoff.get("ok") is True
        and handoff.get("freshness_status") == "fresh"
        and handoff.get("status") == "reviewer_input_pending"
        and handoff_gate.get("latest_apply_status") == "response_pending"
        and handoff_gate.get("pending_rows_in_batch") == 6
        and handoff_gate.get("pending_model_assessments_in_batch") == 18
        and handoff_gate.get("rows_missing_timing") == 6
    )
    rows.append(
        check_row(
            check_id="C065",
            invariant="current reviewer handoff is fresh and timing-aware",
            passed=handoff_passed,
            evidence=SUMMARY_SPECS["handoff"],
            result=(
                "handoff is fresh and points to 6 pending rows, 18 model assessments, and 6 timing rows"
                if handoff_passed
                else "reviewer handoff is stale or does not match the current row/model/timing gate"
            ),
            next_action="Regenerate reviewer handoff and action checklist before opening the local review packet.",
        )
    )


def add_command_plan_check(payloads: dict[str, dict[str, Any]], rows: list[dict[str, str]]) -> None:
    post_review = payloads.get("post_review", {})
    closeout = payloads.get("closeout", {})
    plan = post_review.get("post_review_command_plan")
    plan = plan if isinstance(plan, dict) else {}
    closeout_commands = plan.get("closeout_commands")
    closeout_commands = closeout_commands if isinstance(closeout_commands, dict) else {}
    post_write_order = plan.get("post_write_order")
    post_write_order = post_write_order if isinstance(post_write_order, list) else []
    ordered_gates = [
        str(item.get("gate", ""))
        for item in post_write_order
        if isinstance(item, dict)
    ]
    commands_by_gate = {
        str(item.get("gate", "")): str(item.get("command", ""))
        for item in post_write_order
        if isinstance(item, dict)
    }
    expected_gates = [
        "human_audit_refresh",
        "strict_human_reviewed_recovery",
        "post_review_checklist",
        "objective_requirements_audit",
    ]
    strict_dry_run = str(closeout_commands.get("strict_dry_run", ""))
    write_refresh = str(closeout_commands.get("write_refresh_prepare_next", ""))
    strict_recovery = commands_by_gate.get("strict_human_reviewed_recovery", "")
    plan_passed = (
        plan.get("current_first_action") == "complete_response_closeout"
        and closeout.get("status") == "response_closeout_blocked"
        and all(flag in strict_dry_run for flag in (
            "--require-complete",
            "--require-timing",
            "--require-session-start-gate",
        ))
        and all(flag in write_refresh for flag in (
            "--write",
            "--refresh-after-write",
            "--prepare-next-after-write",
            "--require-complete",
            "--require-timing",
            "--require-session-start-gate",
        ))
        and ordered_gates == expected_gates
        and "refresh_human_audit_evidence.py" in commands_by_gate.get("human_audit_refresh", "")
        and "evaluate_human_reviewed_recovery_policies.py" in strict_recovery
        and "--allow-pending-summary" not in strict_recovery
        and "build_post_review_evidence_checklist.py" in commands_by_gate.get("post_review_checklist", "")
        and "audit_postdoc_objective_requirements.py" in commands_by_gate.get("objective_requirements_audit", "")
    )
    rows.append(
        check_row(
            check_id="C066",
            invariant="post-review command plan preserves strict recovery order",
            passed=plan_passed,
            evidence=SUMMARY_SPECS["post_review"],
            result=(
                "post-review command plan starts with response closeout and routes through refresh, strict recovery, checklist, and objective audit"
                if plan_passed
                else "post-review command plan is missing, stale, out of order, or allows pending recovery evidence"
            ),
            next_action="Refresh the post-review checklist before local response write/refresh and do not promote proxy recovery.",
        )
    )


def timing_command_coverage(
    commands: dict[str, Any],
    row_numbers: list[int],
) -> tuple[bool, list[str]]:
    start_by_row = commands.get("timing_start_write_by_row")
    finish_by_row = commands.get("timing_finish_write_by_row")
    if not isinstance(start_by_row, dict) or not isinstance(finish_by_row, dict):
        return False, ["missing_by_row_command_maps"]

    missing_or_invalid: list[str] = []
    for row_number in row_numbers:
        key = str(row_number)
        start = str(start_by_row.get(key, "") or "")
        finish = str(finish_by_row.get(key, "") or "")
        if not all(
            token in start
            for token in (
                "mark_human_audit_response_timing.py",
                f"--row-number {row_number}",
                "--mark-start",
                "--write",
            )
        ):
            missing_or_invalid.append(f"start:{key}")
        if not all(
            token in finish
            for token in (
                "mark_human_audit_response_timing.py",
                f"--row-number {row_number}",
                "--mark-finish",
                "--write",
            )
        ):
            missing_or_invalid.append(f"finish:{key}")

    first = str(row_numbers[0]) if row_numbers else ""
    alias_ok = True
    if first:
        alias_ok = (
            commands.get("timing_start_write") == start_by_row.get(first)
            and commands.get("timing_finish_write") == finish_by_row.get(first)
        )
        if not alias_ok:
            missing_or_invalid.append("row_1_alias")
    return not missing_or_invalid, missing_or_invalid


def add_reviewer_timing_command_check(
    payloads: dict[str, dict[str, Any]],
    rows: list[dict[str, str]],
) -> None:
    handoff = payloads.get("handoff", {})
    action = payloads.get("action_checklist", {})
    session = payloads.get("session_start", {})
    packet = handoff.get("current_packet") if isinstance(handoff.get("current_packet"), dict) else {}
    row_numbers = [
        int(item)
        for item in packet.get("row_numbers", [])
        if isinstance(item, int) or (isinstance(item, str) and item.isdigit())
    ]
    expected_rows = [1, 2, 3, 4, 5, 6]
    handoff_ok, handoff_errors = timing_command_coverage(
        handoff.get("commands", {}) if isinstance(handoff.get("commands"), dict) else {},
        row_numbers,
    )
    action_ok, action_errors = timing_command_coverage(
        action.get("timing_helper_commands", {})
        if isinstance(action.get("timing_helper_commands"), dict)
        else {},
        row_numbers,
    )
    session_ok, session_errors = timing_command_coverage(
        session.get("commands", {}) if isinstance(session.get("commands"), dict) else {},
        row_numbers,
    )
    passed = (
        row_numbers == expected_rows
        and handoff_ok
        and action_ok
        and session_ok
    )
    error_text = "; ".join(
        part
        for part in (
            f"row_numbers={row_numbers}" if row_numbers != expected_rows else "",
            f"handoff={','.join(handoff_errors)}" if handoff_errors else "",
            f"action={','.join(action_errors)}" if action_errors else "",
            f"session={','.join(session_errors)}" if session_errors else "",
        )
        if part
    )
    rows.append(
        check_row(
            check_id="C067",
            invariant="per-row timing helper commands cover the current reviewer packet",
            passed=passed,
            evidence=(
                f"{SUMMARY_SPECS['handoff']}; "
                f"{SUMMARY_SPECS['action_checklist']}; "
                f"{SUMMARY_SPECS['session_start']}"
            ),
            result=(
                "timing helper commands cover rows 1-6 across handoff, action checklist, and session start"
                if passed
                else f"per-row timing command coverage drifted: {error_text or 'unknown'}"
            ),
            next_action="Regenerate reviewer handoff, action checklist, and session start before local review timing entry.",
        )
    )


def add_gap_tsv_command_check(
    root: Path,
    payloads: dict[str, dict[str, Any]],
    rows: list[dict[str, str]],
) -> None:
    gap_tsv_path = root / RESPONSE_GAP_TSV_RELATIVE
    if not gap_tsv_path.exists():
        rows.append(
            check_row(
                check_id="C068",
                invariant="response gap TSV includes per-row timing helper commands",
                passed=False,
                evidence=RESPONSE_GAP_TSV_RELATIVE,
                result="response gap TSV is missing",
                next_action="Rerun build_human_audit_response_closeout_checklist.py before reviewer work.",
            )
        )
        return

    gap_rows = read_tsv_rows(gap_tsv_path)
    closeout = payloads.get("closeout", {})
    closeout_rows = closeout.get("response_gap_summary_by_row")
    closeout_rows = closeout_rows if isinstance(closeout_rows, list) else []
    expected_row_numbers = [
        str(item.get("row_number", ""))
        for item in closeout_rows
        if isinstance(item, dict)
    ]
    gap_row_numbers = [str(item.get("row_number", "")) for item in gap_rows]
    handoff = payloads.get("handoff", {})
    commands = handoff.get("commands") if isinstance(handoff.get("commands"), dict) else {}
    start_by_row = commands.get("timing_start_write_by_row")
    finish_by_row = commands.get("timing_finish_write_by_row")
    start_by_row = start_by_row if isinstance(start_by_row, dict) else {}
    finish_by_row = finish_by_row if isinstance(finish_by_row, dict) else {}
    command_errors: list[str] = []
    for row in gap_rows:
        row_number = str(row.get("row_number", ""))
        start = str(row.get("timing_start_write_command", "") or "")
        finish = str(row.get("timing_finish_write_command", "") or "")
        if start != str(start_by_row.get(row_number, "") or ""):
            command_errors.append(f"start:{row_number}")
        if finish != str(finish_by_row.get(row_number, "") or ""):
            command_errors.append(f"finish:{row_number}")

    sensitive = False
    try:
        assert_aggregate_safe(gap_rows)
    except ValueError:
        sensitive = True

    passed = (
        gap_row_numbers == expected_row_numbers
        and expected_row_numbers == ["1", "2", "3", "4", "5", "6"]
        and not command_errors
        and not sensitive
    )
    rows.append(
        check_row(
            check_id="C068",
            invariant="response gap TSV includes per-row timing helper commands",
            passed=passed,
            evidence=RESPONSE_GAP_TSV_RELATIVE,
            result=(
                "gap TSV rows 1-6 match closeout gaps and handoff timing commands"
                if passed
                else (
                    f"gap_row_numbers={gap_row_numbers}; "
                    f"expected={expected_row_numbers}; "
                    f"command_errors={','.join(command_errors) or 'none'}; "
                    f"sensitive={sensitive}"
                )
            ),
            next_action="Regenerate closeout gap TSV and reviewer handoff before local review timing entry.",
        )
    )


def add_response_action_items_check(
    root: Path,
    payloads: dict[str, dict[str, Any]],
    rows: list[dict[str, str]],
) -> None:
    action_items_path = root / RESPONSE_ACTION_ITEMS_TSV_RELATIVE
    if not action_items_path.exists():
        rows.append(
            check_row(
                check_id="C069",
                invariant="response action-items TSV matches closeout gap counts",
                passed=False,
                evidence=RESPONSE_ACTION_ITEMS_TSV_RELATIVE,
                result="response action-items TSV is missing",
                next_action="Rerun build_human_audit_response_closeout_checklist.py before reviewer work.",
            )
        )
        return

    action_items = read_tsv_rows(action_items_path)
    closeout = payloads.get("closeout", {})
    overview = closeout.get("response_action_item_overview")
    overview = overview if isinstance(overview, dict) else {}
    counts = {
        "total_action_items": len(action_items),
        "row_field_action_items": sum(
            1 for item in action_items if item.get("action_scope") == "row_field"
        ),
        "model_field_action_items": sum(
            1
            for item in action_items
            if item.get("action_scope") == "model_assessment_field"
        ),
        "timing_action_items": sum(
            1 for item in action_items if item.get("action_scope") == "review_timing"
        ),
    }
    expected_counts = {
        "total_action_items": int(overview.get("total_action_items") or 0),
        "row_field_action_items": int(overview.get("row_field_action_items") or 0),
        "model_field_action_items": int(overview.get("model_field_action_items") or 0),
        "timing_action_items": int(overview.get("timing_action_items") or 0),
    }
    unique_action_ids = {
        str(item.get("action_id", ""))
        for item in action_items
        if item.get("action_id")
    }
    all_items_pending = all(item.get("status") == "pending" for item in action_items)
    timing_items_have_commands = all(
        item.get("timing_start_write_command")
        and item.get("timing_finish_write_command")
        for item in action_items
        if item.get("action_scope") == "review_timing"
    )
    sensitive = False
    try:
        assert_aggregate_safe(action_items)
    except ValueError:
        sensitive = True

    passed = (
        counts == expected_counts
        and len(unique_action_ids) == len(action_items)
        and all_items_pending
        and timing_items_have_commands
        and not sensitive
    )
    rows.append(
        check_row(
            check_id="C069",
            invariant="response action-items TSV matches closeout gap counts",
            passed=passed,
            evidence=RESPONSE_ACTION_ITEMS_TSV_RELATIVE,
            result=(
                "action-items TSV has unique pending row/model/timing items and matches closeout counts"
                if passed
                else (
                    f"counts={counts}; expected={expected_counts}; "
                    f"unique_action_ids={len(unique_action_ids)}/{len(action_items)}; "
                    f"all_items_pending={all_items_pending}; "
                    f"timing_items_have_commands={timing_items_have_commands}; "
                    f"sensitive={sensitive}"
                )
            ),
            next_action="Regenerate response action-items TSV from closeout before local review.",
        )
    )


def add_review_work_order_check(
    root: Path,
    payloads: dict[str, dict[str, Any]],
    rows: list[dict[str, str]],
) -> None:
    work_order_path = root / REVIEW_WORK_ORDER_TSV_RELATIVE
    if not work_order_path.exists():
        rows.append(
            check_row(
                check_id="C071",
                invariant="review work-order TSV covers current packet actions",
                passed=False,
                evidence=REVIEW_WORK_ORDER_TSV_RELATIVE,
                result="review work-order TSV is missing",
                next_action="Run build_human_audit_review_work_order.py before reviewer work.",
            )
        )
        return

    work_order = payloads.get("work_order", {})
    overview = work_order.get("review_work_order_overview")
    overview = overview if isinstance(overview, dict) else {}
    closeout = payloads.get("closeout", {})
    closeout_overview = closeout.get("response_action_item_overview")
    closeout_overview = closeout_overview if isinstance(closeout_overview, dict) else {}
    closeout_rows = closeout.get("response_gap_summary_by_row")
    closeout_row_numbers = {
        str(item.get("row_number", ""))
        for item in closeout_rows
        if isinstance(item, dict) and item.get("row_number") is not None
    } if isinstance(closeout_rows, list) else set()
    rows_tsv = read_tsv_rows(work_order_path)
    row_step_numbers = {
        item.get("row_number", "")
        for item in rows_tsv
        if item.get("row_number") and item.get("row_number") != "packet"
    }
    step_types = {item.get("step_type", "") for item in rows_tsv}
    required_step_types = {
        "mark_timing_start",
        "open_local_row",
        "fill_row_fields",
        "fill_model_fields",
        "mark_timing_finish",
        "strict_dry_run",
        "response_closeout",
        "write_refresh_prepare_next",
        "post_review_checklist",
        "objective_requirements_audit",
    }
    sensitive = False
    try:
        assert_aggregate_safe({"summary": work_order, "rows": rows_tsv})
    except ValueError:
        sensitive = True
    counts_match = int(overview.get("total_action_items") or 0) == int(
        closeout_overview.get("total_action_items") or 0
    )
    row_coverage_ok = row_step_numbers == closeout_row_numbers
    steps_ok = required_step_types.issubset(step_types)
    status_ok = work_order.get("status") == "review_work_order_ready"
    passed = counts_match and row_coverage_ok and steps_ok and status_ok and not sensitive
    rows.append(
        check_row(
            check_id="C071",
            invariant="review work-order TSV covers current packet actions",
            passed=passed,
            evidence=REVIEW_WORK_ORDER_TSV_RELATIVE,
            result=(
                "review work-order TSV covers current row/model/timing actions and packet closeout order"
                if passed
                else (
                    f"counts_match={counts_match}; "
                    f"row_coverage_ok={row_coverage_ok}; "
                    f"steps_ok={steps_ok}; "
                    f"status={work_order.get('status', '')}; "
                    f"sensitive={sensitive}"
                )
            ),
            next_action="Regenerate review work order from action-items, closeout, and handoff summaries before local review.",
        )
    )


def add_post_review_sequence_check(
    root: Path,
    payloads: dict[str, dict[str, Any]],
    rows: list[dict[str, str]],
) -> None:
    sequence_path = root / POST_REVIEW_SEQUENCE_TSV_RELATIVE
    if not sequence_path.exists():
        rows.append(
            check_row(
                check_id="C072",
                invariant="post-review sequence preserves strict evidence order",
                passed=False,
                evidence=POST_REVIEW_SEQUENCE_TSV_RELATIVE,
                result="post-review sequence TSV is missing",
                next_action="Run run_post_review_evidence_sequence.py before final post-review claims.",
            )
        )
        return

    sequence = payloads.get("post_review_sequence", {})
    sequence_rows = read_tsv_rows(sequence_path)
    step_types = [item.get("step_type", "") for item in sequence_rows]
    expected_order = [
        "strict_dry_run",
        "response_closeout",
        "write_refresh_prepare_next",
        "human_audit_refresh",
        "strict_human_reviewed_recovery",
        "post_review_checklist",
        "objective_requirements_audit",
    ]
    strict_recovery_rows = [
        item
        for item in sequence_rows
        if item.get("step_type") == "strict_human_reviewed_recovery"
    ]
    strict_recovery_command = strict_recovery_rows[0].get("command", "") if strict_recovery_rows else ""
    closeout = payloads.get("closeout", {})
    closeout_ready = (
        closeout.get("ok") is True
        and closeout.get("status") == "response_complete_ready_to_write"
    )
    blocked_state_ok = (
        closeout_ready
        or sequence.get("status") == "post_review_sequence_blocked"
        and "strict_dry_run" in sequence.get("blocker_keys", [])
    )
    command_strict = (
        "evaluate_human_reviewed_recovery_policies.py" in strict_recovery_command
        and "--allow-pending-summary" not in strict_recovery_command
    )
    sequence_status = sequence.get("status", "")
    status_ok = sequence.get("mode") == "plan_only" and (
        (
            sequence_status in {
                "post_review_sequence_blocked",
                "post_review_sequence_ready_to_execute",
            }
            and sequence.get("ok") is False
        )
        or (
            sequence_status == "post_review_sequence_complete"
            and sequence.get("ok") is True
        )
    )
    order_ok = step_types == expected_order
    sensitive = False
    try:
        assert_aggregate_safe({"summary": sequence, "rows": sequence_rows})
    except ValueError:
        sensitive = True
    passed = order_ok and command_strict and status_ok and blocked_state_ok and not sensitive
    rows.append(
        check_row(
            check_id="C072",
            invariant="post-review sequence preserves strict evidence order",
            passed=passed,
            evidence=POST_REVIEW_SEQUENCE_TSV_RELATIVE,
            result=(
                "post-review sequence is plan-only, ordered, strict, and blocked before response closeout"
                if passed
                else (
                    f"order_ok={order_ok}; "
                    f"command_strict={command_strict}; "
                    f"status_ok={status_ok}; "
                    f"blocked_state_ok={blocked_state_ok}; "
                    f"sensitive={sensitive}"
                )
            ),
            next_action=(
                "After local response closeout is ready, run the sequence with --execute; "
                "do not skip strict human-reviewed recovery or objective audit."
            ),
        )
    )


def add_candidate_check(payloads: dict[str, dict[str, Any]], rows: list[dict[str, str]]) -> None:
    candidate = payloads.get("candidate_recheck", {})
    bounded_statuses = {
        str(item.get("status", ""))
        for item in candidate.get("bounded_probes", [])
        if isinstance(item, dict)
    }
    promotion = str(candidate.get("promotion_decision", "")).lower()
    candidate_passed = (
        candidate.get("ok") is True
        and "no requested asr/gemma candidate" in promotion
        and "timeout_before_inference" in bounded_statuses
        and "blocked_local_transformers_multimodal_class_missing" in bounded_statuses
    )
    rows.append(
        check_row(
            check_id="C070",
            invariant="expanded ASR/Gemma candidates stay behind locale/runtime gates",
            passed=candidate_passed,
            evidence=SUMMARY_SPECS["candidate_recheck"],
            result=(
                "current recheck keeps Whisper v3/v3-turbo, SenseVoice, Qwen3-ASR, and Gemma from promotion"
                if candidate_passed
                else "candidate promotion decision or blocked/runtime evidence is incomplete"
            ),
            next_action="Do not run 258-row or selected-300 promotion for these candidates before locale/runtime policy changes.",
        )
    )


def add_safety_check(payloads: dict[str, dict[str, Any]], rows: list[dict[str, str]]) -> None:
    safe = True
    for payload in payloads.values():
        try:
            assert_aggregate_safe(payload)
        except ValueError:
            safe = False
            break
    rows.append(
        check_row(
            check_id="C080",
            invariant="source summaries remain aggregate-safe",
            passed=safe,
            evidence="all input aggregate summaries",
            result=(
                "no transcript-bearing field tokens were found in source summaries"
                if safe
                else "one or more source summaries contains a blocked raw-field token"
            ),
            next_action="Remove raw row-level content from tracked summaries before committing.",
        )
    )


def build_consistency_audit(root: Path) -> dict[str, Any]:
    payloads, rows = load_summaries(root)
    if len(payloads) == len(SUMMARY_SPECS):
        add_policy_checks(payloads, rows)
        add_timing_checks(payloads, rows)
        add_readiness_checks(payloads, rows)
        add_command_plan_check(payloads, rows)
        add_reviewer_timing_command_check(payloads, rows)
        add_gap_tsv_command_check(root, payloads, rows)
        add_response_action_items_check(root, payloads, rows)
        add_review_work_order_check(root, payloads, rows)
        add_post_review_sequence_check(root, payloads, rows)
        add_candidate_check(payloads, rows)
        add_safety_check(payloads, rows)

    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    failed = [row for row in rows if row["status"] != "pass"]
    payload = {
        "ok": not failed,
        "status_counts": dict(sorted(counts.items())),
        "failed_checks": [
            {
                "check_id": row["check_id"],
                "invariant": row["invariant"],
                "result": row["result"],
                "next_action": row["next_action"],
            }
            for row in failed
        ],
        "reference_transcript_policy": "Reference transcripts are already human-reviewed for WER/CER; this audit does not reopen transcript review.",
        "remaining_review_scope": "Selected-300 completion still requires risk, decision, expected safe action, confidence, per-model fields, and per-row review timing.",
        "consistency_rows": rows,
        "next_decision": (
            "If this audit is pass, continue with the local selected-300 "
            "row/model/timing response closeout; if it fails, refresh the stale "
            "aggregate generator before paper-facing claims."
        ),
    }
    assert_aggregate_safe(payload)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-tsv", type=Path)
    return parser.parse_args()


def main() -> int:
    started = time.time()
    args = parse_args()
    payload = build_consistency_audit(args.repo_root.resolve())
    payload["runtime_seconds"] = round(time.time() - started, 4)
    assert_aggregate_safe(payload)
    output_json = args.output_json or args.output_dir / SUMMARY_NAME
    output_tsv = args.output_tsv or args.output_dir / TSV_NAME
    write_json(output_json, payload)
    write_tsv(output_tsv, payload["consistency_rows"])
    print(
        json.dumps(
            {
                "ok": payload["ok"],
                "status_counts": payload["status_counts"],
                "failed_checks": payload["failed_checks"],
                "output_json": str(output_json),
                "output_tsv": str(output_tsv),
            },
            ensure_ascii=False,
        )
    )
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

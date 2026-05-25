#!/usr/bin/env python3
"""Build a repo-safe value contract for selected-300 reviewer work."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
ANNOTATION_DIR = SCRIPT_PATH.parent
REPO_ROOT = SCRIPT_PATH.parents[2]
if str(ANNOTATION_DIR) not in sys.path:
    sys.path.insert(0, str(ANNOTATION_DIR))

import validate_human_risk_atom_audit as validation  # noqa: E402
from build_human_audit_reviewer_action_checklist import (  # noqa: E402
    CHECKLIST_SUMMARY_NAME,
)
from build_human_audit_reviewer_handoff import DEFAULT_RUN_DIR  # noqa: E402
from prepare_human_audit_review_batch import (  # noqa: E402
    REFERENCE_TRANSCRIPT_POLICY,
    REMAINING_REVIEW_SCOPE,
    assert_tracked_safe,
    repo_relative,
)


RUBRIC_SUMMARY_NAME = "human_audit_reviewer_rubric_summary.json"
VALUE_CONTRACT_TSV_NAME = "human_audit_reviewer_value_contract.tsv"


VALUE_GUIDANCE = {
    "row_risk_label": {
        "no_escalation": "No high-stakes routing or intervention should be triggered.",
        "review": "Manual review is warranted, but not urgent escalation.",
        "priority_review": "Priority human review is warranted because a safety-relevant risk is present.",
        "critical_escalation": "Immediate escalation is warranted because the risk could be severe.",
    },
    "decision_change": {
        "yes": "The ASR difference could change escalation, routing, or conservative action.",
        "no": "The ASR difference is harmless for the downstream decision.",
        "uncertain": "The decision effect is unresolved from the available review context.",
    },
    "safe_action": {
        "none": "No additional action is needed after review.",
        "manual_review": "Route to normal human review.",
        "priority_review": "Route to high-priority human review.",
        "critical_escalation": "Escalate immediately.",
        "conservative_machine_action": "Use a conservative automated action instead of unsafe downrouting.",
        "abstain": "Do not make an automated decision.",
    },
    "confidence": {
        "high": "Clear evidence supports the review decision.",
        "medium": "Evidence supports the decision, but some ambiguity remains.",
        "low": "The decision is tentative or needs a second reviewer.",
    },
    "risk_atom": {
        "negation": "A negation or denial changes the safety meaning.",
        "amount": "A money, count, or magnitude term changes the risk.",
        "action": "A requested or reported action changes the risk.",
        "actor": "The person or organization involved changes the risk.",
        "intent": "Intent, willingness, or pressure changes the risk.",
        "time": "Timing, deadline, or sequence changes the risk.",
        "uncertainty": "A hedge, doubt, or ambiguity changes the risk.",
        "scam_pattern": "A scam-specific pattern or scenario changes the risk.",
    },
}


def read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = ["category", "value", "use_when", "paper_evidence_role", "caution"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def value_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for category, guidance in VALUE_GUIDANCE.items():
        for value in sorted(guidance):
            rows.append(
                {
                    "category": category,
                    "value": value,
                    "use_when": guidance[value],
                    "paper_evidence_role": paper_role(category),
                    "caution": caution_for(category, value),
                }
            )
    return rows


def paper_role(category: str) -> str:
    return {
        "row_risk_label": "row-level human risk target",
        "decision_change": "decision-stability target",
        "safe_action": "recovery-policy target",
        "confidence": "review-quality stratifier",
        "risk_atom": "semantic consequence category",
    }[category]


def caution_for(category: str, value: str) -> str:
    if category == "decision_change" and value == "yes":
        return "Use only for a plausible downstream decision change, not a harmless wording error."
    if category == "decision_change" and value == "uncertain":
        return "Prefer low or medium confidence and consider abstain or review actions."
    if category == "safe_action" and value == "none":
        return "Use only when the decision remains safe."
    if category == "confidence" and value == "high":
        return "Use only when the decision-relevant span is clear."
    return ""


def current_gate_from_action_checklist(path: Path) -> dict[str, Any]:
    payload = read_json_if_exists(path)
    if not payload:
        return {
            "available": False,
            "status": "missing",
            "selection_stratum": "",
            "pending_rows_in_batch": 0,
            "rows_in_batch": 0,
            "pending_model_assessments_in_batch": 0,
            "model_assessments_in_batch": 0,
            "rows_missing_timing": 0,
            "latest_apply_status": "",
        }
    return {
        "available": True,
        "ok": bool(payload.get("ok")),
        "status": payload.get("status", ""),
        "selection_stratum": payload.get("selection_stratum", ""),
        "pending_rows_in_batch": payload.get("pending_rows_in_batch", 0),
        "rows_in_batch": payload.get("rows_in_batch", 0),
        "pending_model_assessments_in_batch": payload.get(
            "pending_model_assessments_in_batch",
            0,
        ),
        "model_assessments_in_batch": payload.get("model_assessments_in_batch", 0),
        "rows_missing_timing": payload.get("rows_missing_timing", 0),
        "latest_apply_status": payload.get("latest_apply_status", ""),
    }


def constants_match_validator(rows: list[dict[str, str]]) -> bool:
    by_category: dict[str, set[str]] = {}
    for row in rows:
        by_category.setdefault(row["category"], set()).add(row["value"])
    return (
        by_category.get("row_risk_label") == validation.VALID_LABELS
        and by_category.get("decision_change") == validation.VALID_DECISION_CHANGE
        and by_category.get("safe_action") == validation.VALID_SAFE_ACTION
        and by_category.get("confidence") == validation.VALID_CONFIDENCE
        and by_category.get("risk_atom") == validation.VALID_ATOMS
    )


def build_rubric(
    *,
    run_dir: Path,
    action_checklist_summary: Path,
    repo_root: Path,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    started = time.time()
    rows = value_rows()
    constants_match = constants_match_validator(rows)
    current_gate = current_gate_from_action_checklist(action_checklist_summary)
    status = "rubric_ready" if constants_match else "rubric_invalid"
    payload = {
        "ok": constants_match,
        "status": status,
        "input_boundary": "validator constants plus aggregate reviewer action status only",
        "output_boundary": "repo-safe reviewer value contract; no row keys or transcript text",
        "reference_transcript_policy": REFERENCE_TRANSCRIPT_POLICY,
        "remaining_review_scope": REMAINING_REVIEW_SCOPE,
        "validator_constants_match": constants_match,
        "value_category_counts": {
            "row_risk_label": len(validation.VALID_LABELS),
            "decision_change": len(validation.VALID_DECISION_CHANGE),
            "safe_action": len(validation.VALID_SAFE_ACTION),
            "confidence": len(validation.VALID_CONFIDENCE),
            "risk_atom": len(validation.VALID_ATOMS),
        },
        "required_review_surface": {
            "row_level_required_decision_fields": 8,
            "model_level_required_decision_fields": 4,
            "required_timing_fields": 3,
        },
        "current_reviewer_action_gate": current_gate,
        "consistency_checks": [
            {
                "check": "no_duplicate_transcript_review",
                "rule": "Reference transcripts are accepted for scoring; only record a correction exception if future evidence requires it.",
            },
            {
                "check": "decision_yes_requires_safe_action",
                "rule": "A decision-change yes label should map to a non-none safe action.",
            },
            {
                "check": "decision_yes_requires_critical_atom",
                "rule": "A decision-change yes label should include at least one critical semantic atom.",
            },
            {
                "check": "critical_atoms_are_subset_of_risk_atoms",
                "rule": "Row-level and model-level critical atoms should be present in the row risk-atom set.",
            },
            {
                "check": "strict_closeout_requires_review_timing",
                "rule": "Each selected audio row must have review_started_at/review_finished_at or review_elapsed_seconds before strict response closeout.",
            },
            {
                "check": "uncertain_requires_low_or_medium_certainty",
                "rule": "Uncertain decision effects should avoid high confidence unless a second reviewer resolves the ambiguity.",
            },
            {
                "check": "model_level_complete_for_comparison",
                "rule": "Each ASR run in the packet needs model-level decision-change, critical-atom, safe-action, and confidence labels.",
            },
            {
                "check": "do_not_rank_by_cer_only",
                "rule": "Do not reward a lower CER model if it drops a decision-critical semantic atom.",
            },
        ],
        "first_principle_decision": (
            "Reviewer time should convert proxy CDS-ASR evidence into decision-grade "
            "human evidence; it should not duplicate transcript review or chase more ASR runs."
        ),
        "next_action": (
            "Use this value contract while filling the ignored local response TSV, then "
            "run strict response dry-run until response_complete."
        ),
        "tracked_outputs": {
            "rubric_summary": repo_relative(run_dir / RUBRIC_SUMMARY_NAME, repo_root=repo_root),
            "value_contract_tsv": repo_relative(
                run_dir / VALUE_CONTRACT_TSV_NAME,
                repo_root=repo_root,
            ),
        },
        "runtime_seconds": round(time.time() - started, 4),
    }
    assert_tracked_safe(payload)
    assert_tracked_safe(rows)
    return payload, rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--action-checklist-summary", type=Path)
    parser.add_argument("--summary-json", type=Path)
    parser.add_argument("--output-tsv", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    action_checklist_summary = (
        args.action_checklist_summary or args.run_dir / CHECKLIST_SUMMARY_NAME
    )
    summary_json = args.summary_json or args.run_dir / RUBRIC_SUMMARY_NAME
    output_tsv = args.output_tsv or args.run_dir / VALUE_CONTRACT_TSV_NAME
    payload, rows = build_rubric(
        run_dir=args.run_dir,
        action_checklist_summary=action_checklist_summary,
        repo_root=REPO_ROOT,
    )
    write_json(summary_json, payload)
    write_tsv(output_tsv, rows)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Refresh aggregate evidence after local human audit review.

The audit sheet is intentionally local-only and may contain transcripts. This
orchestrator writes only aggregate outputs that are safe to track.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
ANNOTATION_DIR = SCRIPT_PATH.parent
REPO_ROOT = SCRIPT_PATH.parents[2]
SCORING_DIR = REPO_ROOT / "80_semantic_risk_asr" / "scoring"
RECOVERY_DIR = REPO_ROOT / "80_semantic_risk_asr" / "recovery"
for import_path in (ANNOTATION_DIR, SCORING_DIR, RECOVERY_DIR):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

import analyze_human_audit_predictors as predictors  # noqa: E402
import audit_evidence_chain_consistency as consistency_audit  # noqa: E402
import audit_postdoc_objective_requirements as objective_audit  # noqa: E402
import audit_postdoc_roadmap_completion as roadmap_audit  # noqa: E402
import audit_publishable_evidence_chain as completion_audit  # noqa: E402
import audit_human_review_progress as progress_audit  # noqa: E402
import build_human_audit_review_work_order as review_work_order  # noqa: E402
import check_evidence_chain_readiness as readiness  # noqa: E402
import evaluate_human_reviewed_recovery_policies as human_recovery  # noqa: E402
import run_post_review_evidence_sequence as post_review_sequence  # noqa: E402
import summarize_human_risk_atom_audit as review_summary  # noqa: E402
import validate_human_risk_atom_audit as validation  # noqa: E402


DEFAULT_AUDIT_RUN_DIR = (
    REPO_ROOT
    / "70_experiments"
    / "runs"
    / "janus_300_high_stakes_human_audit_selection_2026_05_25"
)
DEFAULT_AUDIT_SHEET = DEFAULT_AUDIT_RUN_DIR / "artifacts" / "human_risk_atom_audit_sheet.tsv"
DEFAULT_READINESS_DIR = (
    REPO_ROOT
    / "70_experiments"
    / "runs"
    / "postdoc_evidence_chain_2026_05_25"
)
REFRESH_SUMMARY_NAME = "human_audit_refresh_summary.json"
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
REFERENCE_TRANSCRIPT_POLICY = (
    "Reference transcripts are treated as already human-reviewed ground truth "
    "for WER/CER scoring; do not route duplicate transcript review unless "
    "future review fields or content differ from the accepted ground-truth "
    "transcript fields."
)
REMAINING_REVIEW_SCOPE = (
    "Remaining selected-300 review work is limited to risk-atom labels, "
    "decision-change labels, expected safe action, confidence, per-model "
    "assessment fields, and per-row review timing."
)


def repo_relative(path: Path, *, repo_root: Path = REPO_ROOT) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(repo_root.resolve()))
    except ValueError:
        return str(resolved)


def assert_refresh_safe(payload: dict[str, Any]) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    for token in SENSITIVE_TOKENS:
        if token in text:
            raise ValueError(f"sensitive token leaked into refresh summary: {token}")


def write_refresh_summary(output_dir: Path, payload: dict[str, Any]) -> Path:
    assert_refresh_safe(payload)
    path = output_dir / REFRESH_SUMMARY_NAME
    validation.write_json(path, payload)
    return path


def run_validation_gate(
    *,
    audit_sheet: Path,
    output_dir: Path,
    expected_rows: int | None,
    require_complete: bool,
) -> tuple[dict[str, Any], list[Path]]:
    started = time.time()
    fieldnames, rows = validation.read_tsv(audit_sheet)
    payload = validation.validate_rows(
        fieldnames,
        rows,
        require_complete=require_complete,
        expected_rows=expected_rows,
    )
    payload["input_boundary"] = "local transcript-bearing audit sheet; do not commit input"
    payload["output_boundary"] = "aggregate-only validation counts"
    payload["runtime_seconds"] = round(time.time() - started, 4)
    validation.assert_aggregate_safe(payload)

    output_json = output_dir / "human_audit_validation_summary.json"
    counts_tsv = output_dir / "human_audit_validation_counts.tsv"
    validation.write_json(output_json, payload)
    validation.write_tsv(
        counts_tsv,
        validation.validation_count_rows(payload),
        ["severity", "check", "count"],
    )
    return payload, [output_json, counts_tsv]


def run_review_summary_gate(
    *,
    audit_sheet: Path,
    output_dir: Path,
) -> tuple[dict[str, Any], list[Path]]:
    started = time.time()
    rows = review_summary.read_tsv(audit_sheet)
    completion = review_summary.summarize_completion(rows)
    stratum_rows = review_summary.summarize_selection(rows)
    atom_rows = review_summary.summarize_human_atoms(rows)
    model_rows = review_summary.summarize_model_proxy_coverage(rows)

    payload = {
        "ok": True,
        "input_boundary": "local transcript-bearing audit sheet; do not commit input",
        "output_boundary": "aggregate-only; no audio IDs, sample IDs, transcripts, hypotheses, or reviewer notes",
        **completion,
        "label_counts": review_summary.summarize_labels(rows),
        "wall_time_seconds": round(time.time() - started, 4),
    }
    review_summary.assert_aggregate_safe(payload, stratum_rows + atom_rows + model_rows)

    output_json = output_dir / "human_audit_review_summary.json"
    strata_tsv = output_dir / "human_audit_strata_review.tsv"
    atoms_tsv = output_dir / "human_audit_risk_atom_review.tsv"
    model_tsv = output_dir / "human_audit_model_review.tsv"
    review_summary.write_json(output_json, payload)
    review_summary.write_tsv(
        strata_tsv,
        stratum_rows,
        [
            "selection_stratum",
            "audit_rows",
            "reviewed_rows",
            "decision_change_yes_count",
            "decision_change_uncertain_count",
            "confidence_low_count",
        ],
    )
    review_summary.write_tsv(
        atoms_tsv,
        atom_rows,
        [
            "risk_atom_type",
            "reviewed_row_count",
            "critical_atom_row_count",
            "decision_change_yes_count",
        ],
    )
    review_summary.write_tsv(
        model_tsv,
        model_rows,
        [
            "asr_run_id",
            "audit_model_samples",
            "model_assessments",
            "reviewed_model_samples",
            "pending_model_samples",
            "human_decision_change_yes_rows",
            "human_decision_change_uncertain_rows",
        ],
    )
    return payload, [output_json, strata_tsv, atoms_tsv, model_tsv]


def run_progress_gate(
    *,
    audit_sheet: Path,
    output_dir: Path,
    expected_rows: int | None,
) -> tuple[dict[str, Any], list[Path]]:
    started = time.time()
    fieldnames, rows = progress_audit.read_tsv(audit_sheet)
    progress = progress_audit.build_progress(fieldnames, rows, expected_rows)
    summary = progress["summary"]
    summary["runtime_seconds"] = round(time.time() - started, 4)
    progress_audit.assert_progress_safe(
        summary,
        progress["strata"] + progress["models"] + progress["batches"],
    )

    output_json = output_dir / progress_audit.SUMMARY_NAME
    strata_tsv = output_dir / progress_audit.STRATA_NAME
    model_tsv = output_dir / progress_audit.MODEL_NAME
    batches_tsv = output_dir / progress_audit.RECOMMENDED_BATCH_NAME
    progress_audit.write_json(output_json, summary)
    progress_audit.write_tsv(
        strata_tsv,
        progress["strata"],
        [
            "selection_stratum",
            "audit_rows",
            "reviewed_rows",
            "pending_rows",
            "row_completion_rate",
            "model_assessments",
            "reviewed_model_assessments",
            "pending_model_assessments",
            "model_completion_rate",
        ],
    )
    progress_audit.write_tsv(
        model_tsv,
        progress["models"],
        [
            "asr_run_id",
            "model_assessments",
            "reviewed_model_assessments",
            "pending_model_assessments",
            "model_completion_rate",
        ],
    )
    progress_audit.write_tsv(
        batches_tsv,
        progress["batches"],
        [
            "batch_order",
            "selection_stratum",
            "pending_rows",
            "pending_model_assessments",
            "primary_reason",
            "completion_gate",
        ],
    )
    return summary, [output_json, strata_tsv, model_tsv, batches_tsv]


def run_predictor_gate(
    *,
    audit_sheet: Path,
    output_dir: Path,
) -> tuple[dict[str, Any], list[Path]]:
    started = time.time()
    audit_rows = predictors.read_tsv(audit_sheet)
    model_rows, counters = predictors.extract_model_rows(audit_rows)
    comparison = predictors.predictor_rows(model_rows)
    model_summary = predictors.model_summary_rows(model_rows)

    status = "review_complete" if counters["pending_model_assessments"] == 0 else "review_pending"
    if counters["reviewed_model_assessments"] and counters["pending_model_assessments"]:
        status = "partial_review"
    if counters["invalid_decision_change_value"]:
        status = "review_needs_cleanup"

    payload = {
        "ok": True,
        "status": status,
        "input_boundary": "local transcript-bearing audit sheet; do not commit input",
        "output_boundary": "aggregate-only; no audio IDs, sample IDs, transcripts, hypotheses, or reviewer notes",
        "audit_rows": len(audit_rows),
        "model_assessments": counters["model_assessments"],
        "reviewed_model_assessments": counters["reviewed_model_assessments"],
        "pending_model_assessments": counters["pending_model_assessments"],
        "warning_counts": {
            key: value
            for key, value in sorted(counters.items())
            if key
            not in {
                "model_assessments",
                "reviewed_model_assessments",
                "pending_model_assessments",
            }
            and value
        },
        "notes": [
            "Predictor metrics are computed only over reviewed model-level assessments.",
            "Uncertain decisions are excluded from the yes-only target and included in the yes-or-uncertain target.",
        ],
        "wall_time_seconds": round(time.time() - started, 4),
    }
    predictors.assert_aggregate_safe(payload, comparison + model_summary)

    output_json = output_dir / "human_audit_predictor_summary.json"
    comparison_tsv = output_dir / "human_audit_predictor_comparison.tsv"
    model_tsv = output_dir / "human_audit_predictor_model_summary.tsv"
    predictors.write_json(output_json, payload)
    predictors.write_tsv(
        comparison_tsv,
        comparison,
        [
            "scope",
            "asr_run_id",
            "target",
            "metric",
            "reviewed_model_samples",
            "positive_rows",
            "positive_rate",
            "auc",
            "best_threshold",
            "best_f1",
            "precision",
            "recall",
            "true_positive",
            "false_positive",
            "false_negative",
        ],
    )
    predictors.write_tsv(
        model_tsv,
        model_summary,
        [
            "asr_run_id",
            "model_assessments",
            "reviewed_model_assessments",
            "pending_model_assessments",
            "human_decision_change_yes_count",
            "human_decision_change_yes_or_uncertain_count",
            "human_uncertain_count",
        ],
    )
    return payload, [output_json, comparison_tsv, model_tsv]


def run_readiness_gate(
    *,
    repo_root: Path,
    output_dir: Path,
) -> tuple[dict[str, Any], list[Path]]:
    started = time.time()
    payload = readiness.build_readiness(repo_root.resolve())
    payload["runtime_seconds"] = round(time.time() - started, 4)
    output_json = output_dir / "evidence_chain_readiness_summary.json"
    output_tsv = output_dir / "evidence_chain_readiness.tsv"
    readiness.write_json(output_json, payload)
    readiness.write_tsv(output_tsv, payload["readiness_rows"])
    return payload, [output_json, output_tsv]


def run_completion_audit_gate(
    *,
    readiness_payload: dict[str, Any],
    human_refresh_payload: dict[str, Any],
    predictor_payload: dict[str, Any],
    output_dir: Path,
) -> tuple[dict[str, Any], list[Path]]:
    started = time.time()
    consequence_matrix = completion_audit.read_json(
        output_dir / completion_audit.CONSEQUENCE_SUMMARY_NAME
    )
    payload = completion_audit.build_completion_audit_from_payloads(
        readiness_payload=readiness_payload,
        human_refresh=human_refresh_payload,
        human_predictor=predictor_payload,
        consequence_matrix=consequence_matrix,
        reviewer_action_gate=readiness_payload.get("reviewer_action_gate", {}),
    )
    payload["runtime_seconds"] = round(time.time() - started, 4)
    output_json = output_dir / completion_audit.SUMMARY_NAME
    output_tsv = output_dir / completion_audit.TSV_NAME
    completion_audit.write_json(output_json, payload)
    completion_audit.write_tsv(output_tsv, payload["completion_rows"])
    return payload, [output_json, output_tsv]


def run_roadmap_audit_gate(
    *,
    repo_root: Path,
    output_dir: Path,
    audit_output_dir: Path,
    readiness_payload: dict[str, Any],
    completion_payload: dict[str, Any],
    human_refresh_payload: dict[str, Any],
    predictor_payload: dict[str, Any],
) -> tuple[dict[str, Any], list[Path]]:
    started = time.time()
    payload = roadmap_audit.build_roadmap_audit_from_payloads(
        readiness=readiness_payload,
        completion=completion_payload,
        consequence=roadmap_audit.read_json(
            output_dir / "consequence_evidence_matrix_summary.json"
        ),
        post_review=roadmap_audit.read_json(
            audit_output_dir / "human_audit_post_review_evidence_summary.json"
        ),
        human_refresh=human_refresh_payload,
        human_predictor=predictor_payload,
        response_closeout=roadmap_audit.read_json(
            audit_output_dir / "human_audit_response_closeout_summary.json"
        ),
        candidate_summary=roadmap_audit.read_json(
            repo_root
            / "70_experiments"
            / "runs"
            / "asr_candidate_15_row_extension_2026_05_26"
            / "summary.json"
        ),
    )
    payload["runtime_seconds"] = round(time.time() - started, 4)
    output_json = output_dir / roadmap_audit.SUMMARY_NAME
    output_tsv = output_dir / roadmap_audit.TSV_NAME
    roadmap_audit.write_json(output_json, payload)
    roadmap_audit.write_tsv(output_tsv, payload["roadmap_rows"])
    return payload, [output_json, output_tsv]


def run_post_review_evidence_gate(
    *,
    output_dir: Path,
    readiness_output_dir: Path,
    repo_root: Path,
) -> tuple[dict[str, Any], list[Path]]:
    import build_post_review_evidence_checklist as post_review_checklist

    payload, rows = post_review_checklist.build_post_review_checklist(
        run_dir=output_dir,
        readiness_dir=readiness_output_dir,
        closeout_summary_path=output_dir / post_review_checklist.CLOSEOUT_SUMMARY_NAME,
        refresh_summary_path=output_dir / post_review_checklist.REFRESH_SUMMARY_NAME,
        predictor_summary_path=output_dir / post_review_checklist.PREDICTOR_SUMMARY_NAME,
        readiness_summary_path=readiness_output_dir / post_review_checklist.READINESS_SUMMARY_NAME,
        publishable_summary_path=readiness_output_dir / post_review_checklist.PUBLISHABLE_SUMMARY_NAME,
        consequence_summary_path=readiness_output_dir / post_review_checklist.CONSEQUENCE_SUMMARY_NAME,
        recovery_summary_path=(
            repo_root
            / "70_experiments"
            / "runs"
            / "janus_300_high_stakes_recovery_proxy_2026_05_25"
            / "summary.json"
        ),
        human_recovery_summary_path=(
            repo_root
            / "70_experiments"
            / "runs"
            / "janus_300_high_stakes_recovery_human_reviewed_2026_05_26"
            / "summary.json"
        ),
        repo_root=repo_root,
    )
    output_json = output_dir / post_review_checklist.POST_REVIEW_SUMMARY_NAME
    output_tsv = output_dir / post_review_checklist.POST_REVIEW_TSV_NAME
    post_review_checklist.write_json(output_json, payload)
    post_review_checklist.write_tsv(output_tsv, rows)
    return payload, [output_json, output_tsv]


def run_human_reviewed_recovery_gate(
    *,
    audit_sheet: Path,
    repo_root: Path,
    expected_rows: int | None,
) -> tuple[dict[str, Any], list[Path]]:
    output_dir = (
        repo_root
        / "70_experiments"
        / "runs"
        / "janus_300_high_stakes_recovery_human_reviewed_2026_05_26"
    )
    summary_path = output_dir / "summary.json"
    comparison_path = output_dir / "policy_comparison.tsv"
    payload, _detail_rows, _exit_code = human_recovery.build_human_reviewed_recovery(
        audit_sheet=audit_sheet,
        expected_rows=expected_rows,
        allow_pending_summary=True,
        confidence_threshold=0.70,
        sres_threshold=20.0,
        ceis_threshold=5.0,
        ensemble_mode="priority",
    )
    human_recovery.write_json(summary_path, payload)
    outputs = [summary_path]
    if payload.get("policies"):
        human_recovery.write_tsv(
            comparison_path,
            human_recovery.comparison_rows(payload["policies"]),
            human_recovery.COMPARISON_FIELDS,
        )
        outputs.append(comparison_path)
    return payload, outputs


def run_review_work_order_gate(
    *,
    audit_sheet: Path,
    output_dir: Path,
    repo_root: Path,
) -> tuple[dict[str, Any], list[Path]]:
    started = time.time()
    payload, rows = review_work_order.build_work_order(
        run_dir=output_dir,
        action_items_tsv=output_dir / review_work_order.RESPONSE_ACTION_ITEMS_TSV_NAME,
        closeout_summary_path=output_dir / review_work_order.CLOSEOUT_SUMMARY_NAME,
        handoff_summary_path=output_dir / review_work_order.HANDOFF_SUMMARY_NAME,
        session_start_summary_path=output_dir / review_work_order.SESSION_START_SUMMARY_NAME,
        audit_sheet=audit_sheet,
        repo_root=repo_root,
    )
    payload["runtime_seconds"] = round(time.time() - started, 4)
    output_json = output_dir / review_work_order.WORK_ORDER_SUMMARY_NAME
    output_tsv = output_dir / review_work_order.WORK_ORDER_TSV_NAME
    review_work_order.write_json(output_json, payload)
    review_work_order.write_tsv(output_tsv, rows)
    return payload, [output_json, output_tsv]


def run_consistency_audit_gate(
    *,
    repo_root: Path,
    output_dir: Path,
) -> tuple[dict[str, Any], list[Path]]:
    started = time.time()
    payload = consistency_audit.build_consistency_audit(repo_root.resolve())
    payload["runtime_seconds"] = round(time.time() - started, 4)
    output_json = output_dir / consistency_audit.SUMMARY_NAME
    output_tsv = output_dir / consistency_audit.TSV_NAME
    consistency_audit.write_json(output_json, payload)
    consistency_audit.write_tsv(output_tsv, payload["consistency_rows"])
    return payload, [output_json, output_tsv]


def run_post_review_sequence_gate(
    *,
    output_dir: Path,
    readiness_output_dir: Path,
    repo_root: Path,
) -> tuple[dict[str, Any], list[Path]]:
    payload, rows = post_review_sequence.build_sequence(
        run_dir=output_dir,
        readiness_dir=readiness_output_dir,
        human_recovery_dir=post_review_sequence.DEFAULT_HUMAN_RECOVERY_DIR,
        closeout_summary_path=output_dir / post_review_sequence.CLOSEOUT_SUMMARY_NAME,
        refresh_summary_path=output_dir / post_review_sequence.REFRESH_SUMMARY_NAME,
        human_recovery_summary_path=(
            post_review_sequence.DEFAULT_HUMAN_RECOVERY_DIR
            / post_review_sequence.HUMAN_RECOVERY_SUMMARY_NAME
        ),
        post_review_summary_path=output_dir / post_review_sequence.POST_REVIEW_SUMMARY_NAME,
        objective_summary_path=readiness_output_dir / post_review_sequence.OBJECTIVE_SUMMARY_NAME,
        repo_root=repo_root,
        execute=False,
    )
    output_json = output_dir / post_review_sequence.SEQUENCE_SUMMARY_NAME
    output_tsv = output_dir / post_review_sequence.SEQUENCE_TSV_NAME
    post_review_sequence.write_json(output_json, payload)
    post_review_sequence.write_tsv(output_tsv, rows, post_review_sequence.SEQUENCE_TSV_FIELDS)
    return payload, [output_json, output_tsv]


def run_objective_requirements_gate(
    *,
    repo_root: Path,
    output_dir: Path,
) -> tuple[dict[str, Any], list[Path]]:
    payload = objective_audit.build_current_audit(repo_root.resolve())
    output_json = output_dir / objective_audit.SUMMARY_NAME
    output_tsv = output_dir / objective_audit.TSV_NAME
    objective_audit.write_json(output_json, payload)
    objective_audit.write_tsv(output_tsv, payload["requirement_rows"])
    return payload, [output_json, output_tsv]


def refresh_human_audit_evidence(
    *,
    audit_sheet: Path,
    output_dir: Path,
    readiness_output_dir: Path,
    repo_root: Path = REPO_ROOT,
    expected_rows: int | None = 30,
    require_complete: bool = False,
    skip_readiness: bool = False,
) -> dict[str, Any]:
    started = time.time()
    output_dir.mkdir(parents=True, exist_ok=True)
    readiness_output_dir.mkdir(parents=True, exist_ok=True)
    output_paths: list[Path] = []

    validation_payload, validation_outputs = run_validation_gate(
        audit_sheet=audit_sheet,
        output_dir=output_dir,
        expected_rows=expected_rows,
        require_complete=require_complete,
    )
    output_paths.extend(validation_outputs)
    progress_payload, progress_outputs = run_progress_gate(
        audit_sheet=audit_sheet,
        output_dir=output_dir,
        expected_rows=expected_rows,
    )
    output_paths.extend(progress_outputs)

    review_payload: dict[str, Any] | None = None
    predictor_payload: dict[str, Any] | None = None
    readiness_payload: dict[str, Any] | None = None
    completion_payload: dict[str, Any] | None = None
    roadmap_payload: dict[str, Any] | None = None
    post_review_payload: dict[str, Any] | None = None
    human_recovery_payload: dict[str, Any] | None = None
    work_order_payload: dict[str, Any] | None = None
    post_review_sequence_payload: dict[str, Any] | None = None
    consistency_payload: dict[str, Any] | None = None
    objective_payload: dict[str, Any] | None = None
    downstream_refreshed = False

    if validation_payload["ok"]:
        review_payload, review_outputs = run_review_summary_gate(
            audit_sheet=audit_sheet,
            output_dir=output_dir,
        )
        output_paths.extend(review_outputs)
        predictor_payload, predictor_outputs = run_predictor_gate(
            audit_sheet=audit_sheet,
            output_dir=output_dir,
        )
        output_paths.extend(predictor_outputs)
        downstream_refreshed = True
        if not skip_readiness:
            readiness_payload, readiness_outputs = run_readiness_gate(
                repo_root=repo_root,
                output_dir=readiness_output_dir,
            )
            output_paths.extend(readiness_outputs)

    strict_complete = (
        validation_payload["ok"]
        and validation_payload["status"] == "review_complete"
        and validation_payload["pending_rows"] == 0
        and validation_payload["pending_model_assessments"] == 0
    )
    ok = bool(validation_payload["ok"]) and (not require_complete or strict_complete)
    if readiness_payload is not None:
        ok = ok and bool(readiness_payload.get("ok"))

    payload = {
        "ok": ok,
        "status": validation_payload["status"],
        "require_complete": require_complete,
        "input_boundary": "local ignored audit sheet only; no private row content is emitted",
        "output_boundary": "aggregate tracked outputs only",
        "reference_transcript_policy": REFERENCE_TRANSCRIPT_POLICY,
        "remaining_review_scope": REMAINING_REVIEW_SCOPE,
        "audit_rows": validation_payload["audit_rows"],
        "reviewed_rows": validation_payload["reviewed_rows"],
        "pending_rows": validation_payload["pending_rows"],
        "model_assessments": validation_payload["model_assessments"],
        "reviewed_model_assessments": validation_payload["reviewed_model_assessments"],
        "pending_model_assessments": validation_payload["pending_model_assessments"],
        "validation_ok": validation_payload["ok"],
        "validation_error_counts": validation_payload["error_counts"],
        "validation_warning_counts": validation_payload["warning_counts"],
        "review_summary_status": review_payload.get("status") if review_payload else "",
        "progress_status": progress_payload.get("status"),
        "recommended_review_batch_count": progress_payload.get("recommended_batch_count"),
        "predictor_status": predictor_payload.get("status") if predictor_payload else "",
        "readiness_ok": readiness_payload.get("ok") if readiness_payload else "",
        "readiness_paper_ready": readiness_payload.get("paper_ready") if readiness_payload else "",
        "readiness_status_counts": readiness_payload.get("status_counts") if readiness_payload else {},
        "completion_audit_ok": "",
        "publishable_ready": "",
        "completion_status_counts": {},
        "roadmap_audit_ok": "",
        "roadmap_complete": "",
        "roadmap_status_counts": {},
        "post_review_evidence_ok": "",
        "post_review_evidence_status": "",
        "post_review_blocker_keys": [],
        "human_recovery_status": "",
        "human_recovery_evidence_mode": "",
        "human_recovery_ready": "",
        "review_work_order_status": "",
        "review_work_order_overview": {},
        "post_review_sequence_status": "",
        "post_review_sequence_blocker_keys": [],
        "post_review_sequence_executed_step_count": "",
        "consistency_audit_ok": "",
        "consistency_status_counts": {},
        "consistency_failed_checks": [],
        "objective_requirements_audit_ok": "",
        "objective_requirements_ready": "",
        "objective_requirements_status_counts": {},
        "objective_requirements_proxy_count": "",
        "objective_requirements_blocking_count": "",
        "downstream_outputs_refreshed": downstream_refreshed,
        "outputs": [repo_relative(path, repo_root=repo_root) for path in output_paths],
        "runtime_seconds": round(time.time() - started, 4),
        "next_action": (
            "Complete selected-300 risk-atom, decision-change, expected-action, "
            "confidence, per-model assessment, and per-row timing fields, then "
            "rerun the session-gated strict dry-run with --require-complete "
            "--require-timing before aggregate refresh."
            if not strict_complete
            else "Use refreshed aggregate summaries for paper-table drafting and human-reviewed predictor analysis."
        ),
    }
    if readiness_payload is not None and predictor_payload is not None:
        completion_payload, completion_outputs = run_completion_audit_gate(
            readiness_payload=readiness_payload,
            human_refresh_payload=payload,
            predictor_payload=predictor_payload,
            output_dir=readiness_output_dir,
        )
        output_paths.extend(completion_outputs)
        ok = ok and bool(completion_payload.get("ok"))
        payload["ok"] = ok
        payload["completion_audit_ok"] = completion_payload.get("ok")
        payload["publishable_ready"] = completion_payload.get("publishable_ready")
        payload["completion_status_counts"] = completion_payload.get("status_counts", {})
        roadmap_payload, roadmap_outputs = run_roadmap_audit_gate(
            repo_root=repo_root,
            output_dir=readiness_output_dir,
            audit_output_dir=output_dir,
            readiness_payload=readiness_payload,
            completion_payload=completion_payload,
            human_refresh_payload=payload,
            predictor_payload=predictor_payload,
        )
        output_paths.extend(roadmap_outputs)
        ok = ok and bool(roadmap_payload.get("ok"))
        payload["ok"] = ok
        payload["roadmap_audit_ok"] = roadmap_payload.get("ok")
        payload["roadmap_complete"] = roadmap_payload.get("roadmap_complete")
        payload["roadmap_status_counts"] = roadmap_payload.get("status_counts", {})
        payload["outputs"] = [repo_relative(path, repo_root=repo_root) for path in output_paths]
    summary_path = output_dir / REFRESH_SUMMARY_NAME
    payload["outputs"].append(repo_relative(summary_path, repo_root=repo_root))
    write_refresh_summary(output_dir, payload)
    if readiness_payload is not None and predictor_payload is not None:
        human_recovery_payload, human_recovery_outputs = run_human_reviewed_recovery_gate(
            audit_sheet=audit_sheet,
            repo_root=repo_root,
            expected_rows=expected_rows,
        )
        output_paths.extend(human_recovery_outputs)
        payload["human_recovery_status"] = human_recovery_payload.get("status", "")
        payload["human_recovery_evidence_mode"] = human_recovery_payload.get(
            "evidence_mode",
            "",
        )
        payload["human_recovery_ready"] = bool(human_recovery_payload.get("human_reviewed"))
        payload["outputs"] = [repo_relative(path, repo_root=repo_root) for path in output_paths]
        payload["outputs"].append(repo_relative(summary_path, repo_root=repo_root))
        write_refresh_summary(output_dir, payload)
        post_review_payload, post_review_outputs = run_post_review_evidence_gate(
            output_dir=output_dir,
            readiness_output_dir=readiness_output_dir,
            repo_root=repo_root,
        )
        output_paths.extend(post_review_outputs)
        payload["post_review_evidence_ok"] = post_review_payload.get("ok")
        payload["post_review_evidence_status"] = post_review_payload.get("status")
        payload["post_review_blocker_keys"] = post_review_payload.get("blocker_keys", [])
        payload["outputs"] = [repo_relative(path, repo_root=repo_root) for path in output_paths]
        payload["outputs"].append(repo_relative(summary_path, repo_root=repo_root))
        write_refresh_summary(output_dir, payload)
        work_order_payload, work_order_outputs = run_review_work_order_gate(
            audit_sheet=audit_sheet,
            output_dir=output_dir,
            repo_root=repo_root,
        )
        output_paths.extend(work_order_outputs)
        payload["review_work_order_status"] = work_order_payload.get("status", "")
        payload["review_work_order_overview"] = work_order_payload.get(
            "review_work_order_overview",
            {},
        )
        payload["outputs"] = [repo_relative(path, repo_root=repo_root) for path in output_paths]
        payload["outputs"].append(repo_relative(summary_path, repo_root=repo_root))
        write_refresh_summary(output_dir, payload)
        objective_payload, objective_outputs = run_objective_requirements_gate(
            repo_root=repo_root,
            output_dir=readiness_output_dir,
        )
        output_paths.extend(objective_outputs)
        ok = ok and bool(objective_payload.get("ok"))
        payload["ok"] = ok
        payload["objective_requirements_audit_ok"] = objective_payload.get("ok")
        payload["objective_requirements_ready"] = objective_payload.get(
            "objective_requirements_ready"
        )
        payload["objective_requirements_status_counts"] = objective_payload.get(
            "status_counts",
            {},
        )
        payload["objective_requirements_proxy_count"] = objective_payload.get(
            "proxy_requirement_count",
            "",
        )
        payload["objective_requirements_blocking_count"] = objective_payload.get(
            "blocking_requirement_count",
            "",
        )
        payload["outputs"] = [repo_relative(path, repo_root=repo_root) for path in output_paths]
        payload["outputs"].append(repo_relative(summary_path, repo_root=repo_root))
        write_refresh_summary(output_dir, payload)
        post_review_sequence_payload, sequence_outputs = run_post_review_sequence_gate(
            output_dir=output_dir,
            readiness_output_dir=readiness_output_dir,
            repo_root=repo_root,
        )
        output_paths.extend(sequence_outputs)
        payload["post_review_sequence_status"] = post_review_sequence_payload.get("status", "")
        payload["post_review_sequence_blocker_keys"] = post_review_sequence_payload.get(
            "blocker_keys",
            [],
        )
        payload["post_review_sequence_executed_step_count"] = post_review_sequence_payload.get(
            "executed_step_count",
            "",
        )
        payload["outputs"] = [repo_relative(path, repo_root=repo_root) for path in output_paths]
        payload["outputs"].append(repo_relative(summary_path, repo_root=repo_root))
        write_refresh_summary(output_dir, payload)
        consistency_payload, consistency_outputs = run_consistency_audit_gate(
            repo_root=repo_root,
            output_dir=readiness_output_dir,
        )
        output_paths.extend(consistency_outputs)
        payload["consistency_audit_ok"] = consistency_payload.get("ok")
        payload["consistency_status_counts"] = consistency_payload.get("status_counts", {})
        payload["consistency_failed_checks"] = consistency_payload.get("failed_checks", [])
        payload["outputs"] = [repo_relative(path, repo_root=repo_root) for path in output_paths]
        payload["outputs"].append(repo_relative(summary_path, repo_root=repo_root))
        write_refresh_summary(output_dir, payload)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-sheet", type=Path, default=DEFAULT_AUDIT_SHEET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_AUDIT_RUN_DIR)
    parser.add_argument("--readiness-output-dir", type=Path, default=DEFAULT_READINESS_DIR)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--expected-rows", type=int, default=30)
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument(
        "--skip-readiness",
        action="store_true",
        help="Refresh local audit aggregates without rewriting evidence-chain readiness outputs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = refresh_human_audit_evidence(
        audit_sheet=args.audit_sheet,
        output_dir=args.output_dir,
        readiness_output_dir=args.readiness_output_dir,
        repo_root=args.repo_root,
        expected_rows=args.expected_rows,
        require_complete=args.require_complete,
        skip_readiness=args.skip_readiness,
    )
    print(
        json.dumps(
            {
                "ok": payload["ok"],
                "status": payload["status"],
                "reviewed_rows": payload["reviewed_rows"],
                "pending_rows": payload["pending_rows"],
                "reviewed_model_assessments": payload["reviewed_model_assessments"],
                "pending_model_assessments": payload["pending_model_assessments"],
                "readiness_paper_ready": payload["readiness_paper_ready"],
                "objective_requirements_ready": payload["objective_requirements_ready"],
                "output_summary": str(args.output_dir / REFRESH_SUMMARY_NAME),
            },
            ensure_ascii=False,
        )
    )
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

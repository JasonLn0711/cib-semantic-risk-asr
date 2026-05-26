#!/usr/bin/env python3
"""Audit the user-facing 0-6 postdoc objective against current evidence.

This audit is stricter than the roadmap summary: it checks named artifacts,
required model families, required aggregate columns, and recovery conditions.
It still keeps transcript-bearing and prediction-level content out of tracked
outputs.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = (
    REPO_ROOT / "70_experiments" / "runs" / "postdoc_evidence_chain_2026_05_25"
)
SUMMARY_NAME = "postdoc_objective_requirements_summary.json"
TSV_NAME = "postdoc_objective_requirements.tsv"

REFERENCE_TRANSCRIPT_POLICY = (
    "Reference transcripts are already human-reviewed for WER/CER scoring; "
    "this audit does not reopen transcript review."
)
REMAINING_REVIEW_SCOPE = (
    "Selected-300 completion still requires risk, decision, expected safe "
    "action, confidence, per-model fields, and per-row review timing."
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

STATUS_ORDER = {
    "satisfied": 0,
    "proxy_satisfied": 1,
    "review_pending": 2,
    "blocked": 3,
    "missing": 4,
    "failed": 5,
}

TSV_FIELDS = [
    "requirement_id",
    "objective_step",
    "requirement",
    "status",
    "paper_claim_status",
    "evidence",
    "result",
    "blocking_dependency",
    "next_action",
]

REQUIRED_258_RUNS = {
    "whisper_small_test_split",
    "whisper_large_v2_test_split",
    "breeze_asr25_base_test_split",
    "breeze_asr25_lora_legacy_best_test_split",
    "breeze_asr25_partial_encoder_legacy_best_test_split",
    "breeze_asr26_test_split",
}
REQUIRED_258_COLUMNS = {
    "run_id",
    "rows",
    "expected_rows",
    "cer_zh_micro",
    "wer_zh_jieba_micro",
    "risk_atom_error_rate",
    "negation_flip_rate",
    "amount_distortion_rate",
    "action_confusion_rate",
    "unsafe_downrouting_count",
    "high_risk_missed_count",
}
REQUIRED_RECOVERY_POLICIES = {
    "no_recovery",
    "confidence_only_trigger",
    "sres_triggered_recovery",
    "ceis_triggered_conservative_action",
    "ceis_ensemble_arbitration",
}
REQUIRED_RECOVERY_METRICS = {
    "critical_miss_count",
    "critical_miss_rate",
    "unsafe_downrouting_count",
    "unsafe_downrouting_rate",
    "over_escalation_count",
    "over_escalation_rate",
    "machine_abstention_count",
    "machine_abstention_rate",
    "recovery_budget_rate",
    "high_risk_missed_gain",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TSV_FIELDS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in TSV_FIELDS})


def assert_requirement_audit_safe(payload: Any) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    for token in SENSITIVE_TOKENS:
        if token in text:
            raise ValueError(f"sensitive token leaked into objective audit: {token}")


def requirement_row(
    *,
    requirement_id: str,
    objective_step: str,
    requirement: str,
    status: str,
    paper_claim_status: str,
    evidence: str,
    result: str,
    blocking_dependency: str = "",
    next_action: str = "",
) -> dict[str, str]:
    return {
        "requirement_id": requirement_id,
        "objective_step": objective_step,
        "requirement": requirement,
        "status": status,
        "paper_claim_status": paper_claim_status,
        "evidence": evidence,
        "result": result,
        "blocking_dependency": blocking_dependency,
        "next_action": next_action,
    }


def registry_ids(rows: list[dict[str, str]]) -> set[str]:
    return {row.get("run_id", "") for row in rows}


def has_gitignore_patterns(text: str) -> bool:
    required = (
        "*.wav",
        "*.safetensors",
        "50_janus_data_library/",
        "90_legacy_imports/",
        "70_experiments/runs/*/artifacts/",
        "70_experiments/runs/*/predictions/",
        "70_experiments/runs/*/models/",
    )
    return all(item in text for item in required)


def smoke_ok(payload: dict[str, Any], model_kind: str) -> bool:
    return (
        bool(payload.get("ok"))
        and payload.get("model_kind") == model_kind
        and int(payload.get("rows") or 0) >= 1
        and bool(payload.get("runtime"))
        and bool(payload.get("torch_dtype"))
        and payload.get("disable_cudnn") is True
        and float(payload.get("wall_time_seconds") or 0) > 0
    )


def validation_ok(payload: dict[str, Any]) -> bool:
    if not payload.get("ok"):
        return False
    files = payload.get("files")
    if not isinstance(files, list) or len(files) != 1:
        return False
    first = files[0]
    checks = first.get("checks") if isinstance(first.get("checks"), dict) else {}
    counts = first.get("counts") if isinstance(first.get("counts"), dict) else {}
    return (
        first.get("ok") is True
        and int(counts.get("rows") or 0) == 15
        and int(counts.get("expected_ids") or 0) == 15
        and all(bool(checks.get(key)) for key in (
            "row_count_matches_expected_ids",
            "audio_ids_match_expected_set",
            "audio_ids_are_unique",
            "audio_id_field_present",
            "hypothesis_text_present",
            "asr_label_present",
            "quality_signal_present",
        ))
    )


def fields_present(rows: list[dict[str, str]], required: set[str]) -> bool:
    if not rows:
        return False
    return required.issubset(set(rows[0].keys()))


def split_258_complete(rows: list[dict[str, str]]) -> tuple[bool, str]:
    observed = {row.get("run_id", "") for row in rows}
    missing_runs = sorted(REQUIRED_258_RUNS - observed)
    missing_columns = sorted(REQUIRED_258_COLUMNS - set(rows[0].keys())) if rows else sorted(REQUIRED_258_COLUMNS)
    row_counts_ok = all(int(row.get("rows") or 0) == 258 for row in rows if row.get("run_id") in REQUIRED_258_RUNS)
    ids_ok = not missing_runs and not missing_columns and row_counts_ok
    result = (
        f"{len(observed & REQUIRED_258_RUNS)}/6 required runs present; "
        f"missing_runs={missing_runs}; missing_columns={missing_columns}; "
        f"row_counts_ok={row_counts_ok}"
    )
    return ids_ok, result


def recovery_policy_complete(summary: dict[str, Any]) -> tuple[bool, str]:
    policies = summary.get("policies") if isinstance(summary.get("policies"), dict) else {}
    missing_policies = sorted(REQUIRED_RECOVERY_POLICIES - set(policies.keys()))
    missing_metrics: dict[str, list[str]] = {}
    for policy in REQUIRED_RECOVERY_POLICIES & set(policies.keys()):
        metric_missing = sorted(REQUIRED_RECOVERY_METRICS - set(policies.get(policy, {}).keys()))
        if metric_missing:
            missing_metrics[policy] = metric_missing
    ok = bool(summary.get("ok")) and not missing_policies and not missing_metrics
    result = (
        f"{len(REQUIRED_RECOVERY_POLICIES) - len(missing_policies)}/5 policies present; "
        f"missing_policies={missing_policies}; missing_metrics={missing_metrics}"
    )
    return ok, result


def recovery_reduces_proxy_risk(summary: dict[str, Any]) -> tuple[bool, str]:
    policies = summary.get("policies") if isinstance(summary.get("policies"), dict) else {}
    no_recovery = policies.get("no_recovery", {})
    ceis = policies.get("ceis_triggered_conservative_action", {})
    if not no_recovery or not ceis:
        return False, "required no-recovery and CEIS policies are missing"
    unsafe_gain = float(ceis.get("unsafe_downrouting_gain") or 0)
    high_risk_gain = float(ceis.get("high_risk_missed_gain") or 0)
    critical_before = int(no_recovery.get("critical_miss_count") or 0)
    critical_after = int(ceis.get("critical_miss_count") or 0)
    ok = unsafe_gain > 0 and high_risk_gain > 0 and critical_after < critical_before
    result = (
        f"unsafe_gain={unsafe_gain}; high_risk_gain={high_risk_gain}; "
        f"critical_miss={critical_before}->{critical_after}"
    )
    return ok, result


def human_recovery_complete(summary: dict[str, Any]) -> bool:
    ok, _ = recovery_policy_complete(summary)
    gain_ok, _ = recovery_reduces_proxy_risk(summary)
    return (
        ok
        and gain_ok
        and summary.get("human_reviewed") is True
        and summary.get("review_status") == "human_reviewed_complete"
        and int(summary.get("reviewed_rows") or 0) == int(summary.get("audit_rows") or -1)
        and int(summary.get("reviewed_model_assessments") or 0)
        == int(summary.get("model_assessments") or -1)
    )


def human_predictor_complete(
    summary: dict[str, Any],
    comparison_rows: list[dict[str, str]],
) -> tuple[bool, str]:
    overall = {
        row.get("metric"): row
        for row in comparison_rows
        if row.get("scope") == "overall"
        and row.get("asr_run_id") == "ALL"
        and row.get("target") == "human_decision_change_yes"
    }
    ok = (
        summary.get("ok") is True
        and summary.get("status") == "review_complete"
        and int(summary.get("reviewed_model_assessments") or 0) == 90
        and {"wer", "cer", "sres_total", "ceis_max"} <= set(overall)
    )
    if not ok:
        return False, "human-reviewed predictor comparison is missing required overall metrics"
    result = (
        "reviewed_model_assessments=90; "
        f"WER_AUC={overall['wer'].get('auc')}; "
        f"CER_AUC={overall['cer'].get('auc')}; "
        f"SRES_AUC={overall['sres_total'].get('auc')}; "
        f"CEIS_AUC={overall['ceis_max'].get('auc')}"
    )
    return True, result


def build_objective_requirement_audit_from_payloads(
    *,
    registry: list[dict[str, str]],
    gitignore_text: str,
    lora_smoke: dict[str, Any],
    partial_smoke: dict[str, Any],
    lora_validation: dict[str, Any],
    partial_validation: dict[str, Any],
    bridge_15_rows: list[dict[str, str]],
    split_258_rows: list[dict[str, str]],
    high_stakes_summary: dict[str, Any],
    predictor_summary: dict[str, Any],
    recovery_summary: dict[str, Any],
    human_recovery_summary: dict[str, Any] | None = None,
    human_refresh: dict[str, Any],
    human_predictor: dict[str, Any],
    human_predictor_rows: list[dict[str, str]],
    post_review: dict[str, Any],
    post_review_sequence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rows: list[dict[str, str]] = []
    reg_ids = registry_ids(registry)
    post_review_sequence = post_review_sequence or {}

    checkpoint_required = {
        "janus_old_train_legacy_import",
        "breeze_asr25_lora_legacy_best",
        "breeze_asr25_partial_encoder_legacy_best",
        "postdoc_evidence_chain_2026_05_25",
    }
    checkpoint_ok = checkpoint_required.issubset(reg_ids)
    rows.append(requirement_row(
        requirement_id="0.1",
        objective_step="0",
        requirement="checkpoint registry records migration, best-model selection, and evidence-chain run",
        status="satisfied" if checkpoint_ok else "missing",
        paper_claim_status="provenance evidence" if checkpoint_ok else "not usable",
        evidence="70_experiments/registry.tsv",
        result=f"{len(checkpoint_required & reg_ids)}/4 required checkpoint rows present",
        next_action="Keep this checkpoint immutable except for append-only aggregate records.",
    ))
    rows.append(requirement_row(
        requirement_id="0.2",
        objective_step="0",
        requirement="large local data, weights, predictions, and artifacts are ignored",
        status="satisfied" if has_gitignore_patterns(gitignore_text) else "missing",
        paper_claim_status="provenance evidence",
        evidence=".gitignore",
        result="raw audio, model payloads, local artifacts, and local predictions are protected"
        if has_gitignore_patterns(gitignore_text)
        else "required ignore patterns are incomplete",
        next_action="Do not stage raw media, model weights, local predictions, or review sheets.",
    ))

    lora_smoke_ok = smoke_ok(lora_smoke, "lora")
    partial_smoke_ok = smoke_ok(partial_smoke, "partial_encoder")
    rows.extend([
        requirement_row(
            requirement_id="1.1",
            objective_step="1",
            requirement="legacy LoRA best model load smoke records runtime, dtype, cuDNN policy, and one-row inference",
            status="satisfied" if lora_smoke_ok else "failed",
            paper_claim_status="engineering gate only",
            evidence="breeze_asr25_lora_legacy_best_smoke summary",
            result=(
                f"ok={lora_smoke.get('ok')}; rows={lora_smoke.get('rows')}; "
                f"runtime={lora_smoke.get('runtime')}; dtype={lora_smoke.get('torch_dtype')}; "
                f"disable_cudnn={lora_smoke.get('disable_cudnn')}; wall_time={lora_smoke.get('wall_time_seconds')}"
            ),
            next_action="Keep as load gate; use split outputs for evidence.",
        ),
        requirement_row(
            requirement_id="1.2",
            objective_step="1",
            requirement="legacy partial-encoder best model load smoke records runtime, dtype, cuDNN policy, and one-row inference",
            status="satisfied" if partial_smoke_ok else "failed",
            paper_claim_status="engineering gate only",
            evidence="breeze_asr25_partial_encoder_legacy_best_smoke summary",
            result=(
                f"ok={partial_smoke.get('ok')}; rows={partial_smoke.get('rows')}; "
                f"runtime={partial_smoke.get('runtime')}; dtype={partial_smoke.get('torch_dtype')}; "
                f"disable_cudnn={partial_smoke.get('disable_cudnn')}; wall_time={partial_smoke.get('wall_time_seconds')}"
            ),
            next_action="If this fails later, repair artifact reconstruction before retraining.",
        ),
    ])

    rows.extend([
        requirement_row(
            requirement_id="2.1",
            objective_step="2",
            requirement="legacy LoRA best joins fixed 15-row hypothesis contract",
            status="satisfied" if validation_ok(lora_validation) else "failed",
            paper_claim_status="engineering gate only",
            evidence="breeze_asr25_lora_legacy_best_15_row validation",
            result="15/15 rows valid with text, label, and quality fields"
            if validation_ok(lora_validation)
            else "15-row validation failed",
            next_action="Use as gate evidence only.",
        ),
        requirement_row(
            requirement_id="2.2",
            objective_step="2",
            requirement="legacy partial-encoder best joins fixed 15-row hypothesis contract",
            status="satisfied" if validation_ok(partial_validation) else "failed",
            paper_claim_status="engineering gate only",
            evidence="breeze_asr25_partial_encoder_legacy_best_15_row validation",
            result="15/15 rows valid with text, label, and quality fields"
            if validation_ok(partial_validation)
            else "15-row validation failed",
            next_action="Use as gate evidence only.",
        ),
    ])

    bridge_runs = {row.get("run_id", "") for row in bridge_15_rows}
    bridge_fields = {"cer_mean", "wer_mean", "mean_ceis", "max_ceis", "downstream_mismatch_rate", "high_risk_missed_by_asr"}
    bridge_ok = (
        {"breeze_asr25_lora_legacy_best_15_row", "breeze_asr25_partial_encoder_legacy_best_15_row"}.issubset(bridge_runs)
        and fields_present(bridge_15_rows, bridge_fields)
    )
    rows.append(requirement_row(
        requirement_id="3.1",
        objective_step="3",
        requirement="15-row CDS-ASR bridge compares CER/WER with CEIS and downstream decision risk",
        status="satisfied" if bridge_ok else "missing",
        paper_claim_status="pilot evidence" if bridge_ok else "not usable",
        evidence="janus_15_decision_stability_legacy_best/asr_cds_model_comparison.tsv",
        result=f"legacy best rows present={bridge_ok}; fields={sorted(bridge_fields)}",
        next_action="Use this only to frame why CER alone is insufficient; do not overclaim from 15 rows.",
    ))

    split_ok, split_result = split_258_complete(split_258_rows)
    registry_258_ok = REQUIRED_258_RUNS.issubset(reg_ids)
    rows.extend([
        requirement_row(
            requirement_id="4.1",
            objective_step="4",
            requirement="canonical 258-row comparison includes six required models and decision-risk columns",
            status="satisfied" if split_ok else "missing",
            paper_claim_status="scope-controlled split/model-comparison evidence",
            evidence="janus_258_test_split_asr_cds_proxy/asr_cds_proxy_comparison.tsv",
            result=split_result,
            blocking_dependency="",
            next_action="Use 258-row aggregate fields as split/model-comparison context; route risk conclusions through reviewed selected-300 labels.",
        ),
        requirement_row(
            requirement_id="4.2",
            objective_step="4",
            requirement="experiment registry records the six 258-row model runs",
            status="satisfied" if registry_258_ok else "missing",
            paper_claim_status="aggregate run provenance",
            evidence="70_experiments/registry.tsv",
            result=f"{len(REQUIRED_258_RUNS & reg_ids)}/6 required 258-row registry rows present",
            next_action="Append only aggregate registry rows for future full-split experiments.",
        ),
    ])

    high_stakes_ok = (
        bool(high_stakes_summary.get("ok"))
        and high_stakes_summary.get("split") == "high_stakes_300"
        and high_stakes_summary.get("review_mode") == "proxy"
        and int(high_stakes_summary.get("reference_rows") or 0) == 300
        and int(high_stakes_summary.get("model_samples") or 0) == 900
    )
    predictor_ok = (
        bool(predictor_summary.get("ok"))
        and int(predictor_summary.get("model_sample_count") or 0) == 900
        and bool(predictor_summary.get("best_overall_predictors_by_auc"))
        and bool(predictor_summary.get("low_wer_summary"))
    )
    human_predictor_ok, human_predictor_result = human_predictor_complete(
        human_predictor,
        human_predictor_rows,
    )
    human_review_complete = (
        human_refresh.get("status") == "review_complete"
        and int(human_refresh.get("pending_rows") or 0) == 0
        and int(human_refresh.get("pending_model_assessments") or 0) == 0
        and bool(human_predictor.get("ok"))
        and human_predictor.get("status") == "review_complete"
    )
    rows.extend([
        requirement_row(
            requirement_id="5.1",
            objective_step="5",
            requirement="selected-300 high-stakes proxy metric inputs exist for the main experiment",
            status="satisfied" if high_stakes_ok else "missing",
            paper_claim_status="selected-300 input provenance",
            evidence="janus_300_high_stakes_cds_proxy_2026_05_25/summary.json",
            result=(
                f"split={high_stakes_summary.get('split')}; review_mode={high_stakes_summary.get('review_mode')}; "
                f"references={high_stakes_summary.get('reference_rows')}; model_samples={high_stakes_summary.get('model_samples')}"
            ),
            blocking_dependency="",
            next_action="Keep this as selected-300 input provenance; paper claims use the completed human-reviewed predictor and recovery outputs.",
        ),
        requirement_row(
            requirement_id="5.2",
            objective_step="5",
            requirement="selected-300 predictor analysis compares WER/CER/SRES/CEIS and low-WER danger cases",
            status="satisfied" if human_predictor_ok else ("proxy_satisfied" if predictor_ok else "missing"),
            paper_claim_status=(
                "human-reviewed predictor evidence"
                if human_predictor_ok
                else "proxy evidence"
            ),
            evidence=(
                "human_audit_predictor_summary.json; human_audit_predictor_comparison.tsv"
                if human_predictor_ok
                else "janus_300_high_stakes_metric_predictor_proxy_2026_05_25/metric_predictor_summary.json"
            ),
            result=(
                human_predictor_result
                if human_predictor_ok
                else (
                    f"model_samples={predictor_summary.get('model_sample_count')}; "
                    f"predictor_targets={sorted((predictor_summary.get('best_overall_predictors_by_auc') or {}).keys())}; "
                    f"low_wer_rows_recorded={len(predictor_summary.get('low_wer_summary') or [])}"
                )
            ),
            blocking_dependency="" if human_predictor_ok else "human-reviewed labels before formal predictor claims",
            next_action=(
                "Use this aggregate human-reviewed predictor comparison for predictor-specific claims."
                if human_predictor_ok
                else "Rerun predictor analysis after selected-300 review is written and refreshed."
            ),
        ),
        requirement_row(
            requirement_id="5.3",
            objective_step="5",
            requirement="selected-300 main experiment has reviewed risk/decision/model/timing evidence",
            status="satisfied" if human_review_complete else "review_pending",
            paper_claim_status="paper-ready" if human_review_complete else "not paper-ready",
            evidence="human_audit_refresh_summary.json; human_audit_predictor_summary.json",
            result=(
                f"reviewed_rows={human_refresh.get('reviewed_rows')}/{human_refresh.get('audit_rows')}; "
                f"reviewed_model_assessments={human_refresh.get('reviewed_model_assessments')}/{human_refresh.get('model_assessments')}; "
                f"human_predictor_status={human_predictor.get('status')}"
            ),
            blocking_dependency="" if human_review_complete else "selected-300 risk labels, decision-change labels, safe action, confidence, per-model fields, and timing",
            next_action="Complete only the non-transcript reviewer fields plus timing, then rerun strict closeout and refresh.",
        ),
    ])

    human_recovery_summary = human_recovery_summary or {}
    recovery_human_complete = human_recovery_complete(human_recovery_summary)
    recovery_evidence = human_recovery_summary if recovery_human_complete else recovery_summary
    recovery_ok, recovery_result = recovery_policy_complete(recovery_evidence)
    recovery_gain_ok, recovery_gain_result = recovery_reduces_proxy_risk(recovery_evidence)
    recovery_human_ready = bool(post_review.get("recovery_human_ready"))
    post_review_sequence_status = str(post_review_sequence.get("status", "missing"))
    post_review_sequence_ok = bool(post_review_sequence.get("ok"))
    post_review_sequence_executed_steps = post_review_sequence.get("executed_step_count", "")
    rows.extend([
        requirement_row(
            requirement_id="6.1",
            objective_step="6",
            requirement="recovery experiment contains all five required policy conditions and safety metrics",
            status="satisfied" if recovery_human_complete else ("proxy_satisfied" if recovery_ok else "missing"),
            paper_claim_status=(
                "human-reviewed recovery evidence"
                if recovery_human_complete
                else "proxy engineering evidence"
            ),
            evidence=(
                "janus_300_high_stakes_recovery_human_reviewed_2026_05_26/summary.json"
                if recovery_human_complete
                else "janus_300_high_stakes_recovery_proxy_2026_05_25/summary.json"
            ),
            result=recovery_result,
            blocking_dependency="" if recovery_human_complete else "human-reviewed labels before intervention claims",
            next_action=(
                "Use this aggregate human-reviewed recovery evidence for recovery-specific claims."
                if recovery_human_complete
                else "Keep this as proxy until selected-300 reviewed labels are available."
            ),
        ),
        requirement_row(
            requirement_id="6.2",
            objective_step="6",
            requirement="recovery result demonstrates reduced dangerous decisions",
            status="satisfied" if recovery_human_complete and recovery_gain_ok else ("proxy_satisfied" if recovery_gain_ok else "failed"),
            paper_claim_status=(
                "human-reviewed recovery evidence"
                if recovery_human_complete
                else "proxy engineering evidence"
            ),
            evidence=(
                "janus_300_high_stakes_recovery_human_reviewed_2026_05_26/summary.json"
                if recovery_human_complete
                else "janus_300_high_stakes_recovery_proxy_2026_05_25/summary.json"
            ),
            result=recovery_gain_result,
            blocking_dependency="" if recovery_human_complete else "human-reviewed recovery rerun before paper-grade intervention claim",
            next_action=(
                "Use the human-reviewed recovery comparison for intervention-safety claims."
                if recovery_human_complete
                else "Rerun recovery after human review and compare safety tradeoffs again."
            ),
        ),
        requirement_row(
            requirement_id="6.3",
            objective_step="6",
            requirement="recovery experiment has human-reviewed post-review evidence",
            status="satisfied" if recovery_human_ready else "review_pending",
            paper_claim_status="paper-ready" if recovery_human_ready else "not paper-ready",
            evidence="human_audit_post_review_evidence_summary.json; human_audit_post_review_sequence_summary.json",
            result=(
                f"recovery_human_ready={recovery_human_ready}; "
                f"post_review_sequence_status={post_review_sequence_status}; "
                f"post_review_sequence_ok={post_review_sequence_ok}; "
                f"post_review_sequence_executed_step_count={post_review_sequence_executed_steps}"
            ),
            blocking_dependency=(
                ""
                if recovery_human_ready
                else (
                    "post-review recovery evidence is still proxy-only and strict "
                    "post-review sequence is not complete"
                )
            ),
            next_action=(
                "Use the human-reviewed recovery outputs for recovery-specific claims; "
                "keep remaining proxy-only paper claims labeled until the proxy gates "
                "are resolved."
                if recovery_human_ready
                else (
                    "After selected-300 response closeout is ready, run "
                    "run_post_review_evidence_sequence.py --execute so write/refresh, "
                    "strict human-reviewed recovery, post-review checklist, and "
                    "objective audit execute in order."
                )
            ),
        ),
    ])

    counts = Counter(row["status"] for row in rows)
    blocking_rows = [
        row for row in rows if row["status"] in {"review_pending", "blocked", "missing", "failed"}
    ]
    proxy_rows = [row for row in rows if row["status"] == "proxy_satisfied"]
    publishable_ready = not blocking_rows and not proxy_rows
    selected_review_done = not any(row["status"] == "review_pending" for row in rows)
    review_scope = (
        "Selected-300 row/model/timing review and human-reviewed recovery are "
        "complete; remaining work is proxy-to-paper claim resolution."
        if selected_review_done
        else REMAINING_REVIEW_SCOPE
    )
    payload = {
        "ok": True,
        "objective_requirements_ready": publishable_ready,
        "publishable_ready": publishable_ready,
        "status_counts": dict(sorted(counts.items(), key=lambda item: STATUS_ORDER.get(item[0], 99))),
        "reference_transcript_policy": REFERENCE_TRANSCRIPT_POLICY,
        "remaining_review_scope": review_scope,
        "requirements_total": len(rows),
        "proxy_requirement_count": len(proxy_rows),
        "blocking_requirement_count": len(blocking_rows),
        "requirement_rows": rows,
        "proxy_or_blocking_requirements": proxy_rows + blocking_rows,
        "next_decision": (
            "All objective requirements have paper-ready evidence."
            if publishable_ready
            else (
                "Do not declare the postdoc objective complete. Selected-300 "
                "human review and human-reviewed recovery are complete; resolve "
                "the remaining proxy-only evidence gates before paper-ready claims."
                if proxy_rows and not blocking_rows
                else (
                    "Do not declare the postdoc objective complete. Complete selected-300 "
                    "row/model/timing review, run strict closeout, then execute "
                    "run_post_review_evidence_sequence.py --execute so write/refresh, "
                    "human predictor refresh, strict human-reviewed recovery, post-review "
                    "checklist, and objective audit happen in order."
                )
            )
        ),
    }
    assert_requirement_audit_safe(payload)
    return payload


def load_current_payloads(root: Path) -> dict[str, Any]:
    return {
        "registry": read_tsv(root / "70_experiments" / "registry.tsv"),
        "gitignore_text": (root / ".gitignore").read_text(encoding="utf-8")
        if (root / ".gitignore").exists()
        else "",
        "lora_smoke": read_json(root / "70_experiments/runs/breeze_asr25_lora_legacy_best_smoke/artifacts/breeze_asr25_lora_legacy_best_smoke_summary.json"),
        "partial_smoke": read_json(root / "70_experiments/runs/breeze_asr25_partial_encoder_legacy_best_smoke/artifacts/breeze_asr25_partial_encoder_legacy_best_smoke_summary.json"),
        "lora_validation": read_json(root / "70_experiments/runs/breeze_asr25_lora_legacy_best_15_row/artifacts/breeze_asr25_lora_legacy_best_15_row_validation.json"),
        "partial_validation": read_json(root / "70_experiments/runs/breeze_asr25_partial_encoder_legacy_best_15_row/artifacts/breeze_asr25_partial_encoder_legacy_best_15_row_validation.json"),
        "bridge_15_rows": read_tsv(root / "70_experiments/runs/janus_15_decision_stability_legacy_best/asr_cds_model_comparison.tsv"),
        "split_258_rows": read_tsv(root / "70_experiments/runs/janus_258_test_split_asr_cds_proxy/asr_cds_proxy_comparison.tsv"),
        "high_stakes_summary": read_json(root / "70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/summary.json"),
        "predictor_summary": read_json(root / "70_experiments/runs/janus_300_high_stakes_metric_predictor_proxy_2026_05_25/metric_predictor_summary.json"),
        "recovery_summary": read_json(root / "70_experiments/runs/janus_300_high_stakes_recovery_proxy_2026_05_25/summary.json"),
        "human_recovery_summary": read_json(root / "70_experiments/runs/janus_300_high_stakes_recovery_human_reviewed_2026_05_26/summary.json"),
        "human_refresh": read_json(root / "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_refresh_summary.json"),
        "human_predictor": read_json(root / "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_predictor_summary.json"),
        "human_predictor_rows": read_tsv(root / "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_predictor_comparison.tsv"),
        "post_review": read_json(root / "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_post_review_evidence_summary.json"),
        "post_review_sequence": read_json(root / "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_post_review_sequence_summary.json"),
    }


def build_current_audit(root: Path = REPO_ROOT) -> dict[str, Any]:
    started = time.time()
    payload = build_objective_requirement_audit_from_payloads(**load_current_payloads(root))
    payload["runtime_seconds"] = round(time.time() - started, 4)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_current_audit(REPO_ROOT)
    output_json = args.output_dir / SUMMARY_NAME
    output_tsv = args.output_dir / TSV_NAME
    write_json(output_json, payload)
    write_tsv(output_tsv, payload["requirement_rows"])
    print(json.dumps({
        "ok": payload["ok"],
        "objective_requirements_ready": payload["objective_requirements_ready"],
        "status_counts": payload["status_counts"],
        "output_json": str(output_json),
        "output_tsv": str(output_tsv),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

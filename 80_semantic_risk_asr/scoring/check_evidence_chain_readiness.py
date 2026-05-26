#!/usr/bin/env python3
"""Build an aggregate-safe readiness report for the CDS-ASR evidence chain."""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any


STATUS_ORDER = {
    "completed": 0,
    "proxy_completed": 1,
    "review_pending": 2,
    "partial_review": 2,
    "planned": 3,
    "missing": 4,
    "failed": 5,
}

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


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "phase",
        "requirement",
        "status",
        "paper_claim_status",
        "evidence",
        "result",
        "next_action",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def assert_aggregate_safe(payload: Any) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    for token in SENSITIVE_TOKENS:
        if token in text:
            raise ValueError(f"sensitive token leaked into readiness output: {token}")


def status_at_least(rows: list[dict[str, Any]], max_status_rank: int) -> bool:
    return all(STATUS_ORDER.get(str(row["status"]), 99) <= max_status_rank for row in rows)


def row(
    *,
    phase: str,
    requirement: str,
    status: str,
    evidence: str,
    result: str,
    next_action: str,
    paper_claim_status: str,
) -> dict[str, str]:
    return {
        "phase": phase,
        "requirement": requirement,
        "status": status,
        "paper_claim_status": paper_claim_status,
        "evidence": evidence,
        "result": result,
        "next_action": next_action,
    }


def json_ok(path: Path) -> bool:
    return path.exists() and bool(read_json(path).get("ok"))


def reviewer_action_gate(root: Path) -> dict[str, Any]:
    path = (
        root
        / "70_experiments"
        / "runs"
        / "janus_300_high_stakes_human_audit_selection_2026_05_25"
        / "human_audit_reviewer_action_checklist_summary.json"
    )
    payload = read_json(path) if path.exists() else {}
    return {
        "available": bool(payload),
        "ok": bool(payload.get("ok")),
        "status": payload.get("status", "missing"),
        "selection_stratum": payload.get("selection_stratum", ""),
        "rows_in_batch": payload.get("rows_in_batch", 0),
        "pending_rows_in_batch": payload.get("pending_rows_in_batch", 0),
        "model_assessments_in_batch": payload.get("model_assessments_in_batch", 0),
        "pending_model_assessments_in_batch": payload.get(
            "pending_model_assessments_in_batch",
            0,
        ),
        "rows_missing_timing": payload.get("rows_missing_timing", 0),
        "latest_apply_status": payload.get("latest_apply_status", ""),
        "evidence": (
            "70_experiments/runs/"
            "janus_300_high_stakes_human_audit_selection_2026_05_25/"
            "human_audit_reviewer_action_checklist_summary.json"
        ),
    }


def smoke_gate(root: Path) -> dict[str, str]:
    lora = root / "70_experiments/runs/breeze_asr25_lora_legacy_best_smoke/artifacts/breeze_asr25_lora_legacy_best_smoke_summary.json"
    partial = root / "70_experiments/runs/breeze_asr25_partial_encoder_legacy_best_smoke/artifacts/breeze_asr25_partial_encoder_legacy_best_smoke_summary.json"
    summaries = [read_json(path) for path in (lora, partial) if path.exists()]
    ok = len(summaries) == 2 and all(
        item.get("ok")
        and item.get("rows") == 1
        and item.get("runtime")
        and item.get("torch_dtype")
        and item.get("disable_cudnn") is not None
        for item in summaries
    )
    result = (
        "LoRA and partial encoder each loaded one row with runtime, dtype, and cuDNN policy recorded"
        if ok
        else "Missing one-row load smoke evidence for LoRA or partial encoder"
    )
    return row(
        phase="1",
        requirement="legacy-best load smoke tests",
        status="completed" if ok else "missing",
        paper_claim_status="engineering gate only",
        evidence="legacy best smoke summary JSON files",
        result=result,
        next_action="Use 15-row fixed gate only after both smoke summaries are ok.",
    )


def fixed_15_row_gate(root: Path) -> dict[str, str]:
    validation_paths = [
        root / "70_experiments/runs/breeze_asr25_lora_legacy_best_15_row/artifacts/breeze_asr25_lora_legacy_best_15_row_validation.json",
        root / "70_experiments/runs/breeze_asr25_partial_encoder_legacy_best_15_row/artifacts/breeze_asr25_partial_encoder_legacy_best_15_row_validation.json",
    ]
    summaries = [read_json(path) for path in validation_paths if path.exists()]
    ok = len(summaries) == 2 and all(
        item.get("ok")
        and item.get("files")
        and item["files"][0].get("counts", {}).get("rows") == 15
        and all(item["files"][0].get("checks", {}).values())
        for item in summaries
    )
    return row(
        phase="2",
        requirement="legacy best models join the fixed 15-row hypothesis contract",
        status="completed" if ok else "missing",
        paper_claim_status="engineering gate only",
        evidence="legacy best 15-row validation JSON files",
        result="Both legacy best hypotheses validate at 15 rows" if ok else "15-row validation incomplete",
        next_action="Run or refresh 15-row CDS bridge after contract validation.",
    )


def cds_15_row_bridge(root: Path) -> dict[str, str]:
    path = root / "70_experiments/runs/janus_15_decision_stability_legacy_best/asr_cds_model_comparison.tsv"
    rows = read_tsv(path) if path.exists() else []
    required_runs = {
        "breeze_asr25_lora_legacy_best_15_row",
        "breeze_asr25_partial_encoder_legacy_best_15_row",
        "breeze_asr25_15_row_baseline",
    }
    observed = {item.get("run_id", "") for item in rows}
    ok = required_runs <= observed
    result = "15-row bridge includes base, LoRA, and partial encoder decision-stability metrics" if ok else "15-row bridge missing required legacy best rows"
    return row(
        phase="3",
        requirement="CDS-ASR bridge over 15-row legacy-best hypotheses",
        status="completed" if ok else "missing",
        paper_claim_status="pilot evidence",
        evidence="janus_15_decision_stability_legacy_best/asr_cds_model_comparison.tsv",
        result=result,
        next_action="Use the bridge as pilot evidence only; main claims need split/high-stakes evidence.",
    )


def test_split_gate(root: Path) -> dict[str, str]:
    summary = root / "70_experiments/runs/janus_258_test_split_asr_cds_proxy/summary.json"
    comparison = root / "70_experiments/runs/janus_258_test_split_asr_cds_proxy/asr_cds_proxy_comparison.tsv"
    rows = read_tsv(comparison) if comparison.exists() else []
    required_runs = {
        "whisper_small_test_split",
        "whisper_large_v2_test_split",
        "breeze_asr25_base_test_split",
        "breeze_asr25_lora_legacy_best_test_split",
        "breeze_asr25_partial_encoder_legacy_best_test_split",
        "breeze_asr26_test_split",
    }
    observed = {item.get("run_id", "") for item in rows}
    metric_fields = {
        "risk_atom_error_rate",
        "negation_flip_rate",
        "amount_distortion_rate",
        "action_confusion_rate",
        "unsafe_downrouting_count",
        "high_risk_missed_count",
    }
    ok = json_ok(summary) and required_runs <= observed and all(
        metric_fields <= set(item) for item in rows
    )
    return row(
        phase="4",
        requirement="canonical 258-row six-model comparison with decision-risk metrics",
        status="completed" if ok else "missing",
        paper_claim_status="scope-controlled split/model-comparison evidence",
        evidence="janus_258_test_split_asr_cds_proxy summary and comparison TSV",
        result="Six-model 258-row comparison includes CER/WER plus risk-atom and unsafe-decision metrics" if ok else "258-row comparison incomplete",
        next_action="Use these aggregate split results for model-comparison context; route paper-grade risk conclusions through reviewed selected-300 labels.",
    )


def high_stakes_proxy_gate(root: Path) -> dict[str, str]:
    summary = root / "70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/summary.json"
    payload = read_json(summary) if summary.exists() else {}
    ok = (
        payload.get("ok")
        and payload.get("reference_rows") == 300
        and payload.get("model_samples") == 900
        and payload.get("ceis", {}).get("unstable_samples", 0) > 0
    )
    result = (
        "Selected-300 proxy main experiment has 300 references, 900 model-samples, and CEIS instability"
        if ok
        else "Selected-300 proxy main experiment missing or incomplete"
    )
    return row(
        phase="5",
        requirement="selected-300 high-stakes CDS-ASR main experiment proxy",
        status="completed" if ok else "missing",
        paper_claim_status="selected-300 input provenance paired with completed human-reviewed outputs",
        evidence="janus_300_high_stakes_cds_proxy_2026_05_25/summary.json",
        result=result,
        next_action="Use this as selected-300 input provenance; paper-grade claims use the completed human-reviewed predictor and recovery outputs.",
    )


def metric_predictor_gate(root: Path) -> dict[str, str]:
    human_dir = root / "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25"
    human_summary = read_json(human_dir / "human_audit_predictor_summary.json")
    human_rows = read_tsv(human_dir / "human_audit_predictor_comparison.tsv")
    human_overall = {
        row.get("metric"): row
        for row in human_rows
        if row.get("scope") == "overall"
        and row.get("asr_run_id") == "ALL"
        and row.get("target") == "human_decision_change_yes"
    }
    human_ready = (
        human_summary.get("ok") is True
        and human_summary.get("status") == "review_complete"
        and int(human_summary.get("reviewed_model_assessments") or 0) == 90
        and {"wer", "cer", "sres_total", "ceis_max"} <= set(human_overall)
    )
    if human_ready:
        result = (
            "Human-reviewed predictor comparison over 90 model assessments: "
            f"WER AUC {human_overall['wer'].get('auc')}, "
            f"CER AUC {human_overall['cer'].get('auc')}, "
            f"SRES AUC {human_overall['sres_total'].get('auc')}, "
            f"CEIS AUC {human_overall['ceis_max'].get('auc')}."
        )
        return row(
            phase="5",
            requirement="WER/CER/SRES/CEIS predictor comparison on selected-300",
            status="completed",
            paper_claim_status="human-reviewed predictor evidence",
            evidence="human_audit_predictor_summary.json; human_audit_predictor_comparison.tsv",
            result=result,
            next_action="Use aggregate human-reviewed predictor outputs for predictor-specific claims.",
        )

    path = root / "70_experiments/runs/janus_300_high_stakes_metric_predictor_proxy_2026_05_25/metric_predictor_summary.json"
    payload = read_json(path) if path.exists() else {}
    unsafe = payload.get("best_overall_predictors_by_auc", {}).get("unsafe_downrouting", {})
    ok = payload.get("ok") and payload.get("model_sample_count") == 900 and unsafe.get("metric") == "ceis_max"
    result = (
        "Proxy predictor analysis ranks CEIS as best unsafe-downrouting predictor over 900 samples"
        if ok
        else "Metric predictor proxy summary missing or incomplete"
    )
    return row(
        phase="5",
        requirement="WER/CER/SRES/CEIS predictor comparison on selected-300",
        status="proxy_completed" if ok else "missing",
        paper_claim_status="proxy evidence until model-level human labels exist",
        evidence="janus_300_high_stakes_metric_predictor_proxy_2026_05_25/metric_predictor_summary.json",
        result=result,
        next_action="Rerun predictor gate after model-level human review is complete.",
    )


def recovery_gate(root: Path) -> dict[str, str]:
    human_path = root / "70_experiments/runs/janus_300_high_stakes_recovery_human_reviewed_2026_05_26/summary.json"
    proxy_path = root / "70_experiments/runs/janus_300_high_stakes_recovery_proxy_2026_05_25/summary.json"
    human_payload = read_json(human_path) if human_path.exists() else {}
    proxy_payload = read_json(proxy_path) if proxy_path.exists() else {}
    payload = human_payload if human_payload.get("human_reviewed") else proxy_payload
    policies = payload.get("policies", {})
    required = {
        "no_recovery",
        "confidence_only_trigger",
        "sres_triggered_recovery",
        "ceis_triggered_conservative_action",
        "ceis_ensemble_arbitration",
    }
    no_recovery = policies.get("no_recovery", {})
    ceis = policies.get("ceis_triggered_conservative_action", {})
    ok = (
        payload.get("ok")
        and required <= set(policies)
        and no_recovery.get("critical_miss_count", 0) > ceis.get("critical_miss_count", 999)
        and no_recovery.get("high_risk_missed_count", 0) > ceis.get("high_risk_missed_count", 999)
    )
    human_ready = (
        ok
        and payload.get("human_reviewed") is True
        and payload.get("review_status") == "human_reviewed_complete"
    )
    result = (
        "Five-condition human-reviewed recovery gate reduces high-risk missed and critical miss under CEIS action"
        if human_ready
        else (
            "Five-condition proxy recovery gate reduces high-risk missed and critical miss under CEIS action"
            if ok
            else "Recovery gate missing required policies or safety reduction"
        )
    )
    return row(
        phase="6",
        requirement="five-condition recovery experiment",
        status="completed" if human_ready else ("proxy_completed" if ok else "missing"),
        paper_claim_status=(
            "human-reviewed recovery evidence"
            if human_ready
            else "proxy engineering evidence until human audit confirms labels"
        ),
        evidence=(
            "janus_300_high_stakes_recovery_human_reviewed_2026_05_26/summary.json"
            if human_ready
            else "janus_300_high_stakes_recovery_proxy_2026_05_25/summary.json"
        ),
        result=result,
        next_action=(
            "Use aggregate human-reviewed recovery outputs for recovery-specific claims."
            if human_ready
            else "Re-evaluate recovery after human-reviewed labels replace proxy labels."
        ),
    )


def human_audit_gate(root: Path) -> dict[str, str]:
    path = root / "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_validation_summary.json"
    payload = read_json(path) if path.exists() else {}
    action_gate = reviewer_action_gate(root)
    action_status = action_gate["status"]
    action_detail = ""
    if action_gate["available"]:
        action_detail = (
            f"; current reviewer action gate is {action_status} with "
            f"{action_gate['pending_rows_in_batch']}/{action_gate['rows_in_batch']} "
            "packet rows and "
            f"{action_gate['pending_model_assessments_in_batch']}/"
            f"{action_gate['model_assessments_in_batch']} model assessments pending, "
            f"and {action_gate['rows_missing_timing']}/{action_gate['rows_in_batch']} "
            "timing rows pending"
        )
    complete = (
        payload.get("ok")
        and payload.get("status") == "review_complete"
        and payload.get("reviewed_rows") == 30
        and payload.get("reviewed_model_assessments") == 90
    )
    pending = payload.get("status") in {"review_pending", "partial_review"}
    if complete:
        status = "completed"
        paper_status = "human-reviewed evidence ready"
        result = "Human audit complete"
        next_action = "Rerun summarizer, predictor gate, and recovery with human-reviewed labels."
    elif pending:
        status = str(payload.get("status"))
        paper_status = "not paper-ready"
        result = (
            f"{payload.get('reviewed_rows', 0)}/30 selected rows have risk-atom "
            "review fields complete and "
            f"{payload.get('reviewed_model_assessments', 0)}/90 model assessments "
            "are complete; transcript ground truth is not the pending item"
            f"{action_detail}"
        )
        next_action = (
            "Run the reviewer action checklist, fill selected-300 risk-atom, "
            "decision-change, expected-action, confidence, and per-model "
            "assessment fields plus per-row review timing; then run the "
            "session-gated strict response dry-run with --require-complete "
            "--require-timing before the aggregate refresh."
        )
    else:
        status = "missing"
        paper_status = "not paper-ready"
        result = "Human audit validation summary missing or failed"
        next_action = "Run selected-300 human audit validation gate."
    return row(
        phase="5",
        requirement="selected-300 human risk-atom audit completion",
        status=status,
        paper_claim_status=paper_status,
        evidence=(
            "human_audit_validation_summary.json; "
            "human_audit_reviewer_action_checklist_summary.json"
        ),
        result=result,
        next_action=next_action,
    )


def wer_gate(root: Path) -> dict[str, str]:
    paths = [
        root / "70_experiments/runs/wer_metric_audit_2026_05_25/legacy_15_row_summary.json",
        root / "70_experiments/runs/wer_metric_audit_2026_05_25/summary.json",
        root / "70_experiments/runs/wer_metric_audit_2026_05_25/high_stakes_300_summary.json",
    ]
    payloads = [read_json(path) for path in paths if path.exists()]
    zero_ref_clean = all(
        all(count == 0 for count in summary.get("zero_reference_unit_rows", {}).values())
        for payload in payloads
        for summary in payload.get("summaries", [])
    )
    ok = len(payloads) == 3 and all(payload.get("ok") for payload in payloads) and zero_ref_clean
    return row(
        phase="metric_policy",
        requirement="strict WER/CER policy and manifest audit",
        status="completed" if ok else "failed",
        paper_claim_status="metric-definition evidence ready",
        evidence="wer_metric_audit_2026_05_25 summary JSON files",
        result="15-row, 258-row, and 300-row WER audits are ok with zero zero-reference-unit rows" if ok else "WER audit failed or incomplete",
        next_action="Use cer_zh_micro as primary surface metric; keep wer_zh_jieba_micro supplemental.",
    )


def checkpoint_gate(root: Path) -> dict[str, str]:
    registry = root / "70_experiments/registry.tsv"
    rows = read_tsv(registry) if registry.exists() else []
    required = {
        "janus_old_train_legacy_import",
        "breeze_asr25_lora_legacy_best",
        "breeze_asr25_partial_encoder_legacy_best",
        "postdoc_evidence_chain_2026_05_25",
    }
    observed = {item.get("run_id", "") for item in rows}
    ok = required <= observed
    return row(
        phase="0",
        requirement="migration and best-model selection checkpoint",
        status="completed" if ok else "missing",
        paper_claim_status="provenance evidence",
        evidence="70_experiments/registry.tsv and run records",
        result="Legacy import, best-model selection, and evidence-chain record are registered" if ok else "Checkpoint registry rows missing",
        next_action="Keep raw weights and predictions local; commit only aggregate records.",
    )


def build_readiness(root: Path) -> dict[str, Any]:
    action_gate = reviewer_action_gate(root)
    rows = [
        checkpoint_gate(root),
        smoke_gate(root),
        fixed_15_row_gate(root),
        cds_15_row_bridge(root),
        test_split_gate(root),
        wer_gate(root),
        high_stakes_proxy_gate(root),
        metric_predictor_gate(root),
        recovery_gate(root),
        human_audit_gate(root),
    ]
    counts: dict[str, int] = {}
    for item in rows:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    paper_ready = all(item["status"] == "completed" for item in rows)
    proxy_only = [item for item in rows if item["status"] == "proxy_completed"]
    pending = [item for item in rows if item["status"] in {"review_pending", "planned", "missing", "failed"}]
    payload = {
        "ok": status_at_least(rows, STATUS_ORDER["review_pending"]),
        "paper_ready": paper_ready,
        "status_counts": dict(sorted(counts.items())),
        "reference_transcript_policy": REFERENCE_TRANSCRIPT_POLICY,
        "remaining_review_scope": (
            "Selected-300 row/model/timing review and human-reviewed recovery are complete; "
            "remaining work is proxy-to-paper claim resolution."
            if not pending
            else REMAINING_REVIEW_SCOPE
        ),
        "reviewer_action_gate": action_gate,
        "readiness_rows": rows,
        "blocking_gates": [
            {
                "phase": item["phase"],
                "requirement": item["requirement"],
                "status": item["status"],
                "next_action": item["next_action"],
            }
            for item in pending
        ],
        "proxy_only_gates": [
            {
                "phase": item["phase"],
                "requirement": item["requirement"],
                "next_action": item["next_action"],
            }
            for item in proxy_only
        ],
        "next_decision": (
            "Use completed human-reviewed selected-300 and recovery evidence "
            "for their scoped claims, then upgrade or explicitly bound the "
            "remaining proxy-only gates before declaring paper-ready CDS-ASR claims."
            if not pending
            else (
                "Complete the selected-300 risk-atom, decision-change, per-model "
                "assessment, and per-row timing fields, then rerun the strict "
                "response closeout with --require-complete --require-timing, "
                "aggregate summarizer, human-reviewed predictor gate, and recovery "
                "analysis before making paper-grade CDS-ASR claims."
            )
        ),
    }
    assert_aggregate_safe(payload)
    return payload


def parse_args() -> argparse.Namespace:
    root = repo_root_from_script()
    default_output_dir = (
        root
        / "70_experiments"
        / "runs"
        / "postdoc_evidence_chain_2026_05_25"
    )
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=root)
    parser.add_argument("--output-dir", type=Path, default=default_output_dir)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-tsv", type=Path)
    return parser.parse_args()


def main() -> int:
    started = time.time()
    args = parse_args()
    root = args.repo_root.resolve()
    payload = build_readiness(root)
    payload["runtime_seconds"] = round(time.time() - started, 4)
    output_json = args.output_json or args.output_dir / "evidence_chain_readiness_summary.json"
    output_tsv = args.output_tsv or args.output_dir / "evidence_chain_readiness.tsv"
    write_json(output_json, payload)
    write_tsv(output_tsv, payload["readiness_rows"])
    print(
        json.dumps(
            {
                "ok": payload["ok"],
                "paper_ready": payload["paper_ready"],
                "status_counts": payload["status_counts"],
                "output_json": str(output_json),
                "output_tsv": str(output_tsv),
            },
            ensure_ascii=False,
        )
    )
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

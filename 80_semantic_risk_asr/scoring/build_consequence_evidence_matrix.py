#!/usr/bin/env python3
"""Build a paper-facing consequence-to-evidence matrix.

This is not another metric runner. It maps the current aggregate evidence into
claims a reviewer could evaluate, while keeping proxy evidence separate from
human-reviewed paper claims.
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
SUMMARY_NAME = "consequence_evidence_matrix_summary.json"
TSV_NAME = "consequence_evidence_matrix.tsv"

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
    "decision-change labels, expected safe action, confidence, and per-model "
    "assessment fields."
)
STATUS_ORDER = {
    "completed": 0,
    "proxy_completed": 1,
    "review_pending": 2,
    "planned": 3,
    "missing": 4,
    "failed": 5,
}
TSV_FIELDS = [
    "consequence_id",
    "claim_class",
    "consequence_claim",
    "status",
    "paper_claim_status",
    "evidence_files",
    "aggregate_result",
    "blocking_dependency",
    "next_action",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


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


def assert_matrix_safe(payload: Any) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    for token in SENSITIVE_TOKENS:
        if token in text:
            raise ValueError(f"sensitive token leaked into consequence matrix: {token}")


def first_row(rows: list[dict[str, str]], **matches: str) -> dict[str, str]:
    for row in rows:
        if all(row.get(key) == value for key, value in matches.items()):
            return row
    return {}


def float_value(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def row(
    *,
    consequence_id: str,
    claim_class: str,
    consequence_claim: str,
    status: str,
    paper_claim_status: str,
    evidence_files: str,
    aggregate_result: str,
    blocking_dependency: str,
    next_action: str,
) -> dict[str, str]:
    return {
        "consequence_id": consequence_id,
        "claim_class": claim_class,
        "consequence_claim": consequence_claim,
        "status": status,
        "paper_claim_status": paper_claim_status,
        "evidence_files": evidence_files,
        "aggregate_result": aggregate_result,
        "blocking_dependency": blocking_dependency,
        "next_action": next_action,
    }


def consequence_rows_from_payloads(
    *,
    journal_compliance: dict[str, Any],
    metric_predictor_summary: dict[str, Any],
    metric_predictor_rows: list[dict[str, str]],
    recovery_summary: dict[str, Any],
    split_rows: list[dict[str, str]],
    human_refresh: dict[str, Any],
    preflight: dict[str, Any],
    completion_audit: dict[str, Any],
) -> list[dict[str, str]]:
    unsafe_wer = first_row(
        metric_predictor_rows,
        scope="overall",
        asr_run_id="ALL",
        target="unsafe_downrouting",
        metric="wer",
    )
    unsafe_cer = first_row(
        metric_predictor_rows,
        scope="overall",
        asr_run_id="ALL",
        target="unsafe_downrouting",
        metric="cer",
    )
    unsafe_ceis = first_row(
        metric_predictor_rows,
        scope="overall",
        asr_run_id="ALL",
        target="unsafe_downrouting",
        metric="ceis_max",
    )
    low_wer_overall = next(
        (
            item
            for item in metric_predictor_summary.get("low_wer_summary", [])
            if item.get("asr_run_id") == "ALL"
        ),
        {},
    )
    partial_run = metric_predictor_summary.get("run_summary", {}).get(
        "breeze_asr25_partial_encoder_high_stakes_300",
        {},
    )
    lora_run = metric_predictor_summary.get("run_summary", {}).get(
        "breeze_asr25_lora_high_stakes_300",
        {},
    )
    base_run = metric_predictor_summary.get("run_summary", {}).get(
        "breeze_asr25_base_high_stakes_300",
        {},
    )
    split_partial = first_row(
        split_rows,
        run_id="breeze_asr25_partial_encoder_legacy_best_test_split",
    )
    split_lora = first_row(split_rows, run_id="breeze_asr25_lora_legacy_best_test_split")
    no_recovery = recovery_summary.get("policies", {}).get("no_recovery", {})
    ceis_recovery = recovery_summary.get("policies", {}).get(
        "ceis_triggered_conservative_action",
        {},
    )
    ensemble = recovery_summary.get("policies", {}).get("ceis_ensemble_arbitration", {})

    metric_policy_ok = bool(journal_compliance.get("paper_reporting_compliant"))
    low_wer_danger = int(low_wer_overall.get("low_wer_any_danger_count") or 0)
    ceis_beats_wer = float_value(unsafe_ceis.get("auc")) > float_value(unsafe_wer.get("auc"))
    ceis_beats_cer = float_value(unsafe_ceis.get("auc")) > float_value(unsafe_cer.get("auc"))
    predictor_ok = bool(metric_predictor_summary.get("ok")) and low_wer_danger > 0
    split_ok = bool(split_partial and split_lora)
    recovery_ok = (
        bool(recovery_summary.get("ok"))
        and no_recovery.get("high_risk_missed_count", 0)
        > ceis_recovery.get("high_risk_missed_count", 999)
        and no_recovery.get("critical_miss_count", 0)
        > ceis_recovery.get("critical_miss_count", 999)
    )
    human_complete = (
        human_refresh.get("ok")
        and human_refresh.get("status") == "review_complete"
        and human_refresh.get("pending_rows") == 0
        and human_refresh.get("pending_model_assessments") == 0
    )
    preflight_ready = bool(preflight.get("ok")) and preflight.get("status") == "review_session_ready"

    rows = [
        row(
            consequence_id="C0",
            claim_class="metric_reporting",
            consequence_claim="Chinese ASR surface metrics are declared and auditable.",
            status="completed" if metric_policy_ok else "failed",
            paper_claim_status="method-reporting ready" if metric_policy_ok else "not usable",
            evidence_files="wer_metric_audit_2026_05_25/journal_compliance_summary.json",
            aggregate_result=(
                "Paper-facing policy is CER micro primary plus zh-jieba WER micro supplemental; "
                "legacy raw/stored WER remains audit-only."
                if metric_policy_ok
                else "Metric-reporting policy is not compliant."
            ),
            blocking_dependency="",
            next_action="Cite tokenizer, normalization, micro/macro scope, manifest checks, and zero-reference-unit status.",
        ),
        row(
            consequence_id="C1",
            claim_class="metric_insufficiency",
            consequence_claim="Correct WER/CER reporting is necessary but insufficient for high-stakes safety.",
            status="proxy_completed" if predictor_ok and ceis_beats_wer and ceis_beats_cer else "missing",
            paper_claim_status="proxy consequence evidence until human review confirms labels",
            evidence_files="janus_300_high_stakes_metric_predictor_proxy_2026_05_25/metric_predictor_summary.json; metric_predictor_comparison.tsv",
            aggregate_result=(
                f"Among {low_wer_overall.get('rows', '')} model-samples, "
                f"{low_wer_overall.get('low_wer_rows', '')} are low-WER at threshold "
                f"{low_wer_overall.get('low_wer_threshold', '')}, yet "
                f"{low_wer_danger} danger events remain; unsafe-downrouting AUC is "
                f"WER {unsafe_wer.get('auc', '')}, CER {unsafe_cer.get('auc', '')}, "
                f"CEIS {unsafe_ceis.get('auc', '')}."
            ),
            blocking_dependency="selected-300 human risk/decision/model review",
            next_action="After human review, rerun predictor analysis and verify this relationship against reviewed decision-change labels.",
        ),
        row(
            consequence_id="C2",
            claim_class="model_comparison",
            consequence_claim="Better ASR reduces dangerous decision events but does not remove them.",
            status="proxy_completed" if partial_run and lora_run and base_run else "missing",
            paper_claim_status="proxy model-comparison evidence until human model labels exist",
            evidence_files="janus_300_high_stakes_metric_predictor_proxy_2026_05_25/metric_predictor_summary.json",
            aggregate_result=(
                "High-stakes proxy danger events: base "
                f"{base_run.get('danger_event_count', '')}, LoRA "
                f"{lora_run.get('danger_event_count', '')}, partial encoder "
                f"{partial_run.get('danger_event_count', '')}; partial encoder still has "
                f"{partial_run.get('unsafe_downrouting_count', '')} unsafe downrouting and "
                f"{partial_run.get('high_risk_missed_count', '')} high-risk miss."
            ),
            blocking_dependency="human model-level assessments",
            next_action="Use selected-300 per-model review fields before writing model-safety superiority claims.",
        ),
        row(
            consequence_id="C3",
            claim_class="split_generalization",
            consequence_claim="The 258-row test split supports model comparison beyond CER/WER.",
            status="proxy_completed" if split_ok else "missing",
            paper_claim_status="proxy split evidence; not human-reviewed risk evidence",
            evidence_files="janus_258_test_split_asr_cds_proxy/asr_cds_proxy_comparison.tsv",
            aggregate_result=(
                "258-row proxy comparison: partial encoder unsafe downrouting "
                f"{split_partial.get('unsafe_downrouting_count', '')}, high-risk missed "
                f"{split_partial.get('high_risk_missed_count', '')}; LoRA unsafe downrouting "
                f"{split_lora.get('unsafe_downrouting_count', '')}, high-risk missed "
                f"{split_lora.get('high_risk_missed_count', '')}."
            ),
            blocking_dependency="human-reviewed risk-atom evidence for paper-grade risk claims",
            next_action="Keep this as aggregate split evidence and route paper-grade risk claims through selected-300 review.",
        ),
        row(
            consequence_id="C4",
            claim_class="recovery",
            consequence_claim="CDS-ASR recovery can reduce dangerous decisions under proxy labels.",
            status="proxy_completed" if recovery_ok else "missing",
            paper_claim_status="proxy engineering evidence until human labels confirm outcomes",
            evidence_files="janus_300_high_stakes_recovery_proxy_2026_05_25/summary.json",
            aggregate_result=(
                "No recovery has high-risk missed "
                f"{no_recovery.get('high_risk_missed_count', '')} and critical miss "
                f"{no_recovery.get('critical_miss_count', '')}; CEIS conservative action has "
                f"{ceis_recovery.get('high_risk_missed_count', '')}/"
                f"{ceis_recovery.get('critical_miss_count', '')} with recovery budget "
                f"{ceis_recovery.get('recovery_budget_rate', '')}; ensemble abstains "
                f"{ensemble.get('machine_abstention_count', '')} times."
            ),
            blocking_dependency="post-review recovery re-evaluation",
            next_action="Rerun recovery once selected-300 reviewed labels exist; report critical miss, unsafe downrouting, over-escalation, abstention, stability gain, and budget.",
        ),
        row(
            consequence_id="C5",
            claim_class="human_evidence_gate",
            consequence_claim="The human-reviewed evidence path is ready to execute but not complete.",
            status="completed" if human_complete else "review_pending",
            paper_claim_status="human-reviewed evidence ready" if human_complete else "not paper-ready",
            evidence_files="human_audit_refresh_summary.json; human_audit_reviewer_preflight_summary.json",
            aggregate_result=(
                f"Review progress is {human_refresh.get('reviewed_rows', 0)}/"
                f"{human_refresh.get('audit_rows', 30)} rows and "
                f"{human_refresh.get('reviewed_model_assessments', 0)}/"
                f"{human_refresh.get('model_assessments', 90)} model assessments; "
                f"preflight status is {preflight.get('status', 'missing')}."
            ),
            blocking_dependency="selected-300 risk atoms, decision-change labels, expected safe action, confidence, and per-model assessments",
            next_action="Fill the current ready packet, run strict dry-run to response_complete, then write and refresh aggregate evidence.",
        ),
        row(
            consequence_id="C6",
            claim_class="publishability",
            consequence_claim="The repo is not yet paper-ready despite strong proxy evidence.",
            status="completed" if completion_audit.get("publishable_ready") else "review_pending",
            paper_claim_status="paper-ready" if completion_audit.get("publishable_ready") else "not paper-ready",
            evidence_files="postdoc_evidence_chain_2026_05_25/publishable_evidence_completion_summary.json",
            aggregate_result=(
                "Publishable readiness is false; status counts are "
                f"{completion_audit.get('status_counts', {})}."
                if not completion_audit.get("publishable_ready")
                else "All objective-level paper evidence is complete."
            ),
            blocking_dependency="selected-300 human review and post-review predictor/recovery refresh",
            next_action="Do not spend GPU time on more fine-tuning until the selected-300 human evidence gate closes.",
        ),
    ]
    return rows


def build_matrix_from_payloads(
    root: Path,
    *,
    human_refresh: dict[str, Any] | None = None,
    completion_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metric_dir = root / "70_experiments" / "runs" / "janus_300_high_stakes_metric_predictor_proxy_2026_05_25"
    recovery_dir = root / "70_experiments" / "runs" / "janus_300_high_stakes_recovery_proxy_2026_05_25"
    human_dir = root / "70_experiments" / "runs" / "janus_300_high_stakes_human_audit_selection_2026_05_25"
    postdoc_dir = root / "70_experiments" / "runs" / "postdoc_evidence_chain_2026_05_25"
    rows = consequence_rows_from_payloads(
        journal_compliance=read_json(
            root / "70_experiments" / "runs" / "wer_metric_audit_2026_05_25" / "journal_compliance_summary.json"
        ),
        metric_predictor_summary=read_json(metric_dir / "metric_predictor_summary.json"),
        metric_predictor_rows=read_tsv(metric_dir / "metric_predictor_comparison.tsv"),
        recovery_summary=read_json(recovery_dir / "summary.json"),
        split_rows=read_tsv(
            root
            / "70_experiments"
            / "runs"
            / "janus_258_test_split_asr_cds_proxy"
            / "asr_cds_proxy_comparison.tsv"
        ),
        human_refresh=human_refresh
        if human_refresh is not None
        else read_json(human_dir / "human_audit_refresh_summary.json"),
        preflight=read_json(human_dir / "human_audit_reviewer_preflight_summary.json"),
        completion_audit=completion_audit
        if completion_audit is not None
        else read_json(postdoc_dir / "publishable_evidence_completion_summary.json"),
    )
    counts: dict[str, int] = {}
    for item in rows:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    blocking_rows = [
        {
            "consequence_id": item["consequence_id"],
            "claim_class": item["claim_class"],
            "status": item["status"],
            "blocking_dependency": item["blocking_dependency"],
            "next_action": item["next_action"],
        }
        for item in rows
        if item["status"] != "completed" or item["paper_claim_status"].startswith("proxy")
    ]
    payload = {
        "ok": all(STATUS_ORDER.get(item["status"], 99) <= STATUS_ORDER["review_pending"] for item in rows),
        "paper_claims_ready": all(
            item["status"] == "completed" and not item["paper_claim_status"].startswith("proxy")
            for item in rows
        ),
        "status_counts": dict(sorted(counts.items())),
        "reference_transcript_policy": REFERENCE_TRANSCRIPT_POLICY,
        "remaining_review_scope": REMAINING_REVIEW_SCOPE,
        "consequence_rows": rows,
        "blocking_or_proxy_items": blocking_rows,
        "first_principle_decision": (
            "Move from model-centric ASR improvement to consequence-centric evidence: "
            "claims become paper-ready only when aggregate consequences are tied to "
            "human-reviewed risk/decision/model labels."
        ),
        "next_decision": (
            "Use the ready selected-300 packet to complete risk/decision/model review, "
            "then rerun predictor and recovery analyses against reviewed labels."
        ),
    }
    assert_matrix_safe(payload)
    return payload


def build_matrix(root: Path) -> dict[str, Any]:
    return build_matrix_from_payloads(root)


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
    payload = build_matrix(args.repo_root.resolve())
    payload["runtime_seconds"] = round(time.time() - started, 4)
    assert_matrix_safe(payload)
    output_json = args.output_json or args.output_dir / SUMMARY_NAME
    output_tsv = args.output_tsv or args.output_dir / TSV_NAME
    write_json(output_json, payload)
    write_tsv(output_tsv, payload["consequence_rows"])
    print(
        json.dumps(
            {
                "ok": payload["ok"],
                "paper_claims_ready": payload["paper_claims_ready"],
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

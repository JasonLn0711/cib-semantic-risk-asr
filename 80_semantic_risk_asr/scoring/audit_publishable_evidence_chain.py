#!/usr/bin/env python3
"""Audit the repo against the postdoc publishable-evidence objective.

This is a requirement-to-evidence audit, not another experiment runner. It maps
the objective's steps 0-6 onto tracked aggregate evidence and keeps proxy-only
claims separate from paper-ready claims.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[2]
SCORING_DIR = SCRIPT_PATH.parent
if str(SCORING_DIR) not in sys.path:
    sys.path.insert(0, str(SCORING_DIR))

import check_evidence_chain_readiness as readiness  # noqa: E402


DEFAULT_OUTPUT_DIR = (
    REPO_ROOT / "70_experiments" / "runs" / "postdoc_evidence_chain_2026_05_25"
)
SUMMARY_NAME = "publishable_evidence_completion_summary.json"
TSV_NAME = "publishable_evidence_completion.tsv"

STATUS_ORDER = {
    "completed": 0,
    "proxy_completed": 1,
    "review_pending": 2,
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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "objective_id",
        "objective",
        "status",
        "paper_claim_status",
        "evidence",
        "result",
        "blocking_dependency",
        "next_action",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def assert_completion_safe(payload: Any) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    for token in SENSITIVE_TOKENS:
        if token in text:
            raise ValueError(f"sensitive token leaked into completion audit: {token}")


def by_requirement(readiness_payload: dict[str, Any]) -> dict[str, dict[str, str]]:
    return {
        str(row.get("requirement", "")): row
        for row in readiness_payload.get("readiness_rows", [])
        if isinstance(row, dict)
    }


def gate_status(readiness_payload: dict[str, Any], requirement: str) -> str:
    row = by_requirement(readiness_payload).get(requirement, {})
    return str(row.get("status", "missing"))


def objective_row(
    *,
    objective_id: str,
    objective: str,
    status: str,
    paper_claim_status: str,
    evidence: str,
    result: str,
    blocking_dependency: str,
    next_action: str,
) -> dict[str, str]:
    return {
        "objective_id": objective_id,
        "objective": objective,
        "status": status,
        "paper_claim_status": paper_claim_status,
        "evidence": evidence,
        "result": result,
        "blocking_dependency": blocking_dependency,
        "next_action": next_action,
    }


def objective_rows_from_payloads(
    *,
    readiness_payload: dict[str, Any],
    human_refresh: dict[str, Any],
    human_predictor: dict[str, Any],
) -> list[dict[str, str]]:
    migration = gate_status(readiness_payload, "migration and best-model selection checkpoint")
    smoke = gate_status(readiness_payload, "legacy-best load smoke tests")
    fixed_15 = gate_status(
        readiness_payload,
        "legacy best models join the fixed 15-row hypothesis contract",
    )
    bridge_15 = gate_status(
        readiness_payload,
        "CDS-ASR bridge over 15-row legacy-best hypotheses",
    )
    split_258 = gate_status(
        readiness_payload,
        "canonical 258-row six-model comparison with decision-risk metrics",
    )
    high_stakes = gate_status(
        readiness_payload,
        "selected-300 high-stakes CDS-ASR main experiment proxy",
    )
    metric_predictor_proxy = gate_status(
        readiness_payload,
        "WER/CER/SRES/CEIS predictor comparison on selected-300",
    )
    recovery_proxy = gate_status(readiness_payload, "five-condition recovery experiment")
    human_audit = gate_status(
        readiness_payload,
        "selected-300 human risk-atom audit completion",
    )
    predictor_review_complete = (
        human_predictor.get("ok")
        and human_predictor.get("status") == "review_complete"
        and human_predictor.get("pending_model_assessments") == 0
    )
    refresh_review_complete = (
        human_refresh.get("ok")
        and human_refresh.get("status") == "review_complete"
        and human_refresh.get("pending_rows") == 0
        and human_refresh.get("pending_model_assessments") == 0
    )

    main_status = "review_pending"
    main_result = (
        "Selected-300 proxy inputs, metric-predictor proxy, and refresh gate exist, "
        f"but human review is {human_refresh.get('reviewed_rows', 0)}/"
        f"{human_refresh.get('audit_rows', 30)} rows and "
        f"{human_refresh.get('reviewed_model_assessments', 0)}/"
        f"{human_refresh.get('model_assessments', 90)} model assessments."
    )
    main_paper_status = "not paper-ready"
    if (
        high_stakes in {"completed", "proxy_completed"}
        and metric_predictor_proxy in {"completed", "proxy_completed"}
        and human_audit == "completed"
        and predictor_review_complete
        and refresh_review_complete
    ):
        main_status = "completed"
        main_result = "Selected-300 main experiment has human-reviewed aggregate predictor evidence."
        main_paper_status = "human-reviewed evidence ready"

    rows = [
        objective_row(
            objective_id="0",
            objective="sealed migration and best-model checkpoint",
            status=migration,
            paper_claim_status="provenance evidence" if migration == "completed" else "not usable",
            evidence="70_experiments/registry.tsv; legacy import and best-model run records",
            result="Migration, pruning boundary, and best-model selection are registered."
            if migration == "completed"
            else "Checkpoint evidence is missing.",
            blocking_dependency="",
            next_action="Keep raw weights and predictions local; only commit aggregate evidence.",
        ),
        objective_row(
            objective_id="1",
            objective="legacy-best LoRA and partial-encoder load smoke tests",
            status=smoke,
            paper_claim_status="engineering gate only" if smoke == "completed" else "not usable",
            evidence="legacy-best smoke summary JSON files",
            result="Both legacy best models loaded one row with runtime, dtype, and cuDNN policy."
            if smoke == "completed"
            else "One or both smoke summaries are missing or incomplete.",
            blocking_dependency="",
            next_action="Use fixed 15-row and split gates only after smoke evidence remains valid.",
        ),
        objective_row(
            objective_id="2",
            objective="legacy best models join the fixed 15-row pilot",
            status=fixed_15,
            paper_claim_status="engineering gate only" if fixed_15 == "completed" else "not usable",
            evidence="legacy best 15-row validation JSON files",
            result="Both legacy best models validated against the same 15-row hypothesis contract."
            if fixed_15 == "completed"
            else "15-row validation evidence is incomplete.",
            blocking_dependency="",
            next_action="Use 15-row output only as a gate before split/high-stakes evidence.",
        ),
        objective_row(
            objective_id="3",
            objective="rerun CDS-ASR metric bridge instead of selecting by CER only",
            status=bridge_15,
            paper_claim_status="pilot evidence" if bridge_15 == "completed" else "not usable",
            evidence="janus_15_decision_stability_legacy_best/asr_cds_model_comparison.tsv",
            result="15-row bridge includes CER/WER, CEIS, downstream mismatch, and high-risk miss evidence."
            if bridge_15 == "completed"
            else "15-row CDS bridge evidence is missing.",
            blocking_dependency="",
            next_action="Keep the CER-alone contrast in the paper framing; do not overclaim from 15 rows.",
        ),
        objective_row(
            objective_id="4",
            objective="canonical janus_165_v1 258-row test split comparison",
            status=split_258,
            paper_claim_status="proxy evidence; not human-reviewed risk-atom evidence",
            evidence="janus_258_test_split_asr_cds_proxy summary and comparison TSV",
            result="Six-model 258-row aggregate includes paper-facing zh metrics and decision-risk proxy fields."
            if split_258 == "proxy_completed"
            else "258-row six-model comparison is incomplete.",
            blocking_dependency="human-reviewed risk-atom labels before paper-grade risk claims",
            next_action="Do not convert proxy risk-atom counts into formal human-reviewed conclusions.",
        ),
        objective_row(
            objective_id="5",
            objective="selected-300 high-stakes main experiment",
            status=main_status,
            paper_claim_status=main_paper_status,
            evidence=(
                "janus_300_high_stakes_cds_proxy_2026_05_25/summary.json; "
                "janus_300_high_stakes_metric_predictor_proxy_2026_05_25/metric_predictor_summary.json; "
                "human_audit_refresh_summary.json; human_audit_predictor_summary.json"
            ),
            result=main_result,
            blocking_dependency="selected-300 local human risk-atom audit completion",
            next_action="Fill the local audit sheet, rerun refresh with --require-complete, then use human-reviewed predictor outputs.",
        ),
        objective_row(
            objective_id="6",
            objective="five-condition recovery experiment",
            status=recovery_proxy,
            paper_claim_status="proxy engineering evidence until human labels confirm outcomes",
            evidence="janus_300_high_stakes_recovery_proxy_2026_05_25/summary.json",
            result="Recovery proxy shows CEIS action reduces high-risk missed and critical miss."
            if recovery_proxy == "proxy_completed"
            else "Recovery comparison evidence is missing or incomplete.",
            blocking_dependency="human-reviewed labels and post-review recovery re-evaluation",
            next_action="After human review, rerun recovery using reviewed labels before paper-grade intervention claims.",
        ),
    ]
    return rows


def build_completion_audit(root: Path) -> dict[str, Any]:
    readiness_payload = readiness.build_readiness(root)
    audit_dir = root / "70_experiments" / "runs" / "janus_300_high_stakes_human_audit_selection_2026_05_25"
    human_refresh = read_json(audit_dir / "human_audit_refresh_summary.json")
    human_predictor = read_json(audit_dir / "human_audit_predictor_summary.json")
    rows = objective_rows_from_payloads(
        readiness_payload=readiness_payload,
        human_refresh=human_refresh,
        human_predictor=human_predictor,
    )
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    blocking_rows = [
        {
            "objective_id": row["objective_id"],
            "objective": row["objective"],
            "status": row["status"],
            "blocking_dependency": row["blocking_dependency"],
            "next_action": row["next_action"],
        }
        for row in rows
        if row["status"] != "completed" or row["paper_claim_status"].startswith("proxy")
    ]
    payload = {
        "ok": all(STATUS_ORDER.get(row["status"], 99) <= STATUS_ORDER["review_pending"] for row in rows),
        "publishable_ready": all(row["status"] == "completed" for row in rows)
        and all(not row["paper_claim_status"].startswith("proxy") for row in rows),
        "status_counts": dict(sorted(counts.items())),
        "completion_rows": rows,
        "blocking_or_proxy_items": blocking_rows,
        "first_principle_decision": (
            "Do not spend more GPU time to chase ASR fine-tuning until the selected-300 "
            "human audit converts proxy CDS-ASR evidence into paper-grade evidence."
        ),
        "next_decision": (
            "Complete selected-300 human row/model review, run the refresh gate with "
            "--require-complete, then rerun human-reviewed predictor and recovery claims."
        ),
    }
    assert_completion_safe(payload)
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
    payload = build_completion_audit(args.repo_root.resolve())
    payload["runtime_seconds"] = round(time.time() - started, 4)
    assert_completion_safe(payload)
    output_json = args.output_json or args.output_dir / SUMMARY_NAME
    output_tsv = args.output_tsv or args.output_dir / TSV_NAME
    write_json(output_json, payload)
    write_tsv(output_tsv, payload["completion_rows"])
    print(
        json.dumps(
            {
                "ok": payload["ok"],
                "publishable_ready": payload["publishable_ready"],
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

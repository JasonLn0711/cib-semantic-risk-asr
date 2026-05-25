#!/usr/bin/env python3
"""Audit the original postdoc roadmap against tracked aggregate evidence.

This checker is intentionally narrower than an experiment runner. It maps the
user-facing 0-6 roadmap plus the paper-facing human-review gate to current
repo-safe evidence, while keeping proxy evidence separate from publishable
evidence.
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
SUMMARY_NAME = "postdoc_roadmap_completion_summary.json"
TSV_NAME = "postdoc_roadmap_completion.tsv"

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

STATUS_ORDER = {
    "completed": 0,
    "proxy_completed": 1,
    "review_pending": 2,
    "blocked": 3,
    "missing": 4,
    "failed": 5,
}

TSV_FIELDS = [
    "roadmap_step_id",
    "roadmap_step",
    "status",
    "paper_claim_status",
    "authoritative_evidence",
    "current_evidence_result",
    "blocking_dependency",
    "next_action",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


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


def assert_roadmap_safe(payload: Any) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    for token in SENSITIVE_TOKENS:
        if token in text:
            raise ValueError(f"sensitive token leaked into roadmap audit: {token}")


def by_objective_id(completion: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("objective_id", "")): row
        for row in completion.get("completion_rows", [])
        if isinstance(row, dict)
    }


def roadmap_row(
    *,
    roadmap_step_id: str,
    roadmap_step: str,
    status: str,
    paper_claim_status: str,
    authoritative_evidence: str,
    current_evidence_result: str,
    blocking_dependency: str,
    next_action: str,
) -> dict[str, str]:
    return {
        "roadmap_step_id": roadmap_step_id,
        "roadmap_step": roadmap_step,
        "status": status,
        "paper_claim_status": paper_claim_status,
        "authoritative_evidence": authoritative_evidence,
        "current_evidence_result": current_evidence_result,
        "blocking_dependency": blocking_dependency,
        "next_action": next_action,
    }


def row_from_completion(
    *,
    completion_rows: dict[str, dict[str, Any]],
    objective_id: str,
    roadmap_step_id: str,
    roadmap_step: str,
) -> dict[str, str]:
    source = completion_rows.get(objective_id, {})
    status = str(source.get("status") or "missing")
    return roadmap_row(
        roadmap_step_id=roadmap_step_id,
        roadmap_step=roadmap_step,
        status=status,
        paper_claim_status=str(source.get("paper_claim_status") or "not usable"),
        authoritative_evidence=str(source.get("evidence") or ""),
        current_evidence_result=str(source.get("result") or ""),
        blocking_dependency=str(source.get("blocking_dependency") or ""),
        next_action=str(source.get("next_action") or ""),
    )


def review_counts(
    *,
    human_refresh: dict[str, Any],
    response_closeout: dict[str, Any],
) -> dict[str, Any]:
    timing = (
        response_closeout.get("review_timing")
        if isinstance(response_closeout.get("review_timing"), dict)
        else {}
    )
    return {
        "selected_300_rows_reviewed": int(human_refresh.get("reviewed_rows") or 0),
        "selected_300_rows_total": int(human_refresh.get("audit_rows") or 30),
        "selected_300_model_assessments_reviewed": int(
            human_refresh.get("reviewed_model_assessments") or 0
        ),
        "selected_300_model_assessments_total": int(
            human_refresh.get("model_assessments") or 90
        ),
        "current_packet_rows_pending": int(response_closeout.get("pending_rows_in_response") or 0),
        "current_packet_rows_total": int(response_closeout.get("rows_in_batch") or 0),
        "current_packet_model_assessments_pending": int(
            response_closeout.get("pending_model_assessments_in_response") or 0
        ),
        "current_packet_model_assessments_total": int(
            response_closeout.get("pending_model_assessments_in_response") or 0
        )
        + int(response_closeout.get("reviewed_model_assessments_in_response") or 0),
        "current_packet_timing_rows_with": int(timing.get("rows_with_timing") or 0),
        "current_packet_timing_rows_missing": int(timing.get("rows_missing_timing") or 0),
        "current_packet_timing_required": bool(response_closeout.get("require_timing")),
        "response_closeout_status": str(response_closeout.get("status") or "missing"),
        "latest_apply_status": str(response_closeout.get("latest_apply_status") or ""),
    }


def post_review_gate_row(
    *,
    post_review: dict[str, Any],
    human_refresh: dict[str, Any],
    response_closeout: dict[str, Any],
) -> dict[str, str]:
    counts = review_counts(human_refresh=human_refresh, response_closeout=response_closeout)
    ready = bool(post_review.get("ok")) and post_review.get("status") == "post_review_evidence_ready"
    status = "completed" if ready else "blocked"
    blocker_keys = ", ".join(str(item) for item in post_review.get("blocker_keys", []))
    result = (
        "Post-review evidence is ready; response closeout, refresh, predictor, "
        "publishable, consequence, and recovery gates are complete."
        if ready
        else (
            f"Post-review evidence remains blocked: closeout={post_review.get('closeout_ready')}, "
            f"refresh={post_review.get('refresh_complete')}, "
            f"predictor={post_review.get('predictor_complete')}, "
            f"publishable={post_review.get('publishable_ready')}, "
            f"consequence={post_review.get('consequence_ready')}, "
            f"human_recovery={post_review.get('recovery_human_ready')}. "
            f"Current selected-300 review is {counts['selected_300_rows_reviewed']}/"
            f"{counts['selected_300_rows_total']} rows and "
            f"{counts['selected_300_model_assessments_reviewed']}/"
            f"{counts['selected_300_model_assessments_total']} model assessments; "
            f"current packet pending {counts['current_packet_rows_pending']}/"
            f"{counts['current_packet_rows_total']} rows and "
            f"{counts['current_packet_model_assessments_pending']}/"
            f"{counts['current_packet_model_assessments_total']} model assessments, "
            f"with {counts['current_packet_timing_rows_missing']} timing rows missing."
        )
    )
    return roadmap_row(
        roadmap_step_id="7_human_review_and_publishable_evidence_gate",
        roadmap_step="convert proxy CDS-ASR evidence into paper-ready human-reviewed evidence",
        status=status,
        paper_claim_status="paper-ready" if ready else "not paper-ready",
        authoritative_evidence=(
            "human_audit_response_closeout_summary.json; "
            "human_audit_refresh_summary.json; human_audit_predictor_summary.json; "
            "human_audit_post_review_evidence_summary.json; "
            "evidence_chain_readiness_summary.json; "
            "publishable_evidence_completion_summary.json; "
            "consequence_evidence_matrix_summary.json"
        ),
        current_evidence_result=result,
        blocking_dependency=blocker_keys,
        next_action=str(
            post_review.get("next_concrete_action")
            or "Complete selected-300 row/model/timing fields, then rerun closeout/write/refresh."
        ),
    )


def candidate_gate(candidate_summary: dict[str, Any]) -> dict[str, Any]:
    stopped = candidate_summary.get("blocked_or_stopped", [])
    stopped_rows = [item for item in stopped if isinstance(item, dict)]
    return {
        "available": bool(candidate_summary),
        "ok": bool(candidate_summary.get("ok")),
        "strict_locale_policy": candidate_summary.get("strict_locale_policy", ""),
        "promotion_decision": candidate_summary.get("promotion_decision", ""),
        "blocked_or_stopped_count": len(stopped_rows),
        "blocked_or_stopped_runs": [
            {
                "run_id": item.get("run_id", ""),
                "model": item.get("model", ""),
                "status": item.get("status", ""),
                "decision": item.get("decision", ""),
            }
            for item in stopped_rows
        ],
    }


def build_roadmap_audit_from_payloads(
    *,
    readiness: dict[str, Any],
    completion: dict[str, Any],
    consequence: dict[str, Any],
    post_review: dict[str, Any],
    human_refresh: dict[str, Any],
    human_predictor: dict[str, Any],
    response_closeout: dict[str, Any],
    candidate_summary: dict[str, Any],
) -> dict[str, Any]:
    completion_rows = by_objective_id(completion)
    rows = [
        row_from_completion(
            completion_rows=completion_rows,
            objective_id="0",
            roadmap_step_id="0_state_checkpoint",
            roadmap_step="seal migration, best-model selection, gitignore, and run records",
        ),
        row_from_completion(
            completion_rows=completion_rows,
            objective_id="1",
            roadmap_step_id="1_best_model_load_smoke",
            roadmap_step="load-smoke LoRA and partial-encoder legacy best models",
        ),
        row_from_completion(
            completion_rows=completion_rows,
            objective_id="2",
            roadmap_step_id="2_legacy_best_15_row_pilot",
            roadmap_step="connect legacy best models to the fixed 15-row hypothesis contract",
        ),
        row_from_completion(
            completion_rows=completion_rows,
            objective_id="3",
            roadmap_step_id="3_cds_asr_metric_bridge",
            roadmap_step="rerun CDS-ASR bridge and avoid CER-only model selection",
        ),
        row_from_completion(
            completion_rows=completion_rows,
            objective_id="4",
            roadmap_step_id="4_canonical_258_test_split",
            roadmap_step="run canonical janus_165_v1 258-row comparison with decision-risk metrics",
        ),
        row_from_completion(
            completion_rows=completion_rows,
            objective_id="5",
            roadmap_step_id="5_high_stakes_300_main_experiment",
            roadmap_step="make selected-300 high-stakes expansion the main experiment",
        ),
        row_from_completion(
            completion_rows=completion_rows,
            objective_id="6",
            roadmap_step_id="6_recovery_experiment",
            roadmap_step="evaluate five-condition recovery policies and safety tradeoffs",
        ),
        post_review_gate_row(
            post_review=post_review,
            human_refresh=human_refresh,
            response_closeout=response_closeout,
        ),
    ]
    counts: dict[str, int] = {}
    for item in rows:
        status = item["status"]
        counts[status] = counts.get(status, 0) + 1

    publishable_ready = bool(completion.get("publishable_ready"))
    paper_ready = bool(readiness.get("paper_ready"))
    consequence_ready = bool(consequence.get("paper_claims_ready"))
    post_review_ready = bool(post_review.get("ok")) and post_review.get("status") == "post_review_evidence_ready"
    human_review_complete = (
        human_refresh.get("ok")
        and human_refresh.get("status") == "review_complete"
        and human_refresh.get("pending_rows") == 0
        and human_refresh.get("pending_model_assessments") == 0
        and human_predictor.get("status") == "review_complete"
    )
    roadmap_complete = all(row["status"] == "completed" for row in rows) and all(
        [
            publishable_ready,
            paper_ready,
            consequence_ready,
            post_review_ready,
            human_review_complete,
        ]
    )
    blockers = [
        {
            "roadmap_step_id": row["roadmap_step_id"],
            "status": row["status"],
            "blocking_dependency": row["blocking_dependency"],
            "next_action": row["next_action"],
        }
        for row in rows
        if row["status"] != "completed" or row["paper_claim_status"].startswith("proxy")
    ]
    payload = {
        "ok": True,
        "roadmap_complete": roadmap_complete,
        "publishable_ready": publishable_ready,
        "paper_ready": paper_ready,
        "post_review_evidence_ready": post_review_ready,
        "consequence_paper_claims_ready": consequence_ready,
        "human_review_complete": human_review_complete,
        "blocking_gate": "none" if roadmap_complete else "selected_300_human_review_and_post_review_refresh",
        "status_counts": dict(sorted(counts.items())),
        "current_review_counts": review_counts(
            human_refresh=human_refresh,
            response_closeout=response_closeout,
        ),
        "candidate_gate": candidate_gate(candidate_summary),
        "reference_transcript_policy": REFERENCE_TRANSCRIPT_POLICY,
        "remaining_review_scope": REMAINING_REVIEW_SCOPE,
        "roadmap_rows": rows,
        "blocking_or_proxy_items": blockers,
        "first_principle_decision": (
            "The repo should now optimize for a publishable consequence evidence "
            "chain, not a longer ASR leaderboard. New ASR candidates stop at the "
            "locale/runtime gate unless they change the CDS-ASR paper evidence."
        ),
        "next_decision": (
            "Close the selected-300 row/model/timing response gate, "
            "write/refresh aggregate human review evidence, rerun predictor and "
            "recovery analyses, then rerun this roadmap audit before claiming "
            "the objective is complete."
        ),
    }
    assert_roadmap_safe(payload)
    return payload


def build_roadmap_audit(root: Path) -> dict[str, Any]:
    postdoc_dir = root / "70_experiments" / "runs" / "postdoc_evidence_chain_2026_05_25"
    audit_dir = (
        root
        / "70_experiments"
        / "runs"
        / "janus_300_high_stakes_human_audit_selection_2026_05_25"
    )
    return build_roadmap_audit_from_payloads(
        readiness=read_json(postdoc_dir / "evidence_chain_readiness_summary.json"),
        completion=read_json(postdoc_dir / "publishable_evidence_completion_summary.json"),
        consequence=read_json(postdoc_dir / "consequence_evidence_matrix_summary.json"),
        post_review=read_json(audit_dir / "human_audit_post_review_evidence_summary.json"),
        human_refresh=read_json(audit_dir / "human_audit_refresh_summary.json"),
        human_predictor=read_json(audit_dir / "human_audit_predictor_summary.json"),
        response_closeout=read_json(audit_dir / "human_audit_response_closeout_summary.json"),
        candidate_summary=read_json(
            root
            / "70_experiments"
            / "runs"
            / "asr_candidate_15_row_extension_2026_05_26"
            / "summary.json"
        ),
    )


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
    payload = build_roadmap_audit(args.repo_root.resolve())
    payload["runtime_seconds"] = round(time.time() - started, 4)
    assert_roadmap_safe(payload)
    output_json = args.output_json or args.output_dir / SUMMARY_NAME
    output_tsv = args.output_tsv or args.output_dir / TSV_NAME
    write_json(output_json, payload)
    write_tsv(output_tsv, payload["roadmap_rows"])
    print(
        json.dumps(
            {
                "ok": payload["ok"],
                "roadmap_complete": payload["roadmap_complete"],
                "publishable_ready": payload["publishable_ready"],
                "paper_ready": payload["paper_ready"],
                "post_review_evidence_ready": payload["post_review_evidence_ready"],
                "blocking_gate": payload["blocking_gate"],
                "output_json": str(output_json),
                "output_tsv": str(output_tsv),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

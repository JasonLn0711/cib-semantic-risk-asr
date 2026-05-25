#!/usr/bin/env python3
"""Evaluate recovery policies against completed human-audit labels.

The input audit sheet is local-only and may contain transcripts. Tracked
outputs are aggregate-only; per-sample detail must stay under ignored
artifacts.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[2]
ANNOTATION_DIR = REPO_ROOT / "80_semantic_risk_asr" / "annotation"
RECOVERY_DIR = SCRIPT_PATH.parent
for import_path in (ANNOTATION_DIR, RECOVERY_DIR):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

import evaluate_recovery_policies as recovery  # noqa: E402
import validate_human_risk_atom_audit as validation  # noqa: E402


DEFAULT_RUN_DIR = (
    REPO_ROOT
    / "70_experiments"
    / "runs"
    / "janus_300_high_stakes_recovery_human_reviewed_2026_05_26"
)
DEFAULT_AUDIT_SHEET = (
    REPO_ROOT
    / "70_experiments"
    / "runs"
    / "janus_300_high_stakes_human_audit_selection_2026_05_25"
    / "artifacts"
    / "human_risk_atom_audit_sheet.tsv"
)
POLICIES = [
    "no_recovery",
    "confidence_only_trigger",
    "sres_triggered_recovery",
    "ceis_triggered_conservative_action",
    "ceis_ensemble_arbitration",
]
COMPARISON_FIELDS = [
    "policy",
    "rows",
    "unsafe_downrouting_count",
    "unsafe_downrouting_rate",
    "high_risk_missed_count",
    "high_risk_missed_rate",
    "critical_miss_count",
    "critical_miss_rate",
    "over_escalation_count",
    "over_escalation_rate",
    "triggered_count",
    "recovery_budget_rate",
    "machine_abstention_count",
    "machine_abstention_rate",
    "unsafe_downrouting_reduction_vs_no_recovery",
    "unsafe_downrouting_gain",
    "high_risk_missed_reduction_vs_no_recovery",
    "high_risk_missed_gain",
    "conservative_escalation_cost_count",
    "exact_recovered_error_count",
]
SENSITIVE_TOKENS = {
    "audio_id",
    "sample_id",
    "reference_text",
    "hypothesis_text",
    "asr_hypotheses_json",
    "reviewer_model_assessments_json",
    "reviewer_notes",
    "reviewer_verified_transcript",
    "PRIVATE_",
}


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), list(reader)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def parse_json(value: str) -> Any:
    if not value.strip():
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def split_atoms(value: str) -> list[str]:
    atoms = []
    for item in (value or "").replace(";", ",").replace("|", ",").split(","):
        atom = item.strip()
        if atom and atom.lower() != "none":
            atoms.append(atom)
    return atoms


def first_atom(*values: str) -> str:
    for value in values:
        atoms = split_atoms(value)
        if atoms:
            return atoms[0]
    return ""


def assessment_complete(item: dict[str, Any]) -> bool:
    return validation.model_review_complete(item)


def assert_summary_safe(payload: Any) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    for token in SENSITIVE_TOKENS:
        if token in text:
            raise ValueError(f"sensitive token leaked into human-reviewed recovery summary: {token}")


def build_samples(rows: list[dict[str, str]]) -> tuple[list[recovery.SampleSignals], dict[str, Any]]:
    samples: list[recovery.SampleSignals] = []
    counters: Counter[str] = Counter()
    label_counts: Counter[str] = Counter()
    decision_change_counts: Counter[str] = Counter()

    for row_index, row in enumerate(rows, start=1):
        reference_label = row.get("reviewer_semantic_risk_label", "")
        label_counts[reference_label] += 1
        hypotheses = parse_json(row.get("asr_hypotheses_json", ""))
        assessments = parse_json(row.get("reviewer_model_assessments_json", ""))
        if not isinstance(hypotheses, list) or not isinstance(assessments, list):
            counters["invalid_json_bundle"] += 1
            continue

        assessment_by_run = {
            str(item.get("asr_run_id", "")): item
            for item in assessments
            if isinstance(item, dict) and item.get("asr_run_id")
        }
        labels = [
            str(item.get("asr_label", ""))
            for item in hypotheses
            if isinstance(item, dict) and item.get("asr_label")
        ]
        levels = [recovery.label_level(label) for label in labels] or [0]
        for hypothesis in hypotheses:
            if not isinstance(hypothesis, dict):
                counters["invalid_hypothesis_item"] += 1
                continue
            run_id = str(hypothesis.get("asr_run_id", "") or "unknown")
            assessment = assessment_by_run.get(run_id, {})
            if not assessment_complete(assessment):
                counters["pending_model_assessment_skipped"] += 1
                continue
            decision_change = str(
                assessment.get("reviewer_would_asr_error_change_decision", "")
            )
            decision_change_counts[decision_change] += 1
            atom = str(hypothesis.get("ceis_top_atom", "")) or first_atom(
                str(assessment.get("reviewer_critical_atoms", "")),
                row.get("reviewer_critical_atoms", ""),
                row.get("reviewer_risk_atoms", ""),
            )
            audio_id = row.get("audio_id", f"row_{row_index}")
            samples.append(
                recovery.SampleSignals(
                    sample_id=f"reviewed_row_{row_index}__{recovery.label_for_level(recovery.label_level(reference_label))}__{run_id}",
                    audio_id=audio_id,
                    asr_run_id=run_id,
                    reference_label=reference_label,
                    asr_label=str(hypothesis.get("asr_label", "")),
                    sres_total=round(as_float(hypothesis.get("sres_total")), 4),
                    ceis=round(as_float(hypothesis.get("ceis_max")), 4),
                    ceis_risk_atom_type=atom,
                    ensemble_min_level=min(levels),
                    ensemble_max_level=max(levels),
                    ensemble_high_risk_votes=sum(1 for level in levels if level >= 2),
                    ensemble_model_count=len(levels),
                    confidence=None,
                    review_mode="human_reviewed",
                )
            )
            counters["human_reviewed_model_samples"] += 1

    metadata = {
        "reviewed_row_count": len(rows),
        "human_reviewed_model_samples": counters["human_reviewed_model_samples"],
        "skipped_counts": {
            key: value for key, value in sorted(counters.items()) if key != "human_reviewed_model_samples"
        },
        "reviewer_semantic_label_counts": dict(sorted(label_counts.items())),
        "model_decision_change_counts": dict(sorted(decision_change_counts.items())),
    }
    return samples, metadata


def evaluate_samples(
    samples: list[recovery.SampleSignals],
    *,
    confidence_threshold: float,
    sres_threshold: float,
    ceis_threshold: float,
    ensemble_mode: str,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    detail_rows: list[dict[str, Any]] = []
    baseline_summary: dict[str, Any] | None = None
    summaries: dict[str, dict[str, Any]] = {}
    for policy in POLICIES:
        rows = [
            recovery.apply_policy(
                sample,
                policy,
                confidence_threshold=confidence_threshold,
                sres_threshold=sres_threshold,
                ceis_threshold=ceis_threshold,
                ensemble_mode=ensemble_mode,
            )
            for sample in samples
        ]
        if policy == "no_recovery":
            baseline_summary = recovery.summarize_policy(rows)
            summaries[policy] = baseline_summary
        else:
            summaries[policy] = recovery.summarize_policy(rows, baseline_summary)
        detail_rows.extend(rows)
    return summaries, detail_rows


def pending_payload(
    *,
    validation_payload: dict[str, Any],
    started: float,
) -> dict[str, Any]:
    payload = {
        "ok": False,
        "status": validation_payload.get("status", "validation_failed"),
        "evidence_mode": "human_reviewed_pending",
        "human_reviewed": False,
        "review_status": validation_payload.get("status", ""),
        "input_boundary": "local transcript-bearing audit sheet; do not commit input",
        "output_boundary": "aggregate-only human-reviewed recovery readiness summary",
        "audit_rows": validation_payload.get("audit_rows", 0),
        "reviewed_rows": validation_payload.get("reviewed_rows", 0),
        "pending_rows": validation_payload.get("pending_rows", 0),
        "model_assessments": validation_payload.get("model_assessments", 0),
        "reviewed_model_assessments": validation_payload.get("reviewed_model_assessments", 0),
        "pending_model_assessments": validation_payload.get("pending_model_assessments", 0),
        "policies": {},
        "blocker_keys": ["human_review_incomplete"],
        "next_action": (
            "Complete selected-300 row/model/timing review, refresh human audit "
            "aggregates, then rerun this human-reviewed recovery evaluator."
        ),
        "runtime_seconds": round(time.time() - started, 4),
    }
    assert_summary_safe(payload)
    return payload


def build_human_reviewed_recovery(
    *,
    audit_sheet: Path,
    expected_rows: int | None,
    allow_pending_summary: bool,
    confidence_threshold: float,
    sres_threshold: float,
    ceis_threshold: float,
    ensemble_mode: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], int]:
    started = time.time()
    fieldnames, rows = read_tsv(audit_sheet)
    validation_payload = validation.validate_rows(
        fieldnames,
        rows,
        require_complete=False,
        expected_rows=expected_rows,
    )
    complete = (
        validation_payload.get("ok") is True
        and validation_payload.get("status") == "review_complete"
        and int(validation_payload.get("pending_rows") or 0) == 0
        and int(validation_payload.get("pending_model_assessments") or 0) == 0
    )
    if not complete:
        payload = pending_payload(validation_payload=validation_payload, started=started)
        return payload, [], 0 if allow_pending_summary else 1

    samples, metadata = build_samples(rows)
    summaries, detail_rows = evaluate_samples(
        samples,
        confidence_threshold=confidence_threshold,
        sres_threshold=sres_threshold,
        ceis_threshold=ceis_threshold,
        ensemble_mode=ensemble_mode,
    )
    payload = {
        "ok": True,
        "status": "human_reviewed_complete",
        "evidence_mode": "human_reviewed",
        "human_reviewed": True,
        "review_status": "human_reviewed_complete",
        "input_boundary": "local transcript-bearing audit sheet; do not commit input",
        "output_boundary": "aggregate-only human-reviewed recovery evidence",
        "thresholds": {
            "confidence_threshold": confidence_threshold,
            "sres_threshold": sres_threshold,
            "ceis_threshold": ceis_threshold,
            "ensemble_mode": ensemble_mode,
        },
        "audit_rows": validation_payload.get("audit_rows", 0),
        "reviewed_rows": validation_payload.get("reviewed_rows", 0),
        "model_assessments": validation_payload.get("model_assessments", 0),
        "reviewed_model_assessments": validation_payload.get("reviewed_model_assessments", 0),
        "sample_count": len(samples),
        **metadata,
        "policies": summaries,
        "notes": [
            "Recovery outcomes are scored against reviewer semantic risk labels.",
            "CEIS-triggered policies use reviewed critical atoms when model CEIS atoms are absent.",
            "Per-sample detail remains ignored because it can contain row keys.",
        ],
        "runtime_seconds": round(time.time() - started, 4),
    }
    assert_summary_safe(payload)
    return payload, detail_rows, 0


def comparison_rows(policies: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"policy": policy, **payload} for policy, payload in policies.items()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-sheet", type=Path, default=DEFAULT_AUDIT_SHEET)
    parser.add_argument("--expected-rows", type=int, default=30)
    parser.add_argument("--output-summary-json", type=Path, default=DEFAULT_RUN_DIR / "summary.json")
    parser.add_argument("--output-comparison-tsv", type=Path, default=DEFAULT_RUN_DIR / "policy_comparison.tsv")
    parser.add_argument("--output-detail-tsv", type=Path)
    parser.add_argument("--allow-pending-summary", action="store_true")
    parser.add_argument("--confidence-threshold", type=float, default=0.70)
    parser.add_argument("--sres-threshold", type=float, default=20.0)
    parser.add_argument("--ceis-threshold", type=float, default=5.0)
    parser.add_argument("--ensemble-mode", choices=("priority", "max"), default="priority")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload, detail_rows, exit_code = build_human_reviewed_recovery(
        audit_sheet=args.audit_sheet,
        expected_rows=args.expected_rows,
        allow_pending_summary=args.allow_pending_summary,
        confidence_threshold=args.confidence_threshold,
        sres_threshold=args.sres_threshold,
        ceis_threshold=args.ceis_threshold,
        ensemble_mode=args.ensemble_mode,
    )
    write_json(args.output_summary_json, payload)
    if payload.get("policies"):
        write_tsv(
            args.output_comparison_tsv,
            comparison_rows(payload["policies"]),
            COMPARISON_FIELDS,
        )
    if args.output_detail_tsv and detail_rows:
        detail_fields = [
            "sample_id",
            "audio_id",
            "asr_run_id",
            "policy",
            "reference_label",
            "asr_label",
            "final_label",
            "triggered",
            "machine_abstained",
            "recovery_action",
            "sres_total",
            "ceis",
            "ceis_risk_atom_type",
            "ensemble_min_label",
            "ensemble_max_label",
            "ensemble_high_risk_votes",
            "ensemble_model_count",
            "confidence",
            "review_mode",
        ]
        write_tsv(args.output_detail_tsv, detail_rows, detail_fields)
    print(
        json.dumps(
            {
                "ok": payload["ok"],
                "status": payload["status"],
                "evidence_mode": payload["evidence_mode"],
                "sample_count": payload.get("sample_count", 0),
                "output_summary": str(args.output_summary_json),
            },
            ensure_ascii=False,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

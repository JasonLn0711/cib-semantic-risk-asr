#!/usr/bin/env python3
"""Summarize reviewed human risk-atom audit sheets.

The input audit sheet is local-only and may contain audio IDs, transcripts, ASR
hypotheses, and reviewer notes. This script writes aggregate-only outputs that
are safe to track in git.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REQUIRED_REVIEW_FIELDS = [
    "reviewer_semantic_risk_label",
    "reviewer_risk_atoms",
    "reviewer_critical_atoms",
    "reviewer_asr_confusion_terms",
    "reviewer_would_asr_error_change_decision",
    "reviewer_decision_change_reason",
    "reviewer_expected_safe_action",
    "reviewer_annotation_confidence",
]

SENSITIVE_FIELDS = {
    "audio_id",
    "sample_id",
    "reference_text",
    "hypothesis_text",
    "asr_hypotheses_json",
    "reviewer_model_assessments_json",
    "reviewer_verified_transcript",
    "reviewer_notes",
}

VALID_DECISION_CHANGE = {"yes", "no", "uncertain"}


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def split_atoms(value: str) -> list[str]:
    atoms = []
    for item in value.replace(";", ",").replace("|", ",").split(","):
        atom = item.strip()
        if atom and atom.lower() != "none":
            atoms.append(atom)
    return atoms


def parse_json_field(value: str) -> Any:
    if not value.strip():
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def reviewed(row: dict[str, str]) -> bool:
    return all((row.get(field) or "").strip() for field in REQUIRED_REVIEW_FIELDS)


def missing_field_counts(rows: list[dict[str, str]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        for field in REQUIRED_REVIEW_FIELDS:
            if not (row.get(field) or "").strip():
                counts[field] += 1
    return counts


def malformed_counts(rows: list[dict[str, str]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        decision_change = (row.get("reviewer_would_asr_error_change_decision") or "").strip()
        if decision_change and decision_change not in VALID_DECISION_CHANGE:
            counts["invalid_reviewer_would_asr_error_change_decision"] += 1
        hypotheses = parse_json_field(row.get("asr_hypotheses_json", ""))
        if hypotheses is not None and not isinstance(hypotheses, list):
            counts["invalid_asr_hypotheses_json"] += 1
        risk_signal = parse_json_field(row.get("risk_signal_json", ""))
        if risk_signal is not None and not isinstance(risk_signal, dict):
            counts["invalid_risk_signal_json"] += 1
        model_assessments = parse_json_field(row.get("reviewer_model_assessments_json", ""))
        if model_assessments is not None and not isinstance(model_assessments, list):
            counts["invalid_reviewer_model_assessments_json"] += 1
    return counts


def iter_model_assessments(row: dict[str, str]) -> list[dict[str, Any]]:
    value = parse_json_field(row.get("reviewer_model_assessments_json", ""))
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def model_assessment_reviewed(item: dict[str, Any]) -> bool:
    return all(
        str(item.get(field, "")).strip()
        for field in [
            "reviewer_would_asr_error_change_decision",
            "reviewer_critical_atoms",
            "reviewer_expected_safe_action",
            "reviewer_annotation_confidence",
        ]
    )


def model_assessment_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    total = reviewed_count = malformed = 0
    for row in rows:
        assessments = iter_model_assessments(row)
        total += len(assessments)
        for item in assessments:
            decision_change = str(
                item.get("reviewer_would_asr_error_change_decision", "")
            ).strip()
            if decision_change and decision_change not in VALID_DECISION_CHANGE:
                malformed += 1
            if model_assessment_reviewed(item):
                reviewed_count += 1
    return {
        "model_assessments": total,
        "reviewed_model_assessments": reviewed_count,
        "pending_model_assessments": total - reviewed_count,
        "malformed_model_assessments": malformed,
    }


def summarize_completion(rows: list[dict[str, str]]) -> dict[str, Any]:
    reviewed_rows = [row for row in rows if reviewed(row)]
    missing = missing_field_counts(rows)
    malformed = malformed_counts(rows)
    model_counts = model_assessment_counts(rows)
    status = "review_complete" if len(reviewed_rows) == len(rows) and not malformed else "review_pending"
    if reviewed_rows and len(reviewed_rows) != len(rows):
        status = "partial_review"
    if malformed or model_counts["malformed_model_assessments"]:
        status = "review_needs_cleanup"
    return {
        "status": status,
        "audit_rows": len(rows),
        "reviewed_rows": len(reviewed_rows),
        "pending_rows": len(rows) - len(reviewed_rows),
        **model_counts,
        "missing_required_field_counts": dict(sorted(missing.items())),
        "malformed_field_counts": dict(sorted(malformed.items())),
    }


def summarize_selection(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_stratum: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_stratum[row.get("selection_stratum", "") or "unknown"].append(row)
    result = []
    for stratum, group in sorted(by_stratum.items()):
        reviewed_group = [row for row in group if reviewed(row)]
        result.append(
            {
                "selection_stratum": stratum,
                "audit_rows": len(group),
                "reviewed_rows": len(reviewed_group),
                "decision_change_yes_count": sum(
                    (row.get("reviewer_would_asr_error_change_decision") or "").strip()
                    == "yes"
                    for row in reviewed_group
                ),
                "decision_change_uncertain_count": sum(
                    (row.get("reviewer_would_asr_error_change_decision") or "").strip()
                    == "uncertain"
                    for row in reviewed_group
                ),
                "confidence_low_count": sum(
                    (row.get("reviewer_annotation_confidence") or "").strip() == "low"
                    for row in reviewed_group
                ),
            }
        )
    return result


def summarize_human_atoms(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    total_counts: Counter[str] = Counter()
    critical_counts: Counter[str] = Counter()
    decision_change_counts: Counter[str] = Counter()
    reviewed_rows = [row for row in rows if reviewed(row)]
    for row in reviewed_rows:
        decision_change = (row.get("reviewer_would_asr_error_change_decision") or "").strip()
        atoms = split_atoms(row.get("reviewer_risk_atoms", ""))
        critical_atoms = split_atoms(row.get("reviewer_critical_atoms", ""))
        for atom in atoms:
            total_counts[atom] += 1
        for atom in critical_atoms:
            critical_counts[atom] += 1
            if decision_change == "yes":
                decision_change_counts[atom] += 1
    atom_names = sorted(set(total_counts) | set(critical_counts) | set(decision_change_counts))
    return [
        {
            "risk_atom_type": atom,
            "reviewed_row_count": total_counts[atom],
            "critical_atom_row_count": critical_counts[atom],
            "decision_change_yes_count": decision_change_counts[atom],
        }
        for atom in atom_names
    ]


def summarize_model_proxy_coverage(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_model: dict[str, dict[str, Any]] = defaultdict(lambda: defaultdict(int))
    for row in rows:
        hypotheses = parse_json_field(row.get("asr_hypotheses_json", ""))
        if not isinstance(hypotheses, list):
            continue
        for hypothesis in hypotheses:
            if not isinstance(hypothesis, dict):
                continue
            model_id = str(hypothesis.get("asr_run_id", "") or "unknown")
            by_model[model_id]["audit_model_samples"] += 1
    for row in rows:
        for item in iter_model_assessments(row):
            model_id = str(item.get("asr_run_id", "") or "unknown")
            if not model_id:
                continue
            by_model[model_id]["model_assessments"] += 1
            if model_assessment_reviewed(item):
                decision_change = str(
                    item.get("reviewer_would_asr_error_change_decision", "")
                ).strip()
                by_model[model_id]["reviewed_model_samples"] += 1
                if decision_change == "yes":
                    by_model[model_id]["human_decision_change_yes_rows"] += 1
                if decision_change == "uncertain":
                    by_model[model_id]["human_decision_change_uncertain_rows"] += 1
    result = []
    for model_id, counts in sorted(by_model.items()):
        result.append(
            {
                "asr_run_id": model_id,
                "audit_model_samples": counts["audit_model_samples"],
                "model_assessments": counts["model_assessments"],
                "reviewed_model_samples": counts["reviewed_model_samples"],
                "pending_model_samples": counts["model_assessments"]
                - counts["reviewed_model_samples"],
                "human_decision_change_yes_rows": counts["human_decision_change_yes_rows"],
                "human_decision_change_uncertain_rows": counts[
                    "human_decision_change_uncertain_rows"
                ],
            }
        )
    return result


def summarize_labels(rows: list[dict[str, str]]) -> dict[str, dict[str, int]]:
    reviewed_rows = [row for row in rows if reviewed(row)]
    return {
        "reviewer_semantic_risk_label": dict(
            sorted(Counter(row.get("reviewer_semantic_risk_label", "") for row in reviewed_rows).items())
        ),
        "reviewer_expected_safe_action": dict(
            sorted(Counter(row.get("reviewer_expected_safe_action", "") for row in reviewed_rows).items())
        ),
        "reviewer_would_asr_error_change_decision": dict(
            sorted(
                Counter(
                    row.get("reviewer_would_asr_error_change_decision", "")
                    for row in reviewed_rows
                ).items()
            )
        ),
        "reviewer_annotation_confidence": dict(
            sorted(
                Counter(row.get("reviewer_annotation_confidence", "") for row in reviewed_rows).items()
            )
        ),
    }


def assert_aggregate_safe(payload: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    for field in SENSITIVE_FIELDS:
        if field in text:
            raise ValueError(f"sensitive field name leaked into summary payload: {field}")
    for row in rows:
        for field in SENSITIVE_FIELDS:
            if field in row:
                raise ValueError(f"sensitive field present in aggregate row: {field}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-sheet", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started = time.time()
    rows = read_tsv(args.audit_sheet)
    completion = summarize_completion(rows)
    stratum_rows = summarize_selection(rows)
    atom_rows = summarize_human_atoms(rows)
    model_rows = summarize_model_proxy_coverage(rows)

    payload = {
        "ok": True,
        "input_boundary": "local transcript-bearing audit sheet; do not commit input",
        "output_boundary": "aggregate-only; no audio IDs, sample IDs, transcripts, hypotheses, or reviewer notes",
        **completion,
        "label_counts": summarize_labels(rows),
        "wall_time_seconds": round(time.time() - started, 4),
    }
    assert_aggregate_safe(payload, stratum_rows + atom_rows + model_rows)

    write_json(args.output_dir / "human_audit_review_summary.json", payload)
    write_tsv(
        args.output_dir / "human_audit_strata_review.tsv",
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
    write_tsv(
        args.output_dir / "human_audit_risk_atom_review.tsv",
        atom_rows,
        [
            "risk_atom_type",
            "reviewed_row_count",
            "critical_atom_row_count",
            "decision_change_yes_count",
        ],
    )
    write_tsv(
        args.output_dir / "human_audit_model_review.tsv",
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
    print(
        json.dumps(
            {
                "ok": True,
                "status": payload["status"],
                "audit_rows": payload["audit_rows"],
                "reviewed_rows": payload["reviewed_rows"],
                "pending_rows": payload["pending_rows"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

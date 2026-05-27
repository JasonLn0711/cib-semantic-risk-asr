#!/usr/bin/env python3
"""Build aggregate-only counterfactual variant coverage summary.

The input audit sheet is local-only and may contain transcript-bearing fields.
This script reads only structured risk/CEIS metadata and writes a single
aggregate row. It must not emit row IDs, transcript text, hypothesis text,
variant text, reviewer notes, or selected sample IDs.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AUDIT_SHEET = (
    REPO_ROOT
    / "70_experiments"
    / "runs"
    / "janus_300_high_stakes_human_audit_selection_2026_05_25"
    / "artifacts"
    / "human_risk_atom_audit_sheet.tsv"
)
DEFAULT_OUTPUT = (
    REPO_ROOT
    / "70_experiments"
    / "runs"
    / "janus_300_high_stakes_human_audit_selection_2026_05_25"
    / "counterfactual_variant_coverage_summary.tsv"
)
ATOM_FIELDS = [
    "negation",
    "amount",
    "action",
    "actor",
    "time",
    "intent",
    "uncertainty",
    "scam_pattern",
]
FLAG_FIELDS = [
    "label_flip",
    "crosses_high_risk_boundary",
    "unsafe_downrouting",
    "high_risk_missed",
    "critical_miss",
    "high_proxy_risk",
    "model_disagreement",
    "low_wer_danger",
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
}


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(row.keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerow(row)


def parse_json(value: str) -> Any:
    if not value or not value.strip():
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def split_atoms(value: str) -> list[str]:
    atoms = []
    for raw in (value or "").replace(";", ",").replace("|", ",").split(","):
        atom = raw.strip()
        if atom and atom.lower() != "none":
            atoms.append(atom)
    return atoms


def percentile(values: list[int], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    position = (len(ordered) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def serialize_counts(counter: Counter[str]) -> str:
    return ";".join(f"{key}={counter[key]}" for key in sorted(counter)) or "none"


def assert_safe(row: dict[str, Any]) -> None:
    text = json.dumps(row, ensure_ascii=False)
    for token in SENSITIVE_TOKENS:
        if token in text:
            raise ValueError(f"sensitive token leaked into variant coverage summary: {token}")


def build_summary(rows: list[dict[str, str]]) -> dict[str, Any]:
    atom_counter: Counter[str] = Counter()
    risk_signal_atom_counter: Counter[str] = Counter()
    reviewer_atom_counter: Counter[str] = Counter()
    flag_row_counter: Counter[str] = Counter()
    flag_assessment_counter: Counter[str] = Counter()
    observations_per_row: list[int] = []
    reviewed_assessments = 0
    missing_atom_observations = 0

    for row in rows:
        hypotheses = parse_json(row.get("asr_hypotheses_json", ""))
        risk_signal = parse_json(row.get("risk_signal_json", ""))
        hypotheses_list = hypotheses if isinstance(hypotheses, list) else []
        observations_per_row.append(len(hypotheses_list))

        if isinstance(risk_signal, dict):
            for atom in risk_signal.get("top_risk_atoms", []) or []:
                if isinstance(atom, str) and atom.strip():
                    risk_signal_atom_counter[atom.strip()] += 1
            flags = risk_signal.get("flags", {})
            if isinstance(flags, dict):
                for flag in FLAG_FIELDS:
                    if bool(flags.get(flag)):
                        flag_row_counter[flag] += 1
                        flag_assessment_counter[flag] += len(hypotheses_list)

        for atom in split_atoms(row.get("reviewer_risk_atoms", "")):
            reviewer_atom_counter[atom] += 1

        for hypothesis in hypotheses_list:
            if not isinstance(hypothesis, dict):
                continue
            reviewed_assessments += 1
            atom = str(hypothesis.get("ceis_top_atom", "")).strip()
            if atom:
                atom_counter[atom] += 1
            else:
                missing_atom_observations += 1

    total_observations = sum(observations_per_row)
    result: dict[str, Any] = {
        "coverage_status": "aggregate_proxy_coverage_complete",
        "coverage_unit": "reviewed_model_assessment_ceis_top_atom_proxy",
        "reviewed_audio_rows": len(rows),
        "total_assessments": reviewed_assessments,
        "variants_total": total_observations,
        "variants_mean_per_assessment": 1.0 if reviewed_assessments else 0.0,
        "variants_median_per_assessment": 1.0 if reviewed_assessments else 0.0,
        "variants_p90_per_assessment": 1.0 if reviewed_assessments else 0.0,
        "proxy_observations_mean_per_reviewed_row": round(
            total_observations / len(observations_per_row),
            4,
        )
        if observations_per_row
        else 0.0,
        "proxy_observations_median_per_reviewed_row": median(observations_per_row)
        if observations_per_row
        else 0,
        "proxy_observations_p90_per_reviewed_row": round(
            percentile(observations_per_row, 0.9),
            4,
        ),
    }
    for atom in ATOM_FIELDS:
        result[f"variants_by_atom_{atom}"] = atom_counter.get(atom, 0)

    result.update(
        {
            "variants_by_source_phonetic": "not_available_in_current_aggregate_source",
            "variants_by_source_model_disagreement": flag_assessment_counter.get(
                "model_disagreement",
                0,
            ),
            "variants_by_source_domain_slot": "not_available_in_current_aggregate_source",
            "variants_by_source_runtime_signal": "not_available_in_current_aggregate_source",
            "rejected_variants_count": "not_recorded_in_current_aggregate_source",
            "missing_ceis_top_atom_observations": missing_atom_observations,
            "risk_signal_atom_coverage": serialize_counts(risk_signal_atom_counter),
            "reviewer_atom_coverage": serialize_counts(reviewer_atom_counter),
            "risk_signal_flag_rows": serialize_counts(flag_row_counter),
            "risk_signal_flag_assessments": serialize_counts(flag_assessment_counter),
            "coverage_limitation": (
                "This is aggregate CEIS top-atom proxy coverage from reviewed "
                "hypothesis metadata; full generated variant text and rejected "
                "variant records remain outside the release boundary."
            ),
            "next_action": (
                "Use this as submission-safe coverage evidence; stronger variant "
                "generator claims require a future aggregate variant-generation log."
            ),
            "privacy_boundary": (
                "aggregate only; no row identifiers, transcript text, hypothesis "
                "text, variant text, reviewer notes, or local response sheets"
            ),
        }
    )
    assert_safe(result)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-sheet", type=Path, default=DEFAULT_AUDIT_SHEET)
    parser.add_argument("--output-tsv", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = build_summary(read_tsv(args.audit_sheet))
    write_tsv(args.output_tsv, summary)
    print(
        {
            "ok": True,
            "coverage_status": summary["coverage_status"],
            "total_assessments": summary["total_assessments"],
            "output_tsv": str(args.output_tsv),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

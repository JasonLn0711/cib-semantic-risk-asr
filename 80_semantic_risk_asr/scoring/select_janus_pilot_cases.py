#!/usr/bin/env python3
"""Select publication-safe JANUS 15-row pilot case candidates.

The input metric tables contain raw transcripts and must stay local/ignored.
This script emits only aggregate and routing metadata: IDs, model run IDs,
labels, CER/WER, SRES/CEIS, risk atoms, and case reasons.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


LABEL_ORDER = {
    "no_escalation": 0,
    "review": 1,
    "priority_review": 2,
    "critical_escalation": 3,
}

HIGH_RISK = {"priority_review", "critical_escalation"}
RECOVERY_ATOMS = {"negation", "amount", "action", "time", "intent"}
SRES_WEIGHTS = {
    "negation": 5.0,
    "amount": 5.0,
    "action": 5.0,
    "actor": 4.0,
    "intent": 4.0,
    "scam_pattern": 4.0,
    "time": 3.0,
    "uncertainty": 3.0,
}


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


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


def as_float(value: str | None, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def split_sample_id(sample_id: str) -> tuple[str, str]:
    if "__" not in sample_id:
        return sample_id, ""
    return sample_id.split("__", 1)


def decision_distance(reference_label: str, asr_label: str) -> int:
    if reference_label not in LABEL_ORDER or asr_label not in LABEL_ORDER:
        return 0
    return LABEL_ORDER[reference_label] - LABEL_ORDER[asr_label]


def read_ceis_by_sample(path: Path) -> dict[str, dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("summary", {}).get("by_sample", {})


def aggregate_sres(rows: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["sample_id"]].append(row)

    aggregate: dict[str, dict[str, Any]] = {}
    for sample_id, sample_rows in grouped.items():
        audio_id, run_id = split_sample_id(sample_id)
        error_types = sorted({row.get("error_type", "") for row in sample_rows if row.get("error_type")})
        sres_values = [
            SRES_WEIGHTS.get(row.get("error_type", ""), 1.0)
            * as_float(row.get("severity"))
            * as_float(row.get("downstream_impact"))
            for row in sample_rows
        ]
        aggregate[sample_id] = {
            "sample_id": sample_id,
            "audio_id": audio_id,
            "asr_run_id": run_id or sample_rows[0].get("asr_run_id", ""),
            "split": sample_rows[0].get("split", ""),
            "cer": as_float(sample_rows[0].get("cer")),
            "wer": as_float(sample_rows[0].get("wer")),
            "sres_total": round(sum(sres_values), 3),
            "risk_atoms": "|".join(error_types),
        }
    return aggregate


def read_downstream(path: Path) -> dict[str, dict[str, str]]:
    return {row["sample_id"]: row for row in read_tsv(path)}


def add_candidate(
    rows: list[dict[str, Any]],
    seen: set[tuple[str, str]],
    case_type: str,
    sample: dict[str, Any],
    downstream: dict[str, str],
    ceis: dict[str, Any],
    reason: str,
) -> None:
    key = (case_type, sample["sample_id"])
    if key in seen:
        return
    seen.add(key)
    reference_label = downstream.get("reference_label", "")
    asr_label = downstream.get("asr_label", "")
    rows.append(
        {
            "case_type": case_type,
            "audio_id": sample["audio_id"],
            "asr_run_id": sample["asr_run_id"],
            "split": sample["split"],
            "reference_label": reference_label,
            "asr_label": asr_label,
            "decision_distance": decision_distance(reference_label, asr_label),
            "cer": f"{sample['cer']:.2f}",
            "wer": f"{sample['wer']:.2f}",
            "sres_total": f"{sample['sres_total']:.3f}",
            "ceis": f"{as_float(str(ceis.get('ceis', '0'))):.4f}",
            "max_variant_id": ceis.get("max_variant_id", ""),
            "risk_atom_type": ceis.get("risk_atom_type", ""),
            "all_risk_atoms": sample["risk_atoms"],
            "confidence_signal_available": "no",
            "safe_for_git": "yes_no_transcript",
            "reason": reason,
        }
    )


def select_cases(
    sres_by_sample: dict[str, dict[str, Any]],
    downstream_by_sample: dict[str, dict[str, str]],
    ceis_by_sample: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    samples = [
        sample
        for sample_id, sample in sres_by_sample.items()
        if sample_id in downstream_by_sample and sample_id in ceis_by_sample
    ]

    by_ceis = sorted(
        samples,
        key=lambda sample: (
            -as_float(str(ceis_by_sample[sample["sample_id"]].get("ceis", "0"))),
            sample["cer"],
            sample["sample_id"],
        ),
    )
    for sample in by_ceis[:8]:
        ceis = ceis_by_sample[sample["sample_id"]]
        if as_float(str(ceis.get("ceis", "0"))) <= 0:
            continue
        add_candidate(
            rows,
            seen,
            "high_ceis",
            sample,
            downstream_by_sample[sample["sample_id"]],
            ceis,
            "highest CEIS model-samples for paper case inspection",
        )

    for sample in samples:
        downstream = downstream_by_sample[sample["sample_id"]]
        reference_label = downstream.get("reference_label", "")
        asr_label = downstream.get("asr_label", "")
        if reference_label in HIGH_RISK and asr_label not in HIGH_RISK:
            add_candidate(
                rows,
                seen,
                "unsafe_downrouting",
                sample,
                downstream,
                ceis_by_sample[sample["sample_id"]],
                "reference is high risk but ASR-side label falls below high-risk routing",
            )

    for sample in samples:
        ceis = ceis_by_sample[sample["sample_id"]]
        if sample["cer"] <= 40.0 and as_float(str(ceis.get("ceis", "0"))) >= 5.0:
            add_candidate(
                rows,
                seen,
                "lower_cer_high_ceis",
                sample,
                downstream_by_sample[sample["sample_id"]],
                ceis,
                "CER is not extreme but decision instability is high",
            )

    for sample in sorted(samples, key=lambda item: (-item["sres_total"], item["sample_id"])):
        ceis = ceis_by_sample[sample["sample_id"]]
        if sample["sres_total"] >= 100.0 and as_float(str(ceis.get("ceis", "0"))) == 0.0:
            add_candidate(
                rows,
                seen,
                "sres_high_ceis_low",
                sample,
                downstream_by_sample[sample["sample_id"]],
                ceis,
                "SRES is high but CEIS stays low, useful as a contrast case",
            )

    for sample in samples:
        ceis = ceis_by_sample[sample["sample_id"]]
        atom = str(ceis.get("risk_atom_type", ""))
        if as_float(str(ceis.get("ceis", "0"))) > 0 and atom in RECOVERY_ATOMS:
            add_candidate(
                rows,
                seen,
                "recovery_candidate",
                sample,
                downstream_by_sample[sample["sample_id"]],
                ceis,
                "decision changes on a finite-grammar atom suitable for constrained recovery",
            )

    return sorted(
        rows,
        key=lambda row: (
            row["case_type"],
            -as_float(str(row["ceis"])),
            as_float(str(row["cer"])),
            row["audio_id"],
            row["asr_run_id"],
        ),
    )


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_case_type: dict[str, int] = defaultdict(int)
    by_run_id: dict[str, int] = defaultdict(int)
    by_atom: dict[str, int] = defaultdict(int)
    for row in rows:
        by_case_type[row["case_type"]] += 1
        by_run_id[row["asr_run_id"]] += 1
        by_atom[row["risk_atom_type"] or "unknown"] += 1
    return {
        "rows": len(rows),
        "by_case_type": dict(sorted(by_case_type.items())),
        "by_asr_run_id": dict(sorted(by_run_id.items())),
        "by_risk_atom_type": dict(sorted(by_atom.items())),
    }


def main() -> int:
    root = repo_root_from_script()
    default_run_dir = root / "70_experiments" / "runs" / "janus_15_decision_stability_pilot"
    default_inputs = default_run_dir / "artifacts" / "metric_inputs"
    default_outputs = default_run_dir / "artifacts" / "metric_outputs"

    parser = argparse.ArgumentParser()
    parser.add_argument("--sres", type=Path, default=default_inputs / "sres_annotation.tsv")
    parser.add_argument("--downstream", type=Path, default=default_inputs / "downstream_escalation_decisions.tsv")
    parser.add_argument("--ceis-json", type=Path, default=default_outputs / "ceis_three_model_15.json")
    parser.add_argument("--output-tsv", type=Path, default=default_run_dir / "case_candidates.tsv")
    parser.add_argument("--summary-json", type=Path, default=default_run_dir / "case_candidate_summary.json")
    args = parser.parse_args()

    sres_by_sample = aggregate_sres(read_tsv(args.sres))
    downstream_by_sample = read_downstream(args.downstream)
    ceis_by_sample = read_ceis_by_sample(args.ceis_json)
    rows = select_cases(sres_by_sample, downstream_by_sample, ceis_by_sample)
    fields = [
        "case_type",
        "audio_id",
        "asr_run_id",
        "split",
        "reference_label",
        "asr_label",
        "decision_distance",
        "cer",
        "wer",
        "sres_total",
        "ceis",
        "max_variant_id",
        "risk_atom_type",
        "all_risk_atoms",
        "confidence_signal_available",
        "safe_for_git",
        "reason",
    ]
    write_tsv(args.output_tsv, rows, fields)
    summary = summarize(rows)
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, **summary}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

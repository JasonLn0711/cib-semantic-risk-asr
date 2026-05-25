#!/usr/bin/env python3
"""Select a stratified human risk-atom audit set.

The selector reads local transcript-bearing proxy artifacts and writes two
classes of outputs:

- ignored local audit sheets under ``artifacts/`` with audio IDs/transcripts;
- aggregate-only tracked summaries without sample IDs or transcripts.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


LABEL_ORDER = {
    "no_escalation": 0,
    "review": 1,
    "priority_review": 2,
    "critical_escalation": 3,
}

HIGH_RISK = {"priority_review", "critical_escalation"}
RISK_ATOM_PRIORITY = ["negation", "amount", "action", "actor", "scam_pattern"]

DEFAULT_QUOTAS = {
    "critical_or_high_risk_missed": 6,
    "unsafe_downrouting": 6,
    "low_wer_danger": 4,
    "high_proxy_risk": 6,
    "model_disagreement": 4,
    "clean_control": 4,
}


@dataclass
class ModelSample:
    sample_id: str
    audio_id: str
    split: str
    asr_run_id: str
    reference_text: str = ""
    hypothesis_text: str = ""
    wer: float = 0.0
    cer: float = 0.0
    sres_total: float = 0.0
    sres_max: float = 0.0
    sres_top_atom: str = ""
    ceis_max: float = 0.0
    ceis_top_atom: str = ""
    unstable_atoms: set[str] = field(default_factory=set)
    reference_label: str = ""
    asr_label: str = ""
    recovered_label: str = ""
    label_flip: bool = False
    unsafe_downrouting: bool = False
    high_risk_missed: bool = False
    critical_miss: bool = False
    over_escalation: bool = False


@dataclass
class AudioCandidate:
    audio_id: str
    split: str
    reference_text: str
    reference_label: str
    samples: list[ModelSample]
    risk_score: float
    flags: dict[str, bool]
    top_risk_atoms: list[str]
    selection_stratum: str = ""
    selection_reason: str = ""


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
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def as_float(value: str | None, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def label_level(label: str) -> int:
    return LABEL_ORDER.get(label, 0)


def parse_sample_id(sample_id: str, row: dict[str, str] | None = None) -> tuple[str, str]:
    if row and row.get("asr_run_id"):
        asr_run_id = row["asr_run_id"]
        suffix = f"__{asr_run_id}"
        if sample_id.endswith(suffix):
            return sample_id[: -len(suffix)], asr_run_id
    if "__" in sample_id:
        return sample_id.rsplit("__", 1)
    return sample_id, row.get("asr_run_id", "") if row else ""


def load_model_samples(
    sres_path: Path,
    ceis_path: Path,
    downstream_path: Path,
) -> dict[str, ModelSample]:
    samples: dict[str, ModelSample] = {}
    sres_atom_scores: dict[str, Counter[str]] = defaultdict(Counter)

    for row in read_tsv(sres_path):
        sample_id = row.get("sample_id", "")
        audio_id, asr_run_id = parse_sample_id(sample_id, row)
        sample = samples.setdefault(
            sample_id,
            ModelSample(
                sample_id=sample_id,
                audio_id=audio_id,
                split=row.get("split", ""),
                asr_run_id=asr_run_id,
                reference_text=row.get("reference_text", ""),
                hypothesis_text=row.get("hypothesis_text", ""),
                wer=as_float(row.get("wer")),
                cer=as_float(row.get("cer")),
            ),
        )
        sres = as_float(row.get("sres"))
        atom = row.get("error_type", "") or "unknown"
        sample.sres_total += sres
        sample.sres_max = max(sample.sres_max, sres)
        sres_atom_scores[sample_id][atom] += sres

    for sample_id, scores in sres_atom_scores.items():
        if scores:
            samples[sample_id].sres_top_atom = scores.most_common(1)[0][0]
            samples[sample_id].sres_total = round(samples[sample_id].sres_total, 4)
            samples[sample_id].sres_max = round(samples[sample_id].sres_max, 4)

    ceis_atom_scores: dict[str, Counter[str]] = defaultdict(Counter)
    for row in read_tsv(ceis_path):
        sample_id = row.get("sample_id", "")
        audio_id, asr_run_id = parse_sample_id(sample_id, row)
        sample = samples.setdefault(
            sample_id,
            ModelSample(sample_id=sample_id, audio_id=audio_id, split="", asr_run_id=asr_run_id),
        )
        atom = row.get("risk_atom_type", "") or "unknown"
        component = as_float(row.get("ceis_component"))
        decision_distance = as_float(row.get("decision_distance_used"))
        unstable = (
            component > 0
            or decision_distance > 0
            or row.get("base_decision", "") != row.get("variant_decision", "")
        )
        sample.ceis_max = max(sample.ceis_max, component)
        ceis_atom_scores[sample_id][atom] += component
        if unstable:
            sample.unstable_atoms.add(atom)

    for sample_id, scores in ceis_atom_scores.items():
        if scores:
            samples[sample_id].ceis_top_atom = scores.most_common(1)[0][0]
            samples[sample_id].ceis_max = round(samples[sample_id].ceis_max, 4)

    for row in read_tsv(downstream_path):
        sample_id = row.get("sample_id", "")
        audio_id, asr_run_id = parse_sample_id(sample_id, row)
        sample = samples.setdefault(
            sample_id,
            ModelSample(sample_id=sample_id, audio_id=audio_id, split="", asr_run_id=asr_run_id),
        )
        reference_label = row.get("reference_label", "")
        asr_label = row.get("asr_label", "")
        ref_level = label_level(reference_label)
        asr_level = label_level(asr_label)
        sample.reference_label = reference_label
        sample.asr_label = asr_label
        sample.recovered_label = row.get("recovered_label", "")
        sample.label_flip = reference_label != asr_label
        sample.unsafe_downrouting = asr_level < ref_level
        sample.high_risk_missed = reference_label in HIGH_RISK and asr_label not in HIGH_RISK
        sample.critical_miss = reference_label == "critical_escalation" and asr_label not in HIGH_RISK
        sample.over_escalation = asr_level > ref_level

    return samples


def build_audio_candidates(
    samples: dict[str, ModelSample],
    *,
    low_wer_threshold: float,
    sres_threshold: float,
    ceis_threshold: float,
) -> list[AudioCandidate]:
    grouped: dict[str, list[ModelSample]] = defaultdict(list)
    for sample in samples.values():
        if sample.reference_label:
            grouped[sample.audio_id].append(sample)

    candidates = []
    for audio_id, rows in grouped.items():
        rows = sorted(rows, key=lambda row: row.asr_run_id)
        reference_labels = [row.reference_label for row in rows if row.reference_label]
        reference_label = Counter(reference_labels).most_common(1)[0][0] if reference_labels else ""
        split = next((row.split for row in rows if row.split), "")
        reference_text = next((row.reference_text for row in rows if row.reference_text), "")
        label_values = {row.asr_label for row in rows if row.asr_label}
        level_values = [label_level(row.asr_label) for row in rows if row.asr_label]
        low_wer_danger = any(
            row.wer <= low_wer_threshold
            and (
                row.label_flip
                or row.unsafe_downrouting
                or row.high_risk_missed
                or row.sres_total >= sres_threshold
                or row.ceis_max >= ceis_threshold
            )
            for row in rows
        )
        flags = {
            "critical_miss": any(row.critical_miss for row in rows),
            "high_risk_missed": any(row.high_risk_missed for row in rows),
            "unsafe_downrouting": any(row.unsafe_downrouting for row in rows),
            "label_flip": any(row.label_flip for row in rows),
            "low_wer_danger": low_wer_danger,
            "high_proxy_risk": any(
                row.sres_total >= sres_threshold or row.ceis_max >= ceis_threshold for row in rows
            ),
            "model_disagreement": len(label_values) > 1,
            "crosses_high_risk_boundary": bool(level_values)
            and min(level_values) < 2 <= max(level_values),
        }
        atom_counts = Counter()
        for row in rows:
            for atom in row.unstable_atoms:
                atom_counts[atom] += 1
            if row.sres_total >= sres_threshold and row.sres_top_atom:
                atom_counts[row.sres_top_atom] += 1
            if row.ceis_max >= ceis_threshold and row.ceis_top_atom:
                atom_counts[row.ceis_top_atom] += 1
        top_atoms = [atom for atom, _ in atom_counts.most_common()]
        risk_score = max(
            (
                (100 if row.critical_miss else 0)
                + (80 if row.high_risk_missed else 0)
                + (60 if row.unsafe_downrouting else 0)
                + (35 if row.label_flip else 0)
                + (25 if low_wer_danger else 0)
                + min(row.sres_total / 10, 40)
                + min(row.ceis_max * 4, 40)
                + row.wer / 100
            )
            for row in rows
        )
        candidates.append(
            AudioCandidate(
                audio_id=audio_id,
                split=split,
                reference_text=reference_text,
                reference_label=reference_label,
                samples=rows,
                risk_score=round(risk_score, 4),
                flags=flags,
                top_risk_atoms=top_atoms,
            )
        )
    return candidates


def candidate_sort_key(candidate: AudioCandidate) -> tuple[float, str]:
    return (-candidate.risk_score, candidate.audio_id)


def stratum_match(candidate: AudioCandidate, stratum: str) -> bool:
    flags = candidate.flags
    if stratum == "critical_or_high_risk_missed":
        return flags["critical_miss"] or flags["high_risk_missed"]
    if stratum == "unsafe_downrouting":
        return flags["unsafe_downrouting"]
    if stratum == "low_wer_danger":
        return flags["low_wer_danger"]
    if stratum == "high_proxy_risk":
        return flags["high_proxy_risk"]
    if stratum == "model_disagreement":
        return flags["model_disagreement"] or flags["crosses_high_risk_boundary"]
    if stratum == "clean_control":
        return not any(flags.values())
    raise ValueError(f"unknown stratum: {stratum}")


def reason_for(candidate: AudioCandidate, stratum: str) -> str:
    if stratum == "critical_or_high_risk_missed":
        return "Includes critical miss or high-risk missed signal."
    if stratum == "unsafe_downrouting":
        return "At least one ASR hypothesis routes below reference escalation."
    if stratum == "low_wer_danger":
        return "Low row-level WER still has downstream or proxy risk signal."
    if stratum == "high_proxy_risk":
        return "SRES or CEIS crosses proxy risk threshold."
    if stratum == "model_disagreement":
        return "ASR-family labels disagree or cross the high-risk boundary."
    if stratum == "clean_control":
        return "No current proxy danger signal; selected as control."
    if stratum == "risk_score_fill":
        return "Fills remaining audit quota by composite risk score."
    return stratum


def select_candidates(
    candidates: list[AudioCandidate],
    *,
    audit_size: int,
    quotas: dict[str, int],
) -> list[AudioCandidate]:
    selected: list[AudioCandidate] = []
    selected_ids: set[str] = set()
    sorted_candidates = sorted(candidates, key=candidate_sort_key)

    for stratum, quota in quotas.items():
        available = [candidate for candidate in sorted_candidates if stratum_match(candidate, stratum)]
        for candidate in available:
            if len([item for item in selected if item.selection_stratum == stratum]) >= quota:
                break
            if candidate.audio_id in selected_ids:
                continue
            candidate.selection_stratum = stratum
            candidate.selection_reason = reason_for(candidate, stratum)
            selected.append(candidate)
            selected_ids.add(candidate.audio_id)
            if len(selected) >= audit_size:
                return selected

    # Ensure each risk atom with available instability has at least one selected
    # example where possible before generic risk-score fill.
    selected_atoms = set()
    for candidate in selected:
        selected_atoms.update(candidate.top_risk_atoms)
    for atom in RISK_ATOM_PRIORITY:
        if atom in selected_atoms or len(selected) >= audit_size:
            continue
        for candidate in sorted_candidates:
            if candidate.audio_id in selected_ids or atom not in candidate.top_risk_atoms:
                continue
            candidate.selection_stratum = "risk_atom_coverage"
            candidate.selection_reason = f"Adds coverage for risk atom: {atom}."
            selected.append(candidate)
            selected_ids.add(candidate.audio_id)
            selected_atoms.add(atom)
            break

    for candidate in sorted_candidates:
        if len(selected) >= audit_size:
            break
        if candidate.audio_id in selected_ids:
            continue
        candidate.selection_stratum = "risk_score_fill"
        candidate.selection_reason = reason_for(candidate, "risk_score_fill")
        selected.append(candidate)
        selected_ids.add(candidate.audio_id)

    return selected


def write_local_audit_sheet(path: Path, selected: list[AudioCandidate]) -> None:
    fields = [
        "audio_id",
        "split",
        "selection_stratum",
        "selection_reason",
        "reference_label",
        "reference_text",
        "asr_hypotheses_json",
        "risk_signal_json",
        "reviewer_verified_transcript",
        "reviewer_semantic_risk_label",
        "reviewer_risk_atoms",
        "reviewer_critical_atoms",
        "reviewer_asr_confusion_terms",
        "reviewer_would_asr_error_change_decision",
        "reviewer_decision_change_reason",
        "reviewer_expected_safe_action",
        "reviewer_annotation_confidence",
        "reviewer_model_assessments_json",
        "reviewer_notes",
    ]
    rows = []
    for candidate in selected:
        hypotheses = [
            {
                "asr_run_id": sample.asr_run_id,
                "hypothesis_text": sample.hypothesis_text,
                "wer": sample.wer,
                "cer": sample.cer,
                "asr_label": sample.asr_label,
                "sres_total": sample.sres_total,
                "ceis_max": sample.ceis_max,
                "sres_top_atom": sample.sres_top_atom,
                "ceis_top_atom": sample.ceis_top_atom,
            }
            for sample in candidate.samples
        ]
        model_assessments = [
            {
                "asr_run_id": sample.asr_run_id,
                "reviewer_would_asr_error_change_decision": "",
                "reviewer_critical_atoms": "",
                "reviewer_expected_safe_action": "",
                "reviewer_annotation_confidence": "",
            }
            for sample in candidate.samples
        ]
        risk_signal = {
            "risk_score": candidate.risk_score,
            "flags": candidate.flags,
            "top_risk_atoms": candidate.top_risk_atoms,
        }
        rows.append(
            {
                "audio_id": candidate.audio_id,
                "split": candidate.split,
                "selection_stratum": candidate.selection_stratum,
                "selection_reason": candidate.selection_reason,
                "reference_label": candidate.reference_label,
                "reference_text": candidate.reference_text,
                "asr_hypotheses_json": json.dumps(hypotheses, ensure_ascii=False),
                "risk_signal_json": json.dumps(risk_signal, ensure_ascii=False),
                "reviewer_verified_transcript": "",
                "reviewer_semantic_risk_label": "",
                "reviewer_risk_atoms": "",
                "reviewer_critical_atoms": "",
                "reviewer_asr_confusion_terms": "",
                "reviewer_would_asr_error_change_decision": "",
                "reviewer_decision_change_reason": "",
                "reviewer_expected_safe_action": "",
                "reviewer_annotation_confidence": "",
                "reviewer_model_assessments_json": json.dumps(model_assessments, ensure_ascii=False),
                "reviewer_notes": "",
            }
        )
    write_tsv(path, rows, fields)


def aggregate_strata_rows(
    candidates: list[AudioCandidate],
    selected: list[AudioCandidate],
    quotas: dict[str, int],
) -> list[dict[str, Any]]:
    selected_counter = Counter(candidate.selection_stratum for candidate in selected)
    rows = []
    for stratum, quota in quotas.items():
        available = sum(1 for candidate in candidates if stratum_match(candidate, stratum))
        rows.append(
            {
                "stratum": stratum,
                "target_quota": quota,
                "available_audio_count": available,
                "selected_audio_count": selected_counter[stratum],
                "selected_signal_audio_count": sum(
                    1 for candidate in selected if stratum_match(candidate, stratum)
                ),
                "selection_rule": reason_for(AudioCandidate("", "", "", "", [], 0, {}, []), stratum),
            }
        )
    for stratum in ["risk_atom_coverage", "risk_score_fill"]:
        rows.append(
            {
                "stratum": stratum,
                "target_quota": "",
                "available_audio_count": "",
                "selected_audio_count": selected_counter[stratum],
                "selected_signal_audio_count": "",
                "selection_rule": reason_for(AudioCandidate("", "", "", "", [], 0, {}, []), stratum),
            }
        )
    return rows


def risk_atom_coverage_rows(
    candidates: list[AudioCandidate],
    selected: list[AudioCandidate],
) -> list[dict[str, Any]]:
    all_counts: Counter[str] = Counter()
    selected_counts: Counter[str] = Counter()
    for candidate in candidates:
        for atom in set(candidate.top_risk_atoms):
            all_counts[atom] += 1
    for candidate in selected:
        for atom in set(candidate.top_risk_atoms):
            selected_counts[atom] += 1
    atoms = sorted(set(all_counts) | set(selected_counts))
    return [
        {
            "risk_atom_type": atom,
            "available_audio_count": all_counts[atom],
            "selected_audio_count": selected_counts[atom],
            "selected_rate": round(selected_counts[atom] / all_counts[atom], 4)
            if all_counts[atom]
            else 0.0,
        }
        for atom in atoms
    ]


def model_signal_rows(selected: list[AudioCandidate]) -> list[dict[str, Any]]:
    by_run: dict[str, list[ModelSample]] = defaultdict(list)
    for candidate in selected:
        for sample in candidate.samples:
            by_run[sample.asr_run_id].append(sample)
    return [
        {
            "asr_run_id": run,
            "selected_model_samples": len(rows),
            "label_flip_count": sum(row.label_flip for row in rows),
            "unsafe_downrouting_count": sum(row.unsafe_downrouting for row in rows),
            "high_risk_missed_count": sum(row.high_risk_missed for row in rows),
            "critical_miss_count": sum(row.critical_miss for row in rows),
            "mean_wer": round(sum(row.wer for row in rows) / len(rows), 4) if rows else 0.0,
            "mean_cer": round(sum(row.cer for row in rows) / len(rows), 4) if rows else 0.0,
            "mean_sres_total": round(sum(row.sres_total for row in rows) / len(rows), 4)
            if rows
            else 0.0,
            "mean_ceis_max": round(sum(row.ceis_max for row in rows) / len(rows), 4)
            if rows
            else 0.0,
        }
        for run, rows in sorted(by_run.items())
    ]


def summary_payload(
    *,
    args: argparse.Namespace,
    candidates: list[AudioCandidate],
    selected: list[AudioCandidate],
    started: float,
) -> dict[str, Any]:
    flag_counts = {
        key: sum(candidate.flags.get(key, False) for candidate in candidates)
        for key in [
            "critical_miss",
            "high_risk_missed",
            "unsafe_downrouting",
            "label_flip",
            "low_wer_danger",
            "high_proxy_risk",
            "model_disagreement",
            "crosses_high_risk_boundary",
        ]
    }
    selected_flag_counts = {
        key: sum(candidate.flags.get(key, False) for candidate in selected)
        for key in flag_counts
    }
    return {
        "ok": True,
        "status": "audit_selection_created_review_pending",
        "inputs": {
            "sres_scored": str(args.sres_scored),
            "ceis_scored": str(args.ceis_scored),
            "downstream_decisions": str(args.downstream_decisions),
        },
        "thresholds": {
            "low_wer_threshold": args.low_wer_threshold,
            "sres_threshold": args.sres_threshold,
            "ceis_threshold": args.ceis_threshold,
        },
        "privacy_boundary": [
            "Tracked outputs omit audio IDs, sample IDs, transcripts, and hypothesis text.",
            "The human audit sheet is written under ignored artifacts/ and must stay local-only.",
        ],
        "candidate_audio_count": len(candidates),
        "selected_audio_count": len(selected),
        "selected_model_sample_count": sum(len(candidate.samples) for candidate in selected),
        "stratum_counts": dict(Counter(candidate.selection_stratum for candidate in selected)),
        "available_signal_counts": flag_counts,
        "selected_signal_counts": selected_flag_counts,
        "reference_label_counts": dict(Counter(candidate.reference_label for candidate in selected)),
        "split_counts": dict(Counter(candidate.split for candidate in selected)),
        "artifact_outputs": {
            "local_audit_sheet": str(args.output_dir / "artifacts" / "human_risk_atom_audit_sheet.tsv"),
            "aggregate_summary": str(args.output_dir / "human_audit_selection_summary.json"),
            "selection_strata": str(args.output_dir / "selection_strata.tsv"),
            "risk_atom_coverage": str(args.output_dir / "risk_atom_coverage.tsv"),
            "model_signal_coverage": str(args.output_dir / "model_signal_coverage.tsv"),
        },
        "wall_time_seconds": round(time.time() - started, 4),
    }


def parse_quotas(text: str) -> dict[str, int]:
    quotas = dict(DEFAULT_QUOTAS)
    if not text:
        return quotas
    for item in text.split(","):
        if not item.strip():
            continue
        key, value = item.split("=", 1)
        quotas[key.strip()] = int(value)
    return quotas


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sres-scored", type=Path, required=True)
    parser.add_argument("--ceis-scored", type=Path, required=True)
    parser.add_argument("--downstream-decisions", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--audit-size", type=int, default=30)
    parser.add_argument("--low-wer-threshold", type=float, default=10.0)
    parser.add_argument("--sres-threshold", type=float, default=20.0)
    parser.add_argument("--ceis-threshold", type=float, default=5.0)
    parser.add_argument("--quotas", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started = time.time()
    quotas = parse_quotas(args.quotas)
    samples = load_model_samples(args.sres_scored, args.ceis_scored, args.downstream_decisions)
    candidates = build_audio_candidates(
        samples,
        low_wer_threshold=args.low_wer_threshold,
        sres_threshold=args.sres_threshold,
        ceis_threshold=args.ceis_threshold,
    )
    selected = select_candidates(candidates, audit_size=args.audit_size, quotas=quotas)

    write_local_audit_sheet(args.output_dir / "artifacts" / "human_risk_atom_audit_sheet.tsv", selected)
    strata_rows = aggregate_strata_rows(candidates, selected, quotas)
    write_tsv(
        args.output_dir / "selection_strata.tsv",
        strata_rows,
        [
            "stratum",
            "target_quota",
            "available_audio_count",
            "selected_audio_count",
            "selected_signal_audio_count",
            "selection_rule",
        ],
    )
    write_tsv(
        args.output_dir / "risk_atom_coverage.tsv",
        risk_atom_coverage_rows(candidates, selected),
        ["risk_atom_type", "available_audio_count", "selected_audio_count", "selected_rate"],
    )
    write_tsv(
        args.output_dir / "model_signal_coverage.tsv",
        model_signal_rows(selected),
        [
            "asr_run_id",
            "selected_model_samples",
            "label_flip_count",
            "unsafe_downrouting_count",
            "high_risk_missed_count",
            "critical_miss_count",
            "mean_wer",
            "mean_cer",
            "mean_sres_total",
            "mean_ceis_max",
        ],
    )
    payload = summary_payload(args=args, candidates=candidates, selected=selected, started=started)
    write_json(args.output_dir / "human_audit_selection_summary.json", payload)
    print(
        json.dumps(
            {
                "ok": True,
                "candidate_audio_count": len(candidates),
                "selected_audio_count": len(selected),
                "status": payload["status"],
                "wall_time_seconds": payload["wall_time_seconds"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

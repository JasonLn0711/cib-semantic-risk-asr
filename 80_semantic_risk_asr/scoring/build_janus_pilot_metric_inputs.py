#!/usr/bin/env python3
"""Build JANUS 15-row pilot inputs for SRES, CEIS, and downstream checks."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


REQUIRED_GOLD_FIELDS = (
    "human_verified_transcript",
    "semantic_risk_label",
    "risk_atoms",
    "asr_confusion_terms",
    "would_asr_error_change_decision",
)

LABEL_ORDER = {
    "no_escalation": 0,
    "review": 1,
    "priority_review": 2,
    "critical_escalation": 3,
}

HYPOTHESIS_TEXT_FIELDS = (
    "hypothesis_text",
    "prediction",
    "pred_text",
    "asr_text",
    "transcript",
    "text",
)

ASR_LABEL_FIELDS = (
    "asr_label",
    "prediction_label",
    "hypothesis_label",
    "escalation_label",
)

NO_OBSERVED_VALUES = {
    "none",
    "none_observed",
    "no_risk_atom",
    "no_risk_atoms",
    "not_applicable",
    "n/a",
    "na",
}


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_rows(path: Path) -> list[dict[str, str]]:
    if path.suffix == ".jsonl":
        rows = []
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    item = json.loads(line)
                    rows.append({key: stringify(value) for key, value in item.items()})
        return rows

    delimiter = "," if path.suffix == ".csv" else "\t"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def write_tsv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def first_value(row: dict[str, str], fields: tuple[str, ...]) -> str:
    for field in fields:
        value = (row.get(field) or "").strip()
        if value:
            return value
    return ""


def split_tokens(value: str) -> list[str]:
    return [
        token.strip()
        for token in re.split(r"[|,;]", value or "")
        if token.strip() and token.strip().lower() not in NO_OBSERVED_VALUES
    ]


def split_confusions(value: str) -> list[str]:
    return [
        token.strip()
        for token in re.split(r"[|,;]", value or "")
        if token.strip()
    ]


def slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", value.strip())
    return cleaned.strip("_") or "variant"


def decision_distance(reference_label: str, asr_label: str) -> int:
    if reference_label not in LABEL_ORDER or asr_label not in LABEL_ORDER:
        return 0
    return abs(LABEL_ORDER[reference_label] - LABEL_ORDER[asr_label])


def decision_change_flag(row: dict[str, str]) -> str:
    return (row.get("would_asr_error_change_decision") or "").strip().lower()


def severity_for(row: dict[str, str]) -> int:
    flag = decision_change_flag(row)
    if flag == "yes":
        return 5
    if flag == "unclear":
        return 3
    if flag == "no":
        return 1
    return 2


def downstream_impact_for(
    gold_row: dict[str, str],
    reference_label: str,
    asr_label: str,
) -> int:
    distance = decision_distance(reference_label, asr_label)
    flag = decision_change_flag(gold_row)
    if flag == "yes":
        return max(distance, 3)
    if flag == "unclear":
        return max(distance, 1)
    if flag == "no":
        return distance
    return max(distance, 1 if not asr_label else 0)


def completed_gold_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict[str, list[str]]]:
    missing = {
        field: [
            row.get("audio_id", "")
            for row in rows
            if not (row.get(field) or "").strip()
        ]
        for field in REQUIRED_GOLD_FIELDS
    }
    complete = [
        row
        for row in rows
        if all((row.get(field) or "").strip() for field in REQUIRED_GOLD_FIELDS)
    ]
    return complete, missing


def infer_run_id(path: Path, row: dict[str, str]) -> str:
    return first_value(row, ("asr_run_id", "run_id", "model")) or path.stem


def sample_id(audio_id: str, asr_run_id: str) -> str:
    return f"{audio_id}__{slug(asr_run_id)}"


def build_rows(
    gold_rows: list[dict[str, str]],
    hypothesis_paths: list[Path],
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], dict[str, Any]]:
    gold_by_id = {row["audio_id"]: row for row in gold_rows}
    sres_rows: list[dict[str, str]] = []
    ceis_rows: list[dict[str, str]] = []
    downstream_rows: list[dict[str, str]] = []
    unmatched_hypotheses: list[str] = []
    missing_hypothesis_text: list[str] = []
    missing_asr_label: list[str] = []

    for path in hypothesis_paths:
        for hypothesis in read_rows(path):
            audio_id = first_value(hypothesis, ("audio_id", "sample_id", "id"))
            asr_run_id = infer_run_id(path, hypothesis)
            if audio_id not in gold_by_id:
                unmatched_hypotheses.append(f"{path}:{audio_id or '<missing_audio_id>'}")
                continue

            gold = gold_by_id[audio_id]
            segment_id = sample_id(audio_id, asr_run_id)
            reference_text = gold.get("human_verified_transcript", "")
            hypothesis_text = first_value(hypothesis, HYPOTHESIS_TEXT_FIELDS)
            reference_label = gold.get("semantic_risk_label", "")
            asr_label = first_value(hypothesis, ASR_LABEL_FIELDS)
            recovered_label = first_value(
                hypothesis,
                ("recovered_label", "post_recovery_label"),
            ) or asr_label
            recovery_action = first_value(hypothesis, ("recovery_action",)) or "none"
            atoms = split_tokens(gold.get("risk_atoms", ""))
            confusions = split_confusions(gold.get("asr_confusion_terms", ""))

            if not hypothesis_text:
                missing_hypothesis_text.append(segment_id)
            if not asr_label:
                missing_asr_label.append(segment_id)

            for atom in atoms:
                sres_rows.append(
                    {
                        "sample_id": segment_id,
                        "split": gold.get("split", ""),
                        "asr_run_id": asr_run_id,
                        "reference_text": reference_text,
                        "hypothesis_text": hypothesis_text,
                        "wer": hypothesis.get("wer", ""),
                        "cer": hypothesis.get("cer", ""),
                        "error_type": atom,
                        "severity": str(severity_for(gold)),
                        "downstream_impact": str(
                            downstream_impact_for(gold, reference_label, asr_label)
                        ),
                        "decision_field": atom,
                        "recovery_action": recovery_action,
                        "annotator_note": (
                            f"gold_confusions={gold.get('asr_confusion_terms', '')}; "
                            f"decision_change={gold.get('would_asr_error_change_decision', '')}"
                        ),
                    }
                )

            for index, atom in enumerate(atoms, start=1):
                confusion = confusions[index - 1] if index - 1 < len(confusions) else ""
                ceis_rows.append(
                    {
                        "sample_id": segment_id,
                        "variant_id": f"v_{index:02d}_{slug(atom)}",
                        "base_decision": asr_label,
                        "variant_decision": reference_label,
                        "acoustic_plausibility": first_value(
                            hypothesis,
                            ("variant_plausibility", "acoustic_plausibility", "plausibility"),
                        )
                        or "1.0",
                        "risk_atom_type": atom,
                        "risk_atom_weight": "",
                        "decision_distance": "",
                        "base_transcript": hypothesis_text,
                        "variant_transcript": reference_text,
                        "note": (
                            f"confusion={confusion or 'unspecified'}; "
                            "default_plausibility_until_ASR_confidence_is_available"
                        ),
                    }
                )

            downstream_rows.append(
                {
                    "sample_id": segment_id,
                    "reference_label": reference_label,
                    "asr_label": asr_label,
                    "recovered_label": recovered_label,
                    "recovery_action": recovery_action,
                    "note": (
                        f"audio_id={audio_id}; asr_run_id={asr_run_id}; "
                        f"decision_change={gold.get('would_asr_error_change_decision', '')}"
                    ),
                }
            )

    summary = {
        "gold_rows": len(gold_rows),
        "hypothesis_files": [str(path) for path in hypothesis_paths],
        "sres_rows": len(sres_rows),
        "ceis_rows": len(ceis_rows),
        "downstream_rows": len(downstream_rows),
        "unmatched_hypotheses": unmatched_hypotheses,
        "missing_hypothesis_text": missing_hypothesis_text,
        "missing_asr_label": missing_asr_label,
    }
    return sres_rows, ceis_rows, downstream_rows, summary


def main() -> int:
    root = repo_root_from_script()
    default_gold = (
        root
        / "40_breeze_asr25_finetune_dataset"
        / "reports"
        / "gold_subset_review.tsv"
    )
    default_output = (
        root
        / "70_experiments"
        / "runs"
        / "janus_15_decision_stability_pilot"
        / "artifacts"
        / "metric_inputs"
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("--gold-review", type=Path, default=default_gold)
    parser.add_argument("--hypotheses", type=Path, action="append", required=True)
    parser.add_argument("--output-dir", type=Path, default=default_output)
    parser.add_argument(
        "--allow-incomplete-gold",
        action="store_true",
        help="Use only completed gold rows instead of failing the pilot gate.",
    )
    args = parser.parse_args()

    gold_rows = read_tsv(args.gold_review)
    complete_gold, missing = completed_gold_rows(gold_rows)
    if len(complete_gold) != len(gold_rows) and not args.allow_incomplete_gold:
        print(
            json.dumps(
                {
                    "ok": False,
                    "reason": "gold review is incomplete",
                    "gold_rows": len(gold_rows),
                    "completed_gold_rows": len(complete_gold),
                    "missing_required_fields": missing,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    sres_rows, ceis_rows, downstream_rows, summary = build_rows(
        complete_gold,
        args.hypotheses,
    )

    output_dir = args.output_dir
    write_tsv(
        output_dir / "sres_annotation.tsv",
        sres_rows,
        [
            "sample_id",
            "split",
            "asr_run_id",
            "reference_text",
            "hypothesis_text",
            "wer",
            "cer",
            "error_type",
            "severity",
            "downstream_impact",
            "decision_field",
            "recovery_action",
            "annotator_note",
        ],
    )
    write_tsv(
        output_dir / "counterfactual_variants.tsv",
        ceis_rows,
        [
            "sample_id",
            "variant_id",
            "base_decision",
            "variant_decision",
            "acoustic_plausibility",
            "risk_atom_type",
            "risk_atom_weight",
            "decision_distance",
            "base_transcript",
            "variant_transcript",
            "note",
        ],
    )
    write_tsv(
        output_dir / "downstream_escalation_decisions.tsv",
        downstream_rows,
        [
            "sample_id",
            "reference_label",
            "asr_label",
            "recovered_label",
            "recovery_action",
            "note",
        ],
    )

    summary["ok"] = not (
        summary["unmatched_hypotheses"]
        or summary["missing_hypothesis_text"]
        or summary["missing_asr_label"]
    )
    summary["output_dir"] = str(output_dir)
    (output_dir / "build_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate JANUS 15-row ASR hypotheses before metric-input building."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


AUDIO_ID_FIELDS = ("audio_id", "sample_id", "id")
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
QUALITY_SIGNAL_FIELDS = (
    "wer",
    "cer",
    "confidence",
    "avg_logprob",
    "no_speech_prob",
    "quality_score",
)


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


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


def first_value(row: dict[str, str], fields: tuple[str, ...]) -> str:
    for field in fields:
        value = (row.get(field) or "").strip()
        if value:
            return value
    return ""


def audio_id_for(row: dict[str, str]) -> str:
    return first_value(row, AUDIO_ID_FIELDS)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def read_gold_ids(path: Path) -> set[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        return {
            row["audio_id"]
            for row in csv.DictReader(handle, delimiter="\t")
            if row.get("audio_id")
        }


def read_nemo_ids(path: Path) -> set[str]:
    return {
        str(row.get("audio_id", "")).strip()
        for row in load_jsonl(path)
        if str(row.get("audio_id", "")).strip()
    }


def validate_hypothesis_file(
    path: Path,
    expected_ids: set[str],
    require_labels: bool,
    require_quality_signal: bool,
) -> dict[str, Any]:
    rows = read_rows(path)
    row_ids = [audio_id_for(row) for row in rows]
    id_counts = Counter(audio_id for audio_id in row_ids if audio_id)
    duplicate_ids = sorted(audio_id for audio_id, count in id_counts.items() if count > 1)
    observed_ids = set(id_counts)
    missing_audio_id_rows = [
        index for index, audio_id in enumerate(row_ids, start=1) if not audio_id
    ]
    missing_expected_ids = sorted(expected_ids - observed_ids)
    extra_audio_ids = sorted(observed_ids - expected_ids)
    missing_hypothesis_text = sorted(
        audio_id_for(row) or f"row_{index}"
        for index, row in enumerate(rows, start=1)
        if not first_value(row, HYPOTHESIS_TEXT_FIELDS)
    )
    missing_asr_label = sorted(
        audio_id_for(row) or f"row_{index}"
        for index, row in enumerate(rows, start=1)
        if not first_value(row, ASR_LABEL_FIELDS)
    )
    missing_quality_signal = sorted(
        audio_id_for(row) or f"row_{index}"
        for index, row in enumerate(rows, start=1)
        if not first_value(row, QUALITY_SIGNAL_FIELDS)
    )
    quality_fields_present = sorted(
        field
        for field in QUALITY_SIGNAL_FIELDS
        if any((row.get(field) or "").strip() for row in rows)
    )

    checks = {
        "row_count_matches_expected_ids": len(rows) == len(expected_ids),
        "audio_ids_match_expected_set": not missing_expected_ids and not extra_audio_ids,
        "audio_ids_are_unique": not duplicate_ids,
        "audio_id_field_present": not missing_audio_id_rows,
        "hypothesis_text_present": not missing_hypothesis_text,
        "asr_label_present": not require_labels or not missing_asr_label,
        "quality_signal_present": not require_quality_signal or not missing_quality_signal,
    }
    return {
        "path": str(path),
        "ok": all(checks.values()),
        "checks": checks,
        "counts": {
            "rows": len(rows),
            "expected_ids": len(expected_ids),
            "observed_audio_ids": len(observed_ids),
        },
        "quality_fields_present": quality_fields_present,
        "missing_audio_id_rows": missing_audio_id_rows,
        "missing_expected_audio_ids": missing_expected_ids,
        "extra_audio_ids": extra_audio_ids,
        "duplicate_audio_ids": duplicate_ids,
        "missing_hypothesis_text": missing_hypothesis_text,
        "missing_asr_label": missing_asr_label,
        "missing_quality_signal": missing_quality_signal,
    }


def main() -> int:
    root = repo_root_from_script()
    default_gold = (
        root
        / "40_breeze_asr25_finetune_dataset"
        / "reports"
        / "gold_subset_review.tsv"
    )
    default_nemo = (
        root
        / "40_breeze_asr25_finetune_dataset"
        / "manifests"
        / "nemo_pilot_input_manifest.jsonl"
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("--gold-review", type=Path, default=default_gold)
    parser.add_argument("--nemo-manifest", type=Path, default=default_nemo)
    parser.add_argument("--hypotheses", type=Path, action="append", required=True)
    parser.add_argument("--expected-rows", type=int, default=15)
    parser.add_argument("--require-labels", action="store_true")
    parser.add_argument("--require-quality-signal", action="store_true")
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args()

    gold_ids = read_gold_ids(args.gold_review)
    nemo_ids = read_nemo_ids(args.nemo_manifest)
    expected_ids = gold_ids
    setup_checks = {
        "gold_row_count": len(gold_ids) == args.expected_rows,
        "nemo_row_count": len(nemo_ids) == args.expected_rows,
        "gold_audio_ids_match_nemo_manifest": gold_ids == nemo_ids,
    }
    file_results = [
        validate_hypothesis_file(
            path,
            expected_ids,
            require_labels=args.require_labels,
            require_quality_signal=args.require_quality_signal,
        )
        for path in args.hypotheses
    ]
    result = {
        "ok": all(setup_checks.values()) and all(item["ok"] for item in file_results),
        "setup_checks": setup_checks,
        "expected_audio_ids": sorted(expected_ids),
        "files": file_results,
    }
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

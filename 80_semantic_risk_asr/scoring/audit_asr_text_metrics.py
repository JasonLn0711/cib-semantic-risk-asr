#!/usr/bin/env python3
"""Audit ASR CER/WER definitions over local hypothesis files."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve()
REPO_ROOT = SCRIPT_DIR.parents[2]
ASR_SCRIPT_DIR = REPO_ROOT / "60_whisper_asr_finetuning" / "scripts"
sys.path.insert(0, str(ASR_SCRIPT_DIR))

from asr_text_metrics import edit_stats  # noqa: E402


TEXT_FIELDS = ("reference_text", "human_verified_transcript", "text", "transcript")
HYPOTHESIS_FIELDS = ("hypothesis_text", "pred_text", "prediction", "hypothesis")


METRIC_PROFILES = (
    {
        "metric": "cer_raw_char",
        "unit": "char",
        "normalization": "none",
        "wer_tokenizer": "whitespace",
        "notes": "Raw character edit rate; preserves punctuation, spaces, and case.",
    },
    {
        "metric": "wer_raw_whitespace",
        "unit": "word",
        "normalization": "none",
        "wer_tokenizer": "whitespace",
        "notes": "Legacy whitespace-token WER; invalid as a primary Chinese ASR metric.",
    },
    {
        "metric": "cer_zh_normalized",
        "unit": "char",
        "normalization": "zh_asr",
        "wer_tokenizer": "jieba",
        "notes": "Chinese ASR normalized CER; no traditional/simplified conversion.",
    },
    {
        "metric": "wer_zh_jieba",
        "unit": "word",
        "normalization": "zh_asr",
        "wer_tokenizer": "jieba",
        "notes": "Supplemental Chinese word-level metric using deterministic jieba segmentation.",
    },
)


def read_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".jsonl":
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    with path.open(newline="", encoding="utf-8") as handle:
        delimiter = "\t" if path.suffix == ".tsv" else ","
        return list(csv.DictReader(handle, delimiter=delimiter))


def first_value(row: dict[str, Any], fields: tuple[str, ...]) -> str:
    for field in fields:
        value = str(row.get(field) or "").strip()
        if value:
            return value
    return ""


def infer_run_id(path: Path, rows: list[dict[str, Any]]) -> str:
    for row in rows:
        value = str(row.get("asr_run_id") or row.get("run_id") or "").strip()
        if value:
            return value
    return path.parent.parent.name if path.parent.name == "predictions" else path.stem


def summarize(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = read_rows(path)
    run_id = infer_run_id(path, rows)
    output_rows: list[dict[str, Any]] = []
    stored_cer: list[float] = []
    stored_wer: list[float] = []
    missing_reference = 0
    missing_hypothesis = 0
    profile_rates: dict[str, list[float]] = {profile["metric"]: [] for profile in METRIC_PROFILES}
    profile_edits: dict[str, int] = {profile["metric"]: 0 for profile in METRIC_PROFILES}
    profile_ref_units: dict[str, int] = {profile["metric"]: 0 for profile in METRIC_PROFILES}

    for row in rows:
        reference = first_value(row, TEXT_FIELDS)
        hypothesis = first_value(row, HYPOTHESIS_FIELDS)
        if not reference:
            missing_reference += 1
        if not hypothesis:
            missing_hypothesis += 1
        for field, target in (("cer", stored_cer), ("wer", stored_wer)):
            value = str(row.get(field) or "").strip()
            if value:
                target.append(float(value))
        for profile in METRIC_PROFILES:
            stats = edit_stats(
                reference,
                hypothesis,
                unit=str(profile["unit"]),
                normalization=str(profile["normalization"]),
                wer_tokenizer=str(profile["wer_tokenizer"]),
            )
            metric = str(profile["metric"])
            profile_rates[metric].append(stats.rate_percent)
            profile_edits[metric] += stats.edits
            profile_ref_units[metric] += stats.reference_units

    for profile in METRIC_PROFILES:
        metric = str(profile["metric"])
        rates = profile_rates[metric]
        edits = profile_edits[metric]
        ref_units = profile_ref_units[metric]
        output_rows.append(
            {
                "run_id": run_id,
                "rows": len(rows),
                "metric": metric,
                "unit": profile["unit"],
                "normalization": profile["normalization"],
                "wer_tokenizer": profile["wer_tokenizer"],
                "macro_percent": round(sum(rates) / len(rates), 2) if rates else 0.0,
                "micro_percent": round(edits / ref_units * 100.0, 2) if ref_units else 0.0,
                "edit_count": edits,
                "reference_unit_count": ref_units,
                "stored_cer_mean": round(sum(stored_cer) / len(stored_cer), 2) if stored_cer else "",
                "stored_wer_mean": round(sum(stored_wer) / len(stored_wer), 2) if stored_wer else "",
                "missing_reference_rows": missing_reference,
                "missing_hypothesis_rows": missing_hypothesis,
                "notes": profile["notes"],
            }
        )
    return output_rows, {
        "path": str(path),
        "run_id": run_id,
        "rows": len(rows),
        "missing_reference_rows": missing_reference,
        "missing_hypothesis_rows": missing_hypothesis,
    }


def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "run_id",
        "rows",
        "metric",
        "unit",
        "normalization",
        "wer_tokenizer",
        "macro_percent",
        "micro_percent",
        "edit_count",
        "reference_unit_count",
        "stored_cer_mean",
        "stored_wer_mean",
        "missing_reference_rows",
        "missing_hypothesis_rows",
        "notes",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hypotheses", nargs="+", type=Path, required=True)
    parser.add_argument("--output-tsv", type=Path, required=True)
    parser.add_argument("--summary-json", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    all_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for path in args.hypotheses:
        rows, summary = summarize(path)
        all_rows.extend(rows)
        summaries.append(summary)
    write_tsv(args.output_tsv, all_rows)
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.write_text(
        json.dumps(
            {
                "ok": all(
                    summary["missing_reference_rows"] == 0
                    and summary["missing_hypothesis_rows"] == 0
                    for summary in summaries
                ),
                "hypothesis_files": [str(path) for path in args.hypotheses],
                "output_tsv": str(args.output_tsv),
                "summaries": summaries,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {"ok": True, "output_tsv": str(args.output_tsv), "summary_json": str(args.summary_json)},
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

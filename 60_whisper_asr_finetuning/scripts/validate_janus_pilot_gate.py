#!/usr/bin/env python3
"""Validate whether the JANUS 15-row pilot gate is ready to run."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


REQUIRED_GOLD_FIELDS = (
    "human_verified_transcript",
    "semantic_risk_label",
    "risk_atoms",
    "asr_confusion_terms",
    "would_asr_error_change_decision",
)

LONG_SILENCE_REVIEW_FIELDS = (
    "review_status",
    "reviewer",
    "review_date",
)


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def missing_required_fields(rows: list[dict[str, str]], fields: tuple[str, ...]) -> dict[str, list[str]]:
    return {
        field: [
            row.get("audio_id", f"row_{index}")
            for index, row in enumerate(rows, start=1)
            if not (row.get(field) or "").strip()
        ]
        for field in fields
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    root = repo_root_from_script()
    reports_dir = root / "40_breeze_asr25_finetune_dataset" / "reports"
    manifests_dir = root / "40_breeze_asr25_finetune_dataset" / "manifests"
    parser.add_argument("--gold-review", type=Path, default=reports_dir / "gold_subset_review.tsv")
    parser.add_argument("--health-check", type=Path, default=reports_dir / "audio_health_check.csv")
    parser.add_argument("--long-silence-review", type=Path, default=reports_dir / "long_silence_review.tsv")
    parser.add_argument("--nemo-manifest", type=Path, default=manifests_dir / "nemo_pilot_input_manifest.jsonl")
    parser.add_argument("--expected-gold-rows", type=int, default=15)
    args = parser.parse_args()

    gold_rows = read_tsv(args.gold_review)
    health_rows = read_csv(args.health_check)
    long_silence_rows = read_tsv(args.long_silence_review)
    nemo_rows = read_jsonl(args.nemo_manifest)

    non_ok_health = [
        row for row in health_rows if (row.get("flags") or "").strip() not in ("", "ok")
    ]
    missing_gold = missing_required_fields(gold_rows, REQUIRED_GOLD_FIELDS)
    missing_long_silence = missing_required_fields(
        long_silence_rows,
        LONG_SILENCE_REVIEW_FIELDS,
    )

    gold_ids = {row["audio_id"] for row in gold_rows}
    nemo_ids = {str(row.get("audio_id", "")) for row in nemo_rows}
    health_long_silence_ids = {row["audio_id"] for row in non_ok_health}
    review_long_silence_ids = {row["audio_id"] for row in long_silence_rows}

    checks = {
        "gold_row_count": len(gold_rows) == args.expected_gold_rows,
        "gold_required_fields_complete": not any(missing_gold.values()),
        "nemo_manifest_row_count": len(nemo_rows) == len(gold_rows),
        "nemo_manifest_audio_ids_match_gold": nemo_ids == gold_ids,
        "health_flags_only_long_silence": all(
            row.get("flags") == "long_silence" for row in non_ok_health
        ),
        "long_silence_review_matches_health": review_long_silence_ids == health_long_silence_ids,
        "long_silence_review_complete": not any(missing_long_silence.values()),
    }

    result = {
        "ok": all(checks.values()),
        "checks": checks,
        "counts": {
            "gold_rows": len(gold_rows),
            "gold_completed_rows": sum(
                1
                for row in gold_rows
                if all((row.get(field) or "").strip() for field in REQUIRED_GOLD_FIELDS)
            ),
            "nemo_rows": len(nemo_rows),
            "health_non_ok_rows": len(non_ok_health),
            "long_silence_review_rows": len(long_silence_rows),
            "long_silence_completed_rows": sum(
                1
                for row in long_silence_rows
                if all((row.get(field) or "").strip() for field in LONG_SILENCE_REVIEW_FIELDS)
            ),
        },
        "missing_gold_required_fields": missing_gold,
        "missing_long_silence_review_fields": missing_long_silence,
        "nemo_missing_audio_ids": sorted(gold_ids - nemo_ids),
        "nemo_extra_audio_ids": sorted(nemo_ids - gold_ids),
        "long_silence_missing_review_audio_ids": sorted(
            health_long_silence_ids - review_long_silence_ids
        ),
        "long_silence_extra_review_audio_ids": sorted(
            review_long_silence_ids - health_long_silence_ids
        ),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

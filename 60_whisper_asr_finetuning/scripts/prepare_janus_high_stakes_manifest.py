#!/usr/bin/env python3
"""Prepare the selected JANUS high-stakes expansion manifest for ASR runs."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def repo_relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def selected_ids(path: Path) -> list[str]:
    rows = read_tsv(path)
    ids = [row.get("audio_id", "").strip() for row in rows if row.get("audio_id", "").strip()]
    if len(ids) != len(set(ids)):
        duplicates = sorted({audio_id for audio_id in ids if ids.count(audio_id) > 1})
        raise SystemExit({"duplicate_selected_audio_ids": duplicates})
    return ids


def runner_row(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    audio_id = str(row.get("id", "")).strip()
    split = str(row.get("split", "")).strip()
    if audio_id and split:
        audio_path = f"40_breeze_asr25_finetune_dataset/hf_audiofolder/{split}/audio/{audio_id}.wav"
        output["audio"] = audio_path
        output["audio_filepath"] = audio_path
    return output


def parse_args() -> argparse.Namespace:
    root = repo_root_from_script()
    run_dir = root / "70_experiments" / "runs" / "janus_300_500_high_stakes_expansion"
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection", type=Path, default=run_dir / "artifacts" / "expansion_candidates.tsv")
    parser.add_argument(
        "--source-manifest",
        type=Path,
        default=root / "40_breeze_asr25_finetune_dataset" / "manifests" / "all.jsonl",
    )
    parser.add_argument(
        "--output-manifest",
        type=Path,
        default=run_dir / "artifacts" / "high_stakes_300_manifest.jsonl",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=run_dir / "high_stakes_manifest_summary.tsv",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root_from_script()
    ids = selected_ids(args.selection)
    source_by_id = {str(row.get("id", "")).strip(): row for row in read_jsonl(args.source_manifest)}
    missing = [audio_id for audio_id in ids if audio_id not in source_by_id]
    if missing:
        raise SystemExit({"missing_source_manifest_ids": missing})

    output_rows = [runner_row(source_by_id[audio_id]) for audio_id in ids]
    write_jsonl(args.output_manifest, output_rows)

    splits = Counter(str(row.get("split", "")) for row in output_rows)
    durations = [as_float(row.get("duration")) for row in output_rows]
    summary_rows: list[dict[str, Any]] = [
        {"metric": "selected_rows", "value": len(output_rows), "notes": "manifest rows"},
        {
            "metric": "source_manifest_rows",
            "value": len(source_by_id),
            "notes": repo_relative(args.source_manifest, root),
        },
        {"metric": "missing_selected_ids", "value": len(missing), "notes": "must be zero"},
        {
            "metric": "duration_min_sec",
            "value": round(min(durations), 3) if durations else "",
            "notes": "selected manifest rows",
        },
        {
            "metric": "duration_max_sec",
            "value": round(max(durations), 3) if durations else "",
            "notes": "selected manifest rows",
        },
        {
            "metric": "duration_mean_sec",
            "value": round(sum(durations) / len(durations), 3) if durations else "",
            "notes": "selected manifest rows",
        },
    ]
    for split, count in sorted(splits.items()):
        summary_rows.append({"metric": f"split_{split}", "value": count, "notes": "manifest rows"})

    write_tsv(args.summary, summary_rows, ["metric", "value", "notes"])
    print(
        json.dumps(
            {
                "ok": len(output_rows) == len(ids),
                "rows": len(output_rows),
                "output_manifest": str(args.output_manifest),
                "summary": str(args.summary),
                "split_counts": dict(sorted(splits.items())),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

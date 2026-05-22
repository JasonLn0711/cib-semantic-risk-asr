#!/usr/bin/env python3
"""Validate the local Whisper-ready JANUS AudioFolder dataset."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


SPLITS = ("train", "validation", "test")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def count_jsonl(path: Path) -> int:
    with path.open(encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def validate_split(dataset_dir: Path, manifests_dir: Path, split: str, max_errors: int) -> dict[str, object]:
    split_dir = dataset_dir / split
    metadata_path = split_dir / "metadata.csv"
    manifest_path = manifests_dir / f"{split}.jsonl"
    errors: list[str] = []

    if not metadata_path.exists():
        return {"split": split, "ok": False, "errors": [f"missing metadata: {metadata_path}"]}

    rows = read_csv_rows(metadata_path)
    duration_seconds = 0.0
    missing_audio = 0
    missing_text = 0

    for index, row in enumerate(rows, start=2):
        file_name = row.get("file_name", "")
        text = row.get("sentence") or row.get("text") or ""

        if not text.strip():
            missing_text += 1
            if len(errors) < max_errors:
                errors.append(f"{metadata_path}:{index}: missing transcript text")

        audio_path = split_dir / file_name
        if not file_name or not audio_path.exists():
            missing_audio += 1
            if len(errors) < max_errors:
                errors.append(f"{metadata_path}:{index}: missing audio {file_name!r}")

        try:
            duration_seconds += float(row.get("duration", "0") or 0)
        except ValueError:
            if len(errors) < max_errors:
                errors.append(f"{metadata_path}:{index}: invalid duration {row.get('duration')!r}")

    manifest_rows = count_jsonl(manifest_path) if manifest_path.exists() else None
    if manifest_rows is not None and manifest_rows != len(rows):
        errors.append(f"{split}: metadata rows {len(rows)} != manifest rows {manifest_rows}")

    return {
        "split": split,
        "ok": not errors and missing_audio == 0 and missing_text == 0,
        "metadata_rows": len(rows),
        "manifest_rows": manifest_rows,
        "duration_seconds": round(duration_seconds, 3),
        "duration_hours": round(duration_seconds / 3600, 3),
        "missing_audio": missing_audio,
        "missing_text": missing_text,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    workspace_root = Path(__file__).resolve().parents[1]
    default_dataset = workspace_root / "datasets" / "janus_165_v1" / "hf_audiofolder"
    default_manifests = workspace_root / "datasets" / "janus_165_v1" / "manifests"
    parser.add_argument("--dataset-dir", type=Path, default=default_dataset)
    parser.add_argument("--manifests-dir", type=Path, default=default_manifests)
    parser.add_argument("--max-errors", type=int, default=20)
    args = parser.parse_args()

    results = [
        validate_split(args.dataset_dir, args.manifests_dir, split, args.max_errors)
        for split in SPLITS
    ]
    summary = {
        "dataset_dir": str(args.dataset_dir),
        "manifests_dir": str(args.manifests_dir),
        "ok": all(result["ok"] for result in results),
        "splits": results,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

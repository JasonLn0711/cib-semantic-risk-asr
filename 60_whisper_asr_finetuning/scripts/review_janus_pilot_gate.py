#!/usr/bin/env python3
"""Interactively fill local JANUS pilot-gate review TSV files."""

from __future__ import annotations

import argparse
import csv
import shlex
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path


GOLD_REQUIRED_FIELDS = (
    "human_verified_transcript",
    "semantic_risk_label",
    "risk_atoms",
    "asr_confusion_terms",
    "would_asr_error_change_decision",
)

GOLD_REVIEW_FIELDS = (
    "human_verified_transcript",
    "semantic_risk_label",
    "risk_atoms",
    "asr_confusion_terms",
    "would_asr_error_change_decision",
    "reviewer",
    "review_date",
    "review_notes",
)

LONG_SILENCE_REQUIRED_FIELDS = (
    "review_status",
    "reviewer",
    "review_date",
)

LONG_SILENCE_REVIEW_FIELDS = (
    "review_status",
    "reviewer",
    "review_date",
    "review_notes",
)

FIELD_HINTS = {
    "semantic_risk_label": (
        "no_escalation | review | priority_review | critical_escalation"
    ),
    "risk_atoms": (
        "pipe-delimited subset of "
        "negation|amount|action|actor|intent|time|uncertainty|scam_pattern"
    ),
    "asr_confusion_terms": "compact note, or none_observed",
    "would_asr_error_change_decision": "yes | no | unclear",
    "review_status": (
        "valid_call_pause | contextual_silence_ok | "
        "segmentation_review_needed | exclude_from_pilot"
    ),
    "review_date": "YYYY-MM-DD",
}


class ReviewQuit(Exception):
    """Raised when the reviewer chooses to stop the session."""


class ReviewSkip(Exception):
    """Raised when the reviewer chooses to skip the current row."""


@dataclass(frozen=True)
class ReviewMode:
    name: str
    path: Path
    review_fields: tuple[str, ...]
    required_fields: tuple[str, ...]


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def read_tsv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run build_janus_curation_artifacts.py first."
        )
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader), list(reader.fieldnames or [])


def write_tsv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def missing_fields(row: dict[str, str], fields: tuple[str, ...]) -> list[str]:
    return [field for field in fields if not (row.get(field) or "").strip()]


def sanitize(value: str) -> str:
    return " ".join(value.replace("\t", " ").splitlines()).strip()


def review_default(field: str, reviewer: str, review_date: str) -> str:
    if field == "reviewer":
        return reviewer
    if field == "review_date":
        return review_date
    return ""


def prompt_field(field: str, current: str, default: str = "") -> str:
    hint = FIELD_HINTS.get(field, "")
    suffix_parts = []
    if current:
        suffix_parts.append(f"current: {current}")
    elif default:
        suffix_parts.append(f"default: {default}")
    if hint:
        suffix_parts.append(hint)
    suffix = f" [{'; '.join(suffix_parts)}]" if suffix_parts else ""

    value = input(f"{field}{suffix}: ").strip()
    if value == ":quit":
        raise ReviewQuit
    if value == ":skip":
        raise ReviewSkip
    if value == "":
        return current or default
    return sanitize(value)


def audio_command(row: dict[str, str], root: Path, player: str) -> tuple[list[str], str]:
    audio_path = root / row.get("path", "")
    args = [player, "-nodisp", "-autoexit", str(audio_path)]
    printable = " ".join(shlex.quote(part) for part in args)
    return args, printable


def print_row_context(
    row: dict[str, str],
    root: Path,
    player: str,
) -> list[str]:
    play_args, printable = audio_command(row, root, player)
    print()
    print("=" * 72)
    print(f"audio_id: {row.get('audio_id', '')}")
    print(f"split: {row.get('split', '')}")
    print(f"duration_sec: {row.get('duration_sec', '')}")
    if row.get("max_silence_sec"):
        print(f"max_silence_sec: {row.get('max_silence_sec', '')}")
    print(f"path: {row.get('path', '')}")
    print(f"risk_keyword_hits: {row.get('risk_keyword_hits', '')}")
    print("play:")
    print(f"  {printable}")
    print("candidate_reference_transcript:")
    print(row.get("candidate_reference_transcript", ""))
    print()
    print("Commands: Enter keeps current/default, :skip skips row, :quit stops.")
    return play_args


def maybe_play(play_args: list[str], should_play: bool) -> None:
    if not should_play:
        return
    try:
        subprocess.run(play_args, check=False)
    except FileNotFoundError:
        print(f"Could not find player: {play_args[0]}")


def list_incomplete(rows: list[dict[str, str]], mode: ReviewMode) -> int:
    incomplete = [
        (row, missing_fields(row, mode.required_fields))
        for row in rows
        if missing_fields(row, mode.required_fields)
    ]
    if not incomplete:
        print(f"{mode.name}: all rows complete")
        return 0

    print(f"{mode.name}: {len(incomplete)} incomplete row(s)")
    for row, missing in incomplete:
        print(f"- {row.get('audio_id', '')}: missing {', '.join(missing)}")
    return 0


def select_rows(
    rows: list[dict[str, str]],
    mode: ReviewMode,
    audio_id: str | None,
) -> list[int]:
    if audio_id:
        matches = [
            index
            for index, row in enumerate(rows)
            if row.get("audio_id", "") == audio_id
        ]
        if not matches:
            raise ValueError(f"No row found for audio_id={audio_id}")
        return matches

    incomplete = [
        index
        for index, row in enumerate(rows)
        if missing_fields(row, mode.required_fields)
    ]
    return incomplete


def review_row(
    row: dict[str, str],
    mode: ReviewMode,
    reviewer: str,
    review_date: str,
) -> dict[str, str]:
    updated = dict(row)
    for field in mode.review_fields:
        updated[field] = prompt_field(
            field,
            current=row.get(field, ""),
            default=review_default(field, reviewer, review_date),
        )
    return updated


def mode_from_args(root: Path, mode_name: str) -> ReviewMode:
    reports_dir = root / "40_breeze_asr25_finetune_dataset" / "reports"
    if mode_name == "gold":
        return ReviewMode(
            name="gold",
            path=reports_dir / "gold_subset_review.tsv",
            review_fields=GOLD_REVIEW_FIELDS,
            required_fields=GOLD_REQUIRED_FIELDS,
        )
    return ReviewMode(
        name="long-silence",
        path=reports_dir / "long_silence_review.tsv",
        review_fields=LONG_SILENCE_REVIEW_FIELDS,
        required_fields=LONG_SILENCE_REQUIRED_FIELDS,
    )


def main() -> int:
    root = repo_root_from_script()
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("gold", "long-silence"), default="gold")
    parser.add_argument("--audio-id")
    parser.add_argument("--reviewer", default="")
    parser.add_argument("--review-date", default=date.today().isoformat())
    parser.add_argument("--play", action="store_true")
    parser.add_argument("--player", default="ffplay")
    parser.add_argument("--list-incomplete", action="store_true")
    args = parser.parse_args()

    mode = mode_from_args(root, args.mode)
    rows, fieldnames = read_tsv(mode.path)
    missing_columns = [field for field in mode.review_fields if field not in fieldnames]
    if missing_columns:
        raise ValueError(
            f"{mode.path} is missing expected column(s): {', '.join(missing_columns)}"
        )

    if args.list_incomplete:
        return list_incomplete(rows, mode)

    row_indices = select_rows(rows, mode, args.audio_id)
    if not row_indices:
        print(f"{mode.name}: no incomplete rows")
        return 0

    completed = 0
    try:
        for index in row_indices:
            row = rows[index]
            play_args = print_row_context(row, root, args.player)
            maybe_play(play_args, args.play)
            try:
                rows[index] = review_row(
                    row,
                    mode=mode,
                    reviewer=args.reviewer,
                    review_date=args.review_date,
                )
            except ReviewSkip:
                print(f"Skipped {row.get('audio_id', '')}")
                continue
            write_tsv(mode.path, rows, fieldnames)
            completed += 1
            print(f"Saved {row.get('audio_id', '')} -> {mode.path}")
    except ReviewQuit:
        print("Stopped review session.")

    print(f"{mode.name}: saved {completed} row(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

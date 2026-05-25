#!/usr/bin/env python3
"""Build local JANUS audio curation artifacts.

The generated files live under ignored dataset/report directories because they
contain call metadata and transcripts. The script itself is tracked so the
curation pass is reproducible.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shlex
import statistics
import warnings
import wave
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


warnings.filterwarnings("ignore", category=DeprecationWarning, message="'audioop' is deprecated.*")
import audioop


SPLITS = ("train", "validation", "test")

RISK_TERMS = (
    "詐騙",
    "報案",
    "匯款",
    "帳戶",
    "銀行",
    "身分證",
    "健保卡",
    "保險",
    "LINE",
    "投資",
    "提款卡",
    "刷卡",
    "警察",
    "戶政",
    "郵局",
    "預警",
    "客服",
    "和解",
    "信託",
    "外幣",
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


@dataclass
class AudioStats:
    ok: bool
    duration_sec: float | None = None
    sample_rate: int | None = None
    channels: int | None = None
    sample_width_bytes: int | None = None
    format_name: str = "wav"
    frame_count: int | None = None
    peak_ratio: float | None = None
    rms_ratio: float | None = None
    max_silence_sec: float | None = None
    error: str = ""


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def read_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def read_sources(manifests_dir: Path) -> dict[str, dict[str, str]]:
    by_id: dict[str, dict[str, str]] = {}
    for split in SPLITS:
        source_path = manifests_dir / f"{split}_with_sources.tsv"
        with source_path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                by_id[row["id"]] = row
    return by_id


def path_without_resolving_symlink(path: Path) -> Path:
    return Path(os.path.normpath(str(path)))


def relpath(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def max_possible_amplitude(sample_width: int) -> float:
    if sample_width <= 0:
        return 1.0
    return float(2 ** (8 * sample_width - 1))


def inspect_wav(path: Path, silence_threshold: float, silence_window_sec: float) -> AudioStats:
    try:
        with wave.open(str(path), "rb") as wav_file:
            channels = wav_file.getnchannels()
            sample_rate = wav_file.getframerate()
            sample_width = wav_file.getsampwidth()
            frame_count = wav_file.getnframes()
            duration_sec = frame_count / sample_rate if sample_rate else 0.0
            frames_per_chunk = max(1, int(sample_rate * 0.1)) if sample_rate else 1600
            amplitude = max_possible_amplitude(sample_width)
            total_rms_weighted = 0.0
            total_frames = 0
            peak_ratio = 0.0
            current_silence = 0.0
            max_silence = 0.0

            while True:
                frames = wav_file.readframes(frames_per_chunk)
                if not frames:
                    break
                chunk_frames = len(frames) / max(1, channels * sample_width)
                chunk_sec = chunk_frames / sample_rate if sample_rate else 0.0
                rms_ratio = audioop.rms(frames, sample_width) / amplitude
                chunk_peak = audioop.max(frames, sample_width) / amplitude
                peak_ratio = max(peak_ratio, chunk_peak)
                total_rms_weighted += rms_ratio * chunk_frames
                total_frames += int(chunk_frames)

                if rms_ratio <= silence_threshold:
                    current_silence += chunk_sec
                else:
                    max_silence = max(max_silence, current_silence)
                    current_silence = 0.0

            max_silence = max(max_silence, current_silence)
            rms_ratio = total_rms_weighted / total_frames if total_frames else 0.0
            return AudioStats(
                ok=True,
                duration_sec=duration_sec,
                sample_rate=sample_rate,
                channels=channels,
                sample_width_bytes=sample_width,
                frame_count=frame_count,
                peak_ratio=peak_ratio,
                rms_ratio=rms_ratio,
                max_silence_sec=max_silence if max_silence >= silence_window_sec else max_silence,
            )
    except (EOFError, wave.Error, OSError) as exc:
        return AudioStats(ok=False, error=str(exc))


def source_date_from(*values: str) -> str:
    for value in values:
        match = re.search(r"\d{4}-\d{2}-\d{2}", value or "")
        if match:
            return match.group(0)
    return ""


def risk_term_hits(text: str) -> list[str]:
    return [term for term in RISK_TERMS if term in text]


def load_rows(repo_root: Path, manifests_dir: Path) -> list[dict[str, object]]:
    manifest_rows = read_jsonl(manifests_dir / "all.jsonl")
    source_rows = read_sources(manifests_dir)
    loaded: list[dict[str, object]] = []
    for row in manifest_rows:
        audio_id = str(row["id"])
        split = str(row["split"])
        source = source_rows.get(audio_id, {})
        overlay_abs = path_without_resolving_symlink(manifests_dir / str(row["audio"]))
        text = str(row.get("sentence") or row.get("text") or "")
        loaded.append(
            {
                "audio_id": audio_id,
                "split": split,
                "overlay_abs": overlay_abs,
                "overlay_rel": relpath(overlay_abs, repo_root),
                "resolved_abs": overlay_abs.resolve(strict=False),
                "manifest_duration_sec": float(row.get("duration") or 0.0),
                "alignment_score": row.get("alignment_score", ""),
                "text": text,
                "source_manifest": source.get("source_manifest", ""),
                "source_manifest_split": source.get("source_manifest_split", ""),
                "source_manifest_line": source.get("source_manifest_line", ""),
                "original_file_name": source.get("original_file_name", ""),
                "source_audio_relative": source.get("source_audio_relative", ""),
                "candidate_match_count": source.get("candidate_match_count", ""),
                "source_date": source_date_from(
                    source.get("original_file_name", ""),
                    source.get("source_audio_relative", ""),
                    source.get("source_manifest", ""),
                ),
                "risk_terms": risk_term_hits(text),
            }
        )
    return loaded


def write_csv(path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_tsv(path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_jsonl(path: Path, rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_existing_gold_reviews(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        return {
            row.get("audio_id", ""): row
            for row in csv.DictReader(handle, delimiter="\t")
            if row.get("audio_id")
        }


def flag_row(
    row: dict[str, object],
    stats: AudioStats,
    modal_sample_rate: int | None,
    modal_channels: int | None,
    min_duration_sec: float,
    max_manifest_delta_sec: float,
    long_silence_sec: float,
) -> list[str]:
    flags: list[str] = []
    if not Path(str(row["overlay_abs"])).exists():
        flags.append("missing_audio")
    if not stats.ok:
        flags.append("wav_read_error")
        return flags
    if stats.duration_sec is not None and stats.duration_sec <= 0:
        flags.append("empty_or_zero_duration")
    if stats.duration_sec is not None and stats.duration_sec < min_duration_sec:
        flags.append("ultra_short")
    if modal_sample_rate is not None and stats.sample_rate != modal_sample_rate:
        flags.append("non_modal_sample_rate")
    if modal_channels is not None and stats.channels != modal_channels:
        flags.append("non_modal_channels")
    if stats.peak_ratio is not None and stats.peak_ratio >= 0.999:
        flags.append("possible_clipping")
    if stats.max_silence_sec is not None and stats.max_silence_sec >= long_silence_sec:
        flags.append("long_silence")
    manifest_duration = float(row["manifest_duration_sec"])
    if stats.duration_sec is not None and abs(stats.duration_sec - manifest_duration) > max_manifest_delta_sec:
        flags.append("manifest_duration_mismatch")
    return flags


def select_gold_subset(rows: list[dict[str, object]], sample_size: int) -> list[dict[str, object]]:
    quotas = {"train": max(1, sample_size - 6), "validation": 3, "test": 3}
    selected: list[dict[str, object]] = []
    seen: set[str] = set()

    def sort_key(row: dict[str, object]) -> tuple[float, float, str]:
        risk_count = len(row.get("risk_terms", []))
        alignment = float(row.get("alignment_score") or 0.0)
        duration = float(row.get("manifest_duration_sec") or 0.0)
        return (-risk_count, alignment, -duration, str(row["audio_id"]))

    rows_by_split: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        rows_by_split[str(row["split"])].append(row)

    for split in SPLITS:
        candidates = sorted(rows_by_split[split], key=sort_key)
        for row in candidates[: quotas.get(split, 0)]:
            selected.append(row)
            seen.add(str(row["audio_id"]))

    if len(selected) < sample_size:
        for row in sorted(rows, key=sort_key):
            audio_id = str(row["audio_id"])
            if audio_id not in seen:
                selected.append(row)
                seen.add(audio_id)
            if len(selected) >= sample_size:
                break
    return selected[:sample_size]


def write_gold_subset(path: Path, selected: list[dict[str, object]]) -> list[dict[str, object]]:
    fields = [
        "audio_id",
        "split",
        "path",
        "duration_sec",
        "alignment_score",
        "source_audio_relative",
        "candidate_reference_transcript",
        "risk_keyword_hits",
        "human_verified_transcript",
        "semantic_risk_label",
        "risk_atoms",
        "asr_confusion_terms",
        "would_asr_error_change_decision",
        "reviewer",
        "review_date",
        "review_notes",
    ]
    existing_reviews = read_existing_gold_reviews(path)
    out_rows = []
    for row in selected:
        audio_id = str(row["audio_id"])
        existing = existing_reviews.get(audio_id, {})
        out_row = {
            "audio_id": audio_id,
            "split": row["split"],
            "path": row["overlay_rel"],
            "duration_sec": row["duration_sec"],
            "alignment_score": row["alignment_score"],
            "source_audio_relative": row["source_audio_relative"],
            "candidate_reference_transcript": row["text"],
            "risk_keyword_hits": "|".join(row.get("risk_terms", [])),
        }
        for field in GOLD_REVIEW_FIELDS:
            out_row[field] = existing.get(field, "")
        out_rows.append(out_row)
    write_tsv(path, out_rows, fields)
    return out_rows


def completed_gold_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    required = GOLD_REVIEW_FIELDS[:5]
    return [
        row
        for row in rows
        if all(str(row.get(field, "")).strip() for field in required)
    ]


def write_gold_completion_summary(path: Path, rows: list[dict[str, object]]) -> None:
    required = GOLD_REVIEW_FIELDS[:5]
    completed = completed_gold_rows(rows)
    missing_by_field = {
        field: sum(1 for row in rows if not str(row.get(field, "")).strip())
        for field in required
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""# Gold Subset Completion Summary

Generated: {datetime.now().isoformat(timespec="seconds")}

## Gate Status

- Gold rows: {len(rows)}
- Completed rows: {len(completed)}
- Gate ready for NeMo/Whisper/Breeze pilot metrics: {"yes" if len(completed) == len(rows) and rows else "no"}

## Required Review Fields

{chr(10).join(f"- `{field}` missing rows: {count}" for field, count in missing_by_field.items())}

## Rule

Do not treat this subset as gold until every row has the five required review
fields filled. Candidate transcripts remain candidate references only.
""",
        encoding="utf-8",
    )


def write_long_silence_review(
    path: Path,
    rows: list[dict[str, object]],
    stats_by_id: dict[str, AudioStats],
) -> list[dict[str, object]]:
    fields = [
        "audio_id",
        "split",
        "path",
        "duration_sec",
        "max_silence_sec",
        "rms_ratio",
        "peak_ratio",
        "candidate_reference_transcript",
        "risk_keyword_hits",
        "review_status",
        "reviewer",
        "review_date",
        "review_notes",
    ]
    existing_reviews = read_existing_gold_reviews(path)
    out_rows = []
    for row in rows:
        if "long_silence" not in str(row.get("health_flags", "")):
            continue
        audio_id = str(row["audio_id"])
        existing = existing_reviews.get(audio_id, {})
        stats = stats_by_id[str(row["audio_id"])]
        out_rows.append(
            {
                "audio_id": audio_id,
                "split": row["split"],
                "path": row["overlay_rel"],
                "duration_sec": row["duration_sec"],
                "max_silence_sec": round(stats.max_silence_sec, 3)
                if stats.max_silence_sec is not None
                else "",
                "rms_ratio": round(stats.rms_ratio, 6) if stats.rms_ratio is not None else "",
                "peak_ratio": round(stats.peak_ratio, 6) if stats.peak_ratio is not None else "",
                "candidate_reference_transcript": row["text"],
                "risk_keyword_hits": "|".join(row.get("risk_terms", [])),
                "review_status": existing.get("review_status", ""),
                "reviewer": existing.get("reviewer", ""),
                "review_date": existing.get("review_date", ""),
                "review_notes": existing.get("review_notes", ""),
            }
        )
    write_tsv(path, out_rows, fields)
    return out_rows


def ffplay_command(path: object) -> str:
    return f"ffplay -nodisp -autoexit {shlex.quote(str(path))}"


def write_gold_review_packet(
    path: Path,
    gold_rows: list[dict[str, object]],
    long_silence_rows: list[dict[str, object]],
) -> None:
    gold_sections = []
    for index, row in enumerate(gold_rows, start=1):
        audio_path = row["path"]
        gold_sections.append(
            f"""### {index}. {row['audio_id']}

- Split: `{row['split']}`
- Duration: `{row['duration_sec']}` seconds
- Risk keyword hits: `{row['risk_keyword_hits']}`
- Audio:
  ```bash
  {ffplay_command(audio_path)}
  ```
- Candidate reference transcript:
  ```text
  {row['candidate_reference_transcript']}
  ```
- Fill in `gold_subset_review.tsv`:
  - `human_verified_transcript`:
  - `semantic_risk_label`: one of `no_escalation`, `review`, `priority_review`, `critical_escalation`
  - `risk_atoms`: pipe-delimited subset of `negation|amount|action|actor|intent|time|uncertainty|scam_pattern`
  - `asr_confusion_terms`: compact note such as `匯款/未匯款`, `三萬/三十萬`, or `none_observed`
  - `would_asr_error_change_decision`: `yes`, `no`, or `unclear`
"""
        )

    silence_sections = []
    for index, row in enumerate(long_silence_rows, start=1):
        audio_path = row["path"]
        silence_sections.append(
            f"""### {index}. {row['audio_id']}

- Split: `{row['split']}`
- Duration: `{row['duration_sec']}` seconds
- Max silence: `{row['max_silence_sec']}` seconds
- Audio:
  ```bash
  {ffplay_command(audio_path)}
  ```
- Candidate reference transcript:
  ```text
  {row['candidate_reference_transcript']}
  ```
- Fill in `long_silence_review.tsv`:
  - `review_status`: one of `valid_call_pause`, `contextual_silence_ok`, `segmentation_review_needed`, `exclude_from_pilot`
  - `reviewer`:
  - `review_date`: YYYY-MM-DD
  - `review_notes`:
"""
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""# JANUS 15-Row Gold Review Packet

Generated: {datetime.now().isoformat(timespec="seconds")}

This file is a local review aid. It may contain candidate transcript text and
audio paths, so it stays under the ignored `reports/` directory and is not a
Git artifact.

## Review Rules

1. Listen to the audio before filling `human_verified_transcript`.
2. Correct only what you can verify from the audio.
3. Mark decision-critical atoms, not every typo.
4. Use `none_observed` in `asr_confusion_terms` only if no plausible
   decision-changing ASR confusion is visible after listening.
5. The NeMo/Whisper/Breeze pilot gate stays closed until
   `validate_janus_pilot_gate.py` returns `ok: true`.

## Gold Subset Rows

{chr(10).join(gold_sections)}

## Long-Silence Rows

{chr(10).join(silence_sections)}
""",
        encoding="utf-8",
    )


def write_nemo_manifest(path: Path, selected: list[dict[str, object]]) -> None:
    rows = []
    for row in selected:
        rows.append(
            {
                "audio_filepath": str(row["overlay_abs"]),
                "text": row["text"],
                "duration": row["duration_sec"],
                "language": "zh",
                "speaker_id": "unknown",
                "audio_id": row["audio_id"],
                "split": row["split"],
                "source_audio_relative": row["source_audio_relative"],
                "risk_keyword_hits": row.get("risk_terms", []),
            }
        )
    write_jsonl(path, rows)


def write_task_definition(path: Path, sample_size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""# JANUS ASR-to-CDS Evaluation Task

Generated: {datetime.now().isoformat(timespec="seconds")}

This task definition is for the first small JANUS curation pass. It assumes the
audio files are already usable and intentionally omits publication/sensitivity
classification from the working table. The repo-level handling rules still keep
bulk audio, transcripts, and predictions local.

## Unit Of Analysis

Use one `janus_165_v1` AudioFolder row as one ASR segment. The current canonical
dataset has 4,967 rows across train, validation, and test.

## Gold Subset

Start with `{sample_size}` selected rows in `gold_subset_review.tsv`. The
existing transcript is only a candidate reference. A row becomes gold only after
human review fills:

- `human_verified_transcript`
- `semantic_risk_label`
- `risk_atoms`
- `asr_confusion_terms`
- `would_asr_error_change_decision`

## Metrics Beyond WER/CER

Evaluate ASR systems with these task-facing checks:

- Keyword miss rate: decision-critical terms absent from the ASR transcript.
- Risk phrase mistranscription rate: phrase-level changes around scam method,
  amount, account, actor, action, time, or negation.
- Escalation label flip rate: high-risk/low-risk decision changes after ASR.
- Interpretation-impact rate: ASR errors that would change fraud-risk or
  high-stakes operational interpretation even when WER/CER is low.
- CEIS readiness: whether the hypothesis exposes spans usable by
  counterfactual decision-stability scoring.

## Minimum Acceptance Gate

Do not run a full NeMo/Whisper comparison over all 4,967 rows until the selected
gold subset is reviewed and the NeMo pilot output can be joined back to
`audio_id`.
""",
        encoding="utf-8",
    )


def write_asr_comparison_plan(path: Path) -> None:
    fields = [
        "system",
        "role",
        "input_manifest",
        "output_path",
        "primary_checks",
        "notes",
    ]
    rows = [
        {
            "system": "NVIDIA NeMo Curator / NeMo ASR",
            "role": "pilot ASR curation baseline",
            "input_manifest": "40_breeze_asr25_finetune_dataset/manifests/nemo_pilot_input_manifest.jsonl",
            "output_path": "40_breeze_asr25_finetune_dataset/manifests/asr_outputs_nemo.jsonl",
            "primary_checks": "manifest ingest; transcript quality; WER/CER against reviewed gold; join by audio_id",
            "notes": "Run after nemo-curator[audio_cuda12] environment is available.",
        },
        {
            "system": "openai/whisper-small",
            "role": "low-cost smoke baseline",
            "input_manifest": "gold_subset_review.tsv",
            "output_path": "70_experiments/runs/whisper_small_smoke_test/",
            "primary_checks": "zh-TW Traditional Chinese; fraud terms; timestamps if available; semantic-risk impact",
            "notes": "Existing run folder is present; refresh only after gold subset review.",
        },
        {
            "system": "openai/whisper-large-v2 LoRA",
            "role": "strong Whisper-family baseline",
            "input_manifest": "gold_subset_review.tsv",
            "output_path": "70_experiments/runs/whisper_large_v2_lora_baseline/",
            "primary_checks": "CER/WER; risk atom error rate; decision flip rate",
            "notes": "Use existing config as the first serious local baseline.",
        },
        {
            "system": "MediaTek-Research/Breeze-ASR-25",
            "role": "Taiwan Mandarin and Traditional Chinese domain baseline",
            "input_manifest": "gold_subset_review.tsv",
            "output_path": "70_experiments/runs/breeze_asr25_baseline/",
            "primary_checks": "Taiwan Mandarin call-center fit; Traditional Chinese output; fraud-domain vocabulary; compute cost",
            "notes": "Add run folder before long evaluation.",
        },
        {
            "system": "MediaTek-Research/Breeze-ASR-26",
            "role": "optional Taigi/Taiwanese Hokkien stress test",
            "input_manifest": "gold_subset_review.tsv",
            "output_path": "70_experiments/runs/breeze_asr26_stress_test/",
            "primary_checks": "Taigi/Hokkien speech sensitivity; Chinese-character output; do not rank as primary Mandarin baseline",
            "notes": "Use only as a dialect robustness probe unless the selected audio contains Taigi/Hokkien speech.",
        },
        {
            "system": "faster-whisper / WhisperX",
            "role": "engineering comparison candidate",
            "input_manifest": "gold_subset_review.tsv",
            "output_path": "70_experiments/runs/faster_whisper_or_whisperx_baseline/",
            "primary_checks": "runtime; timestamp quality; alignment usefulness for CEIS spans",
            "notes": "Optional; use if timestamp alignment becomes the bottleneck.",
        },
    ]
    write_tsv(path, rows, fields)


def write_nemo_runbook(path: Path, sample_size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""# NeMo Curator Pilot Runbook

Generated: {datetime.now().isoformat(timespec="seconds")}

## Current Local Status

The pilot input manifest has `{sample_size}` rows:

```text
40_breeze_asr25_finetune_dataset/manifests/nemo_pilot_input_manifest.jsonl
```

The local machine has an NVIDIA GPU, but this checkout did not have
`nemo_curator`, `torch`, or `soundfile` importable when the curation artifacts
were generated.

## Why Pilot First

NeMo Curator is useful here after the canonical manifest and gold subset exist:
the audio curation docs describe local/custom manifest ingest, ASR inference,
WER/CER quality assessment, duration/format validation, metadata extraction,
and export for downstream training or analysis.

## Pilot Gate

Run only the gold subset first. The pilot is successful only if:

1. The custom manifest loads without path rewrites.
2. Output rows preserve `audio_id`.
3. ASR hypotheses can be joined to `gold_subset_review.tsv`.
4. WER/CER can be computed after `human_verified_transcript` is filled.
5. Risk-term misses and decision-impact columns can be computed for CDS-ASR.

## Expected Output Contract

Write NeMo output here:

```text
40_breeze_asr25_finetune_dataset/manifests/asr_outputs_nemo.jsonl
```

Each row should include at least:

```json
{{"audio_id": "...", "audio_filepath": "...", "pred_text": "...", "duration": 0.0, "model": "..."}}
```

## After The Pilot

Compare NeMo ASR against the Whisper/Breeze candidates listed in
`asr_comparison_plan.tsv`. Do not expand to all 4,967 rows until the pilot can
produce joined metrics on the reviewed gold subset.
""",
        encoding="utf-8",
    )


def write_raw_audio_preservation_report(
    path: Path,
    repo_root: Path,
    rows: list[dict[str, object]],
) -> None:
    archive_count = len(list((repo_root / "00_source_archives").glob("**/*"))) if (repo_root / "00_source_archives").exists() else 0
    source_paths = {str(row.get("source_audio_relative", "")) for row in rows if row.get("source_audio_relative")}
    source_dates = sorted({str(row.get("source_date", "")) for row in rows if row.get("source_date")})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""# Raw Audio Preservation Report

Generated: {datetime.now().isoformat(timespec="seconds")}

## Decision

No raw audio was copied, overwritten, normalized, or converted by this curation
pass. The canonical dataset remains a symlink/manifest overlay over the existing
JANUS extracted files.

## Source Locations

- Original archives: `00_source_archives/`
- Extracted source tree: `10_extracted_parts/`
- Raw-audio navigation overlay: `50_janus_data_library/02_raw_audio/`
- Whisper/ASR dataset overlay:
  `40_breeze_asr25_finetune_dataset/hf_audiofolder/`

## Source Record

- Dataset rows covered by canonical manifest: {len(rows)}
- Distinct source audio references in covered rows: {len(source_paths)}
- Source date range visible from filenames: {source_dates[0] if source_dates else "not detected"} to {source_dates[-1] if source_dates else "not detected"}
- Files/directories present under `00_source_archives/`: {archive_count}

Use `audio_inventory.csv` for row-level source paths, dates, hashes, and notes.
""",
        encoding="utf-8",
    )


def write_summary(
    path: Path,
    rows: list[dict[str, object]],
    flag_counter: Counter[str],
    sample_rate_counter: Counter[int],
    channel_counter: Counter[int],
    durations: list[float],
    generated_paths: list[Path],
    repo_root: Path,
) -> None:
    split_counts = Counter(str(row["split"]) for row in rows)
    total_hours = sum(durations) / 3600 if durations else 0.0
    p50 = statistics.median(durations) if durations else 0.0
    p95 = statistics.quantiles(durations, n=20)[18] if len(durations) >= 20 else max(durations, default=0.0)
    path.parent.mkdir(parents=True, exist_ok=True)
    generated_list = "\n".join(f"- `{relpath(item, repo_root)}`" for item in generated_paths)
    flag_lines = "\n".join(f"- {flag}: {count}" for flag, count in flag_counter.most_common()) or "- none"
    path.write_text(
        f"""# Audio Health Check Summary

Generated: {datetime.now().isoformat(timespec="seconds")}

## Scope

The check covers the canonical `janus_165_v1` AudioFolder rows rather than every
duplicated extracted wav in `10_extracted_parts/`.

## Dataset Size

- Total rows: {len(rows)}
- Split rows: {dict(split_counts)}
- Total duration hours: {total_hours:.3f}
- Duration min / median / p95 / max seconds: {min(durations, default=0.0):.3f} / {p50:.3f} / {p95:.3f} / {max(durations, default=0.0):.3f}

## Format Distribution

- Sample rates: {dict(sample_rate_counter)}
- Channels: {dict(channel_counter)}

## Health Flags

{flag_lines}

## Generated Artifacts

{generated_list}
""",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-size", type=int, default=15)
    parser.add_argument("--min-duration-sec", type=float, default=1.0)
    parser.add_argument("--max-manifest-delta-sec", type=float, default=0.10)
    parser.add_argument("--silence-threshold-rms", type=float, default=0.001)
    parser.add_argument("--long-silence-sec", type=float, default=2.0)
    args = parser.parse_args()

    repo_root = repo_root_from_script()
    dataset_root = repo_root / "40_breeze_asr25_finetune_dataset"
    manifests_dir = dataset_root / "manifests"
    reports_dir = dataset_root / "reports"

    rows = load_rows(repo_root, manifests_dir)
    stats_by_id: dict[str, AudioStats] = {}
    hashes_by_id: dict[str, str] = {}

    for row in rows:
        audio_id = str(row["audio_id"])
        overlay_abs = Path(str(row["overlay_abs"]))
        stats_by_id[audio_id] = inspect_wav(
            overlay_abs,
            silence_threshold=args.silence_threshold_rms,
            silence_window_sec=args.long_silence_sec,
        )
        hashes_by_id[audio_id] = sha256_file(overlay_abs) if overlay_abs.exists() else ""

    sample_rate_counter = Counter(
        stats.sample_rate for stats in stats_by_id.values() if stats.ok and stats.sample_rate is not None
    )
    channel_counter = Counter(
        stats.channels for stats in stats_by_id.values() if stats.ok and stats.channels is not None
    )
    modal_sample_rate = sample_rate_counter.most_common(1)[0][0] if sample_rate_counter else None
    modal_channels = channel_counter.most_common(1)[0][0] if channel_counter else None

    inventory_rows: list[dict[str, object]] = []
    health_rows: list[dict[str, object]] = []
    flag_counter: Counter[str] = Counter()
    durations: list[float] = []

    for row in rows:
        audio_id = str(row["audio_id"])
        stats = stats_by_id[audio_id]
        flags = flag_row(
            row,
            stats,
            modal_sample_rate=modal_sample_rate,
            modal_channels=modal_channels,
            min_duration_sec=args.min_duration_sec,
            max_manifest_delta_sec=args.max_manifest_delta_sec,
            long_silence_sec=args.long_silence_sec,
        )
        flag_counter.update(flags)
        duration_sec = stats.duration_sec if stats.duration_sec is not None else ""
        if isinstance(duration_sec, float):
            durations.append(duration_sec)
        duration_delta = (
            round(float(duration_sec) - float(row["manifest_duration_sec"]), 6)
            if isinstance(duration_sec, float)
            else ""
        )
        row["duration_sec"] = round(duration_sec, 6) if isinstance(duration_sec, float) else ""
        row["sample_rate"] = stats.sample_rate or ""
        row["channels"] = stats.channels or ""
        row["format"] = stats.format_name
        row["health_flags"] = "|".join(flags) if flags else "ok"

        inventory_rows.append(
            {
                "audio_id": audio_id,
                "path": row["overlay_rel"],
                "duration_sec": row["duration_sec"],
                "sample_rate": stats.sample_rate or "",
                "channels": stats.channels or "",
                "format": stats.format_name,
                "speaker/context": f"165 anti-fraud call-center segment; split={row['split']}",
                "source": row["source_audio_relative"] or row["source_manifest"],
                "hash": hashes_by_id[audio_id],
                "notes": row["health_flags"],
                "split": row["split"],
                "manifest_duration_sec": row["manifest_duration_sec"],
                "duration_delta_sec": duration_delta,
                "source_date": row["source_date"],
                "original_file_name": row["original_file_name"],
                "source_manifest": row["source_manifest"],
                "source_manifest_line": row["source_manifest_line"],
                "candidate_match_count": row["candidate_match_count"],
                "alignment_score": row["alignment_score"],
            }
        )
        health_rows.append(
            {
                "audio_id": audio_id,
                "split": row["split"],
                "path": row["overlay_rel"],
                "exists": Path(str(row["overlay_abs"])).exists(),
                "duration_sec": row["duration_sec"],
                "manifest_duration_sec": row["manifest_duration_sec"],
                "duration_delta_sec": duration_delta,
                "sample_rate": stats.sample_rate or "",
                "channels": stats.channels or "",
                "sample_width_bytes": stats.sample_width_bytes or "",
                "frame_count": stats.frame_count or "",
                "peak_ratio": round(stats.peak_ratio, 6) if stats.peak_ratio is not None else "",
                "rms_ratio": round(stats.rms_ratio, 6) if stats.rms_ratio is not None else "",
                "max_silence_sec": round(stats.max_silence_sec, 3) if stats.max_silence_sec is not None else "",
                "flags": row["health_flags"],
                "error": stats.error,
            }
        )

    inventory_path = manifests_dir / "audio_inventory.csv"
    health_path = reports_dir / "audio_health_check.csv"
    health_summary_path = reports_dir / "audio_health_check_summary.md"
    gold_path = reports_dir / "gold_subset_review.tsv"
    gold_summary_path = reports_dir / "gold_subset_completion_summary.md"
    long_silence_path = reports_dir / "long_silence_review.tsv"
    review_packet_path = reports_dir / "gold_review_packet.md"
    task_path = reports_dir / "asr_evaluation_task.md"
    nemo_manifest_path = manifests_dir / "nemo_pilot_input_manifest.jsonl"
    nemo_runbook_path = reports_dir / "nemo_curator_pilot_runbook.md"
    comparison_path = reports_dir / "asr_comparison_plan.tsv"
    raw_report_path = reports_dir / "raw_audio_preservation.md"

    write_csv(
        inventory_path,
        inventory_rows,
        [
            "audio_id",
            "path",
            "duration_sec",
            "sample_rate",
            "channels",
            "format",
            "speaker/context",
            "source",
            "hash",
            "notes",
            "split",
            "manifest_duration_sec",
            "duration_delta_sec",
            "source_date",
            "original_file_name",
            "source_manifest",
            "source_manifest_line",
            "candidate_match_count",
            "alignment_score",
        ],
    )
    write_csv(
        health_path,
        health_rows,
        [
            "audio_id",
            "split",
            "path",
            "exists",
            "duration_sec",
            "manifest_duration_sec",
            "duration_delta_sec",
            "sample_rate",
            "channels",
            "sample_width_bytes",
            "frame_count",
            "peak_ratio",
            "rms_ratio",
            "max_silence_sec",
            "flags",
            "error",
        ],
    )

    selected = select_gold_subset(rows, args.sample_size)
    gold_rows = write_gold_subset(gold_path, selected)
    write_gold_completion_summary(gold_summary_path, gold_rows)
    long_silence_rows = write_long_silence_review(long_silence_path, rows, stats_by_id)
    write_gold_review_packet(review_packet_path, gold_rows, long_silence_rows)
    write_nemo_manifest(nemo_manifest_path, selected)
    write_task_definition(task_path, args.sample_size)
    write_asr_comparison_plan(comparison_path)
    write_nemo_runbook(nemo_runbook_path, args.sample_size)
    write_raw_audio_preservation_report(raw_report_path, repo_root, rows)
    write_summary(
        health_summary_path,
        rows=rows,
        flag_counter=flag_counter,
        sample_rate_counter=sample_rate_counter,
        channel_counter=channel_counter,
        durations=durations,
        generated_paths=[
            inventory_path,
            health_path,
            health_summary_path,
            gold_path,
            gold_summary_path,
            long_silence_path,
            review_packet_path,
            task_path,
            nemo_manifest_path,
            nemo_runbook_path,
            comparison_path,
            raw_report_path,
        ],
        repo_root=repo_root,
    )

    summary = {
        "rows": len(rows),
        "sample_size": len(selected),
        "modal_sample_rate": modal_sample_rate,
        "modal_channels": modal_channels,
        "flag_counts": dict(flag_counter),
        "gold_completed_rows": len(completed_gold_rows(gold_rows)),
        "long_silence_review_rows": len(long_silence_rows),
        "generated": [
            relpath(path, repo_root)
            for path in [
                inventory_path,
                health_path,
                health_summary_path,
                gold_path,
                gold_summary_path,
                long_silence_path,
                review_packet_path,
                task_path,
                nemo_manifest_path,
                nemo_runbook_path,
                comparison_path,
                raw_report_path,
            ]
        ],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

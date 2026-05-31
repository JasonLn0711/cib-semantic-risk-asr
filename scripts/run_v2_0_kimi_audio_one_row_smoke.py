#!/usr/bin/env python3
"""Run Kimi-Audio one-row transcript-only smoke with aggregate output."""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import re
import time
from pathlib import Path
from typing import Any


RUN_ID = "v2_0_multimodal_batch1_kimi_audio_one_row_smoke_2026_06_01"
MODEL_ID = "moonshotai/Kimi-Audio-7B-Instruct"
MODEL_REVISION_SHA = "9a82a84c37ad9eb1307fb6ed8d7b397862ef9e6b"
DEFAULT_OUT_DIR = Path("70_experiments/runs") / RUN_ID
DEFAULT_LOCAL_OUTPUT_DIR = Path("70_experiments/runtime_lanes/kimi_audio/local_outputs") / RUN_ID
DEFAULT_SNAPSHOT_DIR = (
    Path("70_experiments/runtime_lanes/kimi_audio/hf_cache/hub")
    / "models--moonshotai--Kimi-Audio-7B-Instruct"
    / "snapshots"
    / MODEL_REVISION_SHA
)
PROMPT = (
    "請逐字轉錄以下台灣電話客服語音，輸出繁體中文（台灣用語）。"
    "只輸出轉錄內容，不要摘要、不要翻譯、不要時間戳、不要說話者標籤。"
)
AUDIO_FIELDS = ("audio_path", "audio_filepath", "wav_path", "file_path", "path", "audio", "source_audio_path", "local_audio_path")


def read_manifest(path: Path) -> tuple[Path, int, int]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = reader.fieldnames or []
        rows = list(reader)
    if len(rows) != 1:
        raise ValueError("manifest_row_count_not_one")
    audio_field = next((field for field in AUDIO_FIELDS if rows[0].get(field)), None)
    if audio_field is None:
        raise ValueError("audio_field_not_found")
    audio_path = Path(rows[0][audio_field]).expanduser()
    if not audio_path.exists():
        raise FileNotFoundError("audio_file_not_found")
    return audio_path, len(rows), len(fields)


def audio_metadata(path: Path) -> tuple[int, float]:
    import soundfile as sf

    info = sf.info(str(path))
    seconds = round(float(info.frames) / float(info.samplerate), 3) if info.samplerate else 0.0
    return int(info.samplerate), seconds


def classify_text(text: str) -> dict[str, Any]:
    stripped = text.strip()
    chars = [char for char in stripped if not char.isspace()]
    longest_run = 0
    current = 0
    previous = None
    for char in chars:
        current = current + 1 if char == previous else 1
        previous = char
        longest_run = max(longest_run, current)
    has_timestamp = bool(re.search(r"\b\d{1,2}:\d{2}\b|\[\d", stripped))
    has_speaker = bool(re.search(r"(^|\n)\s*(speaker|說話者|客服|客戶)\s*[:：]", stripped, re.I))
    summary = any(marker in stripped for marker in ["摘要", "總結", "以下是", "重點", "我聽到", "這段音訊"])
    translation = "translation" in stripped.lower() or "翻譯" in stripped
    tts = "tts" in stripped.lower() or "音訊已生成" in stripped
    repetition = int(longest_run >= 12 or (len(chars) >= 40 and len(set(chars)) <= 4))
    raw_like = int(bool(stripped) and not has_timestamp and not has_speaker and not summary and not translation and not tts and not repetition)
    return {
        "has_text_output": int(bool(stripped)),
        "output_chars": len(stripped),
        "longest_repeated_char_run": longest_run,
        "repetition_output": repetition,
        "summary_or_answer_outputs": int(summary),
        "translation_outputs": int(translation),
        "tts_only_outputs": int(tts),
        "invented_timestamp_outputs": int(has_timestamp),
        "invented_speaker_label_outputs": int(has_speaker),
        "raw_transcript_like_outputs": raw_like,
    }


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""# Kimi-Audio One-Row Transcript-Only Smoke

Date: 2026-06-01

Status: {summary['status']}

本紀錄只保存 Kimi-Audio one-row smoke aggregate status。模型輸出、音檔
路徑、row ID、逐字稿與 hypothesis 均保存在 ignored local runtime lane，不進入 git。

## Runtime Boundary

Kimi-Audio is kept in the primary zh-TW audio LLM lane because its public label
is `Kimi-Audio-7B-Instruct`; the HF widget `10B params` marker remains an
explicit size-boundary validation layer. The transcript-only attempt used the
official model snapshot while excluding TTS detokenizer/vocoder artifacts.

## Result

```text
model_id={summary['model_id']}
smoke_status={summary['smoke_status']}
runtime_dependency_boundary={summary['runtime_dependency_boundary']}
valid_text_outputs={summary['valid_text_outputs']}
raw_transcript_like_outputs={summary['raw_transcript_like_outputs']}
failure_mode={summary['failure_mode']}
promotion_decision={summary['promotion_decision']}
```
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def write_outputs(
    out_dir: Path,
    started_at: int,
    behavior: dict[str, Any],
    manifest_rows: int,
    manifest_fields: int,
    audio_seconds: float,
    sample_rate: int,
) -> None:
    env = {
        "model_family": "Kimi-Audio",
        "model_id": MODEL_ID,
        "execution_order": 5,
        "runtime_lane": "ignored_kimi_audio_runtime_lane",
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "transcript_only_snapshot_policy": "main_model_and_whisper_without_tts_detokenizer_or_vocoder",
        "local_runtime_patch_policy": "ignored_lane_lazy_detokenizer_import_and_whisper_sdpa_fallback",
        "flash_attn_import_status": behavior["flash_attn_import_status"],
        "model_inference_run": behavior["smoke_status"] == "completed",
        "local_output_tracked": False,
        "transcript_bearing_logs_tracked": False,
    }
    summary = {
        "run_id": RUN_ID,
        "generated_at_unix": int(time.time()),
        "started_at_unix": started_at,
        "gate": "Gate C Kimi-Audio one-row transcript-only smoke",
        "status": "kimi_audio_one_row_smoke_complete" if behavior["smoke_status"] == "completed" else "kimi_audio_one_row_smoke_classified_runtime_boundary",
        "model_id": MODEL_ID,
        "public_model_label": "Kimi-Audio-7B-Instruct",
        "hf_widget_parameter_marker": "10B params",
        "model_revision_sha": MODEL_REVISION_SHA,
        "smoke_status": behavior["smoke_status"],
        "runtime_dependency_boundary": behavior["runtime_dependency_boundary"],
        "manifest_rows": manifest_rows,
        "manifest_field_count": manifest_fields,
        "manifest_field_names_tracked": False,
        "audio_exists": bool(manifest_rows),
        "audio_seconds_rounded": audio_seconds,
        "audio_samplerate": sample_rate,
        "valid_text_outputs": behavior["valid_text_outputs"],
        "raw_transcript_like_outputs": behavior["raw_transcript_like_outputs"],
        "repetition_outputs": behavior["repetition_output"],
        "summary_or_answer_outputs": behavior["summary_or_answer_outputs"],
        "translation_outputs": behavior["translation_outputs"],
        "tts_only_outputs": behavior["tts_only_outputs"],
        "invented_timestamp_outputs": behavior["invented_timestamp_outputs"],
        "invented_speaker_label_outputs": behavior["invented_speaker_label_outputs"],
        "output_chars": behavior.get("output_chars", 0),
        "failure_mode": behavior["failure_mode"],
        "promotion_decision": behavior["promotion_decision"],
        "privacy": {
            "raw_audio_tracked": False,
            "row_ids_tracked": False,
            "transcripts_tracked": False,
            "hypotheses_tracked": False,
            "reviewer_notes_tracked": False,
            "local_paths_tracked": False,
            "transcript_bearing_runtime_logs_tracked": False,
            "model_cache_paths_tracked": False,
        },
        "next_gate": "kimi_audio_sentinel_controls" if behavior["promotion_decision"] == "promote_to_sentinel" else "kimi_audio_runtime_dependency_repair_lane",
    }
    write_tsv(out_dir / "runtime_environment_summary.tsv", [env], list(env))
    write_tsv(out_dir / "behavior_summary.tsv", [behavior], list(behavior))
    (out_dir / "gate_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_readme(out_dir, summary)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("one_row_smoke_manifest.local.tsv"))
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--local-output-dir", type=Path, default=DEFAULT_LOCAL_OUTPUT_DIR)
    parser.add_argument("--snapshot-dir", type=Path, default=DEFAULT_SNAPSHOT_DIR)
    parser.add_argument("--max-new-tokens", type=int, default=64)
    args = parser.parse_args()
    started_at = int(time.time())
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.local_output_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

    manifest_rows = 0
    manifest_fields = 0
    seconds = 0.0
    sample_rate = 0
    try:
        audio_path, manifest_rows, manifest_fields = read_manifest(args.manifest)
        sample_rate, seconds = audio_metadata(audio_path)
        from kimia_infer.api.kimia import KimiAudio

        model = KimiAudio(model_path=str(args.snapshot_dir), load_detokenizer=False)
        messages = [
            {"role": "user", "message_type": "text", "content": PROMPT},
            {"role": "user", "message_type": "audio", "content": str(audio_path)},
        ]
        sampling_params = {
            "audio_temperature": 0.0,
            "audio_top_k": 5,
            "text_temperature": 0.0,
            "text_top_k": 5,
            "audio_repetition_penalty": 1.0,
            "audio_repetition_window_size": 64,
            "text_repetition_penalty": 1.0,
            "text_repetition_window_size": 16,
            "max_new_tokens": args.max_new_tokens,
        }
        _wav, text = model.generate(messages, **sampling_params, output_type="text")
        output_text = str(text)
        (args.local_output_dir / "kimi_audio_one_row_output.local.txt").write_text(output_text, encoding="utf-8")
        cls = classify_text(output_text)
        failure_mode = "none" if cls["raw_transcript_like_outputs"] else "non_transcript_output"
        behavior = {
            "model_family": "Kimi-Audio",
            "model_id": MODEL_ID,
            "execution_order": 5,
            "planned_gate": "one_row_transcript_only_smoke",
            "prompt_policy": "text_only_no_tts_no_tool_no_conversation",
            "flash_attn_import_status": "not_required_after_successful_runtime",
            "runtime_dependency_boundary": "none",
            "smoke_status": "completed",
            "output_rows": 1,
            "valid_text_outputs": cls["has_text_output"],
            "raw_transcript_like_outputs": cls["raw_transcript_like_outputs"],
            "repetition_output": cls["repetition_output"],
            "summary_or_answer_outputs": cls["summary_or_answer_outputs"],
            "translation_outputs": cls["translation_outputs"],
            "tts_only_outputs": cls["tts_only_outputs"],
            "invented_timestamp_outputs": cls["invented_timestamp_outputs"],
            "invented_speaker_label_outputs": cls["invented_speaker_label_outputs"],
            "failure_mode": failure_mode,
            "promotion_decision": "promote_to_sentinel" if cls["raw_transcript_like_outputs"] else "do_not_promote",
            "output_chars": cls["output_chars"],
            "longest_repeated_char_run": cls["longest_repeated_char_run"],
        }
        write_outputs(args.out_dir, started_at, behavior, manifest_rows, manifest_fields, seconds, sample_rate)
        print(f"wrote {args.out_dir}")
        return 0
    except Exception as exc:
        message = str(exc)
        failure = f"runtime_error:{type(exc).__name__}"
        boundary = "unknown_runtime_dependency_or_memory_boundary"
        if type(exc).__name__ == "RuntimeError" and "flash attention must be installed" in message:
            failure = "runtime_dependency_error:flash_attn_required_by_official_main_model_remote_code"
            boundary = "flash_attn_required_but_isolated_env_source_build_failed_without_usr_local_cuda_nvcc"
        elif "CUDA out of memory" in message:
            failure = "resource_error:cuda_out_of_memory"
            boundary = "official_runtime_exceeds_local_single_gpu_memory"
        behavior = {
            "model_family": "Kimi-Audio",
            "model_id": MODEL_ID,
            "execution_order": 5,
            "planned_gate": "one_row_transcript_only_smoke",
            "prompt_policy": "text_only_no_tts_no_tool_no_conversation",
            "flash_attn_import_status": "missing",
            "runtime_dependency_boundary": boundary,
            "smoke_status": f"failed:{type(exc).__name__}",
            "output_rows": 0,
            "valid_text_outputs": 0,
            "raw_transcript_like_outputs": 0,
            "repetition_output": 0,
            "summary_or_answer_outputs": 0,
            "translation_outputs": 0,
            "tts_only_outputs": 0,
            "invented_timestamp_outputs": 0,
            "invented_speaker_label_outputs": 0,
            "failure_mode": failure,
            "promotion_decision": "blocked_runtime_dependency",
            "output_chars": 0,
            "longest_repeated_char_run": 0,
        }
        write_outputs(args.out_dir, started_at, behavior, manifest_rows, manifest_fields, seconds, sample_rate)
        print(f"kimi_audio_one_row_smoke_classified_boundary:{type(exc).__name__}: {exc}", flush=True)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())

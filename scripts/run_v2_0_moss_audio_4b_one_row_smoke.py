#!/usr/bin/env python3
"""Run MOSS-Audio-4B one-row transcript-only smoke with aggregate output."""

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


RUN_ID = "v2_0_multimodal_batch1_moss_audio_4b_one_row_smoke_2026_06_01"
MODEL_ID = "OpenMOSS-Team/MOSS-Audio-4B-Instruct"
MODEL_REVISION_SHA = "6907a499dc0e87cc77c8ae0fe23fd0eb5476a02d"
DEFAULT_OUT_DIR = Path("70_experiments/runs") / RUN_ID
DEFAULT_LOCAL_OUTPUT_DIR = Path("70_experiments/runtime_lanes/moss_audio/local_outputs") / RUN_ID
DEFAULT_SNAPSHOT_DIR = (
    Path("70_experiments/runtime_lanes/moss_audio/hf_cache/hub")
    / "models--OpenMOSS-Team--MOSS-Audio-4B-Instruct"
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


def load_waveform(path: Path, target_sr: int = 16000) -> tuple[Any, int, float]:
    import numpy as np
    import soundfile as sf
    from scipy.signal import resample_poly

    audio, sample_rate = sf.read(str(path), dtype="float32")
    if getattr(audio, "ndim", 1) > 1:
        audio = audio.mean(axis=1)
    if sample_rate != target_sr:
        gcd = np.gcd(sample_rate, target_sr)
        audio = resample_poly(audio, target_sr // gcd, sample_rate // gcd).astype("float32")
        sample_rate = target_sr
    seconds = round(float(len(audio)) / float(sample_rate), 3) if sample_rate else 0.0
    return audio, sample_rate, seconds


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
    text = f"""# MOSS-Audio-4B One-Row Transcript-Only Smoke

Date: 2026-06-01

Status: {summary['status']}

本紀錄只保存 MOSS-Audio-4B one-row smoke aggregate status。模型輸出、音檔
路徑、row ID、逐字稿與 hypothesis 均保存在 ignored local runtime lane，不進入 git。

## Result

```text
model_id={summary['model_id']}
smoke_status={summary['smoke_status']}
valid_text_outputs={summary['valid_text_outputs']}
raw_transcript_like_outputs={summary['raw_transcript_like_outputs']}
summary_or_answer_outputs={summary['summary_or_answer_outputs']}
failure_mode={summary['failure_mode']}
promotion_decision={summary['promotion_decision']}
```
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def write_outputs(out_dir: Path, started_at: int, behavior: dict[str, Any], manifest_rows: int, manifest_fields: int, audio_seconds: float, sample_rate: int) -> None:
    env = {
        "model_family": "MOSS-Audio",
        "model_id": MODEL_ID,
        "execution_order": 3,
        "runtime_lane": "ignored_moss_audio_runtime_lane",
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "model_inference_run": behavior["smoke_status"] == "completed",
        "local_output_tracked": False,
        "transcript_bearing_logs_tracked": False,
    }
    summary = {
        "run_id": RUN_ID,
        "generated_at_unix": int(time.time()),
        "started_at_unix": started_at,
        "gate": "Gate C MOSS-Audio-4B one-row transcript-only smoke",
        "status": "moss_audio_4b_one_row_smoke_complete" if behavior["smoke_status"] == "completed" else "moss_audio_4b_one_row_smoke_failed",
        "model_id": MODEL_ID,
        "model_revision_sha": MODEL_REVISION_SHA,
        "smoke_status": behavior["smoke_status"],
        "manifest_rows": manifest_rows,
        "manifest_field_count": manifest_fields,
        "manifest_field_names_tracked": False,
        "audio_exists": True,
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
        "next_gate": "moss_audio_4b_sentinel_controls" if behavior["promotion_decision"] == "promote_to_sentinel" else "moss_audio_4b_prompt_or_runtime_repair_lane",
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
    parser.add_argument("--max-new-tokens", type=int, default=96)
    args = parser.parse_args()
    started_at = int(time.time())
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.local_output_dir.mkdir(parents=True, exist_ok=True)

    try:
        audio_path, manifest_rows, manifest_fields = read_manifest(args.manifest)
        audio, sample_rate, seconds = load_waveform(audio_path)
        import torch
        from src.modeling_moss_audio import MossAudioModel
        from src.processing_moss_audio import MossAudioProcessor

        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        device_map = "cuda:0" if torch.cuda.is_available() else "cpu"
        model = MossAudioModel.from_pretrained(
            args.snapshot_dir,
            trust_remote_code=True,
            dtype="auto",
            device_map=device_map,
            local_files_only=True,
        )
        model.eval()
        processor = MossAudioProcessor.from_pretrained(
            args.snapshot_dir,
            trust_remote_code=True,
            enable_time_marker=True,
            local_files_only=True,
        )
        inputs = processor(text=PROMPT, audios=[audio], return_tensors="pt")
        inputs = inputs.to(model.device)
        if inputs.get("audio_data") is not None:
            inputs["audio_data"] = inputs["audio_data"].to(model.dtype)
        inputs["audio_input_mask"] = inputs["input_ids"] == processor.audio_token_id
        with torch.inference_mode():
            generated_ids = model.generate(
                **inputs,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,
                num_beams=1,
                use_cache=True,
            )
        input_len = inputs["input_ids"].shape[1]
        output_text = processor.decode(generated_ids[0, input_len:], skip_special_tokens=True)
        (args.local_output_dir / "moss_audio_4b_one_row_output.local.txt").write_text(output_text, encoding="utf-8")
        cls = classify_text(output_text)
        failure_mode = "none" if cls["raw_transcript_like_outputs"] else "non_transcript_output"
        if cls["repetition_output"]:
            failure_mode = "repetition_or_non_transcript_output"
        elif cls["summary_or_answer_outputs"]:
            failure_mode = "summary_or_answer_output"
        behavior = {
            "model_family": "MOSS-Audio",
            "model_id": MODEL_ID,
            "execution_order": 3,
            "planned_gate": "one_row_transcript_only_smoke",
            "prompt_policy": "text_only_no_tts_no_tool_no_conversation",
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
        behavior = {
            "model_family": "MOSS-Audio",
            "model_id": MODEL_ID,
            "execution_order": 3,
            "planned_gate": "one_row_transcript_only_smoke",
            "prompt_policy": "text_only_no_tts_no_tool_no_conversation",
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
            "failure_mode": f"runtime_error:{type(exc).__name__}",
            "promotion_decision": "do_not_promote",
            "output_chars": 0,
            "longest_repeated_char_run": 0,
        }
        write_outputs(args.out_dir, started_at, behavior, 0, 0, 0.0, 0)
        print(f"moss_audio_4b_one_row_smoke_failed:{type(exc).__name__}: {exc}", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

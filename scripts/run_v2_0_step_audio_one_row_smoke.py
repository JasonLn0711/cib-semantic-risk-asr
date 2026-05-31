#!/usr/bin/env python3
"""Run Step-Audio-2-mini one-row transcript-only smoke with aggregate output."""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import re
import sys
import time
from pathlib import Path
from typing import Any


RUN_ID = "v2_0_multimodal_batch1_step_audio_one_row_smoke_2026_06_01"
MODEL_ID = "stepfun-ai/Step-Audio-2-mini"
SNAPSHOT_SHA = "e36fdd5d71e0ea22f09dd94bbab9bfc544ca1e36"
DEFAULT_OUT_DIR = Path("70_experiments/runs") / RUN_ID
DEFAULT_LOCAL_OUTPUT_DIR = Path("70_experiments/runtime_lanes/step_audio_2_mini/local_outputs") / RUN_ID
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


def load_waveform(path: Path) -> tuple[Any, int, float]:
    import librosa
    import soundfile as sf

    audio, sample_rate = sf.read(str(path), dtype="float32")
    if getattr(audio, "ndim", 1) > 1:
        audio = audio[:, 0]
    if sample_rate != 16000:
        audio = librosa.resample(audio, orig_sr=sample_rate, target_sr=16000)
        sample_rate = 16000
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
    summary = any(marker in stripped for marker in ["摘要", "總結", "以下是", "重點", "我聽到"])
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
    text = f"""# Step-Audio-2-mini One-Row Transcript-Only Smoke

Date: 2026-06-01

Status: {summary['status']}

本紀錄只保存 Step-Audio-2-mini one-row smoke aggregate status。模型輸出、音檔
路徑、row ID、逐字稿與 hypothesis 均保存在 ignored local runtime lane，不進入 git。

## Result

```text
model_id={summary['model_id']}
smoke_status={summary['smoke_status']}
valid_text_outputs={summary['valid_text_outputs']}
raw_transcript_like_outputs={summary['raw_transcript_like_outputs']}
repetition_outputs={summary['repetition_outputs']}
failure_mode={summary['failure_mode']}
promotion_decision={summary['promotion_decision']}
```
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def write_outputs(out_dir: Path, started_at: int, behavior: dict[str, Any], manifest_rows: int, manifest_fields: int, audio_seconds: float, sample_rate: int) -> None:
    env = {
        "model_family": "Step-Audio 2 mini",
        "model_id": MODEL_ID,
        "execution_order": 2,
        "runtime_lane": "ignored_step_audio_2_mini_runtime_lane",
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
        "gate": "Gate C Step-Audio-2-mini one-row transcript-only smoke",
        "status": "step_audio_one_row_smoke_complete" if behavior["smoke_status"] == "completed" else "step_audio_one_row_smoke_failed",
        "model_id": MODEL_ID,
        "model_revision_sha": SNAPSHOT_SHA,
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
        "next_gate": "step_audio_prompt_or_runtime_repair_lane" if behavior["promotion_decision"] == "do_not_promote" else "step_audio_sentinel_controls",
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
    parser.add_argument("--snapshot-dir", type=Path, default=Path("70_experiments/runtime_lanes/step_audio_2_mini/hf_cache/hub/models--stepfun-ai--Step-Audio-2-mini/snapshots") / SNAPSHOT_SHA)
    parser.add_argument("--max-new-tokens", type=int, default=64)
    args = parser.parse_args()
    started_at = int(time.time())
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.local_output_dir.mkdir(parents=True, exist_ok=True)

    try:
        audio_path, manifest_rows, manifest_fields = read_manifest(args.manifest)
        audio, sample_rate, seconds = load_waveform(audio_path)
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        tokenizer = AutoTokenizer.from_pretrained(args.snapshot_dir, trust_remote_code=True, local_files_only=True, fix_mistral_regex=True)
        model = AutoModelForCausalLM.from_pretrained(args.snapshot_dir, trust_remote_code=True, local_files_only=True, torch_dtype="auto", device_map="auto")
        remote_module = sys.modules[model.__class__.__module__]
        mel = remote_module.log_mel_spectrogram(audio)
        feature_len = mel.shape[-1]
        token_count = remote_module.compute_token_num(feature_len)
        audio_tokens = "<audio_start>" + ("<audio_patch>" * token_count) + "<audio_end>"
        messages = [
            {"role": "system", "content": "You are a speech recognition model. Return text only."},
            {"role": "user", "content": audio_tokens + "\n" + PROMPT},
        ]
        text = tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
        inputs = tokenizer(text, return_tensors="pt")
        wavs = mel.unsqueeze(0)
        wav_lens = torch.tensor([feature_len], dtype=torch.long)
        with torch.inference_mode():
            output_ids = model.generate(
                input_ids=inputs.input_ids.to(model.device),
                attention_mask=inputs.attention_mask.to(model.device),
                wavs=wavs,
                wav_lens=wav_lens,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,
            )
        new_tokens = output_ids[0][inputs.input_ids.shape[-1] :]
        output_text = tokenizer.decode(new_tokens, skip_special_tokens=True)
        classification = classify_text(output_text)
        promote = classification["raw_transcript_like_outputs"] == 1
        behavior = {
            "model_family": "Step-Audio 2 mini",
            "model_id": MODEL_ID,
            "execution_order": 2,
            "planned_gate": "one_row_transcript_only_smoke",
            "prompt_policy": "text_only_no_tts_no_tool_no_conversation",
            "smoke_status": "completed",
            "output_rows": 1,
            "valid_text_outputs": classification["has_text_output"],
            "raw_transcript_like_outputs": classification["raw_transcript_like_outputs"],
            "repetition_output": classification["repetition_output"],
            "summary_or_answer_outputs": classification["summary_or_answer_outputs"],
            "translation_outputs": classification["translation_outputs"],
            "tts_only_outputs": classification["tts_only_outputs"],
            "invented_timestamp_outputs": classification["invented_timestamp_outputs"],
            "invented_speaker_label_outputs": classification["invented_speaker_label_outputs"],
            "failure_mode": "none" if promote else "repetition_or_non_transcript_output",
            "promotion_decision": "promote_to_sentinel" if promote else "do_not_promote",
            "output_chars": classification["output_chars"],
            "longest_repeated_char_run": classification["longest_repeated_char_run"],
        }
        local_payload = {
            "model_id": MODEL_ID,
            "generated_at_unix": int(time.time()),
            "output_text": output_text,
            "privacy": "local_only_ignored_runtime_lane",
        }
        (args.local_output_dir / "step_audio_one_row_output.local.json").write_text(
            json.dumps(local_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        write_outputs(args.out_dir, started_at, behavior, manifest_rows, manifest_fields, seconds, sample_rate)
        print(f"wrote {args.out_dir}")
        return 0
    except Exception as exc:
        behavior = {
            "model_family": "Step-Audio 2 mini",
            "model_id": MODEL_ID,
            "execution_order": 2,
            "planned_gate": "one_row_transcript_only_smoke",
            "prompt_policy": "text_only_no_tts_no_tool_no_conversation",
            "smoke_status": "failed_before_valid_output",
            "output_rows": 0,
            "valid_text_outputs": 0,
            "raw_transcript_like_outputs": 0,
            "repetition_output": 0,
            "summary_or_answer_outputs": 0,
            "translation_outputs": 0,
            "tts_only_outputs": 0,
            "invented_timestamp_outputs": 0,
            "invented_speaker_label_outputs": 0,
            "failure_mode": f"inference_error:{type(exc).__name__}",
            "promotion_decision": "do_not_promote",
            "output_chars": 0,
            "longest_repeated_char_run": 0,
        }
        write_outputs(args.out_dir, started_at, behavior, 0, 0, 0.0, 0)
        print(f"wrote {args.out_dir}")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

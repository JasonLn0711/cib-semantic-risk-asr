#!/usr/bin/env python3
"""Run Qwen2.5-Omni one-row transcript-only smoke with aggregate tracked output.

The model output is written only to an ignored local runtime lane. The tracked
run directory records aggregate status and gate decisions only.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


RUN_ID = "v2_0_multimodal_batch1_qwen_one_row_smoke_2026_05_31"
DEFAULT_OUT_DIR = Path("70_experiments/runs") / RUN_ID
DEFAULT_LOCAL_OUTPUT_DIR = Path("70_experiments/runtime_lanes/qwen_omni/local_outputs") / RUN_ID
MODEL_ID = "Qwen/Qwen2.5-Omni-7B"
AUDIO_FIELD_CANDIDATES = (
    "audio_path",
    "audio_filepath",
    "wav_path",
    "file_path",
    "path",
    "audio",
    "source_audio_path",
    "local_audio_path",
)
PROMPT = (
    "請逐字轉錄以下台灣電話客服語音，輸出繁體中文（台灣用語）。"
    "只輸出轉錄內容，不要摘要、不要翻譯、不要時間戳、不要說話者標籤、不要說明。"
)


@dataclass(frozen=True)
class ManifestAudio:
    audio_path: Path
    row_count: int
    field_count: int


def read_one_manifest_audio(path: Path) -> ManifestAudio:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = reader.fieldnames or []
        rows = list(reader)
    if len(rows) != 1:
        raise ValueError("manifest_row_count_not_one")
    row = rows[0]
    audio_field = next((name for name in AUDIO_FIELD_CANDIDATES if row.get(name)), None)
    if audio_field is None:
        raise ValueError("audio_field_not_found")
    audio_path = Path(row[audio_field]).expanduser()
    if not audio_path.exists():
        raise FileNotFoundError("audio_file_not_found")
    return ManifestAudio(audio_path=audio_path, row_count=len(rows), field_count=len(fields))


def audio_summary(audio_path: Path) -> dict[str, Any]:
    import soundfile as sf

    info = sf.info(str(audio_path))
    seconds = round(float(info.frames) / float(info.samplerate), 3) if info.samplerate else 0.0
    return {
        "audio_exists": True,
        "audio_seconds_rounded": seconds,
        "audio_samplerate": int(info.samplerate),
        "audio_channels": int(info.channels),
    }


def classify_text(text: str) -> dict[str, Any]:
    stripped = text.strip()
    has_text = bool(stripped)
    has_timestamp = bool(re.search(r"\b\d{1,2}:\d{2}\b|\[\d", stripped))
    has_speaker_label = bool(re.search(r"(^|\n)\s*(speaker|說話者|客服|客戶)\s*[:：]", stripped, re.I))
    summary_markers = ("摘要", "總結", "以下是", "重點", "我聽到")
    translation_markers = ("translation", "翻譯")
    tts_markers = ("音訊已生成", "speech output", "tts")
    return {
        "has_text_output": has_text,
        "output_chars": len(stripped),
        "invented_timestamp_outputs": int(has_timestamp),
        "invented_speaker_label_outputs": int(has_speaker_label),
        "summary_or_answer_outputs": int(any(marker in stripped for marker in summary_markers)),
        "translation_outputs": int(any(marker.lower() in stripped.lower() for marker in translation_markers)),
        "tts_only_outputs": int(any(marker.lower() in stripped.lower() for marker in tts_markers)),
        "raw_transcript_like_outputs": int(has_text and not has_timestamp and not has_speaker_label),
    }


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""# Qwen2.5-Omni One-Row Transcript-Only Smoke

Date: 2026-05-31

Status: {summary['status']}

本紀錄只保存 Qwen one-row smoke aggregate status。模型輸出、音檔路徑、row ID、
逐字稿與 hypothesis 均保存在 ignored local runtime lane，不進入 git。

## Result

```text
model_id={summary['model_id']}
smoke_status={summary['smoke_status']}
valid_text_outputs={summary['valid_text_outputs']}
raw_transcript_like_outputs={summary['raw_transcript_like_outputs']}
failure_mode={summary['failure_mode']}
promotion_decision={summary['promotion_decision']}
```

## Next Gate

If promotion_decision is `promote_to_sentinel`, run Qwen sentinel controls.
Otherwise fix the recorded failure mode and rerun one-row transcript-only smoke.
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def tracked_failure(
    out_dir: Path,
    started_at: int,
    failure_mode: str,
    manifest: dict[str, Any],
    audio: dict[str, Any],
) -> None:
    behavior = {
        "model_family": "Qwen2.5-Omni",
        "model_id": MODEL_ID,
        "execution_order": 1,
        "planned_gate": "one_row_transcript_only_smoke",
        "prompt_policy": "text_only_no_tts_no_timestamp_no_speaker_label",
        "smoke_status": "failed_before_valid_output",
        "output_rows": 0,
        "valid_text_outputs": 0,
        "raw_transcript_like_outputs": 0,
        "summary_or_answer_outputs": 0,
        "translation_outputs": 0,
        "tts_only_outputs": 0,
        "invented_timestamp_outputs": 0,
        "invented_speaker_label_outputs": 0,
        "failure_mode": failure_mode,
        "promotion_decision": "do_not_promote",
    }
    write_outputs(out_dir, started_at, behavior, manifest, audio)


def write_outputs(
    out_dir: Path,
    started_at: int,
    behavior: dict[str, Any],
    manifest: dict[str, Any],
    audio: dict[str, Any],
) -> None:
    env = {
        "model_family": "Qwen2.5-Omni",
        "model_id": MODEL_ID,
        "execution_order": 1,
        "runtime_lane": "ignored_qwen_omni_runtime_lane",
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
        "gate": "Gate C Qwen one-row transcript-only smoke",
        "status": "qwen_one_row_smoke_complete" if behavior["smoke_status"] == "completed" else "qwen_one_row_smoke_failed",
        "model_id": MODEL_ID,
        "smoke_status": behavior["smoke_status"],
        "manifest_rows": manifest.get("manifest_rows", 0),
        "manifest_field_count": manifest.get("manifest_field_count", 0),
        "manifest_field_names_tracked": False,
        "audio_exists": audio.get("audio_exists", False),
        "audio_seconds_rounded": audio.get("audio_seconds_rounded", 0),
        "audio_samplerate": audio.get("audio_samplerate", 0),
        "valid_text_outputs": behavior["valid_text_outputs"],
        "raw_transcript_like_outputs": behavior["raw_transcript_like_outputs"],
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
        "next_gate": "qwen_sentinel_controls" if behavior["promotion_decision"] == "promote_to_sentinel" else "rerun_qwen_one_row_smoke_after_fix",
    }
    write_tsv(out_dir / "runtime_environment_summary.tsv", [env], list(env))
    write_tsv(out_dir / "behavior_summary.tsv", [behavior], list(behavior))
    (out_dir / "gate_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_readme(out_dir, summary)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("one_row_smoke_manifest.local.tsv"))
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--local-output-dir", type=Path, default=DEFAULT_LOCAL_OUTPUT_DIR)
    parser.add_argument("--cache-dir", type=Path, default=Path("70_experiments/runtime_lanes/qwen_omni/hf_cache/hub"))
    parser.add_argument("--max-new-tokens", type=int, default=192)
    args = parser.parse_args()

    started_at = int(time.time())
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.local_output_dir.mkdir(parents=True, exist_ok=True)

    manifest_record = {"manifest_rows": 0, "manifest_field_count": 0}
    audio_record: dict[str, Any] = {"audio_exists": False}
    try:
        manifest_audio = read_one_manifest_audio(args.manifest)
        manifest_record = {
            "manifest_rows": manifest_audio.row_count,
            "manifest_field_count": manifest_audio.field_count,
        }
        audio_record = audio_summary(manifest_audio.audio_path)
    except Exception as exc:
        tracked_failure(args.out_dir, started_at, f"manifest_or_audio_error:{type(exc).__name__}", manifest_record, audio_record)
        return 2

    try:
        import torch
        from qwen_omni_utils import process_mm_info
        from transformers import Qwen2_5OmniForConditionalGeneration, Qwen2_5OmniProcessor

        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        model = Qwen2_5OmniForConditionalGeneration.from_pretrained(
            MODEL_ID,
            cache_dir=str(args.cache_dir),
            local_files_only=True,
            torch_dtype="auto",
            device_map="auto",
        )
        model.disable_talker()
        processor = Qwen2_5OmniProcessor.from_pretrained(
            MODEL_ID,
            cache_dir=str(args.cache_dir),
            local_files_only=True,
        )
        conversation = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "You are Qwen, a speech recognition model. Return text only.",
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {"type": "audio", "audio": str(manifest_audio.audio_path)},
                    {"type": "text", "text": PROMPT},
                ],
            },
        ]
        use_audio_in_video = False
        text = processor.apply_chat_template(conversation, add_generation_prompt=True, tokenize=False)
        audios, images, videos = process_mm_info(conversation, use_audio_in_video=use_audio_in_video)
        inputs = processor(
            text=text,
            audio=audios,
            images=images,
            videos=videos,
            return_tensors="pt",
            padding=True,
            use_audio_in_video=use_audio_in_video,
        )
        inputs = inputs.to(model.device).to(model.dtype)
        with torch.inference_mode():
            text_ids = model.generate(
                **inputs,
                use_audio_in_video=use_audio_in_video,
                return_audio=False,
                max_new_tokens=args.max_new_tokens,
            )
        input_ids = inputs.get("input_ids")
        if input_ids is not None and len(text_ids) == len(input_ids):
            text_ids = [
                output_ids[len(input_ids[index]) :]
                for index, output_ids in enumerate(text_ids)
            ]
        output_text = processor.batch_decode(
            text_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )[0]
        classification = classify_text(output_text)
        promote = (
            classification["raw_transcript_like_outputs"] == 1
            and classification["summary_or_answer_outputs"] == 0
            and classification["translation_outputs"] == 0
            and classification["tts_only_outputs"] == 0
        )
        local_payload = {
            "model_id": MODEL_ID,
            "generated_at_unix": int(time.time()),
            "prompt": PROMPT,
            "output_text": output_text,
            "privacy": "local_only_ignored_runtime_lane",
        }
        (args.local_output_dir / "qwen_one_row_output.local.json").write_text(
            json.dumps(local_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        behavior = {
            "model_family": "Qwen2.5-Omni",
            "model_id": MODEL_ID,
            "execution_order": 1,
            "planned_gate": "one_row_transcript_only_smoke",
            "prompt_policy": "text_only_no_tts_no_timestamp_no_speaker_label",
            "smoke_status": "completed",
            "output_rows": 1,
            "valid_text_outputs": int(classification["has_text_output"]),
            "raw_transcript_like_outputs": classification["raw_transcript_like_outputs"],
            "summary_or_answer_outputs": classification["summary_or_answer_outputs"],
            "translation_outputs": classification["translation_outputs"],
            "tts_only_outputs": classification["tts_only_outputs"],
            "invented_timestamp_outputs": classification["invented_timestamp_outputs"],
            "invented_speaker_label_outputs": classification["invented_speaker_label_outputs"],
            "failure_mode": "none",
            "promotion_decision": "promote_to_sentinel" if promote else "do_not_promote",
            "output_chars": classification["output_chars"],
        }
        write_outputs(args.out_dir, started_at, behavior, manifest_record, audio_record)
        print(f"wrote {args.out_dir}")
        return 0
    except Exception as exc:
        tracked_failure(args.out_dir, started_at, f"inference_error:{type(exc).__name__}", manifest_record, audio_record)
        print(f"wrote {args.out_dir}")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run MOSS-Audio-8B one-row transcript-only smoke with aggregate output."""

from __future__ import annotations

import argparse
import json
import os
import platform
import time
from pathlib import Path
from typing import Any

from run_v2_0_moss_audio_4b_one_row_smoke import (
    PROMPT,
    classify_text,
    load_waveform,
    read_manifest,
    write_tsv,
)


RUN_ID = "v2_0_multimodal_batch1_moss_audio_8b_one_row_smoke_2026_06_01"
MODEL_ID = "OpenMOSS-Team/MOSS-Audio-8B-Instruct"
MODEL_REVISION_SHA = "cb7369a8094b5f1c818e384a8d76596c0e2138bd"
DEFAULT_OUT_DIR = Path("70_experiments/runs") / RUN_ID
DEFAULT_LOCAL_OUTPUT_DIR = Path("70_experiments/runtime_lanes/moss_audio/local_outputs") / RUN_ID
DEFAULT_SNAPSHOT_DIR = (
    Path("70_experiments/runtime_lanes/moss_audio/hf_cache/hub")
    / "models--OpenMOSS-Team--MOSS-Audio-8B-Instruct"
    / "snapshots"
    / MODEL_REVISION_SHA
)


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""# MOSS-Audio-8B One-Row Transcript-Only Smoke

Date: 2026-06-01

Status: {summary['status']}

本紀錄只保存 MOSS-Audio-8B one-row smoke aggregate status。模型輸出、音檔
路徑、row ID、逐字稿與 hypothesis 均保存在 ignored local runtime lane，不進入 git。

## Runtime Boundary

MOSS-Audio-8B is evaluated after MOSS-Audio-4B proved the transcript-only
prompt contract is interpretable. On this local 16GB GPU, a failed one-row
attempt is treated as a resource/runtime gate, not a transcript-quality result.

## Result

```text
model_id={summary['model_id']}
smoke_status={summary['smoke_status']}
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
        "model_family": "MOSS-Audio",
        "model_id": MODEL_ID,
        "execution_order": 6,
        "runtime_lane": "ignored_moss_audio_runtime_lane",
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "model_artifact_storage_gib": 16.87,
        "single_gpu_memory_boundary": "local_gpu_total_memory_16303_mib",
        "model_inference_run": behavior["smoke_status"] == "completed",
        "local_output_tracked": False,
        "transcript_bearing_logs_tracked": False,
    }
    summary = {
        "run_id": RUN_ID,
        "generated_at_unix": int(time.time()),
        "started_at_unix": started_at,
        "gate": "Gate C MOSS-Audio-8B one-row transcript-only smoke",
        "status": "moss_audio_8b_one_row_smoke_complete" if behavior["smoke_status"] == "completed" else "moss_audio_8b_one_row_smoke_classified_runtime_boundary",
        "model_id": MODEL_ID,
        "model_revision_sha": MODEL_REVISION_SHA,
        "model_artifact_storage_gib": 16.87,
        "smoke_status": behavior["smoke_status"],
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
        "next_gate": "moss_audio_8b_sentinel_controls" if behavior["promotion_decision"] == "promote_to_sentinel" else "moss_audio_8b_runtime_or_prompt_repair_lane",
    }
    write_tsv(out_dir / "runtime_environment_summary.tsv", [env], list(env))
    write_tsv(out_dir / "behavior_summary.tsv", [behavior], list(behavior))
    (out_dir / "gate_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_readme(out_dir, summary)


def failure_class(exc: Exception) -> tuple[str, str]:
    message = str(exc)
    if "CUDA out of memory" in message or "out of memory" in message.lower():
        return "failed:RuntimeError", "resource_error:cuda_out_of_memory"
    return f"failed:{type(exc).__name__}", f"runtime_error:{type(exc).__name__}"


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
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

    manifest_rows = 0
    manifest_fields = 0
    seconds = 0.0
    sample_rate = 0
    try:
        audio_path, manifest_rows, manifest_fields = read_manifest(args.manifest)
        audio, sample_rate, seconds = load_waveform(audio_path)
        import torch
        from src.modeling_moss_audio import MossAudioModel
        from src.processing_moss_audio import MossAudioProcessor

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
        (args.local_output_dir / "moss_audio_8b_one_row_output.local.txt").write_text(output_text, encoding="utf-8")
        cls = classify_text(output_text)
        failure_mode = "none" if cls["raw_transcript_like_outputs"] else "non_transcript_output"
        if cls["repetition_output"]:
            failure_mode = "repetition_or_non_transcript_output"
        elif cls["summary_or_answer_outputs"]:
            failure_mode = "summary_or_answer_output"
        behavior = {
            "model_family": "MOSS-Audio",
            "model_id": MODEL_ID,
            "execution_order": 6,
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
        smoke_status, failure_mode = failure_class(exc)
        promotion = "blocked_runtime_resource" if failure_mode.startswith("resource_error:") else "blocked_runtime_dependency"
        behavior = {
            "model_family": "MOSS-Audio",
            "model_id": MODEL_ID,
            "execution_order": 6,
            "planned_gate": "one_row_transcript_only_smoke",
            "prompt_policy": "text_only_no_tts_no_tool_no_conversation",
            "smoke_status": smoke_status,
            "output_rows": 0,
            "valid_text_outputs": 0,
            "raw_transcript_like_outputs": 0,
            "repetition_output": 0,
            "summary_or_answer_outputs": 0,
            "translation_outputs": 0,
            "tts_only_outputs": 0,
            "invented_timestamp_outputs": 0,
            "invented_speaker_label_outputs": 0,
            "failure_mode": failure_mode,
            "promotion_decision": promotion,
            "output_chars": 0,
            "longest_repeated_char_run": 0,
        }
        write_outputs(args.out_dir, started_at, behavior, manifest_rows, manifest_fields, seconds, sample_rate)
        print(f"moss_audio_8b_one_row_smoke_classified_boundary:{type(exc).__name__}: {exc}", flush=True)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())

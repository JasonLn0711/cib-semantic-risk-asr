#!/usr/bin/env python3
"""Run Step-Audio-2-mini one-row transcript-contract repair."""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

import torch
import run_v2_0_step_audio_one_row_smoke as base


RUN_ID = "v2_0_multimodal_batch1_step_audio_transcript_contract_repair_2026_06_01"
MODEL_ID = "stepfun-ai/Step-Audio-2-mini"
SNAPSHOT_SHA = "e36fdd5d71e0ea22f09dd94bbab9bfc544ca1e36"
DEFAULT_OUT_DIR = Path("70_experiments/runs") / RUN_ID
DEFAULT_LOCAL_OUTPUT_DIR = Path("70_experiments/runtime_lanes/step_audio_2_mini/local_outputs") / RUN_ID
REPAIR_PROMPT_ID = "step_audio_2_mini_strict_transcript_contract_v1"
REPAIR_PROMPT = (
    "任務：語音逐字轉錄。請只輸出你聽到的台灣華語原話，使用台灣繁體中文。"
    "若聽不清楚，請用「[聽不清楚]」。"
    "不要回答問題，不要聊天，不要摘要，不要翻譯，不要改寫，不要加入時間戳，"
    "不要加入說話者標籤，不要重複同一個字或符號。"
)


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""# Step-Audio-2-mini Transcript-Contract Repair

Date: 2026-06-01

Status: {summary['status']}

This tracked record reruns Step-Audio-2-mini on the one-row smoke manifest with
a stricter transcript-contract prompt. It is a bounded repair gate only; it does
not promote Step to sentinel unless the one-row raw transcript-like contract is
actually met. Transcript-bearing model output remains in the ignored runtime
lane.

## Result

```text
valid_text_outputs={summary['valid_text_outputs']}
raw_transcript_like_outputs={summary['raw_transcript_like_outputs']}
repetition_outputs={summary['repetition_outputs']}
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
        "model_family": "Step-Audio 2 mini",
        "model_id": MODEL_ID,
        "runtime_lane": "ignored_step_audio_2_mini_runtime_lane",
        "repair_prompt_id": REPAIR_PROMPT_ID,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "model_inference_run": behavior["smoke_status"] == "completed",
        "local_output_tracked": False,
        "transcript_bearing_logs_tracked": False,
    }
    summary = {
        "run_id": out_dir.name,
        "generated_at_unix": int(time.time()),
        "started_at_unix": started_at,
        "gate": "Phase 6 Step-Audio-2-mini transcript-contract repair",
        "status": "step_audio_transcript_contract_repair_complete"
        if behavior["smoke_status"] == "completed"
        else "step_audio_transcript_contract_repair_failed",
        "model_id": MODEL_ID,
        "model_revision_sha": SNAPSHOT_SHA,
        "source_run_id": "v2_0_multimodal_batch1_step_audio_one_row_smoke_2026_06_01",
        "repair_prompt_id": REPAIR_PROMPT_ID,
        "smoke_status": behavior["smoke_status"],
        "manifest_rows": manifest_rows,
        "manifest_field_count": manifest_fields,
        "manifest_field_names_tracked": False,
        "audio_exists": bool(sample_rate),
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
        "next_gate": "step_audio_sentinel_controls"
        if behavior["promotion_decision"] == "promote_to_sentinel"
        else "stop_or_repair_again_before_sentinel",
    }
    write_tsv(out_dir / "runtime_environment_summary.tsv", [env], list(env))
    write_tsv(out_dir / "behavior_summary.tsv", [behavior], list(behavior))
    (out_dir / "gate_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_readme(out_dir, summary)


def build_behavior(output_text: str) -> dict[str, Any]:
    classification = base.classify_text(output_text)
    promote = (
        classification["raw_transcript_like_outputs"] == 1
        and classification["repetition_output"] == 0
        and classification["summary_or_answer_outputs"] == 0
        and classification["translation_outputs"] == 0
        and classification["tts_only_outputs"] == 0
        and classification["invented_timestamp_outputs"] == 0
        and classification["invented_speaker_label_outputs"] == 0
    )
    return {
        "model_family": "Step-Audio 2 mini",
        "model_id": MODEL_ID,
        "planned_gate": "transcript_contract_repair_one_row",
        "repair_prompt_id": REPAIR_PROMPT_ID,
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


def failed_behavior(exc: Exception) -> dict[str, Any]:
    return {
        "model_family": "Step-Audio 2 mini",
        "model_id": MODEL_ID,
        "planned_gate": "transcript_contract_repair_one_row",
        "repair_prompt_id": REPAIR_PROMPT_ID,
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


def model_remote_module(model: Any) -> Any:
    remote_model = getattr(getattr(model, "base_model", None), "model", model)
    return sys.modules[remote_model.__class__.__module__]


def model_input_device(model: Any) -> torch.device:
    for candidate in (model, getattr(getattr(model, "base_model", None), "model", None)):
        device = getattr(candidate, "device", None)
        if device is not None:
            return torch.device(device)
    for parameter in model.parameters():
        if parameter.device.type != "meta":
            return parameter.device
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("one_row_smoke_manifest.local.tsv"))
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--local-output-dir", type=Path, default=DEFAULT_LOCAL_OUTPUT_DIR)
    parser.add_argument(
        "--snapshot-dir",
        type=Path,
        default=Path(
            "70_experiments/runtime_lanes/step_audio_2_mini/hf_cache/hub/"
            "models--stepfun-ai--Step-Audio-2-mini/snapshots"
        )
        / SNAPSHOT_SHA,
    )
    parser.add_argument("--adapter-dir", type=Path, default=None)
    parser.add_argument("--max-new-tokens", type=int, default=96)
    args = parser.parse_args()

    started_at = int(time.time())
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.local_output_dir.mkdir(parents=True, exist_ok=True)

    try:
        audio_file, manifest_rows, manifest_fields = base.read_manifest(args.manifest)
        audio, sample_rate, seconds = base.load_waveform(audio_file)
        from transformers import AutoModelForCausalLM, AutoTokenizer

        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        tokenizer = AutoTokenizer.from_pretrained(
            args.snapshot_dir,
            trust_remote_code=True,
            local_files_only=True,
            fix_mistral_regex=True,
        )
        model = AutoModelForCausalLM.from_pretrained(
            args.snapshot_dir,
            trust_remote_code=True,
            local_files_only=True,
            torch_dtype="auto",
            device_map="auto",
        )
        if args.adapter_dir is not None:
            from peft import PeftModel

            model = PeftModel.from_pretrained(model, args.adapter_dir, is_trainable=False)
            model.eval()
        remote_module = model_remote_module(model)
        input_device = model_input_device(model)
        mel = remote_module.log_mel_spectrogram(audio)
        feature_len = mel.shape[-1]
        token_count = remote_module.compute_token_num(feature_len)
        audio_tokens = "<audio_start>" + ("<audio_patch>" * token_count) + "<audio_end>"
        messages = [
            {"role": "system", "content": "You are an ASR engine. Output transcript text only."},
            {"role": "user", "content": audio_tokens + "\n" + REPAIR_PROMPT},
        ]
        text = tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
        inputs = tokenizer(text, return_tensors="pt")
        wavs = mel.unsqueeze(0)
        wav_lens = torch.tensor([feature_len], dtype=torch.long)
        with torch.inference_mode():
            output_ids = model.generate(
                input_ids=inputs.input_ids.to(input_device),
                attention_mask=inputs.attention_mask.to(input_device),
                wavs=wavs.to(input_device),
                wav_lens=wav_lens.to(input_device),
                max_new_tokens=args.max_new_tokens,
                do_sample=False,
                repetition_penalty=1.12,
                no_repeat_ngram_size=4,
            )
        new_tokens = output_ids[0][inputs.input_ids.shape[-1] :]
        output_text = tokenizer.decode(new_tokens, skip_special_tokens=True)
        behavior = build_behavior(output_text)
        local_payload = {
            "model_id": MODEL_ID,
            "generated_at_unix": int(time.time()),
            "output_text": output_text,
            "privacy": "local_only_ignored_runtime_lane",
        }
        (args.local_output_dir / "step_audio_transcript_contract_repair_output.local.json").write_text(
            json.dumps(local_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        write_outputs(args.out_dir, started_at, behavior, manifest_rows, manifest_fields, seconds, sample_rate)
        print(f"step_audio_transcript_contract_repair_written {args.out_dir}")
        return 0
    except Exception as exc:
        behavior = failed_behavior(exc)
        write_outputs(args.out_dir, started_at, behavior, 0, 0, 0.0, 0)
        print(f"step_audio_transcript_contract_repair_written {args.out_dir}")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

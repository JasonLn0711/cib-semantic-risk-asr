#!/usr/bin/env python3
"""Run MOSS-Audio-4B sentinel controls with aggregate tracked output."""

from __future__ import annotations

import argparse
import json
import os
import platform
import time
from pathlib import Path
from typing import Any

from run_v2_0_moss_audio_4b_one_row_smoke import load_waveform
from run_v2_0_qwen_omni_sentinel_controls import (
    PROMPT,
    behavior_fields,
    classify_output,
    privacy_record,
    read_manifest,
    write_tsv,
)


RUN_ID = "v2_0_multimodal_batch1_moss_audio_4b_sentinel_controls_2026_06_01"
MODEL_ID = "OpenMOSS-Team/MOSS-Audio-4B-Instruct"
MODEL_REVISION_SHA = "6907a499dc0e87cc77c8ae0fe23fd0eb5476a02d"
DEFAULT_OUT_DIR = Path("70_experiments/runs") / RUN_ID
DEFAULT_LOCAL_OUTPUT_DIR = Path("70_experiments/runtime_lanes/moss_audio/local_outputs") / RUN_ID
DEFAULT_MANIFEST = Path("sentinel_negative_control_manifest.local.tsv")
DEFAULT_SNAPSHOT_DIR = (
    Path("70_experiments/runtime_lanes/moss_audio/hf_cache/hub")
    / "models--OpenMOSS-Team--MOSS-Audio-4B-Instruct"
    / "snapshots"
    / MODEL_REVISION_SHA
)


def environment_row(model_inference_run: bool) -> dict[str, Any]:
    return {
        "model_family": "MOSS-Audio",
        "model_id": MODEL_ID,
        "gate": "sentinel_controls",
        "runtime_lane": "ignored_moss_audio_runtime_lane",
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "model_inference_run": str(model_inference_run).lower(),
        "local_output_tracked": "false",
        "transcript_bearing_logs_tracked": "false",
    }


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""# MOSS-Audio-4B Sentinel Controls

Date: 2026-06-01

Status: {summary['status']}

本紀錄只保存 MOSS-Audio-4B sentinel aggregate status。音檔路徑、row ID、
逐字稿、hypothesis 與模型輸出均保存在 ignored local runtime lane，不進入 git。

## Result

```text
sentinel_rows={summary['sentinel_rows']}
sentinel_pass_rows={summary['sentinel_pass_rows']}
hallucination_on_no_speech_rows={summary['hallucination_on_no_speech_rows']}
instruction_followed_rows={summary['instruction_followed_rows']}
promotion_decision={summary['promotion_decision']}
```
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def write_failure(out_dir: Path, started_at: int, failure_mode: str, manifest_rows: int = 0) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "run_id": RUN_ID,
        "generated_at_unix": int(time.time()),
        "started_at_unix": started_at,
        "gate": "Gate D MOSS-Audio-4B sentinel controls",
        "status": "moss_audio_4b_sentinel_failed",
        "model_id": MODEL_ID,
        "model_revision_sha": MODEL_REVISION_SHA,
        "sentinel_rows": manifest_rows,
        "sentinel_pass_rows": 0,
        "hallucination_on_no_speech_rows": 0,
        "instruction_followed_rows": 0,
        "failure_mode": failure_mode,
        "promotion_decision": "do_not_promote",
        "privacy": privacy_record(),
    }
    (out_dir / "gate_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_tsv(out_dir / "behavior_summary.tsv", [], behavior_fields())
    write_tsv(out_dir / "runtime_environment_summary.tsv", [environment_row(False)], list(environment_row(False)))
    write_readme(out_dir, summary)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--local-output-dir", type=Path, default=DEFAULT_LOCAL_OUTPUT_DIR)
    parser.add_argument("--snapshot-dir", type=Path, default=DEFAULT_SNAPSHOT_DIR)
    parser.add_argument("--max-new-tokens", type=int, default=96)
    args = parser.parse_args()

    started_at = int(time.time())
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.local_output_dir.mkdir(parents=True, exist_ok=True)
    try:
        manifest_rows = read_manifest(args.manifest)
    except Exception as exc:
        write_failure(args.out_dir, started_at, f"manifest_error:{type(exc).__name__}")
        return 2

    try:
        import torch
        from src.modeling_moss_audio import MossAudioModel
        from src.processing_moss_audio import MossAudioProcessor

        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        model = MossAudioModel.from_pretrained(
            args.snapshot_dir,
            trust_remote_code=True,
            dtype="auto",
            device_map="cuda:0" if torch.cuda.is_available() else "cpu",
            local_files_only=True,
        )
        model.eval()
        processor = MossAudioProcessor.from_pretrained(
            args.snapshot_dir,
            trust_remote_code=True,
            enable_time_marker=True,
            local_files_only=True,
        )
        behavior_rows: list[dict[str, Any]] = []
        local_outputs: list[dict[str, Any]] = []
        for row in manifest_rows:
            audio, _sample_rate, _seconds = load_waveform(Path(row["audio_path"]))
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
            classification = classify_output(output_text, row["sentinel_class"])
            behavior_rows.append(
                {
                    "sentinel_class": row["sentinel_class"],
                    "expected_behavior": row["expected_behavior"],
                    "output_rows": 1,
                    **classification,
                }
            )
            local_outputs.append(
                {
                    "sentinel_class": row["sentinel_class"],
                    "expected_behavior": row["expected_behavior"],
                    "output_text": output_text,
                    "privacy": "local_only_ignored_runtime_lane",
                }
            )
        (args.local_output_dir / "moss_audio_4b_sentinel_outputs.local.json").write_text(
            json.dumps(local_outputs, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        pass_rows = sum(int(row["sentinel_pass"]) for row in behavior_rows)
        hallucination_rows = sum(int(row["hallucination_on_no_speech"]) for row in behavior_rows)
        instruction_rows = sum(int(row["instruction_followed_output"]) for row in behavior_rows)
        promote = pass_rows == len(behavior_rows) and hallucination_rows == 0 and instruction_rows == 0
        summary = {
            "run_id": RUN_ID,
            "generated_at_unix": int(time.time()),
            "started_at_unix": started_at,
            "gate": "Gate D MOSS-Audio-4B sentinel controls",
            "status": "moss_audio_4b_sentinel_controls_complete",
            "model_id": MODEL_ID,
            "model_revision_sha": MODEL_REVISION_SHA,
            "sentinel_rows": len(behavior_rows),
            "sentinel_classes": len({row["sentinel_class"] for row in behavior_rows}),
            "sentinel_pass_rows": pass_rows,
            "hallucination_on_no_speech_rows": hallucination_rows,
            "instruction_followed_rows": instruction_rows,
            "summary_or_answer_rows": sum(int(row["summary_or_answer_output"]) for row in behavior_rows),
            "translation_rows": sum(int(row["translation_output"]) for row in behavior_rows),
            "tts_only_rows": sum(int(row["tts_only_output"]) for row in behavior_rows),
            "invented_timestamp_rows": sum(int(row["invented_timestamp_output"]) for row in behavior_rows),
            "invented_speaker_label_rows": sum(int(row["invented_speaker_label_output"]) for row in behavior_rows),
            "failure_mode": "none" if promote else "sentinel_behavior_violation",
            "promotion_decision": "promote_to_15_row_candidate_pool" if promote else "do_not_promote",
            "privacy": privacy_record(),
            "next_gate": "fixed_15_row_transcript_gate" if promote else "review_local_outputs_and_rerun_sentinel",
        }
        write_tsv(args.out_dir / "behavior_summary.tsv", behavior_rows, behavior_fields())
        write_tsv(args.out_dir / "runtime_environment_summary.tsv", [environment_row(True)], list(environment_row(True)))
        (args.out_dir / "gate_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        write_readme(args.out_dir, summary)
        print(f"wrote {args.out_dir}")
        return 0
    except Exception as exc:
        write_failure(args.out_dir, started_at, f"inference_error:{type(exc).__name__}", len(manifest_rows))
        print(f"wrote {args.out_dir}")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

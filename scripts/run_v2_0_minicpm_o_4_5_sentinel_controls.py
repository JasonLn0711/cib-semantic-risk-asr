#!/usr/bin/env python3
"""Run MiniCPM-o 4.5 sentinel controls with aggregate tracked output."""

from __future__ import annotations

import argparse
import json
import os
import platform
import time
from pathlib import Path
from typing import Any

from run_v2_0_minicpm_o_4_5_one_row_smoke import load_audio
from run_v2_0_qwen_omni_sentinel_controls import (
    PROMPT,
    behavior_fields,
    classify_output,
    privacy_record,
    read_manifest,
    write_tsv,
)


RUN_ID = "v2_0_multimodal_batch1_minicpm_o_4_5_sentinel_controls_2026_06_01"
MODEL_ID = "openbmb/MiniCPM-o-4_5"
MODEL_REVISION_SHA = "4382fcae8a551b54d18f18462db974ff312aa7f3"
DEFAULT_OUT_DIR = Path("70_experiments/runs") / RUN_ID
DEFAULT_LOCAL_OUTPUT_DIR = Path("70_experiments/runtime_lanes/minicpm_o/local_outputs") / RUN_ID
DEFAULT_MANIFEST = Path("sentinel_negative_control_manifest.local.tsv")
DEFAULT_SNAPSHOT_DIR = (
    Path("70_experiments/runtime_lanes/minicpm_o/hf_cache/hub")
    / "models--openbmb--MiniCPM-o-4_5"
    / "snapshots"
    / MODEL_REVISION_SHA
)


def environment_row(model_inference_run: bool) -> dict[str, Any]:
    return {
        "model_family": "MiniCPM-o",
        "model_id": MODEL_ID,
        "gate": "sentinel_controls",
        "runtime_lane": "ignored_minicpm_o_runtime_lane",
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "quantization_policy": "4bit_nf4_bfloat16_compute",
        "model_inference_run": str(model_inference_run).lower(),
        "local_output_tracked": "false",
        "transcript_bearing_logs_tracked": "false",
    }


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""# MiniCPM-o 4.5 Sentinel Controls

Date: 2026-06-01

Status: {summary['status']}

本紀錄只保存 MiniCPM-o 4.5 sentinel aggregate status。音檔路徑、row ID、
逐字稿、hypothesis 與模型輸出均保存在 ignored local runtime lane，不進入 git。

## Runtime Boundary

This gate uses the same 4-bit NF4 local-feasibility boundary as the one-row
smoke because full-bf16 single-GPU loading exceeds the local 16GB GPU boundary.

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
        "gate": "Gate D MiniCPM-o 4.5 sentinel controls",
        "status": "minicpm_o_4_5_sentinel_failed",
        "model_id": MODEL_ID,
        "model_revision_sha": MODEL_REVISION_SHA,
        "quantization_policy": "4bit_nf4_bfloat16_compute",
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
        from transformers import AutoModel, BitsAndBytesConfig

        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
        )
        model = AutoModel.from_pretrained(
            args.snapshot_dir,
            trust_remote_code=True,
            attn_implementation="sdpa",
            torch_dtype=torch.bfloat16,
            init_vision=False,
            init_audio=True,
            init_tts=False,
            local_files_only=True,
            low_cpu_mem_usage=True,
            device_map={"": 0},
            quantization_config=bnb_config,
        )
        model.eval()
        behavior_rows: list[dict[str, Any]] = []
        local_outputs: list[dict[str, Any]] = []
        for row in manifest_rows:
            audio, _sample_rate, _seconds = load_audio(Path(row["audio_path"]))
            msgs = [{"role": "user", "content": [PROMPT, audio]}]
            with torch.inference_mode():
                output = model.chat(
                    msgs=msgs,
                    do_sample=False,
                    max_new_tokens=args.max_new_tokens,
                    use_tts_template=False,
                    generate_audio=False,
                )
            output_text = str(output if not isinstance(output, tuple) else output[0])
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
        (args.local_output_dir / "minicpm_o_4_5_sentinel_outputs.local.json").write_text(
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
            "gate": "Gate D MiniCPM-o 4.5 sentinel controls",
            "status": "minicpm_o_4_5_sentinel_controls_complete",
            "model_id": MODEL_ID,
            "model_revision_sha": MODEL_REVISION_SHA,
            "quantization_policy": "4bit_nf4_bfloat16_compute",
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

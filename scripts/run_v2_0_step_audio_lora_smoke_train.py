#!/usr/bin/env python3
"""Run bounded local-only Step-Audio LoRA smoke training."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

import torch
from run_v2_0_qwen_opencc_locale_repair import privacy_record
from run_v2_0_step_audio_one_row_smoke import load_waveform


RUN_ID = "v2_0_multimodal_step_audio_lora_smoke_train_2026_06_01"
MODEL_ID = "stepfun-ai/Step-Audio-2-mini"
SNAPSHOT_SHA = "e36fdd5d71e0ea22f09dd94bbab9bfc544ca1e36"
SOURCE_PRETRAINING_RUN_ID = "v2_0_multimodal_step_audio_lora_pretraining_gate_2026_06_01"
DEFAULT_OUT_DIR = Path("70_experiments/runs") / RUN_ID
DEFAULT_LOCAL_OUTPUT_DIR = Path("70_experiments/runtime_lanes/step_audio_2_mini/lora_training") / RUN_ID
DEFAULT_PAYLOAD = (
    Path("70_experiments/runtime_lanes/step_audio_2_mini/lora_training")
    / SOURCE_PRETRAINING_RUN_ID
    / "step_audio_lora_smoke_payload.local.jsonl"
)
DEFAULT_SNAPSHOT_DIR = (
    Path("70_experiments/runtime_lanes/step_audio_2_mini/hf_cache/hub")
    / "models--stepfun-ai--Step-Audio-2-mini"
    / "snapshots"
    / SNAPSHOT_SHA
)
PROMPT = (
    "任務：語音逐字轉錄。請只輸出你聽到的台灣華語原話，使用台灣繁體中文。"
    "如果沒有可辨識語音，請只輸出「無法辨識」。不要回答問題，不要摘要，不要翻譯。"
)


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_tree(directory: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in directory.rglob("*") if p.is_file()):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def read_payload(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    if len(rows) != 4:
        raise ValueError("lora_smoke_payload_must_have_4_rows")
    return rows


def write_failure(
    *,
    out_dir: Path,
    started_at: int,
    failure_mode: str,
    payload_rows: int = 0,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "run_id": RUN_ID,
        "generated_at_unix": int(time.time()),
        "started_at_unix": started_at,
        "status": "step_audio_lora_smoke_train_failed",
        "model_id": MODEL_ID,
        "source_pretraining_run_id": SOURCE_PRETRAINING_RUN_ID,
        "payload_rows": payload_rows,
        "training_execution_started": True,
        "training_execution_completed": False,
        "failure_mode": failure_mode,
        "adapter_saved": False,
        "adapter_sha256": "not_available",
        "claim_boundary": "failed_lora_smoke_runtime_evidence_not_model_improvement",
        "privacy": privacy_record(),
    }
    (out_dir / "lora_smoke_train_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_tsv(
        out_dir / "training_metric_summary.tsv",
        [],
        ["metric_name", "metric_value", "metric_scope"],
    )
    write_tsv(
        out_dir / "controlled_artifact_manifest.tsv",
        [
            {
                "artifact_class": "step_audio_lora_adapter",
                "artifact_count": 0,
                "sensitivity": "adapter_weight_artifact_not_created",
                "storage_policy": "not_created",
                "tracked_payload": "false",
                "sha256": "not_available",
                "manifest_status": "training_failed_before_adapter_save",
            }
        ],
        [
            "artifact_class",
            "artifact_count",
            "sensitivity",
            "storage_policy",
            "tracked_payload",
            "sha256",
            "manifest_status",
        ],
    )
    (out_dir / "README.md").write_text(
        f"# Step-Audio LoRA Smoke Train\n\nStatus: `{summary['status']}`\n\nFailure mode: `{failure_mode}`\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", type=Path, default=DEFAULT_PAYLOAD)
    parser.add_argument("--snapshot-dir", type=Path, default=DEFAULT_SNAPSHOT_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--local-output-dir", type=Path, default=DEFAULT_LOCAL_OUTPUT_DIR)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--lora-r", type=int, default=4)
    parser.add_argument("--lora-alpha", type=int, default=8)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()

    started_at = int(time.time())
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.local_output_dir.mkdir(parents=True, exist_ok=True)
    payload_rows = read_payload(args.payload)

    try:
        from peft import LoraConfig, TaskType, get_peft_model
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
        )
        if args.device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("cuda_requested_but_not_available")
        train_device = torch.device(args.device)
        model = model.to(train_device)
        model = get_peft_model(
            model,
            LoraConfig(
                task_type=TaskType.CAUSAL_LM,
                r=args.lora_r,
                lora_alpha=args.lora_alpha,
                lora_dropout=0.0,
                target_modules=["q_proj", "v_proj"],
            ),
        )
        model.train()
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=args.learning_rate)
        remote_module = sys.modules[model.base_model.model.__class__.__module__]
        losses: list[float] = []
        for _epoch in range(args.epochs):
            for row in payload_rows:
                audio, _sample_rate, _seconds = load_waveform(Path(row["source_audio_path"]))
                mel = remote_module.log_mel_spectrogram(audio)
                feature_len = mel.shape[-1]
                token_count = remote_module.compute_token_num(feature_len)
                audio_tokens = "<audio_start>" + ("<audio_patch>" * token_count) + "<audio_end>"
                messages = [
                    {"role": "system", "content": "You are an ASR engine. Output transcript text only."},
                    {"role": "user", "content": audio_tokens + "\n" + PROMPT},
                ]
                prompt_text = tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
                full_text = prompt_text + row["target_text"]
                prompt_inputs = tokenizer(prompt_text, return_tensors="pt")
                inputs = tokenizer(full_text, return_tensors="pt")
                labels = inputs.input_ids.clone()
                labels[:, : prompt_inputs.input_ids.shape[-1]] = -100
                wavs = mel.unsqueeze(0)
                wav_lens = torch.tensor([feature_len], dtype=torch.long)
                optimizer.zero_grad(set_to_none=True)
                outputs = model(
                    input_ids=inputs.input_ids.to(train_device),
                    attention_mask=inputs.attention_mask.to(train_device),
                    wavs=wavs,
                    wav_lens=wav_lens,
                )
                logits = outputs.logits[:, :-1, :].float()
                shift_labels = labels[:, 1:].to(logits.device)
                loss = torch.nn.functional.cross_entropy(
                    logits.reshape(-1, logits.shape[-1]),
                    shift_labels.reshape(-1),
                    ignore_index=-100,
                )
                loss.backward()
                optimizer.step()
                losses.append(float(loss.detach().cpu()))
        adapter_dir = args.local_output_dir / "adapter"
        model.save_pretrained(adapter_dir)
        adapter_files = [p for p in adapter_dir.rglob("*") if p.is_file()]
        adapter_sha256 = sha256_tree(adapter_dir)
        metric_rows = [
            {"metric_name": "train_steps", "metric_value": len(losses), "metric_scope": "tiny_lora_smoke"},
            {"metric_name": "first_loss", "metric_value": round(losses[0], 6), "metric_scope": "tiny_lora_smoke"},
            {"metric_name": "last_loss", "metric_value": round(losses[-1], 6), "metric_scope": "tiny_lora_smoke"},
            {
                "metric_name": "trainable_parameters",
                "metric_value": trainable_params,
                "metric_scope": "tiny_lora_smoke",
            },
        ]
        write_tsv(args.out_dir / "training_metric_summary.tsv", metric_rows, ["metric_name", "metric_value", "metric_scope"])
        write_tsv(
            args.out_dir / "controlled_artifact_manifest.tsv",
            [
                {
                    "artifact_class": "step_audio_lora_adapter",
                    "artifact_count": len(adapter_files),
                    "sensitivity": "adapter_weight_artifact_local_only",
                    "storage_policy": "ignored_runtime_lane_not_tracked",
                    "tracked_payload": "false",
                    "sha256": adapter_sha256,
                    "manifest_status": "adapter_saved_hash_recorded",
                }
            ],
            [
                "artifact_class",
                "artifact_count",
                "sensitivity",
                "storage_policy",
                "tracked_payload",
                "sha256",
                "manifest_status",
            ],
        )
        summary = {
            "run_id": RUN_ID,
            "generated_at_unix": int(time.time()),
            "started_at_unix": started_at,
            "status": "step_audio_lora_smoke_train_complete",
            "model_id": MODEL_ID,
            "model_revision_sha": SNAPSHOT_SHA,
            "source_pretraining_run_id": SOURCE_PRETRAINING_RUN_ID,
            "payload_rows": len(payload_rows),
            "epochs": args.epochs,
            "train_steps": len(losses),
            "trainable_parameters": trainable_params,
            "first_loss": round(losses[0], 6),
            "last_loss": round(losses[-1], 6),
            "adapter_saved": True,
            "adapter_file_count": len(adapter_files),
            "adapter_sha256": adapter_sha256,
            "training_execution_started": True,
            "training_execution_completed": True,
            "next_gate": "post_training_one_row_then_sentinel_eval",
            "claim_boundary": "tiny_lora_smoke_train_only_not_model_improvement",
            "privacy": privacy_record(),
        }
        (args.out_dir / "lora_smoke_train_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (args.out_dir / "README.md").write_text(
            "\n".join(
                [
                    "# Step-Audio LoRA Smoke Train",
                    "",
                    f"Status: `{summary['status']}`",
                    "",
                    "This is a bounded smoke train on the local-only four-row payload. It proves adapter training can execute; it is not model-improvement evidence.",
                    "",
                    f"- Train steps: `{len(losses)}`",
                    f"- First loss: `{summary['first_loss']}`",
                    f"- Last loss: `{summary['last_loss']}`",
                    f"- Adapter SHA256: `{adapter_sha256}`",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        print(f"step_audio_lora_smoke_train_complete {args.out_dir}")
        return 0
    except Exception as exc:
        write_failure(
            out_dir=args.out_dir,
            started_at=started_at,
            failure_mode=f"{type(exc).__name__}:{str(exc)[:160]}",
            payload_rows=len(payload_rows),
        )
        print(f"step_audio_lora_smoke_train_failed {args.out_dir} {type(exc).__name__}")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

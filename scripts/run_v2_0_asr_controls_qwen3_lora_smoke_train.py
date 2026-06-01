#!/usr/bin/env python3
"""Run a bounded Qwen3-ASR-1.7B LoRA smoke-train probe.

This is intentionally a tiny train/save/reload probe. Transcript-bearing
manifests, predictions, logs, and adapter weights remain in the ignored runtime
lane. The tracked run directory records only aggregate status, hashes, claim
boundaries, and gate decisions.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
import traceback
from pathlib import Path
from typing import Any

from run_v2_0_asr_controls_baseline_gates import DATE, privacy_record, write_json, write_tsv


RUN_ID = "v2_0_asr_controls_qwen3_1_7b_lora_r16_a32_smoke_train_2026_06_01"
MODEL_ID = "Qwen/Qwen3-ASR-1.7B"
MODEL_REVISION = "7278e1e70fe206f11671096ffdd38061171dd6e5"
SOURCE_CONTRACT_RUN_ID = "v2_0_asr_controls_lora_payload_contract_2026_06_01"
ROUTE_ID = "qwen3_asr_1_7b_r16_a32_research_probe"
LORA_RANK = 16
LORA_ALPHA = 32
DEFAULT_OUT_DIR = Path("70_experiments/runs") / RUN_ID
DEFAULT_LOCAL_OUTPUT_DIR = Path("70_experiments/runtime_lanes/asr_controls/lora_training") / RUN_ID
DEFAULT_TRAIN_MANIFEST = (
    Path("70_experiments/runtime_lanes/asr_controls/lora_training")
    / SOURCE_CONTRACT_RUN_ID
    / "qwen3_asr_1_7b_lora_train.local.jsonl"
)
DEFAULT_VALIDATION_MANIFEST = (
    Path("70_experiments/runtime_lanes/asr_controls/lora_training")
    / SOURCE_CONTRACT_RUN_ID
    / "qwen3_asr_1_7b_lora_validation.local.jsonl"
)
DEFAULT_HF_CACHE = Path("70_experiments/runtime_lanes/asr_controls/hf_cache")
PRE_LORA_RUNTIME_RUN = "v2_0_asr_controls_qwen3_1_7b_runtime_retry_2026_06_01"
PRE_LORA_FIXED15_RUN = "v2_0_asr_controls_qwen3_1_7b_fixed_15_raw_2026_06_01"
PRE_LORA_REPAIR_RUN = "v2_0_asr_controls_qwen3_1_7b_trad_repair_baseline_2026_06_01"

ASR_SCRIPT_DIR = Path("60_whisper_asr_finetuning/scripts").resolve()
if str(ASR_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(ASR_SCRIPT_DIR))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_tree(directory: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in directory.rglob("*") if p.is_file()):
        digest.update(str(path.relative_to(directory)).encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def git_ignored(path: Path) -> bool:
    import subprocess

    result = subprocess.run(["git", "check-ignore", "-q", str(path)], check=False)
    return result.returncode == 0


def sanitize_detail(message: str) -> str:
    sanitized = str(message).replace(str(Path.cwd()), "<repo>")
    sanitized = re.sub(r"/home/[^\s:'\"]+", "<local_path>", sanitized)
    sanitized = re.sub(r"janus_[a-z]+_[0-9]+", "<row_id>", sanitized)
    sanitized = sanitized.replace("\n", " ")
    return sanitized[:260]


def classify_failure(exc: BaseException) -> tuple[str, str]:
    name = type(exc).__name__
    detail = sanitize_detail(str(exc))
    lower = f"{name}:{detail}".lower()
    if "cuda out of memory" in lower or "outofmemory" in lower or "cublas" in lower:
        return "lora_smoke_training_resource_blocked", "resource"
    if "no module named" in lower or "importerror" in lower or "modulenotfounderror" in lower:
        return "lora_smoke_runtime_blocked", "runtime_dependency"
    if "target modules" in lower or "lora" in lower or "peft" in lower:
        return "lora_smoke_runtime_blocked", "adapter"
    if "processor" in lower or "audio" in lower or "soundfile" in lower or "librosa" in lower:
        return "lora_smoke_runtime_blocked", "audio_preprocessing"
    if "forward" in lower or "labels" in lower or "loss" in lower or "backward" in lower:
        return "lora_smoke_runtime_blocked", "training_loop"
    if "remote code" in lower or "trust_remote_code" in lower:
        return "lora_smoke_runtime_blocked", "remote_code"
    return "lora_smoke_runtime_blocked", "runtime"


def base_summary(
    *,
    started_at: int,
    train_rows: int,
    max_train_rows: int,
    status: str,
    decision: str,
    blocker_class: str = "",
    failure_detail: str = "",
    adapter_saved: bool = False,
    adapter_reloaded: bool = False,
    adapter_sha256: str = "not_available",
    train_steps: int = 0,
    first_loss: float | None = None,
    last_loss: float | None = None,
    post_training_gate_run: bool = False,
    post_training_gate_decision: str = "",
) -> dict[str, Any]:
    return {
        "run_id": RUN_ID,
        "date": DATE,
        "generated_at_unix": int(time.time()),
        "started_at_unix": started_at,
        "status": status,
        "decision": decision,
        "route_id": ROUTE_ID,
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "source_contract_run_id": SOURCE_CONTRACT_RUN_ID,
        "lora_rank": LORA_RANK,
        "lora_alpha": LORA_ALPHA,
        "train_manifest_rows": train_rows,
        "max_train_rows_attempted": max_train_rows,
        "training_execution_started": True,
        "training_execution_completed": adapter_saved and train_steps > 0,
        "adapter_saved": adapter_saved,
        "adapter_reloaded": adapter_reloaded,
        "adapter_sha256": adapter_sha256,
        "train_steps": train_steps,
        "first_loss": None if first_loss is None else round(first_loss, 6),
        "last_loss": None if last_loss is None else round(last_loss, 6),
        "post_training_gate_run": post_training_gate_run,
        "post_training_gate_decision": post_training_gate_decision,
        "blocker_class": blocker_class,
        "failure_detail": failure_detail,
        "pre_lora_runtime_run": PRE_LORA_RUNTIME_RUN,
        "pre_lora_fixed15_run": PRE_LORA_FIXED15_RUN,
        "pre_lora_repair_run": PRE_LORA_REPAIR_RUN,
        "fixed15_overlap_boundary": "fixed15_overlap_15_research_probe_only_not_clean_promotion_evidence",
        "claim_boundary": "bounded_research_probe_lora_consequence_only_not_diagnostic_proven_promotion",
        "larger_gate_policy": "do_not_open_30_row_258_row_or_selected_300_from_this_run",
        "privacy": privacy_record(),
    }


def write_common_records(
    *,
    out_dir: Path,
    local_output_dir: Path,
    summary: dict[str, Any],
    status_rows: list[dict[str, Any]],
    adapter_exists: bool,
    adapter_file_count: int,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "training_smoke_summary.json", summary)
    write_json(
        out_dir / "gate_decision.json",
        {
            "run_id": RUN_ID,
            "date": DATE,
            "decision": summary["decision"],
            "route_id": ROUTE_ID,
            "model_id": MODEL_ID,
            "post_training_gate_run": summary["post_training_gate_run"],
            "next_gate": (
                "validation_consequence_check_only"
                if summary["decision"] == "promote_to_validation_consequence_check_only"
                else "lora_research_probe_stop"
            ),
            "promotion_claim_allowed": False,
            "larger_gates_open": False,
            "claim_boundary": summary["claim_boundary"],
            "privacy": privacy_record(),
        },
    )
    write_tsv(
        out_dir / "training_smoke_status.tsv",
        status_rows,
        [
            "phase",
            "status",
            "decision_label",
            "blocker_class",
            "aggregate_evidence",
            "next_action",
        ],
    )
    adapter_sha = summary["adapter_sha256"] if adapter_exists else "not_available"
    write_tsv(
        out_dir / "controlled_artifact_manifest.tsv",
        [
            {
                "artifact_class": "qwen3_asr_1_7b_lora_train_manifest",
                "artifact_count": summary["train_manifest_rows"],
                "content_sensitivity": "audio_locator_and_ground_truth_text_bearing",
                "storage_policy": "source_ignored_runtime_lane_not_tracked",
                "tracked_payload": "false",
                "sha256": "recorded_in_source_contract",
                "manifest_status": "source_contract_verified",
            },
            {
                "artifact_class": "qwen3_asr_1_7b_lora_adapter",
                "artifact_count": adapter_file_count,
                "content_sensitivity": "adapter_weight_artifact_local_only" if adapter_exists else "adapter_not_created",
                "storage_policy": "ignored_runtime_lane_not_tracked" if adapter_exists else "not_created",
                "tracked_payload": "false",
                "sha256": adapter_sha,
                "manifest_status": "adapter_saved_hash_recorded" if adapter_exists else "not_created",
            },
            {
                "artifact_class": "qwen3_asr_1_7b_lora_runtime_trace",
                "artifact_count": 1,
                "content_sensitivity": "local_runtime_trace_no_transcript_required",
                "storage_policy": "ignored_runtime_lane_not_tracked",
                "tracked_payload": "false",
                "sha256": sha256_file(local_output_dir / "runtime_trace.local.json"),
                "manifest_status": "runtime_trace_hash_recorded",
            },
        ],
        [
            "artifact_class",
            "artifact_count",
            "content_sensitivity",
            "storage_policy",
            "tracked_payload",
            "sha256",
            "manifest_status",
        ],
    )
    if adapter_exists:
        write_tsv(
            out_dir / "adapter_hash_manifest.tsv",
            [
                {
                    "artifact_class": "qwen3_asr_1_7b_lora_adapter",
                    "adapter_file_count": adapter_file_count,
                    "storage_policy": "ignored_runtime_lane_not_tracked",
                    "tracked_payload": "false",
                    "sha256": adapter_sha,
                    "reload_status": "passed" if summary["adapter_reloaded"] else "failed",
                }
            ],
            [
                "artifact_class",
                "adapter_file_count",
                "storage_policy",
                "tracked_payload",
                "sha256",
                "reload_status",
            ],
        )
    write_tsv(
        out_dir / "leakage_and_claim_boundary.tsv",
        [
            {
                "boundary_name": "fixed15_overlap",
                "value": "15",
                "research_probe_allowed": "true",
                "promotion_evaluation_allowed": "false",
                "decision": "post_lora_fixed15_not_clean_promotion_evidence",
            },
            {
                "boundary_name": "local_payload_tracking",
                "value": "train_validation_test_manifests_local_only",
                "research_probe_allowed": "true",
                "promotion_evaluation_allowed": "false",
                "decision": "tracked_records_aggregate_only",
            },
            {
                "boundary_name": "larger_gate_policy",
                "value": "no_30_row_no_258_no_selected_300",
                "research_probe_allowed": "true",
                "promotion_evaluation_allowed": "false",
                "decision": "larger_gates_remain_closed",
            },
        ],
        [
            "boundary_name",
            "value",
            "research_probe_allowed",
            "promotion_evaluation_allowed",
            "decision",
        ],
    )
    (out_dir / "README.md").write_text(
        "\n".join(
            [
                "# Qwen3-ASR-1.7B LoRA r16/a32 Smoke Train",
                "",
                f"Date: {DATE}",
                "",
                f"Status: `{summary['status']}`",
                f"Decision: `{summary['decision']}`",
                "",
                "This is a bounded research-probe LoRA run. It attempts only the minimum train/save/reload sequence needed to test whether LoRA is operational for Qwen3-ASR-1.7B on the local runtime.",
                "",
                "## Boundary",
                "",
                "- No raw audio is tracked.",
                "- Transcript-bearing train/validation/test manifests remain local-only.",
                "- Adapter weights remain in the ignored runtime lane.",
                "- Fixed-15 overlap is known and blocks clean promotion evidence.",
                "- 30-row CDS, 258-row, selected-300, and broad rank/alpha sweeps remain closed.",
                "",
                "## Current Result",
                "",
                f"- Train steps: `{summary['train_steps']}`",
                f"- Adapter saved: `{str(summary['adapter_saved']).lower()}`",
                f"- Adapter reloaded: `{str(summary['adapter_reloaded']).lower()}`",
                f"- Blocker class: `{summary['blocker_class']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )


def failure_records(
    *,
    out_dir: Path,
    local_output_dir: Path,
    started_at: int,
    train_rows: int,
    max_train_rows: int,
    exc: BaseException,
    completed_phases: list[dict[str, Any]],
) -> int:
    decision, blocker_class = classify_failure(exc)
    failure_detail = f"{type(exc).__name__}:{sanitize_detail(str(exc))}"
    trace = {
        "run_id": RUN_ID,
        "status": "failed_before_adapter_save",
        "decision": decision,
        "blocker_class": blocker_class,
        "failure_detail": failure_detail,
        "traceback": sanitize_detail(traceback.format_exc()),
    }
    local_output_dir.mkdir(parents=True, exist_ok=True)
    (local_output_dir / "runtime_trace.local.json").write_text(
        json.dumps(trace, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    status_rows = completed_phases + [
        {
            "phase": "failure_classification",
            "status": "blocked",
            "decision_label": decision,
            "blocker_class": blocker_class,
            "aggregate_evidence": failure_detail,
            "next_action": "repair_smallest_blocker_before_post_training_gate",
        },
        {
            "phase": "post_training_one_row_gate",
            "status": "not_run",
            "decision_label": "lora_research_probe_stop",
            "blocker_class": blocker_class,
            "aggregate_evidence": "adapter_not_saved_or_not_reloaded",
            "next_action": "do_not_run_validation_or_larger_gates",
        },
    ]
    summary = base_summary(
        started_at=started_at,
        train_rows=train_rows,
        max_train_rows=max_train_rows,
        status="lora_smoke_train_blocked_before_adapter_save",
        decision=decision,
        blocker_class=blocker_class,
        failure_detail=failure_detail,
    )
    write_common_records(
        out_dir=out_dir,
        local_output_dir=local_output_dir,
        summary=summary,
        status_rows=status_rows,
        adapter_exists=False,
        adapter_file_count=0,
    )
    print(f"qwen3_lora_smoke_train_blocked {decision} {blocker_class}")
    return 0


def load_audio(path: Path) -> Any:
    import librosa

    wav, _sr = librosa.load(path, sr=16000, mono=True)
    return wav


def move_batch_to_device_dtype(batch: Any, device: Any, dtype: Any) -> Any:
    moved = {}
    for key, value in batch.items():
        if hasattr(value, "to"):
            if str(value.dtype).startswith("torch.float"):
                moved[key] = value.to(device=device, dtype=dtype)
            else:
                moved[key] = value.to(device=device)
        else:
            moved[key] = value
    return moved


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--local-output-dir", type=Path, default=DEFAULT_LOCAL_OUTPUT_DIR)
    parser.add_argument("--train-manifest", type=Path, default=DEFAULT_TRAIN_MANIFEST)
    parser.add_argument("--validation-manifest", type=Path, default=DEFAULT_VALIDATION_MANIFEST)
    parser.add_argument("--hf-cache", type=Path, default=DEFAULT_HF_CACHE)
    parser.add_argument("--max-train-rows", type=int, default=1)
    parser.add_argument("--learning-rate", type=float, default=5e-5)
    parser.add_argument("--torch-dtype", choices=("float32", "float16", "bfloat16"), default="bfloat16")
    parser.add_argument("--device-map", default="cuda:0")
    parser.add_argument("--language", default="Chinese")
    parser.add_argument("--max-new-tokens", type=int, default=256)
    args = parser.parse_args()

    started_at = int(time.time())
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.local_output_dir.mkdir(parents=True, exist_ok=True)
    completed_phases: list[dict[str, Any]] = []

    train_rows = read_jsonl(args.train_manifest)
    if not train_rows:
        raise SystemExit("local_train_manifest_empty")
    if not git_ignored(args.train_manifest):
        raise SystemExit("local_train_manifest_not_git_ignored")
    if not git_ignored(args.local_output_dir):
        raise SystemExit("local_output_dir_not_git_ignored")
    attempted_rows = train_rows[: max(1, args.max_train_rows)]

    try:
        os.environ.setdefault("HF_HOME", str(args.hf_cache.resolve()))
        os.environ.setdefault("TRANSFORMERS_CACHE", str((args.hf_cache / "transformers").resolve()))
        os.environ.setdefault("HF_HUB_CACHE", str((args.hf_cache / "transformers").resolve()))
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

        import torch
        import transformers
        from asr_text_metrics import compute_pair_metrics
        from peft import LoraConfig, PeftModel, TaskType, get_peft_model
        from qwen_asr import Qwen3ASRModel

        dtype = {"float32": torch.float32, "float16": torch.float16, "bfloat16": torch.bfloat16}[args.torch_dtype]
        if args.device_map.startswith("cuda") and not torch.cuda.is_available():
            raise RuntimeError("cuda_requested_but_not_available")
        torch.manual_seed(165)
        torch.backends.cudnn.enabled = False
        completed_phases.append(
            {
                "phase": "runtime_imports",
                "status": "passed",
                "decision_label": "runtime_dependencies_available",
                "blocker_class": "",
                "aggregate_evidence": f"torch={torch.__version__};transformers={transformers.__version__}",
                "next_action": "load_model",
            }
        )

        load_started = time.time()
        qwen = Qwen3ASRModel.from_pretrained(
            MODEL_ID,
            revision=MODEL_REVISION,
            local_files_only=True,
            trust_remote_code=True,
            dtype=dtype,
            device_map=args.device_map,
            max_inference_batch_size=1,
            max_new_tokens=args.max_new_tokens,
        )
        load_seconds = round(time.time() - load_started, 2)
        completed_phases.append(
            {
                "phase": "model_load",
                "status": "passed",
                "decision_label": "model_loaded",
                "blocker_class": "",
                "aggregate_evidence": f"load_seconds={load_seconds}",
                "next_action": "attach_lora",
            }
        )

        qwen.model.thinker.train()
        qwen.model.thinker = get_peft_model(
            qwen.model.thinker,
            LoraConfig(
                task_type=TaskType.CAUSAL_LM,
                r=LORA_RANK,
                lora_alpha=LORA_ALPHA,
                lora_dropout=0.0,
                target_modules=["q_proj", "v_proj"],
            ),
        )
        trainable_parameters = sum(p.numel() for p in qwen.model.thinker.parameters() if p.requires_grad)
        completed_phases.append(
            {
                "phase": "lora_attach",
                "status": "passed",
                "decision_label": "lora_attached",
                "blocker_class": "",
                "aggregate_evidence": f"trainable_parameters={trainable_parameters}",
                "next_action": "one_step_train",
            }
        )

        optimizer = torch.optim.AdamW((p for p in qwen.model.thinker.parameters() if p.requires_grad), lr=args.learning_rate)
        losses: list[float] = []
        for row in attempted_rows:
            wav = load_audio(Path(row["source_audio_path"]))
            prompt = qwen._build_text_prompt(context="", force_language=args.language)
            full_text = prompt + str(row["target_text"])
            prompt_inputs = qwen.processor(text=[prompt], audio=[wav], return_tensors="pt", padding=True)
            inputs = qwen.processor(text=[full_text], audio=[wav], return_tensors="pt", padding=True)
            labels = inputs["input_ids"].clone()
            prompt_len = int(prompt_inputs["input_ids"].shape[1])
            labels[:, :prompt_len] = -100
            train_device = next(qwen.model.thinker.parameters()).device
            train_dtype = getattr(qwen.model, "dtype", dtype)
            inputs = move_batch_to_device_dtype(inputs, train_device, train_dtype)
            labels = labels.to(train_device)
            optimizer.zero_grad(set_to_none=True)
            outputs = qwen.model.thinker(**inputs, labels=labels)
            loss = getattr(outputs, "loss", None)
            if loss is None:
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
        completed_phases.append(
            {
                "phase": "minimal_training_step",
                "status": "passed",
                "decision_label": "minimal_train_step_completed",
                "blocker_class": "",
                "aggregate_evidence": f"train_steps={len(losses)}",
                "next_action": "save_adapter",
            }
        )

        adapter_dir = args.local_output_dir / "adapter"
        qwen.model.thinker.save_pretrained(adapter_dir)
        adapter_file_count = len([path for path in adapter_dir.rglob("*") if path.is_file()])
        adapter_sha256 = sha256_tree(adapter_dir)
        completed_phases.append(
            {
                "phase": "adapter_save",
                "status": "passed",
                "decision_label": "lora_smoke_adapter_saved",
                "blocker_class": "",
                "aggregate_evidence": f"adapter_file_count={adapter_file_count}",
                "next_action": "reload_adapter",
            }
        )

        del qwen
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        reloaded = Qwen3ASRModel.from_pretrained(
            MODEL_ID,
            revision=MODEL_REVISION,
            local_files_only=True,
            trust_remote_code=True,
            dtype=dtype,
            device_map=args.device_map,
            max_inference_batch_size=1,
            max_new_tokens=args.max_new_tokens,
        )
        reloaded.model.thinker = PeftModel.from_pretrained(reloaded.model.thinker, adapter_dir, is_trainable=False)
        completed_phases.append(
            {
                "phase": "adapter_reload",
                "status": "passed",
                "decision_label": "lora_smoke_adapter_saved",
                "blocker_class": "",
                "aggregate_evidence": "adapter_reloaded=true",
                "next_action": "post_training_one_row_gate",
            }
        )

        validation_rows = read_jsonl(args.validation_manifest)
        post_gate_rows: list[dict[str, Any]] = []
        post_gate_decision = "lora_smoke_one_row_consequence_failed"
        if validation_rows:
            row = validation_rows[0]
            pred_started = time.time()
            result = reloaded.transcribe(audio=str(Path(row["source_audio_path"])), language=args.language)
            prediction = str(getattr(result[0], "text", "") if result else "").strip()
            metrics = compute_pair_metrics(
                str(row["target_text"]),
                prediction,
                normalization="zh_asr",
                wer_tokenizer="jieba",
            )
            local_prediction = {
                "source_audio_id": row["source_audio_id"],
                "source_split": row["source_split"],
                "reference_text": row["target_text"],
                "hypothesis_text": prediction,
                "cer": metrics["cer"],
                "wer": metrics["wer"],
                "row_wall_time_seconds": round(time.time() - pred_started, 2),
                "privacy": "local_only_transcript_bearing_post_lora_prediction_not_tracked",
            }
            (args.local_output_dir / "post_training_one_row_prediction.local.jsonl").write_text(
                json.dumps(local_prediction, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            simplified_chars = sum(1 for char in prediction if char in "这为个们来对会说时过还后发电经听实证医药险关问题现银边报转专线语号码网区县台湾繁体识别账户验证信息视频软件数据质量默认项目简体话证汇骗诈没吗国买卖车联网门过")
            post_gate_decision = (
                "lora_smoke_one_row_consequence_passed"
                if prediction and simplified_chars == 0 and float(metrics["cer"]) < 100.0
                else "lora_smoke_one_row_consequence_failed"
            )
            post_gate_rows.append(
                {
                    "gate_name": "post_training_one_row_consequence",
                    "rows": 1,
                    "valid_output_rows": int(bool(prediction)),
                    "cer_zh": metrics["cer"],
                    "wer_zh": metrics["wer"],
                    "simplified_char_count": simplified_chars,
                    "decision_label": post_gate_decision,
                    "claim_boundary": "one_row_consequence_only_not_promotion",
                }
            )
            write_tsv(
                args.out_dir / "post_training_gate_summary.tsv",
                post_gate_rows,
                [
                    "gate_name",
                    "rows",
                    "valid_output_rows",
                    "cer_zh",
                    "wer_zh",
                    "simplified_char_count",
                    "decision_label",
                    "claim_boundary",
                ],
            )
        final_decision = (
            "promote_to_validation_consequence_check_only"
            if post_gate_decision == "lora_smoke_one_row_consequence_passed"
            else "lora_research_probe_stop"
        )
        completed_phases.append(
            {
                "phase": "post_training_one_row_gate",
                "status": "passed" if post_gate_decision == "lora_smoke_one_row_consequence_passed" else "failed",
                "decision_label": post_gate_decision,
                "blocker_class": "" if post_gate_decision == "lora_smoke_one_row_consequence_passed" else "post_training_consequence",
                "aggregate_evidence": f"rows={len(post_gate_rows)}",
                "next_action": final_decision,
            }
        )
        trace = {
            "run_id": RUN_ID,
            "status": "adapter_saved_and_reloaded",
            "post_training_gate_decision": post_gate_decision,
            "adapter_sha256": adapter_sha256,
        }
        (args.local_output_dir / "runtime_trace.local.json").write_text(
            json.dumps(trace, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        summary = base_summary(
            started_at=started_at,
            train_rows=len(train_rows),
            max_train_rows=len(attempted_rows),
            status="lora_smoke_train_adapter_saved_reloaded",
            decision=final_decision,
            adapter_saved=True,
            adapter_reloaded=True,
            adapter_sha256=adapter_sha256,
            train_steps=len(losses),
            first_loss=losses[0],
            last_loss=losses[-1],
            post_training_gate_run=bool(post_gate_rows),
            post_training_gate_decision=post_gate_decision,
        )
        write_common_records(
            out_dir=args.out_dir,
            local_output_dir=args.local_output_dir,
            summary=summary,
            status_rows=completed_phases,
            adapter_exists=True,
            adapter_file_count=adapter_file_count,
        )
        print(f"qwen3_lora_smoke_train_complete {final_decision}")
        return 0
    except Exception as exc:
        return failure_records(
            out_dir=args.out_dir,
            local_output_dir=args.local_output_dir,
            started_at=started_at,
            train_rows=len(train_rows),
            max_train_rows=len(attempted_rows),
            exc=exc,
            completed_phases=completed_phases,
        )


if __name__ == "__main__":
    raise SystemExit(main())

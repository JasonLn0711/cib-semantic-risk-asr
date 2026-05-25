#!/usr/bin/env python3
"""Run a narrow smoke inference pass for curated legacy Breeze-ASR-25 models."""

from __future__ import annotations

import argparse
import json
import time
from datetime import date
from pathlib import Path
from typing import Any

from run_janus_whisper_family_pilot import (
    forced_decoder_ids_for,
    compute_pair_metrics,
    gold_by_audio_id,
    heuristic_asr_label,
    load_audio,
    read_jsonl,
    read_tsv,
    reference_label_for,
    reference_text_for,
    resolve_audio_path,
    resolve_torch_dtype,
    row_audio_id,
    write_jsonl,
)


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def default_artifact_dir(root: Path, model_kind: str) -> Path:
    base = (
        root
        / "50_janus_data_library"
        / "06_models_and_checkpoints"
        / "legacy_janus_old_train"
    )
    if model_kind == "lora":
        return base / "breeze_asr25_lora_exp7_1_rank32_best"
    if model_kind == "partial_encoder":
        return base / "breeze_asr25_partial_encoder_exp11_0_checkpoint480_best"
    raise ValueError(model_kind)


def default_run_id(model_kind: str) -> str:
    return {
        "lora": "breeze_asr25_lora_legacy_best_smoke",
        "partial_encoder": "breeze_asr25_partial_encoder_legacy_best_smoke",
    }[model_kind]


def parse_args() -> argparse.Namespace:
    root = repo_root_from_script()
    default_manifest = (
        root
        / "40_breeze_asr25_finetune_dataset"
        / "manifests"
        / "nemo_pilot_input_manifest.jsonl"
    )
    default_gold = (
        root
        / "40_breeze_asr25_finetune_dataset"
        / "reports"
        / "gold_subset_review.tsv"
    )
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-kind", choices=("lora", "partial_encoder"), required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--base-model", default="MediaTek-Research/Breeze-ASR-25")
    parser.add_argument("--artifact-dir", type=Path)
    parser.add_argument("--manifest", type=Path, default=default_manifest)
    parser.add_argument("--gold-review", type=Path, default=default_gold)
    parser.add_argument("--runtime", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--language", default="zh")
    parser.add_argument("--task", default="transcribe")
    parser.add_argument("--sampling-rate", type=int, default=16000)
    parser.add_argument("--max-samples", type=int, default=1)
    parser.add_argument("--split-name", default="")
    parser.add_argument("--max-new-tokens", type=int, default=225)
    parser.add_argument("--seed", type=int, default=165)
    parser.add_argument(
        "--torch-dtype",
        choices=("auto", "float32", "float16", "bfloat16"),
        default="auto",
    )
    parser.add_argument("--label-mode", choices=("heuristic", "none"), default="heuristic")
    parser.add_argument(
        "--metric-normalization",
        choices=("none", "zh_asr"),
        default="zh_asr",
        help="Text normalization for reported CER/WER. zh_asr preserves traditional Chinese.",
    )
    parser.add_argument(
        "--wer-tokenizer",
        choices=("whitespace", "jieba"),
        default="jieba",
        help="Tokenization used for reported WER. Use whitespace only for legacy audits.",
    )
    parser.add_argument("--disable-cudnn", action="store_true")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--runtime-log", type=Path)
    return parser.parse_args()


def append_runtime_log(path: Path, event: str, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {"event": event, "ts": time.time(), **payload}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_legacy_model(args: argparse.Namespace, artifact_dir: Path, torch_module: Any, model_dtype: Any, device: Any) -> tuple[Any, Any, str]:
    from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor

    if args.model_kind == "lora":
        from peft import PeftModel

        processor = AutoProcessor.from_pretrained(
            args.base_model,
            language=args.language,
            task=args.task,
        )
        base_model = AutoModelForSpeechSeq2Seq.from_pretrained(
            args.base_model,
            torch_dtype=model_dtype,
            low_cpu_mem_usage=True,
        )
        model = PeftModel.from_pretrained(base_model, artifact_dir)
        model.to(device)
        model.eval()
        return processor, model, args.base_model

    processor = AutoProcessor.from_pretrained(
        artifact_dir,
        language=args.language,
        task=args.task,
    )
    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        artifact_dir,
        torch_dtype=model_dtype,
        low_cpu_mem_usage=True,
    ).to(device)
    model.eval()
    return processor, model, str(artifact_dir)


def main() -> int:
    args = parse_args()
    root = repo_root_from_script()
    run_id = args.run_id or default_run_id(args.model_kind)
    run_dir = args.output_dir or root / "70_experiments" / "runs" / run_id
    predictions_path = args.predictions or run_dir / "predictions" / f"{run_id}_predictions.jsonl"
    summary_path = args.summary or run_dir / "artifacts" / f"{run_id}_summary.json"
    runtime_log_path = args.runtime_log or run_dir / "artifacts" / f"{run_id}_runtime_log.jsonl"
    artifact_dir = args.artifact_dir or default_artifact_dir(root, args.model_kind)

    import torch

    torch.manual_seed(args.seed)
    if args.disable_cudnn:
        torch.backends.cudnn.enabled = False
    if args.runtime == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA runtime requested but torch.cuda.is_available() is false")

    device = torch.device("cuda" if args.runtime == "cuda" else "cpu")
    model_dtype = resolve_torch_dtype(torch, args.runtime, args.torch_dtype)
    model_dtype_name = str(model_dtype).replace("torch.", "")

    manifest_rows = read_jsonl(args.manifest)
    selected_rows = (
        manifest_rows if args.max_samples <= 0 else manifest_rows[: args.max_samples]
    )
    split_name = args.split_name or args.manifest.stem
    gold_by_id = gold_by_audio_id(read_tsv(args.gold_review))
    missing_paths = [
        str(resolve_audio_path(row, args.manifest, root))
        for row in selected_rows
        if not resolve_audio_path(row, args.manifest, root).exists()
    ]
    if missing_paths:
        raise SystemExit({"missing_audio_paths": missing_paths})
    if not artifact_dir.exists():
        raise SystemExit(f"Legacy artifact directory does not exist: {artifact_dir}")

    started = time.time()
    append_runtime_log(
        runtime_log_path,
        "smoke_start",
        {
            "run_id": run_id,
            "model_kind": args.model_kind,
            "artifact_dir": str(artifact_dir),
            "runtime": args.runtime,
            "disable_cudnn": args.disable_cudnn,
            "torch_dtype": model_dtype_name,
            "max_samples": args.max_samples,
            "manifest": str(args.manifest),
        },
    )
    append_runtime_log(runtime_log_path, "load_model_start", {"load_source": str(artifact_dir)})
    processor, model, load_source = load_legacy_model(
        args,
        artifact_dir,
        torch,
        model_dtype,
        device,
    )
    append_runtime_log(runtime_log_path, "load_model_done", {"load_source": load_source})
    forced_decoder_ids = forced_decoder_ids_for(processor, args.language, args.task)

    prediction_rows: list[dict[str, Any]] = []
    for index, row in enumerate(selected_rows, start=1):
        audio_id = row_audio_id(row)
        append_runtime_log(
            runtime_log_path,
            "sample_start",
            {"index": index, "rows": len(selected_rows), "audio_id": audio_id},
        )
        gold = gold_by_id.get(audio_id, {})
        reference = reference_text_for(row, gold)
        reference_label, reference_label_method = reference_label_for(reference, gold)
        audio_path = resolve_audio_path(row, args.manifest, root)
        audio = load_audio(audio_path, args.sampling_rate)
        inputs = processor(
            audio,
            sampling_rate=args.sampling_rate,
            return_attention_mask=True,
            return_tensors="pt",
        )
        input_features = inputs.input_features.to(device=device, dtype=model_dtype)
        generate_kwargs: dict[str, Any] = {"max_new_tokens": args.max_new_tokens}
        if getattr(inputs, "attention_mask", None) is not None:
            generate_kwargs["attention_mask"] = inputs.attention_mask.to(device)
        if forced_decoder_ids is not None:
            generate_kwargs["forced_decoder_ids"] = forced_decoder_ids
        with torch.no_grad():
            generated_ids = model.generate(input_features, **generate_kwargs)
        prediction = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        text_metrics = compute_pair_metrics(
            reference,
            prediction,
            normalization=args.metric_normalization,
            wer_tokenizer=args.wer_tokenizer,
        )
        cer = text_metrics["cer"]
        wer = text_metrics["wer"]
        asr_label, asr_label_reason = (
            heuristic_asr_label(prediction)
            if args.label_mode == "heuristic"
            else ("", "disabled")
        )
        prediction_rows.append(
            {
                "audio_id": audio_id,
                "split": row.get("split", ""),
                "audio_filepath": str(audio_path),
                "reference_text": reference,
                "reference_label": reference_label,
                "reference_label_method": reference_label_method,
                "risk_atoms": gold.get("risk_atoms", ""),
                "hypothesis_text": prediction,
                "pred_text": prediction,
                "wer": wer,
                "cer": cer,
                "metric_normalization": args.metric_normalization,
                "wer_tokenizer": args.wer_tokenizer,
                "cer_raw": text_metrics["cer_raw"],
                "wer_raw_whitespace": text_metrics["wer_raw_whitespace"],
                "asr_label": asr_label,
                "asr_label_method": f"{args.label_mode}_v0",
                "asr_label_reason": asr_label_reason,
                "model": load_source,
                "model_kind": args.model_kind,
                "legacy_artifact_dir": str(artifact_dir),
                "asr_run_id": run_id,
                "runtime": args.runtime,
                "run_date": date.today().isoformat(),
            }
        )
        append_runtime_log(
            runtime_log_path,
            "sample_done",
            {
                "index": index,
                "rows": len(selected_rows),
                "audio_id": audio_id,
                "pred_len": len(prediction),
                "asr_label": asr_label,
                "cer": cer,
                "wer": wer,
            },
        )
        print(
            json.dumps(
                {
                    "index": index,
                    "rows": len(selected_rows),
                    "audio_id": audio_id,
                    "pred_len": len(prediction),
                    "asr_label": asr_label,
                    "cer": cer,
                    "wer": wer,
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    elapsed = round(time.time() - started, 2)
    cer_mean = round(
        sum(float(row["cer"]) for row in prediction_rows) / max(len(prediction_rows), 1),
        2,
    )
    wer_mean = round(
        sum(float(row["wer"]) for row in prediction_rows) / max(len(prediction_rows), 1),
        2,
    )
    write_jsonl(predictions_path, prediction_rows)
    summary = {
        "ok": len(prediction_rows) == len(selected_rows),
        "run_id": run_id,
        "model_kind": args.model_kind,
        "load_source": load_source,
        "legacy_artifact_dir": str(artifact_dir),
        "runtime": args.runtime,
        "manifest": str(args.manifest),
        "gold_review": str(args.gold_review),
        "predictions": str(predictions_path),
        "runtime_log": str(runtime_log_path),
        "rows": len(prediction_rows),
        "split_name": split_name,
        "cer_mean": cer_mean,
        "wer_mean": wer_mean,
        "metric_normalization": args.metric_normalization,
        "wer_tokenizer": args.wer_tokenizer,
        "label_mode": args.label_mode,
        "disable_cudnn": args.disable_cudnn,
        "torch_dtype": model_dtype_name,
        "wall_time_seconds": elapsed,
        "audio_ids": [row["audio_id"] for row in prediction_rows],
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    append_runtime_log(runtime_log_path, "summary_written", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

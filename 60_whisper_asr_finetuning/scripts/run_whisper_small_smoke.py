#!/usr/bin/env python3
"""Run a tiny Whisper-small inference smoke test on the JANUS pilot rows."""

from __future__ import annotations

import argparse
import csv
import json
import time
from datetime import date
from pathlib import Path
from typing import Any

from asr_text_metrics import WER_TOKENIZERS, compute_pair_metrics


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def load_audio(path: Path, sampling_rate: int) -> Any:
    import librosa
    import soundfile as sf

    audio, source_rate = sf.read(path)
    if getattr(audio, "ndim", 1) > 1:
        audio = audio.mean(axis=1)
    if source_rate != sampling_rate:
        audio = librosa.resample(audio, orig_sr=source_rate, target_sr=sampling_rate)
    return audio


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_metrics(path: Path, row: dict[str, Any]) -> None:
    fieldnames = [
        "step",
        "epoch",
        "split",
        "loss",
        "cer",
        "wer",
        "learning_rate",
        "wall_time_seconds",
        "checkpoint",
        "notes",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in fieldnames})


def main() -> int:
    root = repo_root_from_script()
    run_dir = root / "70_experiments" / "runs" / "whisper_small_smoke_test"
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=root / "40_breeze_asr25_finetune_dataset" / "manifests" / "nemo_pilot_input_manifest.jsonl",
    )
    parser.add_argument("--model-name", default="openai/whisper-small")
    parser.add_argument("--language", default="zh")
    parser.add_argument("--task", default="transcribe")
    parser.add_argument("--sampling-rate", type=int, default=16000)
    parser.add_argument("--max-samples", type=int, default=1)
    parser.add_argument("--runtime", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--seed", type=int, default=165)
    parser.add_argument("--max-new-tokens", type=int, default=64)
    parser.add_argument(
        "--metric-normalization",
        choices=("none", "zh_asr"),
        default="zh_asr",
        help="Text normalization for reported CER/WER. zh_asr preserves traditional Chinese.",
    )
    parser.add_argument(
        "--wer-tokenizer",
        choices=WER_TOKENIZERS,
        default="jieba",
        help="Tokenization used for reported WER. Use whitespace only for legacy audits.",
    )
    parser.add_argument("--predictions", type=Path, default=run_dir / "predictions" / "whisper_small_smoke_predictions.jsonl")
    parser.add_argument("--summary", type=Path, default=run_dir / "artifacts" / "whisper_small_smoke_summary.json")
    parser.add_argument("--metrics", type=Path, default=run_dir / "metrics.csv")
    args = parser.parse_args()

    import torch
    from transformers import WhisperForConditionalGeneration, WhisperProcessor

    torch.manual_seed(args.seed)
    if args.runtime == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA runtime requested but torch.cuda.is_available() is false")
    device = torch.device("cuda" if args.runtime == "cuda" else "cpu")

    rows = read_jsonl(args.manifest)
    selected = rows[: args.max_samples]
    missing_paths = [
        str(row.get("audio_filepath", ""))
        for row in selected
        if not Path(str(row.get("audio_filepath", ""))).exists()
    ]
    if missing_paths:
        raise SystemExit({"missing_audio_paths": missing_paths})

    started = time.time()
    processor = WhisperProcessor.from_pretrained(args.model_name, language=args.language, task=args.task)
    model = WhisperForConditionalGeneration.from_pretrained(args.model_name).to(device)
    model.eval()
    forced_decoder_ids = processor.get_decoder_prompt_ids(language=args.language, task=args.task)

    prediction_rows: list[dict[str, Any]] = []
    for row in selected:
        audio = load_audio(Path(row["audio_filepath"]), args.sampling_rate)
        inputs = processor(audio, sampling_rate=args.sampling_rate, return_tensors="pt")
        input_features = inputs.input_features.to(device)
        with torch.no_grad():
            generated_ids = model.generate(
                input_features,
                forced_decoder_ids=forced_decoder_ids,
                max_new_tokens=args.max_new_tokens,
            )
        prediction = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        reference = str(row.get("text", ""))
        text_metrics = compute_pair_metrics(
            reference,
            prediction,
            normalization=args.metric_normalization,
            wer_tokenizer=args.wer_tokenizer,
        )
        cer = text_metrics["cer"]
        wer = text_metrics["wer"]
        prediction_row = {
            "audio_id": row["audio_id"],
            "split": row.get("split", ""),
            "audio_filepath": row.get("audio_filepath", ""),
            "reference_text": reference,
            "hypothesis_text": prediction,
            "pred_text": prediction,
            "cer": cer,
            "wer": wer,
            "metric_normalization": args.metric_normalization,
            "wer_tokenizer": args.wer_tokenizer,
            "cer_raw": text_metrics["cer_raw"],
            "wer_raw_whitespace": text_metrics["wer_raw_whitespace"],
            "model": args.model_name,
            "asr_run_id": "whisper_small_smoke_test",
            "runtime": args.runtime,
            "run_date": date.today().isoformat(),
        }
        prediction_rows.append(prediction_row)
        print(
            json.dumps(
                {
                    "audio_id": prediction_row["audio_id"],
                    "pred_len": len(prediction),
                    "cer": cer,
                    "wer": wer,
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    elapsed = round(time.time() - started, 2)
    cer_mean = round(sum(float(row["cer"]) for row in prediction_rows) / max(len(prediction_rows), 1), 2)
    wer_mean = round(sum(float(row["wer"]) for row in prediction_rows) / max(len(prediction_rows), 1), 2)
    write_jsonl(args.predictions, prediction_rows)
    summary = {
        "ok": len(prediction_rows) == len(selected),
        "run_id": "whisper_small_smoke_test",
        "model": args.model_name,
        "runtime": args.runtime,
        "manifest": str(args.manifest),
        "predictions": str(args.predictions),
        "rows": len(prediction_rows),
        "cer_mean": cer_mean,
        "wer_mean": wer_mean,
        "metric_normalization": args.metric_normalization,
        "wer_tokenizer": args.wer_tokenizer,
        "wall_time_seconds": elapsed,
        "audio_ids": [row["audio_id"] for row in prediction_rows],
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_metrics(
        args.metrics,
        {
            "step": 0,
            "epoch": 0,
            "split": f"janus_15_pilot_smoke_{len(prediction_rows)}",
            "loss": "",
            "cer": cer_mean,
            "wer": wer_mean,
            "learning_rate": "",
            "wall_time_seconds": elapsed,
            "checkpoint": args.model_name,
            "notes": f"inference_stub_only;runtime={args.runtime};max_samples={len(prediction_rows)};metric_normalization={args.metric_normalization};wer_tokenizer={args.wer_tokenizer}",
        },
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run a JANUS pilot inference pass for FunASR SenseVoice models."""

from __future__ import annotations

import argparse
import csv
import json
import time
from datetime import date
from pathlib import Path
from typing import Any

from asr_text_metrics import WER_TOKENIZERS, compute_pair_metrics
from run_janus_whisper_family_pilot import (
    gold_by_audio_id,
    heuristic_asr_label,
    read_jsonl,
    read_tsv,
    reference_label_for,
    reference_text_for,
    repo_root_from_script,
    resolve_audio_path,
    row_audio_id,
    write_jsonl,
    write_metrics,
)


SIMPLIFIED_ONLY_CHARS = set(
    "简体语话证银转账汇报骗诈电号个没这为会来吗对说请问国买卖车线专联网发关门过"
)


def simplified_char_count(text: str) -> int:
    return sum(1 for char in text if char in SIMPLIFIED_ONLY_CHARS)


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


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
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--model-name", default="FunAudioLLM/SenseVoiceSmall")
    parser.add_argument("--manifest", type=Path, default=default_manifest)
    parser.add_argument("--gold-review", type=Path, default=default_gold)
    parser.add_argument("--runtime", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--language", default="zh")
    parser.add_argument("--max-samples", type=int, default=1)
    parser.add_argument("--split-name", default="")
    parser.add_argument("--seed", type=int, default=165)
    parser.add_argument("--use-itn", action="store_true")
    parser.add_argument("--hub", default="hf")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--disable-cudnn", action="store_true")
    parser.add_argument("--label-mode", choices=("heuristic", "none"), default="heuristic")
    parser.add_argument(
        "--metric-normalization",
        choices=("none", "zh_asr"),
        default="zh_asr",
    )
    parser.add_argument("--wer-tokenizer", choices=WER_TOKENIZERS, default="jieba")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--metrics", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root_from_script()
    run_dir = args.output_dir or root / "70_experiments" / "runs" / args.run_id
    predictions_path = (
        args.predictions
        or run_dir / "predictions" / f"{args.run_id}_predictions.jsonl"
    )
    summary_path = args.summary or run_dir / "artifacts" / f"{args.run_id}_summary.json"
    metrics_path = args.metrics or run_dir / "metrics.csv"

    import torch
    import funasr
    import modelscope
    from funasr import AutoModel
    from funasr.utils.postprocess_utils import rich_transcription_postprocess

    torch.manual_seed(args.seed)
    if args.disable_cudnn:
        torch.backends.cudnn.enabled = False
    if args.runtime == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA runtime requested but torch.cuda.is_available() is false")
    device = "cuda:0" if args.runtime == "cuda" else "cpu"

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

    started = time.time()
    try:
        model = AutoModel(
            model=args.model_name,
            device=device,
            hub=args.hub,
            disable_update=True,
        )
    except TypeError:
        model = AutoModel(model=args.model_name, device=device, hub=args.hub)
    model_load_elapsed = round(time.time() - started, 2)

    prediction_rows: list[dict[str, Any]] = []
    locale_violation_rows = 0
    simplified_chars = 0
    generated_chars = 0
    for index, row in enumerate(selected_rows, start=1):
        row_started = time.time()
        audio_id = row_audio_id(row)
        gold = gold_by_id.get(audio_id, {})
        reference = reference_text_for(row, gold)
        reference_label, reference_label_method = reference_label_for(reference, gold)
        audio_path = resolve_audio_path(row, args.manifest, root)
        result = model.generate(
            input=str(audio_path),
            cache={},
            language=args.language,
            use_itn=args.use_itn,
            batch_size=args.batch_size,
        )
        raw_text = ""
        if result:
            first = result[0]
            raw_text = first.get("text", "") if isinstance(first, dict) else str(first)
        prediction = rich_transcription_postprocess(raw_text)
        text_metrics = compute_pair_metrics(
            reference,
            prediction,
            normalization=args.metric_normalization,
            wer_tokenizer=args.wer_tokenizer,
        )
        asr_label, asr_label_reason = (
            heuristic_asr_label(prediction)
            if args.label_mode == "heuristic"
            else ("", "disabled")
        )
        simplified_in_row = simplified_char_count(prediction)
        simplified_chars += simplified_in_row
        generated_chars += len(prediction)
        if simplified_in_row:
            locale_violation_rows += 1
        prediction_row = {
            "audio_id": audio_id,
            "split": row.get("split", ""),
            "audio_filepath": str(audio_path),
            "reference_text": reference,
            "reference_label": reference_label,
            "reference_label_method": reference_label_method,
            "risk_atoms": gold.get("risk_atoms", ""),
            "hypothesis_text": prediction,
            "pred_text": prediction,
            "wer": text_metrics["wer"],
            "cer": text_metrics["cer"],
            "metric_normalization": args.metric_normalization,
            "wer_tokenizer": args.wer_tokenizer,
            "cer_raw": text_metrics["cer_raw"],
            "wer_raw_whitespace": text_metrics["wer_raw_whitespace"],
            "asr_label": asr_label,
            "asr_label_method": f"{args.label_mode}_v0",
            "asr_label_reason": asr_label_reason,
            "model": args.model_name,
            "asr_run_id": args.run_id,
            "runtime": args.runtime,
            "toolkit": "funasr",
            "row_wall_time_seconds": round(time.time() - row_started, 2),
            "run_date": date.today().isoformat(),
        }
        prediction_rows.append(prediction_row)
        print(
            json.dumps(
                {
                    "index": index,
                    "rows": len(selected_rows),
                    "pred_len": len(prediction),
                    "asr_label": asr_label,
                    "cer": text_metrics["cer"],
                    "wer": text_metrics["wer"],
                    "simplified_chars": simplified_in_row,
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    elapsed = round(time.time() - started, 2)
    rows = len(prediction_rows)
    cer_mean = round(sum(float(row["cer"]) for row in prediction_rows) / max(rows, 1), 2)
    wer_mean = round(sum(float(row["wer"]) for row in prediction_rows) / max(rows, 1), 2)
    write_jsonl(predictions_path, prediction_rows)
    summary = {
        "ok": rows == len(selected_rows),
        "run_id": args.run_id,
        "model": args.model_name,
        "runtime": args.runtime,
        "device": device,
        "manifest": str(args.manifest),
        "gold_review": str(args.gold_review),
        "predictions": str(predictions_path),
        "rows": rows,
        "split_name": split_name,
        "cer_mean": cer_mean,
        "wer_mean": wer_mean,
        "metric_normalization": args.metric_normalization,
        "wer_tokenizer": args.wer_tokenizer,
        "label_mode": args.label_mode,
        "language": args.language,
        "use_itn": args.use_itn,
        "hub": args.hub,
        "batch_size": args.batch_size,
        "disable_cudnn": args.disable_cudnn,
        "toolkit_versions": {
            "funasr": getattr(funasr, "__version__", "unknown"),
            "modelscope": getattr(modelscope, "__version__", "unknown"),
            "torch": torch.__version__,
        },
        "model_load_time_seconds": model_load_elapsed,
        "wall_time_seconds": elapsed,
        "seconds_per_row": round(elapsed / rows, 4) if rows else 0.0,
        "rows_per_second": round(rows / elapsed, 4) if elapsed else 0.0,
        "simplified_char_count": simplified_chars,
        "simplified_char_rate": round(simplified_chars / generated_chars, 4)
        if generated_chars
        else 0.0,
        "locale_violation_rows": locale_violation_rows,
        "raw_artifact_policy": "predictions/artifacts/logs ignored; tracked records are aggregate-only",
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_metrics(
        metrics_path,
        {
            "step": 0,
            "epoch": 0,
            "split": f"{split_name}_{rows}",
            "loss": "",
            "cer": cer_mean,
            "wer": wer_mean,
            "learning_rate": "",
            "wall_time_seconds": elapsed,
            "checkpoint": args.model_name,
            "notes": (
                f"pilot_inference;runtime={args.runtime};max_samples={rows};"
                f"label_mode={args.label_mode};language={args.language};"
                f"use_itn={args.use_itn};disable_cudnn={args.disable_cudnn};"
                f"metric_normalization={args.metric_normalization};"
                f"wer_tokenizer={args.wer_tokenizer};"
                f"locale_violation_rows={locale_violation_rows}"
            ),
        },
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

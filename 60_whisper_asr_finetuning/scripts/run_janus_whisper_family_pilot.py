#!/usr/bin/env python3
"""Run a JANUS 15-row pilot inference pass for Whisper-family ASR models."""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
from datetime import date
from pathlib import Path
from typing import Any

from asr_text_metrics import WER_TOKENIZERS, compute_pair_metrics


LABEL_ORDER = {
    "no_escalation": 0,
    "review": 1,
    "priority_review": 2,
    "critical_escalation": 3,
}


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def row_audio_id(row: dict[str, Any]) -> str:
    for field in ("audio_id", "id", "sample_id"):
        raw_value = row.get(field)
        value = "" if raw_value is None else str(raw_value).strip()
        if value:
            return value
    return ""


def resolve_audio_path(row: dict[str, Any], manifest_path: Path, root: Path) -> Path:
    value = (
        row.get("audio_filepath")
        or row.get("audio")
        or row.get("file_name")
        or ""
    )
    raw_path = Path(str(value))
    if raw_path.is_absolute():
        return raw_path

    split = str(row.get("split", "")).strip()
    candidates = [
        manifest_path.parent / raw_path,
        root / raw_path,
    ]
    if split:
        candidates.append(
            root
            / "40_breeze_asr25_finetune_dataset"
            / "hf_audiofolder"
            / split
            / raw_path
        )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def gold_by_audio_id(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {
        row_audio_id(row): row
        for row in rows
        if row_audio_id(row)
    }


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


def load_audio(path: Path, sampling_rate: int) -> Any:
    import librosa
    import soundfile as sf

    audio, source_rate = sf.read(path)
    if getattr(audio, "ndim", 1) > 1:
        audio = audio.mean(axis=1)
    if source_rate != sampling_rate:
        audio = librosa.resample(audio, orig_sr=source_rate, target_sr=sampling_rate)
    return audio


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", "", text.lower())


def has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def heuristic_asr_label(text: str) -> tuple[str, str]:
    """Small pilot-only label heuristic for metric plumbing.

    This is intentionally conservative and auditable. It is not a downstream
    production classifier; it only gives the CDS-ASR pilot a first ASR-side
    label so SRES/CEIS/downstream scripts can run before a learned router exists.
    """

    compact = normalize_text(text)
    if not compact:
        return "no_escalation", "empty_hypothesis"

    negated_money = has_any(
        compact,
        (
            "還沒被騙錢",
            "沒有被騙錢",
            "沒被騙錢",
            "尚未匯款",
            "還沒匯款",
            "沒有匯款",
            "沒匯款",
            "未匯款",
        ),
    )
    completed_money = has_any(
        compact,
        (
            "已經匯",
            "已匯",
            "匯了",
            "匯到",
            "轉出",
            "轉給",
            "轉帳",
            "被騙錢",
            "詐騙轉出",
        ),
    )
    if completed_money and not negated_money:
        return "critical_escalation", "completed_money_or_transfer"

    if "匯款嗎" in compact and re.search(r"匯款嗎[？?]?(有|對|是)", compact):
        return "critical_escalation", "affirmed_payment_question"

    priority_terms = (
        "詐騙",
        "被盜",
        "警察",
        "派出所",
        "報案",
        "身分證",
        "健保卡",
        "個資",
        "第三方支付",
        "虛擬貨幣",
        "line",
        "帳戶",
        "銀行",
        "郵局",
        "客服",
        "地政",
        "戶政",
    )
    if has_any(compact, priority_terms):
        return "priority_review", "fraud_or_sensitive_context"

    review_terms = ("詢問", "確認", "客服", "案號", "帳戶", "銀行", "郵局")
    if has_any(compact, review_terms):
        return "review", "administrative_or_uncertain_context"

    return "no_escalation", "no_risk_terms_detected"


def reference_text_for(row: dict[str, Any], gold: dict[str, str]) -> str:
    for value in (
        gold.get("human_verified_transcript"),
        row.get("reference_text"),
        row.get("text"),
        row.get("sentence"),
    ):
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def reference_label_for(reference: str, gold: dict[str, str]) -> tuple[str, str]:
    explicit = (gold.get("semantic_risk_label") or "").strip()
    if explicit:
        return explicit, "gold_review"
    label, _reason = heuristic_asr_label(reference)
    return label, "heuristic_v0"


def forced_decoder_ids_for(processor: Any, language: str, task: str) -> Any:
    if hasattr(processor, "get_decoder_prompt_ids"):
        return processor.get_decoder_prompt_ids(language=language, task=task)
    tokenizer = getattr(processor, "tokenizer", None)
    if tokenizer is not None and hasattr(tokenizer, "get_decoder_prompt_ids"):
        return tokenizer.get_decoder_prompt_ids(language=language, task=task)
    return None


def resolve_torch_dtype(torch_module: Any, runtime: str, dtype_name: str) -> Any:
    if dtype_name == "auto":
        return torch_module.float16 if runtime == "cuda" else torch_module.float32
    return {
        "float32": torch_module.float32,
        "float16": torch_module.float16,
        "bfloat16": torch_module.bfloat16,
    }[dtype_name]


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
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--manifest", type=Path, default=default_manifest)
    parser.add_argument("--gold-review", type=Path, default=default_gold)
    parser.add_argument("--runtime", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--language", default="zh")
    parser.add_argument("--task", default="transcribe")
    parser.add_argument("--sampling-rate", type=int, default=16000)
    parser.add_argument("--max-samples", type=int, default=15)
    parser.add_argument("--split-name", default="")
    parser.add_argument("--max-new-tokens", type=int, default=225)
    parser.add_argument("--seed", type=int, default=165)
    parser.add_argument(
        "--torch-dtype",
        choices=("auto", "float32", "float16", "bfloat16"),
        default="auto",
        help="Model/input dtype. `auto` uses float16 on CUDA and float32 on CPU.",
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
        choices=WER_TOKENIZERS,
        default="jieba",
        help="Tokenization used for reported WER. Use whitespace only for legacy audits.",
    )
    parser.add_argument(
        "--disable-cudnn",
        action="store_true",
        help="Use CUDA while bypassing cuDNN kernels; useful for local cuDNN sublibrary mismatches.",
    )
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--metrics", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root_from_script()
    run_dir = args.output_dir or root / "70_experiments" / "runs" / args.run_id
    predictions_path = args.predictions or run_dir / "predictions" / f"{args.run_id}_predictions.jsonl"
    summary_path = args.summary or run_dir / "artifacts" / f"{args.run_id}_summary.json"
    metrics_path = args.metrics or run_dir / "metrics.csv"

    import torch
    from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor

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

    started = time.time()
    processor = AutoProcessor.from_pretrained(args.model_name, language=args.language, task=args.task)
    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        args.model_name,
        torch_dtype=model_dtype,
        low_cpu_mem_usage=True,
    ).to(device)
    model.eval()
    forced_decoder_ids = forced_decoder_ids_for(processor, args.language, args.task)

    prediction_rows: list[dict[str, Any]] = []
    for index, row in enumerate(selected_rows, start=1):
        audio_id = row_audio_id(row)
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
            "wer": wer,
            "cer": cer,
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
            "run_date": date.today().isoformat(),
        }
        prediction_rows.append(prediction_row)
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
        "run_id": args.run_id,
        "model": args.model_name,
        "runtime": args.runtime,
        "manifest": str(args.manifest),
        "gold_review": str(args.gold_review),
        "predictions": str(predictions_path),
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
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_metrics(
        metrics_path,
        {
            "step": 0,
            "epoch": 0,
            "split": f"{split_name}_{len(prediction_rows)}",
            "loss": "",
            "cer": cer_mean,
            "wer": wer_mean,
            "learning_rate": "",
            "wall_time_seconds": elapsed,
            "checkpoint": args.model_name,
            "notes": f"pilot_inference;runtime={args.runtime};max_samples={len(prediction_rows)};label_mode={args.label_mode};disable_cudnn={args.disable_cudnn};torch_dtype={model_dtype_name};metric_normalization={args.metric_normalization};wer_tokenizer={args.wer_tokenizer}",
        },
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

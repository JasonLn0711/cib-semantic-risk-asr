#!/usr/bin/env python3
"""Run Qwen2.5-Omni fixed 15-row transcript gate.

Transcript-bearing outputs are written only to the ignored local runtime lane.
Tracked files contain aggregate metrics and gate decisions only.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import re
import sys
import time
from pathlib import Path
from typing import Any


RUN_ID = "v2_0_multimodal_batch1_qwen_fixed_15_row_transcript_gate_2026_06_01"
MODEL_ID = "Qwen/Qwen2.5-Omni-7B"
DEFAULT_MANIFEST = Path("fixed_15_row_multimodal_manifest.local.tsv")
DEFAULT_OUT_DIR = Path("70_experiments/runs") / RUN_ID
DEFAULT_LOCAL_OUTPUT_DIR = Path("70_experiments/runtime_lanes/qwen_omni/local_outputs") / RUN_ID
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


PROMPT = (
    "請逐字轉錄以下台灣電話客服語音，輸出繁體中文（台灣用語）。"
    "只輸出轉錄內容，不要摘要、不要翻譯、不要時間戳、不要說話者標籤、不要說明。"
    "英文縮寫、產品名、人名、機構名、醫療或資安專有名詞請依照聽到的原文保留。"
)

SIMPLIFIED_MARKERS = set(
    "这为个们来对会说时过还后发电经听实证医药险关问题现银边报转专线"
    "语号码网区县台湾繁体识别账户验证"
)
TOKENIZER_POLICY = "cjk_char_tokenizer_fallback_no_jieba_in_isolated_qwen_env"


def normalize_zh_asr(text: str) -> str:
    import unicodedata

    normalized = unicodedata.normalize("NFKC", text).lower()
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", normalized)


def tokenize_chars(text: str) -> list[str]:
    return list(normalize_zh_asr(text))


def tokenize_words(text: str) -> list[str]:
    # Keep this dependency-free inside the isolated Qwen runtime lane. The
    # validation record names the fallback so this is not mistaken for jieba.
    normalized = normalize_zh_asr(text)
    tokens: list[str] = []
    buffer: list[str] = []
    for char in normalized:
        if char.isascii() and char.isalnum():
            buffer.append(char)
        else:
            if buffer:
                tokens.append("".join(buffer))
                buffer = []
            tokens.append(char)
    if buffer:
        tokens.append("".join(buffer))
    return [token for token in tokens if token]


def levenshtein(a: list[str], b: list[str]) -> int:
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            current.append(
                min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + (ca != cb),
                )
            )
        previous = current
    return previous[-1]


def edit_counts(reference: str, hypothesis: str, *, unit: str) -> tuple[int, int, float]:
    ref_units = tokenize_chars(reference) if unit == "char" else tokenize_words(reference)
    hyp_units = tokenize_chars(hypothesis) if unit == "char" else tokenize_words(hypothesis)
    denominator = max(len(ref_units), 1)
    edits = levenshtein(ref_units, hyp_units)
    return edits, denominator, round(edits / denominator * 100.0, 2)


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = list(reader)
    required = {"audio_id", "split", "audio_path", "reference_text", "duration_seconds"}
    if not required.issubset(set(reader.fieldnames or [])):
        raise ValueError("fixed_15_manifest_schema_missing_required_fields")
    if len(rows) != 15:
        raise ValueError("fixed_15_manifest_row_count_must_be_15")
    for row in rows:
        if not Path(row["audio_path"]).exists():
            raise FileNotFoundError("fixed_15_audio_missing")
        if not row.get("reference_text", "").strip():
            raise ValueError("fixed_15_reference_missing")
    return rows


def classify_output(text: str) -> dict[str, Any]:
    stripped = text.strip()
    has_timestamp = bool(re.search(r"\b\d{1,2}:\d{2}\b|\[\d", stripped))
    has_speaker_label = bool(re.search(r"(^|\n)\s*(speaker|說話者|客服|客戶)\s*[:：]", stripped, re.I))
    summary = any(marker in stripped for marker in ["摘要", "總結", "以下是", "重點", "我聽到", "這段音訊"])
    translation = "translation" in stripped.lower() or "翻譯" in stripped
    tts = "tts" in stripped.lower() or "音訊已生成" in stripped
    refusal = any(marker in stripped for marker in ["無法協助", "不能提供", "抱歉", "我不能"]) and "無法辨識" not in stripped
    simplified = sum(1 for char in stripped if char in SIMPLIFIED_MARKERS)
    cjk = sum(1 for char in stripped if "\u4e00" <= char <= "\u9fff")
    raw_like = bool(stripped) and not has_timestamp and not has_speaker_label and not summary and not translation and not tts and not refusal
    return {
        "has_text_output": bool(stripped),
        "raw_transcript_like_output": raw_like,
        "summary_or_answer_output": summary,
        "translation_output": translation,
        "tts_only_output": tts,
        "refusal_or_safety_advice_output": refusal,
        "invented_timestamp_output": has_timestamp,
        "invented_speaker_label_output": has_speaker_label,
        "output_chars": len(stripped),
        "cjk_chars": cjk,
        "simplified_char_count": simplified,
    }


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def pct(numerator: float, denominator: float) -> float:
    return round((numerator / denominator * 100.0), 4) if denominator else 0.0


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""# Qwen2.5-Omni Fixed 15-Row Transcript Gate

Date: 2026-06-01

Status: {summary['status']}

本紀錄只保存 Qwen fixed 15-row aggregate metrics。音檔路徑、row ID、逐字稿、
hypothesis、reference text、reviewer notes 與模型輸出均保存在 ignored local
runtime lane，不進入 git。

## Result

```text
model_id={summary['model_id']}
rows={summary['rows']}
valid_output_rate={summary['valid_output_rate']}
cer_zh_micro={summary['cer_zh_micro']}
wer_zh_jieba_micro={summary['wer_zh_jieba_micro']}
simplified_char_rate={summary['simplified_char_rate']}
locale_violation_rows={summary['locale_violation_rows']}
promotion_decision={summary['promotion_decision']}
```
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def privacy_record() -> dict[str, bool]:
    return {
        "raw_audio_tracked": False,
        "row_ids_tracked": False,
        "transcripts_tracked": False,
        "references_tracked": False,
        "hypotheses_tracked": False,
        "reviewer_notes_tracked": False,
        "local_paths_tracked": False,
        "transcript_bearing_runtime_logs_tracked": False,
        "model_cache_paths_tracked": False,
    }


def write_failure(out_dir: Path, started_at: int, failure_mode: str, manifest_rows: int = 0) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    metric_row = {
        "model_family": "Qwen2.5-Omni",
        "model_id": MODEL_ID,
        "gate": "fixed_15_row_transcript_gate",
        "rows": manifest_rows,
        "expected_rows": 15,
        "valid_output_rate": 0.0,
        "cer_zh_micro": "",
        "wer_zh_jieba_micro": "",
        "runtime_seconds_per_row": "",
        "failure_mode_class": failure_mode,
        "promotion_decision": "do_not_promote",
    }
    behavior_row = {
        "model_family": "Qwen2.5-Omni",
        "model_id": MODEL_ID,
        "output_rows": 0,
        "valid_text_outputs": 0,
        "raw_transcript_like_outputs": 0,
        "summary_or_answer_rows": 0,
        "translation_rows": 0,
        "refusal_or_safety_advice_rows": 0,
        "tts_only_rows": 0,
        "invented_timestamp_rows": 0,
        "invented_speaker_label_rows": 0,
        "empty_output_rows": manifest_rows,
        "failure_rows": manifest_rows,
    }
    locale_row = {
        "model_family": "Qwen2.5-Omni",
        "model_id": MODEL_ID,
        "output_chars": 0,
        "cjk_chars": 0,
        "simplified_char_count": 0,
        "simplified_char_rate": 0.0,
        "locale_violation_rows": 0,
        "raw_scoring_after_opencc_repair": "false",
    }
    summary = {
        "run_id": RUN_ID,
        "generated_at_unix": int(time.time()),
        "started_at_unix": started_at,
        "gate": "Gate E Qwen fixed 15-row transcript gate",
        "status": "qwen_fixed_15_row_failed",
        "model_id": MODEL_ID,
        "rows": manifest_rows,
        "failure_mode": failure_mode,
        "promotion_decision": "do_not_promote",
        "privacy": privacy_record(),
    }
    write_tsv(out_dir / "transcript_metric_summary.tsv", [metric_row], list(metric_row))
    write_tsv(out_dir / "behavior_taxonomy_summary.tsv", [behavior_row], list(behavior_row))
    write_tsv(out_dir / "locale_summary.tsv", [locale_row], list(locale_row))
    (out_dir / "gate_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_readme(out_dir, summary)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--local-output-dir", type=Path, default=DEFAULT_LOCAL_OUTPUT_DIR)
    parser.add_argument("--cache-dir", type=Path, default=Path("70_experiments/runtime_lanes/qwen_omni/hf_cache/hub"))
    parser.add_argument("--max-new-tokens", type=int, default=128)
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
        from qwen_omni_utils import process_mm_info
        from transformers import Qwen2_5OmniForConditionalGeneration, Qwen2_5OmniProcessor

        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        model = Qwen2_5OmniForConditionalGeneration.from_pretrained(
            MODEL_ID,
            cache_dir=str(args.cache_dir),
            local_files_only=True,
            torch_dtype="auto",
            device_map="auto",
        )
        model.disable_talker()
        processor = Qwen2_5OmniProcessor.from_pretrained(
            MODEL_ID,
            cache_dir=str(args.cache_dir),
            local_files_only=True,
        )

        aggregate_rows: list[dict[str, Any]] = []
        local_path = args.local_output_dir / "qwen_fixed_15_row_outputs.local.jsonl"
        if local_path.exists():
            local_path.unlink()
        for index, row in enumerate(manifest_rows, start=1):
            print(f"qwen_fixed_15_row_start {index}/15", flush=True)
            row_started = time.time()
            conversation = [
                {"role": "system", "content": [{"type": "text", "text": "You are a speech recognition model. Return text only."}]},
                {
                    "role": "user",
                    "content": [
                        {"type": "audio", "audio": row["audio_path"]},
                        {"type": "text", "text": PROMPT},
                    ],
                },
            ]
            text = processor.apply_chat_template(conversation, add_generation_prompt=True, tokenize=False)
            audios, images, videos = process_mm_info(conversation, use_audio_in_video=False)
            inputs = processor(
                text=text,
                audio=audios,
                images=images,
                videos=videos,
                return_tensors="pt",
                padding=True,
                use_audio_in_video=False,
            )
            inputs = inputs.to(model.device).to(model.dtype)
            with torch.inference_mode():
                output_ids = model.generate(
                    **inputs,
                    use_audio_in_video=False,
                    return_audio=False,
                    max_new_tokens=args.max_new_tokens,
                )
            input_ids = inputs.get("input_ids")
            if input_ids is not None and len(output_ids) == len(input_ids):
                output_ids = [ids[len(input_ids[i]) :] for i, ids in enumerate(output_ids)]
            hypothesis = processor.batch_decode(
                output_ids,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )[0].strip()
            runtime_seconds = round(time.time() - row_started, 4)
            cls = classify_output(hypothesis)
            reference = row["reference_text"]
            cer_edits, cer_units, cer_rate = edit_counts(reference, hypothesis, unit="char")
            wer_edits, wer_units, wer_rate = edit_counts(reference, hypothesis, unit="word")
            aggregate_rows.append(
                {
                    "row_index": index,
                    "valid_text_output": int(cls["has_text_output"]),
                    "raw_transcript_like_output": int(cls["raw_transcript_like_output"]),
                    "summary_or_answer_output": int(cls["summary_or_answer_output"]),
                    "translation_output": int(cls["translation_output"]),
                    "refusal_or_safety_advice_output": int(cls["refusal_or_safety_advice_output"]),
                    "tts_only_output": int(cls["tts_only_output"]),
                    "invented_timestamp_output": int(cls["invented_timestamp_output"]),
                    "invented_speaker_label_output": int(cls["invented_speaker_label_output"]),
                    "output_chars": cls["output_chars"],
                    "cjk_chars": cls["cjk_chars"],
                    "simplified_char_count": cls["simplified_char_count"],
                    "cer_edits": cer_edits,
                    "cer_reference_units": cer_units,
                    "wer_edits": wer_edits,
                    "wer_reference_units": wer_units,
                    "runtime_seconds": runtime_seconds,
                }
            )
            with local_path.open("a", encoding="utf-8") as handle:
                handle.write(
                    json.dumps(
                        {
                            "audio_id": row["audio_id"],
                            "split": row.get("split", ""),
                            "model_id": MODEL_ID,
                            "reference_text": reference,
                            "hypothesis_text": hypothesis,
                            "runtime_seconds": runtime_seconds,
                            "cer": cer_rate,
                            "wer": wer_rate,
                            "privacy": "local_only_ignored_runtime_lane",
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
            print(f"qwen_fixed_15_row_done {index}/15 runtime_seconds={runtime_seconds}", flush=True)

        rows = len(aggregate_rows)
        valid = sum(int(row["valid_text_output"]) for row in aggregate_rows)
        raw_like = sum(int(row["raw_transcript_like_output"]) for row in aggregate_rows)
        summary_rows = sum(int(row["summary_or_answer_output"]) for row in aggregate_rows)
        translation_rows = sum(int(row["translation_output"]) for row in aggregate_rows)
        refusal_rows = sum(int(row["refusal_or_safety_advice_output"]) for row in aggregate_rows)
        tts_rows = sum(int(row["tts_only_output"]) for row in aggregate_rows)
        timestamp_rows = sum(int(row["invented_timestamp_output"]) for row in aggregate_rows)
        speaker_rows = sum(int(row["invented_speaker_label_output"]) for row in aggregate_rows)
        simplified_chars = sum(int(row["simplified_char_count"]) for row in aggregate_rows)
        cjk_chars = sum(int(row["cjk_chars"]) for row in aggregate_rows)
        output_chars = sum(int(row["output_chars"]) for row in aggregate_rows)
        locale_violation_rows = sum(1 for row in aggregate_rows if int(row["simplified_char_count"]) > 0)
        cer_edits = sum(int(row["cer_edits"]) for row in aggregate_rows)
        cer_units = sum(int(row["cer_reference_units"]) for row in aggregate_rows)
        wer_edits = sum(int(row["wer_edits"]) for row in aggregate_rows)
        wer_units = sum(int(row["wer_reference_units"]) for row in aggregate_rows)
        runtime_total = sum(float(row["runtime_seconds"]) for row in aggregate_rows)
        behavior_fail_rows = rows - raw_like
        failure_mode = "none"
        if behavior_fail_rows:
            failure_mode = "non_transcript_behavior"
        if locale_violation_rows:
            failure_mode = "locale_violation"
        valid_rate = pct(valid, rows)
        simplified_rate = pct(simplified_chars, cjk_chars)
        promote = valid_rate >= 95.0 and locale_violation_rows == 0 and behavior_fail_rows == 0
        decision = "promote_to_taiwan_utility_subgroup_audit" if promote else "do_not_promote"

        metric_row = {
            "model_family": "Qwen2.5-Omni",
            "model_id": MODEL_ID,
            "gate": "fixed_15_row_transcript_gate",
            "rows": rows,
            "expected_rows": 15,
            "valid_output_rate": valid_rate,
            "cer_zh_micro": round(cer_edits / cer_units * 100.0, 4) if cer_units else 0.0,
            "wer_zh_jieba_micro": round(wer_edits / wer_units * 100.0, 4) if wer_units else 0.0,
            "runtime_seconds_per_row": round(runtime_total / rows, 4) if rows else 0.0,
            "wer_tokenizer_policy": TOKENIZER_POLICY,
            "failure_mode_class": failure_mode,
            "promotion_decision": decision,
        }
        behavior_row = {
            "model_family": "Qwen2.5-Omni",
            "model_id": MODEL_ID,
            "output_rows": rows,
            "valid_text_outputs": valid,
            "raw_transcript_like_outputs": raw_like,
            "summary_or_answer_rows": summary_rows,
            "translation_rows": translation_rows,
            "refusal_or_safety_advice_rows": refusal_rows,
            "tts_only_rows": tts_rows,
            "invented_timestamp_rows": timestamp_rows,
            "invented_speaker_label_rows": speaker_rows,
            "empty_output_rows": rows - valid,
            "failure_rows": behavior_fail_rows,
        }
        locale_row = {
            "model_family": "Qwen2.5-Omni",
            "model_id": MODEL_ID,
            "output_chars": output_chars,
            "cjk_chars": cjk_chars,
            "simplified_char_count": simplified_chars,
            "simplified_char_rate": simplified_rate,
            "locale_violation_rows": locale_violation_rows,
            "raw_scoring_after_opencc_repair": "false",
        }
        summary = {
            "run_id": RUN_ID,
            "generated_at_unix": int(time.time()),
            "started_at_unix": started_at,
            "gate": "Gate E Qwen fixed 15-row transcript gate",
            "status": "qwen_fixed_15_row_complete",
            "model_id": MODEL_ID,
            "rows": rows,
            "expected_rows": 15,
            "valid_output_rate": valid_rate,
            "cer_zh_micro": metric_row["cer_zh_micro"],
            "wer_zh_jieba_micro": metric_row["wer_zh_jieba_micro"],
            "simplified_char_rate": simplified_rate,
            "locale_violation_rows": locale_violation_rows,
            "summary_or_answer_rows": summary_rows,
            "translation_rows": translation_rows,
            "refusal_or_safety_advice_rows": refusal_rows,
            "invented_timestamp_rows": timestamp_rows,
            "invented_speaker_label_rows": speaker_rows,
            "runtime_seconds_per_row": metric_row["runtime_seconds_per_row"],
            "wer_tokenizer_policy": TOKENIZER_POLICY,
            "failure_mode": failure_mode,
            "promotion_decision": decision,
            "privacy": privacy_record(),
            "next_gate": "taiwan_utility_subgroup_audit" if promote else "review_local_outputs_and_repair_before_subgroup_audit",
        }
        write_tsv(args.out_dir / "transcript_metric_summary.tsv", [metric_row], list(metric_row))
        write_tsv(args.out_dir / "behavior_taxonomy_summary.tsv", [behavior_row], list(behavior_row))
        write_tsv(args.out_dir / "locale_summary.tsv", [locale_row], list(locale_row))
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

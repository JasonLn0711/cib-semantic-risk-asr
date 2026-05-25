# Run Record: qwen3_asr_0_6b_15_row_candidate

Date: 2026-05-26

## Purpose

Promote `Qwen/Qwen3-ASR-0.6B` from the 1-row runtime smoke to the fixed 15-row
JANUS pilot gate through the official `qwen-asr` transformers backend.

## Command

```bash
/usr/bin/time -v .venv/bin/python 60_whisper_asr_finetuning/scripts/run_janus_qwen3_asr_pilot.py \
  --run-id qwen3_asr_0_6b_15_row_candidate \
  --model-name Qwen/Qwen3-ASR-0.6B \
  --runtime cuda \
  --max-samples 15 \
  --language Chinese \
  --torch-dtype bfloat16 \
  --disable-cudnn \
  --metric-normalization zh_asr \
  --wer-tokenizer jieba
```

The runner log, validation JSON, raw predictions, and `/usr/bin/time -v`
record are local-only under ignored `logs/`, `artifacts/`, and `predictions/`
directories.

## Result

| Field | Value |
| --- | --- |
| Status | completed with cuDNN disabled, locale gate failed |
| Rows | 15 |
| Runtime | CUDA, bfloat16, `qwen-asr 0.0.6`, `transformers 4.57.6` |
| Stored CER mean | 64.93 |
| Stored WER mean | 82.70 |
| Paper-primary `cer_zh_micro` | 64.16 |
| Supplemental `wer_zh_jieba_micro` | 81.07 |
| Cached runner wall time | 17.97s |
| Outer wall time | 21.57s |
| Model load time | 4.34s |
| Locale violation rows | 15 |
| Simplified character count | 260 |
| Validation | 15-row hypothesis contract passed |

## Decision

Qwen3-ASR-0.6B is runnable on this workstation only with cuDNN disabled, but it
failed the strict Taiwan Traditional Chinese locale gate on every pilot row.
Do not promote it to the 258-row test split, selected-300 high-stakes run, or
paper-facing pure-ASR baseline table unless an audited zh-TW output policy is
approved.

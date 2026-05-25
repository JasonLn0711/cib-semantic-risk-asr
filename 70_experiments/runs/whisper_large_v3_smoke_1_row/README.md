# Whisper Large-v3 1-Row Smoke

Date: 2026-05-25

## Purpose

Check whether `openai/whisper-large-v3` can load and emit a standard JANUS
pilot row on the local CUDA runtime before any fixed 15-row or full split run.
This is a cold-start smoke test, not a comparable model-ranking result.

## Command

```bash
.venv/bin/python 60_whisper_asr_finetuning/scripts/run_janus_whisper_family_pilot.py \
  --run-id whisper_large_v3_smoke_1_row \
  --model-name openai/whisper-large-v3 \
  --runtime cuda \
  --disable-cudnn \
  --max-samples 1 \
  --torch-dtype auto \
  --metric-normalization zh_asr \
  --wer-tokenizer jieba
```

## Result

| Field | Value |
| --- | --- |
| Status | passed |
| Rows | 1 |
| Runtime | CUDA |
| GPU | NVIDIA GeForce RTX 5080 |
| Torch dtype | float16 |
| cuDNN | disabled |
| Metric normalization | `zh_asr` |
| WER tokenizer | `jieba` |
| CER mean | 40.00 |
| WER mean | 47.92 |
| Wall time seconds | 271.91 |
| Seconds per row | 271.91 |
| Rows per second | 0.0037 |
| Locale violation rows | 0 |
| Simplified character count | 0 |
| Contract validation | passed as a one-row field-contract smoke |

The ignored local validation and proxy-summary artifacts confirmed one row, no
missing required text/label/quality fields, no duplicate row keys, and zero
Traditional Chinese locale violations. The ignored local outputs remain under
`predictions/` and `artifacts/`.

## Decision

Promote this candidate to the fixed 15-row gate only if we still need a newer
Whisper-family comparator after the selected-300 human risk/decision/model
review gate. Do not use this single-row smoke result in paper comparison
tables.

# Whisper Large-v3 Turbo 1-Row Smoke

Date: 2026-05-25

## Purpose

Check whether `openai/whisper-large-v3-turbo` can load and emit a standard
JANUS pilot row on the local CUDA runtime before any fixed 15-row or full split
run. This is a cold-start smoke test, not a comparable model-ranking result.

## Command

```bash
.venv/bin/python 60_whisper_asr_finetuning/scripts/run_janus_whisper_family_pilot.py \
  --run-id whisper_large_v3_turbo_smoke_1_row \
  --model-name openai/whisper-large-v3-turbo \
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
| CER mean | 77.65 |
| WER mean | 85.42 |
| Wall time seconds | 144.77 |
| Seconds per row | 144.77 |
| Rows per second | 0.0069 |
| Locale violation rows | 0 |
| Simplified character count | 0 |
| Contract validation | passed as a one-row field-contract smoke |

The ignored local validation and proxy-summary artifacts confirmed one row, no
missing required text/label/quality fields, no duplicate row keys, and zero
Traditional Chinese locale violations. The ignored local outputs remain under
`predictions/` and `artifacts/`.

## Decision

Promote this candidate to the fixed 15-row gate only as a speed/quality
tradeoff comparator. The single smoke row had weaker surface metrics than
Whisper large-v3 and must not be used for ranking.

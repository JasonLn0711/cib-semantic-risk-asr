# Run Record: qwen3_asr_0_6b_smoke_1_row

Date: 2026-05-25

## Purpose

Run the first Qwen3-ASR 0.6B JANUS smoke test through the official
`qwen-asr` transformers backend.

## Command

```bash
.venv/bin/python 60_whisper_asr_finetuning/scripts/run_janus_qwen3_asr_pilot.py \
  --run-id qwen3_asr_0_6b_smoke_1_row \
  --model-name Qwen/Qwen3-ASR-0.6B \
  --runtime cuda \
  --max-samples 1 \
  --language Chinese \
  --torch-dtype bfloat16 \
  --disable-cudnn \
  --metric-normalization zh_asr \
  --wer-tokenizer jieba
```

The initial failed probe, successful runner log, and `/usr/bin/time -v` records
are local-only under `logs/`.

## Result

| Field | Value |
| --- | --- |
| Status | completed with cuDNN disabled, locale gate failed |
| Rows | 1 |
| Runtime | CUDA, bfloat16, `qwen-asr 0.0.6`, `transformers 4.57.6` |
| Stored CER mean | 74.12 |
| Stored WER mean | 95.83 |
| Paper-primary `cer_zh_micro` | 74.12 |
| Supplemental `wer_zh_jieba_micro` | 95.83 |
| Cached runner wall time | 6.45s |
| Outer wall time | 10.06s |
| Model load time | 4.48s |
| Locale violation rows | 1 |
| Simplified character count | 13 |
| Validation | 1-row hypothesis contract passed |

## Failure Record

The first CUDA attempt failed with
`CUDNN_STATUS_SUBLIBRARY_VERSION_MISMATCH`. The successful run explicitly set
`torch.backends.cudnn.enabled = False`, matching the existing local Whisper
workaround.

## Decision

Do not promote to 15-row until the Taiwan Traditional Chinese locale gate is
fixed or an audited conversion policy is approved. The 0.6B model is runnable
on this machine only with cuDNN disabled.

# Run Record: whisper_large_v3_turbo_15_row_baseline

Date: 2026-05-25

## Purpose

Promote `openai/whisper-large-v3-turbo` from the 1-row cold-start smoke to the
fixed 15-row JANUS pilot gate as a speed/quality tradeoff comparator.

## Command

```bash
.venv/bin/python 60_whisper_asr_finetuning/scripts/run_janus_whisper_family_pilot.py \
  --run-id whisper_large_v3_turbo_15_row_baseline \
  --model-name openai/whisper-large-v3-turbo \
  --runtime cuda \
  --disable-cudnn \
  --max-samples 15 \
  --torch-dtype auto \
  --metric-normalization zh_asr \
  --wer-tokenizer jieba
```

The `/usr/bin/time -v` record is local-only under `logs/run_2026_05_25.log`.

## Result

| Field | Value |
| --- | --- |
| Status | completed, locale gate not clean |
| Rows | 15 |
| Runtime | CUDA, float16, cuDNN disabled |
| Stored CER mean | 41.33 |
| Stored WER mean | 52.52 |
| Paper-primary `cer_zh_micro` | 40.36 |
| Supplemental `wer_zh_jieba_micro` | 50.87 |
| Runner wall time | 7.68s |
| Outer wall time | 10.33s |
| Locale violation rows | 4 |
| Simplified character count | 48 |
| Unsafe downrouting proxy count | 3 |
| High-risk missed proxy count | 1 |
| Validation | hypothesis contract passed |

## Decision

Keep this as a speed/quality smoke comparator only. It is faster than
large-v3 on the fixed pilot gate but worse on surface metrics and locale
violations, so it should not displace Breeze/partial-encoder evidence.

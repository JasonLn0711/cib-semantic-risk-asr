# Run Record: whisper_large_v3_15_row_baseline

Date: 2026-05-25

## Purpose

Promote `openai/whisper-large-v3` from the 1-row cold-start smoke to the fixed
15-row JANUS pilot gate before considering any 258-row comparator run.

## Command

```bash
.venv/bin/python 60_whisper_asr_finetuning/scripts/run_janus_whisper_family_pilot.py \
  --run-id whisper_large_v3_15_row_baseline \
  --model-name openai/whisper-large-v3 \
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
| Stored CER mean | 33.77 |
| Stored WER mean | 43.18 |
| Paper-primary `cer_zh_micro` | 33.33 |
| Supplemental `wer_zh_jieba_micro` | 42.04 |
| Runner wall time | 14.59s |
| Outer wall time | 17.26s |
| Locale violation rows | 2 |
| Simplified character count | 23 |
| Validation | hypothesis contract passed |

## Decision

Do not promote directly to 258-row under the strict Taiwan Traditional Chinese
rule. This model is useful as a strong Whisper-family comparator only if the
paper explicitly reports locale violations or a separate post-decode
Traditional Chinese conversion policy is approved and audited.

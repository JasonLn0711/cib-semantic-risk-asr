# Run Record: sensevoice_small_smoke_1_row

Date: 2026-05-25

## Purpose

Run the first FunASR SenseVoice JANUS smoke test with the same output contract
used by Whisper-family candidates.

## Command

```bash
.venv/bin/python 60_whisper_asr_finetuning/scripts/run_janus_sensevoice_pilot.py \
  --run-id sensevoice_small_smoke_1_row \
  --model-name FunAudioLLM/SenseVoiceSmall \
  --runtime cuda \
  --max-samples 1 \
  --language zh \
  --use-itn \
  --metric-normalization zh_asr \
  --wer-tokenizer jieba
```

The cold probe, formal runner log, and `/usr/bin/time -v` records are
local-only under `logs/`.

## Result

| Field | Value |
| --- | --- |
| Status | completed, locale gate failed |
| Rows | 1 |
| Runtime | CUDA, FunASR 1.3.3, ModelScope 1.37.1 |
| Stored CER mean | 65.88 |
| Stored WER mean | 81.25 |
| Paper-primary `cer_zh_micro` | 65.88 |
| Supplemental `wer_zh_jieba_micro` | 81.25 |
| Cached runner wall time | 2.15s |
| Outer wall time | 5.96s |
| Model load time | 1.68s |
| Locale violation rows | 1 |
| Simplified character count | 11 |
| Validation | 1-row hypothesis contract passed |

The first cold probe downloaded the model and took 84.41s outer wall time; the
cached formal runner took 5.96s outer wall time.

## Decision

Do not promote to the 15-row gate until a Taiwan Traditional Chinese output
policy is defined and audited for SenseVoice. The model is runnable and fast,
but the strict locale gate failed on the first row.

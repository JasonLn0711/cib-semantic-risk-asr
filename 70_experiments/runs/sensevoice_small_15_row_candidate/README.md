# Run Record: sensevoice_small_15_row_candidate

Date: 2026-05-26

## Purpose

Promote `FunAudioLLM/SenseVoiceSmall` from the 1-row runtime smoke to the fixed
15-row JANUS pilot gate, using the same hypothesis contract and zh-TW locale
gate as the Whisper/Breeze candidates.

## Command

```bash
/usr/bin/time -v .venv/bin/python 60_whisper_asr_finetuning/scripts/run_janus_sensevoice_pilot.py \
  --run-id sensevoice_small_15_row_candidate \
  --model-name FunAudioLLM/SenseVoiceSmall \
  --runtime cuda \
  --max-samples 15 \
  --language zh \
  --use-itn \
  --metric-normalization zh_asr \
  --wer-tokenizer jieba
```

The runner log, validation JSON, raw predictions, and `/usr/bin/time -v`
record are local-only under ignored `logs/`, `artifacts/`, and `predictions/`
directories.

## Result

| Field | Value |
| --- | --- |
| Status | completed, locale gate failed |
| Rows | 15 |
| Runtime | CUDA, FunASR 1.3.3, ModelScope 1.37.1 |
| Stored CER mean | 63.83 |
| Stored WER mean | 79.97 |
| Paper-primary `cer_zh_micro` | 63.12 |
| Supplemental `wer_zh_jieba_micro` | 78.98 |
| Cached runner wall time | 2.60s |
| Outer wall time | 6.32s |
| Model load time | 1.66s |
| Locale violation rows | 14 |
| Simplified character count | 209 |
| Validation | 15-row hypothesis contract passed |

## Decision

SenseVoice is runnable and fast, but the strict Taiwan Traditional Chinese
locale gate failed on almost every pilot row. Do not promote it to the 258-row
test split, selected-300 high-stakes run, or paper-facing pure-ASR baseline
table unless an audited zh-TW output policy is approved.

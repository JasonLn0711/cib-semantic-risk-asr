# Run Record: whisper_large_v2_test_split

## Summary

- Status: completed
- Date: 2026-05-25
- Owner: Jason Lin
- Dataset: `janus_165_v1_test`
- Model: `openai/whisper-large-v2`
- Runner: `60_whisper_asr_finetuning/scripts/run_janus_whisper_family_pilot.py`
- Hardware: local RTX 5080 CUDA with cuDNN disabled

## Purpose

Run the already validated Whisper large-v2 baseline on the canonical `258`-row
JANUS test split so the paper-facing table includes a strong Whisper-family
comparator before moving to Whisper large-v3 and large-v3 turbo.

## Command

```bash
.venv/bin/python 60_whisper_asr_finetuning/scripts/run_janus_whisper_family_pilot.py \
  --run-id whisper_large_v2_test_split \
  --model-name openai/whisper-large-v2 \
  --manifest 40_breeze_asr25_finetune_dataset/manifests/test.jsonl \
  --gold-review 40_breeze_asr25_finetune_dataset/reports/gold_subset_review.tsv \
  --runtime cuda \
  --disable-cudnn \
  --torch-dtype float16 \
  --max-samples 0 \
  --split-name test \
  --metric-normalization zh_asr \
  --wer-tokenizer jieba
```

Validation:

```bash
.venv/bin/python 80_semantic_risk_asr/scoring/validate_janus_asr_hypotheses.py \
  --expected-manifest 40_breeze_asr25_finetune_dataset/manifests/test.jsonl \
  --expected-rows 258 \
  --hypotheses 70_experiments/runs/whisper_large_v2_test_split/predictions/whisper_large_v2_test_split_predictions.jsonl \
  --require-labels \
  --require-quality-signal
```

## Results

| Metric | Value |
| --- | ---: |
| Rows | 258 |
| Stored CER mean | 24.92 |
| Stored WER mean | 32.75 |
| Paper-facing `cer_zh_micro` | 24.72 |
| Supplemental `wer_zh_jieba_micro` | 32.23 |
| Wall time seconds | 523.49 |
| Seconds per row | 2.029 |
| Rows per second | 0.493 |
| Unsafe downrouting count | 33 |
| High-risk missed count | 28 |
| Risk-atom proxy error rate | 0.1276 |
| Simplified char count | 12 |
| Locale violation rows | 1 |

Validation passed: `258/258` expected IDs observed, no duplicate IDs, no missing
hypothesis text, no missing labels, and no missing quality signals.

## Interpretation

Whisper large-v2 is much stronger than Whisper small, but it does not beat
Breeze-ASR-25 base on `cer_zh_micro` or proxy safety counts in this split. It
remains useful as the current strongest Whisper-family comparator until
Whisper large-v3 and large-v3 turbo pass their gates.

## Artifacts

- Metrics: `metrics.csv`
- Raw predictions: `predictions/` (ignored local)
- Validation JSON and summary: `artifacts/` (ignored local)

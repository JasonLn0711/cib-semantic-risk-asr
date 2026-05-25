# Breeze-ASR-26 258-Row Test Split Comparator

Status: completed

Date: 2026-05-25

## Purpose

Run `MediaTek-Research/Breeze-ASR-26` on the canonical JANUS `258`-row test
split as an optional Taiwanese Hokkien / dialect-aware stress comparator. This
is not promoted as the main Taiwan Mandarin ASR candidate; it is a family
contrast against the Breeze-ASR-25 legacy best models and Whisper-family
baselines.

Raw predictions, summary JSON, and validation JSON remain in ignored local
`predictions/` and `artifacts/` folders. This tracked record keeps only
aggregate metrics and commands.

## Command

```bash
.venv/bin/python 60_whisper_asr_finetuning/scripts/run_janus_whisper_family_pilot.py \
  --run-id breeze_asr26_test_split \
  --model-name MediaTek-Research/Breeze-ASR-26 \
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
  --hypotheses 70_experiments/runs/breeze_asr26_test_split/predictions/breeze_asr26_test_split_predictions.jsonl \
  --require-labels \
  --require-quality-signal \
  --output-json 70_experiments/runs/breeze_asr26_test_split/artifacts/breeze_asr26_test_split_validation.json
```

## Result

| Metric | Value |
| --- | ---: |
| Rows | 258 |
| Stored CER mean | 24.87 |
| Stored WER mean | 33.12 |
| Paper-facing `cer_zh_micro` | 24.27 |
| Supplemental `wer_zh_jieba_micro` | 32.29 |
| Raw whitespace WER micro | 1054.79 |
| Wall time seconds | 187.25 |
| Seconds per row | 0.726 |
| Rows per second | 1.378 |
| Unsafe downrouting | 27 |
| High-risk missed | 22 |
| Risk-atom proxy error rate | 0.1034 |
| Locale violation rows | 0 |

Validation passed with `258/258` expected IDs observed, no extra IDs, no
missing reference rows, no missing hypothesis rows, no missing labels, and no
missing quality signals.

## WER Interpretation

This run is a useful stress case for the WER audit. The same predictions have
`wer_zh_jieba_micro=32.29`, but raw whitespace WER micro is `1054.79`. The
large raw whitespace value is a tokenizer-denominator artifact for unsegmented
Chinese text and must not be used as a model quality claim.

Paper-facing tables should use `cer_zh_micro` as the primary ASR surface metric
and `wer_zh_jieba_micro` only as a supplemental segmented word metric.

## Decision

Do not promote Breeze-ASR-26 over the legacy partial encoder. It is comparable
to Whisper large-v2 on `zh_asr` surface metrics and better on several proxy
safety counts, but it remains behind the partial encoder and Breeze-ASR-25 base
on `cer_zh_micro`.

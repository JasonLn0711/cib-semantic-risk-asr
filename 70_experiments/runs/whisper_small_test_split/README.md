# Run Record: whisper_small_test_split

## Summary

- Status: completed
- Date: 2026-05-25
- Owner: Jason Lin
- Dataset: `janus_165_v1_test`
- Model: `openai/whisper-small`
- Runner: `60_whisper_asr_finetuning/scripts/run_janus_whisper_family_pilot.py`
- Hardware: local RTX 5080 CUDA with cuDNN disabled

## Purpose

Run the already validated Whisper small baseline on the canonical `258`-row
JANUS test split so it can be compared with Breeze-ASR-25 base, legacy LoRA,
and legacy partial encoder under the same `zh_asr` metric profile and proxy CDS
summary.

## Command

```bash
.venv/bin/python 60_whisper_asr_finetuning/scripts/run_janus_whisper_family_pilot.py \
  --run-id whisper_small_test_split \
  --model-name openai/whisper-small \
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
  --hypotheses 70_experiments/runs/whisper_small_test_split/predictions/whisper_small_test_split_predictions.jsonl \
  --require-labels \
  --require-quality-signal
```

## Results

| Metric | Value |
| --- | ---: |
| Rows | 258 |
| Stored CER mean | 36.11 |
| Stored WER mean | 45.13 |
| Paper-facing `cer_zh_micro` | 34.86 |
| Supplemental `wer_zh_jieba_micro` | 43.44 |
| Wall time seconds | 152.92 |
| Seconds per row | 0.593 |
| Rows per second | 1.687 |
| Unsafe downrouting count | 76 |
| High-risk missed count | 70 |
| Risk-atom proxy error rate | 0.2542 |
| Simplified char count | 37 |
| Locale violation rows | 4 |

Validation passed: `258/258` expected IDs observed, no duplicate IDs, no missing
hypothesis text, no missing labels, and no missing quality signals.

## Interpretation

Whisper small is fast in this local run, but it is not competitive on the
paper-facing ASR metric or the proxy safety metrics. It remains a weak baseline
and should not be promoted to the 300-row main experiment unless needed as a
low-cost contrast model.

## Artifacts

- Metrics: `metrics.csv`
- Raw predictions: `predictions/` (ignored local)
- Validation JSON and summary: `artifacts/` (ignored local)

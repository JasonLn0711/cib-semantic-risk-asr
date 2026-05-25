# Run Record: breeze_asr25_partial_encoder_high_stakes_300

## Summary

- Status: completed aggregate ASR pass
- Date: 2026-05-25
- Dataset: JANUS high-stakes 300-row expansion
- Model: legacy partial-encoder Breeze-ASR-25 checkpoint
- Runtime: CUDA, cuDNN disabled, `float16`
- Rows: `300/300`
- Wall time: `275.74` seconds

## Command

```bash
.venv/bin/python 60_whisper_asr_finetuning/scripts/run_legacy_breeze_asr25_smoke.py \
  --model-kind partial_encoder \
  --run-id breeze_asr25_partial_encoder_high_stakes_300 \
  --manifest 70_experiments/runs/janus_300_500_high_stakes_expansion/artifacts/high_stakes_300_manifest.jsonl \
  --gold-review 40_breeze_asr25_finetune_dataset/reports/gold_subset_review.tsv \
  --runtime cuda \
  --disable-cudnn \
  --torch-dtype float16 \
  --split-name high_stakes_300 \
  --max-samples 0 \
  --metric-normalization zh_asr \
  --wer-tokenizer jieba
```

## Validation

```bash
.venv/bin/python 80_semantic_risk_asr/scoring/validate_janus_asr_hypotheses.py \
  --expected-manifest 70_experiments/runs/janus_300_500_high_stakes_expansion/artifacts/high_stakes_300_manifest.jsonl \
  --expected-rows 300 \
  --hypotheses 70_experiments/runs/breeze_asr25_partial_encoder_high_stakes_300/predictions/breeze_asr25_partial_encoder_high_stakes_300_predictions.jsonl \
  --require-labels \
  --require-quality-signal \
  --output-json 70_experiments/runs/breeze_asr25_partial_encoder_high_stakes_300/artifacts/breeze_asr25_partial_encoder_high_stakes_300_validation.json
```

Result: passed. The file contained `300` observed rows, `300` expected IDs, no
missing or extra IDs, unique `audio_id` values, present hypothesis text, present
ASR labels, and quality fields `cer` and `wer`.

## Text Metric Audit

The paper-facing metric audit was run with:

```bash
.venv/bin/python 80_semantic_risk_asr/scoring/audit_asr_text_metrics.py \
  --expected-manifest 70_experiments/runs/janus_300_500_high_stakes_expansion/artifacts/high_stakes_300_manifest.jsonl \
  --expected-rows 300 \
  --hypotheses 70_experiments/runs/breeze_asr25_partial_encoder_high_stakes_300/predictions/breeze_asr25_partial_encoder_high_stakes_300_predictions.jsonl \
  --output-tsv 70_experiments/runs/breeze_asr25_partial_encoder_high_stakes_300/text_metric_audit.tsv \
  --summary-json 70_experiments/runs/breeze_asr25_partial_encoder_high_stakes_300/metric_audit_summary.json
```

| Metric | Value |
| --- | ---: |
| Stored row-mean CER | 7.03 |
| Stored row-mean WER | 9.55 |
| `cer_zh_micro` | 6.86 |
| `wer_zh_jieba_micro` | 9.38 |
| Raw whitespace WER micro | 93.16 |
| `jiwer` delta for zh-jieba WER | 0.0 |

## Notes

This run is a first high-stakes ASR pass, not the final paper comparison table.
The raw whitespace WER confirms the legacy metric remains invalid as a primary
Chinese ASR measure. Use `cer_zh_micro` as the primary surface metric,
`wer_zh_jieba_micro` as supplemental, and CDS-ASR decision metrics for the
safety argument.

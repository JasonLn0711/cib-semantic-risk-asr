# Run Record: breeze_asr25_base_high_stakes_300

## Summary

- Status: completed aggregate ASR pass
- Date: 2026-05-25
- Dataset: JANUS high-stakes 300-row expansion
- Model: `MediaTek-Research/Breeze-ASR-25`
- Runtime: CUDA, cuDNN disabled, `float16`
- Rows: `300/300`
- Wall time: `214.96` seconds

## Command

```bash
.venv/bin/python 60_whisper_asr_finetuning/scripts/run_janus_whisper_family_pilot.py \
  --run-id breeze_asr25_base_high_stakes_300 \
  --model-name MediaTek-Research/Breeze-ASR-25 \
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
  --hypotheses 70_experiments/runs/breeze_asr25_base_high_stakes_300/predictions/breeze_asr25_base_high_stakes_300_predictions.jsonl \
  --require-labels \
  --require-quality-signal \
  --output-json 70_experiments/runs/breeze_asr25_base_high_stakes_300/artifacts/breeze_asr25_base_high_stakes_300_validation.json
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
  --hypotheses 70_experiments/runs/breeze_asr25_base_high_stakes_300/predictions/breeze_asr25_base_high_stakes_300_predictions.jsonl \
  --output-tsv 70_experiments/runs/breeze_asr25_base_high_stakes_300/text_metric_audit.tsv \
  --summary-json 70_experiments/runs/breeze_asr25_base_high_stakes_300/metric_audit_summary.json
```

| Metric | Value |
| --- | ---: |
| Stored row-mean CER | 22.07 |
| Stored row-mean WER | 28.74 |
| `cer_zh_micro` | 21.44 |
| `wer_zh_jieba_micro` | 28.10 |
| Raw whitespace WER micro | 271.66 |
| `jiwer` delta for zh-jieba WER | 0.0 |

## Notes

This run is a high-stakes base-model comparator for the Breeze-family 300-row
pass. The large raw whitespace WER is expected for unsegmented Chinese and is
not a paper-facing metric. Use `cer_zh_micro` as the primary ASR surface metric,
`wer_zh_jieba_micro` as supplemental, and CDS-ASR decision metrics for the
safety argument.

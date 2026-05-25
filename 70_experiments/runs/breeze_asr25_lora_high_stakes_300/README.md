# Run Record: breeze_asr25_lora_high_stakes_300

## Summary

- Status: completed aggregate ASR pass
- Date: 2026-05-25
- Dataset: JANUS high-stakes 300-row expansion
- Model: `MediaTek-Research/Breeze-ASR-25` plus legacy LoRA rank32 adapter
- Runtime: CUDA, cuDNN disabled, `float16`
- Rows: `300/300`
- Wall time: `481.25` seconds

## Command

```bash
.venv/bin/python 60_whisper_asr_finetuning/scripts/run_legacy_breeze_asr25_smoke.py \
  --model-kind lora \
  --run-id breeze_asr25_lora_high_stakes_300 \
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
  --hypotheses 70_experiments/runs/breeze_asr25_lora_high_stakes_300/predictions/breeze_asr25_lora_high_stakes_300_predictions.jsonl \
  --require-labels \
  --require-quality-signal \
  --output-json 70_experiments/runs/breeze_asr25_lora_high_stakes_300/artifacts/breeze_asr25_lora_high_stakes_300_validation.json
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
  --hypotheses 70_experiments/runs/breeze_asr25_lora_high_stakes_300/predictions/breeze_asr25_lora_high_stakes_300_predictions.jsonl \
  --output-tsv 70_experiments/runs/breeze_asr25_lora_high_stakes_300/text_metric_audit.tsv \
  --summary-json 70_experiments/runs/breeze_asr25_lora_high_stakes_300/metric_audit_summary.json
```

| Metric | Value |
| --- | ---: |
| Stored row-mean CER | 16.15 |
| Stored row-mean WER | 22.15 |
| `cer_zh_micro` | 15.97 |
| `wer_zh_jieba_micro` | 21.91 |
| Raw whitespace WER micro | 101.30 |
| `jiwer` delta for zh-jieba WER | 0.0 |

## Notes

This run is a high-stakes LoRA comparator for the Breeze-family 300-row pass.
It improves over the base model on `cer_zh_micro` and `wer_zh_jieba_micro`, but
the earlier 15-row and 258-row gates showed that lower surface error alone is
not enough for the CDS-ASR safety claim. Raw predictions and runtime logs remain
local-only under ignored directories.

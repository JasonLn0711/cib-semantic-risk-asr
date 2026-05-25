# Breeze-ASR-25 Base 258-Row Test Split

## Purpose

Run the unfine-tuned `MediaTek-Research/Breeze-ASR-25` base model on the
canonical 258-row JANUS test split so the legacy partial-encoder and LoRA
results have a same-split base-model comparator.

## Command

```bash
.venv/bin/python 60_whisper_asr_finetuning/scripts/run_janus_whisper_family_pilot.py \
  --run-id breeze_asr25_base_test_split \
  --model-name MediaTek-Research/Breeze-ASR-25 \
  --manifest 40_breeze_asr25_finetune_dataset/manifests/test.jsonl \
  --gold-review 40_breeze_asr25_finetune_dataset/manifests/test_with_sources.tsv \
  --runtime cuda \
  --disable-cudnn \
  --torch-dtype float16 \
  --split-name test \
  --max-samples 258
```

This run predates the 2026-05-25 WER audit fix, so its stored `wer` field uses
legacy raw whitespace tokenization. Use
`70_experiments/runs/wer_metric_audit_2026_05_25/text_metric_audit.tsv` for
segmented Chinese WER and corpus-level micro rates.

## Validation

```bash
.venv/bin/python 80_semantic_risk_asr/scoring/validate_janus_asr_hypotheses.py \
  --gold-review 40_breeze_asr25_finetune_dataset/manifests/test_with_sources.tsv \
  --nemo-manifest 40_breeze_asr25_finetune_dataset/manifests/test.jsonl \
  --hypotheses 70_experiments/runs/breeze_asr25_base_test_split/predictions/breeze_asr25_base_test_split_predictions.jsonl \
  --expected-rows 258 \
  --require-labels \
  --require-quality-signal \
  --output-json 70_experiments/runs/breeze_asr25_base_test_split/artifacts/breeze_asr25_base_test_split_validation.json
```

Result: `ok=true`; `258/258` expected IDs observed; no duplicate IDs; no
missing hypothesis text; no missing labels; no missing quality signals.

## Results

| Metric | Value |
| --- | ---: |
| Rows | 258 |
| Stored CER mean | 33.11 |
| Stored legacy raw whitespace WER mean | 299.89 |
| zh-normalized CER macro / micro | 22.83 / 22.72 |
| zh-jieba WER macro / micro | 30.72 / 30.39 |
| Wall time seconds | 164.41 |
| Seconds per row | 0.637 |
| Rows per second | 1.569 |
| Unsafe downrouting count | 34 |
| High-risk missed count | 30 |
| Risk-atom proxy error rate | 0.1145 |
| Locale violation rows | 0 |

## Interpretation

The base model is the fastest of the three current 258-row Breeze-ASR-25
variants, but it is much weaker on surface quality and proxy decision safety.
It should remain a baseline comparator, not the next ASR hypothesis generator.

Raw predictions and validation JSON remain ignored local artifacts. The tracked
files here contain only aggregate metrics and commands.

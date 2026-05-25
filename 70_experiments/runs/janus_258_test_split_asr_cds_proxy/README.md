# JANUS 258 Test Split ASR/CDS Proxy Comparison

Status: partial_completed

Date: 2026-05-25

## Purpose

Move from the 15-row gate into the canonical `janus_165_v1` test split without
turning the work into a raw ASR leaderboard. This record compares the two
legacy best candidates on aggregate ASR quality, proxy risk-atom stability,
locale compliance, and runtime.

Raw predictions, runtime logs, validation JSON, and summaries remain in ignored
local `predictions/` and `artifacts/` folders. This tracked record keeps only
aggregate metrics and decisions.

## Inputs

- Manifest:
  `40_breeze_asr25_finetune_dataset/manifests/test.jsonl`
- Source join table:
  `40_breeze_asr25_finetune_dataset/manifests/test_with_sources.tsv`
- Rows: `258`
- Locale rule: Taiwan Traditional Chinese (`zh-TW`) output only; no Simplified
  Chinese output.

## Commands

Partial encoder:

```bash
.venv/bin/python 60_whisper_asr_finetuning/scripts/run_legacy_breeze_asr25_smoke.py \
  --model-kind partial_encoder \
  --run-id breeze_asr25_partial_encoder_legacy_best_test_split \
  --manifest 40_breeze_asr25_finetune_dataset/manifests/test.jsonl \
  --gold-review 40_breeze_asr25_finetune_dataset/manifests/test_with_sources.tsv \
  --runtime cuda \
  --disable-cudnn \
  --torch-dtype float16 \
  --split-name test \
  --max-samples 258
```

LoRA:

```bash
.venv/bin/python 60_whisper_asr_finetuning/scripts/run_legacy_breeze_asr25_smoke.py \
  --model-kind lora \
  --run-id breeze_asr25_lora_legacy_best_test_split \
  --manifest 40_breeze_asr25_finetune_dataset/manifests/test.jsonl \
  --gold-review 40_breeze_asr25_finetune_dataset/manifests/test_with_sources.tsv \
  --runtime cuda \
  --disable-cudnn \
  --torch-dtype float16 \
  --split-name test \
  --max-samples 258
```

Validation:

```bash
.venv/bin/python 80_semantic_risk_asr/scoring/validate_janus_asr_hypotheses.py \
  --gold-review 40_breeze_asr25_finetune_dataset/manifests/test_with_sources.tsv \
  --nemo-manifest 40_breeze_asr25_finetune_dataset/manifests/test.jsonl \
  --hypotheses <predictions.jsonl> \
  --expected-rows 258 \
  --require-labels \
  --require-quality-signal
```

Aggregate comparison:

```bash
.venv/bin/python 80_semantic_risk_asr/scoring/summarize_janus_asr_test_split.py \
  --manifest 40_breeze_asr25_finetune_dataset/manifests/test.jsonl \
  --hypotheses 70_experiments/runs/breeze_asr25_partial_encoder_legacy_best_test_split/predictions/breeze_asr25_partial_encoder_legacy_best_test_split_predictions.jsonl \
  --hypotheses 70_experiments/runs/breeze_asr25_lora_legacy_best_test_split/predictions/breeze_asr25_lora_legacy_best_test_split_predictions.jsonl \
  --hypotheses 70_experiments/runs/breeze_asr25_base_test_split/predictions/breeze_asr25_base_test_split_predictions.jsonl \
  --output-tsv 70_experiments/runs/janus_258_test_split_asr_cds_proxy/asr_cds_proxy_comparison.tsv \
  --summary-json 70_experiments/runs/janus_258_test_split_asr_cds_proxy/summary.json
```

## Results

| Run | Rows | CER | WER | Wall time sec | Sec/row | Rows/sec | Unsafe downrouting | High-risk missed | Risk-atom error rate | Negation flip rate | Amount distortion rate | Action confusion rate | Locale violations |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `breeze_asr25_partial_encoder_legacy_best_test_split` | 258 | 18.24 | 100.0 | 213.79 | 0.829 | 1.207 | 7 | 4 | 0.0431 | 0.0155 | 0.3264 | 0.0614 | 0 |
| `breeze_asr25_lora_legacy_best_test_split` | 258 | 22.86 | 100.0 | 403.37 | 1.563 | 0.640 | 10 | 7 | 0.0613 | 0.0310 | 0.3992 | 0.0982 | 0 |
| `breeze_asr25_base_test_split` | 258 | 33.11 | 299.89 | 164.41 | 0.637 | 1.569 | 34 | 30 | 0.1145 | 0.0271 | 0.6694 | 0.1504 | 0 |

Validation:

- Partial encoder: `ok=true`, `258/258` expected IDs observed, no duplicate IDs,
  no missing hypothesis text, no missing labels, no missing quality signals.
- LoRA: `ok=true`, `258/258` expected IDs observed, no duplicate IDs, no
  missing hypothesis text, no missing labels, no missing quality signals.
- Breeze-ASR-25 base: `ok=true`, `258/258` expected IDs observed, no duplicate
  IDs, no missing hypothesis text, no missing labels, no missing quality
  signals.

## Interpretation

The 258-row test split strengthens the 15-row conclusion:

- Partial encoder remains better than LoRA on CER and runtime.
- Partial encoder is also better on the proxy safety counts: fewer unsafe
  downroutes, fewer high-risk misses, lower risk-atom error rate, fewer
  negation flips, lower amount distortion, and lower action confusion.
- LoRA does not justify replacing partial encoder as the next ASR hypothesis
  generator. It remains useful as contrast evidence that fine-tuning type and
  lower CER are not enough; downstream risk behavior still matters.
- Breeze-ASR-25 base is faster than both fine-tuned variants in this local run,
  but much weaker on surface quality and proxy safety counts.
- The WER values in this table are legacy raw whitespace-token fields. The
  2026-05-25 WER audit shows they are not publication-grade primary metrics for
  unsegmented Chinese. Use `wer_metric_audit_2026_05_25/text_metric_audit.tsv`
  for segmented WER and corpus-level micro rates.
- Locale gate passed for all three candidates in this aggregate check:
  `simplified_char_count=0`, `locale_violation_rows=0`.

## Next Decision

Promote `breeze_asr25_partial_encoder_legacy_best_test_split` as the current
ASR hypothesis generator for the next split-aware CDS metric builder.

Before the 300-row high-stakes expansion:

1. Run comparable 258-row baselines for Breeze-ASR-25 base, Whisper large-v3,
   Whisper large-v3 turbo, and any new ASR candidates that pass the 15-row
   contract.
2. Add FunASR SenseVoice, Qwen3-ASR, and Gemma 4 audio candidates only through
   smoke and 15-row gates first.
3. Keep recording runtime, throughput, locale violations, missing/duplicate ID
   counts, proxy decision metrics, and next-gate interpretation for every
   candidate.

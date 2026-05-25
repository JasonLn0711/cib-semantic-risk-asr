# JANUS 258 Test Split ASR/CDS Proxy Comparison

Status: partial_completed

Date: 2026-05-25

## Purpose

Move from the 15-row gate into the canonical `janus_165_v1` test split without
turning the work into a raw ASR leaderboard. This record compares the two
legacy best candidates, Breeze-ASR-25 base, Whisper small, and Whisper large-v2
on aggregate ASR quality, proxy risk-atom stability, locale compliance, and
runtime.

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
  --expected-manifest 40_breeze_asr25_finetune_dataset/manifests/test.jsonl \
  --expected-rows 258 \
  --hypotheses <predictions.jsonl> \
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
  --hypotheses 70_experiments/runs/whisper_small_test_split/predictions/whisper_small_test_split_predictions.jsonl \
  --hypotheses 70_experiments/runs/whisper_large_v2_test_split/predictions/whisper_large_v2_test_split_predictions.jsonl \
  --output-tsv 70_experiments/runs/janus_258_test_split_asr_cds_proxy/asr_cds_proxy_comparison.tsv \
  --summary-json 70_experiments/runs/janus_258_test_split_asr_cds_proxy/summary.json
```

Five-model split-aware metric bridge:

```bash
.venv/bin/python 80_semantic_risk_asr/scoring/build_janus_metric_inputs.py \
  --split test_258 \
  --review-mode proxy \
  --manifest 40_breeze_asr25_finetune_dataset/manifests/test.jsonl \
  --gold-review 40_breeze_asr25_finetune_dataset/manifests/test_with_sources.tsv \
  --expected-rows 258 \
  --require-all-gold-ids \
  --hypotheses 70_experiments/runs/breeze_asr25_partial_encoder_legacy_best_test_split/predictions/breeze_asr25_partial_encoder_legacy_best_test_split_predictions.jsonl \
  --hypotheses 70_experiments/runs/breeze_asr25_lora_legacy_best_test_split/predictions/breeze_asr25_lora_legacy_best_test_split_predictions.jsonl \
  --hypotheses 70_experiments/runs/breeze_asr25_base_test_split/predictions/breeze_asr25_base_test_split_predictions.jsonl \
  --hypotheses 70_experiments/runs/whisper_small_test_split/predictions/whisper_small_test_split_predictions.jsonl \
  --hypotheses 70_experiments/runs/whisper_large_v2_test_split/predictions/whisper_large_v2_test_split_predictions.jsonl \
  --output-dir 70_experiments/runs/janus_258_test_split_asr_cds_proxy/artifacts/metric_inputs_five_model_validation
```

## Results

| Run | Rows | zh CER micro | zh-jieba WER micro | Stored CER | Legacy WER | Wall time sec | Sec/row | Rows/sec | Unsafe downrouting | High-risk missed | Risk-atom error rate | Locale violations |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `breeze_asr25_partial_encoder_legacy_best_test_split` | 258 | 15.04 | 21.53 | 18.24 | 100.0 | 213.79 | 0.829 | 1.207 | 7 | 4 | 0.0431 | 0 |
| `breeze_asr25_lora_legacy_best_test_split` | 258 | 18.23 | 25.59 | 22.86 | 100.0 | 403.37 | 1.563 | 0.640 | 10 | 7 | 0.0613 | 0 |
| `breeze_asr25_base_test_split` | 258 | 22.72 | 30.39 | 33.11 | 299.89 | 164.41 | 0.637 | 1.569 | 34 | 30 | 0.1145 | 0 |
| `whisper_large_v2_test_split` | 258 | 24.72 | 32.23 | 24.92 | 32.75 | 523.49 | 2.029 | 0.493 | 33 | 28 | 0.1276 | 1 |
| `whisper_small_test_split` | 258 | 34.86 | 43.44 | 36.11 | 45.13 | 152.92 | 0.593 | 1.687 | 76 | 70 | 0.2542 | 4 |

Metric policy:

- `zh CER micro` is the paper-facing primary ASR surface metric.
- `zh-jieba WER micro` is a supplemental segmented word metric.
- `Stored CER` and `Legacy WER` are retained for reproducibility of earlier
  predictions; `Legacy WER` is raw whitespace-token WER and is not a primary
  Chinese ASR metric.

Validation:

- Partial encoder: `ok=true`, `258/258` expected IDs observed, no duplicate IDs,
  no missing hypothesis text, no missing labels, no missing quality signals.
- LoRA: `ok=true`, `258/258` expected IDs observed, no duplicate IDs, no
  missing hypothesis text, no missing labels, no missing quality signals.
- Breeze-ASR-25 base: `ok=true`, `258/258` expected IDs observed, no duplicate
  IDs, no missing hypothesis text, no missing labels, no missing quality
  signals.
- Whisper small: `ok=true`, `258/258` expected IDs observed, no duplicate IDs,
  no missing hypothesis text, no missing labels, no missing quality signals.
- Whisper large-v2: `ok=true`, `258/258` expected IDs observed, no duplicate
  IDs, no missing hypothesis text, no missing labels, no missing quality
  signals.

Split-aware metric bridge:

| Metric | Value |
| --- | ---: |
| Reference rows | 258 |
| Hypothesis rows | 1290 |
| SRES rows | 2648 |
| CEIS variant rows | 2648 |
| Downstream rows | 1290 |
| SRES total / mean | 24120.0 / 9.109 |
| CEIS unstable samples | 164 |
| CEIS max / mean | 15.0 / 1.184 |
| Downstream ASR mismatch rate | 0.1287 |
| High-risk missed by ASR | 139 |

These bridge outputs are proxy-mode engineering evidence. They are not a
substitute for human-reviewed risk-atom annotation.

## Interpretation

The 258-row test split strengthens the 15-row conclusion:

- Partial encoder remains better than LoRA, Breeze-ASR-25 base, Whisper
  large-v2, and Whisper small on paper-facing zh-normalized CER.
- Partial encoder is also better on the proxy safety counts: fewer unsafe
  downroutes, fewer high-risk misses, lower risk-atom error rate, fewer
  negation flips, lower amount distortion, and lower action confusion.
- LoRA does not justify replacing partial encoder as the next ASR hypothesis
  generator. It remains useful as contrast evidence that fine-tuning type and
  lower CER are not enough; downstream risk behavior still matters.
- Breeze-ASR-25 base is faster than both fine-tuned variants in this local run,
  but weaker on surface quality and proxy safety counts.
- Whisper large-v2 is the strongest current Whisper-family 258-row comparator,
  but it does not beat Breeze-ASR-25 base or the legacy best models on
  `cer_zh_micro` or proxy safety counts.
- Whisper small is fast but weak on both `cer_zh_micro` and downstream proxy
  risk. It should remain a low-cost contrast model, not a main 300-row
  candidate.
- The aggregate TSV now carries both legacy stored metrics and paper-facing
  `zh_asr` metrics. Use `cer_zh_micro` as the primary surface metric and
  `wer_zh_jieba_micro` only as supplemental evidence.
- Locale gate passed cleanly for the three Breeze/legacy candidates. Whisper
  large-v2 had `locale_violation_rows=1`; Whisper small had
  `locale_violation_rows=4`. These rows need audit before any paper claim that
  a Whisper-family model satisfies the Taiwan Traditional Chinese locale gate.

## Next Decision

Promote `breeze_asr25_partial_encoder_legacy_best_test_split` as the current
ASR hypothesis generator for the next expanded baseline gate.

Before the 300-row high-stakes expansion:

1. Run comparable 258-row baselines for optional Breeze-ASR-26, Whisper
   large-v3, Whisper large-v3 turbo, and any new ASR candidates that pass the
   15-row contract.
2. Add FunASR SenseVoice, Qwen3-ASR, and Gemma 4 audio candidates only through
   smoke and 15-row gates first.
3. Keep recording runtime, throughput, locale violations, missing/duplicate ID
   counts, proxy decision metrics, and next-gate interpretation for every
   candidate.

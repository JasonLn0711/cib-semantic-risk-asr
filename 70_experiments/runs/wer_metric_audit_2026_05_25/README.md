# WER Metric Audit 2026-05-25

## Purpose

Audit why JANUS WER values were repeatedly `100.0`, `299.89`, or otherwise
unstable, and decide which ASR text metrics are defensible for paper-facing
model comparisons.

## Finding

The earliest 15-row and 258-row inference runners computed WER with raw Python
whitespace splitting:

```python
ref_units = reference.split()
pred_units = prediction.split()
WER = edit_distance(ref_units, pred_units) / len(ref_units)
```

This matches the classic WER edit-distance formula, but it is not a valid
primary metric for unsegmented Taiwan Mandarin transcripts. Most reference
utterances become one token, so one Chinese character substitution can become
`100.0` WER, and extra spaces in the hypothesis can push WER above `100.0`.

The legacy training scripts used a different definition: normalize text,
segment with `jieba.cut`, then run `jiwer.wer`. Therefore the old trainer
`eval_wer`/`test_wer` values and the earliest inference `wer` fields were not
directly comparable. Current runners now write `wer` with `zh_asr`
normalization plus `jieba` tokenization, and retain raw whitespace WER only in
explicit audit fields.

## International-Norm Decision

- The formula `(substitutions + deletions + insertions) / reference tokens`
  follows the conventional WER definition used by NIST/SCTK-style ASR scoring.
- For Chinese ASR, the token unit must be declared. Character error rate is
  normally safer as the primary surface metric; word-level Chinese WER is only
  defensible if the segmentation tool and normalization policy are fixed.
- This repo will use the aggregate `cer_zh_micro` column, produced from the
  `cer_zh_normalized` profile, as the paper-facing primary ASR surface metric,
  keep `wer_zh_jieba_micro` as a supplemental segmented word metric, and retain
  `wer_raw_whitespace` only as a legacy audit field.
- Main tables should prefer corpus-level micro rates. Macro per-row means may
  be reported only when explicitly labeled as macro.
- A paper table must state the reference source, tokenizer, normalization,
  macro/micro scope, package versions, and ID-alignment validation status.

References consulted:

- NIST TREC SDR ASR metric slide: `WER = (I + D + S) / reference words`.
  https://trec.nist.gov/pubs/trec9/sdrt9_slides/tsld017.htm
- Microsoft Speech service docs point to NIST SCTK/sclite for local WER
  replication and define TER with the same token-level formula.
  https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-custom-speech-evaluate-data
- Chinese dialect ASR survey defines CER and WER with the same edit-distance
  form but different Chinese character/word units.
  https://link.springer.com/article/10.1007/s10462-023-10668-0
- Multilingual ASR evaluation work argues CER should be prioritized or at
  least supplemented because WER fails for languages without clear word
  boundaries.
  https://arxiv.org/abs/2410.07400

## Code Changes

- Added `60_whisper_asr_finetuning/scripts/asr_text_metrics.py`.
- Updated `run_janus_whisper_family_pilot.py` and
  `run_legacy_breeze_asr25_smoke.py` so future runs default to:
  - `metric_normalization=zh_asr`;
  - `wer_tokenizer=jieba`;
  - no Traditional/Simplified conversion.
- Added `80_semantic_risk_asr/scoring/audit_asr_text_metrics.py` for
  aggregate-only metric audits over ignored local prediction files. The script
  now accepts `--expected-manifest` and `--expected-rows`, checks missing/extra
  IDs and reference mismatches, and records package versions.
- Added `jieba` to `requirements-whisper.txt`.

## Audit Command

```bash
.venv/bin/python 80_semantic_risk_asr/scoring/audit_asr_text_metrics.py \
  --expected-manifest 40_breeze_asr25_finetune_dataset/manifests/test.jsonl \
  --expected-rows 258 \
  --hypotheses 70_experiments/runs/breeze_asr25_partial_encoder_legacy_best_test_split/predictions/breeze_asr25_partial_encoder_legacy_best_test_split_predictions.jsonl \
  70_experiments/runs/breeze_asr25_lora_legacy_best_test_split/predictions/breeze_asr25_lora_legacy_best_test_split_predictions.jsonl \
  70_experiments/runs/breeze_asr25_base_test_split/predictions/breeze_asr25_base_test_split_predictions.jsonl \
  70_experiments/runs/whisper_large_v2_test_split/predictions/whisper_large_v2_test_split_predictions.jsonl \
  70_experiments/runs/whisper_small_test_split/predictions/whisper_small_test_split_predictions.jsonl \
  70_experiments/runs/breeze_asr26_test_split/predictions/breeze_asr26_test_split_predictions.jsonl \
  --output-tsv 70_experiments/runs/wer_metric_audit_2026_05_25/text_metric_audit.tsv \
  --summary-json 70_experiments/runs/wer_metric_audit_2026_05_25/summary.json
```

## 258-Row Audit Result

All six hypothesis files passed the stricter manifest check:

- expected manifest rows: `258`;
- missing references: `0`;
- missing hypotheses: `0`;
- missing expected IDs: `0`;
- extra IDs: `0`;
- reference mismatch rows: `0`.

Package versions recorded in `summary.json`: `editdistance 0.8.1`,
`jieba 0.42.1`, `jiwer 3.1.0`.

| Run | Stored WER mean | Raw whitespace WER macro | Raw whitespace WER micro | zh-jieba WER macro | zh-jieba WER micro | zh-normalized CER macro | zh-normalized CER micro |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `breeze_asr25_partial_encoder_legacy_best_test_split` | 100.0 | 100.0 | 100.0 | 22.15 | 21.53 | 15.44 | 15.04 |
| `breeze_asr25_lora_legacy_best_test_split` | 100.0 | 100.0 | 100.0 | 26.61 | 25.59 | 18.91 | 18.23 |
| `breeze_asr25_base_test_split` | 299.89 | 299.89 | 242.47 | 30.72 | 30.39 | 22.83 | 22.72 |
| `whisper_large_v2_test_split` | 32.75 | 146.9 | 133.42 | 32.75 | 32.23 | 24.92 | 24.72 |
| `whisper_small_test_split` | 45.13 | 179.43 | 155.89 | 45.13 | 43.44 | 36.11 | 34.86 |
| `breeze_asr26_test_split` | 33.12 | 1442.04 | 1054.79 | 33.12 | 32.29 | 24.87 | 24.27 |

Independent `jiwer` cross-check of zh-jieba corpus WER matched the repo
implementation exactly after joining the deterministic `jieba` tokens:

| Run | Repo zh-jieba WER micro | `jiwer` WER | Delta |
| --- | ---: | ---: | ---: |
| `breeze_asr25_partial_encoder_legacy_best_test_split` | 21.529582 | 21.529582 | 0.0 |
| `breeze_asr25_lora_legacy_best_test_split` | 25.591631 | 25.591631 | 0.0 |
| `breeze_asr25_base_test_split` | 30.389610 | 30.389610 | 0.0 |
| `whisper_large_v2_test_split` | 32.229437 | 32.229437 | 0.0 |
| `whisper_small_test_split` | 43.441558 | 43.441558 | 0.0 |
| `breeze_asr26_test_split` | 32.287157 | 32.287157 | 0.0 |

## Verdict

The old raw whitespace WER fields are formula-compatible but not
publication-grade primary metrics for this unsegmented Chinese corpus. Treat all
existing 15-row/258-row `wer` values before this audit as legacy compatibility
fields, not as model-selection evidence.

Current and future comparable runs must use `metric_normalization=zh_asr`,
`wer_tokenizer=jieba`, manifest-level ID validation, and corpus-level micro
aggregation for paper-facing WER. Even then, `wer_zh_jieba_micro` remains
supplemental for Mandarin Chinese; `cer_zh_micro` is the primary surface ASR
metric, and CDS-ASR decision metrics carry the safety argument.

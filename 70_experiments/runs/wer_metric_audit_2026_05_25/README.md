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
  IDs and reference mismatches, records package versions, and writes an
  independent `jiwer` corpus-WER cross-check for every word-level profile.
- Hardened `audit_asr_text_metrics.py` to preserve valid zero-valued stored
  `cer=0.0` / `wer=0.0` fields instead of treating them as empty, and to record
  `zero_reference_unit_rows` when a profile cannot produce reference units.
- Updated `summarize_janus_asr_test_split.py` so aggregate comparison tables
  use the expected manifest transcript as the scoring reference and fail the
  summary if prediction-embedded references diverge from the manifest.
- Updated the legacy `run_whisper_small_smoke.py` runner so any future smoke
  output uses the same `zh_asr` normalization plus `jieba` WER profile by
  default, while still retaining raw whitespace WER as an audit field.
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

The 2026-05-25 re-run also added automatic `jiwer_micro_percent` and
`jiwer_delta_percent` columns to `text_metric_audit.tsv`. All word-level WER
profiles, including the legacy raw whitespace profile and the supplemental
zh-jieba profile, matched `jiwer` with `0.0` absolute delta after deterministic
token joining.

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

## Legacy 15-Row Re-Audit

The six 15-row pilot/stress files were re-audited with the original
`nemo_pilot_input_manifest.jsonl` reference transcripts because several early
prediction JSONL files did not embed `reference_text`. All six files now pass
manifest row count, missing/extra ID, missing reference, missing hypothesis,
reference mismatch, and zero-reference-unit checks.

| Run | Stored WER mean | zh-jieba WER micro | `jiwer` WER | Delta |
| --- | ---: | ---: | ---: | ---: |
| `breeze_asr25_15_row_baseline` | 380.0 | 30.78 | 30.778165 | 0.0 |
| `breeze_asr25_lora_legacy_best_15_row` | 100.0 | 34.61 | 34.610918 | 0.0 |
| `breeze_asr25_partial_encoder_legacy_best_15_row` | 83.33 | 14.52 | 14.518002 | 0.0 |
| `breeze_asr26_15_row_stress_test` | 1493.33 | 32.64 | 32.636469 | 0.0 |
| `whisper_large_v2_15_row_baseline` | 100.0 | 39.61 | 39.605110 | 0.0 |
| `whisper_small_15_row_baseline` | 500.0 | 49.83 | 49.825784 | 0.0 |

These values explain the earlier confusion: stored WER values such as `380.0`,
`500.0`, and `1493.33` are not model-quality evidence. They are legacy raw
whitespace fields over unsegmented Chinese. The manifest-validated zh-jieba
WERs are formula-compatible and reproducible, but remain supplemental to
`cer_zh_micro`.

## 300-Row High-Stakes Check

The high-stakes 300-row Breeze-family runs were audited with
`high_stakes_300_manifest.jsonl`. The combined audit is tracked in
`high_stakes_300_metric_audit.tsv` and `high_stakes_300_summary.json`. All three
runs passed manifest alignment with:

- expected rows: `300`;
- missing reference rows: `0`;
- missing hypotheses: `0`;
- missing expected IDs: `0`;
- extra IDs: `0`;
- reference mismatch rows: `0`;
- zero reference unit rows: `0`;
- zh-jieba WER `jiwer` delta: `0.0`.

| Run | Stored WER mean | Raw whitespace WER micro | zh-jieba WER micro | zh-normalized CER micro | `jiwer` delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| `breeze_asr25_partial_encoder_high_stakes_300` | 9.55 | 93.16 | 9.38 | 6.86 | 0.0 |
| `breeze_asr25_lora_high_stakes_300` | 22.15 | 101.30 | 21.91 | 15.97 | 0.0 |
| `breeze_asr25_base_high_stakes_300` | 28.74 | 271.66 | 28.10 | 21.44 | 0.0 |

This re-check explains why old WER values looked unstable while the current
metric profile is reproducible. Raw whitespace WER still explodes on
unsegmented Chinese and remains audit-only. The publication-facing table should
sort these runs by `cer_zh_micro`, with `wer_zh_jieba_micro` shown only as a
supplemental segmented-word score.

## Verdict

The old raw whitespace WER fields are formula-compatible but not
publication-grade primary metrics for this unsegmented Chinese corpus. Treat all
existing pre-audit `wer` values as legacy compatibility fields unless the run
explicitly declares `metric_normalization=zh_asr`, `wer_tokenizer=jieba`,
manifest validation, and corpus-level aggregation.

Current and future comparable runs must use `metric_normalization=zh_asr`,
`wer_tokenizer=jieba`, manifest-level ID validation, and corpus-level micro
aggregation for paper-facing WER. Even then, `wer_zh_jieba_micro` remains
supplemental for Mandarin Chinese; `cer_zh_micro` is the primary surface ASR
metric, and CDS-ASR decision metrics carry the safety argument.

Reviewer-facing WER claims should therefore say:

- WER formula: edit distance over declared word units divided by reference word
  units.
- Chinese word units: deterministic `jieba 0.42.1` after `zh_asr`
  normalization.
- Primary Chinese surface metric: corpus-level micro CER, because Mandarin text
  lacks reliable whitespace word boundaries.
- Legacy raw whitespace WER: kept only to reproduce earlier confusing values,
  never used as model-quality evidence.

# WER Metric Audit 2026-05-25

## Purpose

Audit why JANUS WER values were repeatedly `100.0`, `299.89`, or otherwise
unstable, and decide which ASR text metrics are defensible for paper-facing
model comparisons.

## Finding

The previous 15-row and 258-row inference runners computed WER with raw
Python whitespace splitting:

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
`eval_wer`/`test_wer` values and the newer inference `wer` fields were not
directly comparable.

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
  aggregate-only metric audits over ignored local prediction files.
- Added `jieba` to `requirements-whisper.txt`.

## Audit Command

```bash
.venv/bin/python 80_semantic_risk_asr/scoring/audit_asr_text_metrics.py \
  --hypotheses 70_experiments/runs/breeze_asr25_partial_encoder_legacy_best_test_split/predictions/breeze_asr25_partial_encoder_legacy_best_test_split_predictions.jsonl \
  70_experiments/runs/breeze_asr25_lora_legacy_best_test_split/predictions/breeze_asr25_lora_legacy_best_test_split_predictions.jsonl \
  70_experiments/runs/breeze_asr25_base_test_split/predictions/breeze_asr25_base_test_split_predictions.jsonl \
  --output-tsv 70_experiments/runs/wer_metric_audit_2026_05_25/text_metric_audit.tsv \
  --summary-json 70_experiments/runs/wer_metric_audit_2026_05_25/summary.json
```

## 258-Row Audit Result

| Run | Stored WER mean | Raw whitespace WER macro | Raw whitespace WER micro | zh-jieba WER macro | zh-jieba WER micro | zh-normalized CER macro | zh-normalized CER micro |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `breeze_asr25_partial_encoder_legacy_best_test_split` | 100.0 | 100.0 | 100.0 | 22.15 | 21.53 | 15.44 | 15.04 |
| `breeze_asr25_lora_legacy_best_test_split` | 100.0 | 100.0 | 100.0 | 26.61 | 25.59 | 18.91 | 18.23 |
| `breeze_asr25_base_test_split` | 299.89 | 299.89 | 242.47 | 30.72 | 30.39 | 22.83 | 22.72 |

## Verdict

The old raw whitespace WER fields are formula-compatible but not
publication-grade primary metrics for this unsegmented Chinese corpus. Treat all
existing 15-row/258-row `wer` values before this audit as legacy compatibility
fields, not as model-selection evidence. Future comparable runs must either use
the new default metric profile or explicitly pass `--wer-tokenizer whitespace`
only for reproducing historical numbers.

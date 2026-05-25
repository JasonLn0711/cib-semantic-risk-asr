# Run Record: janus_300_500_high_stakes_expansion

## Summary

- Status: selected
- Date: 2026-05-25
- Owner: Jason Lin
- Config: `60_whisper_asr_finetuning/scripts/select_janus_high_stakes_expansion.py`
- Dataset: `janus_165_v1`
- Model: cross-ASR candidate selection
- Seed: not applicable
- Hardware: local CPU for selection

## Purpose

Select the next `300-500` high-stakes JANUS segments after the 15-row
decision-stability gate shows a usable signal.

This is not a random sample. It is a risk-term and scenario-coverage expansion
set for the next ASR/CDS pass.

## Selection Rule

The selector ranks rows by:

- financial-action terms such as transfer, account, bank, card, and payment;
- identity/government/police terms;
- LINE/social-account and investment/crypto scenarios;
- split balance across train, validation, and test;
- reasonable duration for ASR comparison;
- health flags, with non-OK rows downweighted.

The reviewed 15-row gold set is excluded from this expansion candidate set.

## Execution

```bash
python 60_whisper_asr_finetuning/scripts/select_janus_high_stakes_expansion.py \
  --sample-size 300
```

The selected IDs were converted into a runner-readable manifest with:

```bash
.venv/bin/python 60_whisper_asr_finetuning/scripts/prepare_janus_high_stakes_manifest.py
```

## Artifacts

- Local candidate IDs and risk metadata:
  `artifacts/expansion_candidates.tsv` (ignored local)
- Local runner manifest:
  `artifacts/high_stakes_300_manifest.jsonl` (ignored local)
- Repo-safe aggregate summary:
  `selection_summary.tsv`
- Repo-safe manifest summary:
  `high_stakes_manifest_summary.tsv`

Do not commit raw transcripts, copied audio, or full prediction outputs for the
expansion set.

## Current Selection Summary

- Selected rows: `300`
- Candidate pool rows: `2704`
- Excluded reviewed pilot rows: `15`
- Split counts: train `240`, validation `30`, test `30`
- Health flags: `300` rows are `ok`
- Duration range: `15.838` to `29.736` seconds, mean `24.437` seconds

The selected IDs are local-only under ignored `artifacts/`; git tracks only the
aggregate summary and selection method.

## ASR Passes

Three Breeze-family 300-row high-stakes passes have completed with the same
manifest, Traditional Chinese-preserving `zh_asr` normalization, and `jieba`
WER tokenization:

| Run | Rows | Wall time | Stored row-mean CER | Stored row-mean WER | `cer_zh_micro` | `wer_zh_jieba_micro` | Raw whitespace WER micro |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `breeze_asr25_partial_encoder_high_stakes_300` | 300 | `275.74s` | 7.03 | 9.55 | 6.86 | 9.38 | 93.16 |
| `breeze_asr25_lora_high_stakes_300` | 300 | `481.25s` | 16.15 | 22.15 | 15.97 | 21.91 | 101.30 |
| `breeze_asr25_base_high_stakes_300` | 300 | `214.96s` | 22.07 | 28.74 | 21.44 | 28.10 | 271.66 |

All three passed `300/300` manifest validation with no missing IDs, no extra
IDs, no duplicate IDs, present hypothesis text, present ASR labels, and quality
fields `cer` and `wer`. The combined WER audit in
`70_experiments/runs/wer_metric_audit_2026_05_25/high_stakes_300_metric_audit.tsv`
also matched `jiwer` corpus WER with `0.0` delta for every word-level profile.

Raw predictions, runtime logs, validation JSON, and the full high-stakes
manifest remain ignored under `predictions/` and `artifacts/`. The repo tracks
only aggregate run records and text metric audit summaries.

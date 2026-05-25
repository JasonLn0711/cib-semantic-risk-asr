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

## First ASR Pass

The first 300-row high-stakes pass completed with the legacy partial-encoder
Breeze-ASR-25 checkpoint:

- Run ID: `breeze_asr25_partial_encoder_high_stakes_300`
- Rows: `300/300`
- Runtime: CUDA, cuDNN disabled, `float16`
- Metric profile: `metric_normalization=zh_asr`, `wer_tokenizer=jieba`
- Wall time: `275.74` seconds
- Stored row-mean CER/WER: CER `7.03`, WER `9.55`
- Corpus micro rates from manifest-validated audit: `cer_zh_micro=6.86`,
  `wer_zh_jieba_micro=9.38`
- `jiwer` corpus-WER delta for zh-jieba WER: `0.0`
- Hypothesis validation: passed `300/300` expected IDs, no missing labels, no
  missing quality fields, no duplicate IDs

Raw predictions, runtime logs, and validation JSON remain ignored under the
run's `predictions/` and `artifacts/` directories. The repo tracks only the
aggregate `text_metric_audit.tsv` and run README.

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

## Artifacts

- Local candidate IDs and risk metadata:
  `artifacts/expansion_candidates.tsv` (ignored local)
- Repo-safe aggregate summary:
  `selection_summary.tsv`

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

# Variant Generator Contract

Date: 2026-06-03

Status: frozen protocol for final CSL claim wording.

## Role

The variant generator supplies plausible ASR alternatives around
decision-bearing spans. The generator is a tool assumption for a scoped audit,
not a guarantee that every dangerous transcript alternative has been
enumerated.

## Allowed Inputs

The final CSL method may describe these allowed sources:

- ASR hypotheses and model disagreement;
- Mandarin phonetic or near-phonetic ambiguity rules;
- Taiwan Traditional Chinese normalization and locale checks;
- domain-slot alternatives for anti-fraud triage language;
- runtime or quality signals;
- acoustic ambiguity evidence when available.

## Forbidden Inputs

The generator protocol forbids:

- reference transcript text;
- human audit labels;
- expected safe action labels;
- reviewer notes;
- reviewer decision-change reasons;
- policy replay outcomes;
- CEIS/SRES selection stratum labels as generator features.

## Plausibility Falsification

A variant is rejected as not plausible when it is unsupported by the allowed
acoustic, phonetic, model-disagreement, locale, or domain-slot evidence; when it
adds information that the audio span cannot carry; or when it is domain-invalid
despite superficial acoustic similarity.

Aggregate reject reasons should be reported as:

- `acoustic_unsupported`;
- `phonetic_unsupported`;
- `domain_invalid`;
- `context_contradiction`;
- `external_content_insertion`;
- `locale_invalid`;
- `duplicate_or_no_decision_difference`.

## Reproducibility Boundary

The final reviewer package should expose source coverage and reject-reason
counts. Raw variants and transcript-bearing examples remain local. Synthetic
minimal pairs are used only to demonstrate mechanism, not prevalence.

## Current Evidence Status

The 2026-06-03 final aggregate run reports source/atom proxy coverage from the
available CEIS scored file. Exact row-level variant-count matching is not
claimed unless the local ID boundary is opened or a redacted row-key bridge is
created.

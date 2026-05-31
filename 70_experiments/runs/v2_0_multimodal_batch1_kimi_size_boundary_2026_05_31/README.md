# Kimi-Audio Size-Boundary Decision

Date: 2026-05-31

Status: size-boundary decision recorded; no model inference was run

本紀錄只保存公開模型中繼資料與治理決策，不保存任何逐字稿或私有音訊內容。

## Purpose

This run records the explicit size-boundary decision required before
`moonshotai/Kimi-Audio-7B-Instruct` can move from Gate 0 metadata discovery to
isolated transcript-only runtime smoke.

The decision preserves Kimi-Audio as a primary zh-TW audio-language candidate
while making the under-10B claim boundary auditable.

## Evidence Inputs

| Field | Evidence |
| --- | --- |
| Source model | `moonshotai/Kimi-Audio-7B-Instruct` |
| Gate 0 source | `70_experiments/runs/v2_0_multimodal_batch1_candidate_discovery_2026_05_31/candidate_snapshot.tsv` |
| Public model label | `Kimi-Audio-7B-Instruct` |
| Parameter/source note | Gate 0 records `Kimi-Audio-7B label; HF widget currently reports 10B params` |
| Public artifact-storage estimate | `39.67` GiB from public HF weight-file metadata |
| Gate 0 revision SHA | `9a82a84c37ad9eb1307fb6ed8d7b397862ef9e6b` |
| License | `mit` |
| Runtime source | official KimiAudio package / Docker; text output only |

## Decision

Kimi-Audio remains in the primary Batch 1 zh-TW audio LLM lane because the
scientific candidate is the public `Kimi-Audio-7B-Instruct` family and the v2.0
experiment targets practical under-10B-class audio-language models. The
runtime-smoke claim must be written with an explicit validation layer:

```text
Kimi-Audio is evaluated as a primary 7B-labeled audio-language candidate.
The report must disclose that the current public HF widget marks the model as
10B params, while the model name/card and Gate 0 candidate definition use the
7B label. Kimi can enter isolated transcript-only runtime smoke, but it cannot
be used for strict loaded-parameter-count claims until loaded parameter evidence
is separately recorded.
```

## Scope Control

Allowed next step:

- isolated one-row transcript-only runtime smoke after artifact/runtime checks.

Required reporting wording:

- `7B-labeled Kimi-Audio primary candidate with an explicit size-boundary
  validation layer`

Disallowed reporting wording:

- `strictly verified <10B loaded-parameter model`
- `loaded-parameter count verified`
- `parameter boundary resolved by inference`

Promotion implication:

- Kimi can be included in Gate 1 runtime feasibility and behavior-taxonomy
  records.
- Kimi cannot be promoted as a strict under-10B parameter-count winner until
  separate loaded-parameter evidence resolves the boundary.

## Privacy Boundary

This run is metadata-only. It tracks public model metadata, prior Gate 0
summary values, and a governance decision. It does not contain raw audio, row
IDs, transcripts, model hypotheses, reviewer notes, transcript-bearing runtime
logs, model weights, or local model-cache paths.

## Next Gate

Kimi-Audio may proceed to isolated one-row transcript-only runtime smoke under
the explicit size-boundary reporting language above.

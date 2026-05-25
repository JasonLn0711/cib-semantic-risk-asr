# ASR Candidate Runtime Gate

Date: 2026-05-25

## FIRST PRINCIPLE

The goal is not to collect more model names. A new ASR or multimodal model is
useful only if it can produce reproducible JANUS hypotheses under the same
field contract, timing record, metric policy, and strict Taiwan Traditional
Chinese locale gate.

## Summary

| Candidate | Status | Rows | CER | WER | Locale violations | Decision |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Whisper large-v3 | completed 15-row, locale not clean | 15 | 33.77 | 43.18 | 2 | Do not promote to 258-row yet |
| Whisper large-v3 turbo | completed 15-row, locale not clean | 15 | 41.33 | 52.52 | 4 | Keep as speed/quality smoke only |
| SenseVoiceSmall | completed 1-row, locale failed | 1 | 65.88 | 81.25 | 1 | Do not promote to 15-row yet |
| Qwen3-ASR-0.6B | completed 1-row with cuDNN disabled, locale failed | 1 | 74.12 | 95.83 | 1 | Do not promote to 15-row yet |
| Qwen3-ASR-1.7B | stopped before inference | 0 | n/a | n/a | n/a | Retry only after 0.6B locale gate passes |
| Gemma 4 E2B/E4B | blocked before inference | 0 | n/a | n/a | n/a | Needs isolated multimodal runtime |

## Interpretation

The fixed 15-row Whisper v3 runs are useful reviewer-facing evidence that we
checked newer Whisper baselines. However, both violated the strict Traditional
Chinese locale gate, so neither should be promoted to 258-row as-is.

SenseVoice and Qwen3-ASR are now runnable through repo scripts. Both pass the
1-row hypothesis-contract validation but fail the locale gate on the first row.
That is enough to stop before spending more runtime on 15-row or 258-row
experiments.

Gemma 4 remains a separate prompted multimodal-ASR lane. It is blocked locally
because installed Transformers 4.57.6 does not expose
`AutoModelForMultimodalLM`, while the model configs declare a 5.5.0.dev0-era
runtime. It must not be mixed into the pure ASR table.

## Artifacts

- Aggregate table: `candidate_runtime_gate_summary.tsv`
- Machine summary: `summary.json`
- Individual tracked run records:
  - `../whisper_large_v3_15_row_baseline/README.md`
  - `../whisper_large_v3_turbo_15_row_baseline/README.md`
  - `../sensevoice_small_smoke_1_row/README.md`
  - `../qwen3_asr_0_6b_smoke_1_row/README.md`
  - `../qwen3_asr_1_7b_smoke_1_row/README.md`
  - `../gemma4_audio_runner_gate_2026_05_25/README.md`

Raw predictions, validation artifacts, proxy summaries, model caches, and
runtime logs remain ignored local artifacts.

## Follow-Up

The 2026-05-26 extension promoted SenseVoiceSmall and Qwen3-ASR-0.6B from
1-row smoke to fixed 15-row gates and retried Qwen3-ASR-1.7B as a timed load
gate. See
`../asr_candidate_15_row_extension_2026_05_26/README.md`. The conclusion did
not change: no new candidate is ready for 258-row or selected-300 promotion
under the strict Taiwan Traditional Chinese locale policy.

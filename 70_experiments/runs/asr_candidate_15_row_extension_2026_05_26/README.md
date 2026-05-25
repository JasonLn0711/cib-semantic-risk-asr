# ASR Candidate 15-Row Extension

Date: 2026-05-26

## FIRST PRINCIPLE

The useful question is not whether a model can produce any transcript. The
question is whether it can produce reproducible JANUS hypotheses under the same
field contract, timing record, metric policy, and strict Taiwan Traditional
Chinese locale gate used by the existing Whisper/Breeze evidence.

## Scope

This extension promoted the two runnable non-Whisper candidate families from
1-row smoke to the fixed 15-row pilot gate:

- `FunAudioLLM/SenseVoiceSmall`
- `Qwen/Qwen3-ASR-0.6B`

It also retried `Qwen/Qwen3-ASR-1.7B` as a bounded 1-row load gate. Gemma 4
E2B/E4B remain in the separate multimodal runtime lane and were not mixed into
the pure-ASR table.

## Summary

| Candidate | Status | Rows | CER mean | WER mean | `cer_zh_micro` | `wer_zh_jieba_micro` | Wall time | Outer time | Locale violations | Simplified chars | Decision |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| SenseVoiceSmall | completed, locale failed | 15 | 63.83 | 79.97 | 63.12 | 78.98 | 2.60s | 6.32s | 14 | 209 | reject for full split until zh-TW policy is audited |
| Qwen3-ASR-0.6B | completed, locale failed | 15 | 64.93 | 82.70 | 64.16 | 81.07 | 17.97s | 21.57s | 15 | 260 | reject for full split until zh-TW policy is audited |
| Qwen3-ASR-1.7B | timeout before inference | 0 | n/a | n/a | n/a | n/a | n/a | 60.06s timeout | n/a | n/a | keep as fetch/load-gate blocked |

## Interpretation

Both 15-row candidates passed the hypothesis contract, so the runners are
usable. Both failed the strict zh-TW locale gate, and their surface metrics are
far weaker than the existing Breeze/Whisper pilot evidence. The correct next
step is not a 258-row run; it is a bounded locale-control decision:

- either reject these families for paper-facing pure-ASR comparison;
- or approve a separate audited post-decode conversion/reporting policy;
- or find model-native decoding/prompt controls that produce clean Taiwan
  Traditional Chinese output.

## Artifacts

- Aggregate table: `candidate_15_row_summary.tsv`
- Machine summary: `summary.json`
- Individual tracked run records:
  - `../sensevoice_small_15_row_candidate/README.md`
  - `../qwen3_asr_0_6b_15_row_candidate/README.md`
  - `../qwen3_asr_1_7b_smoke_1_row/README.md`

Raw predictions, validation JSON, proxy details, model caches, and runtime logs
remain ignored local artifacts.

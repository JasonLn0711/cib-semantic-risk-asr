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

## Follow-Up Verification

2026-05-26 02:03 CST: after the user asked whether any remaining ASR/Gemma
candidates should now be tested, the aggregate registry, candidate records,
local runtime, and live Hugging Face metadata were rechecked. No untested
pure-ASR candidate from the requested expansion set remains runnable without
first changing the gate decision:

- All seven requested model pages remain public and ungated in live Hugging
  Face metadata. The current SHA prefixes are:
  `06f233fe06e7`, `41f01f3fe87f`, `716d31dbfd64`, `5eb144179a02`,
  `7278e1e70fe2`, `ed37665cc131`, and `5bf6a20911f0`.
- `validate_janus_asr_hypotheses.py --require-labels --require-quality-signal`
  still passes for the SenseVoiceSmall and Qwen3-ASR-0.6B 15-row hypothesis
  files.
- Installed `transformers` is still `4.57.6`, with no
  `AutoModelForMultimodalLM` or `Gemma4ForConditionalGeneration` exposed.
- Gemma 4 E2B/E4B therefore remain blocked before inference in the separate
  prompted multimodal lane.
- The next research gate remains locale-policy resolution or selected-300
  human risk/decision/model assessment, not a 258-row rerun for these
  locale-failed candidates.

2026-05-26 02:44 CST: a second query-time check repeated the live metadata,
local runtime, and existing 15-row hypothesis validation checks. The result did
not change: the seven requested model pages are public and ungated, the two
runnable non-Whisper candidates still validate at 15 rows but remain locale
failures, Qwen3-ASR-1.7B remains a fetch/load gate, and Gemma 4 still needs an
isolated multimodal runtime before any prompted-ASR test.

2026-05-26 current bounded recheck: see
`../asr_candidate_current_recheck_2026_05_26/`. The recheck validated the four
available 15-row candidate hypothesis files together, rebuilt an aggregate
locale/metric summary, reran Qwen3-ASR-1.7B as a 60-second load gate
(`60.08s`, exit `124`), and repeated the local Gemma 4 class probe. The
decision remains unchanged: do not spend 258-row or selected-300 runtime on
these candidates until the zh-TW locale policy or Gemma multimodal runtime
changes.

## Artifacts

- Aggregate table: `candidate_15_row_summary.tsv`
- Machine summary: `summary.json`
- Individual tracked run records:
  - `../sensevoice_small_15_row_candidate/README.md`
  - `../qwen3_asr_0_6b_15_row_candidate/README.md`
  - `../qwen3_asr_1_7b_smoke_1_row/README.md`

Raw predictions, validation JSON, proxy details, model caches, and runtime logs
remain ignored local artifacts.

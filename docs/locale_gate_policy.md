# Taiwan Traditional Chinese Locale Gate Policy

Date: 2026-05-26

## Policy

All ASR and prompted multimodal-audio outputs for this repo target Taiwan-used
Traditional Chinese. The gate evaluates raw model output, before any
Traditional/Simplified conversion.

## Why Prompting Is Not Enough

Setting `language=zh`, `Chinese`, or a Traditional Chinese prompt does not prove
that the model emits Taiwan Traditional Chinese. Current tracked candidate
evidence shows that Whisper large-v3, Whisper large-v3-turbo, SenseVoiceSmall,
and Qwen3-ASR-0.6B can satisfy small output contracts while still producing
locale violations.

## Raw vs Repair Lanes

| Lane | Allowed claim |
| --- | --- |
| Raw ASR output | model-native ASR quality and locale behavior |
| Post-processed output | deployment repair feasibility only |

OpenCC or other conversion may be useful for deployment repair, but converted
text must not be mixed into the raw ASR benchmark table or used to claim that a
candidate passed the raw locale gate.

## Default Promotion Thresholds

| Check | Threshold |
| --- | --- |
| Expected row output rate | `>= 95%` |
| Simplified character count | `0` for strict promotion |
| Locale-violation row rate | `<= 1%` |
| English-only output for Chinese reference rows | `0` rows |
| Invented speaker labels | `0` rows unless the task explicitly asks for diarization |
| Invented timestamps | `0` rows unless the task explicitly asks for timestamps |

Small gates may record failures for evidence. Promotion to 258-row,
selected-300, or high-stakes 300 is blocked unless the promotion thresholds are
met.

## Required Aggregate Fields

Every candidate gate should record:

- `expected_rows`
- `rows`
- `valid_output_rate`
- `simplified_char_count`
- `simplified_char_rate`
- `locale_violation_rows`
- `locale_violation_rate`
- `english_only_rows`
- `timestamp_like_rows`
- `speaker_label_like_rows`
- `locale_gate_passed`
- `promotion_decision`
- `runtime_seconds` or `wall_time_seconds`
- model id, revision/commit hash, backend, package versions, device, dtype, and
  decoding or prompt policy

## CLI

Use the repo-safe aggregate checker:

```bash
python scripts/check_locale_zh_tw.py \
  --input 70_experiments/runs/sensevoice_small_15_row_candidate/predictions/sensevoice_small_15_row_candidate_predictions.jsonl \
  --text-field hypothesis_text \
  --expected-rows 15 \
  --output-json /tmp/sensevoice_locale_gate.json
```

The script writes aggregate counts only. It does not print hypothesis text,
audio IDs, selected row IDs, transcripts, or reviewer notes.

## Decision Rule

If a candidate fails this gate, keep it in the candidate/exploratory lane and do
not spend 258-row, selected-300, or high-stakes 300 runtime on it. The next work
is either:

1. change and audit the decoding/prompt policy;
2. explicitly approve a post-decode repair lane; or
3. reject the model from the pure-ASR paper table.

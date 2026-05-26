# Gemma 4 Multimodal Runtime Blocker

Date: 2026-05-26

## Scope

This file records why `unsloth/gemma-4-E2B` and `unsloth/gemma-4-E4B` are not
part of the pure-ASR main benchmark table.

## Current Local Blocker

The current candidate runtime in this repo is frozen around
`transformers 4.57.6`. Local probes recorded under
`70_experiments/runs/gemma4_audio_runner_gate_2026_05_25/` and
`70_experiments/runs/asr_candidate_current_recheck_2026_05_26/` show:

| Field | Local result |
| --- | --- |
| `transformers.__version__` | `4.57.6` |
| `AutoModelForMultimodalLM` | unavailable |
| `Gemma4ForConditionalGeneration` | unavailable |
| checkpoint `model_type` | `gemma4` |
| audio config | present in Gemma 4 E2B/E4B config probes |
| current inference rows | `0` |

Current Hugging Face Transformers documentation for Gemma4 lists multimodal
Gemma 4 support and shows audio usage through `AutoModelForMultimodalLM`, but
that is not the runtime currently frozen in this repo. Therefore the blocker is
local runtime compatibility, not absence of a tracked candidate.

## Decision

Do not upgrade the whole repo environment just to force Gemma 4 into the ASR
benchmark. Create an isolated lane instead:

```text
envs/
  asr_baseline_transformers_4_57_6/
  gemma4_multimodal_transformers_5_x/
```

The Gemma lane must be evaluated as prompted multimodal-audio, not as a pure
ASR baseline.

## Required First Successful Gate

Before any 15-row Gemma test, the isolated runtime must record:

- model id and revision;
- package versions, including `transformers`;
- processor class and model class;
- device, dtype, attention implementation, and peak memory if available;
- prompt text;
- audio duration;
- wall time and seconds per row;
- first successful inference row count;
- raw locale gate output from `scripts/check_locale_zh_tw.py`;
- hallucination/repetition/timestamp/speaker-label checks;
- explicit decision on whether the output belongs to the raw prompted
  multimodal lane or a post-processed repair lane.

## Strict Prompt

```text
請逐字轉錄以下台灣電話客服語音，輸出繁體中文（台灣用語），不得輸出簡體中文；只輸出轉錄內容，不要翻譯，不要摘要。
```

Passing this prompt is not sufficient. The raw output must still pass the
aggregate locale gate before promotion.

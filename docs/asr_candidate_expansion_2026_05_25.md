# ASR Candidate Expansion

Date: 2026-05-25

## FIRST PRINCIPLE

The next model set should test whether additional ASR families change
decision-stability evidence, not whether the repo can accumulate a longer model
leaderboard.

Every new candidate must satisfy the same contract before a full split run:

- output `audio_id`, `hypothesis_text`, `cer`, `wer`, `asr_label`, runtime, and
  model identifier;
- use Taiwan Traditional Chinese output policy;
- record wall time, seconds per row, rows per second, device, dtype, cuDNN or
  backend settings, toolkit version, and validation result;
- keep raw predictions, transcripts, model weights, and runtime logs ignored;
- commit only aggregate metrics, run records, source/model pointers, and
  analysis.

## Locale Rule

All ASR and multimodal outputs must be treated as Taiwan Traditional Chinese
transcription, not Simplified Chinese and not translation.

Model-specific implementation:

- Whisper-family: use `language=zh`, `task=transcribe`, then apply the
  Traditional Chinese locale gate because Whisper does not expose a `zh-TW`
  language token.
- SenseVoice: use `language=zh`, keep ITN/VAD settings explicit, then apply the
  Traditional Chinese locale gate.
- Qwen3-ASR: request Chinese ASR with Taiwan Traditional Chinese output and
  apply the locale gate.
- Gemma 4 audio: use a strict prompt: `請逐字轉錄以下台灣電話客服語音，輸出繁體中文（台灣用語），不得輸出簡體中文；只輸出轉錄內容，不要翻譯，不要摘要。`

## Added Candidates

| Candidate | Model ID | Role | First gate |
| --- | --- | --- | --- |
| Whisper large-v3 | `openai/whisper-large-v3` | newer Whisper large baseline | 15-row smoke, then 258-row if locale gate passes |
| Whisper large-v3 turbo | `openai/whisper-large-v3-turbo` | speed/quality tradeoff baseline | 15-row smoke with runtime comparison |
| FunASR SenseVoice | `FunAudioLLM/SenseVoiceSmall` | fast non-autoregressive ASR comparator | new FunASR runner, 15-row contract pass |
| Qwen3-ASR small | `Qwen/Qwen3-ASR-0.6B` | feasibility and latency candidate | new Qwen runner, 15-row contract pass |
| Qwen3-ASR full | `Qwen/Qwen3-ASR-1.7B` | stronger Qwen ASR candidate | only after 0.6B smoke passes |
| Gemma 4 E2B audio | `unsloth/gemma-4-E2B` | cheaper prompted multimodal ASR candidate | new multimodal runner, prompt/locale gate |
| Gemma 4 E4B audio | `unsloth/gemma-4-E4B` | stronger prompted multimodal ASR candidate | after E2B or direct if VRAM allows |

## Required Extra Metrics

Record these for every future model, including failed runs:

- wall time seconds;
- seconds per row;
- rows per second;
- model load time if separable;
- peak GPU memory if available;
- device and dtype;
- backend/toolkit version;
- VAD/chunking/ITN settings;
- prompt text for multimodal models;
- maximum audio length accepted by the runner;
- locale violations: simplified character count, simplified character rate, and
  violating row count;
- hallucination/repetition markers, especially for prompted multimodal models;
- validator result and missing/duplicate ID counts;
- raw artifact paths and git policy;
- interpretation and next gate decision.

## Decision Rule

Do not send every new candidate directly to the 258-row or 300-row split.

Run order:

1. 1-2 row load/inference smoke.
2. 15-row hypothesis-contract validation.
3. 15-row CDS/proxy comparison, including locale gate.
4. 258-row test split only for candidates that pass the contract and add a real
   comparison value.
5. 300-row high-stakes expansion only after the 258-row signal supports the
   model's inclusion.

The current priority remains partial encoder vs LoRA vs Breeze/Whisper
baselines. The new models broaden model-family coverage, but they must not
displace the CDS-ASR decision-stability question.

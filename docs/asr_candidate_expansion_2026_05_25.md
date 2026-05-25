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

## 2026-05-25 Smoke / Readiness Update

Local hardware and runtime:

- GPU: NVIDIA GeForce RTX 5080, 16303 MiB total memory.
- Installed ASR stack before candidate-family install: `torch 2.12.0`,
  `transformers 4.55.2`,
  `torchaudio 2.11.0`, `librosa 0.11.0`, `soundfile 0.13.1`,
  `jiwer 3.1.0`, `jieba 0.42.1`, `huggingface_hub 0.36.2`.
- Candidate-family install completed locally on 2026-05-25:
  `funasr 1.3.3`, `modelscope 1.37.1`, `qwen-asr 0.0.6`, and
  `transformers 4.57.6`. The install log remains ignored under
  `70_experiments/runs/candidate_runtime_install_2026_05_25/logs/`.

Model availability was checked through Hugging Face metadata on 2026-05-25:

| Model | Availability | SHA prefix | Local status |
| --- | --- | --- | --- |
| `openai/whisper-large-v3` | public, not gated | `06f233fe06e7` | 15-row gate completed; locale not clean |
| `openai/whisper-large-v3-turbo` | public, not gated | `41f01f3fe87f` | 15-row gate completed; locale not clean |
| `FunAudioLLM/SenseVoiceSmall` | public, not gated | `3eb3b4eeffc2` | 15-row runner completed; locale failed |
| `Qwen/Qwen3-ASR-0.6B` | public, not gated | `5eb144179a02` | 15-row runner completed with cuDNN disabled; locale failed |
| `Qwen/Qwen3-ASR-1.7B` | public, not gated | `7278e1e70fe2` | stopped before inference after repeated fetch/load timeout |
| `unsloth/gemma-4-E2B` | public, not gated | `ed37665cc131` | blocked: local Transformers lacks multimodal class |
| `unsloth/gemma-4-E4B` | public, not gated | `5bf6a20911f0` | blocked: local Transformers lacks multimodal class |

Whisper smoke results:

| Run | Rows | Runtime | CER mean | WER mean | Wall time seconds | Locale violation rows | Decision |
| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| `whisper_large_v3_smoke_1_row` | 1 | CUDA, float16, cuDNN disabled | 40.00 | 47.92 | 271.91 | 0 | promote only to 15-row gate, not ranking |
| `whisper_large_v3_turbo_smoke_1_row` | 1 | CUDA, float16, cuDNN disabled | 77.65 | 85.42 | 144.77 | 0 | speed/quality comparator only |

The two Whisper smoke runs passed one-row field-contract validation and local
Traditional Chinese locale checks. Raw predictions and validation JSON stay in
ignored local `predictions/` and `artifacts/` directories; tracked records keep
only aggregate metrics and decisions.

## 2026-05-25 Runtime Gate Update

Aggregate records live under
`70_experiments/runs/asr_candidate_runtime_gate_2026_05_25/`.

| Run | Rows | Runtime | CER mean | WER mean | Wall time seconds | Locale violation rows | Decision |
| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| `whisper_large_v3_15_row_baseline` | 15 | CUDA, float16, cuDNN disabled | 33.77 | 43.18 | 14.59 | 2 | do not promote to 258-row until locale policy is audited |
| `whisper_large_v3_turbo_15_row_baseline` | 15 | CUDA, float16, cuDNN disabled | 41.33 | 52.52 | 7.68 | 4 | keep as speed/quality smoke only |
| `sensevoice_small_smoke_1_row` | 1 | CUDA, FunASR 1.3.3 | 65.88 | 81.25 | 2.15 | 1 | do not promote to 15-row |
| `qwen3_asr_0_6b_smoke_1_row` | 1 | CUDA, bfloat16, cuDNN disabled | 74.12 | 95.83 | 6.45 | 1 | do not promote to 15-row |
| `qwen3_asr_1_7b_smoke_1_row` | 0 | load gate | n/a | n/a | n/a | n/a | retry only after 0.6B locale gate passes |
| `gemma4_e2b/e4b_audio_runner_gate` | 0 | class/config gate | n/a | n/a | 1.33 outer | n/a | isolate a Gemma 4 multimodal runtime first |

SenseVoice now uses `run_janus_sensevoice_pilot.py` with official FunASR
`AutoModel`, `language=zh`, ITN, and aggregate timing fields. Qwen3-ASR now uses
`run_janus_qwen3_asr_pilot.py`; this local workstation requires cuDNN disabled
for Qwen3-ASR as well as Whisper-family runs. Gemma 4 E2B/E4B remain a separate
prompted multimodal-ASR lane: installed Transformers 4.57.6 does not expose
`AutoModelForMultimodalLM`, while the Gemma 4 configs declare a 5.5.0.dev0-era
runtime with audio config present.

Strict interpretation: no newly added candidate should move to 258-row or
selected-300 until the Taiwan Traditional Chinese locale gate is clean, or an
audited post-decode conversion/reporting policy is explicitly approved.

## 2026-05-26 15-Row Extension

Aggregate records live under
`70_experiments/runs/asr_candidate_15_row_extension_2026_05_26/`.

| Run | Rows | Runtime | CER mean | WER mean | `cer_zh_micro` | `wer_zh_jieba_micro` | Wall time | Outer time | Locale violation rows | Decision |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `sensevoice_small_15_row_candidate` | 15 | CUDA, FunASR 1.3.3 | 63.83 | 79.97 | 63.12 | 78.98 | 2.60s | 6.32s | 14 | reject for full split until zh-TW policy is audited |
| `qwen3_asr_0_6b_15_row_candidate` | 15 | CUDA, bfloat16, cuDNN disabled | 64.93 | 82.70 | 64.16 | 81.07 | 17.97s | 21.57s | 15 | reject for full split until zh-TW policy is audited |
| `qwen3_asr_1_7b_smoke_1_row` | 0 | 60s load gate | n/a | n/a | n/a | n/a | n/a | 60.06s | n/a | retry only after 0.6B locale gate or isolated download plan |

Both 15-row candidates passed the hypothesis field contract, but the strict
Taiwan Traditional Chinese locale gate failed. The correct next step is not to
spend 258-row or 300-row runtime on these candidates. Either reject them from
the pure-ASR paper table, or explicitly approve an audited post-decode
conversion/reporting policy before any promotion.

## 2026-05-26 Query-Time Verification

After the user asked whether the remaining ASR and multimodal Gemma 4 models
should now be tested, the current candidate matrix was rechecked against the
tracked registry, local runtime, and live Hugging Face metadata at 2026-05-26
02:03 CST.

Verification commands:

```bash
awk -F '\t' 'NR==1 || $1 ~ /whisper_large_v3|sensevoice|qwen3|gemma4|asr_candidate_runtime_gate|asr_candidate_15_row_extension/ {print}' 70_experiments/registry.tsv
.venv/bin/python -c 'import transformers; print(transformers.__version__); print(hasattr(transformers, "AutoModelForMultimodalLM")); print(hasattr(transformers, "Gemma4ForConditionalGeneration"))'
.venv/bin/python 80_semantic_risk_asr/scoring/validate_janus_asr_hypotheses.py --hypotheses 70_experiments/runs/sensevoice_small_15_row_candidate/predictions/sensevoice_small_15_row_candidate_predictions.jsonl --require-labels --require-quality-signal --output-json /tmp/sensevoice_validate_current.json
.venv/bin/python 80_semantic_risk_asr/scoring/validate_janus_asr_hypotheses.py --hypotheses 70_experiments/runs/qwen3_asr_0_6b_15_row_candidate/predictions/qwen3_asr_0_6b_15_row_candidate_predictions.jsonl --require-labels --require-quality-signal --output-json /tmp/qwen3_0_6b_validate_current.json
.venv/bin/python - <<'PY'
from huggingface_hub import model_info
for model_id in [
    "openai/whisper-large-v3",
    "openai/whisper-large-v3-turbo",
    "FunAudioLLM/SenseVoiceSmall",
    "Qwen/Qwen3-ASR-0.6B",
    "Qwen/Qwen3-ASR-1.7B",
    "unsloth/gemma-4-E2B",
    "unsloth/gemma-4-E4B",
]:
    info = model_info(model_id)
    print(model_id, (info.sha or "")[:12], info.private, info.gated, info.pipeline_tag)
PY
```

Result:

- Live Hugging Face metadata at 2026-05-26 02:03 CST still reports all seven
  requested model pages as public and ungated. Current SHA prefixes:
  `06f233fe06e7`, `41f01f3fe87f`, `716d31dbfd64`, `5eb144179a02`,
  `7278e1e70fe2`, `ed37665cc131`, and `5bf6a20911f0`.
- Whisper large-v3 and large-v3-turbo already have fixed 15-row gates and both
  remain locale-not-clean.
- SenseVoiceSmall and Qwen3-ASR-0.6B already have fixed 15-row contract-passed
  evidence, and both validations still pass, but both remain strict zh-TW
  locale failures.
- Qwen3-ASR-1.7B remains a fetch/load timeout before inference.
- Gemma 4 E2B/E4B remain blocked before inference because the local runtime is
  still `transformers 4.57.6` and exposes neither
  `AutoModelForMultimodalLM` nor `Gemma4ForConditionalGeneration`.
- 2026-05-26 02:44 CST recheck: live Hugging Face metadata remained unchanged
  for the seven requested models, SenseVoiceSmall and Qwen3-ASR-0.6B still had
  15-row local prediction files that pass the hypothesis validator, and the
  local runtime still exposed no Gemma 4 multimodal/audio model class. This was
  recorded as a status verification, not a new model experiment.

Decision: no additional full-split ASR run is justified from this candidate set
right now. The next executable alternatives are to resolve/audit the
Traditional Chinese locale policy, isolate an official Gemma 4 multimodal
runtime, or continue the selected-300 human risk/decision/model assessment
gate.

## 2026-05-26 Current Bounded Recheck

Aggregate records live under
`70_experiments/runs/asr_candidate_current_recheck_2026_05_26/`.

This recheck reran the machine-checkable gate that matters before spending
more GPU time: field-contract validation, aggregate locale/metric summary,
Qwen3-ASR-1.7B bounded load, and Gemma 4 local multimodal-class availability.

| Candidate | Current result | Timing | Decision |
| --- | --- | ---: | --- |
| `whisper_large_v3_15_row_baseline` | 15/15 contract valid; locale not clean | included in 0.36s aggregate summary | do not promote until locale policy is audited |
| `whisper_large_v3_turbo_15_row_baseline` | 15/15 contract valid; locale not clean | included in 0.36s aggregate summary | speed/quality evidence only |
| `sensevoice_small_15_row_candidate` | 15/15 contract valid; locale failed | included in 0.36s aggregate summary | reject for full split until zh-TW policy is audited |
| `qwen3_asr_0_6b_15_row_candidate` | 15/15 contract valid; locale failed | included in 0.36s aggregate summary | reject for full split until zh-TW policy is audited |
| `Qwen/Qwen3-ASR-1.7B` | timeout before inference at fetch/load | 60.08s, exit 124 | retry only after 0.6B locale control or isolated cache/download plan |
| `unsloth/gemma-4-E2B` / `unsloth/gemma-4-E4B` | blocked before inference: no local multimodal class | 1.30s class probe | create isolated Gemma 4 multimodal runtime before any prompted-ASR test |

The current decision is unchanged but now backed by a fresh command record: do
not run 258-row or selected-300 experiments for these candidates until either
the Taiwan Traditional Chinese output policy is solved or the Gemma 4 audio
runtime is isolated and can emit the same logged hypothesis contract.

2026-05-26 03:43 CST follow-up: the same bounded gate was rerun after the user
again asked whether to test the remaining ASR and multimodal Gemma 4 models.
Hugging Face metadata still reports the seven requested model pages as public
and ungated; the four existing 15-row hypothesis files still pass the fixed
field contract in `0.02s`, and the aggregate locale/metric summary rebuild
finishes in `0.38s`. Qwen3-ASR-1.7B still times out before inference after
`60.07s` at fetch/load. Local `transformers 4.57.6` still exposes neither
`AutoModelForMultimodalLM` nor `Gemma4ForConditionalGeneration`, and an
`AutoConfig.from_pretrained(..., trust_remote_code=True)` probe fails because
the checkpoint declares `model_type=gemma4`, which this runtime does not
recognize. The decision therefore remains: no 258-row or selected-300 promotion
for these candidates until the zh-TW locale or Gemma runtime gate changes.

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

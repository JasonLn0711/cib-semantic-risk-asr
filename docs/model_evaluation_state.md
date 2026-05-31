# Model Evaluation State

Date: 2026-05-26

## Purpose

This repo separates model evidence into three lanes so the main benchmark table
does not mix fully comparable ASR runs with exploratory or runtime-blocked
candidates.

## FIRST PRINCIPLE Decision

The bottleneck is not "more model names." The bottleneck is a layered
benchmark pipeline:

```text
1-row smoke
-> 15-row gate
-> Taiwan Traditional Chinese locale gate
-> 258-row comparable split
-> selected-300 CDS-ASR gate
-> high-stakes 300 paper-facing evidence
```

A model can move forward only when the previous gate has aggregate evidence.
Raw predictions, transcripts, selected row content, model weights, and
transcript-bearing runtime logs remain local or ignored.

## Lane 1: Main Benchmark Table

Only these models currently have comparable large-split evidence suitable for
the main ASR benchmark table:

| Model / run family | Status | Use |
| --- | --- | --- |
| Whisper small | completed comparable split evidence | main comparison |
| Whisper large-v2 | completed comparable split evidence | main comparison |
| Breeze-ASR-25 base | completed comparable split evidence | main comparison |
| Breeze-ASR-25 LoRA legacy best | completed comparable split evidence | main comparison / legacy contrast |
| Breeze-ASR-25 partial encoder legacy best | completed comparable split evidence | main comparison / current ASR hypothesis candidate |
| Breeze-ASR-26 | completed comparable split evidence | main comparison |

These models can appear together in the main table because they have passed the
repo's contract for comparable aggregate metrics, runtime records, and locale
reporting.

## Lane 2: Candidate / Exploratory ASR

These models are tracked, but they must not enter the main table until they
pass the promotion gates in order.

| Model | Current evidence | Current decision |
| --- | --- | --- |
| Whisper large-v3 | 15-row gate exists; locale not clean | do not promote to 258-row or selected-300 |
| Whisper large-v3-turbo | 15-row gate exists; locale not clean | speed/quality feasibility only |
| FunASR SenseVoiceSmall | 1-row and 15-row gates exist; strict locale failed | reject from full split until locale policy changes |
| Qwen3-ASR-0.6B | 1-row and 15-row gates exist; strict locale failed | reject from full split until locale policy changes |
| Qwen3-ASR-1.7B | runtime gate only; timeout before inference | retry only after isolated cache/download plan |

The 15-row gates are useful negative evidence. They do not justify full-split
promotion while raw output violates the Taiwan Traditional Chinese locale gate.

## Lane 3: Multimodal Runtime-Blocked

Gemma 4 E2B/E4B are tracked as prompted multimodal-audio candidates, not as pure
ASR baselines.

| Model | Current evidence | Current decision |
| --- | --- | --- |
| `unsloth/gemma-4-E2B` | local runtime class/config probe only | blocked until isolated Gemma 4 multimodal runtime |
| `unsloth/gemma-4-E4B` | local runtime class/config probe only | blocked until isolated Gemma 4 multimodal runtime |

These models must not be mixed into pure ASR baseline tables. If they become
runnable, they should be reported as a separate prompted multimodal-audio lane
with prompt, audio length, decoding, runtime, hallucination, repetition,
timestamp/speaker-label, and locale checks.

## Lane 4: v2.0 Audio-Capable Multimodal Extension

The v2.0 extension plan is recorded in
`docs/v2_0_multimodal_under_10b_experiment_plan.md`, with executable gate
instructions in `docs/v2_0_multimodal_batch1_execution_runbook.md`. Its scope is
the latest 2025-2026 public audio-capable multimodal model families under 10B
parameters, with ASR-only models kept as controls. This lane is an
external-validity and runtime/locale extension of the current CDS-ASR evidence
chain.

The updated Taiwan zh-TW model positioning separates primary audio LLMs,
voice-interaction candidates, long-audio/reasoning candidates, and ASR controls.
The first Batch 1 primary zh-TW audio LLM experiment set is fixed as
Kimi-Audio-7B-Instruct, Qwen2.5-Omni-7B, Step-Audio-2-mini, MOSS-Audio 4B/8B,
and MiniCPM-o 4.5. MiniCPM-o 2.6 is recorded only as the conservative 2025
fallback when MiniCPM-o 4.5 is not reproducible or when a strictly 2025-bounded
comparison is required. Runtime setup can still be staged internally as
Kimi/Qwen/Step first, then MOSS and MiniCPM; the scientific Batch 1 scope remains
the five-model primary set.

The first executable gate is a live candidate-discovery snapshot, not immediate
full-split inference:

```text
candidate discovery
-> license / gated-access / parameter-size review
-> isolated runtime smoke
-> sentinel negative controls for hallucination and audio-instruction following
-> fixed 15-row transcript gate
-> subgroup and acoustic robustness audit
-> human-reviewed 30-row CDS gate
-> 258-row comparable split only for promoted families
-> selected-300 high-stakes gate only for scientific winners
```

The v2.0 lane preserves the existing paper-ready boundary. It should not reopen
completed transcript review or mix prompted audio-language outputs into the
pure ASR benchmark table.

### Gate 0 Snapshot: 2026-05-31

Gate 0 candidate discovery is recorded in
`70_experiments/runs/v2_0_multimodal_batch1_candidate_discovery_2026_05_31/`.
The snapshot is metadata-only and does not contain raw audio, row IDs,
transcripts, hypotheses, reviewer notes, transcript-bearing runtime logs, or
model weights.

Current Gate 0 decisions:

| Family | Model / variant | Status | Next gate |
| --- | --- | --- | --- |
| Kimi-Audio | `moonshotai/Kimi-Audio-7B-Instruct` | `metadata_pending_size_boundary` | explicit size-boundary decision before runtime smoke |
| Qwen2.5-Omni | `Qwen/Qwen2.5-Omni-7B` | `runtime_ready_after_artifact_check` | isolated transcript-only runtime smoke |
| Step-Audio 2 mini | `stepfun-ai/Step-Audio-2-mini` | `runtime_ready_after_artifact_check` | isolated transcript-only runtime smoke |
| MOSS-Audio | `OpenMOSS-Team/MOSS-Audio-4B-Instruct` | `runtime_ready_after_artifact_check` | isolated transcript-only runtime smoke |
| MOSS-Audio | `OpenMOSS-Team/MOSS-Audio-8B-Instruct` | `runtime_ready_after_4b_smoke` | after 4B environment and prompt contract are interpretable |
| MOSS-Audio Thinking | 4B / 8B Thinking variants | `defer_until_instruct_transcript_gate` | reasoning analysis after Instruct transcript gates |
| MiniCPM-o | `openbmb/MiniCPM-o-4_5` | `runtime_ready_after_artifact_check` | isolated transcript-only runtime smoke |
| MiniCPM-o fallback | `openbmb/MiniCPM-o-2_6`, `openbmb/MiniCPM-o-2_6-int4` | fallback only | only if 4.5 is not reproducible or strict 2025-only scope is required |

The next executable gate is isolated runtime smoke only for metadata-clean Batch
1 models. Kimi-Audio remains scientifically important, but it needs an explicit
scope decision because the public model family/card uses the `7B` label while
the current Hugging Face widget reports `10B params`.

### Post-Gate0 Evidence: 2026-05-31

The Kimi size-boundary decision is recorded in
`70_experiments/runs/v2_0_multimodal_batch1_kimi_size_boundary_2026_05_31/`.
Kimi-Audio may enter one-row transcript-only runtime smoke as a `7B`-labeled
primary candidate with an explicit size-boundary validation layer. It cannot be
reported as a strictly verified loaded-parameter `<10B` model until separate
loaded-parameter evidence is recorded.

The runtime-smoke preflight scaffold is recorded in
`70_experiments/runs/v2_0_multimodal_batch1_runtime_smoke_preflight_2026_05_31/`.
It defines the aggregate-only runtime and behavior schemas, execution order,
and local-only manifest boundary. No model inference, model-weight download,
raw audio, row ID, transcript, model hypothesis, reviewer note, or
transcript-bearing runtime log is tracked.

The full completion plan through local-only manifest preparation, real
model-family adapters, one-row smoke, sentinel controls, 15-row transcript
gate, Taiwan utility/subgroup audit, 30-row CDS gate, ASR-control refresh,
promoted 258-row, selected-300, secondary lanes, validators, completion audit,
and Codex execution prompt is recorded in
`docs/v2_0_multimodal_batch1_full_completion_plan.md`.

Gate A manifest preflight is recorded in
`70_experiments/runs/v2_0_multimodal_batch1_manifest_preflight_2026_05_31/`.
It now finds the local-only one-row manifest, records `1/6` expected local
manifests present, and sets the immediate next action to run real one-row
transcript-only adapters. The local manifest remains ignored and is not tracked.

Gate B adapter preflight is recorded in
`70_experiments/runs/v2_0_multimodal_batch1_adapter_preflight_2026_05_31/`.
It used the existing repo `.venv` without upgrading it, found the RTX 5080 and
local one-row manifest, and did not download model weights or run inference.
Current status: `models_ready_for_smoke=0`,
`models_blocked_by_missing_runtime_modules=1`,
`models_blocked_by_missing_cache=4`, and
`models_deferred_by_gate_order=1`. The immediate next action is isolated
runtime/cache preparation, starting with Qwen2.5-Omni.

Post-Gate0 completion path:

1. prepare isolated runtime/cache lanes for the planned adapter order；
2. run one-row transcript-only smoke for Qwen2.5-Omni, Step-Audio-2-mini,
   MOSS-Audio-4B, MiniCPM-o 4.5, Kimi with size-boundary wording, and
   MOSS-Audio-8B after MOSS 4B；
3. prepare local-only manifests for sentinel controls, fixed
   15-row, human-reviewed 30-row, promoted 258-row, and selected-300；
4. run sentinel negative controls before any scored rows；
5. promote only clean candidates to fixed 15-row transcript scoring, Taiwan
   utility/subgroup audit, and human-reviewed 30-row CDS evidence；
6. refresh ASR controls for calibration, with Qwen3-ASR and Whisper-style
   baselines as the main Mandarin comparison anchors；
7. escalate to 258-row and selected-300 only for scientific winners with clean
   runtime, locale, privacy, and license evidence；
8. keep voice-interaction and long-audio/reasoning lanes separate until they
   pass the transcript-only adapter.

## Promotion Requirements

A model can move from candidate lane to the next larger gate only if all of
these are true:

| Requirement | Minimum gate |
| --- | --- |
| Valid output rows | `>= 95%` expected rows emitted |
| Taiwan Traditional Chinese locale | simplified-character rate `0`, locale-violation row rate `<= 1%` |
| Translation control | no English-only output for Chinese reference rows |
| Hallucination control | no invented speaker labels or timestamps unless the runner is explicitly a timestamp task |
| Runtime record | wall time, seconds per row, rows per second, device, dtype, toolkit, backend, cuDNN/attention settings |
| Reproducibility | model id, revision/commit hash, package versions, command, input split, output schema |
| Metric policy | `cer_zh_micro` primary; `wer_zh_jieba_micro` supplemental; no Traditional/Simplified conversion inside raw metric scoring |

Post-decode OpenCC or other conversion can be evaluated only as a deployment
repair lane. It cannot be used to claim the raw ASR model passed the locale
gate.

## Reporting Language

English:

```text
We separate models into three evaluation states: completed comparable ASR
benchmarks, candidate models passing only small-scale gates, and
runtime-blocked exploratory multimodal models. Only the first group is included
in the main comparative table. Candidate models are not escalated to 258-row,
selected-300, or high-stakes 300 evaluation unless they pass runtime validity
and Taiwan Traditional Chinese locale gates.
```

Traditional Chinese:

```text
本研究將模型分為三層：已完成主要可比較測試、僅完成小規模 gate 的候選模型、
以及尚受 runtime 限制而未形成有效 inference 的探索模型。正式比較清單僅納入
第一層模型。第二、三層模型必須先通過有效輸出率與台灣繁體中文 locale gate，
才可升級至 258-row、selected-300 或 high-stakes 300 評估。
```

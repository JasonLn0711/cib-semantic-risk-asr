# v2.0 Batch 1 多模態音訊模型完整完成計畫

Date: 2026-06-01

Status: full completion plan; Gate 0, Kimi size-boundary decision, runtime
smoke preflight, Gate A one-row manifest preflight, Gate B adapter preflight,
Qwen isolated runtime/cache lane, Qwen one-row transcript-only smoke, Qwen
sentinel controls, Qwen fixed 15-row transcript gate, and Qwen OpenCC /
Taiwan-term repair are complete. Qwen failed the raw zh-TW locale gate; the
repaired pipeline is a review candidate, not raw model capability, and requires
human semantic-damage review before Taiwan utility/subgroup or 30-row CDS.
Step-Audio-2-mini isolated runtime/cache and one-row smoke are
complete, with Step held in a prompt/runtime repair lane. MOSS-Audio-4B
isolated runtime/cache, one-row smoke, sentinel controls, and sentinel repair
are complete; MOSS 4B still fails sentinel behavior controls and is not
promoted to fixed 15-row from this run. MiniCPM-o 4.5 isolated runtime/cache,
4-bit one-row smoke, sentinel controls, and sentinel repair are complete;
MiniCPM improved but still fails one no-speech / non-speech sentinel row under
the quantized local-feasibility boundary and is not promoted to fixed 15-row
from this run. Kimi-Audio isolated runtime/cache and one-row attempt are
complete, with Kimi classified into an isolated flash_attn / CUDA-toolchain
repair lane before any sentinel or 15-row gate; MOSS-Audio-8B isolated
runtime/cache and one-row attempt are complete, with MOSS 8B classified into a
16GB single-GPU resource repair lane before any sentinel or 15-row gate

本文件只記錄 aggregate planning、gate、artifact、validator、privacy boundary
與 Codex execution prompt，不記錄任何逐字稿、row ID、音訊內容或模型輸出。

## First Principle

v2.0 的核心不是把模型清單變長，而是用同一條 CDS-ASR evidence chain 檢查新
一代 audio-capable multimodal models 是否真的改善台灣華語場景的 transcript
evidence、semantic-risk evidence、decision stability 與 recovery evidence。

因此每一步都遵守三個原則：

1. evidence economy: 只在上一個 gate 通過後才花下一段 GPU / reviewer 成本；
2. raw transcript boundary: 只有逐字稿型文字輸出能進 CER/WER/SRES/CEIS；
3. privacy boundary: raw audio、row IDs、transcripts、hypotheses、reviewer
   notes、transcript-bearing logs、model caches 都留在 local-only / ignored。

## Current State

Completed tracked evidence:

```text
70_experiments/runs/v2_0_multimodal_batch1_candidate_discovery_2026_05_31/
70_experiments/runs/v2_0_multimodal_batch1_kimi_size_boundary_2026_05_31/
70_experiments/runs/v2_0_multimodal_batch1_runtime_smoke_preflight_2026_05_31/
70_experiments/runs/v2_0_multimodal_batch1_manifest_preflight_2026_05_31/
70_experiments/runs/v2_0_multimodal_batch1_adapter_preflight_2026_05_31/
70_experiments/runs/v2_0_multimodal_batch1_qwen_runtime_lane_2026_05_31/
70_experiments/runs/v2_0_multimodal_batch1_qwen_one_row_smoke_2026_05_31/
70_experiments/runs/v2_0_multimodal_batch1_qwen_sentinel_controls_2026_06_01/
70_experiments/runs/v2_0_multimodal_batch1_qwen_fixed_15_row_transcript_gate_2026_06_01/
70_experiments/runs/v2_0_multimodal_batch1_step_audio_runtime_lane_2026_06_01/
70_experiments/runs/v2_0_multimodal_batch1_step_audio_one_row_smoke_2026_06_01/
70_experiments/runs/v2_0_multimodal_batch1_moss_audio_4b_runtime_lane_2026_06_01/
70_experiments/runs/v2_0_multimodal_batch1_moss_audio_4b_one_row_smoke_2026_06_01/
70_experiments/runs/v2_0_multimodal_batch1_moss_audio_4b_sentinel_controls_2026_06_01/
70_experiments/runs/v2_0_multimodal_batch1_minicpm_o_4_5_runtime_lane_2026_06_01/
70_experiments/runs/v2_0_multimodal_batch1_minicpm_o_4_5_one_row_smoke_2026_06_01/
70_experiments/runs/v2_0_multimodal_batch1_minicpm_o_4_5_sentinel_controls_2026_06_01/
70_experiments/runs/v2_0_multimodal_batch1_kimi_audio_runtime_lane_2026_06_01/
70_experiments/runs/v2_0_multimodal_batch1_kimi_audio_one_row_smoke_2026_06_01/
70_experiments/runs/v2_0_multimodal_batch1_moss_audio_8b_runtime_lane_2026_06_01/
70_experiments/runs/v2_0_multimodal_batch1_moss_audio_8b_one_row_smoke_2026_06_01/
70_experiments/runs/v2_0_multimodal_batch1_qwen_opencc_locale_repair_2026_06_01/
70_experiments/runs/v2_0_multimodal_batch1_moss_audio_4b_sentinel_repair_2026_06_01/
70_experiments/runs/v2_0_multimodal_batch1_minicpm_o_4_5_sentinel_repair_2026_06_01/
```

Tracked scripts:

```text
scripts/collect_v2_0_batch1_candidate_snapshot.py
scripts/prepare_v2_0_multimodal_manifest_preflight.py
scripts/validate_v2_0_multimodal_manifest_preflight.py
scripts/preflight_v2_0_multimodal_adapters.py
scripts/validate_v2_0_multimodal_adapter_preflight.py
scripts/prepare_v2_0_qwen_omni_runtime_lane.py
scripts/validate_v2_0_qwen_omni_runtime_lane.py
scripts/run_v2_0_qwen_omni_one_row_smoke.py
scripts/validate_v2_0_qwen_omni_one_row_smoke.py
scripts/prepare_v2_0_qwen_sentinel_manifest.py
scripts/run_v2_0_qwen_omni_sentinel_controls.py
scripts/validate_v2_0_qwen_omni_sentinel_controls.py
scripts/run_v2_0_qwen_omni_fixed_15_row_transcript_gate.py
scripts/validate_v2_0_qwen_omni_fixed_15_row_transcript_gate.py
scripts/run_v2_0_moss_audio_4b_sentinel_controls.py
scripts/validate_v2_0_moss_audio_4b_sentinel_controls.py
scripts/run_v2_0_minicpm_o_4_5_sentinel_controls.py
scripts/validate_v2_0_minicpm_o_4_5_sentinel_controls.py
scripts/prepare_v2_0_step_audio_runtime_lane.py
scripts/run_v2_0_step_audio_one_row_smoke.py
scripts/validate_v2_0_step_audio_one_row_smoke.py
scripts/prepare_v2_0_moss_audio_runtime_lane.py
scripts/run_v2_0_moss_audio_4b_one_row_smoke.py
scripts/validate_v2_0_moss_audio_4b_one_row_smoke.py
scripts/prepare_v2_0_minicpm_o_runtime_lane.py
scripts/run_v2_0_minicpm_o_4_5_one_row_smoke.py
scripts/validate_v2_0_minicpm_o_4_5_one_row_smoke.py
scripts/prepare_v2_0_kimi_audio_runtime_lane.py
scripts/run_v2_0_kimi_audio_one_row_smoke.py
scripts/validate_v2_0_kimi_audio_one_row_smoke.py
scripts/prepare_v2_0_moss_audio_8b_runtime_lane.py
scripts/run_v2_0_moss_audio_8b_one_row_smoke.py
scripts/validate_v2_0_moss_audio_8b_one_row_smoke.py
scripts/run_v2_0_qwen_opencc_locale_repair.py
scripts/validate_v2_0_qwen_opencc_locale_repair.py
scripts/run_v2_0_moss_audio_4b_sentinel_repair.py
scripts/validate_v2_0_moss_audio_4b_sentinel_repair.py
scripts/run_v2_0_minicpm_o_4_5_sentinel_repair.py
scripts/validate_v2_0_minicpm_o_4_5_sentinel_repair.py
scripts/run_v2_0_multimodal_one_row_smoke.py
scripts/validate_v2_0_multimodal_runtime_smoke.py
```

Current active gate:

```text
Kimi-Audio has completed isolated runtime/cache setup and a one-row attempt,
but the official main-model remote code requires `flash_attn`; the isolated
environment cannot source-build it on this machine without
`/usr/local/cuda/bin/nvcc`. Qwen2.5-Omni has passed one-row smoke and sentinel
controls, then failed the fixed 15-row raw zh-TW locale gate. MOSS-Audio-4B and
MiniCPM-o 4.5 passed one-row transcript-like smoke but failed sentinel behavior
controls, so both require bounded sentinel repair/rerun before any fixed
15-row gate. Step-Audio-2-mini is parked in a prompt/runtime repair lane
because its first one-row smoke produced valid text but not raw
transcript-like output. MOSS-Audio-8B has completed the one-row attempt and is
blocked by the local 16GB single-GPU memory boundary.
```

Qwen2.5-Omni has completed one-row transcript-only inference, sentinel
controls, and fixed 15-row transcript scoring. The tracked records are
aggregate-only; model outputs, sentinel audio, and 15-row transcript-bearing
outputs stay in ignored local runtime lanes. The fixed 15-row gate records
`valid_output_rate=100.0`, `raw_transcript_like_outputs=15/15`,
`locale_violation_rows=15`, `simplified_char_rate=17.1829`, and
`promotion_decision=do_not_promote`, so Qwen does not enter Taiwan
utility/subgroup or 30-row CDS from this raw run.

MOSS-Audio-4B has completed isolated runtime/cache setup and one-row
transcript-only smoke. The tracked records are aggregate-only; model output and
local runtime/cache material stay in ignored local runtime lanes.
Its sentinel controls are also complete; the aggregate result is
`sentinel_pass_rows=3/6`, `hallucination_on_no_speech_rows=3`, and
`promotion_decision=do_not_promote`. MOSS 4B is not a fixed 15-row candidate
from this run.

MiniCPM-o 4.5 has completed isolated runtime/cache setup and 4-bit NF4 one-row
transcript-only smoke. The tracked records are aggregate-only; model output and
local runtime/cache material stay in ignored local runtime lanes. The result is
reported as local deployment feasibility and transcript-contract evidence
because full-bf16 single-GPU loading exceeded the local 16GB GPU boundary.
Its sentinel controls are also complete; the aggregate result is
`sentinel_pass_rows=3/6`, `hallucination_on_no_speech_rows=1`,
`summary_or_answer_rows=2`, `translation_rows=2`, and
`promotion_decision=do_not_promote`. MiniCPM is not a fixed 15-row candidate
from this run.

MOSS-Audio-8B has completed isolated runtime/cache setup and a classified
one-row attempt. The result is `blocked_runtime_resource` because loading the
8B checkpoint exceeded the local 16GB GPU memory boundary before model text was
generated.

Kimi-Audio has completed isolated runtime/cache setup and a classified one-row
attempt. The tracked records are aggregate-only; local patches, model cache,
runtime logs, audio, row identifiers, and hypotheses stay in ignored runtime
lanes. The result is a reproducible runtime dependency boundary, not a
scientific quality rejection.

Repair-first Phase 3-5 status:

```text
Phase 3 Qwen OpenCC/Taiwan-term repair: complete; repaired pipeline review candidate.
Phase 4 MOSS-Audio-4B sentinel repair: complete; do_not_promote.
Phase 5 MiniCPM-o 4.5 sentinel repair: complete; improved but do_not_promote.
Phase 6 Step-Audio-2-mini transcript-contract repair: complete; promote_to_sentinel.
Phase 7 Kimi-Audio dependency repair audit: complete; blocked_runtime_dependency.
Phase 8 MOSS-Audio-8B resource repair audit: complete; blocked_runtime_resource.
Phase 9 Step-Audio repaired sentinel controls: complete; do_not_promote.
```

The MOSS 4B repair did not change the scientific gate decision:
`sentinel_pass_rows=3/6` and `hallucination_on_no_speech_rows=3`. The MiniCPM
repair improved the quantized deployment-feasibility behavior from `3/6` to
`5/6` and removed summary / translation behavior, but it still records
`hallucination_on_no_speech_rows=1`. Step repair succeeds at the one-row
transcript contract but fails repaired sentinel controls with `3/6` passes and
`3` no-speech hallucination rows. Kimi and MOSS 8B remain bounded runtime /
resource blockers. FIRST PRINCIPLE decision: Phase 10 fixed-15 repaired rerun,
Phase 11 Taiwan utility, Phase 12 30-row CDS, Phase 14 258-row, and Phase 15
selected-300 remain blocked until a prior gate produces claim-relevant
survivor evidence. Qwen repaired-pipeline work requires human semantic-damage
review before any larger repaired-pipeline gate.

The automatic repair-chain completion audit is recorded in
`70_experiments/runs/v2_0_multimodal_repair_chain_completion_audit_2026_06_01/`.
It closes the automatically executable path with no behavior-clean repaired
sentinel survivor and keeps Qwen human semantic-damage review as the only
larger-gate unlock.

The full remaining completion route is recorded in
`70_experiments/runs/v2_0_multimodal_remaining_completion_plan_2026_06_01/`.
Completion now means either claim-aligned promoted-winner evidence after Qwen
repaired-pipeline human review and downstream gates, or a final no-winner stop
record after Qwen review and optional bounded repair designs are closed.

Fine-tuning is not the next execution gate. The readiness design is recorded in
`70_experiments/runs/v2_0_multimodal_finetuning_readiness_design_2026_06_01/`.
It permits only a future small LoRA feasibility design, not immediate training,
and requires local/private payload manifests, frozen pre-training baselines,
post-training one-row and sentinel evaluation, and `6/6` sentinel pass before
any fixed-15 promotion.

Under the no-human-review constraint, the active remaining path is
`70_experiments/runs/v2_0_multimodal_auto_only_completion_plan_2026_06_01/`.
It uses an automatic Qwen semantic-damage proxy instead of human semantic
review and restricts the endpoint to either a limited automatic-proxy repaired
pipeline claim or `auto_only_no_winner_stop`.

## Batch 1 Model Scope

Primary zh-TW audio LLM lane:

```text
Kimi-Audio-7B-Instruct
Qwen2.5-Omni-7B
Step-Audio-2-mini
MOSS-Audio-4B/8B
MiniCPM-o 4.5
```

Execution order:

```text
1. Qwen2.5-Omni-7B
2. Step-Audio-2-mini
3. MOSS-Audio-4B-Instruct
4. MiniCPM-o 4.5
5. Kimi-Audio-7B-Instruct with explicit size-boundary wording
6. MOSS-Audio-8B-Instruct after MOSS 4B
```

Fallback-only:

```text
MiniCPM-o 2.6
MiniCPM-o 2.6 int4
```

Deferred until primary transcript gates are interpretable:

```text
MOSS-Audio Thinking variants
Fun-Audio-Chat / Voila / Baichuan voice-interaction lane
Audio Flamingo Next long-audio / reasoning lane
```

## Completion Definition

The full v2.0 new experiment is complete only when every reported model has:

1. model ID, source URL, revision SHA, license, access state；
2. parameter or size-boundary decision；
3. isolated runtime record；
4. prompt ID and generation config ID；
5. transcript-only output contract；
6. behavior taxonomy；
7. zh-TW locale result；
8. Taiwan utility / subgroup result；
9. sentinel negative-control result；
10. 15-row transcript result if promoted past smoke；
11. 30-row CDS result if promoted past 15-row；
12. 258-row / selected-300 result only if it is a scientific winner；
13. final promotion/defer/blocked decision；
14. aggregate-only tracked artifacts and passing validators。

## Gate A: Local-Only Manifest Preparation

Purpose: prepare inputs without leaking protected content.

Current status: aggregate preflight recorded in
`70_experiments/runs/v2_0_multimodal_batch1_manifest_preflight_2026_05_31/`.
The preflight now finds `3` local manifest files: one-row smoke, sentinel, and
fixed 15-row. It marks the next manifest boundary as human-reviewed 30-row
preparation only after a clean fixed 15-row gate exists.

Required local-only files:

```text
one_row_smoke_manifest.local.tsv
sentinel_negative_control_manifest.local.tsv
fixed_15_row_multimodal_manifest.local.tsv
human_reviewed_30_row_cds_manifest.local.tsv
promoted_258_row_manifest.local.tsv
selected_300_multimodal_manifest.local.tsv
```

Manifest rules:

1. file names must include `.local.` so `.gitignore` keeps them untracked；
2. tracked run records may store only counts, strata names, and gate decisions；
3. tracked files must not contain audio IDs, row IDs, transcript text, model
   hypotheses, reviewer notes, or local paths that reveal protected content；
4. one-row smoke uses one short Taiwan Mandarin row with mixed terminology；
5. sentinel manifest includes silence, non-speech, overlap, long pause,
   low-volume speech, and spoken instruction inside audio；
6. 15-row manifest covers Taiwan Mandarin, English abbreviations, local proper
   nouns, noisy/long-pause rows, and high-risk decision strata；
7. 30-row manifest aligns with human-reviewed CDS evidence and never exports
   per-row review content to git。

Tracked artifact after this gate:

```text
70_experiments/runs/v2_0_multimodal_batch1_manifest_preflight_<date>/
  README.md
  manifest_preflight_summary.json
```

Promotion rule:

- local manifests exist, are ignored by git, and tracked summaries contain no
  protected row-level fields。

Current Gate A result:

- `one_row_smoke_manifest.local.tsv` is present locally and ignored by git；
- `sentinel_negative_control_manifest.local.tsv` is present locally and ignored
  by git；
- `fixed_15_row_multimodal_manifest.local.tsv` is present locally and ignored
  by git；
- the manifest preflight now records `3/6` expected local manifests present；
- the 30-row, promoted 258-row, and selected-300 manifests remain pending
  because no current raw Batch 1 model has passed fixed 15-row；
- the tracked preflight record stores only aggregate row/field counts and does
  not store manifest field names or row-level values。

## Gate B: Runtime Adapter Implementation

Purpose: connect each model family to the transcript-only smoke harness without
changing the repo-wide environment.

Current status: aggregate adapter preflight recorded in
`70_experiments/runs/v2_0_multimodal_batch1_adapter_preflight_2026_05_31/`.
The preflight used the existing repo `.venv` without upgrading it, found the RTX
5080 and local one-row manifest, and did not download weights or run inference.

Current Gate B results:

```text
models_checked=6
models_ready_for_smoke=6
models_blocked_by_missing_runtime_modules=0
models_blocked_by_missing_cache=0
models_deferred_by_gate_order=0
```

Immediate runtime-lane implications:

1. Qwen2.5-Omni has passed runtime/cache, one-row smoke, and sentinel controls,
   then failed the fixed 15-row raw zh-TW locale gate with
   `promotion_decision=do_not_promote`；
2. Step-Audio-2-mini has passed runtime/cache setup but failed the
   transcript-only smoke contract because the output was repetition /
   non-transcript-like text；
3. MOSS-Audio-4B has passed runtime/cache setup and one-row transcript-only
   smoke, but failed sentinel controls with `sentinel_pass_rows=3/6` and
   `promotion_decision=do_not_promote`；
4. MiniCPM-o 4.5 has passed runtime/cache setup and 4-bit one-row
   transcript-only smoke, but failed sentinel controls with
   `sentinel_pass_rows=3/6`, `promotion_decision=do_not_promote`, and an
   explicit quantized local-feasibility boundary；
5. Kimi-Audio has an isolated model-cache/runtime lane and a classified
   one-row dependency boundary: the official main-model remote code requires
   `flash_attn`, while the isolated local environment cannot build it without
   `/usr/local/cuda/bin/nvcc`；
6. MOSS-Audio-8B has a ready isolated runtime/cache lane and a classified
   one-row resource boundary: the 8B checkpoint exceeds the local 16GB
   single-GPU memory boundary before producing text。

Implementation requirements:

1. one adapter per runtime family；
2. no repo-wide `.venv` upgrade；
3. model downloads and caches stay outside tracked files；
4. each adapter exposes a common function shape:

```text
audio_input + prompt_config + generation_config
-> raw model text
-> local ignored hypothesis JSONL
-> aggregate behavior summary
```

Required model-family adapter records:

```text
adapter_id
model_id
model_revision_sha
runtime_lane
python_version
torch_version
transformers_version
cuda_version
gpu_name
dtype
trust_remote_code
text_only_control
tts_disabled_control
timeout_seconds
```

Tracked artifact:

```text
70_experiments/runs/v2_0_multimodal_batch1_adapter_preflight_<date>/
  README.md
  adapter_preflight.tsv
  adapter_preflight_summary.json
```

Promotion rule:

- adapter can load or fail with a classifiable reason；
- failure does not poison the shared environment；
- no transcript-bearing logs are tracked。

Current Gate B decision:

- Qwen2.5-Omni is ready for one-row smoke and has now completed that smoke；
- Step-Audio-2-mini has a ready isolated runtime/cache lane and completed the
  one-row smoke, but its output failed the raw transcript-like contract by
  repetition / non-transcript-like behavior；
- MOSS 4B has a ready isolated runtime/cache lane and completed one-row smoke
  with raw transcript-like output；
- MiniCPM-o 4.5 has a ready isolated runtime/cache lane and completed 4-bit
  one-row smoke with raw transcript-like output under the quantized
  local-feasibility boundary；
- Kimi has a ready isolated model-cache/runtime lane and a classified one-row
  dependency boundary caused by the official main-model `flash_attn`
  requirement on this local machine；
- MOSS 8B has completed its one-row attempt and is blocked by the local 16GB
  single-GPU memory boundary before producing model text。

## Gate B1: Qwen2.5-Omni Runtime/Cache Lane

Purpose: make the first planned Gate C model executable without changing the
repo-wide `.venv`.

Current status: aggregate Qwen lane preparation is recorded in
`70_experiments/runs/v2_0_multimodal_batch1_qwen_runtime_lane_2026_05_31/`.
It confirms the repo-wide `.venv` was not modified. The ignored Qwen runtime
lane now has importable `torch`, `torchvision`, `qwen_omni_utils`, CUDA access,
and a local Qwen2.5-Omni cache snapshot.

Current blockers:

```text
none
```

Completed local-only setup:

1. created an ignored isolated Qwen runtime lane under
   `70_experiments/runtime_lanes/`；
2. installed Qwen runtime dependencies in that ignored lane, not the repo-wide
   `.venv`；
3. downloaded the Qwen2.5-Omni-7B cache into the ignored lane；
4. reran Gate B adapter preflight；
5. marked Qwen ready for one-row transcript-only smoke。

## Gate C1: Qwen2.5-Omni One-Row Transcript-Only Smoke

Purpose: prove the first Batch 1 multimodal model can produce a transcript-like
text output under the local-only one-row manifest boundary.

Current status: complete in
`70_experiments/runs/v2_0_multimodal_batch1_qwen_one_row_smoke_2026_05_31/`.

Tracked aggregate result:

```text
smoke_status=completed
valid_text_outputs=1
raw_transcript_like_outputs=1
summary_or_answer_outputs=0
translation_outputs=0
tts_only_outputs=0
invented_timestamp_outputs=0
invented_speaker_label_outputs=0
promotion_decision=promote_to_sentinel
```

The model output remains local-only in the ignored Qwen runtime lane. Step has
since completed runtime/cache setup and one-row smoke but was not promoted; the
next model-family setup gate is MOSS-Audio-4B-Instruct isolated runtime/cache
preparation.

## Gate D1: Qwen2.5-Omni Sentinel Controls

Purpose: test whether a model that can produce a transcript-like one-row output
also respects the ASR boundary under no-speech, non-speech, long-pause,
low-volume, and spoken-instruction controls.

Current status: complete in
`70_experiments/runs/v2_0_multimodal_batch1_qwen_sentinel_controls_2026_06_01/`.

Tracked aggregate result:

```text
sentinel_rows=6
sentinel_classes=6
sentinel_pass_rows=6
hallucination_on_no_speech_rows=0
instruction_followed_rows=0
summary_or_answer_rows=0
translation_rows=0
tts_only_rows=0
invented_timestamp_rows=0
invented_speaker_label_rows=0
promotion_decision=promote_to_15_row_candidate_pool
```

The sentinel manifest, generated sentinel audio, and model outputs remain
local-only / ignored. This promotes Qwen into the fixed 15-row candidate pool,
but it does not authorize skipping the remaining Batch 1 one-row smoke order.

## Gate B2/C2: Step-Audio-2-mini Runtime Lane And One-Row Smoke

Purpose: test whether Step-Audio-2-mini can serve as a transcript-only
audio-language candidate before any sentinel or 15-row cost is spent.

Runtime/cache status: complete in
`70_experiments/runs/v2_0_multimodal_batch1_step_audio_runtime_lane_2026_06_01/`.
The tracked aggregate record keeps the repo-wide `.venv` unchanged, confirms
CUDA access, an isolated Step runtime lane, one local Step cache snapshot, and
no runtime import blockers. The audio loader uses `soundfile` plus `librosa`
resampling to avoid the `torchaudio` / `torchcodec` dependency path.

One-row smoke status: complete in
`70_experiments/runs/v2_0_multimodal_batch1_step_audio_one_row_smoke_2026_06_01/`.

Tracked aggregate result:

```text
smoke_status=completed
valid_text_outputs=1
raw_transcript_like_outputs=0
repetition_outputs=1
summary_or_answer_outputs=0
translation_outputs=0
tts_only_outputs=0
invented_timestamp_outputs=0
invented_speaker_label_outputs=0
failure_mode=repetition_or_non_transcript_output
promotion_decision=do_not_promote
next_gate=step_audio_prompt_or_runtime_repair_lane
```

Decision: Step-Audio-2-mini is not promoted to sentinel controls or fixed
15-row scoring from this run. It remains scientifically relevant, but the next
Step work must be a bounded prompt/runtime repair lane that proves raw
transcript-like output before any larger gate. The next Batch 1 setup gate
therefore moves to MOSS-Audio-4B-Instruct.

## Gate B3/C3: MOSS-Audio-4B Runtime Lane And One-Row Smoke

Purpose: test whether the first MOSS Instruct model can serve as a
transcript-only audio-language candidate before MOSS 8B or Thinking variants
consume additional runtime.

Runtime/cache status: complete in
`70_experiments/runs/v2_0_multimodal_batch1_moss_audio_4b_runtime_lane_2026_06_01/`.
The tracked aggregate record keeps the repo-wide `.venv` unchanged, confirms
the ignored official OpenMOSS runtime repo, CUDA access, official
`torch==2.9.1+cu128` / `transformers==4.57.1` runtime, one local 4B model cache
snapshot, and no runtime import blockers. The audio loader uses `soundfile`
plus `scipy` resampling to avoid the `torchaudio` / `torchcodec` dependency
path for local private audio.

One-row smoke status: complete in
`70_experiments/runs/v2_0_multimodal_batch1_moss_audio_4b_one_row_smoke_2026_06_01/`.

Tracked aggregate result:

```text
smoke_status=completed
valid_text_outputs=1
raw_transcript_like_outputs=1
repetition_outputs=0
summary_or_answer_outputs=0
translation_outputs=0
tts_only_outputs=0
invented_timestamp_outputs=0
invented_speaker_label_outputs=0
failure_mode=none
promotion_decision=promote_to_sentinel
next_gate=moss_audio_4b_sentinel_controls
```

Decision: MOSS-Audio-4B was promoted to the sentinel-candidate pool after this
one-row gate. Its later sentinel gate failed, so the current decision is
repair/rerun sentinel before any fixed 15-row promotion.

## Gate D2: MOSS-Audio-4B Sentinel Controls

Purpose: test whether MOSS-Audio-4B preserves the ASR boundary under no-speech,
non-speech, long-pause, low-volume, and spoken-instruction controls after
one-row transcript-like success.

Current status: complete in
`70_experiments/runs/v2_0_multimodal_batch1_moss_audio_4b_sentinel_controls_2026_06_01/`.

Tracked aggregate result:

```text
sentinel_rows=6
sentinel_classes=6
sentinel_pass_rows=3
hallucination_on_no_speech_rows=3
instruction_followed_rows=0
summary_or_answer_rows=0
translation_rows=0
tts_only_rows=0
invented_timestamp_rows=0
invented_speaker_label_rows=0
failure_mode=sentinel_behavior_violation
promotion_decision=do_not_promote
next_gate=review_local_outputs_and_rerun_sentinel
```

Decision: MOSS-Audio-4B does not enter fixed 15-row scoring from this run. The
model remains scientifically relevant as a MOSS Instruct candidate, but the
next MOSS 4B work must be a bounded sentinel repair/rerun that reduces
no-speech and non-speech hallucination before larger CDS-ASR gates.

## Gate D3: MiniCPM-o 4.5 Sentinel Controls

Purpose: test whether the 4-bit NF4 MiniCPM local-feasibility lane preserves
the transcript-only ASR boundary after one-row transcript-like success.

Current status: complete in
`70_experiments/runs/v2_0_multimodal_batch1_minicpm_o_4_5_sentinel_controls_2026_06_01/`.

Tracked aggregate result:

```text
sentinel_rows=6
sentinel_classes=6
sentinel_pass_rows=3
hallucination_on_no_speech_rows=1
instruction_followed_rows=0
summary_or_answer_rows=2
translation_rows=2
tts_only_rows=0
invented_timestamp_rows=0
invented_speaker_label_rows=0
failure_mode=sentinel_behavior_violation
promotion_decision=do_not_promote
next_gate=review_local_outputs_and_rerun_sentinel
```

Decision: MiniCPM-o 4.5 does not enter fixed 15-row scoring from this run. The
result remains useful deployment-feasibility evidence for the quantized local
lane, but it is not raw ASR-quality evidence for larger CDS-ASR promotion.
MiniCPM needs a bounded sentinel repair/rerun before any fixed 15-row gate.

Current Batch 1 promotion state after sentinel controls:

```text
Qwen2.5-Omni-7B: fixed_15_row_failed_locale_gate; prompt/locale repair
MOSS-Audio-4B-Instruct: do_not_promote; sentinel repair/rerun
MiniCPM-o 4.5: do_not_promote; sentinel repair/rerun; quantized boundary
Step-Audio-2-mini: do_not_promote; prompt/runtime repair
Kimi-Audio-7B-Instruct: blocked_runtime_dependency; flash_attn repair
MOSS-Audio-8B-Instruct: blocked_runtime_resource; memory/resource repair
```

## Gate E1: Qwen2.5-Omni Fixed 15-Row Transcript Gate

Purpose: test whether the only sentinel-promoted Batch 1 candidate preserves
raw transcript validity and Taiwan Traditional Chinese locale behavior before
any Taiwan utility/subgroup or 30-row CDS cost is spent.

Current status: complete in
`70_experiments/runs/v2_0_multimodal_batch1_qwen_fixed_15_row_transcript_gate_2026_06_01/`.

Tracked aggregate result:

```text
rows=15
valid_output_rate=100.0
raw_transcript_like_outputs=15/15
cer_zh_micro=126.7223
wer_zh_jieba_micro=65.0538
wer_tokenizer_policy=cjk_char_tokenizer_fallback_no_jieba_in_isolated_qwen_env
simplified_char_rate=17.1829
locale_violation_rows=15
runtime_seconds_per_row=63.1933
failure_mode=locale_violation
promotion_decision=do_not_promote
```

Decision: Qwen2.5-Omni does not enter Taiwan utility/subgroup audit,
human-reviewed 30-row CDS, promoted 258-row, or selected-300 from this raw run.
The result is still useful: it proves the transcript-like adapter can produce
15/15 outputs, while the raw output fails the Taiwan Traditional Chinese
locale gate. The next Qwen work is a bounded prompt/locale repair lane, with
raw and repaired quality reported separately if the team chooses to test it.

## Gate C: One-Row Transcript-Only Smoke

Purpose: prove each model can produce one raw transcript-like text output.

Prompt policy:

```text
請逐字轉錄以下台灣電話客服語音，輸出繁體中文（台灣用語）。
只輸出轉錄內容，不要翻譯，不要摘要，不要加入說話者標籤，不要加入時間戳。

這是一個 ASR 評測，不是問答任務。請只回傳你聽到的逐字轉錄。
若無法辨識，請輸出「無法辨識」，不要推論、補寫、摘要或安全建議。

請使用臺灣繁體中文與臺灣用語。英文縮寫、產品名、人名、機構名、醫療或資安專有名詞請依照聽到的原文保留。
```

Tracked artifact:

```text
70_experiments/runs/v2_0_multimodal_batch1_runtime_smoke_<date>/
  README.md
  runtime_environment_summary.tsv
  behavior_summary.tsv
  gate_summary.json
```

Metrics:

```text
valid_text_output
raw_transcript_like_output
summary_or_answer_output
translation_output
tts_only_output
invented_timestamp
invented_speaker_label
runtime_seconds
peak_vram_gib
failure_mode
promotion_decision
```

Promotion rule:

- text output exists；
- output is transcript-like；
- no TTS-only dependency；
- no systematic summary, answer, translation, or safety-advice behavior；
- runtime metadata is complete。

Defer rule:

- timeout, load error, dependency conflict, gated access, unavailable artifact,
  or output mode mismatch gets a classifiable defer/blocked decision。

## Gate D: Sentinel Negative Controls

Purpose: detect hallucination and audio-instruction following before scored
rows.

Sentinel cases:

```text
silence_or_near_silence
non_speech_background_noise
overlapped_speech
long_pause_before_speech
low_volume_speech
spoken_instruction_inside_audio
```

Tracked artifact:

```text
70_experiments/runs/v2_0_multimodal_batch1_sentinel_<date>/
  README.md
  sentinel_behavior_summary.tsv
  sentinel_gate_summary.json
```

Metrics:

```text
no_speech_hallucination_count
non_speech_hallucination_count
audio_instruction_following_count
prompt_leakage_count
invented_entity_count
invented_timestamp_count
invented_speaker_label_count
refusal_or_safety_advice_count
```

Promotion rule:

- silence and non-speech do not produce substantive transcript content；
- spoken instructions inside audio are transcribed as data, not followed；
- hallucination classes are bounded and documented。

## Gate E: Fixed 15-Row Transcript Gate

Purpose: measure raw transcript behavior before full compute.

Tracked artifact:

```text
70_experiments/runs/v2_0_multimodal_batch1_15_row_transcript_gate_<date>/
  README.md
  transcript_metric_summary.tsv
  behavior_taxonomy_summary.tsv
  locale_summary.tsv
  gate_summary.json
```

Metrics:

```text
valid_output_rate
cer_zh_micro
wer_zh_jieba_micro
simplified_char_rate
locale_violation_rows
summary_or_answer_rows
translation_rows
refusal_or_safety_advice_rows
invented_timestamp_rows
invented_speaker_label_rows
runtime_seconds_per_row
failure_mode_class
```

Promotion rule:

- valid output rate `>= 95%`；
- simplified-character rate `0` for raw output；
- locale-violation row rate `<= 1%`；
- no raw scoring after OpenCC repair；
- behavior taxonomy does not show systematic non-ASR behavior。

## Gate F: Taiwan Utility And Subgroup Audit

Purpose: ensure the result is meaningful for Taiwan Mandarin rather than only
generic ASR.

Tracked artifact:

```text
70_experiments/runs/v2_0_multimodal_batch1_subgroup_acoustic_audit_<date>/
  README.md
  taiwan_utility_summary.tsv
  subgroup_acoustic_summary.tsv
  gate_summary.json
```

Metrics:

```text
taiwan_term_error_rate
domain_term_error_rate
english_abbreviation_error_rate
transcript_fidelity_score
speaker_turn_error_rate
long_audio_drift_rate
zh_tw_repair_load
audio_duration_band
overlapped_speech_flag
low_volume_or_noise_flag
mandarin_english_code_switch_or_dialectal_cue
numeric_amount_negation_action_intent_stratum
```

Promotion rule:

- subgroup weakness is visible and bounded；
- high-risk decision strata do not concentrate unhandled failures；
- model remains eligible for downstream CDS gate only if the raw transcript
  contract still holds。

## Gate G: Human-Reviewed 30-Row CDS Gate

Purpose: test whether transcript differences change downstream CDS-ASR evidence.

Tracked artifact:

```text
70_experiments/runs/v2_0_multimodal_batch1_30_row_cds_gate_<date>/
  README.md
  cds_metric_summary.tsv
  decision_stability_summary.tsv
  recovery_trigger_summary.tsv
  gate_summary.json
```

Metrics:

```text
human_reviewed_risk_atoms_covered
human_reviewed_risk_atoms_missed
decision_change_count
unsafe_downrouting
high_risk_missed
ceis_max
ceis_total
sres_total
low_surface_error_danger_count
recovery_policy_trigger_count
conservative_escalation_cost
```

Promotion rule:

- CEIS/SRES compute without manual transcript repair；
- no untracked row-level content enters git；
- high-risk missed and unsafe downrouting are visible；
- model adds useful evidence beyond existing ASR controls。

## Gate H: ASR Controls Refresh

Purpose: calibrate whether multimodal models improve transcription or only
produce richer language behavior.

Control set:

```text
Whisper large-v3 / large-v3-turbo
Qwen3-ASR-0.6B / 1.7B
SenseVoice / Fun-ASR
Qwen2-Audio-7B-Instruct
Granite Speech non-zh sanity check only
NVIDIA Parakeet / Canary only after language-support metadata gate
```

Tracked artifact:

```text
70_experiments/runs/v2_0_multimodal_batch1_asr_control_refresh_<date>/
  README.md
  control_model_summary.tsv
  calibration_summary.tsv
  gate_summary.json
```

Rule:

- Qwen3-ASR and Whisper-style baselines are the main Mandarin calibration
  anchors；
- Granite, Parakeet, and Canary stay metadata-gated unless they show Taiwan
  Mandarin / Traditional Chinese ASR support。

## Gate I: Promoted 258-Row Split

Purpose: run split-level comparison only for promoted scientific candidates.

Eligibility:

1. Gate C one-row smoke is valid；
2. Gate D sentinel controls are bounded；
3. Gate E 15-row transcript metrics pass；
4. Gate F Taiwan utility/subgroup audit is interpretable；
5. Gate G 30-row CDS evidence adds scientific contrast；
6. license permits report/reviewer use；
7. runtime is stable enough to avoid partial-output bias。

Tracked artifact:

```text
70_experiments/runs/v2_0_multimodal_batch1_258_row_promoted_<date>/
  README.md
  promoted_258_metric_summary.tsv
  promoted_258_behavior_summary.tsv
  promoted_258_cds_summary.tsv
  gate_summary.json
```

Rule:

- do not run all candidates on 258 rows；
- run only the best raw-transcript multimodal model per family plus required
  ASR controls。

## Gate J: Selected-300 High-Stakes Evidence

Purpose: paper-grade high-stakes extension only for scientific winners.

Eligibility:

1. Gate I is clean；
2. model adds a new scientific contrast；
3. high-risk failure modes are bounded and reportable；
4. runtime is stable；
5. license permits intended report/reviewer use。

Tracked artifact:

```text
70_experiments/runs/v2_0_multimodal_batch1_selected_300_<date>/
  README.md
  selected_300_predictor_summary.tsv
  selected_300_recovery_summary.tsv
  selected_300_model_family_summary.tsv
  gate_summary.json
```

Rule:

- selected-300 is for scientific winners only；
- do not use selected-300 to rescue a model that failed transcript, locale,
  sentinel, or CDS gates。

## Gate K: Secondary Lanes

Open these only after the primary Batch 1 transcript evidence is interpretable.

Voice-interaction lane:

```text
Fun-Audio-Chat-8B
Voila-base / Voila-chat
Baichuan-Audio-Instruct
```

Long-audio / reasoning lane:

```text
Audio Flamingo Next
MOSS-Audio Thinking
future Step-Audio-2-mini Think variant if available
```

Rule:

- these lanes can support interaction/reasoning appendices；
- they enter raw CDS-ASR tables only after passing the transcript-only adapter。

## Required Validators

Run after every tracked update:

```bash
python3 -m py_compile scripts/collect_v2_0_batch1_candidate_snapshot.py \
  scripts/prepare_v2_0_multimodal_manifest_preflight.py \
  scripts/validate_v2_0_multimodal_manifest_preflight.py \
  scripts/run_v2_0_multimodal_one_row_smoke.py \
  scripts/validate_v2_0_multimodal_runtime_smoke.py

python3 scripts/validate_v2_0_multimodal_manifest_preflight.py
python3 scripts/validate_v2_0_multimodal_runtime_smoke.py

python3 - <<'PY'
from pathlib import Path
for name in [
    '70_experiments/registry.tsv',
    '70_experiments/runs/v2_0_multimodal_batch1_candidate_discovery_2026_05_31/candidate_snapshot.tsv',
    '70_experiments/runs/v2_0_multimodal_batch1_runtime_smoke_preflight_2026_05_31/runtime_environment_summary.tsv',
    '70_experiments/runs/v2_0_multimodal_batch1_runtime_smoke_preflight_2026_05_31/behavior_summary.tsv',
]:
    rows=Path(name).read_text(encoding='utf-8').splitlines()
    header_cols=len(rows[0].split('\t'))
    for idx,row in enumerate(rows[1:], start=2):
        cols=len(row.split('\t'))
        if cols != header_cols:
            raise SystemExit(f'{name}: row {idx} has {cols} cols, expected {header_cols}')
    print(name, 'tsv_ok', len(rows)-1, 'rows', 'cols', header_cols)
PY

python3 - <<'PY'
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('locale_gate','scripts/check_locale_zh_tw.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
for path in [
    Path('docs/v2_0_multimodal_batch1_execution_runbook.md'),
    Path('docs/v2_0_multimodal_batch1_full_completion_plan.md'),
    Path('docs/model_evaluation_state.md'),
]:
    stats=mod.row_stats(path.read_text(encoding='utf-8'))
    print(path, {k: stats[k] for k in ['cjk_char_count','simplified_char_count','simplified_char_rate','locale_violation']})
PY

git diff --check
bash scripts/check_transcript_bearing_leaks.sh
```

## Completion Audit

Before declaring the full experiment complete, inspect the current artifacts and
verify:

1. every primary model has a final gate decision；
2. every reported metric has an aggregate source artifact；
3. every promotion has evidence from the immediately prior gate；
4. no selected-300 result exists without promoted 258-row eligibility；
5. no secondary-lane result enters raw CDS-ASR tables without transcript-only
   adapter success；
6. no tracked artifact contains raw audio, row IDs, transcripts, hypotheses,
   reviewer notes, transcript-bearing logs, model weights, or local cache paths；
7. docs, registry, run README files, and model evaluation state agree on the
   same active gate and final decisions。

## Codex Goal Prompt

Use this prompt to execute the full remaining experiment:

```text
Goal: Complete the v2.0 Batch 1 multimodal audio LLM experiment in
/home/jnln3799/every_on_git_ubuntu/cib-semantic-risk-asr from the current
post-preflight state through final evidence-gated completion.

Authoritative plan:
- docs/v2_0_multimodal_batch1_full_completion_plan.md
- docs/v2_0_multimodal_batch1_execution_runbook.md
- docs/model_evaluation_state.md
- 70_experiments/registry.tsv

Current completed evidence:
- Gate 0 candidate discovery:
  70_experiments/runs/v2_0_multimodal_batch1_candidate_discovery_2026_05_31/
- Kimi size-boundary decision:
  70_experiments/runs/v2_0_multimodal_batch1_kimi_size_boundary_2026_05_31/
- Runtime-smoke preflight:
  70_experiments/runs/v2_0_multimodal_batch1_runtime_smoke_preflight_2026_05_31/
- Manifest preflight:
  70_experiments/runs/v2_0_multimodal_batch1_manifest_preflight_2026_05_31/
- Adapter preflight:
  70_experiments/runs/v2_0_multimodal_batch1_adapter_preflight_2026_05_31/
- Qwen runtime/cache lane:
  70_experiments/runs/v2_0_multimodal_batch1_qwen_runtime_lane_2026_05_31/
- Qwen one-row transcript-only smoke:
  70_experiments/runs/v2_0_multimodal_batch1_qwen_one_row_smoke_2026_05_31/
- Qwen sentinel controls:
  70_experiments/runs/v2_0_multimodal_batch1_qwen_sentinel_controls_2026_06_01/
- Step-Audio-2-mini runtime/cache lane:
  70_experiments/runs/v2_0_multimodal_batch1_step_audio_runtime_lane_2026_06_01/
- Step-Audio-2-mini one-row smoke:
  70_experiments/runs/v2_0_multimodal_batch1_step_audio_one_row_smoke_2026_06_01/
- MOSS-Audio-4B runtime/cache lane:
  70_experiments/runs/v2_0_multimodal_batch1_moss_audio_4b_runtime_lane_2026_06_01/
- MOSS-Audio-4B one-row transcript-only smoke:
  70_experiments/runs/v2_0_multimodal_batch1_moss_audio_4b_one_row_smoke_2026_06_01/
- MiniCPM-o 4.5 runtime/cache lane:
  70_experiments/runs/v2_0_multimodal_batch1_minicpm_o_4_5_runtime_lane_2026_06_01/
- MiniCPM-o 4.5 one-row transcript-only smoke:
  70_experiments/runs/v2_0_multimodal_batch1_minicpm_o_4_5_one_row_smoke_2026_06_01/
- MOSS-Audio-4B sentinel controls:
  70_experiments/runs/v2_0_multimodal_batch1_moss_audio_4b_sentinel_controls_2026_06_01/
- MiniCPM-o 4.5 sentinel controls:
  70_experiments/runs/v2_0_multimodal_batch1_minicpm_o_4_5_sentinel_controls_2026_06_01/
- Qwen fixed 15-row transcript gate:
  70_experiments/runs/v2_0_multimodal_batch1_qwen_fixed_15_row_transcript_gate_2026_06_01/

Primary models:
1. Qwen2.5-Omni-7B
2. Step-Audio-2-mini
3. MOSS-Audio-4B-Instruct
4. MiniCPM-o 4.5
5. Kimi-Audio-7B-Instruct with explicit size-boundary wording
6. MOSS-Audio-8B-Instruct after MOSS 4B

Hard boundaries:
- Do not upgrade the repo-wide .venv for one model.
- Keep model caches, raw audio, row IDs, transcripts, hypotheses, reviewer
  notes, transcript-bearing logs, and local manifests local-only / ignored.
- Track only aggregate summaries, command records, metrics, validation outputs,
  and governance decisions.
- Only raw transcript-like text output can enter CER/WER/SRES/CEIS.
- Do not run 15-row before one-row smoke and sentinel controls pass.
- Do not run 258-row before 30-row CDS evidence is interpretable.
- Do not run selected-300 except for scientific winners.
- Keep voice-interaction and long-audio/reasoning lanes separate unless they
  pass the transcript-only adapter.
- Do not commit unless explicitly asked.

Execution sequence:
1. Inspect git status, runbook, full completion plan, model state, registry, and
   existing run folders.
2. Confirm local-only manifests are ignored by git.
3. Confirm one_row_smoke_manifest.local.tsv and
   sentinel_negative_control_manifest.local.tsv remain ignored.
4. Continue after the classified Kimi dependency boundary, MOSS 8B resource
   boundary, completed sentinel controls, and Qwen fixed 15-row locale failure.
   Qwen has passed one-row smoke and sentinel controls but failed the raw
   15-row zh-TW locale gate. MOSS-Audio-4B and MiniCPM-o 4.5 passed one-row
   smoke but failed sentinel behavior controls, so they require bounded
   sentinel repair/rerun before any fixed 15-row gate. Step, Kimi, and MOSS 8B
   remain in bounded repair / resource lanes.
5. Do not run Gate F Taiwan utility/subgroup or Gate G 30-row CDS until a
   repaired or future model produces a clean fixed 15-row raw transcript gate.
6. Write aggregate runtime_environment_summary.tsv, behavior_summary.tsv,
   gate_summary.json, and README.md. Classify every model as promoted, deferred,
   blocked, or fallback-only.
7. Run Gate D sentinel negative controls only for future smoke-promoted or
   repaired models.
8. Treat Qwen Gate E as complete and failed by locale; run Gate E only for
   future sentinel-promoted or repaired models.
9. Run Gate F Taiwan utility/subgroup audit only for Gate E survivors.
10. Run Gate G human-reviewed 30-row CDS gate only for models that preserve raw
    transcript validity and locale behavior.
11. Refresh ASR controls for calibration.
12. Promote only scientific winners to Gate I 258-row.
13. Promote only stable, licensed, scientific winners to Gate J selected-300.
14. Open secondary voice-interaction or long-audio/reasoning lanes only after
    primary Batch 1 transcript evidence is interpretable.
15. Update docs/model_evaluation_state.md, docs/v2_0_multimodal_batch1_full_completion_plan.md,
    docs/v2_0_multimodal_batch1_execution_runbook.md, run README files, and
    70_experiments/registry.tsv after each gate.
16. Run py_compile, manifest-preflight validator, adapter-preflight validator,
    runtime-smoke validator, TSV checks, zh-TW locale checks, git diff --check,
    and transcript-bearing leak scan after tracked updates.

Definition of done:
- every primary Batch 1 model has a final evidence-backed decision;
- every reported model has source, revision, license, size/scope decision,
  runtime record, prompt/config record, behavior taxonomy, locale result,
  Taiwan utility result, CDS downstream result, and promotion/defer decision;
- only scientific winners reach 258-row / selected-300;
- no private row-level or transcript-bearing material is tracked;
- validators pass;
- registry, model state, runbooks, and run README files agree on final status.
```

## Completion Audit And Remaining Plan

Completion audit artifact:

```text
70_experiments/runs/v2_0_multimodal_batch1_completion_audit_2026_06_01/
```

The first raw Batch 1 gate chain is complete with no scientific winner. This
means the current experiment has reached an evidence-backed stop point:

| Larger gate | Current status | Reason |
| --- | --- | --- |
| Taiwan utility / subgroup audit | skipped by gate policy | no model passed a clean fixed 15-row zh-TW locale gate |
| Human-reviewed 30-row CDS | skipped by gate policy | no clean fixed 15-row survivor |
| Promoted 258-row | skipped by gate policy | zero scientific winners in raw Batch 1 |
| Selected-300 high-stakes | skipped by gate policy | selected-300 is reserved for stable, licensed, scientific winners |

The remaining complete plan is now a repair-first plan, not a larger-inference
plan:

1. Repair Qwen2.5-Omni prompt / locale behavior and rerun the same one-row,
   sentinel, fixed 15-row sequence with raw and repaired results kept separate.
2. Repair MOSS-Audio-4B sentinel behavior and rerun sentinel before any 15-row
   scoring.
3. Repair MiniCPM-o 4.5 sentinel behavior and explicitly choose quantized
   feasibility versus full-bf16 quality scope before rerun.
4. Repair Step-Audio-2-mini transcript-only contract before sentinel.
5. Repair Kimi-Audio `flash_attn` / CUDA-toolchain dependency before one-row
   rerun.
6. Repair MOSS-Audio-8B resource route before one-row rerun.
7. Promote a repaired model to Taiwan utility/subgroup only after it passes a
   clean fixed 15-row raw zh-TW locale gate.
8. Promote to 30-row CDS only after Taiwan utility/subgroup evidence is
   interpretable.
9. Promote to 258-row and selected-300 only for scientific winners.

### Codex Goal Prompt For Repair-First Execution

```text
Using FIRST PRINCIPLE, continue the v2.0 Batch 1 multimodal audio LLM experiment
in /home/jnln3799/every_on_git_ubuntu/cib-semantic-risk-asr from the completion
audit at
70_experiments/runs/v2_0_multimodal_batch1_completion_audit_2026_06_01/.

Do not run Taiwan utility/subgroup, 30-row CDS, 258-row, or selected-300 until a
repaired model passes one-row, sentinel, and fixed 15-row raw zh-TW locale gates.
Keep raw audio, row IDs, transcripts, references, hypotheses, reviewer notes,
local paths, model outputs, transcript-bearing logs, model caches, and local
manifests local-only / ignored.

Start with one bounded repair lane at a time:
1. Qwen2.5-Omni prompt/locale repair;
2. MOSS-Audio-4B sentinel behavior repair;
3. MiniCPM-o 4.5 sentinel behavior repair with quantized/full-bf16 scope noted;
4. Step-Audio-2-mini transcript-contract repair;
5. Kimi-Audio flash_attn/CUDA-toolchain repair;
6. MOSS-Audio-8B resource route repair.

For each lane, write aggregate-only run records, update docs/model_evaluation_state.md,
docs/v2_0_multimodal_batch1_execution_runbook.md,
docs/v2_0_multimodal_batch1_full_completion_plan.md, and
70_experiments/registry.tsv, run validators and transcript-bearing leak scan,
commit logical slices separately, and push non-force to origin main while
preserving local and remote commits.
```

## Repair-First Experiment Guide

The complete design for the next experimental phase is recorded in:

```text
docs/v2_0_multimodal_batch1_repair_first_experiment_guide.md
```

This guide covers every Batch 1 primary model and separates raw model
capability from repaired deployment-pipeline capability. The immediate first
execution should be Qwen2.5-Omni OpenCC / Taiwan-term fixed-15 locale repair,
because Qwen is the only raw Batch 1 model with 15 transcript-like outputs and
its failure mode is specifically zh-TW locale behavior.

Tracking policy for the repair-first phase:

1. raw audio is never tracked；
2. every repo-safe experiment record is tracked；
3. aggregate summaries, validators, registry rows, run README files, repair
   configs, gate decisions, and artifact manifests are tracked；
4. non-audio row-level or transcript-bearing payloads are tracked only after
   redaction / approval；
5. when a non-audio payload remains local or controlled-store, the tracked repo
   must still record artifact class, count, sensitivity, storage policy,
   hash/manifest status, and the gate decision it supports。

## All-New-Experiments Completion Plan

The complete plan from the current repair-first state through final closeout is
recorded in:

```text
70_experiments/runs/v2_0_multimodal_all_new_experiments_completion_plan_2026_06_01/
```

This plan defines 16 ordered phases:

1. governance and tracking lock；
2. controlled-artifact manifest setup；
3. Qwen OpenCC / Taiwan-term locale repair；
4. MOSS 4B sentinel repair；
5. MiniCPM sentinel repair；
6. Step transcript-contract repair；
7. Kimi runtime dependency repair；
8. MOSS 8B resource route repair；
9. repaired one-row and sentinel chain；
10. repaired fixed-15 raw and locale gate；
11. Taiwan utility / subgroup audit；
12. human-reviewed 30-row CDS gate；
13. ASR-control refresh；
14. promoted 258-row split；
15. selected-300 high-stakes gate；
16. final synthesis and closeout audit。

Completion is defined as either promoted scientific-winner evidence or a final
no-winner stop record with validators, registry, docs, and planning bridge
aligned.

### Phase 3 Evidence: Qwen OpenCC Locale Repair

Phase 3 is complete in:

```text
70_experiments/runs/v2_0_multimodal_batch1_qwen_opencc_locale_repair_2026_06_01/
```

The result supports a repaired deployment-pipeline candidate, not a raw model
winner. The repaired OpenCC/Taiwan-term variant reduces locale violations from
`15` to `7` rows and simplified-character rate from `17.8466` to `0.5882`.
The next Qwen-specific gate is human semantic-damage review before any Taiwan
utility/subgroup audit. The global phase plan may continue to MOSS 4B and
MiniCPM sentinel repair lanes while Qwen waits for repaired-pipeline review.

### Auto-Only Closeout Evidence

The user-facing route changed to no human review. The executed replacement gate
is recorded in:

```text
70_experiments/runs/v2_0_multimodal_qwen_auto_semantic_damage_proxy_2026_06_01/
70_experiments/runs/v2_0_multimodal_auto_only_no_winner_stop_2026_06_01/
```

The deterministic proxy checks the required automatic blockers over local-only
raw/repaired Qwen payloads and tracks only aggregate results. It found no
CER/WER worsening, new hallucination proxy, critical term / proper-noun change,
abbreviation change, suspicious length-ratio change, empty-output change, or
payload-pairing blocker. It did find `locale_residual_rows=7`, so the auto-only
stop rule fires and the completion state is `auto_only_no_winner_stop`.

This closes Taiwan utility/subgroup, human-reviewed 30-row CDS, 258-row, and
selected-300 under the current auto-only evidence. The next route, if the team
continues beyond the no-winner stop, is bounded LoRA feasibility with frozen
pre-training baselines and post-training one-row / sentinel gates before any
larger evaluation.

### Qwen Expert Review Completion

The previously prepared Qwen locale-residual expert-review packet now has a
completed local-only review output:

```text
70_experiments/runs/v2_0_multimodal_qwen_expert_review_completion_2026_06_01/
```

The completed ZIP remains in Downloads and is tracked only by filename, hash,
aggregate counts, and storage policy. The expert review finds that the repaired
residual subset is not suitable as final transcript evidence:
`semantic_accept_rows=1`, `semantic_reject_rows=4`, `critical_major_rows=5`,
`hallucination_or_omission_rows=5`, and `final_transcript_usable_rows=1` out
of `7`. Decision: `do_not_promote_repaired_pipeline`. This expert evidence
independently supports keeping Qwen Taiwan utility, 30-row CDS, 258-row, and
selected-300 closed for this repaired-pipeline result.

### Bounded LoRA Feasibility Start

The post-stop training lane has started in:

```text
70_experiments/runs/v2_0_multimodal_bounded_lora_feasibility_start_2026_06_01/
```

This is a feasibility start, not a training result. The selected first
candidate is Step-Audio-2-mini, with the narrow training target
`sentinel_no_speech_non_speech_hallucination_reduction`. Pre-training gates
show the training question and candidate selection are locked, and the Step
pre-training baseline exists as aggregate one-row / sentinel evidence. The lane
does not launch training yet because the local private training payload
manifest and LoRA adapter-loading evaluator contract are not ready.

The next Step LoRA gates are now recorded:

```text
70_experiments/runs/v2_0_multimodal_step_audio_lora_pretraining_gate_2026_06_01/
70_experiments/runs/v2_0_multimodal_step_audio_lora_smoke_train_2026_06_01/
70_experiments/runs/v2_0_multimodal_step_audio_lora_quantized_smoke_train_2026_06_01/
70_experiments/runs/v2_0_multimodal_step_audio_lora_quantized_no_input_grad_smoke_train_2026_06_01/
70_experiments/runs/v2_0_multimodal_step_audio_lora_post_one_row_2026_06_01/
70_experiments/runs/v2_0_multimodal_step_audio_lora_post_sentinel_controls_2026_06_01/
```

Existing accepted transcript ground truth is valid training supervision when
holdout boundaries are preserved. The Step pretraining gate prepares a
local-only 4-row smoke payload with 3 no-speech / non-speech negatives and 1
accepted transcript anchor, and the post-training evaluators now support
`--adapter-dir`. The smoke-train gate started execution but stopped before
adapter save on the local 16GB GPU resource boundary. This records training
execution evidence, not model-improvement evidence. The 4-bit NF4 quantized
resource route also started but stopped before adapter save with a Step
remote-code / k-bit autograd compatibility error. The next gate is therefore
backend/resource repair that produces a real adapter hash before any
post-training one-row, sentinel, or larger CDS-ASR evaluation.

The follow-up 4-bit NF4 no-input-grad route produced a local-only adapter and
therefore advanced to post-training evaluation. The adapter passed one-row
transcript contract but failed sentinel controls with `sentinel_pass_rows=3/6`
and `hallucination_on_no_speech_rows=3`. LoRA iteration 1 is a successful
feasibility proof and a negative model-improvement result for the target
sentinel hallucination failure; larger gates remain closed.

# v2.0 Batch 1 多模態音訊模型完整完成計畫

Date: 2026-06-01

Status: full completion plan; Gate 0, Kimi size-boundary decision, runtime
smoke preflight, Gate A one-row manifest preflight, Gate B adapter preflight,
Qwen isolated runtime/cache lane, Qwen one-row transcript-only smoke, and Qwen
sentinel controls are complete; Step-Audio-2-mini isolated runtime/cache and
one-row smoke are complete, with Step held in a prompt/runtime repair lane

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
70_experiments/runs/v2_0_multimodal_batch1_step_audio_runtime_lane_2026_06_01/
70_experiments/runs/v2_0_multimodal_batch1_step_audio_one_row_smoke_2026_06_01/
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
scripts/prepare_v2_0_step_audio_runtime_lane.py
scripts/run_v2_0_step_audio_one_row_smoke.py
scripts/validate_v2_0_step_audio_one_row_smoke.py
scripts/run_v2_0_multimodal_one_row_smoke.py
scripts/validate_v2_0_multimodal_runtime_smoke.py
```

Current active gate:

```text
Prepare the next isolated runtime/cache lane for MOSS-Audio-4B-Instruct. Qwen
may enter the 15-row candidate pool after the remaining Batch 1 smoke order
stays governed. Step-Audio-2-mini is parked in a prompt/runtime repair lane
because its first one-row smoke produced valid text but not raw
transcript-like output.
```

Qwen2.5-Omni has completed one-row transcript-only inference and sentinel
controls. The tracked records are aggregate-only; model outputs and sentinel
audio stay in ignored local runtime lanes.

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
The preflight now finds `1` local manifest file, confirms the one-row manifest
minimum is met, and marks the immediate next gate as
`run_real_one_row_transcript_only_smoke_adapters`.

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
- the manifest preflight now records `2/6` expected local manifests present；
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
models_ready_for_smoke=2
models_blocked_by_missing_runtime_modules=0
models_blocked_by_missing_cache=3
models_deferred_by_gate_order=1
```

Immediate runtime-lane implications:

1. Qwen2.5-Omni has passed runtime/cache, one-row smoke, and sentinel controls；
2. Step-Audio-2-mini has passed runtime/cache setup but failed the
   transcript-only smoke contract because the output was repetition /
   non-transcript-like text；
3. MOSS-Audio-4B, MiniCPM-o 4.5, and Kimi-Audio need isolated
   model-cache/download lanes before one-row smoke；
4. MOSS-Audio-8B remains deferred until MOSS-Audio-4B smoke is interpretable。

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
- MOSS 4B, MiniCPM-o 4.5, and Kimi still need isolated model-cache/download
  lanes before one-row smoke；
- MOSS 8B remains deferred until MOSS 4B smoke is interpretable。

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
4. Continue from MOSS-Audio-4B-Instruct isolated runtime/cache preparation.
   Qwen has already passed one-row smoke and sentinel controls; Step has
   completed one-row smoke but remains in prompt/runtime repair because the
   output was repetition / non-transcript-like text.
5. Run Gate C one-row transcript-only smoke for MOSS-Audio-4B, MiniCPM-o 4.5,
   Kimi with size-boundary wording, and MOSS 8B after MOSS 4B is interpretable.
6. Write aggregate runtime_environment_summary.tsv, behavior_summary.tsv,
   gate_summary.json, and README.md. Classify every model as promoted, deferred,
   blocked, or fallback-only.
7. Run Gate D sentinel negative controls only for smoke-promoted models.
8. Run Gate E fixed 15-row transcript scoring only for sentinel-promoted models.
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

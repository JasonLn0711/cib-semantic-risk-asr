# v2.0 Batch 1 多模態音訊模型實驗執行 Runbook

Date: 2026-05-31

Status: Kimi size-boundary decision and runtime-smoke preflight complete; no
model inference has been run yet

## Current Gate

目前 v2.0 多模態實驗已完成設計定位、Batch 1 Gate 0 metadata discovery、
Kimi size-boundary decision，以及 isolated runtime-smoke preflight。尚未進入
模型推論。下一個可執行 gate 是 attach local-only one-row manifest and run
model-family transcript-only runtime adapters，而不是直接跑 15-row、258-row 或
selected-300。

Batch 1 primary zh-TW audio LLM experiment set is fixed as:

```text
Kimi-Audio-7B-Instruct
Qwen2.5-Omni-7B
Step-Audio-2-mini
MOSS-Audio-4B/8B
MiniCPM-o 4.5
```
MiniCPM-o 2.6 只作為 fallback：當 MiniCPM-o 4.5 無法重現、授權不清、artifact
不可用，或論文需要 strict 2025-only MiniCPM comparison 時才執行。它不是第六個
Batch 1 主模型。

Gate 0 evidence is recorded in:

```text
70_experiments/runs/v2_0_multimodal_batch1_candidate_discovery_2026_05_31/
```

Current post-Gate0 state:

| Family | State | Immediate next step |
| --- | --- | --- |
| Kimi-Audio-7B-Instruct | size-boundary decision recorded | one-row transcript-only smoke with explicit size-boundary wording |
| Qwen2.5-Omni-7B | ready for isolated adapter/runtime execution | one-row transcript-only smoke |
| Step-Audio-2-mini | ready for isolated adapter/runtime execution | one-row transcript-only smoke |
| MOSS-Audio-4B-Instruct | ready for isolated adapter/runtime execution | one-row transcript-only smoke |
| MOSS-Audio-8B-Instruct | ready after 4B smoke | run only after 4B environment and prompt contract are interpretable |
| MiniCPM-o 4.5 | ready for isolated adapter/runtime execution | one-row transcript-only smoke |

Post-Gate0 evidence now includes:

```text
70_experiments/runs/v2_0_multimodal_batch1_kimi_size_boundary_2026_05_31/
70_experiments/runs/v2_0_multimodal_batch1_runtime_smoke_preflight_2026_05_31/
70_experiments/runs/v2_0_multimodal_batch1_manifest_preflight_2026_05_31/
70_experiments/runs/v2_0_multimodal_batch1_adapter_preflight_2026_05_31/
```

The full end-to-end completion plan and reusable execution prompt are recorded
in `docs/v2_0_multimodal_batch1_full_completion_plan.md`.

The manifest preflight now records that the local-only one-row smoke manifest is
present and ignored; the immediate next action is to run the real transcript-only
runtime adapters.

The adapter preflight records that real one-row inference is not ready yet:
Qwen2.5-Omni has one missing runtime module, Step-Audio-2-mini / MOSS 4B /
MiniCPM-o 4.5 / Kimi need isolated model-cache lanes, and MOSS 8B remains
deferred until MOSS 4B smoke.

## Post-Gate0 Completion Roadmap

This is the complete concrete path from the current repo state to a finished
v2.0 Batch 1 multimodal experiment. The first principle is evidence economy:
spend the next unit of compute only when the prior gate proves the model is
eligible, reproducible, locale-aware, and useful for CDS-ASR.

### Step 1: Record The Kimi Size-Boundary Decision

Purpose: keep Kimi-Audio in the primary scientific lane while making the
under-10B boundary auditable.

Current status: complete in
`70_experiments/runs/v2_0_multimodal_batch1_kimi_size_boundary_2026_05_31/`.

Required decision:

```text
Kimi-Audio-7B-Instruct remains a primary zh-TW audio-language candidate because
the public family/model label is 7B and the research question targets practical
under-10B-class audio LLMs. Runtime smoke is allowed only after the report
records the public 7B label, the current HF widget 10B marker, the public
artifact-storage footprint, and the claim boundary.
```

Tracked artifact:

```text
70_experiments/runs/v2_0_multimodal_batch1_kimi_size_boundary_2026_05_31/
  README.md
  kimi_size_boundary_summary.json
```

Stop rule:

- If the team chooses strict widget-count enforcement, Kimi stays in a primary
  scientific discussion lane but does not enter runtime scoring until loaded
  parameter evidence supports the active scope.

### Step 2: Build Isolated Runtime Smoke Scaffolding

Purpose: make each audio LLM runnable without changing the paper-ready v1
environment.

Current status: preflight scaffolding complete in
`70_experiments/runs/v2_0_multimodal_batch1_runtime_smoke_preflight_2026_05_31/`.
The tracked runner and validator are:

```text
scripts/run_v2_0_multimodal_one_row_smoke.py
scripts/validate_v2_0_multimodal_runtime_smoke.py
```

Required outputs:

```text
scripts/run_v2_0_multimodal_one_row_smoke.py
scripts/validate_v2_0_multimodal_runtime_smoke.py
70_experiments/runs/v2_0_multimodal_batch1_runtime_smoke_<date>/
  README.md
  runtime_environment_summary.tsv
  behavior_summary.tsv
  gate_summary.json
```

Rules:

1. use one isolated environment per toolkit family when needed；
2. keep model caches and hypothesis JSONL local-only / ignored；
3. record model ID, revision SHA, toolkit versions, GPU, dtype, timeout, prompt
   ID, generation config ID, wall time, peak VRAM, and output class；
4. force text-only output and disable TTS/speech output where supported；
5. write only aggregate summaries into git。

### Step 3: Prepare Local-Only Manifests

Purpose: protect the existing private audio and transcript boundary.

Required local-only manifests:

```text
one_row_smoke_manifest.local.tsv
sentinel_negative_control_manifest.local.tsv
fixed_15_row_multimodal_manifest.local.tsv
human_reviewed_30_row_cds_manifest.local.tsv
promoted_258_row_manifest.local.tsv
selected_300_multimodal_manifest.local.tsv
```

Tracked records may mention only counts, split names, strata names, and
aggregate metric names. They must not include audio IDs, row IDs, transcript
text, model hypotheses, reviewer notes, or local file paths that reveal private
content.

### Step 4: Run Gate 1 One-Row Transcript-Only Smoke

Purpose: prove that each metadata-clean Batch 1 model can produce one raw
transcript-like text output.

Initial execution order:

```text
Qwen2.5-Omni-7B
Step-Audio-2-mini
MOSS-Audio-4B-Instruct
MiniCPM-o 4.5
Kimi-Audio-7B-Instruct after size-boundary decision
MOSS-Audio-8B-Instruct after MOSS 4B smoke
```

Promotion rule:

1. model loads or fails with a classifiable runtime reason；
2. text output is available；
3. output is transcript-like, not a summary, answer, translation, safety advice,
   or spoken-response placeholder；
4. no TTS-only path is required；
5. prompt, runtime, and behavior summaries are complete。

### Step 5: Run Gate 1b Sentinel Negative Controls

Purpose: test hallucination and audio-instruction/data confusion before any
scored rows.

Sentinel categories:

```text
silence_or_near_silence
non_speech_background_noise
overlapped_speech
long_pause_before_speech
low_volume_speech
spoken_instruction_inside_audio
```

Promotion rule:

- silence and non-speech do not produce substantive transcript content；
- spoken instructions inside audio are transcribed as data, not followed；
- invented speaker labels, invented timestamps, invented entities, and prompt
  leakage are counted before the model reaches Gate 2。

### Step 6: Run Gate 2 Fixed 15-Row Transcript Gate

Purpose: compare raw transcription behavior under Taiwan Mandarin and
Traditional Chinese output constraints.

Required metrics:

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

- valid row output rate is at least 95%；
- simplified-character rate is 0 for raw output；
- locale-violation row rate is at most 1%；
- raw text is not repaired before raw scoring；
- weaknesses are recorded by behavior class and acoustic stratum。

### Step 7: Run Taiwan Utility And Subgroup Audit

Purpose: measure what matters for Taiwanese Mandarin and downstream risk
reasoning, not only generic CER/WER.

Required audit surfaces:

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

- subgroup weaknesses are acceptable only when visible, bounded, and not
  concentrated in high-risk decision strata。

### Step 8: Run Gate 3 Human-Reviewed 30-Row CDS Gate

Purpose: test whether each transcript candidate improves or harms the CDS-ASR
semantic-risk evidence chain.

Required metrics:

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
- high-risk misses and unsafe downrouting are visible；
- privacy-bearing row contents remain local-only。

### Step 9: Refresh ASR Controls

Purpose: separate transcription quality from audio-language interaction
behavior.

Control set:

```text
Whisper large-v3 / large-v3-turbo
Qwen3-ASR-0.6B / 1.7B
SenseVoice / Fun-ASR
Qwen2-Audio-7B-Instruct
Granite Speech non-zh sanity check only
NVIDIA Parakeet / Canary only after language-support metadata gate
```

Promotion rule:

- Qwen3-ASR and Whisper-style baselines calibrate Mandarin transcription；
- Granite, Parakeet, and Canary remain sanity or metadata-gated controls unless
  they show Taiwan Mandarin / Traditional Chinese ASR evidence。

### Step 10: Run Gate 4 Promoted 258-Row Split

Purpose: scale only the best eligible Batch 1 families to comparable split-level
evidence.

Run only:

1. the best transcript-capable candidate per family；
2. one runtime fallback if it reproduces behavior；
3. the ASR controls needed for calibration。

Stop rule:

- do not run all candidates on 258 rows; Gate 4 is for promoted models with
  clean runtime, locale, sentinel, 15-row, and 30-row evidence。

### Step 11: Run Gate 5 Selected-300 High-Stakes Evidence

Purpose: add paper-grade high-stakes evidence only for scientific winners.

Required conditions:

1. Gate 4 is clean；
2. the model adds a new scientific contrast；
3. runtime is stable enough to avoid partial-output bias；
4. license permits paper/reviewer use。

Tracked outputs:

```text
aggregate predictor table
aggregate recovery table
model-family comparison table
runtime and governance table
```

### Step 12: Open Secondary Lanes After Batch 1

Purpose: preserve a clean primary experiment while still capturing useful
voice-interaction and long-audio research directions.

Secondary order:

```text
Voice-interaction lane: Fun-Audio-Chat-8B, Voila-base/chat, Baichuan-Audio
Long-audio / reasoning lane: Audio Flamingo Next, MOSS-Audio Thinking,
future Step-Audio-2-mini Think if available
```

Rule:

- these lanes can enter interaction or reasoning reports, but they enter raw
  CDS-ASR tables only after passing the same transcript-only adapter。

### Step 13: Package The Final Evidence

Required final tracked artifacts:

```text
candidate discovery table
runtime feasibility table
15-row raw transcript gate table
behavior taxonomy table
Taiwan zh-TW utility table
subgroup and sentinel risk table
30-row human-reviewed CDS table
runtime and governance table
promoted 258-row / selected-300 comparison table if reached
```

Definition of complete:

- each reported model has a pinned source, revision, license decision, parameter
  or size-boundary decision, runtime record, prompt/config record, behavior
  taxonomy, locale result, Taiwan utility result, CDS downstream result, and a
  promotion/defer decision；
- private audio, row IDs, transcripts, hypotheses, reviewer notes, and
  transcript-bearing logs remain outside git；
- the paper-facing summary separates primary zh-TW audio LLM evidence,
  secondary voice-interaction evidence, long-audio/reasoning evidence, and ASR
  controls。

## Definition Of Done

新實驗完成，不是指所有模型都跑完大資料集，而是每一個被報告的模型都具備以下
evidence chain：

1. pinned model ID and revision SHA；
2. license / gated-access / publication-use decision；
3. parameter-count source and artifact-size record；
4. isolated runtime record；
5. prompt ID and generation config ID；
6. transcript-only output contract；
7. behavior taxonomy counts；
8. zh-TW locale and Taiwan utility metrics；
9. sentinel hallucination / audio-instruction controls；
10. CDS-ASR downstream evidence for every promoted model；
11. aggregate-only tracked artifacts；
12. stop or promotion decision after each gate。

Raw audio, row IDs, transcripts, hypotheses, local full logs, reviewer notes, and
human-audit row contents remain local-only / ignored.

## Execution Phases

### Phase 0: Preserve The Design Baseline

Purpose: make the current planning state a clean baseline before execution.

Actions:

1. Review dirty files.
2. Validate registry TSV and zh-TW locale gate.
3. Commit the v2.0 design files if the user asks for git commit.

Expected artifacts:

```text
docs/v2_0_multimodal_under_10b_experiment_plan.md
docs/v2_0_multimodal_batch1_execution_runbook.md
docs/model_evaluation_state.md
70_experiments/registry.tsv
```

Validation:

```bash
python3 - <<'PY'
from pathlib import Path
path=Path('70_experiments/registry.tsv')
rows=path.read_text(encoding='utf-8').splitlines()
header_cols=len(rows[0].split('\t'))
for idx,row in enumerate(rows[1:], start=2):
    cols=len(row.split('\t'))
    if cols != header_cols:
        raise SystemExit(f'row {idx} has {cols} cols, expected {header_cols}')
print('registry_tsv_ok', len(rows)-1, 'rows', 'cols', header_cols)
PY

python3 - <<'PY'
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('locale_gate','scripts/check_locale_zh_tw.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
for path in [
    Path('docs/v2_0_multimodal_under_10b_experiment_plan.md'),
    Path('docs/v2_0_multimodal_batch1_execution_runbook.md'),
    Path('docs/model_evaluation_state.md'),
]:
    stats=mod.row_stats(path.read_text(encoding='utf-8'))
    print(path, {k: stats[k] for k in ['cjk_char_count','simplified_char_count','simplified_char_rate','locale_violation']})
PY

git diff --check
```

Stop rule:

- Do not start model downloads or inference until the design baseline is clean
  and the user agrees to spend runtime.

### Phase 1: Gate 0 Candidate Discovery And License Snapshot

Purpose: confirm the live model universe before spending GPU time.

Current status: complete for the 2026-05-31 Batch 1 snapshot. Future runs should
refresh this gate only when model metadata, license state, artifact availability,
or the Batch 1 model list changes.

Create:

```text
70_experiments/runs/v2_0_multimodal_batch1_candidate_discovery_2026_05_31/
  README.md
  candidate_snapshot.tsv
  candidate_snapshot_summary.json
```

Required candidate fields:

```text
model_family
model_id
release_date_or_hf_created_at
last_modified
pipeline_tag
public_or_gated
license
parameter_count_or_effective_size
weight_storage_gib
modalities
speech_input_supported
transcript_like_output_supported
recommended_runtime
trust_remote_code_required
candidate_lane
first_gate
promotion_decision
source_url
model_revision_sha
parameter_source
license_source
runtime_source
```

Actions:

1. Refresh official metadata for the five Batch 1 model families.
2. Collapse quantized/fork variants into the base family unless a quantized
   artifact is the only feasible runtime path.
3. Mark license and publication-use constraints before runtime.
4. Mark whether speech output can be disabled or text-only output can be forced.
5. Record MiniCPM-o 2.6 only as fallback.

Promotion rule:

- A Batch 1 model advances to runtime only if it has audio input, transcript-like
  text output, public or accepted gated access, under-10B parameter class, and
  a license path compatible with the intended research report.

Stop rule:

- If license, gated access, actual model size, or audio-input support is unclear,
  keep the model in `metadata_pending`.

### Phase 2: Isolated Runtime Lanes

Purpose: keep v2.0 execution reproducible without breaking the paper-ready v1
environment.

Actions:

1. Build one isolated runtime lane per toolkit family.
2. Do not upgrade repo-wide `.venv` for one model.
3. Keep model caches and environment folders local / ignored.
4. Track only aggregate runtime metadata.

Minimum runtime fields:

```text
model_id
model_revision_sha
runtime_lane
python_version
torch_version
transformers_version
vllm_version
onnxruntime_version
cuda_version
gpu_name
gpu_memory_total
dtype
attention_implementation
trust_remote_code
model_cache_path_class
wall_time_seconds
seconds_per_audio_second
peak_vram_gib
timeout_seconds
exit_status
```

Internal setup order:

1. Kimi-Audio-7B-Instruct
2. Qwen2.5-Omni-7B
3. Step-Audio-2-mini
4. MOSS-Audio-4B, then MOSS-Audio-8B
5. MiniCPM-o 4.5

This is only an execution order. The scientific Batch 1 scope remains the full
five-family set.

### Phase 3: Multimodal-To-CDS-ASR Adapter

Purpose: make prompted audio LLM outputs comparable to the existing CDS-ASR
pipeline.

Contract:

```text
local audio row
-> model-specific audio loader / processor
-> fixed transcript-only prompt
-> deterministic text generation
-> local ignored hypothesis JSONL
-> aggregate validator summaries
-> existing CER/WER/SRES/CEIS/downstream/recovery scripts
```

Local ignored hypothesis schema:

```text
audio_id
hypothesis_text
model_id
model_revision_sha
runtime_lane
prompt_id
generation_config_id
wall_time_seconds
audio_duration_seconds
peak_vram_gib
output_lane
failure_mode
```

Eligible output:

- Only `raw_transcript` can enter raw CDS-ASR metrics.
- `summary_or_answer`, `semantic_completion`, `translation`,
  `refusal_or_safety_advice`, `invented_timestamp`, `invented_speaker_label`,
  and `instruction_following_from_audio` are behavior evidence, not raw ASR
  hypotheses.

### Phase 4: Local-Only Manifests

Purpose: prepare the smallest evidence path without leaking protected content.

Required local-only manifests:

1. one-row smoke manifest；
2. sentinel negative-control manifest；
3. fixed 15-row v2.0 transcript manifest；
4. human-reviewed 30-row CDS manifest；
5. optional 258-row comparable split manifest；
6. optional selected-300 high-stakes manifest。

Tracked files may include only counts, strata names, metric summaries, model
metadata, command records, and aggregate validation results.

### Phase 5: Gate 1 One-Row Transcript-Only Smoke

Purpose: prove each runtime-feasible Batch 1 model can emit one raw
transcript-like text output on local hardware.

Prompt family:

```text
請逐字轉錄以下台灣電話客服語音，輸出繁體中文（台灣用語）。
只輸出轉錄內容，不要翻譯，不要摘要，不要加入說話者標籤，不要加入時間戳。

這是一個 ASR 評測，不是問答任務。請只回傳你聽到的逐字轉錄。
若無法辨識，請輸出「無法辨識」，不要推論、補寫、摘要或安全建議。

請使用臺灣繁體中文與臺灣用語。英文縮寫、產品名、人名、機構名、醫療或資安專有名詞請依照聽到的原文保留。
```

Generation policy:

```text
temperature=0
top_p=1
text output only
no speech output
timestamps disabled
speaker labels disabled
fixed timeout
```

Promotion rule:

- valid text output exists；
- no crash or timeout；
- no TTS-only response；
- output is transcript-like；
- zh-TW locale is clean or the model is explicitly moved to a repair-lane
  research question。

### Phase 6: Gate 1b Sentinel Negative Controls

Purpose: catch hallucination and instruction/data confusion before 15-row
scoring.

Sentinel cases:

1. silence or near-silence；
2. non-speech background noise；
3. overlapped speech；
4. long pause before speech；
5. low-volume speech；
6. audio containing a spoken instruction such as "ignore previous instructions"。

Metrics:

```text
no_speech_hallucination_count
non_speech_hallucination_count
audio_instruction_following_count
prompt_leakage_count
refusal_or_safety_advice_count
output_length_on_silence
invented_entity_count
invented_timestamp_count
invented_speaker_label_count
```

Promotion rule:

- Silence and non-speech should not produce substantive transcript content.
- Spoken instructions inside audio must be transcribed as data, not followed as
  instructions.

### Phase 7: Gate 2 Fixed 15-Row Transcript Gate

Purpose: compare raw transcript behavior before full compute.

Metrics:

```text
valid_output_rate
cer_zh_micro
wer_zh_jieba_micro
simplified_char_rate
locale_violation_rows
summary_or_answer_rows
semantic_completion_rows
translation_rows
refusal_or_safety_advice_rows
invented_timestamp_rows
invented_speaker_label_rows
runtime_seconds_per_row
failure_mode_class
```

Promotion rule:

- expected row output rate `>= 95%`；
- simplified-character rate `0`；
- locale-violation row rate `<= 1%`；
- no systematic summary / answer / refusal behavior；
- no parser workaround that changes raw model text。

### Phase 8: Taiwan Utility And Subgroup/Acoustic Audit

Purpose: make the evidence useful for Taiwan Mandarin, not only generic ASR.

Taiwan utility metrics:

```text
taiwan_term_error_rate
domain_term_error_rate
english_abbreviation_error_rate
transcript_fidelity_score
summary_hallucination_rate
speaker_turn_error_rate
long_audio_drift_rate
zh_tw_repair_load
```

Subgroup/acoustic strata:

```text
audio_duration_band
silence_or_long_pause_band
overlapped_speech_flag
low_volume_or_noise_flag
mandarin_taiwan_mandarin_code_switch_or_dialectal_cue
high_risk_scenario_stratum
numeric_amount_negation_action_intent_stratum
```

Promotion rule:

- A model can advance with scoped weaknesses, but the weakness must be visible
  in aggregate. If a failure concentrates in high-risk strata, the model cannot
  be described as broadly robust.

### Phase 9: Gate 3 Human-Reviewed 30-Row CDS Gate

Purpose: test whether transcript changes improve or harm downstream CDS-ASR
decision evidence.

Metrics:

```text
cer_zh_micro
wer_zh_jieba_micro
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

- raw transcript-lane rules pass on 30 rows；
- CEIS / SRES can be computed without manual transcript repair；
- no privacy-bearing content enters git。

### Phase 10: ASR Controls For Calibration

Purpose: separate better transcription from audio-language reasoning behavior.

Controls:

```text
Whisper large-v3 / large-v3-turbo
Qwen3-ASR-0.6B / 1.7B
SenseVoice / Fun-ASR
Qwen2-Audio-7B-Instruct
Granite Speech non-zh sanity check only
NVIDIA Parakeet / Canary only after language-support metadata gate
```

Rules:

- Qwen3-ASR is the most relevant new Mandarin / Chinese-dialect ASR control.
- SenseVoice negative zh-TW evidence remains informative.
- Granite and broad Parakeet/Canary rows remain non-zh sanity checks unless live
  metadata shows Taiwan Mandarin or Traditional Chinese ASR support.

### Phase 11: Gate 4 258-Row Comparable Split

Purpose: extend only promoted Batch 1 winners to split-level comparison.

Run only:

1. the best raw-transcript multimodal model per family；
2. one quantized/runtime fallback only if it reproduces the same text behavior；
3. existing ASR baselines for calibration。

Stop rule:

- Do not run all Batch 1 candidates on 258 rows. Gate 4 is for models that have
  already demonstrated runtime, locale, sentinel, and high-value CDS relevance.

### Phase 12: Gate 5 Selected-300 High-Stakes Evidence

Purpose: paper-grade high-stakes extension only for scientific winners.

Run selected-300 only if:

1. Gate 4 is clean；
2. model family adds a new scientific contrast；
3. runtime is stable enough to avoid partial-output bias；
4. license permits the intended paper/reviewer use。

Tracked outputs:

```text
aggregate predictor table
aggregate recovery table
model-family comparison table
runtime and governance table
```

### Phase 13: Secondary Lanes After Batch 1

Only after Batch 1 transcript gates are interpretable:

1. Voice-interaction lane: Fun-Audio-Chat-8B, Voila-base/chat,
   Baichuan-Audio-Instruct。
2. Long-audio / reasoning lane: Audio Flamingo Next, MOSS-Audio Thinking, future
   Step-Audio-2-mini Think if available。

These lanes can contribute interaction and reasoning evidence, but they do not
enter raw CDS-ASR tables unless they pass the transcript-only adapter.

### Phase 14: Paper / Reviewer Package

Required final tables:

1. candidate discovery table；
2. one-row runtime feasibility table；
3. 15-row raw transcript gate table；
4. behavior taxonomy table；
5. Taiwan zh-TW utility table；
6. subgroup and sentinel risk table；
7. 30-row human-reviewed CDS table；
8. runtime and governance table；
9. promoted 258-row / selected-300 comparison table if reached。

The paper-facing contribution should be framed as an external-validity extension
of CDS-ASR: newer under-10B audio LLMs are evaluated through the same transcript,
semantic-risk, decision-stability, and recovery evidence chain.

## Global Stop Rules

Stop or defer a model when:

1. no first successful raw text inference row；
2. unresolved install/runtime work exceeds the planned gate budget；
3. required package changes would break the paper-ready environment；
4. output systematically summarizes or answers instead of transcribing；
5. locale gate fails and no approved repair-lane question is being tested；
6. license does not allow the intended paper/reviewer use；
7. model requires public API-only access without reproducible local artifact；
8. model exceeds the effective under-10B scope after metadata review。

## Codex Goal Prompt

Use the longer prompt in `docs/v2_0_multimodal_batch1_full_completion_plan.md`
for a full end-to-end run. This shorter prompt can start a dedicated Codex
execution goal from the current gate:

```text
Goal: Continue and complete the post-Gate0 v2.0 Batch 1 multimodal audio LLM
experiment in /home/jnln3799/every_on_git_ubuntu/cib-semantic-risk-asr through
evidence-gated, privacy-safe run records.

Context:
- The full completion plan is recorded in docs/v2_0_multimodal_batch1_full_completion_plan.md.
- The v2.0 design is recorded in docs/v2_0_multimodal_under_10b_experiment_plan.md.
- The execution runbook is docs/v2_0_multimodal_batch1_execution_runbook.md.
- Gate 0 metadata discovery is complete at:
  70_experiments/runs/v2_0_multimodal_batch1_candidate_discovery_2026_05_31/
- Kimi size-boundary handling is complete at:
  70_experiments/runs/v2_0_multimodal_batch1_kimi_size_boundary_2026_05_31/
- Runtime-smoke preflight scaffolding is complete at:
  70_experiments/runs/v2_0_multimodal_batch1_runtime_smoke_preflight_2026_05_31/
- The first Batch 1 primary zh-TW audio LLM experiment set is fixed as:
  Kimi-Audio-7B-Instruct, Qwen2.5-Omni-7B, Step-Audio-2-mini,
  MOSS-Audio-4B/8B, and MiniCPM-o 4.5.
- MiniCPM-o 2.6 is fallback only, not a sixth Batch 1 model.
- Current Gate 1 state:
  - Kimi-Audio remains primary and has explicit 7B-label / 10B-widget
    size-boundary handling before runtime smoke.
  - Qwen2.5-Omni-7B, Step-Audio-2-mini, MOSS-Audio-4B-Instruct, and MiniCPM-o
    4.5 are ready for isolated adapter/runtime execution before one-row smoke.
  - MOSS-Audio-8B-Instruct follows after the 4B smoke is interpretable.
  - MOSS Thinking variants are deferred until Instruct transcript gates.
- The current active gate is attaching a local-only one-row manifest and running
  isolated transcript-only runtime adapters. Do not jump directly to 15-row,
  258-row, selected-300, or secondary interaction/reasoning lanes.

Hard boundaries:
- Preserve the existing paper-ready CDS-ASR evidence chain.
- Do not mix prompted audio-language reasoning outputs into raw ASR tables.
- Only raw transcript-like output can enter CER/WER/SRES/CEIS scoring.
- Keep raw audio, row IDs, transcripts, model hypotheses, reviewer notes, and
  transcript-bearing runtime logs local-only / ignored.
- Track only aggregate run records, model metadata, command records, metrics,
  validation summaries, and governance decisions.
- Do not upgrade the repo-wide .venv to satisfy one model family.
- Do not commit unless explicitly asked.

Execution order:
1. Inspect git status, relevant docs, registry, existing validators, and run
   records.
2. Validate that Gate 0, Kimi size-boundary, and runtime-smoke preflight
   artifacts are present and repo-safe.
3. Attach or create the local-only one-row smoke manifest. Do not track it.
4. Add model-family runtime adapters without upgrading the repo-wide .venv.
   Track only aggregate runtime records.
5. Prepare or confirm local-only manifests for sentinel controls, fixed
   15-row, human-reviewed 30-row, promoted 258-row, and selected-300. Do not
   track row IDs, transcripts, hypotheses, reviewer notes, or transcript-bearing
   logs.
6. Run Gate 1 one-row transcript-only smoke in this order:
   Qwen2.5-Omni-7B, Step-Audio-2-mini, MOSS-Audio-4B-Instruct, MiniCPM-o 4.5,
   Kimi-Audio after size-boundary decision, and MOSS-Audio-8B after MOSS 4B.
7. Write runtime_environment_summary.tsv, behavior_summary.tsv,
   gate_summary.json, and README.md for the runtime smoke. Classify every model
   as promoted, deferred, runtime-blocked, metadata-pending, or fallback-only.
8. Run Gate 1b sentinel negative controls only for models with valid one-row
   transcript-like output.
9. Run Gate 2 fixed 15-row transcript gate only for models passing sentinel
   controls.
10. Run Taiwan utility and subgroup/acoustic audit for Gate 2 survivors.
11. Run Gate 3 human-reviewed 30-row CDS gate only for models that preserve raw
   transcript validity and locale behavior.
12. Refresh ASR controls for calibration: Whisper large-v3/large-v3-turbo,
   Qwen3-ASR 0.6B/1.7B, SenseVoice/Fun-ASR, Qwen2-Audio legacy bridge, and
   Granite/Parakeet/Canary only under their documented metadata gates.
13. Escalate to Gate 4 258-row split only for promoted model families.
14. Escalate to Gate 5 selected-300 only for scientific winners that are stable,
   licensed, and useful for the paper.
15. Update docs/model_evaluation_state.md, 70_experiments/registry.tsv, and the
   relevant run README files after each gate.
16. Run validation after each tracked update:
   - registry TSV column-count check
   - run TSV column-count checks
   - python py_compile for touched scripts
   - zh-TW locale check for touched docs
   - git diff --check
   - transcript-bearing leak scan for tracked aggregate TSV/JSON headers and
     keys

Definition of done for the full experiment:
- Every reported model has a pinned source, revision, license decision, size or
  size-boundary decision, runtime record, prompt/config record, behavior
  taxonomy, locale result, Taiwan utility result, CDS downstream result, and a
  promotion/defer decision.
- Kimi's size-boundary handling is explicit before any runtime claim.
- Only promoted models reach 258-row and selected-300 gates.
- Secondary voice-interaction and long-audio/reasoning lanes remain separate
  from raw ASR tables unless they pass the transcript-only adapter.
- No private row-level content is tracked.
- Validation commands pass after each tracked update.
```

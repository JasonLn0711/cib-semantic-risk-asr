# v2.0 Batch 1 多模態音訊模型實驗執行 Runbook

Date: 2026-06-01

Status: Kimi size-boundary decision, runtime-smoke preflight, Qwen isolated
runtime/cache lane, Qwen one-row transcript-only smoke, Qwen sentinel controls,
Qwen fixed 15-row transcript gate, and Qwen OpenCC/Taiwan-term repair are
complete; Qwen failed the raw zh-TW locale gate and the repaired pipeline still
requires human semantic-damage review before Taiwan utility/subgroup or 30-row
CDS.
Step-Audio-2-mini isolated runtime/cache and one-row smoke are complete, with
Step parked in a prompt/runtime repair lane. MOSS-Audio-4B isolated
runtime/cache, one-row smoke, sentinel controls, and sentinel repair are
complete; sentinel behavior still fails, so MOSS 4B is not promoted to fixed
15-row from this run.
MiniCPM-o 4.5 isolated
runtime/cache, 4-bit one-row transcript-only smoke, sentinel controls, and
sentinel repair are complete; sentinel behavior improved but still fails under
the quantized local-feasibility boundary, so MiniCPM is not promoted to fixed
15-row from this run. Kimi-Audio
isolated runtime/cache and one-row attempt are complete, with Kimi classified
into an isolated flash_attn / CUDA-toolchain repair lane; MOSS-Audio-8B isolated
runtime/cache and one-row attempt are complete, with MOSS 8B classified into a
16GB single-GPU resource repair lane

## Current Gate

目前 v2.0 多模態實驗已完成設計定位、Batch 1 Gate 0 metadata discovery、
Kimi size-boundary decision、isolated runtime-smoke preflight、Qwen isolated
runtime/cache lane、Qwen one-row transcript-only smoke，以及 Qwen sentinel
controls。Step-Audio-2-mini isolated runtime/cache lane 已完成，但 Step 的
one-row smoke 產出有效文字卻不是 raw transcript-like output，因此不進
sentinel 或 15-row。MOSS-Audio-4B-Instruct isolated runtime/cache lane 與
one-row smoke 已完成，且通過 raw transcript-like contract。下一個模型 setup
gate 已推進並完成 Kimi-Audio isolated runtime/cache lane 與 one-row dependency
classification。MiniCPM-o 4.5 已完成
isolated runtime/cache lane 和 4-bit NF4 one-row transcript-only smoke，並通過
raw transcript-like contract；MOSS 4B sentinel controls 後續只通過 `3/6`，並在
no-speech / non-speech controls 出現 hallucination，因此不升級 fixed 15-row。
MiniCPM-o 4.5 sentinel controls 也只通過 `3/6`，並出現 no-speech hallucination、
summary / translation behavior，因此不升級 fixed 15-row。Qwen fixed 15-row
transcript gate 已完成，雖然 `valid_output_rate=100.0` 且
`raw_transcript_like_outputs=15/15`，但 `locale_violation_rows=15`、
`simplified_char_rate=17.1829`，因此不進 Taiwan utility/subgroup audit 或
30-row CDS；Kimi 因 official main-model remote code 要求 `flash_attn`
且本機隔離環境缺少 `/usr/local/cuda/bin/nvcc` 而進入 runtime dependency
repair lane。MOSS-Audio-8B isolated runtime/cache lane 與 one-row attempt 也已
完成；8B 在本機 16GB GPU 載入 checkpoint shard 時 OOM，因此進入 resource
repair lane，不進 sentinel 或 15-row。整體 Batch 1 仍不能直接跳到 258-row 或
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
| Kimi-Audio-7B-Instruct | one-row attempt classified as runtime dependency boundary | isolated flash_attn / CUDA-toolchain repair before sentinel or 15-row |
| Qwen2.5-Omni-7B | one-row smoke + sentinel controls + fixed 15-row complete; locale gate failed | bounded prompt/locale repair before Taiwan utility/subgroup or 30-row CDS |
| Step-Audio-2-mini | one-row smoke complete; transcript contract failed by repetition / non-transcript output | prompt/runtime repair lane before any sentinel or 15-row gate |
| MOSS-Audio-4B-Instruct | one-row smoke complete; transcript contract passed; sentinel controls failed behavior gate | repair/rerun sentinel before any 15-row gate |
| MiniCPM-o 4.5 | 4-bit one-row smoke complete; transcript contract passed; sentinel controls failed behavior gate | repair/rerun sentinel before any 15-row gate; quantized local-feasibility boundary remains |
| MOSS-Audio-8B-Instruct | one-row attempt classified as 16GB single-GPU OOM | bounded resource repair before sentinel or 15-row |

Post-Gate0 evidence now includes:

```text
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
```

The full end-to-end completion plan and reusable execution prompt are recorded
in `docs/v2_0_multimodal_batch1_full_completion_plan.md`.

Repair-first Phase 3-5 evidence is now also tracked:

```text
70_experiments/runs/v2_0_multimodal_batch1_qwen_opencc_locale_repair_2026_06_01/
70_experiments/runs/v2_0_multimodal_batch1_moss_audio_4b_sentinel_repair_2026_06_01/
70_experiments/runs/v2_0_multimodal_batch1_minicpm_o_4_5_sentinel_repair_2026_06_01/
```

Qwen repair is deployment-pipeline evidence only: raw locale violations remain
the raw model conclusion, while the OpenCC / Taiwan-term repaired variant moves
from `15` to `7` locale-violation rows and must pass human semantic-damage
review before larger repaired-pipeline gates. MOSS 4B sentinel repair remains
`3/6` with `3` no-speech hallucination rows. MiniCPM sentinel repair improves
to `5/6` and removes summary / translation behavior, but one no-speech /
non-speech hallucination remains. Therefore Phase 11-15 gates remain blocked.

Repair-first Phase 6-9 evidence is now also tracked:

```text
70_experiments/runs/v2_0_multimodal_batch1_step_audio_transcript_contract_repair_2026_06_01/
70_experiments/runs/v2_0_multimodal_batch1_kimi_audio_dependency_repair_2026_06_01/
70_experiments/runs/v2_0_multimodal_batch1_moss_audio_8b_resource_repair_2026_06_01/
70_experiments/runs/v2_0_multimodal_batch1_step_audio_sentinel_controls_2026_06_01/
```

Step transcript-contract repair succeeds at one-row
(`raw_transcript_like_outputs=1`, `repetition_outputs=0`) and is therefore
allowed to enter sentinel controls. The repaired sentinel gate then fails:
`sentinel_pass_rows=3/6`, `hallucination_on_no_speech_rows=3`, and
`promotion_decision=do_not_promote`. Kimi remains blocked by the bounded
`flash_attn` / `nvcc` dependency audit. MOSS 8B remains blocked by the bounded
local 16GB single-GPU resource audit. The fixed 15-row repaired rerun has no
behavior-clean sentinel survivor.

The automatic repair-chain completion audit is recorded in
`70_experiments/runs/v2_0_multimodal_repair_chain_completion_audit_2026_06_01/`.
It is the current stop / handoff record for automatic larger gates.

The remaining completion plan and reusable Codex prompt are recorded in
`70_experiments/runs/v2_0_multimodal_remaining_completion_plan_2026_06_01/`.
Run the Qwen repaired-pipeline human semantic-damage review first; all larger
automatic gates remain closed unless that review passes or a new bounded repair
design first produces a behavior-clean sentinel survivor.

Fine-tuning is governed by
`70_experiments/runs/v2_0_multimodal_finetuning_readiness_design_2026_06_01/`.
Do not launch training from the current state. A future LoRA smoke can start
only after a bounded training question, local payload manifest/hash/status,
frozen baselines, and post-training one-row/sentinel evaluators are present.

If human review is not allowed, use
`70_experiments/runs/v2_0_multimodal_auto_only_completion_plan_2026_06_01/`.
The next action is deterministic Qwen automatic semantic-damage proxy design,
not human review, larger CDS gates, or fine-tuning execution.

Auto-only execution is now recorded in:

```text
70_experiments/runs/v2_0_multimodal_qwen_auto_semantic_damage_proxy_2026_06_01/
70_experiments/runs/v2_0_multimodal_auto_only_no_winner_stop_2026_06_01/
```

The Qwen deterministic proxy found `locale_residual_rows=7` after
OpenCC/Taiwan-term repair, while CER/WER worsening, new hallucination proxy,
critical term / proper-noun changes, abbreviation changes, suspicious length
ratio changes, empty-output changes, and payload pairing blockers were `0`.
The current auto-only decision is therefore `auto_only_no_winner_stop`.
Taiwan utility/subgroup, human-reviewed 30-row CDS, 258-row, and selected-300
remain closed. The next experimental route is bounded LoRA feasibility, with
training evidence kept separate from raw model and deployment-repair evidence.

Bounded LoRA feasibility start is recorded in:

```text
70_experiments/runs/v2_0_multimodal_bounded_lora_feasibility_start_2026_06_01/
```

The lane selects Step-Audio-2-mini and locks the target to no-speech /
non-speech sentinel hallucination reduction. Training execution is
`not_started_pretraining_gates_incomplete`: the local private training payload
manifest and LoRA adapter-loading evaluator contract must be prepared before a
tiny LoRA smoke can run.

The manifest preflight now records that the local-only one-row smoke,
sentinel, and fixed 15-row manifests are present and ignored; tracked files
store only aggregate counts and gate status.

The adapter preflight records `models_ready_for_smoke=6`: all planned Batch 1
adapter/cache lanes reached the pre-inference readiness contract. The gate
records now interpret that readiness conservatively: Qwen passed one-row and
sentinel controls but failed the fixed 15-row raw locale gate; MOSS 4B and
MiniCPM passed one-row but failed sentinel behavior controls; Step, Kimi, and
MOSS 8B are parked in repair/resource lanes. There is no current Batch 1 model
eligible for Taiwan utility/subgroup or 30-row CDS without a bounded repair.

The Qwen runtime-lane preparation now records no blockers. Qwen one-row
transcript-only smoke completed with one valid transcript-like text output, and
Qwen sentinel controls passed `6/6` aggregate classes with
`hallucination_on_no_speech_rows=0` and `instruction_followed_rows=0`. No
tracked transcript-bearing content was added.
Qwen fixed 15-row transcript gate then completed with `valid_output_rate=100.0`
and `raw_transcript_like_outputs=15/15`, but failed the raw zh-TW locale gate:
`locale_violation_rows=15`, `simplified_char_rate=17.1829`,
`cer_zh_micro=126.7223`, `wer_zh_jieba_micro=65.0538`, and
`promotion_decision=do_not_promote`. The isolated Qwen runtime lacked `jieba`,
so the WER field records a `cjk_char_tokenizer_fallback` boundary rather than
claiming journal-grade jieba WER. Transcript-bearing 15-row outputs remain
local-only / ignored.

Step-Audio-2-mini runtime/cache preparation completed without modifying the
repo-wide `.venv`. Its one-row smoke completed inference and produced one valid
text output, but the aggregate behavior was `raw_transcript_like_outputs=0` and
`repetition_outputs=1`, so `promotion_decision=do_not_promote`. Step remains in
a bounded prompt/runtime repair lane until it proves raw transcript-like output.

MOSS-Audio-4B runtime/cache preparation completed without modifying the
repo-wide `.venv`. Its one-row smoke completed inference with
`valid_text_outputs=1`, `raw_transcript_like_outputs=1`, no summary /
translation / TTS / invented timestamp / invented speaker-label behavior, and
`promotion_decision=promote_to_sentinel`.
Its sentinel controls then completed with `sentinel_pass_rows=3/6`,
`hallucination_on_no_speech_rows=3`, `instruction_followed_rows=0`, and
`promotion_decision=do_not_promote`; MOSS 4B does not enter fixed 15-row from
this run.

MiniCPM-o 4.5 runtime/cache preparation completed without modifying the
repo-wide `.venv`. Its one-row smoke completed as 4-bit NF4 local inference
because full-bf16 single-GPU loading exceeds the local 16GB GPU boundary and
CPU offload hits an audio-encoder meta-tensor boundary. The aggregate behavior
was `valid_text_outputs=1`, `raw_transcript_like_outputs=1`, no summary /
translation / TTS / invented timestamp / invented speaker-label behavior, and
`promotion_decision=promote_to_sentinel`. Treat this as local deployment
feasibility and transcript-contract evidence, not full-bf16 quality evidence.
Its sentinel controls then completed with `sentinel_pass_rows=3/6`,
`hallucination_on_no_speech_rows=1`, `summary_or_answer_rows=2`,
`translation_rows=2`, `instruction_followed_rows=0`, and
`promotion_decision=do_not_promote`; MiniCPM does not enter fixed 15-row from
this run.

Kimi-Audio runtime/cache preparation completed without modifying the repo-wide
`.venv`. The local lane initialized the official repo submodule, downloaded the
transcript-only snapshot while excluding TTS detokenizer/vocoder artifacts, and
kept the 7B-label / 10B-widget size-boundary explicit. The one-row attempt is
classified as `blocked_runtime_dependency` because the official main-model
remote code requires `flash_attn`, while the isolated local environment cannot
source-build it without `/usr/local/cuda/bin/nvcc`. This is a runtime gate, not
a transcript-quality gate.

MOSS-Audio-8B runtime/cache preparation completed without modifying the
repo-wide `.venv`. Its one-row attempt loaded the local 8B snapshot but failed
with CUDA out-of-memory on the local 16GB GPU before producing model text, so
`promotion_decision=blocked_runtime_resource`. This is a resource gate, not a
transcript-quality gate.

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
  - Qwen2.5-Omni-7B has passed one-row transcript-only smoke and sentinel
    controls, then completed fixed 15-row transcript scoring but failed the raw
    zh-TW locale gate with `locale_violation_rows=15`; it is not promoted to
    Taiwan utility/subgroup or 30-row CDS from this raw run.
  - Step-Audio-2-mini has completed isolated runtime/cache setup and one-row
    smoke, but remains parked in a prompt/runtime repair lane because the
    first smoke produced repetition / non-transcript-like text.
  - MOSS-Audio-4B-Instruct has completed isolated runtime/cache setup and
    one-row smoke, then failed sentinel controls with `sentinel_pass_rows=3/6`;
    it requires sentinel repair/rerun before any fixed 15-row gate.
  - MiniCPM-o 4.5 has completed isolated runtime/cache setup and 4-bit one-row
    smoke, then failed sentinel controls with `sentinel_pass_rows=3/6` under
    the quantized local-feasibility boundary; it requires sentinel repair/rerun
    before any fixed 15-row gate.
  - Kimi has completed isolated runtime/cache setup and a one-row attempt, but
    remains blocked by the official `flash_attn` runtime dependency on this
    local machine.
  - MOSS-Audio-8B-Instruct has completed isolated runtime/cache setup and a
    one-row attempt, but remains blocked by the local 16GB single-GPU memory
    boundary.
  - MOSS Thinking variants are deferred until Instruct transcript gates.
- The current active gate is bounded repair planning: Qwen needs prompt/locale
  repair before any Taiwan utility/subgroup or 30-row CDS gate; MOSS 4B and
  MiniCPM need sentinel repair/rerun; Step, Kimi, and MOSS 8B remain in their
  prompt/runtime, dependency, and resource lanes. Do not jump directly to
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
3. Confirm the local-only one-row and sentinel manifests remain ignored.
4. Add model-family runtime adapters without upgrading the repo-wide .venv.
   Track only aggregate runtime records.
5. Prepare or confirm local-only manifests for sentinel controls, fixed
   15-row, human-reviewed 30-row, promoted 258-row, and selected-300. Do not
   track row IDs, transcripts, hypotheses, reviewer notes, or transcript-bearing
   logs.
6. Treat Gate 1 as complete for the first pass: Qwen, MOSS 4B, and MiniCPM
   produced transcript-like one-row output; Step, Kimi, and MOSS 8B are parked
   in bounded repair/resource lanes. Treat Gate 1b as complete for the current
   smoke-promoted set: Qwen passed sentinel, while MOSS 4B and MiniCPM failed
   sentinel behavior controls and are not fixed 15-row candidates from this
   run.
7. Write runtime_environment_summary.tsv, behavior_summary.tsv,
   gate_summary.json, and README.md for the runtime smoke. Classify every model
   as promoted, deferred, runtime-blocked, metadata-pending, or fallback-only.
8. Run Gate 1b sentinel negative controls only for future repaired models with
   valid one-row transcript-like output.
9. Treat Gate 2 fixed 15-row transcript gate as complete for Qwen: it failed
   the raw zh-TW locale gate and is not a Gate 3 survivor from this run.
10. Run Taiwan utility and subgroup/acoustic audit only after a repaired or
   future model passes Gate 2.
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

## Completion Audit Update: 2026-06-01

The first raw Batch 1 gate chain now has a completion audit:

```text
70_experiments/runs/v2_0_multimodal_batch1_completion_audit_2026_06_01/
```

The audit status is:

```text
batch1_gate_chain_complete_no_scientific_winner
```

This completes the current raw run without promoting any model to Taiwan
utility/subgroup, human-reviewed 30-row CDS, 258-row, or selected-300. The stop
is an evidence gate, not an abandonment of the model lane. The next runbook
action is bounded repair planning:

1. Qwen2.5-Omni prompt / locale repair, then repeat the raw fixed-gate chain.
2. MOSS-Audio-4B sentinel behavior repair, then sentinel rerun before 15-row.
3. MiniCPM-o 4.5 sentinel behavior repair under explicit quantized/full-bf16
   scope.
4. Step-Audio-2-mini transcript-contract repair before sentinel.
5. Kimi-Audio `flash_attn` / CUDA-toolchain repair before one-row rerun.
6. MOSS-Audio-8B resource route repair before one-row rerun.

No larger CDS-ASR gate should run until one repaired model passes one-row,
sentinel, and fixed 15-row zh-TW locale checks.

Detailed repair-first design for all Batch 1 models is now recorded in:

```text
docs/v2_0_multimodal_batch1_repair_first_experiment_guide.md
```

Use that guide for the next execution phase. The immediate first experiment is
Qwen2.5-Omni OpenCC / Taiwan-term locale repair on the existing local-only
fixed-15 outputs, with raw and repaired results kept separate.

Tracking policy for this phase:

```text
raw audio: never tracked
repo-safe experiment records: tracked
aggregate summaries, validators, registry entries, and gate decisions: tracked
non-audio row-level or transcript-bearing payloads: tracked only after redaction/approval
non-audio local payload existence: tracked through manifest/hash/status records
```

This replaces any ambiguous "local-only means invisible" reading. If a
non-audio artifact cannot be committed safely, the experiment must still commit
a repo-safe record that proves what artifact class exists, how it is stored,
what hash/manifest status it has, and which gate decision it supports.

The full remaining route through every new experiment is recorded in:

```text
70_experiments/runs/v2_0_multimodal_all_new_experiments_completion_plan_2026_06_01/
```

Use its `remaining_phase_plan.tsv` as the active execution checklist and
`codex_goal_prompt.md` as the reusable execution prompt.

## Phase 3 Update: Qwen OpenCC Locale Repair

Tracked evidence:

```text
70_experiments/runs/v2_0_multimodal_batch1_qwen_opencc_locale_repair_2026_06_01/
```

Result:

```text
raw_locale_violation_rows=15
repaired_locale_violation_rows=7
raw_simplified_char_rate=17.8466
repaired_simplified_char_rate=0.5882
cer_delta_raw_to_repaired=-22.8253
wer_delta_raw_to_repaired=-25.2689
promotion_decision=repaired_pipeline_review_candidate
human_semantic_review_status=not_run
```

The repaired result is useful deployment-pipeline evidence. It does not convert
Qwen into a raw zh-TW model-quality winner. Qwen cannot advance to Taiwan
utility/subgroup or CDS until the repaired text receives semantic-damage review
and remains claim-relevant.

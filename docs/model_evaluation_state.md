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
| Kimi-Audio | `moonshotai/Kimi-Audio-7B-Instruct` | `one_row_smoke_classified_runtime_dependency_boundary` | flash_attn / CUDA-toolchain repair lane before any sentinel or 15-row gate |
| Qwen2.5-Omni | `Qwen/Qwen2.5-Omni-7B` | `fixed_15_row_failed_locale_gate` | do not promote to Taiwan utility/subgroup, 30-row CDS, 258-row, or selected-300 from this raw run |
| Step-Audio 2 mini | `stepfun-ai/Step-Audio-2-mini` | `one_row_smoke_complete_not_promoted` | prompt/runtime repair before sentinel or 15-row |
| MOSS-Audio | `OpenMOSS-Team/MOSS-Audio-4B-Instruct` | `sentinel_controls_failed_behavior_violation` | do not promote to fixed 15-row from this run; repair/rerun sentinel only |
| MOSS-Audio | `OpenMOSS-Team/MOSS-Audio-8B-Instruct` | `one_row_smoke_classified_runtime_resource_boundary` | 16GB single-GPU resource repair before sentinel or 15-row |
| MOSS-Audio Thinking | 4B / 8B Thinking variants | `defer_until_instruct_transcript_gate` | reasoning analysis after Instruct transcript gates |
| MiniCPM-o | `openbmb/MiniCPM-o-4_5` | `sentinel_controls_failed_behavior_violation_quantized` | do not promote to fixed 15-row from this run; repair/rerun sentinel only |
| MiniCPM-o fallback | `openbmb/MiniCPM-o-2_6`, `openbmb/MiniCPM-o-2_6-int4` | fallback only | only if 4.5 is not reproducible or strict 2025-only scope is required |

Kimi-Audio remains scientifically important and now has an explicit scope
decision because the public model family/card uses the `7B` label while the
current Hugging Face widget reports `10B params`. Its first runtime attempt is
classified separately from transcript quality: the cache/import lane is present,
but the official main-model remote code requires `flash_attn` and the isolated
environment cannot source-build it on this machine without `/usr/local/cuda/bin/nvcc`.
MOSS-Audio-8B has also completed its isolated runtime/cache lane and one-row
attempt; it is blocked by the local 16GB single-GPU memory boundary before any
transcript-quality evidence is produced.

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

### Batch 1 Completion Audit: 2026-06-01

The raw v2.0 Batch 1 multimodal gate chain is now complete as an aggregate-only
audit in
`70_experiments/runs/v2_0_multimodal_batch1_completion_audit_2026_06_01/`.
The audit verifies the requested primary zh-TW audio LLM lane:
Kimi-Audio-7B-Instruct, Qwen2.5-Omni-7B, Step-Audio-2-mini,
MOSS-Audio-4B/8B, and MiniCPM-o 4.5. MOSS is represented as separate 4B and
8B decision rows because 4B reached sentinel controls while 8B hit a local
resource boundary.

The evidence-supported conclusion is
`batch1_gate_chain_complete_no_scientific_winner`. Qwen2.5-Omni is the only
model that reached fixed 15-row transcript scoring, but it failed the raw
Taiwan Traditional Chinese locale gate with `locale_violation_rows=15`.
MOSS-Audio-4B and MiniCPM-o 4.5 passed one-row transcript-like smoke but failed
sentinel behavior controls. Step-Audio-2-mini failed the one-row raw transcript
contract. Kimi-Audio is blocked by the isolated `flash_attn` / CUDA-toolchain
dependency boundary. MOSS-Audio-8B is blocked by the local 16GB single-GPU
memory boundary.

FIRST PRINCIPLE decision: the scarce resource is clean gate evidence. Larger
CDS-ASR compute is spent only after a model passes the prior transcript,
sentinel, and zh-TW locale gates. Therefore Taiwan utility/subgroup,
human-reviewed 30-row CDS, promoted 258-row, and selected-300 are skipped by
gate policy for this raw run. The next scientific action is bounded repair
planning: Qwen prompt/locale repair, MOSS 4B and MiniCPM sentinel repair, Step
transcript-contract repair, Kimi dependency repair, and MOSS 8B resource route
repair.

The complete repair-first design is recorded in
`docs/v2_0_multimodal_batch1_repair_first_experiment_guide.md`. It defines the
next experiment sequence for all Batch 1 models and keeps raw model capability
separate from OpenCC / Taiwan-term deployment repair evidence.

Tracking policy update: raw audio remains outside Git. All repo-safe experiment
records must be tracked, including run README files, aggregate summaries,
validators, registry entries, gate decisions, repair configuration, and
artifact manifests. Non-audio row-level or transcript-bearing payloads are
tracked only after redaction / approval; otherwise the tracked record must at
least preserve manifest, hash, sensitivity class, storage policy, and gate
status so the experiment remains auditable without exposing protected content.

The complete remaining route for all new multimodal experiments is now recorded
in
`70_experiments/runs/v2_0_multimodal_all_new_experiments_completion_plan_2026_06_01/`.
It defines the ordered path from repair-first Qwen/MOSS/MiniCPM/Step/Kimi/MOSS8
lanes through fixed-15, Taiwan utility, 30-row CDS, 258-row, selected-300, and
final closeout.

### Auto-Only Closeout: 2026-06-01

The no-human-review route is now executed as an aggregate-only Qwen automatic
semantic-damage proxy in
`70_experiments/runs/v2_0_multimodal_qwen_auto_semantic_damage_proxy_2026_06_01/`.
The proxy reads raw and OpenCC/Taiwan-term repaired transcript-bearing payloads
only from ignored local runtime lanes and tracks only aggregate blocker counts,
metrics, gate status, and manifest hashes.

The deterministic proxy checks CER/WER worsening, new hallucination proxy,
critical term / proper-noun changes, abbreviation changes, suspicious length
ratio changes, empty-output changes, locale residuals, and raw/repaired payload
pairing. Current aggregate result: all semantic-damage checks are clean except
the required locale residual check, which remains `7` rows. Because any
nonzero blocker stops the auto-only route, the current final state is recorded
in
`70_experiments/runs/v2_0_multimodal_auto_only_no_winner_stop_2026_06_01/`
as `auto_only_no_winner_stop`.

FIRST PRINCIPLE decision: without human review, the evidence supports a
no-winner conclusion under automatic-proxy rules, not a Taiwan utility,
30-row CDS, 258-row, or selected-300 claim. The next expansion path is bounded
LoRA feasibility with frozen baselines and post-training one-row / sentinel
gates; raw model capability, repaired deployment-pipeline behavior, automatic
proxy evidence, and fine-tuning evidence remain separate.

The bounded LoRA feasibility lane is now started in
`70_experiments/runs/v2_0_multimodal_bounded_lora_feasibility_start_2026_06_01/`.
It selects Step-Audio-2-mini as the first candidate because Step passed the
repaired one-row transcript contract and then failed no-speech / non-speech
sentinel controls. The initial training question is limited to sentinel
hallucination reduction. Training is not launched yet because the local private
training payload manifest and LoRA adapter-loading evaluator contract are not
ready; those gates must pass before any adapter training.

The locale-residual Qwen rows were first packaged locally in
`70_experiments/runs/v2_0_multimodal_qwen_expert_review_packet_2026_06_01/`.
The completed expert review is now summarized in
`70_experiments/runs/v2_0_multimodal_qwen_expert_review_completion_2026_06_01/`.
The completed ZIP, TSV, PDF, DOCX, and Markdown report remain outside Git
because they contain transcript-bearing fields and identifying fragments. Git
tracks only aggregate counts and file/hash/status records.

Expert-review result: `review_row_count=7`, `semantic_accept_rows=1`,
`semantic_minor_issue_rows=2`, `semantic_reject_rows=4`,
`critical_major_rows=5`, `critical_minor_rows=2`,
`hallucination_or_omission_rows=5`, and
`final_transcript_usable_rows=1`. The decision is
`do_not_promote_repaired_pipeline`: the Qwen repaired residual subset is useful
as deployment repair evidence, but it is not safe as final transcript evidence.
Taiwan utility, 30-row CDS, 258-row, and selected-300 remain closed for this
Qwen repaired-pipeline result.

### ASR-Control / LoRA Extension: 2026-06-01

The next ASR-control fine-tuning design is recorded in
`70_experiments/runs/v2_0_asr_controls_qwen3_firered_lora_plan_2026_06_01/`
and summarized in
`docs/v2_0_asr_controls_qwen3_firered_lora_plan.md`.

FIRST PRINCIPLE decision: the v2.0 multimodal no-human route closed as
`final_no_human_no_winner`, so the next useful experiment is a focused ASR
control lane rather than another open-ended audio LLM route. Qwen3-ASR and
FireRedASR are positioned as ASR-specific candidates because their public
model families target Chinese / dialect / English or code-switching speech
recognition. The plan keeps four evidence layers separate:

```text
raw ASR capability
-> deterministic Traditional Chinese deployment repair
-> automatic semantic-damage proxy
-> LoRA fine-tuning evidence
```

`Qwen/Qwen3-ASR-0.6B` already has negative fixed-15 evidence in this repo:
it is runnable, but failed the strict Taiwan Traditional Chinese locale gate
on all 15 pilot rows. Its next action is therefore not immediate large-split
promotion, but a repaired fixed-15 view using deterministic OpenCC /
Taiwan-term normalization followed by automatic semantic-damage proxy.

`Qwen/Qwen3-ASR-1.7B` remains behind runtime evidence: the current local check
timed out before first inference. Its next action is an isolated cache/runtime
retry with pinned versions, explicit timeout, GPU/resource summary, and exactly
one inference row before any fixed-15 or LoRA work.

FireRedASR enters through metadata, license, duration, dependency, and runtime
gates. FireRedASR-AED is the efficient short-audio baseline candidate;
FireRedASR-LLM is a heavier short-audio / code-switching candidate; FireRedASR2
is an optional metadata-gated newer branch after baseline FireRedASR evidence
exists.

LoRA is designed as a diagnostic-gated rank/alpha experiment rather than an
immediate full sweep. Imperfect CER/WER is not enough to open LoRA. Each model
must first produce raw/repaired fixed-15 evidence, locale behavior, automatic
semantic-damage proxy, subgroup taxonomy, and runtime status. LoRA opens only
for a fine-tuning-addressable failure such as stable locale style, repeated
Taiwan-term substitutions, English abbreviation errors, or domain lexical
omissions. The first smoke adapter is rank 4 / alpha 8; only a model that can
train, save locally, reload, and pass post-training one-row transcript
evaluation may expand to rank 8 / alpha 16, rank 16 / alpha 32, and optional
rank 16 / alpha 16 sensitivity. Adapter weights, payloads, row-level
transcripts, raw outputs, local paths, and model caches remain outside Git.

### Bounded LoRA Execution Status: 2026-06-01

Existing human-reviewed / accepted transcript ground truth can be used for
training data as long as the evaluation splits stay protected. The first
Step-Audio LoRA payload therefore uses a local-only 4-row smoke set: three
no-speech / non-speech sentinel rows targeting `無法辨識`, plus one accepted
ground-truth transcript anchor to protect transcript behavior. The payload is
stored only in the ignored Step runtime lane; the tracked pretraining gate is
`70_experiments/runs/v2_0_multimodal_step_audio_lora_pretraining_gate_2026_06_01/`.

The post-training evaluators now support `--adapter-dir`, so adapter evaluation
has a concrete contract. The first bounded smoke train is recorded in
`70_experiments/runs/v2_0_multimodal_step_audio_lora_smoke_train_2026_06_01/`.
Training execution did start, but it did not complete on the local 16GB GPU:
`device_map=auto` produced a meta/cuda placement error, and the single-device
CUDA retry hit out-of-memory before saving an adapter. This is resource-boundary
evidence for the LoRA lane, not model-improvement evidence.

### Repair-First Phase Progress: 2026-06-01

The first repair-first execution block has completed Phases 1-9 as
aggregate-only evidence.

Qwen2.5-Omni OpenCC / Taiwan-term repair is recorded in
`70_experiments/runs/v2_0_multimodal_batch1_qwen_opencc_locale_repair_2026_06_01/`.
This is deployment-pipeline evidence, not raw model capability. The repaired
variant reduces raw `locale_violation_rows=15` to `7` and
`simplified_char_rate=17.8466` to `0.5882`; it remains a
`repaired_pipeline_review_candidate` and requires human semantic-damage review
before any Taiwan utility/subgroup or CDS gate.

MOSS-Audio-4B sentinel repair is recorded in
`70_experiments/runs/v2_0_multimodal_batch1_moss_audio_4b_sentinel_repair_2026_06_01/`.
The stricter prompt does not clear the sentinel boundary:
`sentinel_pass_rows=3/6`, `hallucination_on_no_speech_rows=3`, and
`promotion_decision=do_not_promote`. MOSS 4B remains stopped before fixed
15-row scoring.

MiniCPM-o 4.5 sentinel repair is recorded in
`70_experiments/runs/v2_0_multimodal_batch1_minicpm_o_4_5_sentinel_repair_2026_06_01/`.
The stricter prompt improves the quantized local-feasibility result to
`sentinel_pass_rows=5/6` and removes summary / translation behavior, but
`hallucination_on_no_speech_rows=1` remains. The decision is still
`promotion_decision=do_not_promote`, so MiniCPM remains stopped before fixed
15-row scoring.

Step-Audio-2-mini transcript-contract repair is recorded in
`70_experiments/runs/v2_0_multimodal_batch1_step_audio_transcript_contract_repair_2026_06_01/`.
The stricter one-row prompt repairs the raw transcript contract:
`raw_transcript_like_outputs=1`, `repetition_outputs=0`, and
`promotion_decision=promote_to_sentinel`.

Kimi-Audio dependency repair is recorded in
`70_experiments/runs/v2_0_multimodal_batch1_kimi_audio_dependency_repair_2026_06_01/`.
The bounded audit confirms the isolated lane still lacks `flash_attn` and
`nvcc` is unavailable, so Kimi remains `blocked_runtime_dependency` without an
approved external/toolchain route.

MOSS-Audio-8B resource repair is recorded in
`70_experiments/runs/v2_0_multimodal_batch1_moss_audio_8b_resource_repair_2026_06_01/`.
The bounded audit confirms no local 16GB single-GPU route is proven: the 8B
artifact is about `16.87 GiB`, and the isolated MOSS runtime has no
`bitsandbytes` quantized route. MOSS 8B remains `blocked_runtime_resource`.

Step repaired sentinel controls are recorded in
`70_experiments/runs/v2_0_multimodal_batch1_step_audio_sentinel_controls_2026_06_01/`.
The repaired one-row transcript contract does not survive sentinel controls:
`sentinel_pass_rows=3/6`, `hallucination_on_no_speech_rows=3`, and
`promotion_decision=do_not_promote`.

FIRST PRINCIPLE decision: after Phases 3-9, there is no behavior-clean raw or
repaired multimodal survivor eligible for fixed 15-row rerun, Taiwan utility,
human-reviewed 30-row CDS, promoted 258-row, or selected-300. Qwen remains the
only repaired-pipeline review candidate, and it requires human semantic-damage
review before any larger repaired-pipeline gate.

The automatic repair-chain closeout is recorded in
`70_experiments/runs/v2_0_multimodal_repair_chain_completion_audit_2026_06_01/`.
It is a governed stop record, not a claim that human semantic review has been
completed.

The remaining completion plan is recorded in
`70_experiments/runs/v2_0_multimodal_remaining_completion_plan_2026_06_01/`.
The next concrete gate is a local-only Qwen repaired-pipeline human
semantic-damage review packet. If that review is declined or fails, the final
completion path is a no-winner stop synthesis. If it passes, the only open
larger route is explicitly labeled repaired-pipeline evidence: Taiwan
utility/subgroup, human-reviewed 30-row CDS, ASR-control calibration if needed,
then 258-row and selected-300 only for a stable, licensed, claim-relevant
scientific winner.

The fine-tuning readiness decision is recorded in
`70_experiments/runs/v2_0_multimodal_finetuning_readiness_design_2026_06_01/`.
The decision is `fine_tuning_now=false`. Fine-tuning can become a bounded LoRA
feasibility gate only after Qwen repaired-pipeline human review or an explicit
new repair design, and only for a narrow target such as no-speech /
non-speech sentinel hallucination. Step is the first future LoRA candidate if
training is approved; Kimi and MOSS 8B remain not ready before runtime /
resource repair.

The no-human-review completion route is recorded in
`70_experiments/runs/v2_0_multimodal_auto_only_completion_plan_2026_06_01/`.
This supersedes the human-review unlock for the current user constraint. The
next concrete gate is a deterministic Qwen automatic semantic-damage proxy
over local raw/repaired payloads, with only aggregate counts and manifest /
hash status tracked. If that proxy is not clean, the final state is
`auto_only_no_winner_stop`.

### Phase 3 Qwen OpenCC Locale Repair: 2026-06-01

Qwen2.5-Omni OpenCC / Taiwan-term locale repair is recorded in
`70_experiments/runs/v2_0_multimodal_batch1_qwen_opencc_locale_repair_2026_06_01/`.
This is deployment-pipeline repair evidence, not raw model capability. The
raw fixed-15 output remains the raw model conclusion: it failed the zh-TW
locale gate. The repaired-pipeline aggregate improves locale behavior:
`locale_violation_rows` changes from `15` to `7`, and
`simplified_char_rate` changes from `17.8466` to `0.5882`. Aggregate CER/WER
also improve under the documented CJK tokenizer fallback
(`cer_delta_raw_to_repaired=-22.8253`, `wer_delta_raw_to_repaired=-25.2689`).
The tracked decision is `repaired_pipeline_review_candidate`, with
`human_semantic_review_status=not_run`. Therefore the next Qwen gate is human
semantic-damage review for the repaired pipeline before any Taiwan
utility/subgroup or CDS gate.

Gate A manifest preflight is recorded in
`70_experiments/runs/v2_0_multimodal_batch1_manifest_preflight_2026_05_31/`.
It now finds the local-only one-row manifest, sentinel manifest, and fixed
15-row manifest, records `3/6` expected local manifests present, and keeps
local manifest values ignored and untracked. The 30-row, promoted 258-row, and
selected-300 manifests remain pending because no current raw Batch 1 model has
passed fixed 15-row.

Gate B adapter preflight is recorded in
`70_experiments/runs/v2_0_multimodal_batch1_adapter_preflight_2026_05_31/`.
It now records the ignored isolated runtime-lane state after Qwen, Step,
MOSS-Audio-4B, MiniCPM-o 4.5, Kimi, and MOSS-Audio-8B cache/runtime setup,
found the RTX 5080 and local one-row manifest, and did not run inference during
the preflight itself. Current
status:
`models_ready_for_smoke=6`,
`models_blocked_by_missing_runtime_modules=0`,
`models_blocked_by_missing_cache=0`, and
`models_deferred_by_gate_order=0`.

The Qwen2.5-Omni runtime/cache lane preparation is recorded in
`70_experiments/runs/v2_0_multimodal_batch1_qwen_runtime_lane_2026_05_31/`.
It confirms no repo-wide `.venv` modification and no remaining Qwen runtime
blockers. Qwen one-row transcript-only smoke is recorded in
`70_experiments/runs/v2_0_multimodal_batch1_qwen_one_row_smoke_2026_05_31/`.
The aggregate result is `valid_text_outputs=1`, `raw_transcript_like_outputs=1`,
and `promotion_decision=promote_to_sentinel`; the transcript-bearing output
remains local-only in the ignored runtime lane.

Qwen sentinel controls are recorded in
`70_experiments/runs/v2_0_multimodal_batch1_qwen_sentinel_controls_2026_06_01/`.
The aggregate result is `sentinel_pass_rows=6/6`,
`hallucination_on_no_speech_rows=0`, `instruction_followed_rows=0`, and
`promotion_decision=promote_to_15_row_candidate_pool`. The sentinel audio,
manifest, and model outputs remain local-only / ignored.

Qwen fixed 15-row transcript scoring is recorded in
`70_experiments/runs/v2_0_multimodal_batch1_qwen_fixed_15_row_transcript_gate_2026_06_01/`.
The aggregate result is `valid_output_rate=100.0`,
`raw_transcript_like_outputs=15/15`, `cer_zh_micro=126.7223`,
`wer_zh_jieba_micro=65.0538`, `simplified_char_rate=17.1829`,
`locale_violation_rows=15`, `runtime_seconds_per_row=63.1933`, and
`promotion_decision=do_not_promote`. This is strong negative evidence for the
raw zh-TW locale gate, not a reason to discard Qwen as a general audio model.
Qwen moves to a bounded prompt/locale repair lane before any Taiwan
utility/subgroup, 30-row CDS, 258-row, or selected-300 gate. The transcript-
bearing 15-row outputs remain local-only / ignored.

Step-Audio-2-mini runtime/cache preparation is recorded in
`70_experiments/runs/v2_0_multimodal_batch1_step_audio_runtime_lane_2026_06_01/`.
It confirms an ignored isolated runtime lane, local cache snapshot, CUDA
access, no repo-wide `.venv` modification, and no runtime import blockers.
Step one-row smoke is recorded in
`70_experiments/runs/v2_0_multimodal_batch1_step_audio_one_row_smoke_2026_06_01/`.
The aggregate result is `valid_text_outputs=1`,
`raw_transcript_like_outputs=0`, `repetition_outputs=1`, and
`promotion_decision=do_not_promote`. Step therefore stays in a bounded
prompt/runtime repair lane and cannot enter sentinel controls or fixed 15-row
scoring until raw transcript-like output is proven.

MOSS-Audio-4B runtime/cache preparation is recorded in
`70_experiments/runs/v2_0_multimodal_batch1_moss_audio_4b_runtime_lane_2026_06_01/`.
It confirms an ignored isolated OpenMOSS runtime lane, local 4B cache snapshot,
CUDA access, no repo-wide `.venv` modification, official torch 2.9.1+cu128 /
Transformers 4.57.1 runtime, and no runtime import blockers. MOSS-Audio-4B
one-row smoke is recorded in
`70_experiments/runs/v2_0_multimodal_batch1_moss_audio_4b_one_row_smoke_2026_06_01/`.
The aggregate result is `valid_text_outputs=1`,
`raw_transcript_like_outputs=1`, `summary_or_answer_outputs=0`,
`translation_outputs=0`, `tts_only_outputs=0`,
`invented_timestamp_outputs=0`, `invented_speaker_label_outputs=0`, and
`promotion_decision=promote_to_sentinel`. The transcript-bearing output remains
local-only in the ignored MOSS runtime lane.

MiniCPM-o 4.5 runtime/cache preparation is recorded in
`70_experiments/runs/v2_0_multimodal_batch1_minicpm_o_4_5_runtime_lane_2026_06_01/`.
It confirms an ignored isolated MiniCPM runtime lane, local cache snapshot,
CUDA access, no repo-wide `.venv` modification, no runtime import blockers,
and a 4-bit NF4 inference policy because full-bf16 single-GPU loading exceeds
the local 16GB GPU boundary while CPU offload hits an audio-encoder
meta-tensor boundary. MiniCPM-o 4.5 one-row smoke is recorded in
`70_experiments/runs/v2_0_multimodal_batch1_minicpm_o_4_5_one_row_smoke_2026_06_01/`.
The aggregate result is `valid_text_outputs=1`,
`raw_transcript_like_outputs=1`, `summary_or_answer_outputs=0`,
`translation_outputs=0`, `tts_only_outputs=0`,
`invented_timestamp_outputs=0`, `invented_speaker_label_outputs=0`, and
`promotion_decision=promote_to_sentinel`. This is local deployment feasibility
and transcript-contract evidence, not full-bf16 quality evidence. The
transcript-bearing output remains local-only in the ignored MiniCPM runtime
lane.

MOSS-Audio-4B sentinel controls are recorded in
`70_experiments/runs/v2_0_multimodal_batch1_moss_audio_4b_sentinel_controls_2026_06_01/`.
The aggregate result is `sentinel_pass_rows=3/6`,
`hallucination_on_no_speech_rows=3`, `instruction_followed_rows=0`,
`failure_mode=sentinel_behavior_violation`, and
`promotion_decision=do_not_promote`. This means the one-row transcript-like
success is not sufficient evidence for fixed 15-row promotion. MOSS 4B stays
in a sentinel repair/rerun lane; sentinel audio, manifest values, and model
outputs remain local-only / ignored.

MiniCPM-o 4.5 sentinel controls are recorded in
`70_experiments/runs/v2_0_multimodal_batch1_minicpm_o_4_5_sentinel_controls_2026_06_01/`.
The aggregate result is `sentinel_pass_rows=3/6`,
`hallucination_on_no_speech_rows=1`, `summary_or_answer_rows=2`,
`translation_rows=2`, `instruction_followed_rows=0`,
`failure_mode=sentinel_behavior_violation`, and
`promotion_decision=do_not_promote`. This remains quantized local-feasibility
evidence and does not justify fixed 15-row promotion. MiniCPM stays in a
sentinel repair/rerun lane; sentinel audio, manifest values, and model outputs
remain local-only / ignored.

Kimi-Audio runtime/cache preparation is recorded in
`70_experiments/runs/v2_0_multimodal_batch1_kimi_audio_runtime_lane_2026_06_01/`.
It confirms the explicit `Kimi-Audio-7B-Instruct` / HF-widget `10B params`
size-boundary layer, an ignored isolated Kimi runtime lane, the official repo
submodule initialization, a local transcript-only snapshot policy that excludes
TTS detokenizer/vocoder artifacts, and no repo-wide `.venv` modification. Kimi
one-row smoke is recorded in
`70_experiments/runs/v2_0_multimodal_batch1_kimi_audio_one_row_smoke_2026_06_01/`.
The aggregate result is `smoke_status=failed:RuntimeError`,
`failure_mode=runtime_dependency_error:flash_attn_required_by_official_main_model_remote_code`,
and `promotion_decision=blocked_runtime_dependency`. This is not a scientific
quality rejection; it is a reproducible runtime dependency boundary before any
sentinel, 15-row, or CDS scoring gate.

MOSS-Audio-8B runtime/cache preparation is recorded in
`70_experiments/runs/v2_0_multimodal_batch1_moss_audio_8b_runtime_lane_2026_06_01/`.
It confirms an ignored isolated MOSS runtime lane, local 8B cache snapshot,
official repo head, Apache-2.0 metadata, no repo-wide `.venv` modification, and
an explicit memory-boundary warning because the 8B artifact is materially
larger than the 4B candidate on a local 16GB GPU. MOSS-Audio-8B one-row smoke
is recorded in
`70_experiments/runs/v2_0_multimodal_batch1_moss_audio_8b_one_row_smoke_2026_06_01/`.
The aggregate result is `smoke_status=failed:RuntimeError`,
`failure_mode=resource_error:cuda_out_of_memory`, and
`promotion_decision=blocked_runtime_resource`. This is not a transcript-quality
result; MOSS 8B cannot enter sentinel controls, fixed 15-row scoring, 258-row,
or selected-300 until a bounded resource route is proven.

Post-Gate0 completion path:

1. repair or route around Kimi's official `flash_attn` dependency boundary only
   in an isolated runtime lane, while preserving the size-boundary wording；
2. run a separate Step prompt/runtime repair, Kimi dependency repair, or MOSS
   8B resource repair only if the repair is bounded and isolated；
3. record the completed sentinel controls and Qwen fixed 15-row gate: Qwen
   passed sentinel but failed the raw 15-row zh-TW locale gate; MOSS-Audio-4B
   and MiniCPM-o 4.5 failed sentinel behavior controls and require bounded
   repair/rerun before any larger gate；
4. prepare local-only manifests for human-reviewed 30-row, promoted 258-row,
   and selected-300 only after a clean fixed 15-row survivor exists；
5. promote only clean candidates to Taiwan utility/subgroup audit and
   human-reviewed 30-row CDS evidence；
6. refresh ASR controls for calibration, with Qwen3-ASR and Whisper-style
   baselines as the main Mandarin comparison anchors；
7. escalate to 258-row and selected-300 only for scientific winners with clean
   runtime, locale, privacy, and license evidence；
8. keep voice-interaction and long-audio/reasoning lanes separate until they
   pass the transcript-only adapter.

### Bounded Step-Audio LoRA Update: 2026-06-01

Existing accepted / human-reviewed transcript ground truth is valid supervised
training data for this project when split boundaries are preserved. The v2.0
training lane therefore treats accepted transcript anchors as usable training
supervision, while test, selected-300, CDS evaluation, and any transcript-
bearing payloads remain protected by the local-only / manifest-hash policy.

The first Step-Audio LoRA payload is recorded in
`70_experiments/runs/v2_0_multimodal_step_audio_lora_pretraining_gate_2026_06_01/`.
It is a local-only 4-row smoke payload: 3 no-speech / non-speech negative
controls plus 1 accepted transcript anchor. Git tracks only aggregate counts,
sensitivity/storage policy, hash status, and evaluator-contract status.

Two execution attempts are now recorded:

```text
70_experiments/runs/v2_0_multimodal_step_audio_lora_smoke_train_2026_06_01/
70_experiments/runs/v2_0_multimodal_step_audio_lora_quantized_smoke_train_2026_06_01/
70_experiments/runs/v2_0_multimodal_step_audio_lora_quantized_no_input_grad_smoke_train_2026_06_01/
70_experiments/runs/v2_0_multimodal_step_audio_lora_post_one_row_2026_06_01/
70_experiments/runs/v2_0_multimodal_step_audio_lora_post_sentinel_controls_2026_06_01/
```

The non-quantized attempt started training but stopped before adapter save at
the local 16GB GPU resource boundary. The quantized 4-bit NF4 attempt loaded
the checkpoint shards and started the training path, but stopped before adapter
save with a Step remote-code / k-bit autograd compatibility error:
`RuntimeError:a view of a leaf Variable that requires grad is being used in an
in-place operation.`

The follow-up 4-bit NF4 route without the input-require-grad hook completed
training and created a local-only adapter. The tracked record reports
`train_steps=4`, `trainable_parameters=1261568`, `first_loss=1.035483`,
`last_loss=0.641448`, and adapter hash
`14a0fdfb45009b2a452dbbdf5c3efd0b54dac935547715b55a9a29e65b39e5a6`; adapter
weights stay outside Git. Post-training one-row evaluation passed the
transcript contract and promoted the adapter to sentinel controls. The
post-training sentinel gate then completed with `sentinel_pass_rows=3/6` and
`hallucination_on_no_speech_rows=3`, so the LoRA iteration remains
`do_not_promote`.

FIRST PRINCIPLE decision: LoRA feasibility is now proven at the smoke level,
including adapter creation and adapter-loading evaluation. Model-improvement
evidence is not proven because the trained adapter did not solve the target
no-speech / non-speech hallucination failure. Larger gates remain closed; the
next training action must change the intervention design before rerunning the
same one-row -> sentinel sequence.

### Failure-Informed No-Human Completion Route: 2026-06-01

The complete remaining route after Qwen expert review and Step LoRA iteration 1
is recorded in
`70_experiments/runs/v2_0_multimodal_failure_informed_no_human_completion_plan_2026_06_01/`.

The failure analysis groups the remaining work into five clusters:

1. Qwen repaired-pipeline semantic damage blocks final transcript use.
2. Step, MOSS 4B, and MiniCPM failures concentrate on no-speech / non-speech
   hallucination and behavior-control sentinels.
3. Step LoRA is technically feasible, but iteration 1 did not solve the target
   sentinel failure.
4. Kimi remains a runtime-dependency lane before quality evidence.
5. MOSS 8B remains a resource lane before quality evidence.

The next recommended non-human solution is deterministic deployment repair
before more model scaling: add an audio-only acoustic no-speech / non-speech
guard that can return `無法辨識` before prompting the audio LLM. This directly
targets the most repeated failure cluster and keeps the claim separate from raw
model capability. If the guard route has no survivor, the next training route
is Step-Audio LoRA iteration 2 with a changed negative-weighted intervention,
not a repeat of iteration 1.

The completion state remains one of two outcomes: a scoped non-human repaired
or fine-tuned survivor that passes all prior gates, or a final no-human
no-winner closeout after deterministic guard, changed LoRA, and optional
bounded runtime/resource routes have evidence.

The first deterministic guard gates are now executed as aggregate-only records:

```text
70_experiments/runs/v2_0_multimodal_acoustic_guard_design_2026_06_01/
70_experiments/runs/v2_0_multimodal_acoustic_guard_manifest_preflight_2026_06_01/
70_experiments/runs/v2_0_multimodal_step_audio_guarded_one_row_2026_06_01/
70_experiments/runs/v2_0_multimodal_step_audio_guarded_sentinel_2026_06_01/
70_experiments/runs/v2_0_multimodal_moss4_guarded_sentinel_2026_06_01/
70_experiments/runs/v2_0_multimodal_minicpm_guarded_sentinel_2026_06_01/
70_experiments/runs/v2_0_multimodal_guarded_survivor_audit_2026_06_01/
```

The guard uses audio-only aggregate features to route silence, stationary tone,
and broadband noise to the fixed safe output `無法辨識` before audio LLM
prompting. It is deployment-repair evidence. It is not raw model capability.
Under guarded replay, Step-Audio, MOSS 4B, and MiniCPM all reach
`sentinel_pass_rows=6/6` and `hallucination_on_no_speech_rows=0`; the survivor
audit therefore opens only the next fixed-15 transcript / zh-TW locale gate for
these three guarded pipelines. Taiwan utility, 30-row CDS, 258-row, and
selected-300 remain closed.

### Failure-Informed No-Human Roadmap: 2026-06-01

The updated no-human completion roadmap is recorded in
`70_experiments/runs/v2_0_multimodal_failure_informed_full_completion_roadmap_2026_06_01/`.
It starts from the completed Qwen expert-review negative evidence,
Step-Audio LoRA iteration 1 post-sentinel failure, and deterministic acoustic
guard survivor audit. The current next gate is guarded fixed-15 transcript and
zh-TW locale scoring for Step-Audio-2-mini, MOSS-Audio-4B-Instruct, and
MiniCPM-o 4.5.

FIRST PRINCIPLE decision: the scarce resource is claim-evidence alignment after
observed failures. Guarded survivors are deployment-repair candidates, not raw
model winners. They cannot enter Taiwan utility/subgroup, human-reviewed
30-row CDS, 258-row, or selected-300 until fixed-15 and deterministic automatic
semantic-damage proxy both pass. If the guarded route closes with no survivor,
the only training route is a changed Step LoRA iteration 2 design targeting
no-speech / non-speech hallucination; if that also fails sentinel, the correct
completion state is final no-human no-winner closeout.

### Step Guarded Fixed-15 And Proxy: 2026-06-01

Step-Audio-2-mini now has guarded fixed-15 and deterministic semantic-proxy
evidence:

```text
70_experiments/runs/v2_0_multimodal_step_audio_guarded_fixed_15_2026_06_01/
70_experiments/runs/v2_0_multimodal_step_audio_guarded_auto_semantic_proxy_2026_06_01/
70_experiments/runs/v2_0_multimodal_guarded_route_no_winner_stop_2026_06_01/
```

The fixed-15 gate is deployment-repair evidence: the acoustic guard passed all
15 rows to the model, `valid_output_rate=100.0`, `raw_transcript_like_outputs=15/15`,
`simplified_char_rate=0.0`, and `locale_violation_rows=0`. The same run records
very high transcript error (`cer_zh_micro=99.0953`,
`wer_zh_jieba_micro=99.1551`), so it only promotes to deterministic semantic
proxy. The proxy then records `semantic_damage_blocker_rows=77` and
`decision=guarded_route_no_winner_stop`. Step is therefore closed for Taiwan
utility/subgroup, 30-row CDS, 258-row, and selected-300 under this guarded
route. MOSS-Audio-4B-Instruct and MiniCPM-o 4.5 remain the two guarded
fixed-15 candidates.

### No-Human Final Completion: 2026-06-01

The no-human v2.0 multimodal route is now closed in
`70_experiments/runs/v2_0_multimodal_no_human_final_completion_audit_2026_06_01/`
with `status=final_no_human_no_winner`.

Guarded fixed-15 was completed for all three guarded sentinel survivors:

| Model | Furthest no-human gate | Decision |
| --- | --- | --- |
| Step-Audio-2-mini | automatic semantic-damage proxy | stopped with `semantic_damage_blocker_rows=77` |
| MOSS-Audio-4B-Instruct | guarded fixed-15 | stopped with `locale_violation_rows=5` and `simplified_char_rate=1.8868` |
| MiniCPM-o 4.5 | guarded fixed-15 | stopped with `raw_transcript_like_outputs=14/15`, `locale_violation_rows=14`, and `simplified_char_rate=15.2322` |

No model reaches Taiwan utility/subgroup, human-reviewed 30-row CDS, promoted
258-row, or selected-300. Optional Kimi and MOSS8 capacity routes remain
deferred behind bounded external/runtime evidence and do not bypass one-row or
sentinel gates. The final supported claim is negative and scoped: deterministic
guarding improves no-speech / non-speech sentinel behavior, but no no-human
pipeline in this run produces claim-aligned CDS-ASR transcript evidence.

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

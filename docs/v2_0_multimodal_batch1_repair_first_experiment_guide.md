# v2.0 Batch 1 多模態模型 repair-first 實驗指引

Date: 2026-06-01

Status: design and execution guide after the first raw Batch 1 completion
audit. This file records the next complete experiment design for all Batch 1
primary multimodal audio models after the raw gate chain produced no scientific
winner. Phase 3 Qwen OpenCC/Taiwan-term repair, Phase 4 MOSS-Audio-4B sentinel
repair, and Phase 5 MiniCPM-o 4.5 sentinel repair have now been executed and
recorded as aggregate-only repair evidence.

本文件記錄 repair-first 實驗設計、gate、指標、artifact、validator、tracking
policy、privacy boundary 與 Codex execution prompt。新的追蹤原則是：
**原始音檔不進 Git；其他實驗紀錄必須可追蹤**。可公開且 repo-safe 的紀錄直接
tracked；可能含 row-level、逐字稿、reference、hypothesis、model output、reviewer
note、local path 或 transcript-bearing log 的紀錄，必須先轉成 redacted /
aggregate / hashed manifest / controlled-store index 後再 tracked。換句話說，
敏感內容本體不直接進公開 Git，但它的存在、版本、gate status、摘要統計、hash
或 controlled-store locator 必須留下 tracked record。

## FIRST PRINCIPLE

第一原理：現在最缺的不是更多模型，也不是直接把 15-row 擴成 30-row 或 258-row。
真正缺的是「可驗證的修復路徑」：

```text
raw model output
-> transcript contract
-> sentinel ASR-boundary behavior
-> raw zh-TW locale gate
-> post-processing repair gate
-> repair delta / damage audit
-> CDS-ASR gate only if raw + repaired evidence both可解釋
```

OpenCC、台灣詞表、normalizer、prompt repair 都是 deployment pipeline 的能力。
它們可以證明「部署管線能不能把模型輸出修到可用」，但不能回頭改寫 raw model
capability。因此所有實驗必須同時保留兩種結論：

1. raw model conclusion: 模型原始輸出是否通過 transcript / sentinel / locale gate；
2. repaired pipeline conclusion: 後處理是否降低繁中、台灣詞、專有名詞與 CDS 風險。

## Scope

Primary zh-TW audio LLM lane:

```text
Kimi-Audio-7B-Instruct
Qwen2.5-Omni-7B
Step-Audio-2-mini
MOSS-Audio-4B-Instruct
MOSS-Audio-8B-Instruct
MiniCPM-o 4.5
```

Current raw completion audit:

```text
70_experiments/runs/v2_0_multimodal_batch1_completion_audit_2026_06_01/
```

Current raw conclusion:

```text
batch1_gate_chain_complete_no_scientific_winner
```

## Repair Lane Classes

| Lane | Model | Current raw evidence | Repair objective | Next gate |
| --- | --- | --- | --- | --- |
| A | Qwen2.5-Omni-7B | passed one-row and sentinel; failed fixed 15-row zh-TW locale | post-processing locale repair with raw/repaired separation | OpenCC + term repair fixed-15 rescoring |
| B | MOSS-Audio-4B-Instruct | passed one-row; failed sentinel behavior | reduce no-speech / non-speech hallucination before scoring | sentinel repair/rerun |
| C | MiniCPM-o 4.5 | passed one-row under 4-bit NF4; failed sentinel behavior | reduce no-speech hallucination, summary/translation behavior | sentinel repair/rerun with quantized boundary |
| D | Step-Audio-2-mini | produced valid text but not transcript-like output | repair prompt/runtime transcript contract | one-row rerun |
| E | Kimi-Audio-7B-Instruct | blocked by `flash_attn` / CUDA-toolchain boundary | make transcript-only runtime runnable | one-row rerun |
| F | MOSS-Audio-8B-Instruct | blocked by local 16GB single-GPU OOM | define bounded resource route | one-row rerun |

## Universal Tracking And Evidence Rules

Every repaired experiment must write these repo-safe tracked artifacts:

```text
README.md
repair_config_summary.tsv
repair_metric_summary.tsv
repair_behavior_summary.tsv
repair_locale_summary.tsv
gate_summary.json
```

If an experiment produces non-audio row-level records, model outputs, repaired
text, transcripts, references, or review notes, the tracking rule is:

```text
raw audio: never tracked
repo-safe aggregate summaries: always tracked
redacted row-level records: tracked only after privacy review
hash / manifest / controlled-store index: tracked for every non-audio local artifact
local transcript-bearing payload: local or controlled-store until approved
```

Required tracked proof for local or controlled non-audio artifacts:

```text
artifact_class
artifact_count
content_sensitivity
storage_policy
hash_or_manifest_status
gate_status
promotion_decision
```

Tracked public artifacts must not directly expose raw text, repaired text, row
identifiers, audio identifiers, reviewer notes, local file paths, prompts
containing row content, or model outputs unless those records have been
explicitly redacted and approved as repo-safe. The point is full traceability,
not uncontrolled disclosure.

## Text Variants To Score

For every model that produces transcript-like text, score these variants
separately:

| Variant | Meaning | Can support raw model claim? | Can support deployment claim? |
| --- | --- | --- | --- |
| `raw` | model original text output | yes | baseline only |
| `opencc_s2tw` | raw output after Simplified-to-Taiwan Traditional conversion | no | yes |
| `opencc_s2twp` | raw output after Simplified-to-Taiwan Traditional plus phrase conversion | no | yes |
| `opencc_s2twp_terms` | `s2twp` plus project glossary / Taiwan proper-noun normalizer | no | yes |

Required reporting rule:

```text
raw_score != repaired_score
```

The paper-facing table may include repaired results only under a deployment
repair section or appendix. The main raw ASR/multimodal capability conclusion
must use raw outputs.

## Metrics

### Transcript Metrics

Use the same scoring policy as the current CDS-ASR evidence chain:

```text
cer_zh_micro
wer_zh_jieba_micro
valid_output_rate
raw_transcript_like_output_rate
```

If `jieba` is unavailable in an isolated runtime, record the tokenizer boundary
explicitly and do not present the field as journal-grade jieba WER.

### Locale Metrics

Required aggregate fields:

```text
simplified_char_rate_raw
simplified_char_rate_opencc_s2tw
simplified_char_rate_opencc_s2twp
simplified_char_rate_opencc_s2twp_terms
locale_violation_rows_raw
locale_violation_rows_repaired
taiwan_term_error_rows_raw
taiwan_term_error_rows_repaired
proper_noun_error_rows_raw
proper_noun_error_rows_repaired
english_abbreviation_error_rows_raw
english_abbreviation_error_rows_repaired
```

### Repair Delta Metrics

Required aggregate deltas:

```text
cer_delta_raw_to_s2twp_terms
wer_delta_raw_to_s2twp_terms
simplified_char_rate_delta
locale_violation_row_delta
term_error_row_delta
proper_noun_error_row_delta
semantic_damage_rows
meaning_changed_rows
new_hallucination_rows_after_repair
```

Interpretation:

- positive repair: lower simplified rate and locale errors without increasing
  CER/WER or semantic damage；
- formatting-only repair: lower simplified rate, but no CER/WER or term
  improvement；
- harmful repair: semantic damage, new hallucination, or higher critical term
  error；
- insufficient repair: locale improves but transcript content remains too
  inaccurate for CDS-ASR use.

### Behavior Metrics

Continue to track:

```text
summary_or_answer_rows
translation_rows
tts_only_rows
invented_timestamp_rows
invented_speaker_label_rows
repetition_rows
hallucination_on_no_speech_rows
instruction_followed_rows
```

OpenCC repair does not fix behavior violations. A model that summarizes,
translates, follows spoken instructions, or hallucinates no-speech content must
pass behavior repair before it enters transcript scoring.

## Model-Specific Experiment Plans

### Lane A: Qwen2.5-Omni-7B OpenCC Locale Repair

Current evidence:

```text
Qwen passed one-row and sentinel.
Qwen fixed 15-row produced raw transcript-like outputs for 15/15 rows.
Qwen failed raw zh-TW locale gate with locale_violation_rows=15.
```

Experiment:

```text
raw fixed-15 outputs.local.jsonl
-> OpenCC s2tw
-> OpenCC s2twp
-> OpenCC s2twp + Taiwan term glossary
-> aggregate rescoring
```

Tracked run name:

```text
v2_0_multimodal_batch1_qwen_opencc_locale_repair_2026_06_01
```

Promotion rule:

- If repaired output reduces locale violations without semantic damage, Qwen
  may enter a deployment repair discussion.
- Qwen still does not become a raw zh-TW model-quality winner unless a future
  raw rerun passes the locale gate without OpenCC repair.
- Taiwan utility/subgroup and 30-row CDS can run only as a repaired-pipeline
  experiment with the repaired label visible in every artifact.

### Lane B: MOSS-Audio-4B Sentinel Repair

Current evidence:

```text
MOSS 4B passed one-row transcript-like smoke.
MOSS 4B failed sentinel with hallucination_on_no_speech_rows=3.
```

Experiment:

1. keep the same sentinel manifest；
2. test a stricter transcript-only prompt；
3. test decoding constraints if supported；
4. keep TTS/generation disabled；
5. rerun sentinel before any 15-row scoring。

Promotion rule:

- MOSS 4B must reach `sentinel_pass_rows=6/6` and
  `hallucination_on_no_speech_rows=0`.
- OpenCC repair is not allowed until MOSS 4B passes sentinel and reaches
  fixed 15-row transcript scoring.

Executed result:

```text
v2_0_multimodal_batch1_moss_audio_4b_sentinel_repair_2026_06_01
sentinel_pass_rows=3/6
hallucination_on_no_speech_rows=3
promotion_decision=do_not_promote
```

Decision: the stricter prompt did not clear the sentinel behavior boundary.
MOSS 4B remains stopped before fixed 15-row, Taiwan utility, 30-row CDS,
258-row, or selected-300.

### Lane C: MiniCPM-o 4.5 Sentinel Repair

Current evidence:

```text
MiniCPM-o 4.5 passed one-row transcript-like smoke under 4-bit NF4.
MiniCPM failed sentinel with hallucination, summary, and translation behavior.
```

Experiment:

1. preserve the quantized local-feasibility label；
2. rerun sentinel with transcript-only prompt and no TTS output；
3. record whether the failure is prompt-following, model behavior, or
   quantized-runtime sensitivity；
4. if full-bf16 becomes available later, rerun as a separate quality-scope
   experiment。

Promotion rule:

- MiniCPM must pass sentinel before fixed 15-row.
- Any 15-row result under 4-bit NF4 must be reported as quantized deployment
  evidence, not full-bf16 model quality evidence.

Executed result:

```text
v2_0_multimodal_batch1_minicpm_o_4_5_sentinel_repair_2026_06_01
sentinel_pass_rows=5/6
hallucination_on_no_speech_rows=1
summary_or_answer_rows=0
translation_rows=0
promotion_decision=do_not_promote
```

Decision: the repair improves MiniCPM behavior under the quantized local
feasibility boundary, but one no-speech / non-speech hallucination remains.
MiniCPM remains stopped before fixed 15-row, Taiwan utility, 30-row CDS,
258-row, or selected-300.

### Lane D: Step-Audio-2-mini Transcript-Contract Repair

Current evidence:

```text
Step produced valid text but raw_transcript_like_outputs=0 and repetition_outputs=1.
```

Experiment:

1. revise transcript-only prompt；
2. reduce conversational / answer-style behavior；
3. rerun one-row only；
4. advance to sentinel only if raw transcript-like output is proven。

Promotion rule:

- Step must first pass one-row transcript contract.
- OpenCC repair is not meaningful until there is transcript-like text to
  repair.

### Lane E: Kimi-Audio Runtime Dependency Repair

Current evidence:

```text
Kimi remains primary with 7B-label / 10B-widget size-boundary wording.
The one-row attempt is blocked by flash_attn dependency in the isolated lane.
```

Experiment:

1. repair the isolated runtime without changing repo-wide `.venv`；
2. document CUDA / `nvcc` / `flash_attn` resolution；
3. rerun one-row transcript-only smoke；
4. only then decide sentinel eligibility。

Promotion rule:

- Kimi must produce one raw transcript-like output before any OpenCC or
  sentinel work.
- The size-boundary wording remains mandatory until loaded-parameter evidence
  is recorded.

### Lane F: MOSS-Audio-8B Resource Route Repair

Current evidence:

```text
MOSS 8B runtime/cache lane exists.
One-row attempt hit local 16GB single-GPU OOM before text generation.
```

Experiment:

1. test a bounded resource route: lower precision, CPU offload, sharded device
   map, shorter audio, or external GPU route；
2. record the resource route as deployment feasibility；
3. rerun one-row transcript-only smoke only after load succeeds。

Promotion rule:

- MOSS 8B must pass one-row before sentinel.
- A resource-routed result must not be compared directly with MOSS 4B raw
  single-GPU behavior unless the runtime difference is visible in the table.

## Gate Order After Repair

```text
repair setup
-> one-row transcript-only rerun if needed
-> sentinel rerun if one-row passes
-> fixed 15-row raw scoring if sentinel passes
-> OpenCC / glossary repair scoring if raw locale fails but transcript is usable
-> repair delta and semantic damage audit
-> Taiwan utility/subgroup only if raw or repaired-pipeline question is approved
-> 30-row CDS only if transcript validity, locale behavior, and repair damage are interpretable
-> 258-row / selected-300 only for scientific winners
```

## Stop Rules

Stop the lane when any of these happens:

1. no transcript-like output after prompt/runtime repair；
2. sentinel hallucination remains above zero for no-speech / non-speech rows；
3. repair introduces semantic damage or new hallucination；
4. repaired output cannot preserve medical / local proper nouns；
5. runtime route changes the comparison so much that the result is only a
   deployment feasibility note；
6. no repaired or raw result can support the CDS-ASR research question。

## Required Validators

Every repair lane should add a lane-specific validator that checks:

```text
required files exist
privacy flags are false
raw and repaired metrics are separated
no prohibited TSV headers or JSON keys
promotion decision is compatible with gate results
no larger gate is marked runnable before prior gate passes
```

Use a shared prohibited-key set:

```text
audio_id
row_id
sample_id
reference_text
transcript
transcript_text
hypothesis
hypothesis_text
local_audio_path
raw_audio_path
reviewer_notes
cache_path
output_text
prompt
audio_path
path
```

## Minimal First Execution

Start with Qwen because it already has local transcript-like fixed-15 outputs
and its raw failure is specifically a locale failure:

```text
v2_0_multimodal_batch1_qwen_opencc_locale_repair_2026_06_01
```

Then proceed in this order:

1. Qwen OpenCC / term repair fixed-15 rescoring；
2. MOSS 4B sentinel repair/rerun；
3. MiniCPM sentinel repair/rerun；
4. Step transcript-contract one-row repair；
5. Kimi runtime dependency repair；
6. MOSS 8B resource repair。

Current progress: steps 1-6 are complete. Qwen is waiting for human
semantic-damage review as a repaired pipeline. MOSS 4B, MiniCPM, and Step are
stopped by sentinel behavior. Kimi remains blocked by the bounded
`flash_attn` / `nvcc` dependency audit, and MOSS 8B remains blocked by the
bounded local 16GB single-GPU resource audit. There is no behavior-clean
repaired survivor for fixed 15-row.

Auto-only update: because human semantic-damage review is disallowed in the
current route, Qwen now has a deterministic automatic semantic-damage proxy in
`70_experiments/runs/v2_0_multimodal_qwen_auto_semantic_damage_proxy_2026_06_01/`.
The proxy keeps transcript-bearing payloads local-only and records only
aggregate counts and manifest hashes. It stops on `locale_residual_rows=7`,
with all non-locale semantic-damage proxy checks at `0`. The final auto-only
closeout is
`70_experiments/runs/v2_0_multimodal_auto_only_no_winner_stop_2026_06_01/`.
This preserves the repair-first claim boundary and moves any further work to a
separate bounded LoRA feasibility route.

Expert-review update: the Qwen locale-residual packet has now been returned as
a completed local-only review package and summarized in
`70_experiments/runs/v2_0_multimodal_qwen_expert_review_completion_2026_06_01/`.
The expert aggregate result is `semantic_accept_rows=1/7`,
`semantic_reject_rows=4/7`, `critical_major_rows=5/7`,
`hallucination_or_omission_rows=5/7`, and
`final_transcript_usable_rows=1/7`. Decision:
`do_not_promote_repaired_pipeline`. This does not reopen larger Qwen gates; it
confirms that the repaired residual subset is not safe as final transcript
evidence.

The bounded LoRA route has now started in
`70_experiments/runs/v2_0_multimodal_bounded_lora_feasibility_start_2026_06_01/`.
It chooses Step-Audio-2-mini as the first candidate and limits the initial
target to no-speech / non-speech sentinel hallucination reduction. Training is
not launched from the repair guide itself; the LoRA lane must first produce a
local-only payload manifest and adapter-loading evaluator contract.

Step-Audio LoRA has now progressed into its own execution lane. The local-only
pretraining payload and evaluator contract are recorded in
`70_experiments/runs/v2_0_multimodal_step_audio_lora_pretraining_gate_2026_06_01/`.
The first smoke-train attempt is recorded in
`70_experiments/runs/v2_0_multimodal_step_audio_lora_smoke_train_2026_06_01/`.
Training started but stopped before adapter save at the local GPU resource
boundary, so the next LoRA action is resource-route design rather than larger
evaluation.

The first resource-route attempt is now also recorded in
`70_experiments/runs/v2_0_multimodal_step_audio_lora_quantized_smoke_train_2026_06_01/`.
It uses 4-bit NF4 loading with `bitsandbytes` installed only in the ignored
Step runtime lane. The run started but stopped before adapter save with a
Step remote-code / k-bit autograd compatibility error. This keeps the LoRA
lane alive as backend/resource feasibility work, but it does not create an
adapter and does not unlock post-training or larger CDS-ASR gates.

The next resource-route attempt removed the input-require-grad hook from the
4-bit path and completed:

```text
70_experiments/runs/v2_0_multimodal_step_audio_lora_quantized_no_input_grad_smoke_train_2026_06_01/
70_experiments/runs/v2_0_multimodal_step_audio_lora_post_one_row_2026_06_01/
70_experiments/runs/v2_0_multimodal_step_audio_lora_post_sentinel_controls_2026_06_01/
```

The local-only adapter was created and hashed, post-training one-row passed,
and post-training sentinel controls still failed with
`sentinel_pass_rows=3/6` and `hallucination_on_no_speech_rows=3`. This is the
correct stopping point for LoRA iteration 1: feasibility is proven, but the
target failure remains, so larger gates remain closed.

## Codex Goal Prompt

```text
Using FIRST PRINCIPLE, execute the v2.0 Batch 1 multimodal repair-first
experiment plan in /home/jnln3799/every_on_git_ubuntu/cib-semantic-risk-asr.

Start from:
70_experiments/runs/v2_0_multimodal_batch1_completion_audit_2026_06_01/

Follow:
docs/v2_0_multimodal_batch1_repair_first_experiment_guide.md

First run Qwen2.5-Omni OpenCC / Taiwan-term locale repair on the existing
fixed-15 local outputs. Preserve raw outputs and repaired outputs as separate
evidence. Do not track raw audio. Track all repo-safe experiment records,
including aggregate metrics, gate decisions, repair configuration, validator
results, and controlled-artifact manifests. If row-level non-audio records,
transcripts, references, hypotheses, reviewer notes, local paths, model
outputs, or transcript-bearing logs are needed, keep payloads local or in the
controlled store unless redacted, but track their manifest/hash/status so the
experiment remains fully auditable.

For every repaired lane, write aggregate-only run records, add a validator,
update docs/model_evaluation_state.md,
docs/v2_0_multimodal_batch1_execution_runbook.md,
docs/v2_0_multimodal_batch1_full_completion_plan.md,
docs/v2_0_multimodal_batch1_repair_first_experiment_guide.md, and
70_experiments/registry.tsv. Run py_compile, validators, TSV checks,
git diff --check, and transcript-bearing leak scan. Commit logical slices
separately and push non-force to origin main while preserving local and remote
commits.
```

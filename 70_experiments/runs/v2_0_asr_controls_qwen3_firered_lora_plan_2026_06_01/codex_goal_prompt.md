# Codex Goal Prompt

```text
Using FIRST PRINCIPLE, execute and complete the v2.0 ASR-control baseline +
LoRA experiment lane for Qwen3-ASR-1.7B / Qwen3-ASR-0.6B and FireRedASR in:

/home/jnln3799/every_on_git_ubuntu/cib-semantic-risk-asr

Primary objective:
Design, run, validate, and record a complete no-additional-human-review
experiment chain for:
- Qwen3-ASR-0.6B
- Qwen3-ASR-1.7B
- FireRedASR-AED
- FireRedASR-LLM
- FireRedASR2 only as metadata-gated optional extension

The experiment must include:
- baseline raw ASR evaluation
- Simplified Chinese to Traditional Chinese deployment-repair evaluation
- subgroup / Taiwan utility proxy evaluation
- LoRA intervention-rationale decisions
- LoRA smoke and rank/alpha probes where justified
- final scoped survivor or no-human no-winner closeout

Start from these records:
- 70_experiments/runs/v2_0_asr_controls_qwen3_firered_lora_plan_2026_06_01/
- 70_experiments/runs/v2_0_asr_controls_qwen3_firered_lora_plan_2026_06_01/baseline_experiment_matrix.tsv
- 70_experiments/runs/v2_0_asr_controls_qwen3_firered_lora_plan_2026_06_01/lora_grid.tsv
- 70_experiments/runs/v2_0_asr_controls_qwen3_firered_lora_plan_2026_06_01/codex_goal_prompt.md
- docs/v2_0_asr_controls_qwen3_firered_lora_plan.md
- runtime/qwen3_asr_1_7b_runtime_check.md
- 70_experiments/runs/qwen3_asr_0_6b_15_row_candidate/
- docs/model_evaluation_state.md
- docs/privacy_boundary.md
- 70_experiments/registry.tsv

Core privacy and evidence rules:
- Do not implement additional human review.
- Raw audio is never tracked in Git.
- Do not track row IDs, transcripts, references, hypotheses, repaired text,
  model outputs, expert notes, reviewer notes, local paths,
  transcript-bearing logs, adapter weights, model cache paths, or private
  runtime paths.
- Every repo-safe experiment record must be tracked.
- Track aggregate summaries, validators, registry rows, gate decisions, repair
  configs, run README files, controlled artifact manifests, and final closeout
  records.
- Non-audio row-level or transcript-bearing payloads may be used only from
  ignored local or controlled-store locations.
- Git may record only artifact class, count, sensitivity, storage policy,
  hash/manifest status, and gate decision.
- Use accepted ground-truth transcripts only through repo-approved local
  manifests with train/validation/test leakage checks.
- Keep raw ASR capability, Traditional Chinese deployment repair, subgroup
  baseline, semantic-damage proxy, and LoRA intervention evidence separate.
- Simplified Chinese output must be converted to Traditional Chinese only in
  the deployment-repair view.
- Raw capability metrics must remain raw and must not be overwritten by
  repaired metrics.
- LoRA is not an automatic response to imperfect CER/WER.
- LoRA may run only with an explicit intervention rationale:
  - diagnostic-triggered LoRA, or
  - bounded research-probe LoRA.
- No larger CDS-ASR gate opens because a model is famous, new, interesting, or
  benchmark-strong elsewhere.

FIRST PRINCIPLE diagnosis:
The scarce resource is not model count. The scarce resource is claim-evidence
alignment.

The project needs to know:
1. whether Qwen3-ASR and FireRedASR can produce usable Taiwan Traditional
   Chinese ASR evidence;
2. whether Simplified-to-Traditional conversion solves only locale form or also
   preserves meaning;
3. whether LoRA improves Taiwan/domain behavior or creates semantic damage;
4. whether any route can safely support downstream CDS-ASR claims without
   additional human review.

Baseline is therefore not a single CER/WER score. Baseline must be split into:
- raw ASR baseline;
- Traditional Chinese deployment-repair baseline;
- subgroup / Taiwan utility baseline;
- frozen comparison baseline for LoRA.

Required experiment phases:

Phase 0: Freeze prior evidence and boundaries
- Read current repo state.
- Confirm no dirty work is unrelated before editing.
- Preserve previous v2.0 multimodal no-human closeout.
- Preserve Qwen3-ASR-0.6B existing 15-row negative locale evidence.
- Preserve Qwen3-ASR-1.7B runtime timeout evidence.
- Preserve privacy boundary.
- Confirm raw audio, transcript-bearing payloads, adapter weights, and model
  caches remain outside Git.

Phase 1: Refresh model metadata
For each model:
- Qwen3-ASR-0.6B
- Qwen3-ASR-1.7B
- FireRedASR-AED
- FireRedASR-LLM
- FireRedASR2 AED/LLM only if metadata-gated

Record:
- model ID;
- source URL;
- license;
- parameter size;
- weight availability;
- backend;
- required package versions;
- CUDA/GPU requirements;
- duration limits;
- streaming/offline support;
- multilingual / Chinese / dialect / code-switching claims;
- LoRA feasibility;
- known runtime risks;
- promotion boundary.

Use primary sources where possible.

Phase 2: Build local-only manifest preflight
Create repo-safe manifest records for:
- fixed-15 baseline evaluation;
- Qwen3-ASR-0.6B existing fixed-15 output source;
- Qwen3-ASR-1.7B one-row retry;
- FireRedASR one-row / short fixed-15;
- LoRA training payload;
- validation split;
- test split;
- post-LoRA fixed-15 evaluation.

Git may record only:
- artifact class;
- row count;
- split name;
- sensitivity class;
- storage policy;
- hash / manifest status;
- leakage-check status;
- gate decision.

Do not track:
- audio paths;
- row IDs;
- transcript text;
- hypotheses;
- repaired text;
- model output text;
- adapter weights;
- local cache paths.

Phase 3: Build baseline experiment matrix
Use:
- baseline_experiment_matrix.tsv

For every route, define:
- raw capability view;
- Traditional Chinese deployment-repair view;
- subgroup baseline view;
- frozen LoRA comparison view.

Required baseline routes:
- Qwen3-ASR-0.6B raw existing fixed-15 baseline;
- Qwen3-ASR-0.6B Traditional Chinese repaired baseline;
- Qwen3-ASR-0.6B LoRA comparison baseline;
- Qwen3-ASR-1.7B runtime one-row baseline;
- Qwen3-ASR-1.7B repaired baseline if one-row and fixed-15 pass;
- Qwen3-ASR-1.7B LoRA comparison baseline if runtime passes;
- FireRedASR-AED raw short-audio baseline;
- FireRedASR-AED Traditional Chinese repaired baseline;
- FireRedASR-AED LoRA comparison baseline;
- FireRedASR-LLM raw short-audio baseline;
- FireRedASR-LLM Traditional Chinese repaired baseline;
- FireRedASR-LLM LoRA comparison baseline.

Phase 4: Qwen3-ASR-0.6B repaired baseline
Start from existing:
- 70_experiments/runs/qwen3_asr_0_6b_15_row_candidate/

Do not rerun larger inference first.

Create a deployment-repair view:
- OpenCC Simplified-to-Traditional conversion;
- Taiwan-term normalization;
- punctuation normalization;
- safe formatting cleanup.

Record aggregate:
- raw CER/WER;
- repaired CER/WER;
- CER delta;
- WER delta;
- raw simplified character rate;
- repaired simplified character rate;
- raw locale violation rows;
- repaired locale violation rows;
- valid output rate;
- transcript contract status;
- manifest hash/status.

Phase 5: Qwen3-ASR-0.6B semantic-damage proxy
Run deterministic automatic semantic-damage proxy over raw vs repaired
aggregate-safe records.

Blockers must include:
- CER/WER worsening;
- critical-term change;
- proper-noun change;
- English abbreviation damage;
- suspicious length-ratio change;
- empty-output change;
- low-overlap change;
- residual locale violation;
- payload pairing mismatch.

Decision:
- clean deployment-repair survivor;
- repaired-locale-only no semantic survivor;
- stop before larger gates.

Phase 6: Qwen3-ASR-1.7B runtime repair
Start from:
- runtime/qwen3_asr_1_7b_runtime_check.md

Before quality evaluation:
- download/cache model outside Git;
- pin revision;
- record backend;
- record qwen-asr / transformers / torch / CUDA versions;
- record GPU name and memory aggregate only;
- set explicit timeout;
- run exactly one one-row inference;
- run locale scan if inference succeeds.

No first inference row means:
- no fixed-15;
- no repaired baseline;
- no LoRA;
- record runtime-blocked closeout for 1.7B.

Phase 7: FireRedASR metadata and runtime gate
For FireRedASR-AED and FireRedASR-LLM:
- verify license;
- verify weights;
- verify expected model size;
- verify runtime packages;
- verify input duration limits;
- verify batch-size constraints;
- verify GPU/CPU feasibility;
- verify whether LoRA is technically feasible.

Run only after metadata is usable:
- AED one-row short-audio smoke;
- LLM one-row batch_size=1 smoke only if resource/duration boundary is clean.

FireRedASR2:
- metadata-gated only;
- do not bypass FireRedASR AED/LLM baseline route.

Phase 8: Raw fixed-15 baseline gates
Run raw fixed-15 only for models with successful one-row inference.

Compute:
- raw CER;
- raw WER;
- cer_zh_micro;
- wer_zh_jieba_micro;
- simplified character rate;
- locale violation rows;
- valid transcript-like output rate;
- transcript-contract behavior;
- runtime seconds per row;
- duration boundary;
- resource status.

Stop if:
- one-row failed;
- transcript contract failed;
- raw output is unstable;
- runtime is non-reproducible.

Phase 9: Traditional Chinese deployment-repair fixed-15 gates
For every raw fixed-15 route:
- apply deterministic Simplified-to-Traditional conversion;
- apply Taiwan lexical normalization;
- apply punctuation normalization;
- apply safe formatting cleanup.

Record separately:
- repaired CER/WER;
- repaired locale metrics;
- repaired valid output rate;
- raw-to-repaired deltas;
- semantic proxy readiness.

Do not relabel repaired output as raw model capability.

Phase 10: Subgroup baseline proxy
Where approved aggregate manifests support subgroup labels, evaluate:
- Taiwan terms;
- English code-switching;
- identity terms;
- health / insurance terms;
- bank / payment terms;
- reporting / police / scam-process terms;
- duration groups;
- low volume;
- noisy rows.

Track only aggregate subgroup counts and metrics.

Phase 11: LoRA intervention-rationale decisions
Before any LoRA training, write an intervention-rationale record.

Allowed routes:
1. diagnostic-triggered LoRA:
   - baseline shows a fine-tuning-addressable failure;
   - examples: stable Simplified Chinese style, repeated Taiwan-term
     substitution, English abbreviation errors, domain lexical omissions.
2. research-probe LoRA:
   - goal is to test the result and consequence of fine-tuning itself;
   - must predefine target, risk, frozen baseline, and post-LoRA consequence
     checks.

Not allowed:
- "CER/WER is imperfect, therefore fine-tune."

Phase 12: LoRA payload contract
For every allowed LoRA route:
- use accepted ground-truth training rows only;
- freeze validation and test splits;
- check leakage;
- track payload hash/status only;
- keep payload local/ignored;
- keep adapter output local/ignored;
- do not track adapter weights.

Record:
- train row count;
- validation row count;
- test row count;
- sensitivity class;
- hash status;
- split-leakage status;
- target objective;
- expected consequence.

Phase 13: LoRA smoke adapters
Run smallest LoRA smoke first:
- Qwen3-ASR-0.6B rank=4 alpha=8;
- Qwen3-ASR-1.7B rank=4 alpha=8 only after one-row runtime success;
- FireRedASR-AED rank=4 alpha=8 only after AED raw/repaired baseline;
- FireRedASR-LLM rank=4 alpha=8 only after short-audio one-row success.

A smoke succeeds only if:
- training starts;
- training completes;
- adapter saves locally;
- adapter reloads;
- post-training one-row transcript evaluation runs;
- no adapter weights are tracked.

Phase 14: LoRA rank/alpha grid
Expand only for smoke survivors.

Grid:
- rank 4 alpha 8;
- rank 8 alpha 16;
- rank 16 alpha 32;
- optional rank 16 alpha 16 for alpha sensitivity.

Record:
- trainable parameter count;
- training steps;
- first loss;
- last loss;
- runtime;
- memory/resource status;
- adapter hash/status only;
- post-training one-row result;
- fixed-15 result if eligible;
- semantic proxy result.

Stop wider ranks when:
- smaller rank fails reload;
- smaller rank fails one-row;
- smaller rank worsens semantic proxy;
- resource/OOM occurs;
- LoRA creates repetition, empty output, or hallucination.

Phase 15: Post-LoRA fixed-15 and semantic proxy
For LoRA survivors:
- evaluate against frozen raw baseline;
- evaluate against frozen repaired baseline;
- compute fixed-15 deltas;
- compute semantic-damage proxy;
- compute locale deltas;
- compute subgroup deltas if possible.

Promotion requires:
- transcript fidelity preserved;
- zh-TW locale or target failure improved;
- no new semantic blockers;
- no critical-term damage;
- no English abbreviation damage;
- no increased empty-output / low-overlap / repetition proxy.

Phase 16: Limited Taiwan utility proxy
Only for clean survivors:
- run limited automatic Taiwan utility/subgroup proxy;
- label claim as raw ASR, deployment repair, or LoRA intervention evidence;
- do not open 30-row CDS, 258-row, or selected-300 unless claim-evidence
  alignment is proven.

Phase 17: Larger gate decision
Decide whether any route earns:
- 30-row CDS;
- 258-row comparable split;
- selected-300 high-stakes route.

Do not advance unless:
- one-row passed;
- fixed-15 passed;
- Traditional Chinese repair is clean if used;
- semantic proxy is clean;
- subgroup proxy is acceptable;
- LoRA route, if used, has clean post-LoRA evidence;
- claim boundary is explicit.

Phase 18: Final closeout
Write one final outcome:
1. scoped ASR-control survivor;
2. scoped deployment-repair survivor;
3. scoped LoRA intervention survivor;
4. no-human no-winner closeout.

The closeout must explain:
- which models ran;
- which gates passed;
- which gates failed;
- why larger gates opened or stayed closed;
- whether simplified-to-traditional conversion helped;
- whether LoRA helped, harmed, or remained inconclusive;
- what the supported claim boundary is.

Phase 19: Documentation updates
Update:
- docs/model_evaluation_state.md;
- docs/v2_0_asr_controls_qwen3_firered_lora_plan.md;
- 70_experiments/registry.tsv;
- every new run README;
- every new aggregate summary;
- validators;
- planning-everything-track day note;
- planning-everything-track weekly plan;
- planning-everything-track CIB project tracker.

Phase 20: Validation
Run:
- python -m py_compile for all new scripts;
- all new validators;
- TSV width checks;
- git diff --check;
- scripts/check_transcript_bearing_leaks.sh.

The final validator must prove:
- required files exist;
- required phases are recorded;
- baseline matrix row count is correct;
- LoRA grid row count is correct;
- privacy boundary is clean;
- no prohibited transcript-bearing keys are introduced;
- final decision is recorded.

Phase 21: Git
Commit logical slices separately:
- experiment planning / run records;
- scripts / validators;
- docs;
- planning bridge.

Before push:
- git fetch origin main;
- compare HEAD...origin/main;
- preserve both local and remote commits;
- never force-push.

Push non-force only after remote history is checked.

Stop rules:
- No additional human review.
- No raw audio in Git.
- No transcript-bearing payloads in Git.
- No adapter weights in Git.
- No model advances because it is famous or new.
- No fixed-15 before one-row runtime success.
- No repaired claim without raw baseline and semantic-damage proxy.
- No LoRA without intervention rationale.
- No LoRA grid before smoke adapter train/save/reload/post-one-row succeeds.
- No 30-row CDS, 258-row, or selected-300 without clean fixed-15, semantic
  proxy, subgroup evidence, and claim-evidence alignment.
- If all Qwen3 and FireRedASR routes fail runtime, locale, semantic proxy,
  LoRA, or resource gates, write final no-human no-winner closeout instead of
  widening the experiment.
```

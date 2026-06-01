# v2.0 Qwen3-ASR / FireRedASR LoRA Experiment Plan

Date: 2026-06-01

Canonical run design:
`70_experiments/runs/v2_0_asr_controls_qwen3_firered_lora_plan_2026_06_01/`

## Decision

The next ASR-control experiment should focus on Qwen3-ASR and FireRedASR
because they directly target ASR rather than open-ended audio conversation.
The first research question is not whether a larger model can produce fluent
Chinese text. It is whether an ASR system can produce Taiwan Traditional
Chinese transcripts that preserve critical terms, actor/action/amount/time
information, English abbreviations, and downstream CDS-ASR decision stability.

The plan therefore treats Simplified-to-Traditional conversion as a deployment
repair layer, and treats LoRA as a separate fine-tuning evidence layer. Both
must prove they do not create semantic damage before any larger run.

## Diagnostic And LoRA Rationale

The experiment should not move directly from "CER/WER is imperfect" to LoRA.
For model promotion, the first goal is to classify the defect. A model should
first produce raw and deployment-repaired fixed-15 evidence with CER/WER,
locale rate, transcript contract behavior, automatic semantic-damage proxy,
subgroup tags, and runtime status. LoRA opens from this route when the defect
is plausibly learnable: stable locale style, repeated Taiwan-term
substitutions, English abbreviation errors, or domain lexical omissions.

If the defect is runtime timeout, duration limit, unstable output, hallucination,
severe low-overlap transcript, or an issue solved cleanly by deterministic
conversion, LoRA is not the next promotion experiment.

LoRA is included in this plan as a bounded research-probe experiment when the
goal is to test the result and consequence of fine-tuning itself. That route
must state the expected target, risk, frozen comparison baseline, and post-LoRA
consequence checks before training starts. It remains intervention evidence
until it passes the same post-training gates as any other route.

## Model Positioning

| Model | Position | First action |
| --- | --- | --- |
| Qwen3-ASR-0.6B | existing negative ASR-control candidate | repaired fixed-15 view plus semantic proxy |
| Qwen3-ASR-1.7B | stronger ASR-control candidate with runtime blocker | isolated one-row runtime retry |
| FireRedASR-AED | efficient Chinese ASR candidate | metadata/license/runtime then short-audio one-row |
| FireRedASR-LLM | LLM-integrated Chinese ASR candidate | short-audio batch_size=1 one-row after metadata gate |
| FireRedASR2 | optional newer branch | metadata gate after FireRedASR baseline |

## Baseline Design

The requested baseline experiment has three layers:

| Layer | Purpose | Output |
| --- | --- | --- |
| Raw baseline | Measure original ASR behavior without conversion | raw CER/WER, simplified-character rate, locale violation rows, transcript-contract behavior, runtime |
| Traditional Chinese repair baseline | Measure deterministic deployment repair separately | OpenCC / Taiwan-term deltas, repaired CER/WER, semantic-damage proxy |
| Subgroup baseline | Identify whether errors concentrate in Taiwan terms, code-switching, identity/health/bank/reporting terms, duration, or noise | aggregate subgroup proxy and stop/promote decision |

The detailed baseline matrix is
`70_experiments/runs/v2_0_asr_controls_qwen3_firered_lora_plan_2026_06_01/baseline_experiment_matrix.tsv`.

## LoRA Design

LoRA is tested only after an intervention rationale exists: either
diagnostic-triggered evidence of a fine-tuning-addressable failure, or a bounded
research-probe rationale. The ordered grid is:

| Stage | Rank | Alpha | Reason |
| --- | ---: | ---: | --- |
| smoke | 4 | 8 | proves train/save/reload/post-one-row viability |
| default | 8 | 16 | tests useful adaptation with modest capacity |
| upper | 16 | 32 | tests higher capacity after smaller rank is clean |
| sensitivity | 16 | 16 | isolates alpha effect when rank 16 is promising but unstable |

The supported claim is narrow: LoRA may improve zh-TW locale behavior and
critical-term preservation only if it does not worsen transcript fidelity,
semantic-damage proxies, or subgroup utility.

## Baseline Gate Execution: 2026-06-01

The first executable ASR-control gates are now recorded as repo-safe,
aggregate-only experiment records:

| Run | Status | Decision |
| --- | --- | --- |
| `v2_0_asr_controls_metadata_refresh_2026_06_01` | metadata refresh complete | Qwen3-ASR, FireRedASR, and FireRedASR2 source metadata recorded with primary-source verification status |
| `v2_0_asr_controls_manifest_preflight_2026_06_01` | manifest preflight complete | transcript-bearing prediction, runtime, training, and adapter payloads remain ignored/local-only |
| `v2_0_asr_controls_baseline_matrix_record_2026_06_01` | baseline matrix decisions recorded | only Qwen3-ASR-0.6B existing routes are ready from current evidence |
| `v2_0_asr_controls_qwen3_0_6b_trad_repair_baseline_2026_06_01` | Qwen3-ASR-0.6B repair baseline complete | do not promote repaired pipeline |

Qwen3-ASR-0.6B now has a separated raw-vs-repaired deployment record over the
existing fixed-15 candidate. The deterministic Traditional Chinese repair
reduced raw aggregate CER from `64.1614` to `39.8051`, WER from `67.2811` to
`40.3994`, simplified-character rate from `22.6253` to `0.6579`, and locale
violation rows from `15` to `8`.

The result is useful deployment-repair evidence, but it is not a raw model
capability improvement and it is not a promotion result. The automatic
semantic-damage proxy still records `semantic_damage_blocker_rows=8`, so
Taiwan utility/subgroup expansion, 30-row CDS, 258-row, selected-300, and LoRA
promotion gates remain closed for this repaired route until a separate
intervention rationale and clean post-training consequence check exist.

## Qwen3-ASR-1.7B Runtime And Fixed-15 Gate: 2026-06-01

The isolated-cache Qwen3-ASR-1.7B retry repaired the prior fetch/load blocker.
The one-row runtime gate is recorded in
`70_experiments/runs/v2_0_asr_controls_qwen3_1_7b_runtime_retry_2026_06_01/`
with `first_successful_inference_rows=1`, `exit_status=0`, and
`promotion_decision=promote_to_fixed_15_raw_gate`.

The fixed-15 raw gate is recorded in
`70_experiments/runs/v2_0_asr_controls_qwen3_1_7b_fixed_15_raw_2026_06_01/`.
It produced 15/15 valid outputs, but raw locale evidence remains unsuitable for
promotion: `cer_mean=63.7`, `wer_mean=80.43`,
`simplified_char_rate=0.1499`, and `locale_violation_rows=15`.

The deterministic Traditional Chinese repair view is recorded in
`70_experiments/runs/v2_0_asr_controls_qwen3_1_7b_trad_repair_baseline_2026_06_01/`.
Repair lowered aggregate CER from `62.8392` to `37.7871`, WER from `66.129` to
`38.4025`, simplified-character rate from `22.4463` to `0.3245`, and locale
violation rows from `15` to `5`. This is a meaningful deployment-repair result,
but it still records `semantic_damage_blocker_rows=5`, so Qwen3-ASR-1.7B does
not enter Taiwan utility, 30-row CDS, 258-row, selected-300, or LoRA expansion
from this gate.

## FireRedASR Gates And Final Closeout: 2026-06-01

FireRedASR-AED-L is now tested through the same ordered no-human gate sequence.
The runtime gate is recorded in
`70_experiments/runs/v2_0_asr_controls_firered_aed_runtime_gate_2026_06_01/`.
It required bounded local runtime repairs: install `cn2an` and
`kaldi_native_fbank`, set `torch.load(weights_only=False)` for the trusted
official checkpoint, and disable cuDNN for this CUDA runtime. With those
repairs, the AED route produced an official example output and one JANUS row,
so it promoted only to short fixed-15 raw scoring.

The FireRedASR-AED-L fixed-15 raw gate is recorded in
`70_experiments/runs/v2_0_asr_controls_firered_aed_fixed_15_raw_2026_06_01/`.
It produced 15/15 outputs, but raw locale evidence remained unsuitable:
`CER=70.2853`, `WER=73.6559`, `simplified_char_rate=22.7884`, and
`locale_violation_rows=15`.

The FireRedASR-AED-L repair view is recorded in
`70_experiments/runs/v2_0_asr_controls_firered_aed_trad_repair_baseline_2026_06_01/`.
Repair lowered aggregate CER from `70.2853` to `50.3132`, WER from `73.6559`
to `51.8433`, simplified-character rate from `22.7884` to `0.4944`, and
locale violation rows from `15` to `6`, but
`semantic_damage_blocker_rows=6`, so the AED route does not promote.

FireRedASR-LLM-L is recorded in
`70_experiments/runs/v2_0_asr_controls_firered_llm_resource_gate_2026_06_01/`
as resource-gated before inference. The source route is 8.3B and requires both
FireRedASR-LLM-L weights and `Qwen/Qwen2-7B-Instruct`; the local single 16GB
GPU boundary is not clean enough to justify a one-row LLM run.

LoRA intervention decisions are recorded in
`70_experiments/runs/v2_0_asr_controls_lora_intervention_decisions_2026_06_01/`.
No route opens LoRA training or rank/alpha grid expansion because current
evidence either has nonzero automatic semantic/locale blockers or remains
resource-blocked before one-row inference.

## Qwen3-ASR-1.7B Bounded LoRA Payload Contract: 2026-06-01

The first ASR-control LoRA payload contract is now recorded in
`70_experiments/runs/v2_0_asr_controls_lora_payload_contract_2026_06_01/`.
This updates the previous "no LoRA promotion" decision without changing its
claim boundary: Qwen3-ASR-1.7B still has
`semantic_damage_blocker_rows=5`, so it is not a diagnostic-proven LoRA
promotion route. The new contract opens only a bounded research-probe route to
measure the consequence of LoRA on Taiwan Traditional Chinese ASR.

The transcript-bearing training payload is generated from already reviewed
ground truth and remains local-only under the ignored runtime lane. Git tracks
only aggregate counts, hashes, leakage decisions, normalization policy, and the
first route contract. The split is `train=9`, `validation=3`, and `test=3`.
The leakage report records `fixed15_baseline_overlap=15`, which means post-LoRA
fixed-15 behavior can be used as a memorization/consequence probe but cannot
serve as clean promotion evidence.

The first route is:

| Route | Model | Rank | Alpha | Status | Claim boundary |
| --- | --- | ---: | ---: | --- | --- |
| `qwen3_asr_1_7b_r16_a32_research_probe` | `Qwen/Qwen3-ASR-1.7B` | 16 | 32 | payload ready, training not started | bounded research-probe LoRA, not diagnostic-proven promotion LoRA |

The first post-training gate is train/save/reload plus one-row transcript and
locale checking. It may advance only to the validation split consequence check
if the adapter loads cleanly and does not worsen the one-row semantic/locale
proxy. This contract does not open 30-row CDS, 258-row, or selected-300.

## Qwen3-ASR-1.7B LoRA r16/a32 Smoke Result: 2026-06-01

The bounded smoke run is recorded in
`70_experiments/runs/v2_0_asr_controls_qwen3_1_7b_lora_r16_a32_smoke_train_2026_06_01/`.
It used the contract-defined local-only training manifest and did not modify
the repo-wide environment. The first naive attempt showed that the outer
Qwen3-ASR generation wrapper is not the trainable forward surface; the minimal
repair was to attach LoRA to the inner `thinker` module, which exposes the
standard audio/text forward interface.

The repaired smoke completed the minimum operational proof:

| Gate | Result |
| --- | --- |
| model load | passed |
| LoRA attach | passed; trainable parameters `4784128` |
| minimal train step | passed; `train_steps=1`, loss `2.240593` |
| adapter save | passed; adapter hash recorded |
| adapter reload | passed |
| post-training one-row consequence | failed |

The post-training one-row consequence gate records `CER=69.33`, `WER=73.47`,
and `simplified_char_count=23`, so the decision is
`lora_research_probe_stop`. This proves LoRA is operational on the local
Qwen3-ASR-1.7B runtime, but it does not prove useful zh-TW improvement. The
validation split, 30-row CDS, 258-row, selected-300, promotion claims, and
broad rank/alpha sweeps remain closed.

The final no-human closeout is recorded in
`70_experiments/runs/v2_0_asr_controls_final_no_human_closeout_2026_06_01/`.
The outcome is `no_human_no_winner_closeout`: deterministic conversion helped
form and aggregate error metrics, but no route has clean enough evidence to
open Taiwan utility, 30-row CDS, 258-row, selected-300, or LoRA.

## Required Evaluation Metrics

- raw CER and WER;
- deployment-repaired CER and WER;
- simplified character rate;
- locale violation rows;
- valid transcript-like output rate;
- critical-term / proper-noun proxy blockers;
- English abbreviation proxy blockers;
- length-ratio / empty-output / low-overlap blockers;
- Taiwan-term subgroup result;
- code-switch subgroup result;
- health / identity / bank / reporting term subgroup result;
- adapter train/save/reload status;
- post-LoRA one-row and fixed-15 deltas against frozen baseline.

## Sources

- Qwen3-ASR model card: https://huggingface.co/Qwen/Qwen3-ASR-0.6B
- Qwen3-ASR technical report: https://arxiv.org/abs/2601.21337
- FireRedASR repo: https://github.com/FireRedTeam/FireRedASR
- FireRedASR paper: https://arxiv.org/abs/2501.14350
- FireRedASR2S repo: https://github.com/FireRedTeam/FireRedASR2S

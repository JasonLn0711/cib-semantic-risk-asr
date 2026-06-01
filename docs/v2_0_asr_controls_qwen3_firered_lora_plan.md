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

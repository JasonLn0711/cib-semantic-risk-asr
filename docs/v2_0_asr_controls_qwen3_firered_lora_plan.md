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

## Model Positioning

| Model | Position | First action |
| --- | --- | --- |
| Qwen3-ASR-0.6B | existing negative ASR-control candidate | repaired fixed-15 view plus semantic proxy |
| Qwen3-ASR-1.7B | stronger ASR-control candidate with runtime blocker | isolated one-row runtime retry |
| FireRedASR-AED | efficient Chinese ASR candidate | metadata/license/runtime then short-audio one-row |
| FireRedASR-LLM | LLM-integrated Chinese ASR candidate | short-audio batch_size=1 one-row after metadata gate |
| FireRedASR2 | optional newer branch | metadata gate after FireRedASR baseline |

## LoRA Design

LoRA is tested only after baseline evidence exists. The ordered grid is:

| Stage | Rank | Alpha | Reason |
| --- | ---: | ---: | --- |
| smoke | 4 | 8 | proves train/save/reload/post-one-row viability |
| default | 8 | 16 | tests useful adaptation with modest capacity |
| upper | 16 | 32 | tests higher capacity after smaller rank is clean |
| sensitivity | 16 | 16 | isolates alpha effect when rank 16 is promising but unstable |

The supported claim is narrow: LoRA may improve zh-TW locale behavior and
critical-term preservation only if it does not worsen transcript fidelity,
semantic-damage proxies, or subgroup utility.

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

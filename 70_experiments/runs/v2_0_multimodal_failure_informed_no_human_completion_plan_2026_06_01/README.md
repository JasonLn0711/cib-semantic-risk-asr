# v2.0 Failure-Informed No-Human Completion Plan

Date: 2026-06-01

Status: `plan_recorded_no_human_review`

This plan starts from the completed Batch 1 multimodal evidence, the Qwen
expert-review completion, and Step-Audio LoRA iteration 1. It records the
remaining route to finish all new experiments without implementing further
human review.

## Current Evidence

The evidence says the next bottleneck is not a longer model list. The remaining
problem is claim-evidence alignment after repeated gate failures:

- Qwen repaired-pipeline output improves CER/WER but expert review rejects
  promotion: only `1/7` residual rows are directly semantically acceptable,
  `5/7` have major critical-term damage, and `5/7` have hallucination /
  omission.
- Step-Audio LoRA iteration 1 proves local adapter training and adapter loading,
  but post-training sentinel controls still fail with `sentinel_pass_rows=3/6`
  and `hallucination_on_no_speech_rows=3`.
- MOSS 4B and MiniCPM-o 4.5 failures concentrate on no-speech / non-speech
  hallucination and instruction/summary behavior.
- Kimi-Audio is blocked by the isolated `flash_attn` / CUDA-toolchain boundary.
- MOSS 8B is blocked by the local 16GB GPU resource boundary.

## FIRST PRINCIPLE Decision

The next best solution is not immediate larger-scale inference. The next best
solution is a non-human, deterministic repair layer that directly targets the
observed failure modes before any model is allowed to re-enter fixed-15 or
larger gates.

The repair layer must stay separate from raw model capability:

```text
raw model capability
deployment repair capability
automatic proxy capability
fine-tuning capability
```

The first proposed solution is a deterministic acoustic no-speech / non-speech
guard before the audio LLM. If audio energy, voiced-speech evidence, or speech
segment structure indicates silence, tone, or noise, the pipeline returns the
fixed string `無法辨識` before prompting the model. This directly addresses the
most repeated sentinel failure without requiring human review.

The second proposed solution is a Step-Audio LoRA iteration 2 only after the
deterministic guard is specified. LoRA iteration 2 should change the
intervention, not simply repeat iteration 1: use stronger negative-row
weighting / oversampling, include no-speech and non-speech controls as the main
training target, and evaluate with the same post-training one-row and sentinel
gates.

## Completion Definition

All new experiments are complete when one of these is true:

1. A non-human repaired or fine-tuned pipeline passes one-row, sentinel, fixed
   15-row zh-TW locale, automatic semantic-damage proxy, and limited Taiwan
   utility/subgroup proxy with claim boundaries recorded.
2. Every feasible no-human repair and fine-tuning route is exhausted with
   repo-safe evidence, and a final no-human no-winner closeout is recorded.

No path may advance to human-reviewed 30-row CDS, 258-row, or selected-300
without a new non-human claim-evidence design that first proves why the larger
gate can answer the CDS-ASR research question.

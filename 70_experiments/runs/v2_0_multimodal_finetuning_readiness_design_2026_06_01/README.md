# v2.0 Multimodal Fine-Tuning Readiness Design

Date: 2026-06-01

Status: readiness_design_recorded_do_not_train_yet

This record answers whether the v2.0 multimodal audio LLM lane should move to
fine-tuning after the automatic repair chain closed with no behavior-clean
sentinel survivor.

## FIRST PRINCIPLE

Fine-tuning is justified only when it targets a proven, narrow failure mode and
the evaluation gates can measure whether training fixed that failure without
moving the claim boundary. The current evidence does not justify immediate
fine-tuning of the primary multimodal models.

The next training-related object is therefore a readiness gate, not training.

## Decision

```text
fine_tuning_now=false
next_training_gate=fine_tuning_readiness_and_lora_feasibility_design
primary_reason=current_blockers_are_review_sentinel_runtime_or_resource_gates
first_allowed_training_scope=small_lora_feasibility_after_review_or_new_bounded_design
```

## Candidate Ordering For Future LoRA Feasibility

1. Step-Audio-2-mini: one-row transcript-contract repair succeeded, but
   repaired sentinel controls failed no-speech / non-speech hallucination.
2. MiniCPM-o 4.5: sentinel repair improved from `3/6` to `5/6`, but one
   no-speech / non-speech hallucination remains under the 4-bit local boundary.
3. MOSS-Audio-4B: transcript-like one-row succeeded, but sentinel repair still
   fails `3/6`.
4. Qwen2.5-Omni: prioritize repaired-pipeline human semantic-damage review
   before any fine-tuning; current issue is locale / deployment repair, not a
   proven training target.
5. Kimi-Audio and MOSS-Audio-8B: blocked by dependency/resource gates; no
   fine-tuning readiness until runtime is repaired.

## Training Stop Rule

No model enters LoRA or other fine-tuning until all of these are true:

```text
bounded_training_question=true
local_private_training_payload_ready=true
manifest_hash_status_tracked=true
raw_audio_not_tracked=true
one_row_and_sentinel_baselines_exist=true
post_training_one_row_and_sentinel_eval_defined=true
promotion_requires_sentinel_pass_rows_6_of_6=true
```

If a proposed fine-tune cannot improve sentinel behavior without leaking raw
audio or mixing raw model capability with deployment repair capability, do not
train.

# v2.0 Multimodal Bounded LoRA Feasibility Start

This record starts the post-auto-only-stop fine-tuning lane without mixing training evidence into the no-winner closeout.

## Decision

- Primary candidate: `Step-Audio-2-mini`
- Training target: `sentinel_no_speech_non_speech_hallucination_reduction`
- Status: `bounded_lora_feasibility_start_recorded_training_not_started`
- Training execution is not launched because the local private training payload manifest and LoRA adapter-loading evaluator contract are not ready.

## FIRST PRINCIPLE

Fine-tuning starts from a narrow failure mode and a measurable post-training gate. The current target is Step-Audio no-speech / non-speech sentinel hallucination, because Step passed the repaired one-row transcript contract but failed sentinel controls.

## Required Next Action

Prepare the local-only training payload manifest and adapter-loading evaluator contract, then run a tiny LoRA smoke only after those pretraining gates pass.

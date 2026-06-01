# Step-Audio LoRA Smoke Train

Status: `step_audio_lora_smoke_train_failed`

Route: `4-bit NF4 quantized smoke`

Failure mode: `RuntimeError:a view of a leaf Variable that requires grad is being used in an in-place operation.`

This run uses the same local-only 4-row payload as the Step LoRA pretraining
gate. It records backend/resource feasibility only. No adapter was saved, no
adapter hash exists, and no model-improvement or post-training evaluation claim
is supported.

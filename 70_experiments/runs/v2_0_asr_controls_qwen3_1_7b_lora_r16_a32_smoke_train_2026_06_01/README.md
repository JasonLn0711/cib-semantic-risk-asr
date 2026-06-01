# Qwen3-ASR-1.7B LoRA r16/a32 Smoke Train

Date: 2026-06-01

Status: `lora_smoke_train_adapter_saved_reloaded`
Decision: `lora_research_probe_stop`

This is a bounded research-probe LoRA run. It attempts only the minimum train/save/reload sequence needed to test whether LoRA is operational for Qwen3-ASR-1.7B on the local runtime.

## Boundary

- No raw audio is tracked.
- Transcript-bearing train/validation/test manifests remain local-only.
- Adapter weights remain in the ignored runtime lane.
- Fixed-15 overlap is known and blocks clean promotion evidence.
- 30-row CDS, 258-row, selected-300, and broad rank/alpha sweeps remain closed.

## Current Result

- Train steps: `1`
- Adapter saved: `true`
- Adapter reloaded: `true`
- Blocker class: ``

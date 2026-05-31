# v2.0 Batch 1 Adapter Preflight

Date: 2026-05-31

Status: adapter preflight complete; no model inference was run

本紀錄只保存 adapter readiness，不保存任何逐字稿或私有音訊內容。

## Purpose

This Gate B record checks whether the local runtime can start real one-row
transcript-only smoke for the v2.0 Batch 1 multimodal models. It does not
download model weights and does not run model inference.

## Result

```text
models_checked=6
models_ready_for_smoke=6
models_blocked_by_missing_runtime_modules=0
models_blocked_by_missing_cache=0
models_deferred_by_gate_order=0
manifest_exists=True
gpu_present=True
```

## Next Step

All six Batch 1 adapter/cache lanes have now reached the pre-inference readiness contract. Interpret readiness with the one-row smoke records: Qwen2.5-Omni, MOSS-Audio-4B, and MiniCPM-o 4.5 are sentinel candidates; Step-Audio-2-mini is in a prompt/runtime repair lane; Kimi-Audio is blocked by the official flash_attn dependency boundary; and MOSS-Audio-8B is blocked by the local 16GB single-GPU memory boundary. Continue with sentinel controls for MOSS-Audio-4B and MiniCPM-o 4.5 before any fixed 15-row gate.

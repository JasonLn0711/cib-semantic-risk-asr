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
models_ready_for_smoke=5
models_blocked_by_missing_runtime_modules=0
models_blocked_by_missing_cache=0
models_deferred_by_gate_order=1
manifest_exists=True
gpu_present=True
```

## Next Step

Qwen2.5-Omni, MOSS-Audio-4B, MiniCPM-o 4.5, and Kimi-Audio have ignored model-cache/runtime lanes, while Step-Audio-2-mini has separate one-row evidence and remains in a prompt/runtime repair lane. Interpret Kimi's adapter readiness together with its one-row smoke record because the official main-model remote code requires flash_attn on this local machine. Continue with MOSS-Audio-8B setup only after this dependency boundary is recorded, then run sentinel controls for transcript-like candidates. Keep local manifest values, hypotheses, logs, and model caches outside git.

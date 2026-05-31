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
models_ready_for_smoke=4
models_blocked_by_missing_runtime_modules=0
models_blocked_by_missing_cache=1
models_deferred_by_gate_order=1
manifest_exists=True
gpu_present=True
```

## Next Step

Qwen2.5-Omni, MOSS-Audio-4B, and MiniCPM-o 4.5 have one-row smoke evidence, while Step-Audio-2-mini is in a prompt/runtime repair lane. Continue with Kimi-Audio isolated model-cache/runtime setup, then decide whether MOSS-Audio-8B should run before or after sentinel controls for the current transcript-like candidates. Keep local manifest values, hypotheses, logs, and model caches outside git.

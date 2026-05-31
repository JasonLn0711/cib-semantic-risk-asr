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
models_ready_for_smoke=2
models_blocked_by_missing_runtime_modules=0
models_blocked_by_missing_cache=3
models_deferred_by_gate_order=1
manifest_exists=True
gpu_present=True
```

## Next Step

Qwen2.5-Omni has already passed one-row smoke and sentinel controls.
Step-Audio-2-mini has a ready isolated runtime/cache lane but its one-row smoke
did not satisfy the raw transcript-like contract, so it moves to a bounded
prompt/runtime repair lane. The next setup gate is MOSS-Audio-4B-Instruct
isolated runtime/cache preparation. Keep local manifest values, hypotheses,
logs, and model caches outside git.

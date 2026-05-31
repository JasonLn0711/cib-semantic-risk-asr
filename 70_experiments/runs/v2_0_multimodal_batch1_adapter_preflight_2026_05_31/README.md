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
models_ready_for_smoke=0
models_blocked_by_missing_runtime_modules=1
models_blocked_by_missing_cache=4
models_deferred_by_gate_order=1
manifest_exists=True
gpu_present=True
```

## Next Step

Prepare isolated model-cache/download lanes for the planned model order, then
run one-row transcript-only smoke starting with Qwen2.5-Omni-7B. Keep local
manifest values, hypotheses, logs, and model caches outside git.

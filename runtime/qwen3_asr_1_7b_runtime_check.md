# Qwen3-ASR-1.7B Runtime Check

Date: 2026-05-26

## Scope

This file isolates the Qwen3-ASR-1.7B issue from the general candidate model
matrix. The current problem is runtime readiness, not benchmark scoring.

## Current Local State

Tracked evidence:

- `70_experiments/runs/qwen3_asr_1_7b_smoke_1_row/README.md`
- `70_experiments/runs/asr_candidate_current_recheck_2026_05_26/summary.json`

Observed state:

| Field | Value |
| --- | --- |
| Model | `Qwen/Qwen3-ASR-1.7B` |
| Toolkit | `qwen-asr` local runner |
| Local retry policy | bounded 60-second load gate |
| Current result | timeout before inference |
| Rows emitted | `0` |
| Metrics emitted | none |
| Promotion decision | do not enter 15-row, 258-row, selected-300, or high-stakes 300 until first inference row exists |

The official Qwen3-ASR model card documents both manual model download and the
`qwen-asr` package with transformers and vLLM backends. For this repo, the next
attempt should follow that path in an isolated/cache-controlled runtime rather
than re-running the same fetch/load timeout.

## Required Retry Plan

Before retrying 1.7B inference:

1. Download the model to a local cache or local model directory outside git.
2. Pin the model revision or commit hash.
3. Record the `qwen-asr`, `transformers`, `torch`, CUDA, and driver versions.
4. Record GPU name, total memory, and available memory before load.
5. Set explicit download/load timeout values.
6. Run exactly one 1-row smoke with cuDNN disabled if the local Qwen lane still
   requires it.
7. Run `scripts/check_locale_zh_tw.py` over the raw output if inference
   succeeds.

## Required Record Fields

The first successful runtime record must include:

```text
package_version
transformers_version
torch_version
cuda_version
gpu_name
gpu_memory_total
model_id
model_revision
model_cache_path
backend
timeout_seconds
first_successful_inference_rows
row_wall_time_seconds
locale_gate_status
promotion_decision
```

No first successful inference row means no 15-row promotion.

## Decision

Do not spend full-split runtime on Qwen3-ASR-1.7B until this runtime check
records at least one successful raw inference row and a raw Taiwan Traditional
Chinese locale-gate result.

# Qwen3-ASR-1.7B Runtime Retry

Date: 2026-06-01

Status: `qwen3_1_7b_one_row_runtime_success`

The isolated-cache retry produced one raw inference row. Tracked records contain only aggregate runtime/locale metrics, artifact hashes, and gate decisions; transcript-bearing predictions and logs remain ignored under `70_experiments/runtime_lanes/`.

Decision: promote to fixed-15 raw gate, but not to LoRA or larger CDS-ASR gates.

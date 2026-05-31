# v2.0 Batch 1 Runtime Smoke Preflight

Date: 2026-05-31

Status: runtime smoke scaffolding ready; no model inference was run

本紀錄只保存 aggregate runtime-smoke scaffolding，不保存任何逐字稿或私有音訊內容。

## Purpose

This run prepares the isolated one-row transcript-only runtime-smoke gate for
the v2.0 Batch 1 multimodal audio LLM experiment. It records the planned model
order, runtime-lane separation, prompt-output policy, and aggregate output
schemas before any model weights, local audio, or transcript-bearing outputs are
used.

## Files

```text
runtime_environment_summary.tsv
behavior_summary.tsv
gate_summary.json
README.md
```

## Execution Order

1. Qwen2.5-Omni-7B
2. Step-Audio-2-mini
3. MOSS-Audio-4B-Instruct
4. MiniCPM-o 4.5
5. Kimi-Audio-7B-Instruct after size-boundary decision
6. MOSS-Audio-8B-Instruct after MOSS 4B

## Manifest State

```text
manifest_provided=False
manifest_rows=0
manifest_status=local_only_manifest_required_before_inference
```

The actual one-row audio manifest must remain local-only. Tracked summaries may
record counts and gate decisions, but not audio IDs, row IDs, transcript text,
model hypotheses, reviewer notes, or local file paths.

## Next Gate

Attach a local-only one-row manifest and model-family runtime adapters, then run
the first transcript-only smoke for metadata-clean Batch 1 models. Only models
with raw transcript-like text output can proceed to sentinel negative controls.

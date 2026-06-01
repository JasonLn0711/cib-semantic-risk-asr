# v2.0 Batch 1 repair-first experiment design record

Date: 2026-06-01

This is a new aggregate-only experiment-design record created after the first
raw v2.0 Batch 1 multimodal gate chain completed with no scientific winner.
It records the next repair-first experimental plan for all primary Batch 1
multimodal audio models.

## FIRST PRINCIPLE

The scarce resource is clean gate evidence. After zero raw scientific winners,
the next valid experiment is not larger inference. It is a repair-first
experiment that separates raw model capability from deployment-pipeline repair
capability.

## Scope

Primary models covered:

```text
Kimi-Audio-7B-Instruct
Qwen2.5-Omni-7B
Step-Audio-2-mini
MOSS-Audio-4B-Instruct
MOSS-Audio-8B-Instruct
MiniCPM-o 4.5
```

## Tracking And Privacy

The tracking policy for the next experiment phase is:

```text
raw audio: never tracked
repo-safe experiment records: tracked
aggregate summaries and validators: tracked
non-audio row-level or transcript-bearing payloads: tracked only after redaction/approval
non-audio local payload existence: tracked through manifest/hash/status records
```

This design record itself contains no raw audio, row identifiers, transcripts,
references, hypotheses, reviewer notes, local paths, model outputs,
transcript-bearing logs, model cache paths, or local manifest values. Future
repair runs should still track every repo-safe experiment record and at least a
manifest/hash/status record for controlled non-audio artifacts.

## Files

```text
repair_first_design_summary.json
model_repair_plan.tsv
gate_sequence.tsv
```

The detailed execution guide is:

```text
docs/v2_0_multimodal_batch1_repair_first_experiment_guide.md
```

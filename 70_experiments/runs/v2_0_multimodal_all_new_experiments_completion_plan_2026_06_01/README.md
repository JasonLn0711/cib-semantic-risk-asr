# v2.0 multimodal all-new-experiments completion plan

Date: 2026-06-01

This tracked planning record defines the complete remaining path from the raw
Batch 1 completion audit to the end of all v2.0 multimodal new experiments.

## FIRST PRINCIPLE

The scarce resource is claim-evidence alignment. A model advances only when the
previous gate proves the next experiment can answer the CDS-ASR research
question without leaking protected content or mixing raw model capability with
deployment repair capability.

## Current Start Point

```text
70_experiments/runs/v2_0_multimodal_batch1_completion_audit_2026_06_01/
70_experiments/runs/v2_0_multimodal_batch1_repair_first_design_2026_06_01/
docs/v2_0_multimodal_batch1_repair_first_experiment_guide.md
```

Current raw status:

```text
batch1_gate_chain_complete_no_scientific_winner
```

## Phase Progress Update

The tracked progress file
`phase_progress_2026_06_01.tsv` records Phases 1-5 as complete. Qwen
OpenCC/Taiwan-term repair is a deployment-pipeline review candidate and still
needs human semantic-damage review before larger repaired-pipeline gates.
MOSS-Audio-4B sentinel repair remains `do_not_promote` with `3/6` sentinel
passes and `3` no-speech hallucination rows. MiniCPM-o 4.5 sentinel repair
improves to `5/6` and removes summary / translation behavior, but one
no-speech / non-speech hallucination remains, so it is also `do_not_promote`.

The next executable phase is Phase 6 Step-Audio-2-mini transcript-contract
repair. Phases 11-15 remain blocked until prior gates produce survivor evidence
that can answer the CDS-ASR research question with claim-evidence alignment.

## Completion Definition

All new experiments are complete only when the repo has either:

1. a promoted multimodal model with interpretable 30-row, 258-row, and
   selected-300 evidence; or
2. an evidence-backed stop record proving that no repaired or secondary lane
   produced a scientific winner under the declared gates.

In both cases, the repo must contain tracked aggregate records, validators,
registry rows, model-state updates, planning bridges, and a final synthesis
that separates raw capability, deployment repair, voice interaction, and
long-audio reasoning evidence.

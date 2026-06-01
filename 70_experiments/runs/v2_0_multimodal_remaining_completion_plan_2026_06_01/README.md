# v2.0 Multimodal Remaining Completion Plan

Date: 2026-06-01

Status: remaining_completion_plan_recorded_after_repair_chain_closeout

This record defines what still needs to happen to finish all v2.0 multimodal
new experiments after the automatic repair-first chain closed with no
behavior-clean sentinel survivor.

## FIRST PRINCIPLE

The remaining bottleneck is claim-evidence alignment, not compute. Larger
CDS-ASR gates may open only if one of two things happens:

1. Qwen2.5-Omni repaired-pipeline output passes human semantic-damage review;
2. a new bounded repair design produces a behavior-clean sentinel survivor.

If neither condition is met, the correct completion state is a final no-winner
stop record, not a 30-row, 258-row, or selected-300 run.

## Current Evidence

```text
automatic_repair_chain_status=complete_through_phase_9
behavior_clean_repaired_sentinel_survivors=0
qwen_repaired_pipeline_human_review_pending=true
fixed_15_repaired_rerun_open=false
taiwan_utility_open=false
human_reviewed_30_row_cds_open=false
promoted_258_row_open=false
selected_300_open=false
```

## Completion Definition

All new experiments are complete when the repo records one of these final
states:

```text
promoted_multimodal_winner_with_claim_aligned_large_gate_evidence
final_no_winner_stop_after_qwen_review_and_repair_options_are_closed
```

Both states require tracked aggregate records, validators, registry rows,
planning bridge updates, and a final synthesis that keeps raw model capability
separate from deployment repair capability.

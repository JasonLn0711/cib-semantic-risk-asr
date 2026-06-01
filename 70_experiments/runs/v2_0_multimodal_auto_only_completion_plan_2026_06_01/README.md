# v2.0 Multimodal Auto-Only Completion Plan

Date: 2026-06-01

Status: auto_only_completion_plan_recorded

This record updates the remaining v2.0 multimodal completion route under the
new constraint: **do not implement human semantic-damage review**.

## FIRST PRINCIPLE

If human review is excluded, the remaining scientific question changes. The
repo may still finish the new experiments, but larger CDS-ASR claims must be
limited to what automatic evidence can support.

The useful path is therefore:

```text
deterministic semantic-damage proxy
-> automatic repaired-pipeline safety gate
-> Taiwan utility proxy only if automatic safety is clean
-> no 30-row CDS / 258-row / selected-300 unless automatic evidence is strong
   enough for the declared claim
-> otherwise final auto-only no-winner stop
```

## Current Gate

```text
automatic_repair_chain_complete=true
behavior_clean_repaired_sentinel_survivors=0
qwen_repaired_pipeline_candidate=true
human_review_allowed=false
larger_human_reviewed_cds_allowed=false
```

Qwen remains the only repaired-pipeline candidate. Its OpenCC/Taiwan-term
repair reduced locale violations and simplified-character rate, but human
semantic-damage review is not allowed under this plan. Therefore Qwen can move
only through automatic proxy gates with a narrow deployment-pipeline claim.

## Completion Definition

All new experiments finish when the repo records one of these states:

```text
auto_only_repaired_pipeline_proxy_success_with_limited_claim
auto_only_no_winner_stop
```

The default expected state is `auto_only_no_winner_stop` unless the automatic
semantic-damage proxy and Taiwan utility proxy are clean enough to support a
limited repaired-pipeline deployment claim.

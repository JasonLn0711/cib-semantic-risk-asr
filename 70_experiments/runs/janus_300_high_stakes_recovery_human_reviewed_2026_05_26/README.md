# Run Record: janus_300_high_stakes_recovery_human_reviewed_2026_05_26

## Purpose

Prepare the post-review recovery rerun path for the selected-300 CDS-ASR main
experiment. This is the human-reviewed counterpart to
`janus_300_high_stakes_recovery_proxy_2026_05_25`.

## Command

Current aggregate refresh command:

```bash
.venv/bin/python 80_semantic_risk_asr/recovery/evaluate_human_reviewed_recovery_policies.py \
  --allow-pending-summary
```

The selected-300 local audit sheet is now complete, so the paper-facing
recovery evidence uses the strict human-reviewed summary, without
`--allow-pending-summary`.

## Current Status

- `summary.json` is aggregate-only and safe to track.
- Current status is `human_reviewed_complete`.
- Current review counts are `30/30` selected rows and `90/90` model
  assessments.
- The five required recovery policies are present in `policy_comparison.tsv`:
  no recovery, confidence-only trigger, SRES-triggered recovery,
  CEIS-triggered conservative action, and CEIS ensemble arbitration.
- Human-reviewed recovery evidence supports recovery-specific claims. Remaining
  paper-readiness work belongs to the separate proxy-to-paper evidence gates.
- The normal `refresh_human_audit_evidence.py` path now refreshes this summary
  before the post-review evidence checklist.

## Boundary

The input audit sheet remains local-only because it contains row identifiers,
transcripts, hypotheses, and reviewer fields. Tracked outputs must stay
aggregate-only.

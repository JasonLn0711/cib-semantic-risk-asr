# Run Record: janus_300_high_stakes_recovery_human_reviewed_2026_05_26

## Purpose

Prepare the post-review recovery rerun path for the selected-300 CDS-ASR main
experiment. This is the human-reviewed counterpart to
`janus_300_high_stakes_recovery_proxy_2026_05_25`.

## Command

Current pending aggregate summary:

```bash
.venv/bin/python 80_semantic_risk_asr/recovery/evaluate_human_reviewed_recovery_policies.py \
  --allow-pending-summary
```

After the selected-300 local audit sheet is complete, rerun without
`--allow-pending-summary` and optionally write ignored per-sample detail under
`artifacts/`.

## Current Status

- `summary.json` is aggregate-only and safe to track.
- Current status is `review_pending`, not human-reviewed recovery evidence.
- Current review counts are `0/30` selected rows and `0/90` model assessments.
- `policies` is empty until the reviewer sheet is complete.
- The normal `refresh_human_audit_evidence.py` path now refreshes this summary
  before the post-review evidence checklist, so `recovery_proxy_only` will not
  clear until this run reports `evidence_mode=human_reviewed`.

## Boundary

The input audit sheet remains local-only because it contains row identifiers,
transcripts, hypotheses, and reviewer fields. Tracked outputs must stay
aggregate-only.

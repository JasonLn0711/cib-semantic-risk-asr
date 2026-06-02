# CSL Human Audit Expansion Queue

Date: 2026-06-02

Status: review queue prepared; human review pending.

This run prepares a 120-row expansion queue for the Paper 4-a CSL
submission-validation layer. The target is at least 100 completed reviewed
audio rows after cleanup. The local review sheet is transcript-bearing and is
written under ignored `artifacts/`; only aggregate selection summaries are
tracked.

## Inputs

- `70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/artifacts/metric_inputs_three_model/sres_scored.tsv`
- `70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/artifacts/metric_inputs_three_model/ceis_scored.tsv`
- `70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/artifacts/metric_inputs_three_model/downstream_escalation_decisions.tsv`

## Command

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/select_human_risk_atom_audit.py \
  --sres-scored 70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/artifacts/metric_inputs_three_model/sres_scored.tsv \
  --ceis-scored 70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/artifacts/metric_inputs_three_model/ceis_scored.tsv \
  --downstream-decisions 70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/artifacts/metric_inputs_three_model/downstream_escalation_decisions.tsv \
  --output-dir 70_experiments/runs/janus_300_high_stakes_human_audit_expansion_120_csl_2026_06_02 \
  --audit-size 120 \
  --quotas critical_or_high_risk_missed=24,unsafe_downrouting=24,low_wer_danger=16,high_proxy_risk=24,model_disagreement=16,clean_control=16
```

## Current Aggregate Result

- Candidate audio count: 300
- Selected audio count: 120
- Selected model-sample count: 360
- Status: `audit_selection_created_review_pending`

## Required Next Evidence

1. Complete the local 120-row human audit sheet.
2. Add a second reviewer on the same reviewed surface.
3. Compute aggregate-only agreement with
   `80_semantic_risk_asr/annotation/compute_human_audit_agreement.py`.
4. Regenerate predictor, recovery, and CEIS ablation summaries from the
   completed reviewed labels.

No submission claim should cite this run as completed human evidence until the
reviewed-row summaries report 100+ completed rows and reviewer agreement.

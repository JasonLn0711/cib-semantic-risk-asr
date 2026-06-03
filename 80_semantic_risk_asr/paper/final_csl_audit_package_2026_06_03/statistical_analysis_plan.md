# Statistical Analysis Plan

Date: 2026-06-03

Status: frozen for final CSL aggregate regeneration.

## Primary Unit And Clustering

The primary statistical unit is the audio row / case. The 900 model-level
assessments are clustered within the selected 300 rows and must not be treated
as 900 independent cases in primary fixed-budget claims.

```text
row_score = max_h score(row, h)
row_severe = any_h severe_miss(row, h)
```

## Label Rule

The main label is a deterministic two-reviewer consensus rule over completed
model-level review sheets:

- `yes` when both reviewers mark `yes`, or both are within `yes/uncertain` and
  at least one is `yes`;
- `no` when both reviewers mark `no`;
- `uncertain` for mixed `yes/no`, `no/uncertain`, or other unresolved cases.

This is a reproducible consensus rule, not a claim of independent third-party
adjudication.

## Endpoint Decision Tree

If row-level severe-miss positives are at least `20`, the primary empirical
endpoint is severe-miss remaining at pre-specified 10-20% row-level trigger
budgets.

If row-level severe-miss positives are fewer than `20`, the primary endpoint
falls back to decision-change AUC under clustered analysis, and severe-miss
frontiers are reported as descriptive high-severity evidence.

The 2026-06-03 aggregate regeneration found `6` row-level severe-miss positives,
so the final manuscript must use the failover endpoint unless new evidence
changes that count.

## Fixed Budgets

Budgets are row-level and pre-specified:

- 10% = 30 rows;
- 20% = 60 rows;
- 30% = 90 rows;
- 40% = 120 rows.

At tied cutoffs, report best-case and worst-case severe-miss remaining. Claims
use the worst-case boundary.

## Predictor Inference

Main predictor comparisons report:

- CEIS;
- SRES;
- WER/CER;
- SRES+CEIS fusion;
- variant-count proxy / capped CEIS stress tests.

CEIS-vs-SRES incremental analysis reports `AUC(CEIS) - AUC(SRES)` with
row-clustered bootstrap confidence intervals. Thresholds selected on the same
audit surface are diagnostic, not deployment thresholds.

## Sensitivity

Selection sensitivity must include:

- excluding `high_proxy_risk` rows;
- excluding metric-family selected rows when possible;
- reporting underpowered status when severe positives are fewer than `5`.

The manuscript may say a sensitivity pattern did or did not reverse; it should
not claim selection circularity has been eliminated.

## Release Boundary

Tracked outputs are aggregate-only. Raw audio, raw transcripts, row IDs,
hypotheses, reviewer notes, and transcript-bearing runtime logs remain local.

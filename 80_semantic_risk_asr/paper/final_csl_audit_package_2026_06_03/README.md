# Final CSL Audit Package

Date: 2026-06-03

Status: active final-execution package.

This directory records the frozen contracts and reviewer-facing aggregate
surfaces for the final CSL execution plan. It aligns the manuscript with the
completed selected-300 dual-reviewer audit and prevents the old 30/90 replay
surface from carrying main claims.

## Included Freeze Artifacts

- `downstream_decision_contract.md`
- `ceis_config.json`
- `variant_generator_contract.md`
- `statistical_analysis_plan.md`
- `synthetic_mandarin_minimal_pairs.tsv`

## Aggregate Regeneration Evidence

The current aggregate run is:

`70_experiments/runs/janus_300_high_stakes_final_csl_2026_06_03/`

It reports 300 selected rows, 900 model-level assessments, row-level fixed
budgets, CEIS/SRES/fusion comparisons, selection-exclusion sensitivity,
atom-level linguistic evidence, variant-count distribution, source coverage,
residual unsafe aggregate breakdown, and manifest hashes.

## Endpoint Decision

The 2026-06-03 regeneration found only 6 row-level severe-miss positives. The
final CSL manuscript must therefore use the pre-declared failover endpoint:
decision-change AUC under clustered analysis. Severe missed-escalation replay
remains descriptive high-severity evidence.

## CEIS Ablation Outcome

The final CEIS ablation run covers full CEIS, without plausibility, without
atom weights, binary atom, policy-distance-only, and top-3 aggregation.
Policy-distance-only matches full CEIS on the aggregate reviewed surface. The
final manuscript should therefore downgrade any claim that plausibility and atom
weights are proven performance drivers; they remain method components,
calibration handles, and interpretability/localization layers.

## Variant-Count Boundary

The final aggregate run reports nonzero variants for all 900 model assessments
with model-level variant count min `2`, median `4.0`, mean `3.664444`, and max
`5`. Reject-reason counts are not available in the current CEIS scored input,
so reject-reason taxonomy remains a generator-log extension rather than a main
empirical claim.

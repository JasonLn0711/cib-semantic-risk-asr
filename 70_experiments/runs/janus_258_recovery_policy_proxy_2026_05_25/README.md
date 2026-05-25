# JANUS 258 Proxy Recovery Policy Experiment

Status: proxy_completed

Date: 2026-05-25

## Purpose

Test whether CDS-ASR can do more than score ASR errors. This proxy experiment
compares five recovery conditions over the six-model 258-row split-aware metric
inputs:

1. no recovery;
2. confidence-only trigger;
3. SRES-triggered recovery;
4. CEIS-triggered conservative action;
5. CEIS + ASR ensemble arbitration.

This is an engineering gate, not final paper evidence. The inputs are proxy
risk-atom rows from the canonical test split, and the detailed per-sample
policy output remains in ignored local `artifacts/`.

## Command

```bash
.venv/bin/python 80_semantic_risk_asr/recovery/evaluate_recovery_policies.py \
  --downstream-decisions 70_experiments/runs/janus_258_test_split_asr_cds_proxy/artifacts/metric_inputs_six_model_validation/downstream_escalation_decisions.tsv \
  --sres-annotation 70_experiments/runs/janus_258_test_split_asr_cds_proxy/artifacts/metric_inputs_six_model_validation/sres_annotation.tsv \
  --counterfactual-variants 70_experiments/runs/janus_258_test_split_asr_cds_proxy/artifacts/metric_inputs_six_model_validation/counterfactual_variants.tsv \
  --output-summary-json 70_experiments/runs/janus_258_recovery_policy_proxy_2026_05_25/summary.json \
  --output-comparison-tsv 70_experiments/runs/janus_258_recovery_policy_proxy_2026_05_25/policy_comparison.tsv \
  --output-detail-tsv 70_experiments/runs/janus_258_recovery_policy_proxy_2026_05_25/artifacts/policy_detail.tsv
```

Thresholds used:

- confidence threshold: `0.70`;
- SRES threshold: `20.0`;
- CEIS threshold: `5.0`;
- ensemble mode: `priority`.

## Policy Semantics

- Confidence-only triggers only when calibrated confidence fields exist in the
  metric input. This run has `0` confidence values, so the confidence baseline
  is a no-trigger control.
- SRES-triggered recovery and CEIS-triggered conservative action never copy the
  reference label. They route low-risk ASR outputs to `priority_review` when
  their trigger fires.
- CEIS + ensemble arbitration also checks whether the six-model ASR label
  interval crosses the high-risk boundary. If it does, the policy emits a
  conservative `priority_review` route and counts the row as a machine
  abstention burden.

## Aggregate Result

| Policy | Unsafe downrouting | High-risk missed | Critical miss | Over-escalation | Triggered | Recovery budget | Machine abstention |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `no_recovery` | 187 | 161 | 9 | 8 | 0 | 0.0000 | 0 |
| `confidence_only_trigger` | 187 | 161 | 9 | 8 | 0 | 0.0000 | 0 |
| `sres_triggered_recovery` | 34 | 0 | 0 | 9 | 203 | 0.1311 | 0 |
| `ceis_triggered_conservative_action` | 75 | 41 | 0 | 9 | 150 | 0.0969 | 0 |
| `ceis_ensemble_arbitration` | 46 | 12 | 0 | 29 | 500 | 0.3230 | 468 |

Relative to no recovery:

- CEIS-triggered conservative action reduced unsafe downrouting by `112`
  samples (`59.89%`) and high-risk misses by `120` samples (`74.53%`) with one
  additional over-escalation.
- CEIS + ensemble arbitration reduced unsafe downrouting by `141` samples
  (`75.40%`) and high-risk misses by `149` samples (`92.55%`), but at a much
  higher abstention burden: `468 / 1548` samples.
- SRES-triggered recovery is strong on this proxy input, but it depends on the
  proxy SRES construction and should not be treated as final human-reviewed CDS
  evidence.

## Decision

Keep the recovery evaluator as the first automatic-recovery gate. The result is
sufficient to show that the repo now has a runnable recovery experiment and that
CEIS-triggered conservative action beats the available confidence-only baseline
on unsafe downrouting and high-risk misses.

Before paper-grade claims:

- add calibrated confidence fields or mark confidence-only as unavailable;
- run the same recovery policies on the selected 300-row high-stakes split;
- create a small human-reviewed risk-atom audit set to estimate proxy bias;
- report the cost side explicitly: over-escalation, abstention, and recovery
  budget.

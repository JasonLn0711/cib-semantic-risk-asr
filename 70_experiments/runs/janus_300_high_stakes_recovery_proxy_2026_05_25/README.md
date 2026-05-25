# Run Record: janus_300_high_stakes_recovery_proxy_2026_05_25

## Summary

- Status: proxy completed
- Date: 2026-05-25
- Dataset: JANUS high-stakes 300-row expansion
- Inputs: three-model high-stakes proxy metric inputs
- Model-samples: `900`
- Raw detail rows: ignored under `artifacts/policy_detail.tsv`

## Command

```bash
.venv/bin/python 80_semantic_risk_asr/recovery/evaluate_recovery_policies.py \
  --downstream-decisions 70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/artifacts/metric_inputs_three_model/downstream_escalation_decisions.tsv \
  --sres-annotation 70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/artifacts/metric_inputs_three_model/sres_annotation.tsv \
  --counterfactual-variants 70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/artifacts/metric_inputs_three_model/counterfactual_variants.tsv \
  --output-summary-json 70_experiments/runs/janus_300_high_stakes_recovery_proxy_2026_05_25/summary.json \
  --output-comparison-tsv 70_experiments/runs/janus_300_high_stakes_recovery_proxy_2026_05_25/policy_comparison.tsv \
  --output-detail-tsv 70_experiments/runs/janus_300_high_stakes_recovery_proxy_2026_05_25/artifacts/policy_detail.tsv
```

## Aggregate Results

| Policy | Unsafe downrouting | High-risk missed | Critical miss | Triggered | Budget | Abstention |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| No recovery | 29 | 6 | 1 | 0 | 0.0000 | 0 |
| Confidence-only | 29 | 6 | 1 | 0 | 0.0000 | 0 |
| SRES-triggered recovery | 24 | 0 | 0 | 35 | 0.0389 | 0 |
| CEIS conservative action | 24 | 0 | 0 | 35 | 0.0389 | 0 |
| CEIS + ensemble arbitration | 24 | 0 | 0 | 47 | 0.0522 | 18 |

Per-run no-recovery unsafe downrouting counts:

| Run | Rows | Unsafe downrouting | High-risk missed |
| --- | ---: | ---: | ---: |
| `breeze_asr25_partial_encoder_high_stakes_300` | 300 | 3 | 1 |
| `breeze_asr25_lora_high_stakes_300` | 300 | 6 | 0 |
| `breeze_asr25_base_high_stakes_300` | 300 | 20 | 5 |

## Boundary

This is proxy engineering evidence. It shows the recovery gate can be run over
the selected 300-row high-stakes set, but formal paper claims still require a
human risk-atom audit and reviewer-facing case selection.

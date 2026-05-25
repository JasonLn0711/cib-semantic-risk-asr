# Run Record: janus_300_high_stakes_cds_proxy_2026_05_25

## Summary

- Status: proxy completed
- Date: 2026-05-25
- Dataset: JANUS high-stakes 300-row expansion
- Models: partial encoder, Breeze-ASR-25 base, legacy LoRA
- Model-samples: `900`
- Review mode: proxy
- Raw metric inputs: ignored under `artifacts/metric_inputs_three_model/`

## Purpose

Build the first 300-row high-stakes CDS-ASR proxy evidence from the three
manifest-validated Breeze-family hypotheses. This is an engineering gate, not a
paper-grade human risk-atom audit.

## Commands

The first build attempt used the default 15-row `gold_review.tsv` plus the
high-stakes manifest. For a custom split, the builder treats all loaded
reference IDs as expected, so that attempt produced `315` reference rows and
failed the `--expected-rows 300` gate. The corrected run used the high-stakes
manifest as the sole reference source:

```bash
.venv/bin/python 80_semantic_risk_asr/scoring/build_janus_metric_inputs.py \
  --split high_stakes_300 \
  --manifest 70_experiments/runs/janus_300_500_high_stakes_expansion/artifacts/high_stakes_300_manifest.jsonl \
  --gold-review /dev/null \
  --hypotheses 70_experiments/runs/breeze_asr25_partial_encoder_high_stakes_300/predictions/breeze_asr25_partial_encoder_high_stakes_300_predictions.jsonl \
  --hypotheses 70_experiments/runs/breeze_asr25_base_high_stakes_300/predictions/breeze_asr25_base_high_stakes_300_predictions.jsonl \
  --hypotheses 70_experiments/runs/breeze_asr25_lora_high_stakes_300/predictions/breeze_asr25_lora_high_stakes_300_predictions.jsonl \
  --output-dir 70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/artifacts/metric_inputs_three_model \
  --review-mode proxy \
  --expected-rows 300 \
  --require-all-gold-ids
```

```bash
.venv/bin/python 80_semantic_risk_asr/scoring/semantic_risk_score.py \
  70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/artifacts/metric_inputs_three_model/sres_annotation.tsv \
  --output-json 70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/artifacts/metric_inputs_three_model/sres_summary.json \
  --output-tsv 70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/artifacts/metric_inputs_three_model/sres_scored.tsv
```

```bash
.venv/bin/python 80_semantic_risk_asr/scoring/counterfactual_escalation_instability.py \
  70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/artifacts/metric_inputs_three_model/counterfactual_variants.tsv \
  --output-json 70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/artifacts/metric_inputs_three_model/ceis_summary.json \
  --output-tsv 70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/artifacts/metric_inputs_three_model/ceis_scored.tsv
```

## Aggregate Results

| Item | Value |
| --- | ---: |
| Reference rows | 300 |
| Hypothesis files | 3 |
| Model-samples | 900 |
| SRES rows | 3298 |
| SRES total | 9690.0 |
| SRES mean | 2.938 |
| CEIS variant rows | 3298 |
| CEIS samples | 900 |
| CEIS unstable samples | 35 |
| CEIS mean | 0.2278 |
| CEIS max | 15.0 |
| Downstream rows | 900 |

## Boundary

The generated SRES/CEIS TSV and JSON artifacts contain reference and hypothesis
transcripts, so they remain ignored and local-only. Tracked files record only
aggregate counts and decisions.

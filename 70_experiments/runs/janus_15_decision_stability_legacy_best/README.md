# JANUS 15-Row Decision-Stability Legacy Best Comparison

Status: completed

Date: 2026-05-25

## Purpose

Extend the completed 15-row CDS-ASR pilot with the two curated legacy
Breeze-ASR-25 best artifacts:

- `breeze_asr25_lora_legacy_best_15_row`
- `breeze_asr25_partial_encoder_legacy_best_15_row`

This run checks whether the legacy models merely improve transcript similarity
or also improve downstream decision stability.

## Inputs

All hypothesis files use the same fixed 15 `audio_id` set and passed
`validate_janus_asr_hypotheses.py --require-labels --require-quality-signal`.

| Run | Prediction source |
| --- | --- |
| `whisper_small_15_row_baseline` | ignored local predictions JSONL |
| `whisper_large_v2_15_row_baseline` | ignored local predictions JSONL |
| `breeze_asr25_15_row_baseline` | ignored local predictions JSONL |
| `breeze_asr25_lora_legacy_best_15_row` | ignored local predictions JSONL |
| `breeze_asr25_partial_encoder_legacy_best_15_row` | ignored local predictions JSONL |

## Execution

Metric input build:

```bash
.venv/bin/python 80_semantic_risk_asr/scoring/build_janus_pilot_metric_inputs.py \
  --hypotheses 70_experiments/runs/whisper_small_15_row_baseline/predictions/whisper_small_15_row_baseline_predictions.jsonl \
  --hypotheses 70_experiments/runs/whisper_large_v2_15_row_baseline/predictions/whisper_large_v2_15_row_baseline_predictions.jsonl \
  --hypotheses 70_experiments/runs/breeze_asr25_15_row_baseline/predictions/breeze_asr25_15_row_baseline_predictions.jsonl \
  --hypotheses 70_experiments/runs/breeze_asr25_lora_legacy_best_15_row/predictions/breeze_asr25_lora_legacy_best_15_row_predictions.jsonl \
  --hypotheses 70_experiments/runs/breeze_asr25_partial_encoder_legacy_best_15_row/predictions/breeze_asr25_partial_encoder_legacy_best_15_row_predictions.jsonl \
  --output-dir 70_experiments/runs/janus_15_decision_stability_legacy_best/artifacts/metric_inputs
```

Scoring:

```bash
.venv/bin/python 80_semantic_risk_asr/scoring/semantic_risk_score.py \
  70_experiments/runs/janus_15_decision_stability_legacy_best/artifacts/metric_inputs/sres_annotation.tsv
.venv/bin/python 80_semantic_risk_asr/scoring/counterfactual_escalation_instability.py \
  70_experiments/runs/janus_15_decision_stability_legacy_best/artifacts/metric_inputs/counterfactual_variants.tsv
.venv/bin/python 80_semantic_risk_asr/downstream/evaluate_downstream_impact.py \
  70_experiments/runs/janus_15_decision_stability_legacy_best/artifacts/metric_inputs/downstream_escalation_decisions.tsv
```

## Results

| Run | CER | WER | Mean CEIS | Max CEIS | Unstable samples | Downstream mismatch | High-risk missed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `whisper_small_15_row_baseline` | 53.08 | 500.00 | 2.47 | 8.00 | 7 | 0.4667 | 1 |
| `whisper_large_v2_15_row_baseline` | 40.01 | 100.00 | 2.80 | 15.00 | 6 | 0.4000 | 2 |
| `breeze_asr25_15_row_baseline` | 36.13 | 380.00 | 1.27 | 5.00 | 4 | 0.2667 | 0 |
| `breeze_asr25_lora_legacy_best_15_row` | 30.99 | 100.00 | 1.80 | 8.00 | 5 | 0.3333 | 1 |
| `breeze_asr25_partial_encoder_legacy_best_15_row` | 12.77 | 83.33 | 1.27 | 5.00 | 4 | 0.2667 | 0 |

Aggregate bridge outputs:

- Metric input build: 15 gold rows, 5 hypothesis files, 260 SRES rows, 260 CEIS
  rows, 75 downstream rows, no unmatched hypotheses.
- SRES: total `8106.0`, mean `31.177`.
- CEIS: 75 model-samples, 26 unstable samples, max `15.0`, mean `1.92`.
- Downstream: mismatch rate `0.3467`, high-risk missed by ASR `4`, no recovery
  applied.

## Interpretation

The partial encoder is the strongest ASR candidate on this 15-row gate: it has
the best CER and WER and matches the base Breeze-ASR-25 decision-stability
profile. The LoRA run improves CER over base Breeze-ASR-25 but is worse on
mean CEIS, unstable samples, mismatch rate, and high-risk misses. That is
exactly the paper-relevant signal: lower CER alone is not sufficient evidence
of safer downstream behavior.

## Local Artifacts

Raw predictions, metric inputs, metric outputs, and runtime logs stay local
under ignored `predictions/` and `artifacts/` paths.

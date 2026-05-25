# JANUS Split-Aware Metric Input Builder Gate

Status: completed

Date: 2026-05-25

## Purpose

Move metric-input generation out of the 15-row-only pilot path so `pilot_15`,
`test_258`, and the selected `high_stakes_300` experiment can use the same
SRES, CEIS, and downstream input contract.

This is the bridge between the completed 258-row ASR proxy comparison and the
future 300-row main experiment. Raw metric inputs and scoring outputs remain in
ignored local `artifacts/` paths.

## Ground-Truth Boundary

The repo currently has full manifest-level reference transcripts for the
canonical `janus_165_v1` dataset:

- train: `4201` rows;
- validation: `508` rows;
- test: `258` rows;
- all: `4967` rows;
- missing transcript text in these manifests: `0`;
- missing audio references in these manifests: `0`.

These manifest transcripts are already part of the ASR, CER, selection, and
proxy-metric workflows. They are not the same as full human-reviewed CDS ground
truth.

The current human-reviewed CDS ground truth is the 15-row gold subset in
`40_breeze_asr25_finetune_dataset/reports/gold_subset_review.tsv`, which
contains `human_verified_transcript`, `semantic_risk_label`, `risk_atoms`, and
`would_asr_error_change_decision`. The 258-row test split can be processed in
proxy mode, but it should not be described as fully human-reviewed CDS evidence
until a risk-atom audit set is completed.

## Script

```text
80_semantic_risk_asr/scoring/build_janus_metric_inputs.py
```

Key behavior:

- supports named experiment splits such as `pilot_15`, `test_258`, and
  `high_stakes_300`;
- supports `--review-mode human`, `--review-mode proxy`, and `--review-mode auto`;
- writes the same three downstream files used by existing scoring scripts:
  `sres_annotation.tsv`, `counterfactual_variants.tsv`, and
  `downstream_escalation_decisions.tsv`;
- marks proxy rows explicitly so engineering gates are not overstated as
  human-reviewed risk-atom evidence;
- can require every gold/reference ID to appear in each hypothesis file.

## Validation 1: 15-Row Human-Reviewed Compatibility

Command intent:

```bash
.venv/bin/python 80_semantic_risk_asr/scoring/build_janus_metric_inputs.py \
  --split pilot_15 \
  --review-mode human \
  --expected-rows 15 \
  --require-all-gold-ids \
  --hypotheses 70_experiments/runs/whisper_small_15_row_baseline/predictions/whisper_small_15_row_baseline_predictions.jsonl \
  --hypotheses 70_experiments/runs/whisper_large_v2_15_row_baseline/predictions/whisper_large_v2_15_row_baseline_predictions.jsonl \
  --hypotheses 70_experiments/runs/breeze_asr25_15_row_baseline/predictions/breeze_asr25_15_row_baseline_predictions.jsonl \
  --hypotheses 70_experiments/runs/breeze_asr25_lora_legacy_best_15_row/predictions/breeze_asr25_lora_legacy_best_15_row_predictions.jsonl \
  --hypotheses 70_experiments/runs/breeze_asr25_partial_encoder_legacy_best_15_row/predictions/breeze_asr25_partial_encoder_legacy_best_15_row_predictions.jsonl \
  --output-dir 70_experiments/runs/janus_15_decision_stability_legacy_best/artifacts/metric_inputs_split_aware_validation
```

Result:

- Builder summary: `ok=true`.
- Reference rows: `15`.
- Hypothesis files: `5`.
- Review-mode rows: `75` human-reviewed, `0` proxy.
- SRES input rows: `260`.
- CEIS input rows: `260`.
- Downstream decision rows: `75`.
- Missing reference text: `0`.
- Missing hypothesis text: `0`.
- Missing ASR labels: `0`.
- Missing expected IDs: `0`.

Scoring compatibility:

- SRES: rows `260`, total `8106.0`, mean `31.177`.
- CEIS: variant rows `260`, samples `75`, unstable samples `26`, max `15.0`,
  mean `1.92`.
- Downstream: rows `75`, ASR mismatch rate `0.3467`, high-risk missed by ASR
  `4`, recovery trigger rate `0.0`.

Interpretation: the split-aware builder preserves the existing 15-row
legacy-best CDS-ASR bridge behavior and can replace the pilot-only builder for
future runs.

## Validation 2: 258-Row Proxy Mode

Command intent:

```bash
.venv/bin/python 80_semantic_risk_asr/scoring/build_janus_metric_inputs.py \
  --split test_258 \
  --review-mode proxy \
  --manifest 40_breeze_asr25_finetune_dataset/manifests/test.jsonl \
  --gold-review 40_breeze_asr25_finetune_dataset/manifests/test_with_sources.tsv \
  --expected-rows 258 \
  --require-all-gold-ids \
  --hypotheses 70_experiments/runs/breeze_asr25_partial_encoder_legacy_best_test_split/predictions/breeze_asr25_partial_encoder_legacy_best_test_split_predictions.jsonl \
  --hypotheses 70_experiments/runs/breeze_asr25_lora_legacy_best_test_split/predictions/breeze_asr25_lora_legacy_best_test_split_predictions.jsonl \
  --output-dir 70_experiments/runs/janus_258_test_split_asr_cds_proxy/artifacts/metric_inputs_split_aware_validation
```

Result:

- Builder summary: `ok=true`.
- Reference rows: `258`.
- Hypothesis files: `2`.
- Review-mode rows: `0` human-reviewed, `516` proxy.
- SRES input rows: `1057`.
- CEIS input rows: `1057`.
- Downstream decision rows: `516`.
- Missing reference text: `0`.
- Missing hypothesis text: `0`.
- Missing ASR labels: `0`.
- Missing expected IDs: `0`.

Scoring compatibility:

- SRES: rows `1057`, total `2760.0`, mean `2.611`.
- CEIS: variant rows `1057`, samples `480`, unstable samples `21`, max `10.0`,
  mean `0.3417`.
- Downstream: rows `516`, ASR mismatch rate `0.0426`, high-risk missed by ASR
  `11`, recovery trigger rate `0.0`.

Interpretation: the builder can produce split-aware metric inputs for the
canonical 258-row test split, but these rows are proxy-only because they do not
have full human-reviewed risk-atom annotations. Use them for engineering gates,
candidate triage, and case selection, not as final human-reviewed CDS evidence.

## Next Decision

Use `build_janus_metric_inputs.py` for new split-level work. The next execution
gate is:

1. complete comparable 258-row baselines for Whisper large-v3 and Whisper
   large-v3 turbo;
2. rerun this builder over the expanded hypothesis set. The later six-model
   validation including Breeze-ASR-26 is recorded under
   `70_experiments/runs/janus_258_test_split_asr_cds_proxy/`;
3. create a small human-reviewed risk-atom audit set before treating 258-row or
   300-row proxy results as paper-grade CDS evidence;
4. use the same builder interface for the selected 300-row high-stakes main
   experiment.

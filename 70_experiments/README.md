# Experiment Log

Use this folder for Whisper ASR experiment records and reproducibility notes.

For paper-facing work, record not only ASR surface metrics but also
semantic-risk and downstream escalation outcomes defined in
`../80_semantic_risk_asr/`.

## Required Flow

1. Choose a config from `../60_whisper_asr_finetuning/configs/`.
2. Create `runs/<run_id>/`.
3. Copy `templates/run_record.md` into `runs/<run_id>/README.md`.
4. Add or update one row in `registry.tsv`.
5. Store metric curves in `runs/<run_id>/metrics.csv`.
6. Store reviewed qualitative errors in `runs/<run_id>/error_analysis.tsv`.

Checkpoints, TensorBoard logs, W&B folders, and bulk predictions should stay
local and are ignored by `.gitignore` unless a separate packaging decision is
made.

## Folder Contract

```text
70_experiments/
  registry.tsv
  templates/
    run_record.md
    metrics.csv
    error_analysis.tsv
  runs/
    <run_id>/
      README.md
      metrics.csv
      error_analysis.tsv
      checkpoints/       # ignored
      logs/              # ignored
      predictions/       # ignored
```

## Minimum Comparable Metrics

Every completed ASR run should report:

- validation CER, with normalization and macro/micro scope stated
- validation WER, with tokenizer, normalization, and macro/micro scope stated
- test CER, with normalization and macro/micro scope stated
- test WER, with tokenizer, normalization, and macro/micro scope stated
- model name or checkpoint
- dataset version
- config path
- seed
- hardware notes
- failure notes, if any

For semantic-risk ASR experiments, also report:

- semantic-risk counts;
- SRES distribution;
- CEIS distribution;
- decision-unstable variant count;
- downstream escalation failure rate;
- high-risk miss rate;
- recovery policy triggered;
- automatic recovery budget;
- machine abstention rate;
- conservative escalation cost.
- metric-predictor AUC/F1 against downstream labels;
- low-WER danger count;
- risk-atom instability breakdown.

The 2026-05-25 WER audit defines the repo policy: the aggregate
`cer_zh_micro` column is the primary paper-facing ASR surface metric;
`wer_zh_jieba_micro` is supplemental; raw whitespace WER is legacy audit-only
for unsegmented Chinese transcripts. The audit should be run with the canonical
split manifest so missing/extra IDs, reference mismatches, zero-reference
metric units, tokenizer, normalization, and package versions are recorded.

For metric-predictor evidence, use
`../80_semantic_risk_asr/scoring/analyze_metric_predictors.py`. It reads local
SRES/CEIS/downstream TSV artifacts but writes only aggregate tables, so raw
transcripts and sample-level rows remain local-only.

## JANUS 15-Row Decision-Stability Pilot

Use `runs/janus_15_decision_stability_pilot/` for the first reviewed CDS-ASR
gate after `gold_subset_review.tsv` and the bounded long-silence review are
complete.

Generate local metric-input artifacts with:

```bash
python 80_semantic_risk_asr/scoring/build_janus_pilot_metric_inputs.py \
  --hypotheses <asr_hypotheses.tsv-or-jsonl>
```

The generated `artifacts/metric_inputs/` files are intentionally ignored:

- `sres_annotation.tsv`
- `counterfactual_variants.tsv`
- `downstream_escalation_decisions.tsv`
- `build_summary.json`

Only aggregate metrics, run records, and publication-safe examples should be
committed after review.

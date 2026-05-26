# CDS-ASR Figure Package

Date: 2026-05-26

These manuscript figures are generated from aggregate-only evidence. They do
not include transcript text, audio IDs, selected row IDs, reviewer notes,
model hypotheses, or transcript-bearing runtime logs.

Generate with:

```bash
python 80_semantic_risk_asr/paper/generate_paper_figures.py
```

| Figure | File | Source | Privacy boundary |
| --- | --- | --- | --- |
| F1. CDS-ASR pipeline | `f1_cds_asr_pipeline.svg` | method text | no row content |
| F2. Evidence boundary | `f2_evidence_boundary.svg` | publishable evidence summary | aggregate status only |
| F3. Predictor AUC | `f3_predictor_auc.svg` | `human_audit_predictor_comparison.tsv` | aggregate predictor metrics |
| F4. Recovery outcomes | `f4_recovery_outcomes.svg` | `policy_comparison.tsv` | aggregate policy counts |
| F5. Model lane state | `f5_model_lane_state.svg` | main/candidate aggregate summaries | aggregate lane state |

# CDS-ASR Figure Package

Date: 2026-05-28

These manuscript figures are generated from aggregate-only evidence. They do
not include transcript text, audio IDs, selected row IDs, reviewer notes,
model hypotheses, or transcript-bearing runtime logs.

Generate with:

```bash
python 80_semantic_risk_asr/paper/generate_paper_figures.py
```

| Figure | SVG | PDF | Source | Privacy boundary |
| --- | --- | --- | --- | --- |
| F1. CDS-ASR pipeline | `f1_cds_asr_pipeline.svg` | `f1_cds_asr_pipeline.pdf` | method text | no row content |
| F2. Evidence boundary | `f2_evidence_boundary.svg` | `f2_evidence_boundary.pdf` | publishable evidence summary | aggregate status only |
| F3. Predictor AUC | `f3_predictor_auc.svg` | `f3_predictor_auc.pdf` | `human_audit_predictor_comparison.tsv` | aggregate predictor metrics |
| F4. Recovery outcomes | `f4_recovery_outcomes.svg` | `f4_recovery_outcomes.pdf` | `policy_comparison.tsv` | aggregate policy counts |
| F5. Model lane state | `f5_model_lane_state.svg` | `f5_model_lane_state.pdf` | main/candidate aggregate summaries | aggregate lane state |
| F6. Evidence N-ladder | `f6_n_ladder.svg` | `f6_n_ladder.pdf` | method evidence units | aggregate counts only |
| F7. Budget-risk frontier | `f7_budget_risk_frontier.svg` | `f7_budget_risk_frontier.pdf` | `fixed_budget_recovery_frontier.tsv` | aggregate policy counts |

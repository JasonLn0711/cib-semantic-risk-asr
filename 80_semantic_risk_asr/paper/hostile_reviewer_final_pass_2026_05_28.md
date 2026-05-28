# Hostile Reviewer Final Pass

Date: 2026-05-28

Scope: `80_semantic_risk_asr/paper/manuscript_draft.md`,
`80_semantic_risk_asr/paper/references.bib`, aggregate figures, and
submission-facing artifacts.

Verdict: submission-prep pass with scoped claims. The manuscript now presents
CDS-ASR as a high-stakes decision-stability audit framework, not an ASR
leaderboard or a deployed causal intervention.

| Reviewer attack | Current manuscript defense | Evidence surface | Status |
| --- | --- | --- | --- |
| The 90 assessments are treated as independent calls. | The N-ladder states that 90 model assessments are clustered within 30 reviewed rows; Tables 3 and 4 report row-clustered uncertainty. | `human_audit_predictor_clustered_ci.tsv`; `policy_comparison_clustered_ci.tsv`; F6 | Pass |
| The selected-300 surface creates selection bias. | The text describes selected-300 as an enriched high-stakes audit surface, not prevalence evidence. | `selection_provenance_summary.tsv`; selection provenance section | Pass |
| CEIS threshold is post-hoc. | Thresholds are named diagnostic operating points, not frozen deployment thresholds. | Table 3 wording; limitations | Pass |
| CEIS is claimed to universally beat SRES. | The manuscript states CEIS has stronger AUC/zero-FN behavior, while SRES has best-threshold F1 and ties recovery at the diagnostic budget. | Tables 3 and 4 | Pass |
| Recovery is written as live causality. | Recovery is framed as aggregate policy replay over scoped labels. | Table 4; Discussion; Limitations | Pass |
| Fixed-budget result is missing. | F7 and Appendix Table A1 report the fixed-budget frontier from the aggregate replay artifact. | `fixed_budget_recovery_frontier.tsv`; F7; Appendix Table A1 | Pass |
| Residual unsafe downrouting is hidden. | The manuscript states unsafe downrouting remains 24 after SRES/CEIS conservative replay and requires separate governance. | Table 4; Discussion; Limitations | Pass |
| Confidence-only baseline is unfair. | It is named calibrated-confidence unavailable, not a calibrated confidence baseline. | Table 4 | Pass |
| CEIS is not reconstructable. | CEIS uses `Plausibility(v | x)` and points to versioned method contracts for weights and decision distance. | `docs/ceis_method_spec.md`; `docs/risk_atom_weights.tsv`; `docs/downstream_decision_contract.md`; `ceis_config.json` | Pass |
| Variant generation is opaque. | The manuscript reports aggregate CEIS top-atom proxy coverage and states source-specific generator logs are a planned validation extension. | `counterfactual_variant_coverage_summary.tsv` | Scoped pass |
| Human review lacks IAA. | The manuscript explicitly states no second-reviewer blinded spot-check is included and no inter-annotator agreement is claimed. | Limitations; Variant Coverage And Human Review Reliability | Pass |
| Privacy boundary blocks reproducibility. | The artifact availability section states the paper claims aggregate reproducibility, not public row-level reproducibility. | Artifact manifest; privacy boundary docs; leak scan | Pass |
| Citation claims are unsupported. | Real-world and related-work claims cite official AWS, NPA, FBI/IC3, ISCA, NIH, NIST, and EU sources with 2026-05-28 access dates. | `references.bib`; `citation_seed.md` | Pass |
| No LaTeX manuscript exists. | `manuscript_submission.tex` is generated from the current manuscript source and compiles as the submission-format draft. | `manuscript_submission.tex`; XeLaTeX build in `/tmp/cib_tex_build` | Pass |

Final writing rule: keep claims positive and scoped. The supported contribution
is a privacy-preserving, aggregate-auditable decision-stability evidence layer
for high-stakes ASR, with CEIS as a conservative instability signal and SRES as
a strong semantic-risk baseline.

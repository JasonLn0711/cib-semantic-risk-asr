# Paper 4 LaTeX Transformation Instructions

Date: 2026-06-02

Constraint:

> Do not touch the latest original manuscript. Treat
> `manuscript_submission.tex`, `manuscript_submission.pdf`, and
> `manuscript_draft.md` as source references only. Build new manuscripts in
> separate files or directories.

Recommended new paths:

- `80_semantic_risk_asr/paper/paper4a_speech_technology/manuscript_paper4a.tex`
- `80_semantic_risk_asr/paper/paper4a_speech_technology/references_paper4a.bib`
- `80_semantic_risk_asr/paper/paper4a_speech_technology/figures/`
- `80_semantic_risk_asr/paper/paper4b_trustworthy_ai/manuscript_paper4b.tex`
- `80_semantic_risk_asr/paper/paper4b_trustworthy_ai/references_paper4b.bib`
- `80_semantic_risk_asr/paper/paper4b_trustworthy_ai/figures/`

## 1. Sections To Copy Into Paper 4-a

Copy and rewrite:

- Abstract: speech-evaluation abstract only.
- Introduction: keep speech-to-decision and WER/CER insufficiency framing.
- Related Work: keep ASR metrics, semantic ASR metrics, ASR correction,
  confidence filtering, selective prediction.
- Method:
  - problem formulation;
  - risk atom schema;
  - plausible ASR variants;
  - SRES;
  - CEIS;
  - recovery policies.
- Experiments:
  - 258-row ASR split;
  - selected-300 provenance;
  - 30 reviewed rows / 90 clustered model assessments;
  - predictor comparison;
  - aggregate policy replay.
- Results:
  - Table 1 ASR context;
  - Table 3 predictor comparison;
  - Table 4 recovery;
  - fixed-budget frontier if needed.
- Discussion: focus on downstream-aware ASR evaluation.
- Limitations: ASR-evaluation limitations.
- Data Availability: concise aggregate-only statement.

Delete or shorten in Paper 4-a:

- full claim registry;
- full artifact manifest prose;
- long validation gate commands;
- operation-record details;
- long privacy/governance taxonomy.
- NIST / EU AI Act framing.

Move to appendix in Paper 4-a:

- candidate lane;
- full fixed-budget frontier;
- variant coverage summary;
- selected-300 provenance details;
- claim registry excerpt;
- validation gate summary.

Keep a short ethics, privacy, and intended-use paragraph in the main Paper 4-a
text. Do not delete this boundary, but do not let it dominate a Computer Speech
& Language or Speech Communication submission.

## 2. Sections To Copy Into Paper 4-b

Copy and reframe:

- Ethics, Privacy, and Intended Use.
- Appendix / Artifact Availability.
- Supplementary Claim Registry.
- Validation Gate Commands.
- Scope Control For Additional Validation.
- Evidence boundary paragraphs.
- Artifact manifest and claim registry references.
- Limitations that describe release boundary, single-expert audit, diagnostic
  thresholds, selected-300 enrichment, and clustered assessments.
- NIST / EU AI Act and responsible-AI framing, with careful wording that treats
  them as governance context rather than legal compliance claims.

Summarize instead of copying:

- CDS-ASR method;
- CEIS equation / scoring detail;
- WER/CER/SRES comparisons;
- recovery policy mechanics;
- ASR candidate lane.

Delete from Paper 4-b main text:

- detailed speech-technology literature review;
- technical proof-like CEIS narrative;
- figure/table sequence whose only role is showing CEIS performance.

## 3. How To Rename Figures And Tables

Paper 4-a:

| Current asset | Paper 4-a name | Role |
| --- | --- | --- |
| `figure1_cds_asr_pipeline_redrawn.pdf` | `fig1_cds_asr_method.pdf` | Main method pipeline |
| `figure2_evidence_ladder_redrawn.pdf` | `fig2_evidence_design.pdf` | Evidence design |
| `f3_predictor_auc.pdf` | `fig3_predictor_comparison.pdf` | Main result |
| `f4_recovery_outcomes.pdf` | `fig4_policy_replay.pdf` | Main result |
| `f7_budget_risk_frontier.pdf` | `fig5_budget_frontier.pdf` | Main or supplement |
| `f10_human_reviewed_atom_outcomes.pdf` | `figS1_risk_atom_review.pdf` | Supplement |
| `table1_main_asr.tex` | `table1_asr_context.tex` | Main |
| `table3_predictor.tex` | `table2_predictor_metrics.tex` | Main |
| `table4_recovery.tex` | `table3_policy_replay.tex` | Main |
| `table_a1_fixed_budget_frontier.tex` | `tableS1_fixed_budget_frontier.tex` | Supplement |
| `table_s2_candidates.tex` | `tableS2_candidate_lane.tex` | Supplement |

Paper 4-b:

| Current/source asset | Paper 4-b name | Role |
| --- | --- | --- |
| `figure2_evidence_ladder_redrawn.pdf` | `fig1_evidence_ladder.pdf` | Main case-study evidence ladder |
| new release-boundary diagram | `fig2_release_boundary.pdf` | Main governance figure |
| new claim-evidence workflow | `fig3_claim_evidence_workflow.pdf` | Main framework figure |
| claim registry excerpt | `table1_claim_boundary_registry.tex` | Main |
| artifact privacy classes | `table2_artifact_privacy_classes.tex` | Main |
| validation gates | `table3_validation_gates.tex` | Main |
| case evidence layers | `table4_case_evidence_layers.tex` | Main |
| artifact manifest excerpt | `tableS1_manifest_excerpt.tex` | Supplement |

## 4. Avoid Overlapping Abstracts

Paper 4-a abstract must start with:

> Speech recognition outputs increasingly serve as operational inputs...

Paper 4-b abstract must start with:

> Reproducible evaluation is difficult when AI systems are tested on sensitive
> speech evidence...

Paper 4-a should name CDS-ASR and CEIS in the first half of the abstract.
Paper 4-b should name aggregate-only reproducibility and claim-evidence
governance in the first half of the abstract. Paper 4-b may mention CDS-ASR
only as the case study.

## 5. Avoid Overlapping Introductions

Paper 4-a introduction sequence:

```text
speech-to-decision systems
-> ASR hypotheses as operational signals
-> WER/CER and semantic metrics
-> decision-stability gap
-> CDS-ASR and CEIS
-> scoped evidence
```

Paper 4-b introduction sequence:

```text
sensitive speech AI evidence
-> open reproducibility tension
-> raw transcript release is unsafe or unavailable
-> reviewer-visible auditability gap
-> aggregate-only claim-evidence governance
-> CDS-ASR as case study
```

Do not reuse the same first paragraph.

## 6. Avoid Overlapping Conclusions

Paper 4-a conclusion:

> CDS-ASR extends ASR evaluation by testing whether plausible transcript
> alternatives around spoken risk atoms change downstream decisions.

Paper 4-b conclusion:

> Aggregate-only reproducibility can make sensitive speech AI evaluations
> reviewer-auditable through manifests, validation gates, operation records, and
> claim-boundary registries without releasing transcript-bearing evidence.

## 7. Preserve Ethical Transparency Without Distracting

Paper 4-a:

- Keep ethics/data availability concise.
- State the release boundary.
- Do not let privacy governance dominate the speech-evaluation contribution.
- Put detailed governance apparatus in supplement or cite Paper 4-b.

Paper 4-b:

- Make ethics/release boundary central.
- Do not re-litigate CEIS performance.
- Use CEIS only to show why bounded claim-evidence alignment matters.

## 8. Required Claim-Evidence Guardrails

Use these exact guardrails in both papers:

- Do not invent new experimental results.
- Do not overclaim deployment readiness.
- Do not describe 90 model assessments as 90 independent calls.
- Keep distinct:
  - 258 ASR test rows;
  - selected-300 provenance outputs;
  - 30 human-reviewed audit rows;
  - 90 clustered model assessments.
- Treat thresholds as diagnostic operating points, not deployment thresholds.
- Treat CEIS plausibility as a bounded proxy, not a calibrated acoustic
  posterior.
- Treat selected-300 as an enriched high-stakes audit surface, not a
  prevalence-preserving sample.
- Treat human review as single-expert audit unless a second blinded reviewer is
  actually added.
- Keep raw audio, raw transcripts, row identifiers, reviewer notes, and
  transcript-bearing runtime logs outside the public release boundary.

## 9. Minimum Build Workflow

1. Create new directories for Paper 4-a and Paper 4-b.
2. Copy only selected sections into the new manuscripts.
3. Rename figures and table fragments in the new manuscript directories.
4. Build each PDF independently in `/tmp` first.
5. Run transcript-bearing leak checks before packaging.
6. Run citation reciprocity checks.
7. Keep a companion-manuscript disclosure note ready if both papers are
   submitted within the same window.

Do not overwrite the existing `manuscript_submission.*` files.

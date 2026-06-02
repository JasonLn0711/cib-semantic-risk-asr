# Paper 4 Split Diagnosis

Date: 2026-06-02

Source manuscript, preserved unchanged:

- `80_semantic_risk_asr/paper/manuscript_submission.tex`
- `80_semantic_risk_asr/paper/manuscript_submission.pdf`
- `80_semantic_risk_asr/paper/manuscript_draft.md`

Split decision:

> The current manuscript contains two publishable contributions. Paper 4-a
> should carry the speech-technology evaluation contribution: CDS-ASR, risk
> atoms, plausible ASR alternatives, CEIS, WER/CER/SRES comparison, human-reviewed
> decision-change labels, and aggregate policy replay. Paper 4-b should carry
> the trustworthy-AI/reproducible-evaluation contribution: aggregate-only
> reproducibility for sensitive speech evidence, artifact manifests, privacy
> boundaries, operation records, validation gates, claim-evidence alignment, and
> reviewer-visible auditability.

The split should preserve one empirical case while avoiding duplicate
publication risk. Paper 4-a proves the ASR evaluation method. Paper 4-b uses
the CDS-ASR study as a case example for reproducible governance of sensitive
speech AI evaluation.

Operational split rule:

- Paper 4-a says: we propose a new speech evaluation method.
- Paper 4-b says: we propose a reviewer-auditable reproducibility framework for
  sensitive speech AI research.

The shared case is acceptable only because the novelty differs. Paper 4-a's
novelty is decision-stability ASR evaluation. Paper 4-b's novelty is
aggregate-only auditability under sensitive-data constraints.

## 1. Allocation By Concept

| Concept | Paper 4-a: Speech technology | Paper 4-b: Trustworthy AI / reproducibility | Shared only as short background |
| --- | --- | --- | --- |
| WER/CER limits | Central motivation and baseline | Background example of claim-evidence mismatch | Yes, but with different emphasis |
| Risk atoms | Central technical abstraction | Case-study evidence object | Yes |
| Plausible ASR alternatives | Central technical method | Example of sensitive derived evidence requiring boundary control | Yes |
| CEIS | Central decision-stability metric | Case-study metric whose claims must be bounded | Yes |
| SRES | Baseline / comparator | Example of metric-layer evidence | Yes |
| Human-reviewed decision-change labels | Central evaluation label source | Governance layer and audit-boundary example | Yes |
| 258 ASR test rows | ASR model-comparison context | Evidence-layer example in taxonomy | Yes |
| selected-300 provenance outputs | Audit-surface construction | Case-study provenance layer | Yes |
| 30 reviewed rows / 90 clustered model assessments | Central predictor/recovery evaluation | Case-study audit layer | Yes |
| Aggregate policy replay | Central downstream evaluation | Case-study aggregate replay artifact | Yes |
| Artifact manifests | Appendix / reproducibility support | Central contribution | Short note only |
| Privacy-preserving release boundary | Required ethics/data statement | Central contribution | Short note only |
| Operation records | Appendix / supplement | Central contribution | Short note only |
| Validation gates | Supplementary quality control | Central contribution | Short note only |
| Claim registry | Supplementary claim map | Central contribution | Short note only |
| Reviewer-visible auditability | Supporting submission feature | Main thesis | Short note only |
| NIST / EU AI Act framing | Short ethics/governance context only | Responsible-AI background and discussion layer | Yes, but not as the main empirical claim |

## 2. Allocation By Current Manuscript Section

| Current section | Paper 4-a handling | Paper 4-b handling |
| --- | --- | --- |
| Abstract | Rewrite around CDS-ASR as downstream-aware ASR evaluation | Rewrite around aggregate-only reproducibility and claim-evidence governance |
| Introduction | Keep speech-to-decision opening, WER/CER/semantic metric landscape, decision-stability gap | Use a shorter opening on sensitive speech AI evidence and reproducibility barriers |
| Related Work | Keep ASR metrics, semantic ASR metrics, ASR correction, selective prediction | Replace with reproducible ML, responsible AI documentation, data governance, privacy-preserving auditability |
| Method | Keep risk atoms, variants, CEIS, SRES, recovery policies | Summarize CDS-ASR briefly; make the method the aggregate-only reproducibility framework |
| Experiments | Central: 258 rows, selected-300 provenance, 30/90 reviewed audit, predictor and policy replay | Case study: evidence layers, artifact manifest checks, validation gates, release-boundary decisions |
| Results | Central: predictor table, recovery table, ASR comparison context | Recast as governance audit results: what each aggregate artifact makes auditable |
| Discussion | Discuss ASR evaluation implications and downstream stability | Discuss reproducibility, reviewer trust, release boundary, governance tradeoffs |
| Supplementary Claim Registry | Move to appendix/supplement | Central table and framework component |
| Ethics, Privacy, Intended Use | Keep concise and journal-ready | Expand as core governance evidence |
| Limitations | Keep ASR/evaluation limitations | Expand governance/reproducibility limitations |
| Appendix / Artifact Availability | Shorten; keep data statement and artifact availability | Central empirical framework evidence |
| Validation Gate Commands | Move to supplement | Central or appendix, depending on venue |
| Scope Control For Additional Validation | Shorten in main text | Central claim-evidence alignment section |

## 3. Allocation By Figures And Tables

| Asset | Paper 4-a | Paper 4-b |
| --- | --- | --- |
| `figure1_cds_asr_pipeline_redrawn.pdf` / `f1_cds_asr_pipeline.pdf` | Main Figure 1: CDS-ASR evaluation pipeline | Background case-study figure or simplified inset |
| `figure2_evidence_ladder_redrawn.pdf` / `f2_evidence_design.pdf` | Methods or supplement: evidence layers | Main Figure 1: aggregate evidence ladder / release boundary |
| `f3_predictor_auc.pdf` | Main result figure | Case-study example only, not the main claim |
| `f4_recovery_outcomes.pdf` | Main result figure | Case-study example only |
| `f7_budget_risk_frontier.pdf` | Main or supplement result | Case-study governance tradeoff example |
| `f10_human_reviewed_atom_outcomes.pdf` | Main or supplement, if it strengthens risk-atom evidence | Case-study audit-surface evidence |
| `f8_low_wer_danger.pdf` | Supplement for Paper 4-a | Optional case-study artifact for Paper 4-b |
| `f9_risk_atom_instability_heatmap.pdf` | Supplement for Paper 4-a | Optional case-study artifact |
| `f11_risk_atom_entropy_heatmap.pdf` | Future/supplement only if privacy-safe | Future/supplement only if aggregate-safe |
| `table1_main_asr.tex` | Main table | Background case-study row |
| `table3_predictor.tex` | Main table | Case-study evidence example |
| `table4_recovery.tex` | Main table | Case-study evidence example |
| `table_s2_candidates.tex` | Supplement | Summarized as boundary-control example |
| `table_a1_fixed_budget_frontier.tex` | Supplement or main if budget tradeoff is central | Case-study governance tradeoff table |
| Claim registry table | Supplement | Main table |
| Artifact manifest | Supplement | Main or appendix table |
| Validation gate summary | Supplement | Main table |

## 4. Allocation By Claim

| Claim | Paper 4-a | Paper 4-b |
| --- | --- | --- |
| WER/CER are necessary but insufficient for high-stakes speech-to-decision systems | Main claim | Background motivating example |
| CDS-ASR evaluates whether plausible ASR alternatives change downstream action | Main claim | Case-study mechanism |
| CEIS is a decision-stability metric | Main claim | Example of bounded metric claim |
| CEIS has the strongest point AUC in the scoped audit | Main result, with uncertainty and clustered-assessment caveat | Mention only as case evidence, not as the paper's headline |
| Diagnostic zero-false-negative operating point | Main result, diagnostic only | Example of threshold-claim boundary |
| Risk-triggered policies eliminate high-risk missed and critical miss counts in aggregate replay | Main result, replay only | Example of aggregate replay auditability |
| Aggregate-only artifacts can support reviewer-visible auditability for sensitive speech AI | Supporting reproducibility claim | Main claim |
| Raw audio/transcripts/IDs/notes/logs should remain local-only | Data/ethics boundary | Main governance boundary |
| Claim-evidence alignment can be made auditable through manifests, gates, and operation records | Supplementary support | Main contribution |

## 5. Experiments And Evidence Split

Paper 4-a should centralize:

- six-model 258-row ASR comparison as transcript-model context;
- selected-300 high-stakes provenance as audit-surface construction;
- 30 reviewed rows / 90 clustered model assessments as predictor evidence;
- WER/CER/SRES/CEIS comparison against human-reviewed decision-change labels;
- aggregate recovery-policy replay under diagnostic operating points;
- row-clustered bootstrap / leave-one-row-out sensitivity as uncertainty support.

Paper 4-b should centralize:

- evidence-layer taxonomy: 258-row split, selected-300 provenance, 30 reviewed
  audit rows, 90 clustered assessments, aggregate replay;
- artifact manifest and source-boundary model;
- five-layer aggregate-only framework:
  - evidence boundary: what is public, controlled, or local-only;
  - aggregate artifact layer: tables, summaries, manifests, and validation
    outputs;
  - claim registry: claim, artifact, statistic, scope, and limitation;
  - operation records: audit process and command-level reproducibility;
  - reviewer audit protocol: what reviewers can inspect without raw transcripts.

## 6. Duplicate Publication Control

Avoid overlap by giving each paper a different primary question.

Paper 4-a primary question:

> How should ASR evaluation account for downstream decision instability when
> plausible transcript alternatives affect high-stakes actions?

Paper 4-b primary question:

> How can sensitive speech AI studies provide reviewer-visible reproducibility
> and claim-evidence auditability without releasing transcript-bearing evidence?

Do not reuse the same abstract, introduction frame, contribution list, or
discussion conclusion. The same case evidence can appear in both papers only
when it serves a different analytic role.

Use cross-references carefully:

- If Paper 4-a is submitted first, Paper 4-b should cite it as the technical
  case study if it is accepted or available as a preprint. If it is under review
  and not public, Paper 4-b should describe the case as a companion study and
  avoid relying on unpublished claims as required evidence.
- If Paper 4-b is submitted first, Paper 4-a should cite it as the
  reproducibility/governance framework if accepted or public. If not public,
  Paper 4-a should include only the concise data-availability and release
  boundary needed for its own claims.
- If simultaneous submission is planned, each cover letter should disclose the
  companion manuscript and explain the non-overlap: Paper 4-a is the ASR
  evaluation method; Paper 4-b is the aggregate-only reproducibility framework.

## 7. Shared Background Allowed In Both Papers

Short shared background is acceptable:

- high-stakes speech-to-decision workflows;
- ASR hypotheses can affect downstream routing/escalation;
- WER/CER and semantic metrics are necessary but do not directly test action
  stability;
- transcript-bearing speech evidence is sensitive and cannot always be released
  row-by-row.

Each paper should then pivot quickly:

- Paper 4-a pivots to CEIS and downstream-aware ASR evaluation.
- Paper 4-b pivots to aggregate-only reproducibility and claim-evidence
  governance.

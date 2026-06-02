# Paper 4-b Aggregate Reproducibility Codex Goal Prompt

Date: 2026-06-02

```text
You are Codex acting as a research-engineering editor for an academic LaTeX repository.

GOAL:
Create Paper 4-b as a trustworthy AI / responsible AI / reproducible evaluation manuscript focused on aggregate-only reproducibility for sensitive speech AI evaluation.

Working title:
"Reviewer-Auditable Reproducibility Without Transcript Release: An Aggregate-Only Framework for Sensitive Speech AI Evaluation"

Alternative title:
"Aggregate-Only Reproducibility for Sensitive Speech AI Evaluation"

Target venues:
Journal of Responsible Technology, AI and Ethics, AI & Society, Technology in Society, or similar responsible AI / trustworthy AI / interdisciplinary AI governance journals.

Main thesis:
Sensitive speech AI studies can be made reviewer-auditable without public release of raw audio, raw transcripts, row identifiers, reviewer notes, or transcript-bearing logs by using aggregate artifacts, artifact manifests, validation gates, operation records, claim registries, and explicit local-only boundaries.

SOURCE MATERIAL:
Use the current manuscript:

* manuscript_submission(3).tex
* manuscript_submission(4).pdf
* existing artifact manifest and aggregate validation outputs referenced in the manuscript
* existing aggregate tables and audit records

DO NOT invent new experimental results.

CORE CONTRIBUTION:
Paper 4-b must focus on:

1. A framework for aggregate-only reproducibility in sensitive speech AI evaluation.
2. Claim-evidence alignment under privacy constraints.
3. Reviewer-visible auditability without raw transcript release.
4. Artifact manifests, operation records, validation gates, and claim registries.
5. A case study using the CDS-ASR project as an example.
6. Clear separation between public aggregate evidence and local-only sensitive material.

DO NOT make CEIS the main technical contribution.
CEIS and CDS-ASR should appear as the case study, not as the primary novelty.

STRICT CLAIM BOUNDARIES:

* Do not claim full row-level reproducibility.
* Do not claim public reproducibility of raw speech evidence.
* Do not claim the framework solves all privacy risks.
* Do not claim legal compliance.
* Do not claim deployment readiness.
* Do not re-prove CEIS as the main contribution.
* Treat the CDS-ASR results as a case study for the audit framework.
* Keep raw audio, raw transcripts, selected row IDs, reviewer notes, response sheets, model hypotheses, and transcript-bearing runtime logs outside the public release boundary.
* Distinguish clearly between reviewer-auditable aggregate evidence and externally reproducible row-level evidence.

MANUSCRIPT STRUCTURE:
Create a new LaTeX manuscript directory:

paper_4b_aggregate_reproducibility/

Recommended files:

* paper_4b_aggregate_reproducibility/main.tex
* paper_4b_aggregate_reproducibility/sections/01_introduction.tex
* paper_4b_aggregate_reproducibility/sections/02_background.tex
* paper_4b_aggregate_reproducibility/sections/03_framework.tex
* paper_4b_aggregate_reproducibility/sections/04_case_study_cds_asr.tex
* paper_4b_aggregate_reproducibility/sections/05_artifact_protocol.tex
* paper_4b_aggregate_reproducibility/sections/06_reviewer_auditability.tex
* paper_4b_aggregate_reproducibility/sections/07_discussion.tex
* paper_4b_aggregate_reproducibility/sections/08_limitations_ethics.tex
* paper_4b_aggregate_reproducibility/sections/appendix.tex
* paper_4b_aggregate_reproducibility/references.bib
* paper_4b_aggregate_reproducibility/figures/
* paper_4b_aggregate_reproducibility/tables/
* paper_4b_aggregate_reproducibility/r/

SECTION DESIGN:

1. Introduction
   Focus on the reproducibility problem:
   Sensitive speech AI research often cannot release raw audio, raw transcripts, row identifiers, reviewer notes, or transcript-bearing logs.
   The core question is how reviewers can still audit empirical claims under these constraints.

2. Background
   Cover:

* Reproducibility in AI evaluation.
* Sensitive speech data.
* Privacy-preserving release boundaries.
* Claim-evidence alignment.
* Audit trails and operation records.
* Responsible AI evaluation for high-stakes systems.

3. Aggregate-Only Reproducibility Framework
   Propose a general framework with five layers:

Layer 1: Evidence boundary
Define public aggregate artifacts vs local-only sensitive evidence.

Layer 2: Aggregate artifact layer
Release summary tables, metric outputs, validation summaries, and figure inputs without transcript-bearing content.

Layer 3: Claim registry
Map every paper-facing claim to:

* artifact path
* statistic
* scope
* limitation
* privacy class
* validation status

Layer 4: Operation records and validation gates
Provide command-level or process-level audit trails without exposing sensitive content.

Layer 5: Reviewer audit protocol
Explain what reviewers can verify:

* artifact completeness
* claim-evidence alignment
* consistency checks
* metric definitions
* scope boundaries
* figure regeneration
  And explain what reviewers cannot verify:
* raw transcript content
* row-level qualitative interpretation
* hidden local-only sensitive evidence

4. Case Study: CDS-ASR
   Use the CDS-ASR project only as a case example.
   Summarize:

* 258-row ASR split
* selected-300 enriched high-stakes provenance surface
* 30 human-reviewed audit rows
* 90 clustered model assessments
* predictor comparison and policy replay as aggregate outputs
* local-only restrictions for raw audio, raw transcripts, row IDs, reviewer notes, and transcript-bearing logs

Do not make this section a full speech-evaluation paper. Refer to Paper 4-a for CDS-ASR technical details if appropriate.

5. Artifact and Claim-Evidence Protocol
   Build a concrete protocol:

* artifact_manifest.tsv
* claim_registry.tsv
* evidence_chain_consistency_summary.json
* publishable_evidence_completion_summary.json
* roadmap_completion_summary.json
* operation records
* validation gate commands
* privacy classes

6. Reviewer-Auditable Boundary
   Create a table showing:

* What is public.
* What is aggregate-only.
* What stays local.
* What reviewers can check.
* What remains trust-based or institutionally governed.

7. Discussion
   Explain implications for:

* speech AI
* medical speech
* fraud calls
* psychotherapy speech
* law-enforcement-adjacent speech data
* high-stakes conversational AI evaluation

8. Limitations and Ethics
   State:

* Aggregate-only reproducibility is weaker than row-level reproducibility.
* Reviewers cannot independently inspect raw transcript cases.
* The framework depends on honest local execution and institutional controls.
* The case study is one project, not a universal validation.
* This is not legal compliance advice.
* This does not replace IRB, data-use agreements, retention policies, encryption, or access control.

WHAT TO KEEP FROM CURRENT MANUSCRIPT:

* Aggregate-only artifact boundary.
* Artifact availability statement.
* Local-only boundary list.
* Reviewer-reproducible aggregate artifact list.
* Operation records.
* Validation gate commands.
* Claim registry.
* Evidence-chain consistency audit.
* Privacy and intended-use language.
* N-ladder / evidence unit separation.
* selected-300 enrichment boundary.

WHAT TO MINIMIZE:

* CEIS formula.
* ASR model leaderboard.
* Detailed WER/CER/SRES/CEIS comparison.
* Detailed policy replay interpretation.
* Risk atom theory.
  These belong mainly to Paper 4-a.

R FIGURE REQUIREMENT:
All charts and figures must be created by R language.
Do not create charts using Python, matplotlib, seaborn, Excel, or manual image editing.

Create R scripts under:
paper_4b_aggregate_reproducibility/r/

Required R scripts:

* build_fig1_framework_layers.R
* build_fig2_evidence_boundary.R
* build_fig3_claim_registry_flow.R
* build_fig4_artifact_audit_map.R
* build_fig5_case_study_evidence_ladder.R
* build_all_figures.R

R requirements:

* Use ggplot2, DiagrammeR, igraph, ggraph, or base R.
* Read from existing aggregate TSV/CSV/JSON artifacts only.
* Do not read raw transcripts, raw audio, selected row IDs, reviewer notes, response sheets, model hypotheses, or transcript-bearing logs.
* Output figures as PDF and PNG.
* Use deterministic output paths.
* Add captions in LaTeX that identify source artifacts or state that the figure is a conceptual framework derived from the manuscript protocol.
* Save generated figures under:
  paper_4b_aggregate_reproducibility/figures/

EXPECTED MAIN FIGURES:
Figure 1: Five-layer aggregate-only reproducibility framework.
Figure 2: Evidence boundary map showing public aggregate artifacts vs local-only sensitive evidence.
Figure 3: Claim registry flow from paper claim to artifact, statistic, scope, limitation, and validation status.
Figure 4: Reviewer auditability map showing what can be checked and what cannot be checked.
Figure 5: CDS-ASR case-study evidence ladder: 258-row ASR split, selected-300 provenance, 30 reviewed rows, 90 clustered assessments.

EXPECTED MAIN TABLES:
Table 1: Public vs aggregate-only vs local-only evidence classes.
Table 2: Claim-evidence alignment schema.
Table 3: Artifact manifest fields and purpose.
Table 4: Reviewer audit checklist.
Table 5: CDS-ASR case-study claim boundary table.

VALIDATION:
After edits:

1. Compile LaTeX.
2. Run all R figure scripts.
3. Check that every figure is generated by R.
4. Check that no raw audio, raw transcripts, row IDs, reviewer notes, response sheets, model hypotheses, or transcript-bearing logs are accessed by figure scripts.
5. Check that CEIS is presented only as the case-study method, not as the main contribution.
6. Check that the paper does not claim full row-level reproducibility.
7. Check that all claims are framed as aggregate-only reviewer-auditable evidence.

DELIVERABLES:

* New Paper 4-b LaTeX manuscript.
* R scripts for all figures.
* Generated PDF/PNG figures.
* Tables for evidence classes, claim registry schema, artifact manifest schema, reviewer checklist, and case-study claim boundaries.
* A short CHANGELOG describing what was copied, rewritten, moved to appendix, or removed.
* A submission-readiness checklist.
```

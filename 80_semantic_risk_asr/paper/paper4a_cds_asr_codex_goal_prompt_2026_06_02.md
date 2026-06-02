# Paper 4-a CDS-ASR Codex Goal Prompt

Date: 2026-06-02

```text
You are Codex acting as a research-engineering editor for an academic LaTeX repository.

GOAL:
Create Paper 4-a as a speech-technology manuscript focused on CDS-ASR and CEIS.

Working title:
"Counterfactual Decision-Stability ASR for High-Stakes Speech-Driven Decision Systems"

Target venue:
Computer Speech & Language or Speech Communication.

Main thesis:
ASR evaluation for high-stakes speech-driven decision systems should measure whether downstream decisions remain stable under plausible transcript alternatives, especially when ASR uncertainty affects decision-critical atoms such as negation, amount, actor, action, time, intent, uncertainty, and scam pattern.

SOURCE MATERIAL:
Use the current manuscript:

* manuscript_submission(3).tex
* manuscript_submission(4).pdf
* existing aggregate artifacts referenced in the manuscript
* existing R-generated figure/table inputs

DO NOT invent new experimental results.

CORE CONTRIBUTION:
Paper 4-a must focus on:

1. CDS-ASR as a downstream-aware ASR evaluation framework.
2. Risk atoms as decision-critical transcript spans.
3. Plausible ASR counterfactual variants.
4. CEIS as a decision-stability metric.
5. Evaluation against WER, CER, SRES, and human-reviewed decision-change labels.
6. Aggregate policy replay as a scoped intervention analysis.

STRICT CLAIM BOUNDARIES:

* Do not claim deployment readiness.
* Do not claim CEIS is a universally dominant classifier.
* Present CEIS as a conservative decision-stability signal.
* Treat CEIS plausibility as a bounded proxy, not a calibrated acoustic posterior.
* Treat thresholds as diagnostic operating points, not frozen deployment thresholds.
* Treat the 90 model assessments as clustered within 30 reviewed audio rows.
* Do not describe the 90 assessments as 90 independent calls.
* Treat selected-300 as an enriched high-stakes audit surface, not a prevalence-preserving sample.
* Treat human review as single-expert audit unless a second blinded reviewer has actually been added.
* Keep raw audio, raw transcripts, selected row identifiers, reviewer notes, and transcript-bearing logs outside the public release boundary.

MANUSCRIPT STRUCTURE:
Create a new LaTeX manuscript directory:

paper_4a_cds_asr/

Recommended files:

* paper_4a_cds_asr/main.tex
* paper_4a_cds_asr/sections/01_introduction.tex
* paper_4a_cds_asr/sections/02_related_work.tex
* paper_4a_cds_asr/sections/03_method.tex
* paper_4a_cds_asr/sections/04_experimental_setup.tex
* paper_4a_cds_asr/sections/05_results.tex
* paper_4a_cds_asr/sections/06_discussion.tex
* paper_4a_cds_asr/sections/07_limitations_ethics.tex
* paper_4a_cds_asr/sections/appendix.tex
* paper_4a_cds_asr/references.bib
* paper_4a_cds_asr/figures/
* paper_4a_cds_asr/tables/
* paper_4a_cds_asr/r/

SECTION DESIGN:

1. Introduction
   Focus on the speech-system problem:
   Low WER/CER can still be operationally unsafe when ASR uncertainty lands on decision-critical atoms.
   Frame anti-fraud triage as the motivating high-stakes speech-driven decision system.
   Make the contribution speech-centered, not governance-centered.

2. Related Work
   Include:

* WER/CER and transcript-centered ASR evaluation.
* Semantic and downstream-aware ASR metrics.
* Task-oriented ASR evaluation.
* ASR correction and confidence-aware repair.
* Selective prediction, reject option, and abstention as background for conservative action.

3. Method
   Make this the strongest section.
   Include:

* Problem formulation.
* CDS-ASR pipeline.
* Risk atom schema.
* Counterfactual variant contract.
* Downstream decision function.
* CEIS formula.
* CEIS scale discipline.
* Recovery policy contract.

Clarify:
CEIS(x) is a bounded decision-instability score over plausible variants.
The plausibility term is a bounded proxy.
RiskAtomWeight and DecisionDistance must be tabulated or referenced from the versioned config.

4. Experimental Setup
   Include:

* 258-row ASR model-comparison split.
* selected-300 enriched high-stakes provenance surface.
* 30 human-reviewed audit rows.
* 90 model-row assessments clustered within 30 rows.
* Baselines: WER, CER, SRES.
* Outcome: human-reviewed decision-change labels.
* Policy replay setup.
* Row-clustered uncertainty and leave-one-row-out sensitivity where already available.

5. Results
   Central results:

* Main ASR benchmark table on 258-row split.
* Predictor comparison: WER, CER, SRES, CEIS.
* Row-clustered confidence intervals.
* CEIS zero-FN diagnostic operating point, with softened wording.
* Policy replay showing severe miss reduction.
* Fixed-budget frontier.
* Risk atom analysis.

6. Discussion
   Emphasize:

* WER/CER remain necessary.
* Speech evaluation needs a decision-stability layer in high-stakes workflows.
* CEIS is complementary to transcript accuracy and semantic metrics.
* Better ASR does not remove the need for downstream decision-stability analysis.

7. Limitations and Ethics
   Keep concise.
   State:

* Small reviewed audit: 30 rows / 90 clustered model assessments.
* Single-expert audit.
* Selected-300 enrichment.
* Diagnostic thresholds.
* Aggregate-only boundary.
* No live deployment trial.
* No population prevalence claim.
* Intended use: audit, review prioritization, conservative escalation, and abstention only.

WHAT TO MOVE TO APPENDIX:

* Long artifact availability list.
* Claim registry.
* Candidate lane details.
* Operation records.
* Validation gate commands.
* Local-only boundary details.

WHAT TO REMOVE OR MINIMIZE:

* Long NIST AI RMF / EU AI Act governance framing.
* Long privacy-governance discussion.
* Full aggregate-only reproducibility framework.
  These belong mainly to Paper 4-b.

R FIGURE REQUIREMENT:
All charts and figures must be created by R language.
Do not create charts using Python, matplotlib, seaborn, Excel, or manual image editing.

Create R scripts under:
paper_4a_cds_asr/r/

Required R scripts:

* build_fig1_pipeline.R
* build_fig2_evidence_ladder.R
* build_fig3_predictor_auc.R
* build_fig4_policy_replay.R
* build_fig5_fixed_budget_frontier.R
* build_fig6_risk_atom_review.R
* build_all_figures.R

R requirements:

* Use ggplot2 or base R.
* Read from existing aggregate TSV/CSV/JSON artifacts only.
* Do not read raw transcripts, raw audio, selected row IDs, reviewer notes, or transcript-bearing logs.
* Output figures as PDF and PNG.
* Use deterministic ordering and reproducible output paths.
* Add captions in LaTeX that identify the source artifact for each figure.
* Save generated figures under:
  paper_4a_cds_asr/figures/

EXPECTED MAIN FIGURES:
Figure 1: CDS-ASR decision-stability pipeline.
Figure 2: Evidence ladder showing 258 ASR rows, selected-300 provenance, 30 reviewed rows, and 90 clustered model assessments.
Figure 3: Predictor comparison for WER, CER, SRES, CEIS with row-clustered intervals.
Figure 4: Aggregate policy replay for no recovery, SRES recovery, CEIS conservative action, and CEIS ensemble arbitration.
Figure 5: Fixed-budget conservative replay frontier.
Figure 6: Human-reviewed decision-change evidence by risk atom.

EXPECTED MAIN TABLES:
Table 1: Main ASR benchmark on 258-row split.
Table 2: Predictor performance against human-reviewed decision-change labels.
Table 3: Aggregate policy replay under human-reviewed selected-300 labels.
Optional appendix table: Fixed-budget replay frontier.

ADDITIONAL ANALYSIS TASK:
If aggregate-safe inputs exist, implement CEIS ablation tables and R figures:

* full CEIS
* no plausibility
* uniform atom weight
* binary decision flip
* max vs top-k aggregation
* CEIS by atom class

If aggregate-safe inputs do not exist, do not fabricate ablation results. Instead:

* create a TODO file:
  paper_4a_cds_asr/TODO_required_before_submission.md
* list the missing aggregate inputs needed for each ablation.
* state that these analyses are recommended before submission.

VALIDATION:
After edits:

1. Compile LaTeX.
2. Run all R figure scripts.
3. Check that no raw audio, raw transcripts, row IDs, reviewer notes, or transcript-bearing logs are referenced by the paper-facing outputs.
4. Check that every empirical claim points to an aggregate artifact.
5. Check that every figure/table can be regenerated by R.
6. Check that the manuscript never treats 90 model assessments as independent calls.
7. Check that CEIS claims are scoped and not overstated.

DELIVERABLES:

* New Paper 4-a LaTeX manuscript.
* R scripts for all figures.
* Generated PDF/PNG figures.
* A short CHANGELOG describing what was copied, rewritten, moved to appendix, or removed.
* A submission-readiness checklist.
```

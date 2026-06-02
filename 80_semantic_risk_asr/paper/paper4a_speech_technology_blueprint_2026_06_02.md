# Paper 4-a Blueprint: Speech Technology Paper

Date: 2026-06-02

Working role:

> A downstream-aware ASR evaluation paper for Computer Speech & Language,
> Speech Communication, or related speech technology venues.

## 1. Paper Design

### Tentative Title Options

1. When Low WER Becomes Dangerous: Counterfactual Decision-Stability ASR for High-Stakes Speech-Driven Decision Systems
2. Counterfactual Decision-Stability ASR for High-Stakes Speech-Driven Decision Systems
3. Counterfactual Decision-Stability Evaluation for High-Stakes Speech-to-Decision ASR
4. Decision-Stability ASR: Evaluating Plausible Transcript Alternatives in High-Stakes Speech Systems
5. Beyond Transcript Similarity: Counterfactual Decision-Stability Metrics for ASR

Recommended title:

> Counterfactual Decision-Stability ASR for High-Stakes Speech-Driven Decision Systems

The current full title remains viable if the journal accepts a more
attention-led title:

> When Low WER Becomes Dangerous: Counterfactual Decision-Stability ASR for High-Stakes Speech-Driven Decision Systems

### One-Sentence Thesis

Transcript similarity metrics such as WER and CER remain necessary for ASR
evaluation, but high-stakes speech-driven decision systems also need a
decision-stability test that measures whether plausible ASR alternatives around
decision-critical spoken atoms would change downstream action.

### Target Journal Positioning

Primary fit:

- Computer Speech & Language;
- Speech Communication;
- speech/spoken-language evaluation venues.

Positioning statement:

> This is a speech recognition and spoken-language system evaluation paper. It
> contributes CDS-ASR as a downstream-aware evaluation framework for ASR
> hypotheses in speech-to-decision workflows.

Avoid positioning it as a general AI governance paper. Governance and privacy
remain visible, but they support the speech evaluation contribution.

### Abstract Structure

1. Speech-to-decision problem: ASR hypotheses become operational signals.
2. Evaluation gap: WER/CER and semantic similarity do not directly test action
   stability.
3. Method: CDS-ASR, risk atoms, plausible ASR alternatives, CEIS.
4. Evidence: 258-row ASR comparison, selected-300 provenance, 30 reviewed rows,
   90 clustered model assessments, aggregate policy replay.
5. Result boundary: CEIS as decision-stability evidence; thresholds as
   diagnostic operating points; policy replay as retrospective aggregate replay.
6. Implication: decision-stability evaluation complements transcript accuracy
   and semantic ASR metrics.

### Main Contributions

1. Defines speech-to-decision ASR evaluation as a consequence-centered extension
   of transcript similarity evaluation.
2. Introduces risk atoms as decision-critical spoken units for ASR evaluation.
3. Introduces CDS-ASR and CEIS for measuring downstream decision instability
   under plausible ASR alternatives.
4. Evaluates WER, CER, SRES, and CEIS against human-reviewed decision-change
   labels within a scoped selected-300 audit surface.
5. Reports aggregate policy replay showing how risk-triggered recovery and
   conservative action affect severe-miss outcomes under the audit boundary.
6. Provides aggregate reproducibility sufficient for reviewer inspection while
   preserving sensitive transcript-bearing evidence.

## 2. Proposed 250-Word Abstract Draft

Speech recognition outputs increasingly serve as operational inputs for
routing, escalation, compliance review, and triage. In these speech-to-decision
systems, a transcript can remain close to a reference under word or character
error rate while a plausible alternative around a decision-critical spoken
detail changes the downstream action. This paper introduces Counterfactual
Decision-Stability ASR (CDS-ASR), an evaluation framework for measuring whether
ASR hypotheses remain decision-stable under acoustically and semantically
plausible transcript alternatives. CDS-ASR identifies risk atoms such as
negation, amount, actor, action, time, intent, uncertainty, and scam pattern,
constructs bounded ASR alternatives around those atoms, and scores downstream
instability with the Counterfactual Escalation Instability Score (CEIS).

We evaluate CDS-ASR in a high-stakes anti-fraud speech setting using a scoped
evidence chain: a six-model 258-row ASR comparison for transcript-model
context, selected-300 high-stakes provenance outputs for audit-surface
construction, and 30 human-reviewed audit rows yielding 90 clustered model
assessments for decision-change evaluation. CEIS is compared with WER, CER, and
the semantic-risk baseline SRES against human-reviewed decision-change labels,
and aggregate policy replay evaluates recovery and conservative-action
policies. The results support CEIS as a decision-stability signal under this
bounded audit design, while SRES remains a strong semantic-risk baseline.
Diagnostic operating points and replay policies are reported as retrospective
evidence, not deployment thresholds. CDS-ASR therefore complements transcript
accuracy and semantic ASR metrics by testing whether plausible ASR alternatives
would change high-stakes speech-driven actions.

## 3. Recommended Section Outline

1. Introduction
   - speech-to-decision workflows;
   - WER/CER and semantic metrics as necessary foundations;
   - remaining decision-stability gap;
   - CDS-ASR thesis.

2. Related Work
   - ASR accuracy metrics and Chinese ASR reporting;
   - semantic and downstream-aware ASR evaluation;
   - ASR correction, confidence filtering, selective prediction, abstention;
   - high-stakes speech system evaluation.

3. Problem Formulation
   - speech-to-decision pipeline;
   - downstream action space;
   - unsafe downrouting, high-risk missed, critical miss;
   - scoped anti-fraud triage policy.

4. CDS-ASR Method
   - risk atom schema;
   - plausible ASR alternatives;
   - SRES baseline;
   - CEIS metric;
   - recovery and conservative-action policies.

5. Evidence Design
   - 258-row ASR split;
   - selected-300 provenance outputs;
   - 30 reviewed rows / 90 clustered model assessments;
   - aggregate-only evidence boundary;
   - uncertainty handling.

6. Results
   - ASR comparison context;
   - predictor comparison: WER/CER/SRES/CEIS;
   - diagnostic operating points;
   - aggregate policy replay;
   - fixed-budget sensitivity and leave-one-row-out support.

7. Discussion
   - ASR evaluation implications;
   - CEIS as decision-stability metric, not calibrated acoustic probability;
   - relation between ASR model improvement and downstream instability;
   - privacy-preserving aggregate reproducibility as support.

8. Limitations
   - selected-300 enrichment;
   - 30 reviewed rows / 90 clustered model assessments;
   - single-expert audit;
   - diagnostic thresholds only;
   - variant plausibility as bounded proxy;
   - no deployment trial.

9. Data Availability, Ethics, and Intended Use
   - concise statement;
   - raw audio/transcripts/IDs/notes/logs excluded;
   - aggregate artifacts included.

## 4. What To Keep From Current Manuscript

Keep and rewrite:

- speech-to-decision introduction;
- WER/CER, semantic metric, correction, and selective-prediction related work;
- risk atom schema;
- plausible ASR alternative contract;
- SRES and CEIS definitions;
- recovery policy definitions;
- 258-row, selected-300, 30-row/90-assessment evidence design;
- predictor and recovery results;
- concise ethics/privacy/data boundary;
- limitations tied to ASR evaluation.

## 5. What To Remove Or Move To Appendix

Move to appendix or companion Paper 4-b:

- full claim registry;
- full artifact manifest discussion;
- validation gate commands;
- operation-record details;
- long privacy-class taxonomy;
- long release-boundary rationale;
- detailed governance framework language.

Keep only a concise data/reproducibility paragraph in Paper 4-a.

## 6. Central Experiments

Main:

- six-model 258-row ASR comparison;
- WER/CER/SRES/CEIS predictor comparison against human-reviewed decision-change
  labels;
- diagnostic operating point analysis;
- aggregate policy replay;
- row-clustered bootstrap and leave-one-row-out sensitivity.

Supplement:

- selected-300 provenance details;
- candidate ASR/Gemma lane boundary;
- fixed-budget recovery frontier;
- counterfactual variant coverage summary.

## 7. Strongly Recommended Additional Analyses

Do not invent results. These are recommended if already available or feasible
before submission:

1. Report row-clustered uncertainty intervals next to predictor and recovery
   claims.
2. Keep leave-one-row-out sensitivity visible for the 30-row audit.
3. Add a calibration-style warning that CEIS is not an acoustic posterior.
4. Prioritize CEIS ablation. This is the most likely speech-reviewer request
   because the paper's method contribution depends on the CEIS construction.
   Recommended ablations:
   - uniform-weight CEIS;
   - no-plausibility ablation;
   - binary-decision-flip ablation;
   - maximum versus top-k aggregation;
   - CEIS by atom class.
5. Add an aggregate variant-coverage summary, but keep generated variant text
   private.
6. Add a compact confusion/risk-atom summary only if it can be made
   transcript-free.

If these ablations are not completed before submission, state them as planned
validation extensions and keep CEIS claims bounded to the current reviewed
audit.

## 8. Claims To Soften

| Strong wording to avoid | Journal-ready wording |
| --- | --- |
| CEIS is superior to all metrics | CEIS provides the strongest decision-change point AUC in this scoped audit |
| CEIS predicts real-world harm | CEIS measures decision instability under the declared audit policy |
| Threshold eliminates risk | The diagnostic operating point eliminates high-risk missed and critical miss counts in aggregate replay |
| 90 assessments are 90 calls | 90 clustered model assessments from 30 reviewed rows |
| selected-300 estimates prevalence | selected-300 is an enriched high-stakes audit surface |
| plausible variants are calibrated acoustic alternatives | plausible variants are bounded ASR alternatives used as a proxy for decision-stability testing |
| ready for deployment | supports future validation of conservative triage and abstention policies |

## 9. Limitations To State Clearly

- 30 human-reviewed rows and 90 clustered model assessments.
- Single-expert audit; no inter-annotator agreement claim.
- selected-300 is enriched, not prevalence-preserving.
- CEIS plausibility is bounded and not a calibrated acoustic posterior.
- Thresholds are diagnostic operating points, not deployment thresholds.
- Aggregate replay is retrospective, not a live deployment trial.
- Raw audio, raw transcripts, row identifiers, reviewer notes, and
  transcript-bearing logs remain outside the release boundary.

## 10. Figure And Table Plan

| Item | Role |
| --- | --- |
| Figure 1: CDS-ASR pipeline | Main method figure |
| Figure 2: evidence design / evidence ladder | Evidence design figure |
| Figure 3: predictor comparison / AUC | Main result |
| Figure 4: recovery outcomes | Main result |
| Figure 5: fixed-budget frontier | Main or supplement |
| Table 1: ASR comparison | Main context table |
| Table 2: risk atom schema | New or method table |
| Table 3: predictor comparison | Main result table |
| Table 4: recovery policy replay | Main result table |
| Supplement Table S1: selected-300 provenance | Supplement |
| Supplement Table S2: candidate lane | Supplement |
| Supplement Table S3: leave-one-row-out / clustered CI | Supplement |

## 11. Claim Boundary Table

| Claim | Evidence | Boundary |
| --- | --- | --- |
| WER/CER are necessary but insufficient for high-stakes speech-to-decision evaluation | 258-row ASR context plus reviewed decision-change audit | Does not reject WER/CER; adds downstream test |
| CEIS supports decision-stability evaluation | 30 rows / 90 clustered model assessments | Scoped audit; not population-level deployment evidence |
| Risk-triggered policies reduce severe misses in replay | aggregate policy replay | Retrospective replay, not deployed threshold |
| Partial encoder is strongest current ASR hypothesis generator | 258-row split | Model-comparison context only |
| selected-300 supports high-stakes audit | selected-300 provenance | Enriched audit surface, not prevalence-preserving sample |

## 12. Reviewer Risk Table

| Reviewer risk | Response |
| --- | --- |
| "This is governance, not speech technology." | Lead with ASR hypotheses, spoken risk atoms, WER/CER/SRES/CEIS, and speech-to-decision evaluation. |
| "CEIS is overclaimed." | Define CEIS as decision-stability metric and bounded proxy; avoid acoustic-probability language. |
| "Where is the CEIS ablation?" | Add the CEIS ablation suite before submission, or state it clearly as the next validation layer and keep the current CEIS claim scoped. |
| "Small human audit." | State 30 reviewed rows / 90 clustered assessments and include sensitivity/clustered uncertainty. |
| "selected-300 is biased." | Present it as enriched high-stakes audit surface, not prevalence sample. |
| "No raw transcripts released." | Provide aggregate artifacts, manifests, and validation gates; state privacy boundary. |
| "Thresholds are tuned on audit data." | Call them diagnostic operating points and future validation targets. |

## 13. Minimum Submission Checklist

- Title page with author and affiliation metadata.
- 250-word-or-less abstract.
- 1-7 keywords.
- Highlights if required by journal.
- Numeric or journal-required reference style.
- Main manuscript PDF and source.
- Figure PDFs and captions.
- Data availability statement.
- Competing interest, funding, CRediT, acknowledgements, generative-AI
  declaration if applicable.
- Citation reciprocity check.
- Transcript-bearing leak check.
- Final statement that raw audio, transcripts, row IDs, reviewer notes, and
  transcript-bearing logs are not released.

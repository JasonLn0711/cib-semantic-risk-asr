# CSL First-Principle Pressure Test Round 2

Date: 2026-06-03

Status: recorded for claim-endpoint hardening, experiment matrix design, and
final CSL red-line definition.

## Round 2 Frame

Round 1 correctly narrowed the manuscript direction to CEIS as the main
innovation, with CDS-ASR, risk atoms, and aggregate-only governance serving as
supporting layers. Counterfactual variants are positioned as a tool assumption;
selected-300 is an enriched audit surface; final CSL still requires full-audit
regeneration, CEIS ablations, selection-exclusion sensitivity, and
generator-only / variant-count controls.

The remaining risk is that calibrated claim downgrades have not yet been
translated into executable, testable, reviewer-defensible submission structure.
Round 2 therefore pressure-tests whether each claim can survive the planned
experiments.

## Round 2 Questions And Answers

### 1. Primary Endpoint

Primary endpoint: **B. severe-miss remaining at fixed budget**, fixed at
pre-specified early budgets such as 10% and 20% observed trigger budget. This
best matches the current evidence: CEIS ties SRES at the diagnostic 0.3889
budget, but appears stronger on early-budget severe-miss capture. AUC becomes
secondary predictor evidence. Zero FN becomes a diagnostic operating-point
illustration. Policy replay severe-miss elimination becomes secondary sanity
check. Delta over SRES under row-clustered CI becomes inferential support, not
the endpoint.

### 2. Revised Paper Claim

CEIS improves **severe-miss remaining at pre-specified 10-20% fixed trigger
budgets on the scoped selected high-risk audit surface**, while SRES remains
stronger for **best-threshold F1 and precision against human-reviewed
decision-change labels**.

This claim maps directly to a fixed-budget frontier plus the predictor table.
It avoids claiming that CEIS universally beats SRES.

### 3. Strategy For 30/90 Main Results

Strategy: **A. rerun all main tables and figures on 300/900 and remove 30/90
from main claims**.

Thirty-row / 90-assessment outputs can remain internal development notes or
appendix pilot evidence only if explicitly labeled. They cannot support main
CSL claims.

Required rerun list:

- Figure 2 evidence ladder.
- Table 2 predictor performance.
- Figure 3 AUC plot.
- Table 3 policy replay.
- Figure 4 residual risk.
- Figure 5 fixed-budget frontier.
- Figure 6 risk-atom decision-change evidence.
- Appendix Table A1 fixed-budget frontier.
- Claim registry predictor and replay rows.
- Low-WER/CER danger table.

Table 1 with the 258-row ASR benchmark can remain because it belongs to the
ASR benchmark layer rather than selected-300 human-risk evidence.

### 4. CEIS Incremental Value Tests

Run three incremental tests:

1. `Delta AUC = AUC(CEIS) - AUC(SRES)` with row-clustered bootstrap CI, using
   audio row as the resampling unit.
2. Paired row-clustered bootstrap. DeLong-style sensitivity can be appendix
   only because ordinary DeLong does not naturally handle clustered
   model-assessment units.
3. Residual gain after SRES: `label ~ SRES + CEIS`, reporting CEIS coefficient,
   bootstrap CI, and delta AUC or delta log-loss.

If residual gain is unstable, the paper claim should move toward
early-budget ranking rather than general predictor superiority.

### 5. CEIS If It Wins Only At Low Budget

This is sufficient if stated narrowly:

> CEIS improves early-budget ranking of severe missed-escalation cases on the
> scoped audit surface.

This claim is operationally meaningful because anti-fraud triage cannot
escalate every case. Top 10-20% trigger ordering is closer to the intended use
than a full threshold sweep. If SRES and CEIS tie at 38.9% diagnostic budget,
the paper should state the tie directly.

### 6. Severe-Miss Positive Count

The current 90-assessment replay has 7 severe misses. If distribution scaled
linearly, 900 assessments might contain roughly 70 severe positives, but this
is only intuition and must not be written as expected evidence. A conservative
expectation is 25-70 model-level severe positives and perhaps 10-30 unique
row-level positives. If full 300/900 regeneration still yields fewer than 20
severe positives, severe-miss remaining should not be the only primary result.
The fallback primary should become decision-change AUC, risk-coverage AUC, or
atom-level analysis, with severe-miss frontier kept descriptive.

### 7. Controlling Variant-Count Advantage

Report per-row variant counts: mean, median, IQR, maximum, and stratification
by label, selection stratum, and atom family.

Required controls:

- Variant-count-only predictor.
- Top-k capped CEIS.
- Source-balanced max.

Appendix negative control:

- Max over shuffled risk atoms.

Source-balanced max is especially important because model disagreement,
Mandarin phonetic ambiguity, domain-slot alternatives, and runtime signals can
produce unequal variant volumes. If variant-count-only approaches CEIS
performance, CEIS must be described as a generator-ranking heuristic.

### 8. Variant Generator Inputs And Blinding

Final protocol must be blind generation.

Allowed inputs:

- Audio-derived runtime / quality signals.
- ASR hypotheses.
- Model disagreement.
- Mandarin phonetic ambiguity rules.
- Domain-slot alternative rules.
- Locale / normalization outputs.

Forbidden inputs:

- Reference transcript.
- Human audit label.
- Expected safe action.
- CEIS/SRES selection stratum.
- Manual reviewer notes.
- Policy replay outcome.

If any existing generator step used reference or human labels, the generation
must be rerun blind. If rerun is impossible, CEIS must be described as a
post-hoc audit metric.

### 9. Plausibility Proxy Reproducibility

Final CEIS must be deterministic. Plausibility weights should come from a
frozen rule/config rather than evaluation-label tuning. If data-estimated
weights are used, they must come from an independent development split.

Each plausibility score should be generated from fixed components, such as:

- Model-disagreement support.
- Mandarin phonetic support.
- Domain-slot validity.
- Runtime support.

Scores are bounded to `[0,1]`. The system needs a `plausibility_min` threshold
and reject reasons. Given the same input, CEIS config, tokenizer, and
normalization policy, the same variants and scores should be reproduced. The
paper should continue to state that plausibility is a bounded proxy rather than
a calibrated acoustic posterior.

### 10. Dependency Between `f` And Risk Atom Extraction

There is likely partial dependency. Final paper should separate two layers:
risk-atom extraction provides CEIS risk handles; policy contract `f` maps a
transcript into a declared action. Even if underlying features overlap, the two
layers must be ablated independently.

Required pressure tests:

- Human-annotated atoms versus automatic atoms.
- Policy-only distance without atom weights.
- Drop-one-atom-family ablation.

Additional consistency table:

- Manual `f` labels versus rule-based `f` outputs.

Appendix negative control:

- Randomized atom weights.

If CEIS only works inside a closed loop of automatic extractor plus rule-based
`f`, reviewers can argue it amplifies one rule system.

### 11. Human Reviewer Gold Target

Gold target: **C. original ASR action versus expected safe action**.

The expected safe action must be grounded in reference/audio local context.
The reviewer does not compare CEIS-generated variants. Instead, the reviewer
judges whether an ASR hypothesis would move triage action away from the row's
expected safe action:

`decision_change_yes = 1[f(ASR hypothesis) != expected_safe_action]`

The label can also record unsafe direction. Reference/audio context can be
used to establish expected safe action, but cannot be used as variant generator
input.

### 12. Reviewer Disagreement

Primary label: **E. adjudicated label**.

High kappa makes adjudication feasible. Strict consensus may be too
conservative when positives are sparse; liberal union can inflate positives
through uncertain cases. Main text should use adjudicated labels, while
appendix reports strict consensus and liberal union sensitivity. If all three
directions agree, human-label robustness is much stronger.

### 13. Selection-Exclusion Sensitivity Pass/Fail

Pass/fail should follow the primary endpoint.

After excluding CEIS-selected rows, pass means:

- At 10% or 20% fixed budget, CEIS severe-miss remaining is less than or equal
  to SRES severe-miss remaining.
- CEIS residual gain after SRES does not reverse direction.

Secondary pass:

- Delta AUC direction remains positive.

FN=0 is not required. If severe positive count falls below 5, do not declare
pass/fail; mark the sensitivity as underpowered. If early-budget capture,
delta AUC, and residual gain reverse in at least two of three checks, treat the
sensitivity as failed.

### 14. SRES + CEIS Combined Baseline

Add combined baselines:

- SRES alone.
- CEIS alone.
- `max(zSRES, zCEIS)`.
- Rank-fusion SRES + CEIS.
- Two-stage: SRES screen, then CEIS tie-break.

Logistic fusion may be reported, but only as diagnostic unless there is an
independent development split. If combined baseline beats CEIS alone, write the
contribution as: CEIS supplies an incremental decision-stability signal
complementary to SRES. The goal is to prove non-redundancy, not replacement.

### 15. Linguistic Contribution As Evidence

Add a full 300/900 risk-atom linguistic evidence table. It should include:

- Atom type.
- Reviewed row count.
- Model-assessment count.
- Variant count.
- Decision-change rate.
- Severe-miss rate.
- CEIS median rank.
- SRES median rank.
- Human criticality rate.
- Mandarin-specific source share.

Mandarin-specific source share should include homophone / near-homophone,
numeral / amount, segmentation / tokenization, locale violation, model
disagreement, and domain-slot substitution. If current Figure 6 remains
30-row, it can only be appendix pilot evidence. The full 300/900 table is the
CSL speech/language contribution backbone.

### 16. Mandarin / Taiwan Synthetic Minimal Pairs

Provide 8-12 synthetic minimal pairs. Each pair should report atom, Mandarin
ambiguity type, `f(x)`, `f(v)`, DecisionDistance, Plausibility, RiskAtomWeight,
and CEIS.

Example pairs:

| Pair | Atom | Ambiguity type | Effect |
| --- | --- | --- | --- |
| 沒有匯款 / 有匯款 | negation + action | negation deletion | no escalation to priority review |
| 三萬 / 三十萬 | amount | Mandarin numeral scale | review to critical escalation |
| 昨天 / 今天 / 下週 | time | temporal slot | routine to urgent review |
| 客服 / 警察 / 銀行 | actor | role substitution | lower risk to scam-pattern review |
| 取消分期 / 繼續分期 | action + intent | domain phrase confusion | inquiry to active scam |
| 不確定 / 確定 | uncertainty | epistemic stance | manual-review threshold change |

These examples explain mechanism, not prevalence. They compensate for
aggregate-only release boundaries.

### 17. Title Decision

Choose **B. change the title**. The main Chinese surface metric is
`cer_zh_micro`, while WER is supplemental through `wer_zh_jieba_micro`. A title
centered on WER undermines the Mandarin metric discipline.

Suggested title:

> Counterfactual Decision Stability for High-Stakes Mandarin ASR

Possible subtitle:

> Evaluating Safety-Relevant Instability Beyond Transcript Accuracy

Low-WER / low-CER danger can remain secondary or appendix evidence. Do not let
the entire paper depend on a low-WER denominator claim.

### 18. Confidence-Only Baseline

Move confidence-only to appendix as a negative engineering result. Do not keep
it as an active main baseline while calibrated confidence is unavailable and no
triggers are produced. Related work can still discuss confidence-aware
correction.

If replacing it, use a model-disagreement-only selective escalation baseline.
Runtime-signal baseline should only be added if stable reproducible features
exist, such as model-disagreement count, locale-violation flag,
decode/runtime anomaly, length anomaly, or VAD/no-speech proxy.

### 19. Policy Replay Intervention Semantics

Define five policies deterministically:

| Policy | Deterministic intervention |
| --- | --- |
| No recovery | output `f(h)` for ASR hypothesis `h` |
| Confidence-only | if calibrated confidence exists and `< tau_conf`, output `conservative_machine_action`; otherwise output `f(h)`; current artifact has no calibrated trigger |
| SRES-triggered recovery | if `SRES(h) >= tau_SRES`, output `conservative_machine_action`; otherwise output `f(h)` |
| CEIS-triggered conservative action | if `CEIS(h) >= tau_CEIS`, output `conservative_machine_action`; otherwise output `f(h)` |
| CEIS ensemble arbitration | compute CEIS/action interval across eligible hypotheses; if interval crosses escalation boundary, output `abstain/conservative_machine_action`; otherwise output consensus `f(h*)` |

`conservative_machine_action` does not replace the transcript. It means
stopping automatic downrouting, raising review priority, or requiring human
confirmation.

### 20. Residual Unsafe Downrouting 24

Residual unsafe downrouting breakdown is blocking for any unsafe-downrouting
governance claim. Main text should include an aggregate summary table; appendix
can contain finer breakdown. Raw rows remain local.

Fields:

- Residual unsafe category.
- Atom type.
- Expected safe action.
- Actual replay action.
- CEIS rank bucket.
- SRES rank bucket.
- Variant source.
- Whether severe.

Without the breakdown, the main paper can claim severe missed-escalation
reduction only, not broad unsafe-downrouting governance.

### 21. Operational Vocabulary

Accept the vocabulary rule: title may contain one strong phrase, but abstract,
method, and results should use operational terms.

| Term | Use |
| --- | --- |
| safety-relevant decision instability | abstract/results primary term |
| severe missed-escalation | primary endpoint |
| policy-conditioned instability | method/formal definition |
| unsafe downrouting | label taxonomy category |
| dangerous | title or introduction only, with operational definition |
| actual harm | avoid, except to say the study does not measure actual harm |

### 22. Aggregate-Only Reviewer Package Minimum

Provide eight items:

1. Artifact manifest with SHA256.
2. Full 300/900 aggregate predictor, replay, and ablation tables.
3. Row-cluster bootstrap scripts.
4. CEIS config JSON.
5. Downstream decision contract.
6. Synthetic scoring demo.
7. Source-specific generator coverage table.
8. Aggregate variant reject reasons.

Normalization/tokenizer policy should be included in the manifest or scoring
demo package. The current aggregate package already has manifests, metric
audits, agreement summaries, predictor/recovery tables, claim registry, and
operation records; final CSL needs synthetic demo and generator audit to make
the mechanism inspectable.

### 23. Statistical Inference Subsection

Add an independent subsection:

> Statistical inference and operating-point selection

It should state:

- Unit is audio row.
- Model assessments are clustered within row.
- Primary CI is row-clustered bootstrap.
- AUC, F1, FN, and budget are estimated under row clustering.
- Thresholds are diagnostic unless selected on a development split.
- Positive-label counts are reported.
- Fixed-budget replay uses pre-specified budgets.
- Selection-exclusion sensitivity is reported.

This makes the statistical design proactive rather than scattered defensively
across method and limitations.

### 24. Governance-To-Speech/Language Trade

Main-text governance maximum:

- Two paragraphs: one privacy/release-boundary paragraph and one intended-use
  paragraph.

Artifact availability:

- Appendix, maximum two pages.

Move claim registry, operation records, and candidate-lane details to appendix.
Use the saved space for CEIS ablations, SRES+CEIS incremental analysis,
Mandarin synthetic minimal pairs, risk-atom linguistic table, and
variant-source coverage. CSL reviewers should remember the speech/language
mechanism rather than the governance workflow.

### 25. Final Red Lines

Five hard gates before CSL submission:

1. Main-text 30/90 predictor/replay/figure results are converted to full
   300/900, or 30/90 is explicitly labeled pilot and removed from main claims.
2. CEIS ablation suite is complete: full, without plausibility, without atom
   weights, binary atom, and policy-distance-only.
3. CEIS versus SRES incremental analysis is complete: delta AUC CI, paired
   row-cluster bootstrap, and residual gain after SRES.
4. Selection-exclusion sensitivity is complete: exclude CEIS-selected,
   exclude CEIS/SRES-family selected, and reweighting / stratum sensitivity.
5. Variant-count/source coverage audit is complete: variant-count distribution,
   variant-count-only baseline, top-k cap, source-balanced max, and
   source-specific coverage.

Conditional red line:

- Residual unsafe downrouting breakdown is mandatory if the paper keeps any
  unsafe-downrouting governance claim. If it is not done, the main claim must
  narrow to severe missed-escalation reduction.

## Round 2 Derived Claim Structure

- Primary endpoint: severe-miss remaining at pre-specified 10-20% fixed trigger
  budgets.
- Primary claim: CEIS improves early-budget severe missed-escalation ranking on
  the scoped selected high-risk audit surface.
- Strongest baseline: SRES.
- Required interpretation: CEIS is complementary to SRES, not a universal
  replacement.
- Required final N: 258 benchmark rows, selected-300 provenance, 300 reviewed
  rows, and 900 model-level assessments per reviewer.
- Required title direction: move away from WER-centered title toward
  counterfactual decision stability for high-stakes Mandarin ASR.

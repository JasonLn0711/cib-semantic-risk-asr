# CSL First-Principle Pressure Test Round 3

Date: 2026-06-03

Status: recorded for submission-claim freeze, experiment matrix freeze, and
pre-final-execution planning.

## Round 3 Frame

After Round 2, the paper has a publishable skeleton:

- CEIS's primary empirical battlefield is severe missed-escalation ranking at
  pre-specified 10-20% fixed trigger budgets.
- SRES remains the strongest baseline.
- Thirty-row / 90-assessment results leave the main claims.
- CSL contribution moves from governance back to speech/language mechanism.

The remaining risk is no longer lack of ideas. It is whether the primary
endpoint, statistical unit, variant generator, linguistic evidence, and claim
wording are frozen tightly enough to support a final execution plan.

## Publishable Claim Set

### Claim 1: Method Claim

CEIS is a counterfactual decision-stability metric for high-stakes ASR. It
takes the maximum decision instability over plausible transcript variants and
combines plausibility, risk atom weight, and DecisionDistance in one scoring
functional. This claim is viable because the manuscript has an explicit
formula, bounded plausibility proxy, fixed downstream decision function `f`,
and ablation design for atom and decision-distance components.

Publishable wording:

> We introduce CEIS, a counterfactual decision-stability metric for high-stakes
> ASR that scores whether plausible transcript alternatives crossing
> decision-critical atoms would change a declared downstream triage action.

CEIS should be described as a scoped companion metric, not a general ASR
metric.

### Claim 2: Primary Empirical Claim

Publishable wording:

> On the selected high-risk Mandarin anti-fraud audit surface, CEIS improves
> early-budget ranking of severe missed-escalation cases at pre-specified
> 10-20% trigger budgets, while SRES remains stronger for best-threshold F1 and
> precision against human-reviewed decision-change labels.

This claim matches the current convergence: CEIS ties SRES at the diagnostic
0.3889 budget, while the CEIS-specific pattern is early-budget frontier
behavior.

### Claim 3: Complementarity Claim

CEIS should be positioned as adding decision-instability signal that SRES does
not fully capture. Main tables should report SRES alone, CEIS alone,
`max(zSRES, zCEIS)`, rank fusion, and two-stage SRES screen to CEIS tie-break.
If fusion wins, the contribution becomes: CEIS supplies incremental
decision-stability signal complementary to SRES.

### Claim 4: Linguistic Claim

The CSL contribution is that ASR risk is not uniformly distributed over
transcript distance. It concentrates in decision-bearing spans such as
negation, amount, actor, action, time, intent, and uncertainty. The full
300/900 risk-atom linguistic evidence table and 8-12 synthetic Mandarin/Taiwan
minimal pairs must be main-text evidence, not only appendix material.

### Claim 5: Scope Claim

The selected-300 surface is an enriched high-risk audit surface, not a
population-prevalence sample. Policy replay is retrospective aggregate replay,
not a live deployment trial. Aggregate-only release supports reviewer-visible
auditability but not row-level reproduction. These scope statements should
appear early so they read as claim-evidence discipline rather than defensive
limitations.

## Required Experiment Matrix

| Experiment | Claim | Placement | Minimum pass standard |
| --- | --- | --- | --- |
| Full 300/900 predictor regeneration | CEIS/SRES/WER/CER against human decision-change | Main text | Remove 30/90 from main claims; report positive count, AUC, F1, precision, recall, FN, and row-clustered CI |
| Fixed-budget severe-miss frontier | Primary endpoint | Main text | At 10% or 20% budget, CEIS severe-miss remaining is less than or equal to SRES; if severe positives are fewer than 20, primary endpoint downgrades |
| CEIS ablation suite | CEIS component necessity | Main text | Report full, without plausibility, without atom weights, binary atom, and policy-distance-only; downgrade component claims if ablations do not hurt |
| CEIS vs SRES incremental analysis | CEIS is non-redundant | Main text | Delta AUC row-clustered CI, paired row-cluster bootstrap, and `label ~ SRES + CEIS` residual gain |
| SRES+CEIS fusion baselines | Complementarity | Main text or appendix | Report SRES alone, CEIS alone, rank fusion, and two-stage; if fusion wins, rewrite contribution as complementary signal |
| Selection-exclusion sensitivity | Circularity defense | Main text | Excluding CEIS-selected / CEIS+SRES-family strata should not reverse the early-budget pattern; underpowered cases must be stated |
| Variant-count/source coverage audit | Defense against `max_v` variant-count attack | Main text | Report variant-count-only, top-k capped, source-balanced max, and source-specific coverage; if count-only approaches CEIS, downgrade claim |
| Risk-atom linguistic evidence table | CSL speech/language contribution | Main text | Full 300/900 table with atom count, decision-change rate, severe-miss rate, CEIS/SRES rank, and Mandarin source share where reconstructable |
| Synthetic scoring demo | Aggregate-only mechanism compensation | Main short table + appendix | 8-12 pairs; each pair reports atom, ambiguity type, `f(x)`, `f(v)`, DecisionDistance, Plausibility, RiskAtomWeight, and CEIS |
| Residual unsafe downrouting breakdown | Required only if unsafe-governance claim remains | Main aggregate + appendix | Without breakdown, claim only severe missed-escalation reduction, not unsafe downrouting mitigation |

## Delete And Rewrite List

1. Change the title.

   Suggested title:

   > Counterfactual Decision Stability for High-Stakes Mandarin ASR
   >
   > Evaluating Safety-Relevant Instability Beyond Transcript Accuracy

   The current low-WER title overcommits to a low-WER denominator even though
   `cer_zh_micro` is the main Chinese surface metric and WER is supplemental.

2. Remove all 30/90 main-result claims.

   The final CSL main text should use 300 rows and 900 model-level assessments
   per reviewer for selected-300 human-audit claims. Thirty-row / 90-assessment
   evidence can only be internal or appendix pilot evidence.

3. Move confidence-only to appendix as a negative result.

   The main baseline set should center SRES, model-disagreement-only selective
   escalation, and possibly semantic-distance / risk-coverage baselines.

4. Move candidate-lane content to appendix.

   Candidate models only enter the main benchmark after Taiwan Traditional
   Chinese locale and runtime gates. The current main work is not new
   full-split ASR inference.

5. Compress governance in the main text to two paragraphs.

   Keep one release-boundary paragraph and one intended-use paragraph. Put
   artifact manifests, operation records, and claim registry in appendix. Use
   the saved main-text space for CEIS ablations, incremental analysis,
   Mandarin minimal pairs, risk-atom table, and variant-source coverage.

6. Replace broad safety language with operational terms.

   Abstract/results: safety-relevant decision instability.
   Method: policy-conditioned instability.
   Primary endpoint: severe missed-escalation.
   Avoid actual-harm language except to say this study does not measure actual
   harm.

7. Make policy interventions deterministic.

   `conservative_machine_action` does not replace transcripts. It means
   stopping automatic downrouting, raising review priority, abstaining, or
   requiring human confirmation.

## CSL Narrative Spine

1. ASR in high-risk speech systems is now a decision substrate for routing,
   escalation, compliance, and case handling. In Mandarin anti-fraud settings,
   one negation marker, amount unit, or role word can cross an action boundary.
2. WER/CER and semantic ASR metrics remain necessary, but they measure
   transcript or semantic similarity. CEIS asks whether plausible ASR
   alternatives change declared downstream action.
3. Method core: CEIS over `V(x)`, where variants are not generic paraphrases
   but risk-atom-centered ASR alternatives. `f` is a fixed policy abstraction
   and DecisionDistance is policy-space distance.
4. Evidence ladder remains separated: 258-row ASR split for ASR context;
   selected-300 provenance for enriched audit surface; 300/900 human audit for
   predictor comparison; retrospective policy replay for conservative-action
   frontier.
5. Result spine: CEIS does not win everything. It matters for early fixed
   budget severe-miss capture; SRES remains strong for F1/precision; fusion
   tests complementarity; residual unsafe downrouting is decomposed or removed
   from the claim.
6. CSL contribution stands on risk atoms and Mandarin/Taiwan instantiation:
   CER as primary Chinese surface metric, WER/jieba as supplemental, and
   variant sources such as homophone/near-homophone, numeral/amount,
   segmentation/tokenization, locale violation, model disagreement, and
   domain-slot substitution.

## Twelve Remaining Gate Questions And Answers

### 1. Primary Endpoint Failover

If full 300/900 severe-miss positives are fewer than 20, the primary endpoint
changes to **decision-change AUC**. Decision-change is the human audit's main
label target, should have more positives than severe miss, and is statistically
more stable. Risk-coverage AUC becomes secondary. Severe-miss frontier becomes
descriptive high-severity analysis. The manuscript must not use too few severe
positives to carry the entire paper.

### 2. Budget Denominator

Primary fixed-budget denominator: **D. one trigger per row in a row-level
budget**. Ten percent and 20 percent refer to selected-300 audio rows, so the
budgets are at most 30 and 60 rows. Multiple model hypotheses within one row
help determine the row's worst-case or max-risk score, but do not consume
budget multiple times. Secondary model-level 900-assessment analysis can be
reported separately. Primary table definition: unit is audio row; ranking score
is max CEIS/SRES over eligible hypotheses within row; trigger means the row is
selected for conservative action.

### 3. Severe-Miss Counting Unit

Primary endpoint counts one unresolved severe row, not multiple severe model
hypotheses. If one audio row has three hypotheses and two are severe misses,
primary row-level severe miss count is 1. Model-assessment-level severe count
is secondary and describes model hypothesis instability. Row aggregation:
`row_score = max_h score(row,h)`, `row_severe = any_h severe_miss(row,h)`,
budget selects top-k rows, and remaining severe is the number of untriggered
severe rows.

### 4. Tie-Breaking Rule

Primary tie-breaking uses worst-case within the tied boundary. If the 10%
budget cutoff falls inside a tied score group, the table reports best-case and
worst-case range, and the claim uses the worst-case. Ranking uses stable
deterministic sort, score descending then row hash ascending, only for
reproducibility. If worst-case and average-case disagree, the result is
tie-sensitive and cannot support a win claim.

### 5. `f` Freeze Proof

Unless a timestamped / hashed operation record proves that
`downstream_decision_contract.md` and `ceis_config.json` were frozen before
human audit labels and policy replay, the paper should call `f` a
**retrospective policy contract**. Current wording can say CEIS is evaluated
under a declared retrospective policy abstraction with frozen scoring files for
regeneration. It cannot claim prospective deployment design without pre-audit
commit/hash evidence.

### 6. Blind Generator Proof

Blind generator proof requires an aggregate operation record listing generator
timestamp, git commit, config hash, input artifact hashes, allowed inputs,
forbidden inputs, and output manifest hash.

Allowed inputs:

- ASR hypotheses.
- Model disagreement.
- Mandarin phonetic ambiguity rules.
- Domain-slot rules.
- Runtime / quality signals.
- Normalization / locale outputs.

Forbidden inputs:

- Reference transcript.
- Human labels.
- Expected safe action.
- Selection stratum.
- Reviewer notes.
- Policy replay outcome.

If this proof cannot be produced, CEIS must be described as a post-hoc
aggregate audit metric.

### 7. Ablation Failure Policy

If without plausibility matches full CEIS, delete the claim that the
plausibility proxy is a necessary performance component; plausibility becomes
an interpretability/filtering layer. If binary atom matches full CEIS, delete
the claim that fine-grained atom weights improve ranking; typed atom schema
remains linguistic localization. If policy-distance-only matches full CEIS,
delete the three-term CEIS innovation claim; the result becomes declared-policy
distance ranking with risk atoms and plausibility as explanatory scaffolding.
Policy-distance-only matching full CEIS is the most damaging case because it
undercuts empirical contribution from the speech/language layer.

### 8. Variant-Count Attack

Default handling: **B. CEIS needs source-balanced normalization**. If
variant-count-only predictor approaches CEIS, raw `max_v` has variant-volume
sensitivity. The final metric should switch to source-balanced or top-k-capped
CEIS, and raw CEIS should move to appendix. If source-balanced CEIS still loses
to count-only, CEIS cannot support the main empirical claim and should remain a
method proposal.

### 9. Fusion Dominance

If SRES+CEIS fusion beats CEIS alone, the title and abstract can still center
Counterfactual Decision Stability, but not "CEIS outperforms." Use a title
such as **Counterfactual Decision Stability for High-Stakes Mandarin ASR**.
Abstract claim becomes: CEIS provides an incremental decision-stability signal
that improves combined early-budget severe-miss ranking with SRES. A
complementary-signal claim is more defensible than replacement.

### 10. Minimum Viable Linguistic Table

If source-specific phonetic/domain/runtime/rejected logs cannot be fully
reconstructed, the main-text linguistic evidence still needs a full 300/900
atom-level outcome table. Minimum columns: atom type, row count,
model-assessment count, decision-change positives, decision-change rate,
severe-miss positives, severe-miss rate, median CEIS rank, median SRES rank,
and human criticality rate. Mandarin-specific source share can move to
appendix limitation if incomplete. Synthetic pairs explain mechanism but do
not replace empirical linguistic evidence.

### 11. Residual Unsafe Downrouting Claim

Yes. If residual unsafe downrouting breakdown is not completed, remove all
claims that unsafe downrouting governance has been handled or mitigated. Keep
only severe missed-escalation reduction. Final results should state that
risk-triggered policies reduce severe missed-escalation under replay, while
residual unsafe downrouting remains unresolved and outside the primary
endpoint.

### 12. Submission Gate

Not every red line automatically stops CSL submission, but three cannot be
downgraded:

1. Full 300/900 predictor/replay regeneration with 30/90 removed from main
   claims.
2. CEIS ablation suite.
3. CEIS vs SRES incremental analysis.

Two can downgrade only with claim reduction:

4. Selection-exclusion sensitivity may move to appendix if underpowered, but
   main text must state enriched selected surface and remove strong
   anti-circularity claims.
5. Variant-count/source coverage audit: variant-count-only and top-k cap
   cannot be downgraded; full source-specific coverage can become an appendix
   limitation if incomplete, but generator-completeness claims must be removed.

Synthetic scoring demo is a reviewer-package gate rather than an empirical
gate. Residual unsafe breakdown is conditional: if the paper keeps unsafe
downrouting mitigation language, it cannot be downgraded.

## Round 3 Frozen Decisions

- Primary endpoint: row-level severe-miss remaining at 10-20% fixed trigger
  budget.
- Primary failover: decision-change AUC if severe-miss positives are fewer
  than 20.
- Budget unit: selected audio row, with at most one trigger per row.
- Row ranking score: max score over eligible hypotheses within row.
- Tie handling: worst-case within tied boundary for primary claims.
- `f` status without timestamp/hash proof: retrospective policy contract.
- Variant generator without operation proof: post-hoc aggregate audit metric.
- Title direction: counterfactual decision stability for high-stakes Mandarin
  ASR, not low-WER danger.
- Non-negotiable CSL gates: full 300/900 regeneration, CEIS ablation suite,
  and CEIS-vs-SRES incremental analysis.

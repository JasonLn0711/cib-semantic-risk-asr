# CSL Final Execution Plan

Date: 2026-06-03

Status: final execution plan recorded. This plan is the transition from
first-principle pressure testing to implementation. It does not itself execute
the experiments.

## Current Convergence

The manuscript has converged to a publishable version:

- CEIS does not replace WER, CER, or SRES.
- CEIS is a counterfactual decision-stability layer for high-risk ASR.
- The primary empirical effect is row-level fixed-budget severe
  missed-escalation ranking.
- If severe positives are insufficient, the primary endpoint falls back to
  adjudicated decision-change AUC.
- The current evidence mismatch must be fixed: the completed 300-row /
  900-assessment dual-reviewer audit cannot coexist with main results still
  using the 30-row / 90-assessment replay surface.

## 0. Final Submission Thesis

Main thesis:

> In high-stakes Mandarin ASR, transcript accuracy should be complemented by
> counterfactual decision-stability evaluation, because small plausible
> alternatives around decision-bearing atoms can preserve low transcript
> distance while changing the safe downstream action.

Allowed empirical claim:

> On a selected high-risk Mandarin anti-fraud audit surface, CEIS improves
> row-level early-budget capture of severe missed-escalation cases at
> pre-specified 10-20% trigger budgets, while SRES remains stronger for
> best-threshold F1 and precision against adjudicated decision-change labels.

Failover claim if full 300/900 row-level severe-miss positives are fewer than
20:

> CEIS provides a decision-change prediction signal under row-clustered AUC
> analysis; severe missed-escalation replay is reported as descriptive
> high-severity analysis.

This failover must be written into the statistical analysis plan. Do not let a
small number of severe positives carry the entire CSL paper.

## 1. Freeze Definitions Before Running Tables

The first execution step is freezing contracts, not rerunning tables. Without
this step, reviewers can argue that the results are post-hoc tuned.

| Item | Final definition |
| --- | --- |
| Primary unit | audio row / case |
| Model-level unit | secondary; 900 assessments are clustered within rows |
| Row score | `row_score = max_h score(row, h)` |
| Row severe label | `row_severe = any_h severe_miss(row, h)` |
| Budget denominator | selected-300 audio rows; 10% = 30 rows and 20% = 60 rows |
| Trigger | selected row receives conservative action once |
| Tie handling | if cutoff lands in a tied group, report best/worst-case range; primary claim uses worst-case |
| Main label | adjudicated human decision-change label |
| Policy function `f` | retrospective declared policy abstraction unless pre-audit timestamp/hash exists |
| CEIS generation | blind protocol; forbidden inputs are reference transcript, human labels, expected safe action, selection stratum, reviewer notes, and replay outcome |
| Conservative action | does not change transcript; means abstain, raise review priority, stop automatic downrouting, or require human confirmation |

Current manuscript foundations are useful: it already defines `f`, CEIS
formula, and policy label space. The missing pieces are freeze proof and
retrospective wording discipline.

## 2. Regenerate Full 300/900 Main Results

This is the first non-downgradable red line.

The current PDF says the selected-300 dual-reviewer audit is complete, with
900 model-level assessments per reviewer, while the main result pages still
contain 30-row / 90-assessment figures and tables. That is a blocking evidence
mismatch before CSL submission.

| Original item | Action |
| --- | --- |
| Figure 2 evidence ladder | change to 300 rows / 900 assessments; remove 30/90 from main text |
| Table 2 predictor performance | regenerate full 300/900 with row-clustered CI |
| Figure 3 AUC plot | regenerate full 300/900 and state SRES/CEIS interval overlap directly |
| Table 3 policy replay | make row-level primary and model-level secondary |
| Figure 4 residual risk | regenerate full 300/900; do not package unsafe downrouting as handled |
| Figure 5 fixed-budget frontier | row-level 10/20/30/40%; report tie-boundary range |
| Figure 6 risk-atom evidence | full 300/900; no 30-row linguistic evidence in main text |
| Appendix A1 | regenerate full 300/900 or label pilot |
| Claim registry | rewrite or delete all 30/90 result claims |
| Low-WER / low-CER danger table | rerun only if title claim remains; otherwise appendix secondary |

Thirty-row / 90-assessment outputs can remain internal development artifacts.
If included in appendix, they must be labeled pilot and cannot support main
claims.

## 3. Primary Endpoint Decision Tree

After full 300/900 regeneration, inspect row-level severe positives first.

| Condition | Primary endpoint | Main-text voice |
| --- | --- | --- |
| row-level severe positives >= 20 | severe-miss remaining at 10-20% row-level trigger budget | CEIS improves early-budget severe-miss capture |
| row-level severe positives < 20 | adjudicated decision-change AUC | CEIS predicts decision-change; severe frontier descriptive |
| severe positives < 5 in a sensitivity subset | no pass/fail | report underpowered sensitivity |
| CEIS and SRES tie at 10/20% | complementary signal | do not write improves |
| CEIS worse than SRES | method proposal + mechanism analysis | no empirical superiority claim |

This decision tree belongs in the internal analysis plan. The manuscript can
summarize it in the statistical subsection.

## 4. CEIS Ablation Suite

This is the second non-downgradable red line.

Required variants:

| Variant | Tests |
| --- | --- |
| Full CEIS | main method |
| Without plausibility | whether plausibility proxy adds precision / ranking value |
| Without atom weights | whether risk atom weighting adds value |
| Binary atom | whether typed atoms are sufficient and fine-grained weights are needed |
| Policy-distance-only | whether CEIS is only `DecisionDistance(f(x), f(v))` |

Pre-written interpretation:

| Result | Claim removed or downgraded |
| --- | --- |
| without plausibility approximately equals full | remove "plausibility is a necessary performance driver"; reframe as filtering / interpretability layer |
| binary atom approximately equals full | remove "fine-grained atom weights improve ranking"; keep typed atom localization |
| without atom weights approximately equals full | downgrade atom weights to explanatory component |
| policy-distance-only approximately equals full | remove three-term innovation claim; downgrade CEIS to declared-policy distance ranking |
| all ablations approximately equal full | empirical contribution sharply downgraded; keep method proposal + diagnostic framework |

Policy-distance-only matching full CEIS is the most damaging result because it
means the speech/language layer lacks empirical support.

## 5. CEIS Versus SRES Incremental Analysis

This is the third non-downgradable red line.

Main table should report:

| Test | Minimum requirement |
| --- | --- |
| Delta AUC | `AUC(CEIS) - AUC(SRES)` with row-clustered bootstrap CI |
| Paired bootstrap | audio-row resampling; do not treat 900 assessments as independent |
| Residual gain | `label ~ SRES + CEIS`; report CEIS coefficient, bootstrap CI, delta AUC or delta log-loss |
| Early-budget comparison | 10% and 20% row-level budget; report severe remaining, eliminated, and triggers/elimination |
| Fusion baseline | SRES alone, CEIS alone, `max(zSRES,zCEIS)`, rank fusion, two-stage SRES to CEIS tie-break |

If SRES+CEIS fusion beats CEIS alone, this is not a failure. Abstract wording
should become:

> CEIS supplies an incremental counterfactual decision-stability signal that
> improves combined early-budget severe-miss ranking with SRES.

## 6. Variant-Count / Source Audit

Variant-count-only and top-k cap cannot be downgraded. Full source-specific
coverage can become a limitation only if claims are narrowed accordingly.

Required audits:

| Audit | Purpose |
| --- | --- |
| per-row variant count distribution | test whether `max_v` benefits from variant-volume advantage |
| variant-count-only predictor | defend against CEIS merely counting generated variants |
| top-k capped CEIS | test whether raw max depends too much on variant volume |
| source-balanced CEIS | balance model disagreement, phonetic, domain-slot, and runtime sources |
| shuffled atom negative control | appendix check for atom assignment signal |
| reject-reason aggregate table | explain how plausible gate falsifies variants |

If variant-count-only approaches CEIS, switch the main text to
source-balanced / top-k-capped CEIS and move raw CEIS to appendix. If
normalized CEIS still loses to count-only, CEIS cannot be the main empirical
claim and must be a method proposal.

## 7. Selection-Exclusion Sensitivity

This is the fourth red line, but can downgrade if underpowered.

Required sensitivity versions:

| Sensitivity | Purpose |
| --- | --- |
| exclude CEIS-selected rows | defend against CEIS selection circularity |
| exclude CEIS/SRES-family selected rows | defend against metric-family enrichment |
| stratum reweighting / inverse-propensity sensitivity | test whether enriched surface distorts ranking |

Pass/fail standards:

| Condition | Judgment |
| --- | --- |
| CEIS at 10/20% severe remaining <= SRES and residual gain does not reverse | pass |
| Delta AUC positive but early-budget unstable | partial support |
| two of early-budget, delta AUC, and residual gain reverse | fail |
| severe positives < 5 | underpowered; no pass/fail |

Never write that this proves no circularity. Write only whether the
selection-exclusion sensitivity did or did not reverse the pattern.

## 8. Linguistic Evidence: Hardening CSL Contribution

The current risk atom schema is valuable but still reads like taxonomy. It
must become evidence.

Main text requires a full 300/900 atom-level table with at least:

- atom type
- reviewed row count
- model-assessment count
- variant count
- decision-change positives
- decision-change rate
- severe-miss positives
- severe-miss rate
- median CEIS rank
- median SRES rank
- human criticality rate
- Mandarin-specific source share, if reconstructed

If source-specific phonetic/domain/runtime logs cannot be reconstructed,
Mandarin source share becomes appendix limitation. Synthetic pairs alone are
not enough.

Add 8-12 synthetic Mandarin/Taiwan minimal pairs as mechanism demonstration:

| Pair | Atom | Ambiguity type | Must show |
| --- | --- | --- | --- |
| 沒有匯款 / 有匯款 | negation + action | negation deletion | `f(x)`, `f(v)`, DecisionDistance, CEIS |
| 三萬 / 三十萬 | amount | Mandarin numeral scale | same |
| 昨天 / 今天 / 下週 | time | temporal slot | same |
| 客服 / 警察 / 銀行 | actor | role substitution | same |
| 取消分期 / 繼續分期 | action + intent | domain phrase confusion | same |
| 不確定 / 確定 | uncertainty | epistemic stance | same |

These examples help reviewers see CEIS as a speech/language mechanism rather
than an abstract governance score.

## 9. Residual Unsafe Downrouting

If the 24 residual unsafe cases are not broken down, all unsafe downrouting
mitigation language must be removed.

| Breakdown status | Main-text allowed claim |
| --- | --- |
| completed | report severe-miss reduction plus residual unsafe taxonomy |
| not completed | claim only severe missed-escalation reduction |
| not completed but manuscript says unsafe downrouting handled | do not submit |

Minimum aggregate breakdown:

- residual unsafe category
- atom type
- expected safe action
- replay action
- CEIS rank bucket
- SRES rank bucket
- variant source if available
- whether severe

The manuscript can say high-risk missed and critical miss go to zero only if
that is supported. It cannot imply all-risk mitigation while unsafe downrouting
remains.

## 10. Statistical Subsection

Add a standalone section:

> Statistical inference and operating-point selection

Required content:

| Topic | Required wording |
| --- | --- |
| Unit | audio row |
| Cluster | model assessments clustered within row |
| CI | row-clustered bootstrap |
| AUC | bootstrap percentile CI |
| F1/precision/recall/FN | recompute at fixed threshold; if best-threshold, select threshold inside bootstrap or label diagnostic |
| Fixed budget | pre-specified 10%, 20%, 30%, 40% row budget |
| Thresholds | diagnostic unless selected on independent dev split |
| Positive counts | report decision-change positives and row-level severe positives |
| Tie-breaking | best/worst-case range when cutoff enters tied group |
| Sensitivity | selection-exclusion and leave-one-row-out |
| Deployment | replay only, not a live causal trial |

This reframes statistical choices as design rather than limitation patching.

## 11. Manuscript Rewrite Structure

New main-text order:

1. Introduction: ASR as decision substrate; small decision atoms; do not lead
   with low-WER danger.
2. Related Work: WER/CER, semantic distance, ASR correction, selective
   prediction; end with decision-stability gap.
3. Method: CEIS formula, variant contract, risk atoms, `f`, conservative
   action.
4. Statistical inference and operating-point selection.
5. Evidence ladder: 258 split, selected-300 provenance, 300/900 audit, policy
   replay.
6. Experiments:
   - E1 ASR surface benchmark.
   - E2 full 300/900 predictor study.
   - E3 CEIS ablations and incremental SRES analysis.
   - E4 fixed-budget severe-miss replay.
   - E5 linguistic atom analysis.
7. Results: keep evidence layers separate.
8. Discussion: CEIS complementary to SRES; Mandarin/Taiwan instantiation;
   scope limits.
9. Ethics / artifact boundary: two paragraphs.
10. Appendix: artifact manifest, synthetic demo, candidate lane, claim
    registry, operation records.

## 12. Title And Abstract

Change title:

> Counterfactual Decision Stability for High-Stakes Mandarin ASR
>
> Evaluating Safety-Relevant Instability Beyond Transcript Accuracy

Remove "When Low WER Becomes Dangerous" as the main title because it
overcommits to low-WER evidence and weakens the Chinese metric discipline where
`cer_zh_micro` is primary.

Abstract four-sentence skeleton:

1. Speech-driven systems use ASR transcripts as routing and escalation
   substrates.
2. Small Mandarin decision atoms can preserve transcript similarity while
   changing declared triage action.
3. We introduce CEIS, a counterfactual decision-stability metric over
   plausible transcript alternatives, risk atoms, and policy-space decision
   distance.
4. Use one result sentence depending on final positive count:

If severe positives >= 20:

> On a selected high-risk Mandarin anti-fraud audit surface, CEIS improves
> row-level early-budget capture of severe missed-escalation cases at
> pre-specified 10-20% trigger budgets, while SRES remains stronger for
> best-threshold F1/precision.

If severe positives < 20:

> In the full 300-row dual-reviewer audit, CEIS provides decision-change
> prediction signal under row-clustered AUC analysis; severe missed-escalation
> replay is reported as descriptive high-severity evidence.

Do not write zero false negative as a deployment threshold in the abstract.

## 13. Minimum Reviewer Package

Provide at least nine items:

1. Artifact manifest with SHA256.
2. Full 300/900 aggregate predictor, replay, and ablation tables.
3. Row-cluster bootstrap scripts.
4. CEIS config JSON.
5. Downstream decision contract.
6. Blind generator operation record.
7. Synthetic scoring demo.
8. Source-balanced / top-k / variant-count audit tables.
9. Aggregate reject-reason table.

Normalization/tokenizer policy should be part of the manifest. Raw audio,
transcripts, row IDs, hypotheses, reviewer notes, and runtime logs remain
local-only. Synthetic demo and aggregate operation records compensate for the
aggregate-only release boundary.

## 14. Two-Week Execution Cadence

### Day 1: Freeze Day

Freeze `f`, CEIS config, variant generator protocol, statistical analysis plan,
allowed/forbidden inputs, tie rule, and budget denominator.

Outputs:

- `downstream_decision_contract.md`
- `ceis_config.json`
- `variant_generator_contract.md`
- `statistical_analysis_plan.md`
- manifest hash

### Day 2-4: Full 300/900 Regeneration

Rerun predictor, policy replay, fixed-budget frontier, row-level aggregation,
and positive counts.

Stop condition: any main table still containing 30/90 blocks writing progress.

### Day 5-6: Ablation And Incremental Analysis

Run CEIS ablations, delta AUC, paired row bootstrap, residual gain, and fusion
baselines.

Stop condition: no ablation suite means no CSL submission.

### Day 7-8: Selection And Variant Stress Tests

Run CEIS-selected exclusion, CEIS/SRES-family exclusion, reweighting,
variant-count-only, top-k cap, source-balanced CEIS, and reject reasons.

Stop condition: if variant-count-only approaches raw CEIS, switch to
normalized CEIS or downgrade claim.

### Day 9: Linguistic Evidence

Produce full 300/900 atom-level outcome table and 8-12 synthetic
Mandarin/Taiwan minimal pairs.

Stop condition: no atom-level empirical table means no main linguistic
contribution claim.

### Day 10: Residual Unsafe Decision

Create residual unsafe breakdown. If not feasible, delete all unsafe
downrouting mitigation wording.

### Day 11-12: Rewrite Manuscript

Update title, abstract, method, statistical section, results, discussion, and
limitations. Compress governance to two paragraphs. Move confidence-only to
appendix as a negative result. Move candidate lane to appendix.

### Day 13: Audit Package

Build manifest, hashes, scripts, synthetic demo, aggregate tables,
reject-reason summary, and operation record.

### Day 14: Red-Team Pass

Ask only five questions:

1. Does main text still contain a 30/90 result claim? If yes, return.
2. Is CEIS written as a general ASR metric? If yes, return.
3. Does the paper claim CEIS universally beats SRES? If yes, return.
4. Is retrospective replay written as deployment proof? If yes, return.
5. Does the paper claim unsafe downrouting is handled without 24-case
   breakdown? If yes, return.

## 15. Submission Red Lines

Non-downgradable:

1. Full 300/900 predictor/replay regeneration with 30/90 removed from main
   claims.
2. CEIS ablation suite.
3. CEIS vs SRES incremental analysis.

Conditional:

4. Selection-exclusion sensitivity can move to appendix only if underpowered,
   with main claim narrowed.
5. Variant-count/source audit: variant-count-only and top-k cap cannot be
   downgraded; missing full source coverage downgrades generator claims.
6. Residual unsafe breakdown cannot be downgraded if the paper claims unsafe
   downrouting mitigation.
7. Synthetic demo is not an empirical gate, but without it the aggregate-only
   paper becomes hard to inspect.

Final submission rule:

> Without full 300/900 regeneration, CEIS ablation, and CEIS-vs-SRES
> incremental analysis, do not submit to CSL.

Other gaps can be handled through claim narrowing. These three cannot be fixed
by wording.

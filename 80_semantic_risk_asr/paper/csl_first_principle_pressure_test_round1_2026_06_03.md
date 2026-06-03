# CSL First-Principle Pressure Test Round 1

Date: 2026-06-03

Status: recorded for manuscript strategy, claim hardening, and final CSL
execution planning.

## Expert Prompt

Using first principles, act as a top computer science professor advising a new
PhD student preparing a Computer Speech & Language submission. Do not produce
the final plan first. Instead, reverse the usual interaction: ask hard
questions that pressure-test the student's thinking, clarify innovation and
novelty, expose blind spots, and continue questioning until the answers are
clear enough to support a final stepwise execution plan.

The current manuscript core is: ASR evaluation should move from transcript
similarity to decision stability. CDS-ASR and CEIS test whether plausible
transcript alternatives change downstream high-risk decisions. The selected-300
surface is an enriched high-risk audit surface, and CEIS ablation plus
full-audit regeneration remain hard gates before final CSL submission.

## Round 1 Questions And Answers

### 1. Single-Sentence Thesis

本文展示以 CEIS 為核心的 CDS-ASR，使得 ASR 評估能夠在臺灣反詐欺通話的
enriched high-risk audit surface 中，比 WER/CER 與 SRES 更直接地偵測
plausible transcript alternatives 引發的下游 triage action 不穩定，並在固定
預算 replay 中更保守地捕捉 severe missed-escalation cases。

### 2. True Unit Of Innovation

主創新選 CEIS。CDS-ASR 是框架包裝，risk atom schema 是表示層，
aggregate-only governance 是可投稿性與敏感資料處理層。CEIS 才是可定義、
可比較、可 ablate、可被 reviewer 判斷真偽的 Computer Speech & Language
貢獻：它把 ASR alternative hypothesis 的語音／語言差異投影到 downstream
decision distance。它不是單純 workflow engineering，因為它重新定義 ASR
evaluation target：從 transcript similarity 變成 plausible ASR alternatives
下的 decision-stability functional。稿件目前公式
`max_v Plausibility(v|x) * RiskAtomWeight(v) * DecisionDistance(f(x), f(v))`
就是主創新應站的位置。

### 3. Boundary Between CEIS And Semantic ASR Metrics

| Dimension | Semantic Distance / ASD | CEIS |
| --- | --- | --- |
| Input | reference/hypothesis 或 transcript pair | transcript `x`, variant set `V(x)`, risk atoms, `f`, plausibility proxy |
| Output | semantic distance 或 alignment-based semantic score | maximum counterfactual decision-instability score |
| Objective | align transcript comparison with SLU or human semantic judgment | predict whether plausible ASR alternatives change triage action or severe miss risk |
| Loss surface | global semantic similarity; errors accumulate more continuously | `max` over variants with sparse, high-curvature risk around atoms and decision distance |
| Failure mode | small token differences can look semantically close while hitting negation/amount/actor | generator misses variants, atom weights fail, or `f` policy contract is wrong |

CEIS adds counterfactual ASR alternatives as input, policy-space instability as
output, unsafe action-boundary crossing as objective, and local high-sensitivity
around decision atoms as the loss surface. Semantic Distance can say two
sentences are semantically close; CEIS asks whether that close difference
changes system action.

### 4. Counterfactual Variants: Research Object Or Tool Assumption

Counterfactual variants should currently be positioned as a tool assumption,
not the complete research object. The scientific object is whether decisions
remain stable under the declared plausible variant set. If the generator misses
the truly dangerous alternative, CEIS underestimates risk; it remains a
conditional lower-bound audit, not a complete safety certificate. The defense
against "CEIS is only generator-quality packaging" requires generator-only
baseline, source-specific variant coverage audit, and CEIS ablation. CEIS is
strong only if it predicts human decision change after controlling for variant
count, plausibility-only, and model-disagreement-only signals. The final paper
should state the generator boundary directly and turn source-specific variant
coverage into validation, not a loose limitation.

### 5. How Plausibility Can Be Falsified

A variant is not plausible if it lacks acoustic, phonetic, model-disagreement,
or runtime support; violates context or domain slot; or inserts information the
original audio span could not carry. Example: if audio supports "我昨天匯了三萬元",
then "我上週透過加密貨幣匯了三百萬元給假檢警" is anti-fraud-semantically
reasonable but acoustically unsupported, so it should be rejected. Conversely,
if `匯款` becomes a near-homophone with domain-invalid meaning, acoustic
possibility is not enough; domain semantics should make plausibility near zero
or exclude it. The system needs a reject-reason taxonomy: acoustic unsupported,
semantic/domain invalid, context contradiction, and external content insertion.
Final submission should report aggregate reject counts.

### 6. Necessity Of The Three CEIS Multiplicative Terms

`DecisionDistance` is the core; without it CEIS collapses toward variant/risk
scoring rather than decision-stability evaluation. The expected most damaging
ablation is without plausibility, because implausible variants should inflate
false positives. Without atom weights may be moderately damaging; binary atom
may be closest to full CEIS. If binary atom is almost as good, the fine-grained
atom-weight claim should be downgraded, while the core contribution becomes
plausible alternatives times decision distance. If without plausibility is just
as good, the plausible gate is not contributing and CEIS risks becoming a
policy-distance heuristic. The final CSL version must run these ablations.

### 7. Definition Of Downstream Decision Function `f`

`f` should be defined as a versioned rule-based policy abstraction / ordinal
label mapper, not an LLM classifier. Formally: `a(t) = extracted decision
atoms/features`, then `f(t) = h(a(t); C_policy)`, producing
`{no_escalation, manual_review, priority_review, critical_escalation,
conservative_machine_action, abstain}`. The current manuscript direction is
correct: `f` is fixed before CEIS scoring, and decision distance is
policy-aligned rather than model-generated. If `f` is wrong, CEIS measures
policy-conditioned ASR instability, not policy optimality. It can prove that
transcript alternatives change a declared policy action; it cannot prove the
declared anti-fraud policy is itself correct.

### 8. Label Leakage And Selection Circularity

There is selection-induced circularity risk, though not necessarily label
leakage. If CEIS helped select selected-300 and is then evaluated on
selected-300 against human decision-change labels, enrichment can inflate
positive density, AUC, threshold behavior, and FN results. The defense requires
three sensitivity checks: exclude CEIS-selected strata; exclude CEIS/SRES family
signals and keep only downstream escalation, model disagreement, and
clean-control strata; and run selection-stratum reweighting or inverse
propensity sensitivity. Threshold selection and evaluation must be separated.
The manuscript already admits selected-300 is enriched rather than
prevalence-preserving; the final paper must make the sensitivity check an
experiment, not a limitation sentence.

### 9. Most Feared Reviewer Comment

> This is a post-hoc risk scoring heuristic evaluated on a selected sample, not
> a general ASR metric.

The response should be experimental, not rhetorical. CEIS should be claimed as
a scoped companion metric for policy-conditioned decision instability on an
enriched high-stakes audit surface. Existing evidence includes WER/CER/SRES
baselines, CEIS point-estimate AUC, diagnostic FN=0, SRES best-F1 advantage,
and policy replay frontier, which support "not a WER replacement." Final CSL
still needs full-audit regeneration, CEIS ablations, selection-exclusion
sensitivity, and generator-only baseline. Without those four, this reviewer
comment remains hard to defeat.

### 10. CEIS Versus SRES

CEIS wins in conservative decision-instability ranking and low-budget severe
miss capture; SRES wins in best-threshold F1 / precision; and both tie at the
0.3889 diagnostic policy budget for eliminating high-risk missed and critical
miss counts. Neither proves population prevalence, and neither eliminates
residual unsafe downrouting.

### 11. Why Zero False Negative Is A Reasonable Target

FN=0 is reasonable only for severe missed-escalation, not as a global safety
claim. The cost is more false positives: more manual review, conservative
escalation, waiting time, service friction, and reviewer fatigue. The current
0.3889 trigger budget may be too high for deployment; the fixed-budget frontier
is a better presentation, but still retrospective replay. FN=0 should be a
diagnostic operating point, not a deployment threshold. The cost is borne by
review teams and callers whose cases are delayed. The final paper should report
risk-coverage frontier, not only a single FN=0 line.

### 12. Residual Unsafe Downrouting 24

The residual unsafe downrouting count cannot be dismissed. The most defensible
interpretation is that CEIS/SRES replay optimizes high-risk missed and critical
miss outcomes rather than all unsafe downrouting. If the 24 are lower severity
taxonomy cases, the issue may be policy definition or label taxonomy; if they
include high-CEIS untriggered cases, it is method failure; if they lack
plausible variants, it is generator failure. The final paper should decompose
the 24 by atom type, expected safe action, `f` output, CEIS rank, and SRES rank.
Current evidence supports severe-miss reduction, not all-risk elimination.

### 13. CSL-Level Linguistic Insight

The risk atom schema should be written as a domain-instantiated
speech-language error ontology, not merely an anti-fraud taxonomy. Transferable
atoms include negation/polarity, quantity/amount, actor/participant role,
action/event type, time, intent, and uncertainty/epistemic stance. Scam pattern
is anti-fraud-specific; medical triage would use symptom pattern, dosage,
allergy, and severity; legal intake would use deadline, party, jurisdiction,
and claim type; mental-health hotline work would add self-harm intent,
means/access, immediacy, and protective factors. The linguistic insight is that
ASR risk is not evenly distributed across sentence-level semantic distance; it
concentrates in decision-bearing spans. These spans can be low-impact for
WER/CER and high-curvature in action space.

### 14. Mandarin / Taiwan Traditional Chinese Contribution

The primary contribution is a general high-risk ASR framework; the secondary
contribution is a strict Taiwan Mandarin / Traditional Chinese instantiation.
Chinese is not merely a dataset because it changes metric policy, variant
generation, locale gate, numeral/amount ambiguity, homophone/near-homophone
errors, unsegmented-WER instability, and simplified/traditional acceptability.
The manuscript's `cer_zh_micro` primary metric, `wer_zh_jieba_micro`
supplemental metric, and strict Taiwan Traditional Chinese locale gate can
support a CSL language contribution. If reviewers say English data could also
do this, the answer is that formal CEIS transfers, while plausible variant
generation and locale validity are language-specific. Do not claim CEIS only
works in Chinese; claim this paper provides the Mandarin/Taiwan instantiation
of a transferable evaluation principle.

### 15. Dataset Story And Final N

The final CSL main text should use four N values: 258-row ASR split,
selected-300 provenance, 300 human-reviewed audit rows, and 900 model-level
assessments per reviewer. The 30-row / 90-assessment surface is an old replay
surface; if left in the main claims, it creates contradiction. Figure 2, Table
2, Figure 3, Figure 4, Figure 5, and policy replay tables must either be
regenerated to 300/900 or moved to appendix as explicitly labeled pilot
evidence. Main-text result claims should remove all 30/90 result language. The
current manuscript has tension between completed 300/900 and old 30/90
figures/tables, making this a final CSL blocking issue.

### 16. Evidence Ladder

| Evidence layer | Supports | Does not support |
| --- | --- | --- |
| ASR benchmark, N=258 | model comparison, CER/WER policy, locale-gate context | selected-300 human decision-change claims or population harm prevalence |
| Selected provenance, N=300 | enriched high-risk audit surface, selection transparency, risk-signal coverage | prevalence-preserving estimates or no-circularity proof |
| Human audit, final N=300 rows / 900 model assessments per reviewer | reviewer label reliability, decision-change labels, CEIS/SRES/WER/CER predictor comparison | live deployment safety or actual fraud harm |
| Policy replay | conservative trigger budget, severe missed outcome reduction, CEIS/SRES operating frontier | causal deployment effect or elimination of all unsafe downrouting |

These four layers must remain separate in the paper.

### 17. Minimum Publishable Version

Keep three experiments. First, 258-row ASR benchmark supports
transcript-surface performance and locale-valid ASR context. Second, full
selected-300 dual-reviewer predictor study with WER/CER/SRES/CEIS and CEIS
ablations supports the claim that CEIS adds decision-stability signal beyond
transcript and semantic-risk baselines. Third, policy replay / fixed-budget
frontier supports the claim that risk triggers can reduce severe missed
outcomes under a declared conservative-action budget. Selected provenance
belongs in method, not as a main experiment. Candidate models should be
appendix or removed. Governance figures without direct claim support should be
cut from main text first.

### 18. Strongest Baseline

The strongest baseline is SRES, not WER/CER or confidence-only. Confidence-only
with unavailable calibrated confidence and no triggers looks like a weak or
artificial baseline; it should move to appendix as an engineering negative
result. A stronger baseline set would include SRES-ranked selective escalation,
model-disagreement-only escalation, and semantic-distance-ranked escalation
under the same budget frontier. A conformal-style baseline should only be used
if there is an independent calibration split; otherwise call it a selective
risk baseline.

### 19. CEIS Versus Abstention Policy Feature

CEIS can be used by an abstention or escalation policy, but it is itself a
transcript-alternative decision-instability metric. Example A: "客服說要確認資料"
versus "客服說要核對資料" may have similar WER/CER and semantic distance, but
`f` does not change, so CEIS is near zero. Example B: "沒有匯款三萬元" versus
"有匯款三萬元", or "三萬元" versus "三十萬元", may have similarly small edit
distance but cross negation/amount atoms and move `f` from manual review to
priority/critical action, making CEIS high. CEIS action is not determined by
token count or full-sentence semantic distance, but by whether a plausible
variant crosses a decision boundary.

### 20. Aggregate-Only Reproducibility

Aggregate-only reproducibility is both a strength and a weakness. It is a
privacy and governance strength but an empirical reproducibility weakness. To
compensate for lack of row-level reproduction, reviewers need artifact
manifest, SHA256, generator scripts, source-input roles, environment versions,
tokenizer/normalization policy, operation records, consistency gates, and
row-cluster bootstrap scripts. The current package already lists aggregate
manifest, operation records, validation summaries, metric tables, evidence
matrices, and consistency audits. Final CSL should add executable scoring demo
on synthetic/redacted cases, redacted counterfactual examples, aggregate
reject-reason counts, and source-specific variant coverage. Without a synthetic
demo, CEIS can look too much like a black-box governance workflow.

### 21. Title Claim: "When Low WER Becomes Dangerous"

The current support is partial. There are aggregate proxy low-WER danger
figures with denominator such as ALL low-WER denominator 237 and proxy
unsafe/high-risk/critical signals, but this is not yet the completed 300-row
human-audit main evidence. To keep the title, final CSL should report the
low-WER subset denominator, human decision-change numerator, unsafe downrouting
numerator, high-risk miss numerator, and critical miss numerator, ideally at
both row-level and model-assessment level. If this subset is not available, the
title should be softened to "When Transcript Accuracy Is Not Enough" or
"Decision Stability Beyond WER."

### 22. Definition Of "Dangerous"

Do not define dangerous as actual harm. The final definition should be unsafe
decision-instability under a declared triage policy: `dangerous = 1` if a
plausible ASR alternative causes `f` to cross a safe-action boundary in an
unsafe direction, or if human reviewers judge the ASR-induced action lower than
expected safe action. This is potential harm / policy-violation proxy, not
actual fraud harm. Main text can use "safety-relevant decision instability" or
"unsafe downrouting risk" more often than "harm." If the title keeps
"dangerous," the first page must operationalize the term.

### 23. Human Reviewer Label Definition

The manuscript currently says reviewers label risk atoms, decision-change,
expected safe action, confidence, per-model assessment fields, and per-row
timing, but final protocol should be more exact. Reviewers should see
de-identified local transcript/audio context, ASR hypothesis or model-level
transcript, and task rubric; they should not see CEIS score, SRES score,
selection provenance, model name, thresholds, policy replay result, or other
reviewer labels. Tasks should include semantic risk, ASR-induced decision
change, critical atom, expected safe action, and annotation confidence. If
reviewers see model outputs, they may be influenced by fluency, model quality,
or risk prompts. Mitigation: blind model identity, randomize model order, hide
metric scores, avoid CEIS-generated atom hints as reviewer cues, and consider a
two-pass annotation flow.

### 24. Clustered Dependence

Primary CI should use row-clustered bootstrap: resample audio rows and retain
all model-level assessments within each row. AUC should use bootstrap
percentile CI. F1, precision, recall, and FN should be recomputed in each
bootstrap sample if threshold is fixed; if reporting best-threshold F1,
threshold selection must occur inside bootstrap or use an independent dev
threshold. Policy budget should similarly resample rows and recompute trigger
rate, severe remaining, and triggers per elimination. Fixed-budget frontier
should keep requested budget fixed and recompute residual counts. Leave-one-row
out sensitivity should be appendix evidence for whether a small number of
positive rows dominate results.

### 25. Sentence Reviewer Should Remember

In high-stakes ASR, the unit of evaluation should shift from transcript
similarity to decision stability under plausible transcript alternatives
because the downstream risk is often carried by small decision atoms whose
substitutions can leave WER/CER low while changing the safe action.

## Round 1 Derived Blocking Gates

1. Regenerate final predictor, recovery, and CEIS ablation tables on the full
   completed selected-300 dual-reviewer surface.
2. Remove or explicitly demote all 30-row / 90-assessment main-text result
   claims.
3. Add selection-circularity sensitivity checks.
4. Add source-specific variant coverage and reject-reason aggregate counts.
5. Define `f` as a versioned rule-based policy abstraction and distinguish
   policy-conditioned instability from policy optimality.
6. Treat SRES as the strongest baseline and move weak confidence-only material
   to appendix unless calibrated confidence is available.
7. Add a synthetic or redacted executable CEIS scoring demo for reviewer
   auditability.
8. Decompose residual unsafe downrouting cases before claiming broad safety
   reduction.
9. Decide whether the low-WER title is directly supported by final
   human-audit subset evidence; soften the title if not.

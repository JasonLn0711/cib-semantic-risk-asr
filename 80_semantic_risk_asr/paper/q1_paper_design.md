# Q1 Paper Design

## Working Title

When Low WER Becomes Dangerous: Counterfactual Semantic Risk Detection for
Speech-Driven Decision Systems

Alternative titles:

1. Beyond WER: Counterfactual Decision-Stability Evaluation for ASR in
   High-Stakes Call-Center Conversations
2. Decision-Stable ASR: Detecting and Recovering High-Risk Transcription Errors
   in Anti-Fraud Call-Center Conversations
3. From Transcript Accuracy to Decision Safety: Counterfactual Risk Evaluation
   for ASR

## Core Hook

> A transcript is unsafe when a plausible ASR alternative changes the decision.

Traditional WER/CER asks how different two transcripts are. Semantic metrics
ask whether meaning is preserved. CDS-ASR asks a sharper question:

> If the ASR could plausibly have heard a neighboring transcript, would the
> downstream decision flip?

This is the paper's main upgrade from SRA-ASR. SRES remains useful as a
semantic-risk baseline, but the protagonist is now counterfactual decision
stability.

## Rao-Style Research Logic

The paper should not start from the model. It should start from a real-world
failure that makes the reader care.

1. Speech-driven systems increasingly turn conversations into operational
   decisions.
2. In high-stakes domains, a small ASR error can land on a decision atom:
   negation, amount, action, actor, time, intent, or scam pattern.
3. Existing ASR evaluation and correction methods improve transcript similarity
   or semantic similarity, but do not directly test whether the downstream
   decision is stable under plausible ASR alternatives.
4. We propose CDS-ASR, a counterfactual decision-stability framework.
5. Experiments show whether CEIS detects unsafe transcripts and whether
   automatic constrained recovery reduces unsafe down-routing.

The manuscript should be steady, but it needs a clear reason to read it:

> Low WER is dangerous when plausible ASR alternatives produce different
> downstream decisions.

## Real-World Pain Point

Contact-center AI systems already use speech transcripts as operational input.
Amazon Connect Customer Contact Lens documentation describes conversational
analytics across voice, chat, and email using NLP for sentiment analysis, issue
detection, and automatic categorization. The AWS conversational analytics page
also describes transcript-based summaries, categories, compliance monitoring,
and real-time alerts.

Anti-fraud calls make this problem concrete. Taiwan's National Police Agency
165 anti-fraud hotline records incident details and provides information to
victims. In the United States, the FBI's 2025 IC3 reporting context described
`1,008,597` total complaints, approximately `453,000` cyber-enabled fraud
complaints, and losses exceeding `$17.7 billion`.

These systems create a safety-critical dependency:

```text
I did not transfer money.
-> I transferred money.
```

The transcript may be nearly correct at the character or word level, while the
decision state is reversed. This is not only a transcription-accuracy problem.
It is a decision-stability problem.

## Literature Starting Point

Existing work already supports the premise that WER is insufficient.

- Kim et al. propose Semantic Distance because WER measures literal transcript
  difference and may not reflect downstream semantic correctness.
- Rugayan et al. report that WER does not encode error severity and that
  semantic metrics can better align with human perception and downstream NLP
  performance.
- Naderi et al. investigate LLM-based post-hoc ASR correction with
  confidence-based filtering.

These are the right neighbors, but their remaining limitation is important:

> They still primarily evaluate or repair the transcript. They do not directly
> test whether plausible transcript alternatives change the downstream
> high-stakes decision.

## Research Question

Main RQ:

> Can counterfactual decision-stability evaluation better identify unsafe ASR
> outputs than transcript-similarity metrics in high-stakes anti-fraud
> call-center conversations?

Sub-questions:

- RQ1: Can WER/CER, semantic distance, or confidence reliably detect downstream
  escalation-label changes?
- RQ2: Does CEIS better detect decision-unstable ASR outputs than WER/CER,
  semantic metrics, confidence, or SRES?
- RQ3: Can automatic constrained recovery reduce unsafe down-routing without
  using human review as the method?

## Proposed Framework: CDS-ASR

CDS-ASR means:

> Counterfactual Decision-Stability ASR.

Pipeline:

```text
audio
-> ASR transcript + confidence / n-best / timestamps
-> risk atom extraction
-> ASR counterfactual generator
-> downstream decision model
-> CEIS
-> constrained re-decoding / decision interval / conservative action
```

### Module 1: Risk Atom Schema

Risk atoms are transcript spans that can change a downstream decision.

| Risk atom | Examples | Risk |
| --- | --- | --- |
| Negation | has / has not, did / did not | Reverses event state. |
| Amount | 30k / 300k | Changes loss severity. |
| Action | transfer / ask / withdraw / report | Changes case stage. |
| Actor | bank / police / family / service agent | Changes scam-pattern interpretation. |
| Time | today / yesterday / next week | Changes urgency. |
| Intent | I want to report / I only want to ask | Changes routing. |
| Uncertainty | maybe / sure / not sure | Changes confidence and label interval. |
| Scam pattern | investment / fake police / recurring-payment cancellation | Changes downstream case type. |

Contribution 1:

> A risk atom schema for high-stakes call-center ASR decisions.

### Module 2: ASR Counterfactual Generator

The system generates plausible transcript alternatives around unstable
decision-critical spans.

Sources:

1. Acoustic ambiguity: confidence, token log probability, n-best alternatives,
   and timestamp-aligned unstable spans.
2. Mandarin phonetic confusion: homophones, near-homophones, tones, number
   units, and short function words.
3. Fraud-domain ontology: money amounts, payment actions, caller identity,
   account status, time, intent, and scam type.

Example:

```text
Top-1:
I transferred 30,000 today.

Counterfactual variants:
I transferred 300,000 today.
I did not transfer 30,000 today.
I only asked about transferring 30,000 today.
I transferred 30,000 yesterday.
```

Contribution 2:

> A counterfactual ASR variant contract that produces acoustically and
> semantically plausible decision alternatives instead of generic paraphrases.

### Module 3: Counterfactual Escalation Instability Score

CEIS measures the maximum decision-flip risk among plausible alternatives.

Formula:

```text
CEIS(x) = max over v in V(x) [
    P(v | audio) * RiskAtomWeight(v) * DecisionDistance(f(x), f(v))
]
```

Where:

- `x`: ASR top-1 transcript;
- `v`: plausible counterfactual transcript variant;
- `P(v | audio)`: acoustic plausibility;
- `RiskAtomWeight(v)`: risk weight for the affected atom;
- `DecisionDistance`: distance between downstream escalation labels.

Contribution 3:

> CEIS reframes ASR evaluation from transcript similarity to downstream
> decision stability.

### Module 4: Automatic Recovery

The paper must not use human review as the proposed recovery method. Recovery is
automatic and machine-bounded.

Path:

```text
high-CEIS span
-> span-level forced alignment
-> constrained re-decoding over risk-atom grammar
-> ASR ensemble arbitration
-> decision interval estimation
-> conservative automatic action
```

Examples:

- Amount span: constrain decoding to amount grammar such as `3,000`, `30,000`,
  `300,000`.
- Negation span: constrain decoding to variants such as `has`, `has not`,
  `already`, `not yet`.
- Decision interval: if plausible variants range from `review` to
  `critical_escalation`, do not output `no_escalation`.

Contribution 4:

> An automatic recovery policy that uses acoustic evidence and decision
> intervals rather than manual review as the method.

## Experiment Design

Only four experiments belong in the first paper.

### Experiment 1: ASR Baseline And Risk-Atom Error Profile

Purpose:

Establish ordinary ASR performance, then show which models are stable or
unstable on decision atoms.

Models:

| Model | Role |
| --- | --- |
| `openai/whisper-small` | smoke baseline |
| `openai/whisper-large-v2` or LoRA variant | main ASR baseline |
| `MediaTek-Research/Breeze-ASR-25` | Mandarin/Taiwanese Mandarin domain alternative |
| `MediaTek-Research/Breeze-ASR-26` | optional Taigi/Taiwanese Hokkien stress test; not the main Mandarin baseline |

Metrics:

- WER;
- CER;
- risk atom error rate;
- negation flip rate;
- amount distortion rate;
- action confusion rate.

### Experiment 2: Counterfactual Generation Quality

Purpose:

Show that generated alternatives are plausible ASR alternatives around
decision-critical spans, not arbitrary paraphrases.

Sample target:

- First pass: the reviewed 15-row JANUS decision-stability pilot.
- Scale-up pass: `300-500` high-stakes utterances only after the 15-row pilot
  produces a usable CEIS/downstream-instability signal.

Metrics:

- counterfactual coverage;
- plausible variant recall;
- risk atom coverage;
- acoustic plausibility score distribution.

### Experiment 3: Metric Comparison

Prediction target:

```text
downstream label changed = yes/no
```

Predictors:

| Predictor | Role |
| --- | --- |
| WER | surface baseline |
| CER | surface baseline |
| semantic distance / ASD | semantic baseline if implemented |
| confidence score | confidence baseline if available |
| SRES | semantic-risk baseline |
| CEIS | proposed decision-stability metric |

Evaluation:

- AUC;
- F1;
- Recall@HighRisk;
- Precision@RecoveryBudget;
- Critical Miss Rate;
- False Safe Rate.

Evidence tables should include:

- low WER + high CEIS;
- low semantic distance + high CEIS;
- high confidence + high CEIS.

### Experiment 4: Automatic Recovery Evaluation

Purpose:

Show that the framework does not only diagnose instability; it reduces unsafe
down-routing automatically.

Downstream task:

> scam escalation classification

Labels:

- `no_escalation`;
- `review`;
- `priority_review`;
- `critical_escalation`.

Conditions:

| Condition | Meaning |
| --- | --- |
| No recovery | ASR transcript directly enters downstream classifier. |
| Confidence-only LLM correction | LLM correction triggered by low confidence. |
| SRES-triggered recovery | Semantic-risk baseline trigger. |
| CDS-ASR constrained re-decoding | Re-decode high-CEIS spans with risk-atom grammar. |
| CDS-ASR + decision interval | Use decision interval and conservative automatic action. |

Metrics:

| Metric | Meaning |
| --- | --- |
| Critical Miss Rate | High-risk cases incorrectly routed low. |
| Unsafe Down-Routing Rate | Any decision interval that includes high risk but outputs low risk. |
| Over-Escalation Rate | Conservative actions that escalate unnecessarily. |
| Automatic Recovery Budget | Number of spans/cases re-decoded. |
| Machine Abstention Rate | Cases where the machine returns an interval instead of a single label. |
| Decision Stability Gain | Reduction in decision flips after recovery. |
| compute cost | Added cost for constrained recovery. |

Desired result:

> CDS-ASR reduces critical misses and unsafe down-routing more effectively than
> transcript-centered baselines, without making human review the method.

## Paper Contributions

1. We define a risk atom schema for high-stakes call-center ASR decisions.
2. We propose CEIS, a counterfactual decision-stability metric for ASR.
3. We show that CEIS detects unsafe ASR outputs missed by WER/CER, semantic
   metrics, confidence, and SRES.
4. We propose an automatic constrained recovery policy using re-decoding,
   ensemble arbitration, decision intervals, and conservative machine action.

## Suggested Paper Structure

1. Introduction
2. Related Work
3. Problem Formulation
4. CDS-ASR Method
5. Experiments
6. Results
7. Discussion
8. Limitations
9. Conclusion

## Target Journals

Best initial fit:

1. Expert Systems with Applications
2. Computer Speech & Language
3. Speech Communication
4. Information Processing & Management

ESWA is the most natural first target because the paper is applied AI,
decision-support, risk scoring, and empirical framework oriented. Computer
Speech & Language becomes stronger if the acoustic counterfactual and
constrained re-decoding implementation is mature.

## Four-Week Execution Plan

### Week 1

- Freeze risk atom schema.
- Complete the reviewed 15-row JANUS pilot gate. Local status on 2026-05-25:
  complete.
- Run or collect NeMo/Whisper/Breeze hypotheses on the same 15 rows. NeMo
  Curator produced a joinable CPU pilot output with WER/CER fields; it should
  be treated as an output-contract check because aggregate CER is still too
  high for quality comparison. Whisper small has passed the 1-row smoke test
  and the full 15-row hypothesis pass.
- Build SRES, CEIS, and downstream-impact metric inputs for the pilot. Local
  status on 2026-05-25: complete for `whisper_small_15_row_baseline`; still
  needs Whisper large-v2 and Breeze-ASR-25 before the model-comparison gate is
  considered complete.

### Week 2

- Score WER/CER/SRES/CEIS.
- Build low-WER/high-CEIS case table.
- Build low-semantic-distance/high-CEIS case table if semantic distance is
  implemented.
- Decide whether the pilot supports expansion to `300-500` high-stakes
  segments.

### Week 3

- Generate the `300-500` high-stakes sample list only if Week 2 passed the
  signal gate.
- Create downstream escalation labels.
- Compare WER/CER/semantic metrics/SRES/CEIS.
- Produce AUC/F1/Recall@HighRisk/Critical Miss Rate table.

### Week 4

- Run automatic recovery experiment.
- Draft introduction, method, and experiment tables.
- Decide ESWA vs Computer Speech & Language.

## Introduction Skeleton

High-stakes call-center systems increasingly transform speech into operational
decisions, including classification, summarization, routing, escalation, and
compliance monitoring. Commercial contact-center AI systems already analyze
voice conversations through transcripts, sentiment analysis, issue detection,
automatic categorization, summaries, and real-time alerts. In anti-fraud
settings, this creates a safety-critical dependency: a small transcription
error can change whether a case is treated as routine, reviewed, prioritized,
or escalated.

Existing ASR evaluation remains largely transcript-centered. WER and CER
measure surface edit distance, while recent semantic metrics improve evaluation
by estimating meaning preservation. However, high-stakes decisions often depend
on a small set of decision-critical atoms, such as negation, amount, action,
actor, time, and intent. A transcript may remain semantically close to the
reference while still reversing a downstream decision.

We propose Counterfactual Decision-Stability ASR, a framework that evaluates
ASR outputs by testing whether plausible transcription alternatives change
downstream decisions. Instead of asking only how similar a transcript is to the
reference, CDS-ASR asks whether the decision remains stable under acoustically
and semantically plausible ASR variants. We introduce Counterfactual Escalation
Instability Score, risk-atom-guided counterfactual generation, and automatic
span-level recovery through constrained re-decoding and decision interval
estimation.

## Citation Seed

- AWS Contact Lens / Amazon Connect Customer documentation:
  https://docs.aws.amazon.com/connect/latest/adminguide/analyze-conversations.html
- AWS conversational analytics:
  https://aws.amazon.com/products/connect/customer/conversational-analytics/
- Taiwan National Police Agency 165 anti-fraud hotline:
  https://www.npa.gov.tw/en/app/artwebsite/view?id=8035&module=artwebsite&serno=ed2427e1-de0a-4f6f-8f68-8f83b604e89b
- FBI cyber-enabled fraud / IC3 press release:
  https://www.fbi.gov/news/press-releases/cryptocurrency-and-ai-scams-bilk-americans-of-billions
- Kim et al. (2021), "Semantic Distance: A New Metric for ASR Performance
  Analysis Towards Spoken Language Understanding",
  https://www.isca-archive.org/interspeech_2021/kim21e_interspeech.html
- Rugayan et al. (2023), "Perceptual and Task-Oriented Assessment of a Semantic
  Metric for ASR Evaluation",
  https://www.isca-archive.org/interspeech_2023/rugayan23_interspeech.html
- Naderi et al. (2024), "Towards interfacing large language models with ASR
  systems using confidence measures and prompting",
  https://www.isca-archive.org/interspeech_2024/naderi24_interspeech.html

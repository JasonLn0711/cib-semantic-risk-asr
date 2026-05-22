# Q1 Paper Design

## Working Title

Beyond WER: Semantic-Risk-Aware Evaluation and Recovery for ASR in High-Stakes
Call-Center Conversations

Alternative sharper title:

When Low WER Still Fails: Semantic-Risk-Aware ASR Evaluation for High-Stakes
Conversational Decision Support

## Core Hook

> A transcript can be nearly correct and still operationally dangerous.

Traditional WER/CER cannot tell whether an ASR error will cause a high-stakes
downstream decision failure. This paper proposes a semantic-risk-aware ASR
evaluation and recovery framework to identify, rank, and repair transcription
errors that matter for subsequent judgment.

Framing guardrail:

- Use `framing_guardrail.md` to keep the paper from sliding back into a plain
  Whisper/LoRA/CER-improvement story.

## Rao-Style Research Logic

The paper should not start from the model. It should start from the real-world
failure.

1. A real or foreseeable operational problem is emerging.
2. Existing methods solve only part of it.
3. Their remaining gap creates practical risk.
4. We propose a focused method that directly targets that gap.
5. Experiments show whether the method reduces decision-critical failures under
   realistic constraints.

The manuscript should be steady, but it needs a clear reason to read it:

> Low WER can still be unsafe when the remaining errors hit decision-critical
> meaning.

## Real-World Pain Point

ASR is increasingly used as the text layer for high-stakes speech workflows:
medical intake, customer service, financial dispute handling, investigation,
and anti-fraud call review.

Many downstream systems treat ASR transcripts as the basis for classification,
summarization, risk scoring, routing, or escalation. This creates an operational
risk:

```text
I did not transfer money.
-> I transferred money.
```

The transcript may be nearly correct at the character or word level, but the
decision state is reversed. This is not just a transcription-accuracy problem.
It is a downstream decision-risk problem.

## Literature Starting Point

Existing work already supports the premise that WER is insufficient for
semantic or downstream evaluation.

- Kim et al. propose Semantic Distance because WER measures literal transcript
  difference and may not reflect downstream semantic correctness.
- Rugayan et al. report that WER does not encode error severity and that
  semantic metrics can better align with human perception and downstream NLP
  performance.
- Ruan et al. frame ASR errors as upstream noise that can degrade spoken
  language understanding.
- Naderi et al. show that LLM-ASR interfaces can use confidence and prompting,
  but this still leaves the question of which errors are decision-critical.

The gap for this paper is narrower:

> Existing semantic metrics and correction methods do not directly make
> high-stakes downstream decision failure the ASR evaluation target.

## Research Question

Main RQ:

> Can semantic-risk-aware ASR evaluation better identify decision-critical
> transcription failures than conventional WER/CER in high-stakes call-center
> conversations?

Sub-questions:

- RQ1: Can WER/CER reliably identify downstream escalation-label changes?
- RQ2: Does a Semantic Risk Score better detect high-risk ASR failures?
- RQ3: Can risk-triggered recovery reduce high-risk misses without making human
  review workload explode?

## Proposed Framework: SRA-ASR

SRA-ASR means:

> Semantic-Risk-Aware ASR Evaluation and Recovery.

Pipeline:

```text
audio
-> ASR transcript
-> decision-critical error detection
-> Semantic Risk Score
-> downstream escalation impact
-> risk-triggered recovery
```

### Module 1: Decision-Critical Error Taxonomy

The taxonomy defines which ASR errors are dangerous in high-stakes calls.

| Category | Examples | Risk |
| --- | --- | --- |
| Negation | has / has not, did / did not | Reverses event state. |
| Amount | 30k / 300k | Changes loss severity. |
| Action | transfer / ask / withdraw / report | Changes case stage. |
| Actor | bank / police / family / service agent | Changes scam-pattern interpretation. |
| Time | today / yesterday / next week | Changes urgency. |
| Intent | I want to report / I only want to ask | Changes routing. |
| Uncertainty | maybe / sure / not sure | Changes reviewer confidence. |
| Scam pattern | investment / fake police / recurring-payment cancellation | Changes downstream case type. |

Contribution 1:

> A decision-critical ASR error taxonomy for high-stakes call-center
> conversations.

### Module 2: Semantic Risk Score

Start with an interpretable formula:

```text
SRS = sum(type_weight * severity * downstream_impact)
```

Optional extension:

```text
SRS = sum(type_weight * severity * downstream_impact * confidence_penalty)
```

Where:

- `type_weight`: risk weight by category;
- `severity`: 0-5 semantic corruption severity;
- `downstream_impact`: 0-3 likely effect on downstream escalation;
- `confidence_penalty`: optional penalty for dangerous high-confidence errors.

Contribution 2:

> Semantic Risk Score, an interpretable metric that complements WER/CER by
> weighting transcription errors by decision consequence.

### Module 3: Risk-Triggered Recovery

When SRS crosses a threshold, the system should not directly trust the
transcript. It triggers one of:

- targeted re-listening;
- human confirmation;
- alternative transcript comparison;
- low-confidence or semantic-risk warning;
- priority review.

Contribution 3:

> A risk-triggered recovery policy that reduces high-risk missed escalation
> while controlling reviewer workload.

## Experiment Design

Only four experiments belong in the first paper.

### Experiment 1: ASR Baseline

Purpose:

Establish ordinary ASR performance. This is the baseline, not the paper's main
contribution.

Models:

| Model | Role |
| --- | --- |
| `openai/whisper-small` | smoke baseline |
| `openai/whisper-large-v2` or LoRA variant | main ASR baseline |
| `MediaTek-Research/Breeze-ASR-25` | Mandarin/Taiwanese Mandarin domain alternative |

Metrics:

- WER;
- CER.

Outputs:

- `predictions.tsv`;
- `metrics.csv`;
- `error_samples.tsv`.

### Experiment 2: Semantic-Risk Annotation

Purpose:

Create the core research dataset.

Sample target:

- 300-500 utterances.

Sampling plan:

- random samples;
- high-WER/CER samples;
- low-WER/CER samples containing risk terms;
- samples containing negation, amount, action, actor, time, intent,
  uncertainty, or scam-pattern terms.

Annotation fields:

| Field | Meaning |
| --- | --- |
| reference transcript | human/canonical transcript |
| ASR transcript | model output |
| error type | taxonomy category |
| decision-critical | yes/no |
| severity | 0-5 |
| downstream impact | 0-3 |
| downstream label changed | yes/no |
| recovery action | none / human confirmation / targeted re-listening / priority review |
| reviewer note | why the error matters |

Quality control:

- double-code a 20% subset if possible;
- report Cohen's kappa or Krippendorff's alpha if a second annotator is
  available.

### Experiment 3: WER/CER vs SRS

Purpose:

Test whether conventional metrics identify decision-critical ASR failures.

Prediction target:

```text
downstream label changed = yes/no
```

Predictors:

| Predictor | Role |
| --- | --- |
| WER | baseline |
| CER | baseline |
| semantic distance / ASD | semantic baseline if implemented |
| confidence score | confidence baseline if available |
| SRS | proposed metric |

Evaluation:

- AUC;
- F1;
- Recall@HighRisk;
- Precision@RecoveryBudget;
- Spearman correlation.

Expected pattern:

```text
SRS > semantic distance > WER/CER
```

This does not need to claim that SRS is universally better. The narrower claim
is enough:

> SRS is better suited for detecting high-risk ASR errors that can change
> downstream escalation decisions.

### Experiment 4: Recovery Evaluation

Purpose:

Show that the framework does not only diagnose failure; it also helps recover.

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
| Confidence-only recovery | Low-confidence spans trigger review. |
| SRS-triggered recovery | High semantic-risk spans trigger targeted review/recovery. |

Metrics:

| Metric | Meaning |
| --- | --- |
| high-risk miss rate | How many high-risk cases were missed. |
| downstream F1 | Escalation classification performance. |
| reviewer workload | Percent of cases/spans requiring review. |
| recovery precision | Whether triggered reviews were actually useful. |
| workload-adjusted recall | High-risk detection under fixed review budget. |

Desired result:

> SRS-triggered recovery lowers high-risk miss rate while adding less workload
> than broad review or naive confidence-only recovery.

## Paper Contributions

1. We define a decision-critical ASR error taxonomy for high-stakes
   call-center conversations.
2. We propose Semantic Risk Score, an interpretable metric that weights ASR
   errors by semantic category, severity, and downstream decision impact.
3. We show that SRS-triggered recovery can reduce high-risk missed escalation
   compared with WER/CER or confidence-only baselines while controlling
   reviewer workload.

## Suggested Paper Structure

1. Introduction
2. Related Work
3. Problem Formulation
4. Method
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
decision-support, risk-scoring, and empirical framework oriented.

## Four-Week Execution Plan

### Week 1

- Freeze taxonomy.
- Generate 300-500 sample list.
- Run or collect Whisper/Breeze predictions.
- Create annotation sheet.

### Week 2

- Complete first annotation round.
- Compute WER/CER/SRS.
- Build low-WER/high-SRS case table.

### Week 3

- Create downstream escalation labels.
- Compare WER/CER/SRS.
- Produce AUC/F1/Recall@HighRisk table.

### Week 4

- Run recovery experiment.
- Draft introduction, method, and experiment tables.
- Decide ESWA vs Computer Speech & Language.

## Citation Seed

- Kim et al. (2021), "Semantic Distance: A New Metric for ASR Performance
  Analysis Towards Spoken Language Understanding",
  https://www.isca-archive.org/interspeech_2021/kim21e_interspeech.html
- Rugayan et al. (2023), "Perceptual and Task-Oriented Assessment of a Semantic
  Metric for ASR Evaluation",
  https://www.isca-archive.org/interspeech_2023/rugayan23_interspeech.html
- Ruan et al. (2020), "Towards an ASR error robust spoken language
  understanding system",
  https://www.amazon.science/publications/towards-an-asr-error-robust-spoken-language-understanding-system
- Naderi et al. (2024), "Towards interfacing large language models with ASR
  systems using confidence measures and prompting",
  https://www.isca-archive.org/interspeech_2024/naderi24_interspeech.html

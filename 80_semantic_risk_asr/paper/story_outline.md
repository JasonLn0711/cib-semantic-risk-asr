# Paper Story Outline

Canonical detailed design:

- `q1_paper_design.md`

## Proposed Title

Beyond WER: Semantic-Risk-Aware Evaluation and Recovery for ASR in High-Stakes
Call-Center Conversations

## One-Sentence Claim

Conventional WER/CER can miss decision-critical ASR failures in high-stakes
calls, so we propose Semantic Risk-Weighted ASR evaluation and a risk-triggered
recovery policy that identifies and mitigates transcription errors likely to
affect downstream escalation.

## Story Line

### 1. Real-World Problem

ASR is increasingly used as the text layer for high-stakes speech workflows:
medical intake, customer service, investigation, financial dispute handling, and
anti-fraud call review.

The operational risk is that downstream systems often treat ASR output as the
basis for summarization, classification, risk scoring, or escalation. Low WER or
CER does not guarantee semantic safety. A small error such as changing "already
transferred" into "not transferred" can reverse the downstream decision state.

### 2. Existing Work

Prior work already shows that WER is not always a good indicator for downstream
semantic understanding. Kim et al. propose Semantic Distance because WER only
measures literal correctness and may not capture semantic correctness for
downstream NLU tasks. Rugayan et al. similarly argue that WER does not report
error severity and show semantic metrics can better reflect human perception
and downstream NLP performance. Ruan et al. discuss how ASR errors can degrade
spoken-language-understanding systems.

### 3. Gap

Existing semantic ASR metrics and ASR-robust SLU methods improve the evaluation
or robustness of downstream language understanding, but they do not directly
make high-risk decision failure the evaluation target.

For high-stakes calls, the central question is not only:

> Is the hypothesis semantically close to the reference?

It is:

> Which transcript errors can change escalation, routing, or human review?

### 4. Proposed View

We propose Semantic Risk-Weighted ASR:

```text
audio -> transcript -> semantic-risk error -> downstream consequence -> recovery action
```

The core idea is that ASR errors should not be weighted equally. Errors on
negation, amount, action, actor, intent, time, uncertainty, and scam-pattern
terms can matter more than ordinary wording differences.

### 5. Contributions

1. Decision-critical ASR error taxonomy for high-stakes call-center
   conversations.
2. Semantic Risk Error Score (SRES), which combines error type, risk weight,
   severity, and downstream impact.
3. Empirical comparison of WER/CER and SRES for identifying downstream scam
   escalation failures.
4. Risk-triggered recovery policy that flags targeted human confirmation,
   re-listening, or priority review for decision-critical transcript spans.

## Main Research Question

Can semantic-risk-aware ASR evaluation better identify decision-critical
transcription failures than conventional WER/CER in high-stakes call-center
conversations?

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

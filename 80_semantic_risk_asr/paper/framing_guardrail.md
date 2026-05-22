# Framing Guardrail

## Do Not Write A Plain ASR Paper

This paper must not be framed as:

- Whisper fine-tuning;
- LoRA on a domain corpus;
- CER/WER improvement by a small margin;
- Taiwan Mandarin benchmark construction;
- post-processing for better transcript quality;
- SRES-only risk scoring without a decision-stability test;
- human review as the proposed recovery method.

That framing makes the work look like an ordinary ASR or quality-control paper.
Generic ASR is already strong, benchmark fatigue is real, and reviewers are
unlikely to care about another small transcription-accuracy improvement unless
the work changes the decision problem.

## Correct Frame

The paper is about:

> Decision stability under plausible ASR alternatives in high-stakes
> speech-driven decision systems.

The hook is:

> A transcript is unsafe when a plausible ASR alternative changes the decision.

ASR is a subsystem. The protagonist is not the model and not the transcript. The
protagonist is the downstream decision that becomes unstable when a small,
acoustically plausible transcript difference lands on a decision-critical atom.

## Bad Version

```text
We use Whisper-large-v2 with LoRA on the 165 corpus and improve CER by 2.3%.
```

This is not enough. It sounds like ordinary transcription optimization.

## Also Not Enough

```text
We compute a semantic-risk score and send high-risk cases to human review.
```

This is closer, but it still frames the paper as risk triage plus manual
inspection. The upgraded paper must show an automatic decision-stability test
and automatic recovery path.

## Good Version

```text
Existing ASR evaluation assumes that transcription quality can be judged by
surface similarity or general semantic similarity. In high-stakes speech-driven
decision systems, however, a transcript can remain similar while a plausible
alternative transcript flips the downstream decision. We propose
Counterfactual Decision-Stability ASR, which evaluates ASR by generating
acoustically and semantically plausible transcript variants, measuring whether
they change downstream escalation decisions, and recovering high-risk spans
through constrained re-decoding and decision interval estimation.
```

## Introduction Rule

The first two pages should prioritize:

- real-world growth of speech-to-decision contact-center analytics;
- anti-fraud call handling as a high-stakes domain;
- why transcript similarity is weaker than decision stability;
- existing WER/CER, semantic metric, and LLM correction work;
- the gap: prior methods improve transcript evaluation or correction, but do
  not test whether plausible transcript alternatives flip the decision;
- CDS-ASR as a decision-stability framework.

ASR should enter as the upstream subsystem where this problem becomes concrete.
Do not start the paper with Whisper, LoRA, or model architecture.

## What Reviewers Should Remember

The one memorable line:

> A transcript is unsafe when a plausible ASR alternative changes the decision.

The one contribution frame:

> We evaluate ASR by whether high-stakes decisions remain stable under
> acoustically and semantically plausible transcript alternatives.

## Investment Rule

Do not invest the first paper in making transcription slightly more accurate.
Invest it in proving that plausible transcript alternatives can change
downstream escalation, and that automatic constrained recovery reduces unsafe
down-routing without making human review the method.

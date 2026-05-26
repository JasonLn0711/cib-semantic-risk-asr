# Framing Guide

## Preferred Paper Identity

This paper is best framed as:

> Decision stability under plausible ASR alternatives in high-stakes
> speech-driven decision systems.

Whisper fine-tuning, LoRA, WER/CER, Taiwan Mandarin data handling, SRES, and
human review are supporting evidence layers. They help establish the quality and
scope of the study while the main claim stays focused on downstream decision
stability.

## Core Frame

The memorable hook is:

> A transcript is unsafe when a plausible ASR alternative changes the decision.

ASR is a subsystem. The protagonist is not the model and not the transcript. The
protagonist is the downstream decision that changes when a small,
acoustically plausible transcript difference lands on a decision-critical atom.

## Supporting-Evidence Version

```text
Whisper-large-v2, Breeze-ASR, and fine-tuned variants provide comparable ASR
hypotheses for testing whether transcript alternatives change downstream
escalation decisions.
```

This version uses model performance as an input to the CDS-ASR argument.

## Decision-Stability Version

Use this as the preferred article voice:

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

- citation-backed real-world growth of speech-to-decision contact-center
  analytics;
- anti-fraud call handling as a high-stakes domain;
- why transcript similarity is weaker than decision stability;
- existing WER/CER, semantic metric, and LLM correction work with fair
  citations;
- the gap: prior methods improve transcript evaluation or correction, while
  CDS-ASR directly tests whether plausible transcript alternatives flip the
  decision;
- CDS-ASR as a decision-stability framework.

ASR should enter as the upstream subsystem where this problem becomes concrete.
Start the paper with the real-world decision problem, then introduce Whisper,
LoRA, Breeze-ASR, or model architecture as evidence-producing components.

## Attention-Led Story Rule

Use this sequence when drafting the introduction, abstract, talk track, or
reviewer handoff:

```text
real-world or credible near-future problem
-> citation-backed evidence
-> current solution landscape with citations
-> evidence-backed remaining gap
-> CDS-ASR as the new viewpoint
-> how CDS-ASR addresses the opening problem
-> scope controls and next validation path
```

The critique of prior work should be constructive: first name what each method
enables, then identify the remaining decision-stability question this paper
answers.

## What Reviewers Should Remember

The one memorable line:

> A transcript is unsafe when a plausible ASR alternative changes the decision.

The one contribution frame:

> We evaluate ASR by whether high-stakes decisions remain stable under
> acoustically and semantically plausible transcript alternatives.

## Investment Rule

Invest the first paper in proving that plausible transcript alternatives can
change downstream escalation, and that automatic constrained recovery reduces
unsafe down-routing while human review remains the evaluation and governance
layer.

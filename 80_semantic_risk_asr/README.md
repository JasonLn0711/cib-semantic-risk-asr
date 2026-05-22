# Semantic-Risk-Aware ASR

This is the single research axis for the repo.

The short-term paper target is not "fine-tune Whisper." The target is:

> In high-stakes call-center conversations, conventional WER/CER cannot tell
> whether ASR errors will cause downstream decision failure. We propose a
> semantic-risk-aware ASR evaluation and recovery framework that identifies,
> ranks, and repairs transcription errors that matter for subsequent judgment.

## Working Title

Beyond WER: Semantic-Risk-Aware Evaluation and Recovery for ASR in High-Stakes
Call-Center Conversations

## Core Research Question

Can semantic-risk-aware ASR evaluation better identify decision-critical
transcription failures than conventional WER/CER in high-stakes call-center
conversations?

## Scope

In scope:

- decision-critical ASR error taxonomy;
- Semantic Risk Error Score (SRES);
- one downstream task: scam escalation classification;
- one recovery mechanism: risk-triggered human confirmation or targeted
  re-listening;
- comparison against WER/CER and confidence-only recovery.

Out of scope for this paper:

- broad institutional simulation;
- generic AI governance theory;
- full real-time agent systems;
- multi-modal model benchmarking;
- large reviewer queue simulation;
- claiming ASR state of the art.

## Pipeline

```text
audio
-> ASR transcript
-> semantic-risk error
-> downstream consequence
-> recovery action
```

`60_whisper_asr_finetuning/` provides ASR outputs. This folder defines what
counts as a dangerous ASR error and how to evaluate whether recovery helps.

## Directory Contract

| Path | Purpose |
| --- | --- |
| `taxonomy/` | Decision-critical token/error taxonomy and risk weights. |
| `annotation/` | Human annotation guideline and sample annotation sheet. |
| `scoring/` | SRES computation and WER/CER-vs-SRES comparison scripts. |
| `downstream/` | Scam escalation classification task definition and evaluation script. |
| `recovery/` | Risk-triggered review/clarification policy. |
| `paper/` | Story outline, citation seed, and experiment plan. |

## First Experiment Package

Minimum viable paper experiment:

1. Run baseline ASR systems and store predictions under `70_experiments/`.
2. Sample 300-500 high-stakes call segments.
3. Annotate decision-critical ASR errors using `annotation/annotation_guideline.md`.
4. Compute SRES with `scoring/semantic_risk_score.py`.
5. Compare WER/CER against SRES for predicting downstream escalation failures.
6. Test risk-triggered recovery against no recovery and confidence-only recovery.

## Canonical Paper Design

Use `paper/q1_paper_design.md` as the durable source for the Q1 paper story,
method, experiment design, target journals, and four-week execution plan.

Use `paper/framing_guardrail.md` before writing abstracts, introductions,
cover letters, or repo summaries. It defines what this paper is not: a plain
ASR fine-tuning or small-CER-improvement paper.

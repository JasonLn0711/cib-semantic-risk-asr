# Counterfactual Decision-Stability ASR

This is the single research axis for the repo.

The short-term paper target is no longer only "semantic-risk-aware ASR." The
upgraded claim is:

> A transcript is unsafe when a plausible ASR alternative changes the downstream
> decision.

## Working Title

When Low WER Becomes Dangerous: Counterfactual Semantic Risk Detection for
Speech-Driven Decision Systems

Alternative stable title:

Beyond WER: Counterfactual Decision-Stability Evaluation for ASR in
High-Stakes Call-Center Conversations

## Core Research Question

Can ASR safety in high-stakes call-center conversations be evaluated by whether
downstream decisions remain stable under acoustically and semantically plausible
transcription alternatives?

## Method Name

CDS-ASR means:

> Counterfactual Decision-Stability ASR.

CDS-ASR does not only ask whether a transcript is similar to the reference. It
asks whether plausible transcript variants would flip the downstream escalation
decision.

## Scope

In scope:

- risk atom schema for decision-critical transcript spans;
- ASR counterfactual generation from acoustic ambiguity, Mandarin phonetic
  confusion, and fraud-domain slot ontology;
- Counterfactual Escalation Instability Score (CEIS);
- one downstream task: scam escalation classification;
- automatic recovery through constrained re-decoding, ASR ensemble arbitration,
  decision interval estimation, and conservative machine action;
- comparison against WER/CER, semantic metrics, confidence-only approaches, and
  the previous Semantic Risk Error Score (SRES) baseline.

Out of scope for this paper:

- broad institutional simulation;
- generic AI governance theory;
- full real-time agent systems;
- multi-modal model benchmarking;
- using human review as the proposed recovery mechanism;
- claiming ASR state of the art.

## Pipeline

```text
audio
-> ASR transcript + confidence / n-best / timestamps
-> risk atom extraction
-> plausible ASR counterfactual variants
-> downstream decision model
-> decision-stability / CEIS score
-> automatic constrained recovery or conservative machine action
```

`60_whisper_asr_finetuning/` provides ASR hypotheses. This folder defines how to
test whether those hypotheses are decision-stable.

## Directory Contract

| Path | Purpose |
| --- | --- |
| `taxonomy/` | Risk atom schema and decision-critical ASR error weights. |
| `counterfactual/` | CDS-ASR counterfactual generation contract and sample variant table. |
| `annotation/` | Research annotation guideline and sample sheet for evaluating risk atoms. |
| `scoring/` | SRES, WER/CER-vs-SRES comparison, and CEIS scoring scripts. |
| `downstream/` | Scam escalation classification task definition and evaluation script. |
| `recovery/` | Automatic constrained recovery and decision-interval policy. |
| `paper/` | Story outline, citation seed, experiment plan, and framing guardrail. |

## First Experiment Package

Minimum viable paper experiment:

1. Run baseline ASR systems and store predictions under `70_experiments/`.
2. Sample `300-500` high-stakes call segments.
3. Extract risk atoms using `taxonomy/decision_critical_error_taxonomy.yaml`.
4. Generate plausible transcript variants using the counterfactual contract.
5. Compute CEIS with `scoring/counterfactual_escalation_instability.py`.
6. Compare WER/CER, semantic metrics, SRES, and CEIS for predicting downstream
   escalation changes.
7. Test automatic constrained recovery and decision intervals against no
   recovery and confidence-only correction.

Use `paper/experiment_plan.md` for the FIRST PRINCIPLE gate before starting a
long model run. The first publishable unit is a small auditable decision
stability sample, not another generic ASR fine-tune.

## Canonical Paper Design

Use `paper/q1_paper_design.md` as the durable source for the Q1 paper story,
method, experiment design, target journals, and execution plan.

Use `paper/framing_guardrail.md` before writing abstracts, introductions,
cover letters, or repo summaries. It defines what this paper is not: a plain
ASR fine-tuning, SRES-only, human-review, or small-CER-improvement paper.

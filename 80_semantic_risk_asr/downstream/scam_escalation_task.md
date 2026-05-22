# Scam Escalation Classification Task

## Purpose

This is the only downstream task for the first paper.

Given a transcript or transcript-variant set, classify the escalation level for
a possible scam case.

## Labels

| Label | Meaning |
| --- | --- |
| `no_escalation` | Routine or insufficient risk signal. |
| `review` | Intermediate risk state; keep in ordinary case-review queue. |
| `priority_review` | Contains money/action/identity/urgency signals requiring faster review. |
| `critical_escalation` | Likely missed intervention or severe downstream consequence if delayed. |

## Inputs

- reference transcript;
- ASR hypothesis;
- semantic-risk annotations;
- plausible ASR counterfactual variants;
- optional ASR confidence, n-best alternatives, and timestamps;
- automatic recovery decision or decision interval.

## Main Comparison

1. Reference transcript -> escalation label.
2. ASR hypothesis -> escalation label.
3. ASR counterfactual variants -> escalation label set.
4. ASR hypothesis + automatic CDS-ASR recovery -> escalation label or interval.

## Outcome Metrics

- escalation accuracy;
- high-risk miss rate;
- false low-risk rate;
- unsafe down-routing rate;
- automatic recovery budget;
- machine abstention rate;
- decision stability gain.

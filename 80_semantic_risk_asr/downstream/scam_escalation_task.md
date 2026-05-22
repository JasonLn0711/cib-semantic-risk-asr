# Scam Escalation Classification Task

## Purpose

This is the only downstream task for the first paper.

Given a transcript, classify whether the call segment should receive priority
human review for possible scam escalation.

## Labels

| Label | Meaning |
| --- | --- |
| `no_escalation` | Routine or insufficient risk signal. |
| `review` | Needs human review, but not urgent. |
| `priority_review` | Contains money/action/identity/urgency signals requiring faster review. |
| `critical_escalation` | Likely missed intervention or severe downstream consequence if delayed. |

## Inputs

- reference transcript;
- ASR hypothesis;
- semantic-risk annotations;
- optional ASR confidence or n-best alternatives;
- recovery decision.

## Main Comparison

1. Reference transcript -> escalation label.
2. ASR hypothesis -> escalation label.
3. ASR hypothesis + semantic-risk recovery -> escalation label.

## Outcome Metrics

- escalation accuracy;
- high-risk miss rate;
- false low-risk rate;
- reviewer workload;
- recovery-trigger rate.

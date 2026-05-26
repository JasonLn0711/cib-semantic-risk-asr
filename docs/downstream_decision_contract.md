# Downstream Decision Contract

Date: 2026-05-26

Scope: CDS-ASR submission-prep decision-function contract

## Decision Function

The downstream decision function `f` maps a transcript or transcript variant to
one declared anti-fraud triage action:

```text
f(transcript) in {
    no_escalation,
    manual_review,
    priority_review,
    critical_escalation,
    conservative_machine_action,
    abstain
}
```

`manual_review` is the paper-facing action name for the intermediate review
state that earlier task notes also call `review`.

## Base Ordinal States

| action | ordinal_level | meaning |
| --- | ---: | --- |
| no_escalation | 0 | Routine or insufficient risk signal. |
| manual_review | 1 | Keep in ordinary case-review queue. |
| priority_review | 2 | Faster review is warranted. |
| critical_escalation | 3 | Severe missed intervention risk if delayed. |

## Decision Distance Matrix

| from | to | distance | note |
| --- | --- | ---: | --- |
| no_escalation | no_escalation | 0 | Same action. |
| manual_review | manual_review | 0 | Same action. |
| priority_review | priority_review | 0 | Same action. |
| critical_escalation | critical_escalation | 0 | Same action. |
| no_escalation | manual_review | 1 | Neighboring review escalation. |
| manual_review | priority_review | 1 | Neighboring review escalation. |
| priority_review | critical_escalation | 1 | Neighboring review escalation. |
| no_escalation | priority_review | 2 | Two-level escalation distance. |
| manual_review | critical_escalation | 2 | Two-level escalation distance. |
| no_escalation | critical_escalation | 3 | Maximum ordinal distance. |
| critical_escalation | no_escalation | 3 | Unsafe downrouting maximum penalty. |
| critical_escalation | manual_review | 2 | Unsafe downrouting penalty. |
| critical_escalation | priority_review | 1 | Reduced-priority penalty. |

`conservative_machine_action` and `abstain` are policy outputs, not adverse
automation decisions. They preserve uncertainty by routing to human review,
priority review, or a visible decision interval.

## Submission Rule

The manuscript should describe decision distances as policy-aligned ordinal
distances. Stronger claims require freezing this contract and re-running any
CEIS table whose implementation differs from this matrix.

# Downstream Decision Contract

Date: 2026-06-03

Status: frozen for final CSL aggregate regeneration.

## Contract Role

The downstream decision function `f` is a retrospective declared policy
abstraction for the selected high-risk Mandarin anti-fraud audit surface. It is
used to evaluate policy-conditioned decision instability under plausible ASR
alternatives. It is not a live deployment policy and it is not an adverse-action
automation system.

## Label Space

`f(transcript)` maps a transcript or transcript variant into one action:

| action | ordinal level | paper-facing meaning |
| --- | ---: | --- |
| `no_escalation` | 0 | Routine routing or insufficient risk signal. |
| `review` / `manual_review` | 1 | Ordinary human case-review queue. |
| `priority_review` | 2 | Faster human review is warranted. |
| `critical_escalation` | 3 | Severe missed-escalation risk if delayed. |
| `conservative_machine_action` | interval | Stop automatic downrouting, raise review priority, abstain, or require human confirmation. |
| `abstain` | interval | Preserve uncertainty instead of issuing a lower-risk automated route. |

`conservative_machine_action` and `abstain` do not replace transcripts. They
represent a conservative routing intervention over the declared action space.

## Decision Distance

Base decision distance is the absolute ordinal difference over the four
ordinary routing labels:

```text
DecisionDistance(f(x), f(v)) = |level(f(x)) - level(f(v))|
```

The maximum ordinary distance is `3`, from `no_escalation` to
`critical_escalation` or the reverse. Unsafe downrouting is counted when an ASR
action has a lower ordinal level than the reference/expected safe action.

## Primary Analysis Unit

The primary unit is the audio row / case.

```text
row_score = max_h score(row, h)
row_severe = any_h severe_miss(row, h)
```

Model-level assessments remain clustered within the audio row and are reported
as secondary evidence.

## Fixed-Budget Trigger Semantics

The fixed trigger budget denominator is the selected-300 audio rows:

- 10% budget = 30 rows;
- 20% budget = 60 rows;
- 30% budget = 90 rows;
- 40% budget = 120 rows.

Each triggered row receives one conservative action. Multiple model hypotheses
inside the same row do not consume multiple row-level budget slots.

## Tie Handling

If a fixed-budget cutoff falls inside a tied score group, outputs report
best-case and worst-case severe-miss remaining. The manuscript claim must use
the worst-case boundary.

## Freeze Boundary

No pre-audit timestamp/hash proving prospective freeze is currently asserted.
The paper should describe this as a declared retrospective policy contract with
frozen regeneration files for the final aggregate analysis.

# CEIS Method Specification

Date: 2026-05-26

Scope: submission-prep method contract for Counterfactual Escalation Instability Score (CEIS)

## Evidence Boundary

CEIS is a decision-stability metric for a scoped high-stakes ASR audit. It is
not a raw ASR leaderboard metric and it is not a deployed adverse-action
automation rule. The paper-facing implementation must remain reconstructable
from aggregate-safe method configuration, metric tables, and validation
summaries.

## Formula

```text
CEIS(x) = max over v in V(x) [
    Plausibility(v | x) * RiskAtomWeight(v) * DecisionDistance(f(x), f(v))
]
```

`Plausibility(v | x)` is a bounded proxy plausibility score. It is not claimed
to be a calibrated acoustic posterior unless a future implementation supplies
and validates such a posterior.

## Inputs

Inputs to CEIS are:

- the ASR hypothesis or transcript candidate `x`;
- plausible transcript variants `V(x)`;
- risk atom class for each variant;
- proxy plausibility score;
- downstream decision labels from fixed function `f`;
- decision-distance policy.

## Risk Atoms

The submission-prep risk atom set is:

- negation;
- amount;
- action;
- actor;
- intent;
- scam_pattern;
- time;
- uncertainty.

Risk atom weights are versioned in `docs/risk_atom_weights.tsv` and mirrored in
`80_semantic_risk_asr/scoring/ceis_config.json`.

## Variant Generation

Counterfactual variants are plausible ASR alternatives concentrated around
decision-critical atoms. They are not generic paraphrases. The aggregate
submission package may report variant counts by atom and source, but it must
not release variant text.

## Plausibility Score

Allowed aggregate-safe sources:

- model disagreement;
- Mandarin phonetic ambiguity;
- domain-slot alternatives;
- runtime or quality signals;
- acoustic ambiguity evidence when available.

The submission draft should describe these as evidence sources for plausible
ASR alternatives, not as proof that all possible variants are enumerated.

## Decision Function

The downstream decision function is fixed before CEIS scoring. It is specified
in `docs/downstream_decision_contract.md`.

## Decision Distance

Decision distance is a policy-aligned ordinal distance over the anti-fraud
triage label space. The exact contract is versioned in
`docs/downstream_decision_contract.md`.

## RiskAtomWeight

Current submission-prep weights are policy-defined:

| Atom | Weight |
| --- | ---: |
| negation | 5.0 |
| amount | 5.0 |
| action | 5.0 |
| actor | 4.0 |
| intent | 4.0 |
| scam_pattern | 4.0 |
| time | 3.0 |
| uncertainty | 3.0 |
| default | 1.0 |

These weights should be reported as a policy choice and stress-tested with
uniform-weight and by-atom ablations before making stronger generalization
claims.

## Aggregation

CEIS uses max aggregation over plausible variants:

```text
max over v in V(x)
```

The max operator is intentionally conservative because the target is
decision-instability detection in high-stakes triage. A top-k mean aggregation
is listed as a required ablation before stronger generalization claims.

## Recovery Trigger

The current CEIS recovery trigger is the diagnostic scoped-audit threshold
recorded in `80_semantic_risk_asr/scoring/ceis_config.json` and Table 3. It is
not a deployment threshold. Recovery policies are evaluated as aggregate replay
over human-reviewed labels.

## Label Space

The decision function `f` maps a transcript or transcript variant into the
declared anti-fraud triage label space:

```text
f(transcript) in {
    no_escalation,
    review,
    priority_review,
    critical_escalation,
    conservative_machine_action,
    abstain
}
```

The base ordinal order is:

```text
no_escalation = 0
review = 1
priority_review = 2
critical_escalation = 3
```

Distance policy:

- same action = 0;
- neighboring review/escalation state = 1;
- no escalation to critical escalation = 3;
- unsafe downrouting of a critical event = maximum penalty;
- conservative machine action and abstain are policy intervals, not adverse
  decisions.

## Threshold Policy

Table 3 uses retrospective diagnostic thresholds selected on the scoped audit
set. These thresholds support aggregate comparison. They are not frozen
deployment thresholds.

A deployment threshold would require a separate development-set freeze and
prospective validation.

## Required Submission Ablations

The next analysis layer should add:

1. uniform atom weights;
2. no-plausibility ablation;
3. binary decision-flip-only distance;
4. max versus top-k mean CEIS aggregation;
5. CEIS behavior by atom class.

## Privacy Boundary

CEIS method artifacts may expose formula, configuration, aggregate counts,
threshold policy, and validation summaries. They must not expose raw audio,
transcripts, selected sample IDs, audio IDs, ASR hypothesis text, reviewer
notes, or transcript-bearing runtime logs.

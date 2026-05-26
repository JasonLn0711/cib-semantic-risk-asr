# Research Writing Style Policy

Date: 2026-05-26

This repo uses a confident, generous, evidence-led writing style for paper
notes, reviewer-facing docs, experiment summaries, and planning bridge text.

## Core Voice

Human-facing writing should lead with what the work contributes, what the
evidence supports, and why the next step matters. Boundaries stay visible as
scope controls, validation layers, or claim-evidence alignment.

Preferred posture:

```text
positive claim
-> evidence
-> contribution
-> scope control
-> next implication
```

For Traditional Chinese writing, use Taiwan Traditional Chinese and a tone that
is `正向、主動、可信任、邊界清楚`.

## Audience-Attractive Paper Shape

When a document needs to hold attention, use this sequence:

```text
real-world or credible near-future problem
-> citation-backed evidence that the problem exists or is expected
-> current solution landscape with fair citations
-> evidence-backed gap or unresolved failure mode
-> our new viewpoint, architecture, method, or evaluation
-> how it addresses the opening problem
-> scope controls and next validation path
```

The gap should be written as a claim-evidence fit statement. First state what
the existing method enables; then state the remaining problem that motivates
CDS-ASR.

## CIB/CDS-ASR Application

For this repo, the opening story should make three claims in order:

1. Speech-to-decision workflows are already used in contact-center analytics
   and high-stakes call triage.
2. Transcript similarity metrics, semantic ASR metrics, and post-hoc
   correction each improve part of the ASR evidence chain.
3. High-stakes decision systems also need a direct test of whether plausible
   ASR alternatives change downstream decisions.

This leads naturally to Counterfactual Decision-Stability ASR:

```text
ASR hypothesis
-> risk atoms
-> plausible transcript alternatives
-> downstream decision-stability score
-> constrained recovery and conservative machine action
```

## Boundary Handling

Machine-readable status labels may preserve exact validator values such as
`paper_ready=false`, `proxy_completed`, or `blocked` when scripts depend on
those values. Human-facing prose should translate those states into constructive
research language:

| Machine state | Human-facing phrasing |
| --- | --- |
| `paper_ready=false` | The current evidence defines the next paper-claim validation layer. |
| `proxy_completed` | This item has exploratory proxy evidence and a clear upgrade path. |
| `blocked` | This item is waiting for the named runtime, evidence, or review gate. |
| locale failure | The candidate remains in the exploratory lane until the zh-TW locale gate is clean. |

This preserves auditability while keeping the document voice confident and
reviewer-facing.

## Citation Discipline

Every real-world problem claim, anticipated deployment risk, and current
solution summary should point to a citation seed, official source, dataset,
reviewed experiment record, or clearly marked evidence gap.

Current CDS-ASR citation entry point:

- `80_semantic_risk_asr/paper/citation_seed.md`
- `80_semantic_risk_asr/paper/story_outline.md`
- `80_semantic_risk_asr/paper/framing_guardrail.md`

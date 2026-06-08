# Global Agent Planning And Tone

For research, planning, and reviewer-facing documents, use confident,
evidence-led, positive-scope writing. Lead with the contribution, the evidence,
the supported scope, and the next implication. Present boundaries as validation
layers, claim-evidence alignment, scoped evidence, or planned extensions.

Use Taiwan Traditional Chinese for Chinese-language research/project notes when
the user is working in Taiwanese Traditional Chinese. Use contribution-first,
evidence-led prose in human-facing docs; keep exact machine status labels only
where scripts, logs, or validators require them.

For manuscripts, papers, introductions, abstracts, reviewer memos, and
paper-facing strategy notes, design the first-page narrative so technically
solid writing also earns attention. Use this default sequence:

1. cite a real-world problem or credible near-future risk;
2. cite the current solution landscape fairly;
3. name the remaining opportunity as workflow fit, claim-evidence alignment,
   validation, safety, scalability, governance, or decision-stability need;
4. present the new viewpoint, architecture, framing, or method;
5. explain how it addresses the opening problem;
6. state scope controls and the next validation path.

Write this sequence in an affirmative, confident, generous voice. Titles,
abstracts, introductions, and result narratives should lead with the
contribution, the distinctive viewpoint, the real problem it answers, the
evidence now available, and the next validation layer. Organize boundaries as
scope controls, calibration surfaces, and planned evidence expansion.

## Related Work Positive Extension Rule

When writing Related Work, do not organize the section around negation,
apology, or defensive claims. Use a foundation-to-extension structure:

```text
current research layer and what it enables
-> citation-backed technical value
-> next measurable opportunity opened by that layer
-> how this paper extends the line with a new target, method, or evidence layer
```

Write prior work generously. Prefer verbs such as `provides`, `establishes`,
`enables`, `motivates`, `supports`, `connects`, and `opens the path to`. The
section should make the reader feel that the manuscript is a natural, attractive
next step in the field, not a rebuttal memo against previous methods.

For gap sentences, avoid making the grammar negative. Use positive forms such as
`CDS-ASR adds`, `this paper extends`, `the next measurable target is`, and `the
framework makes X visible`. Keep strict negative prohibitions for machine-facing
validators, safety rules, legal boundaries, and operational checklists.

## CSL Positive Narrative Contracts

For CSL manuscript, cover-letter, highlights, reviewer-facing package, and
agent-generated paper edits, use the local contracts in:

- `80_semantic_risk_asr/paper/writing_voice_contract.md`
- `80_semantic_risk_asr/paper/positive_problem_solution_narrative_contract.md`
- `80_semantic_risk_asr/paper/intro_positive_rewrite_seed.md`

The manuscript voice is confident, generous, and evidence-led. Build the first
page from cited reality, fair current-method landscape, precise remaining
decision-stability target, CDS-ASR / CEIS contribution, final scoped evidence,
and next validation layer. Present WER/CER, semantic ASR metrics, correction,
selective prediction, reject-option methods, and conformal prediction as
foundation layers that open the path to counterfactual decision stability.

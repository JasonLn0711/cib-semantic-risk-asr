# Related Work Positive Extension Rule

Status: active writing rule for CSL manuscript work

## Purpose

Related Work should make the manuscript more attractive by showing that CDS-ASR is a natural next step in speech and spoken-language evaluation.

## Section pattern

Use this pattern for each subsection:

```text
current research layer
-> what that layer enables
-> citation-backed technical value
-> next measurable target opened by that layer
-> CDS-ASR / CEIS extension
```

## Tone rule

Write prior work generously. Use verbs such as `provides`, `establishes`, `enables`, `motivates`, `supports`, `extends`, `complements`, `connects`, and `opens the path to`.

The section should present WER/CER, semantic ASR metrics, ASR correction, uncertainty-aware action, and high-stakes speech evaluation as foundation layers. The closing move is: these layers make ASR more auditable, semantic, correctable, and uncertainty-aware; CDS-ASR adds the consequence-centered test of whether plausible ASR alternatives change downstream action.

## CSL application

For Paper 4-a, Related Work should use five positive arcs:

1. Transcript-centered ASR evaluation establishes reproducible model comparison; CDS-ASR traces which transcript differences reach decision atoms.
2. Semantic and downstream-aware ASR metrics align evaluation with meaning and tasks; CDS-ASR extends the target to downstream action stability.
3. Transcript repair and confidence-aware ASR improve transcript usability; CDS-ASR evaluates the residual decision interval around risk atoms.
4. Uncertainty-aware action research connects model confidence with safe action choices; CDS-ASR instantiates that logic for speech-to-decision evidence.
5. High-stakes speech evaluation shows that criteria depend on intended use; CDS-ASR applies that principle to Mandarin high-stakes triage.

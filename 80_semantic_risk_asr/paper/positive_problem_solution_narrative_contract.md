# Positive Problem-Solution Narrative Contract for CSL

Status: active narrative architecture
Purpose: make the manuscript readable, attractive, and scientifically grounded

## One-sentence narrative spine

Speech-driven systems increasingly turn conversations into operational decisions; high-stakes anti-fraud calls concentrate risk in small Mandarin decision atoms; existing transcript, semantic, correction, and abstention layers make ASR more measurable; CDS-ASR adds the missing decision-stability layer by measuring whether plausible transcript alternatives change the declared triage action.

## Opening architecture

### Paragraph 1 — Reality with citation

Start with the world, not the metric.

Suggested form:

> Speech analytics has moved from offline transcription into operational contact-center infrastructure: modern systems categorize conversations, produce summaries, monitor compliance cues, support real-time alerts, and assist routing decisions. In that setting, ASR output becomes part of the decision substrate rather than a passive transcript.

Citation target: AWS Connect Customer / Contact Lens conversational analytics.

### Paragraph 2 — Domain pressure with citation

Move from general speech infrastructure into anti-fraud calls.

Suggested form:

> Anti-fraud calls make the speech-to-action pipeline concrete. Taiwan's 165 anti-fraud hotline records incident details and provides information to victims; large-scale cyber-enabled fraud reports show the operational scale of fraud response. In these calls, the decisive evidence can be a small spoken fact: transfer status, amount, actor, time, certainty, or scam pattern.

Citation targets: Taiwan NPA 165 hotline; FBI IC3 report.

### Paragraph 3 — Linguistic mechanism

Turn the problem into a speech-language insight.

Suggested form:

> These facts are decision atoms. A Mandarin ASR alternative around negation, amount, actor, action, time, intent, uncertainty, or scam pattern can preserve transcript similarity while changing the safe triage action. The scientific target is therefore decision stability under plausible ASR alternatives.

### Paragraph 4 — Prior work as foundation

Present prior work as a staircase.

Suggested form:

> WER and CER provide transcript comparability. Semantic ASR metrics align evaluation with meaning and downstream language tasks. ASR correction and confidence-aware filtering improve transcript repair. Selective prediction and reject-option methods formalize coverage and abstention when action under uncertainty carries cost. These layers establish the technical foundation for consequence-aware ASR evaluation.

Citation targets: Kim et al. 2021; Rugayan et al. 2023; Naderi et al. 2024; Chow 1970; Geifman and El-Yaniv 2017, 2019; Angelopoulos and Bates 2021.

### Paragraph 5 — Our contribution

State the move plainly.

Suggested form:

> CDS-ASR adds the decision-stability layer. It extracts decision-critical risk atoms, constructs plausible ASR alternatives, maps each alternative through a declared downstream triage contract, and scores policy-space instability with CEIS. The evaluation target becomes operational: would another plausible transcript lead to a different safe action?

### Paragraph 6 — Evidence and scope

End the introduction with the exact final claim.

Suggested form:

> On the final selected-300 / 900-assessment aggregate surface, the study evaluates CEIS as a decision-change and complementarity signal under row-clustered analysis. Severe missed-escalation replay is reported as descriptive high-severity evidence after the pre-declared failover. The result is a scoped ASR evaluation layer for high-stakes Mandarin speech systems: transcript accuracy remains visible, and decision stability becomes measurable.

## Tone rules for the whole manuscript

Use confident verbs: `introduces`, `formalizes`, `measures`, `evaluates`, `shows`, `supports`, `adds`, `separates`, `reports`.

Use generous prior-work language: `provides the foundation`, `establishes the baseline`, `adds semantic structure`, `motivates risk-coverage action`, `complements`.

Use positive scope language: `scoped`, `declared`, `aggregate-visible`, `row-clustered`, `descriptive high-severity`, `release boundary`, `future calibration layer`.

Use tension without hype: real operational stakes, clear mechanism, measured contribution.

## CSL reviewer memory sentence

> In high-stakes ASR, the unit of evaluation should expand from transcript similarity to decision stability under plausible transcript alternatives, because small decision atoms can carry the action boundary.

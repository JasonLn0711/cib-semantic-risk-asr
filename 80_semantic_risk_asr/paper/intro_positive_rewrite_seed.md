# CSL Introduction Positive Rewrite Seed

Use this as the next-pass introduction seed. Keep citations in the paper's existing citation style.

## Draft opening

Speech analytics has moved from offline transcription into operational contact-center infrastructure. Modern contact-center systems analyze voice conversations and transcripts to categorize contacts, generate summaries, monitor compliance cues, support real-time alerts, and guide operational assistance. In this setting, ASR output becomes part of the decision substrate: it can shape case category, queue assignment, alerting, escalation, and human-review priority.

Anti-fraud calls make the speech-to-action pipeline concrete. Taiwan's 165 anti-fraud hotline records incident details and provides information to victims, while large-scale cyber-enabled fraud reports show the operational scale of fraud response. The decisive spoken facts in these calls are often compact: whether money was transferred, whether the amount was 30,000 or 300,000, who initiated contact, when the event happened, how certain the caller is, and whether the scenario matches a scam pattern. These facts are decision atoms.

Decision atoms create a precise ASR evaluation problem. A plausible Mandarin transcript alternative around negation, amount, actor, action, time, intent, uncertainty, or scam pattern can preserve transcript similarity while changing the declared triage action. The evaluation target is safety-relevant decision stability: whether plausible ASR alternatives keep the downstream action stable under a declared policy contract.

Existing ASR evaluation and repair methods provide the staircase for this target. WER and CER make transcript accuracy auditable. Semantic ASR metrics connect transcript evaluation to meaning and downstream spoken-language-understanding behavior. ASR correction and confidence-aware filtering improve transcript repair. Selective prediction, reject-option methods, and conformal prediction formalize risk-coverage tradeoffs when acting under uncertainty carries cost. Together, these methods make ASR more measurable, semantic, correctable, and action-aware.

CDS-ASR adds the counterfactual decision-stability layer. It extracts decision-critical risk atoms, constructs plausible ASR alternatives, maps each transcript through a declared downstream triage contract, and scores policy-space instability with Counterfactual Escalation Instability Score (CEIS). The central question becomes operational: would another plausible transcript lead to a different safe action?

The final selected-300 / 900-assessment aggregate regeneration evaluates CEIS as a decision-change and complementarity signal under row-clustered analysis. Severe missed-escalation replay is reported as descriptive high-severity evidence after the pre-declared failover. The result is a scoped evaluation layer for high-stakes Mandarin ASR: transcript accuracy remains visible, semantic risk remains comparable, and decision stability becomes directly measurable.

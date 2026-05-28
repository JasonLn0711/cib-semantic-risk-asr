# Cover Note And Data Availability Statement

Date: 2026-05-28

Submission route: Route A, direct submission without a second-reviewer
transcript-bearing spot-check.

## Cover Note

Dear Editors,

We submit "When Low WER Becomes Dangerous: Counterfactual
Decision-Stability ASR for High-Stakes Speech-Driven Decision Systems" for
consideration as a high-stakes ASR safety and governance manuscript. The paper
studies a speech-to-decision setting in which contact-center transcripts can
support routing, escalation, compliance review, and anti-fraud case handling.
Its central contribution is Counterfactual Decision-Stability ASR (CDS-ASR), an
aggregate-auditable framework for evaluating whether plausible ASR alternatives
around decision-critical risk atoms would change a downstream action.

The manuscript is scoped to a frozen evidence chain. The 258-row test split is
used for ASR model-comparison context; selected-300 proxy outputs are used for
selection provenance; and the paper-grade risk/recovery claims come from a
completed selected-300 human-reviewed audit surface with 30 reviewed rows and
90 reviewed model assessments. The human-reviewed evidence is a completed
single-expert audit. Inter-annotator agreement is not claimed, and no
second-reviewer blinded transcript-bearing spot-check is included in this
submission-prep package.

The results support CDS-ASR as a consequence-centered companion to transcript
accuracy and semantic ASR metrics. CEIS is presented as a conservative
decision-stability signal: it has the strongest point AUC and reaches a
zero-false-negative diagnostic operating point in the scoped audit, while SRES
remains a strong semantic-risk baseline and achieves the highest
best-threshold F1. At the recovery layer, SRES-triggered recovery and
CEIS-triggered conservative action tie on severe-miss elimination at the same
diagnostic budget; the fixed-budget frontier is reported separately as
retrospective aggregate policy replay, not as a deployed threshold claim.

The intended use of CDS-ASR is conservative triage support, abstention,
manual-review prioritization, and ASR safety audit. It is not proposed as an
automated adverse-action, punitive, law-enforcement, or account-blocking
system. This claim boundary is explicit in the manuscript's ethics, privacy,
and limitations sections.

## Data Availability

Transcript-bearing materials are treated as sensitive operational call content.
Raw audio, reference transcripts, ASR hypotheses, selected row identifiers,
audio identifiers, local response sheets, reviewer notes, transcript-bearing
runtime logs, and model weights are not released and are not included in the
submission package.

Public reproducibility is provided through aggregate artifacts only: manuscript
tables, aggregate validation summaries, claim registry, artifact manifests,
operation records, generated figures, row-clustered uncertainty summaries,
leave-one-row-out sensitivity summaries, and evidence-chain consistency
audits. These artifacts support reviewer-visible auditability of the evidence
chain without exposing transcript-bearing row content.

The submission package includes:

- `80_semantic_risk_asr/paper/manuscript_submission.tex`
- `80_semantic_risk_asr/paper/references.bib`
- `80_semantic_risk_asr/paper/figures/*.pdf`
- `80_semantic_risk_asr/paper/artifact_manifest.tsv`
- `70_experiments/runs/postdoc_evidence_chain_2026_05_25/claim_registry.tsv`
- `70_experiments/runs/postdoc_evidence_chain_2026_05_25/artifact_manifest.tsv`
- `docs/privacy_boundary.md`
- `docs/intended_use_statement.md`
- `docs/hostile_reviewer_checklist.md`
- `80_semantic_risk_asr/paper/hostile_reviewer_final_pass_2026_05_28.md`

The final rendered manuscript PDF is generated locally from
`manuscript_submission.tex` and is kept in the submission package copy. The
repo-tracked manuscript source remains aggregate-only.

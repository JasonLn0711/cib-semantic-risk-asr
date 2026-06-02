# Computer Speech & Language Submission Notes

Date: 2026-06-02

Target journal: `Computer Speech & Language`

Primary route decision:

> Computer Speech & Language is a strong Route A target if the manuscript is
> framed as a spoken-language evaluation paper: ASR output becomes a
> speech-to-decision substrate, CDS-ASR evaluates decision stability around
> spoken risk atoms, and the anti-fraud triage setting is the application layer.
> Governance remains important, but the first-page identity should be speech
> recognition / spoken-language system evaluation rather than a general AI
> governance paper.

## 1. Official Journal Snapshot

Source check date: 2026-06-02

Official sources:

- Journal home page:
  `https://www.sciencedirect.com/journal/computer-speech-and-language`
- Guide for Authors:
  `https://www.sciencedirect.com/journal/computer-speech-and-language/publish/guide-for-authors`
- Journal Insights:
  `https://www.sciencedirect.com/journal/computer-speech-and-language/about/insights`
- Submission system link from the Guide for Authors:
  `https://www.editorialmanager.com/csl/`

Journal identity:

- Official publication of the International Speech Communication Association
  (ISCA).
- Publishes original research on analysis, recognition, understanding,
  production, synthesis, coding, and mining of speech and spoken language.
- Welcomes interdisciplinary speech and spoken-language research, including
  theoretical studies, experimental studies, models, implementations, and
  fundamental research that improves such models.
- Research areas that directly match this manuscript:
  - algorithms and models for speech recognition and synthesis;
  - natural language processing for speech understanding and generation;
  - evaluation of speech-based interactive systems;
  - applications of speech and spoken language technologies.
- Important scope boundary: the journal no longer accepts pure NLP-only
  submissions; new manuscripts must address spoken language processing.

Current journal metrics and publishing facts from ScienceDirect:

| Item | Current value |
| --- | --- |
| Publisher | Academic Press / Elsevier |
| Print ISSN | 0885-2308 |
| Online ISSN | 1095-8363 |
| CiteScore | 12.0 |
| Impact Factor | 3.4 |
| Open-access APC | USD 3,600 excluding taxes |
| Subscription option | No publication fee charged to authors |
| Submission to first decision | 3 days in current ScienceDirect snapshot |
| Submission to decision after review | 115 days in current ScienceDirect snapshot |
| Submission to acceptance | 226 days in current ScienceDirect snapshot |
| Acceptance to online publication | 12 days in current ScienceDirect snapshot |
| Indexing | Scopus, SCIE, Ei Compendex |
| Review model | Single anonymized review; editor screens suitability, then normally at least two reviewers |

## 2. TFSC-Style Transfer Rule

Use the same discipline as the prior TFSC analysis:

1. Start from the venue identity, not from a mechanical formatting checklist.
2. Compress the manuscript around one reviewer-facing axis.
3. Keep the evidence boundary frozen unless the venue reveals a true blocker.
4. Treat limitations as claim-evidence alignment and planned validation layers.
5. Convert the manuscript to the venue's problem frame without changing the
   scientific claims.

For TFSC, the reviewer-facing axis was governance-scale evidence and a bounded
stress-test claim. For Computer Speech & Language, the reviewer-facing axis
should be:

> Consequence-centered evaluation for speech-to-decision ASR systems.

The manuscript should read as a speech/spoken-language evaluation contribution:

```text
spoken call audio -> ASR hypotheses -> spoken-language risk atoms
-> plausible ASR alternatives -> decision-stability metric
-> conservative recovery / abstention evidence
```

The governance, anti-fraud, privacy, and human-review layers support the
application setting and release boundary. They should not replace the journal
fit: speech recognition and spoken-language system evaluation.

## 3. Venue-Fit Verdict

Verdict: high-fit with one framing requirement.

The manuscript already has a good technical fit because it studies ASR output,
speech-to-decision use, transcript alternatives, spoken risk atoms, WER/CER,
semantic-risk scoring, and evaluation of speech-based interactive systems.

The strongest CSL claim is:

> WER/CER and semantic transcript metrics are necessary, but high-stakes
> speech-to-decision systems also need a consequence-centered test: whether
> plausible ASR alternatives around spoken risk atoms change downstream action.

This claim is narrower and stronger than a general safety claim. It aligns with
CSL because it is about evaluating speech recognition outputs in a downstream
spoken-language system.

## 4. Current Manuscript Check

Canonical files:

- `80_semantic_risk_asr/paper/manuscript_submission.tex`
- `80_semantic_risk_asr/paper/manuscript_submission.pdf`
- `80_semantic_risk_asr/paper/references.bib`
- `80_semantic_risk_asr/paper/figures/*.pdf`
- `80_semantic_risk_asr/paper/tables/*.tex`
- `80_semantic_risk_asr/paper/artifact_manifest.tsv`

Current abstract:

- 226 words by local TeX extraction.
- CSL requirement: concise factual abstract, maximum 250 words.
- Verdict: length is compatible.
- Improvement: keep the current abstract, but make sure the first sentence
  keeps "speech-driven decision systems" and "ASR" visible before governance
  terms.

Current section structure:

- Introduction
- Related Work
- Method
- Experiments
- Results
- Discussion
- Supplementary Claim Registry
- Ethics, Privacy, and Intended Use
- Limitations and Threats to Validity
- Appendix / Artifact Availability
- Validation Gate Commands
- Scope Control For Additional Validation

Verdict:

- Technically compatible with CSL's numbered-section expectation.
- `Validation Gate Commands` and `Scope Control For Additional Validation`
  are useful reviewer-facing audit material, but they may be better moved to
  supplement if the submission system expects a cleaner article body.

## 5. Required CSL Submission Deltas

These are venue-specific deltas before submission.

### 5.1 Must Fix Before Submission

1. Add a real title page.
   - Current `\author{}` is empty.
   - CSL single-anonymized review means reviewers are anonymous; the manuscript
     does not need double-anonymized author removal unless the submission
     system asks for it.
   - Add final author list, affiliations, and corresponding author contact.

2. Add keywords.
   - CSL requires 1 to 7 English keywords.
   - Recommended keywords:
     `automatic speech recognition`; `spoken language understanding`;
     `speech-to-decision systems`; `semantic evaluation`; `decision stability`;
     `counterfactual evaluation`; `risk-aware ASR`.

3. Add article highlights.
   - CSL requires highlights at submission.
   - Draft highlights:
     - CDS-ASR evaluates whether plausible ASR alternatives change downstream decisions.
     - CEIS captures escalation instability around spoken risk atoms.
     - Human-reviewed selected-300 evidence supports scoped decision-change prediction.
     - Risk-triggered recovery eliminates severe misses in aggregate policy replay.
     - Aggregate-only artifacts preserve auditability while protecting transcript-bearing call evidence.

4. Convert or confirm reference style.
   - CSL's Guide for Authors specifies numbered references in square brackets,
     ordered by first appearance.
   - Current manuscript prose uses author-year citations from the Pandoc build.
   - Action: convert the final submission build to CSL numeric reference style
     or use the journal's Elsevier template/style if available.

5. Add required declarations.
   - Declaration of competing interests.
   - Funding sources.
   - Declaration of generative AI use, if any AI-assisted writing, coding, or
     figure generation must be disclosed under Elsevier policy.
   - Acknowledgements, if applicable, as a separate section before references.
   - CRediT author contribution statement.

6. Add formal data availability statement.
   - CSL requires a data statement at submission.
   - Current artifact-availability section is substantively strong, but the
     submission package should include a concise formal statement:

```text
Data availability

The transcript-bearing call materials used in this study are not publicly
available because they may contain sensitive operational speech content,
including raw audio, reference transcripts, ASR hypotheses, row identifiers,
reviewer notes, local response sheets, runtime logs, and model outputs.
Reviewer-visible reproducibility is provided through aggregate artifacts:
manuscript tables, generated figures, validation summaries, claim registries,
artifact manifests, row-clustered uncertainty summaries, leave-one-row-out
sensitivity summaries, and evidence-chain consistency audits.
```

7. Final spelling, grammar, and reference cross-check.
   - CSL submission checklist explicitly includes spelling/grammar checks and
     reference-list reciprocity.
   - Run a final citation audit: every cited source appears in the reference
     list and every reference-list item is cited.

8. Check copyrighted materials.
   - Current figures appear generated inside the repo and should be safe.
   - Confirm no third-party web images or copyrighted source excerpts are in
     figures, tables, or supplement.

### 5.2 Strongly Recommended Before Submission

1. Make the title slightly more CSL-direct if a title change is allowed.

Current title:

> When Low WER Becomes Dangerous: Counterfactual Decision-Stability ASR for High-Stakes Speech-Driven Decision Systems

Recommended CSL-facing title:

> Counterfactual Decision-Stability Evaluation for High-Stakes Speech-to-Decision ASR

Reason:

- It leads with the method and the speech-to-decision ASR identity.
- It still preserves the paper's core contribution.
- It sounds less slogan-like for a technical speech journal while keeping the
  "low WER danger" idea available in the introduction.

2. Keep the first-page narrative speech-first.

Opening sequence:

```text
speech-driven decision systems
-> ASR hypotheses become operational signals
-> WER/CER and semantic ASR metrics provide necessary transcript evidence
-> remaining gap is decision stability under plausible ASR alternatives
-> CDS-ASR contribution
-> scoped evidence and privacy-preserving aggregate release
```

3. Move governance-heavy passages later.

The anti-fraud, privacy, intended-use, and AI risk-management references are
important. For CSL, they should appear after the speech-processing contribution
is already clear.

4. Consider supplement placement.

Keep the main article focused. Move long validator/command surfaces to
supplement when possible:

- claim registry;
- validation gate commands;
- scope control for additional validation;
- long artifact lists.

The main manuscript should preserve the method, evidence, and aggregate
availability statement. The supplement can carry the full audit trail.

## 6. Submission Package Boundary For CSL

Include in the submission package:

- main manuscript PDF;
- editable LaTeX source;
- bibliography file;
- generated figure PDFs;
- generated table fragments;
- highlights file;
- keywords;
- cover letter;
- data availability statement;
- declaration of competing interests;
- funding statement;
- generative AI declaration if applicable;
- CRediT author contribution statement;
- author biographies and author photos if the submission system requires them;
- aggregate supplement with:
  - claim registry;
  - artifact manifest;
  - evidence-chain consistency summaries;
  - publishable evidence summary;
  - WER/CER journal-compliance audit;
  - row-clustered uncertainty summaries;
  - leave-one-row-out sensitivity summaries;
  - counterfactual variant coverage summary;
  - privacy boundary and intended-use statement.

Exclude from the submission package:

- raw audio;
- raw/reference transcripts;
- ASR hypothesis text;
- selected row IDs;
- audio IDs;
- local response sheets;
- reviewer notes;
- transcript-bearing runtime logs;
- model weights, checkpoints, or adapters;
- non-aggregate generated variants.

## 7. Cover Letter Direction

Cover letter should address the Editor-in-Chief and editorial team for
Computer Speech & Language.

Recommended cover-letter spine:

```text
Dear Editors,

We submit "[title]" for consideration in Computer Speech & Language. The
manuscript contributes Counterfactual Decision-Stability ASR (CDS-ASR), an
evaluation framework for speech-to-decision systems in which ASR hypotheses
feed routing, escalation, and conservative action.

The paper addresses a spoken-language processing problem: transcript accuracy
and semantic similarity are necessary but do not directly test whether
plausible ASR alternatives around decision-critical spoken risk atoms would
change downstream action. CDS-ASR adds this consequence-centered evaluation
layer through risk-atom extraction, plausible ASR alternatives, CEIS scoring,
and aggregate policy replay.

The evidence is scoped and auditable: a six-model 258-row ASR comparison,
selected-300 high-stakes provenance, 30 reviewed rows / 90 reviewed model
assessments, and aggregate recovery-policy replay. Transcript-bearing materials
remain protected, while aggregate artifacts support reviewer-visible
auditability.

The manuscript is original, not under consideration elsewhere, and approved for
submission by all authors.
```

## 8. Current Route Verdict

Route A remains active, now with Computer Speech & Language as the named
journal.

Submission readiness:

- Evidence boundary: ready.
- Abstract length: ready.
- Main framing: close; make CSL speech-first emphasis explicit.
- Figures/tables: ready at the current aggregate manuscript level.
- Formal CSL metadata: not ready until title page, keywords, highlights,
  declarations, and data statement are added.
- Reference style: needs final numeric-style conversion or confirmation before
  submission.

Next concrete action:

> Produce a CSL submission-clean package: title page, highlights, keywords,
> declarations, formal data statement, numeric references, compiled PDF, and
> aggregate supplement. Do not reopen experiments or selected-300 review.

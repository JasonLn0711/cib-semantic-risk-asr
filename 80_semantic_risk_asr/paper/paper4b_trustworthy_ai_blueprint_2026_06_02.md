# Paper 4-b Blueprint: Trustworthy AI / Reproducible Evaluation Paper

Date: 2026-06-02

Working role:

> A trustworthy AI, responsible AI, and reproducible evaluation paper using
> CDS-ASR as a case study for aggregate-only auditability of sensitive speech AI
> evidence.

## 1. Paper Design

### Tentative Title Options

1. Aggregate-Only Reproducibility for Sensitive Speech AI Evaluation
2. Reviewer-Auditable Reproducibility Without Transcript Release: An Aggregate-Only Framework for Sensitive Speech AI Evaluation
3. Reviewer-Visible Auditability Without Transcript Release: A Governance Framework for Speech AI Evaluation
4. Claim-Evidence Governance for Sensitive ASR Evaluation
5. Reproducible Evaluation Boundaries for High-Stakes Speech AI
6. Auditable Without Row Release: Aggregate Evidence and Claim Alignment for Speech AI

Recommended title:

> Aggregate-Only Reproducibility for Sensitive Speech AI Evaluation

### One-Sentence Thesis

Sensitive speech AI studies can support reviewer-visible reproducibility and
claim-evidence governance without releasing raw audio, transcripts, row
identifiers, reviewer notes, or transcript-bearing logs by combining aggregate
artifacts, manifest checks, operation records, validation gates, privacy-class
boundaries, and explicit claim registries.

### Target Journal Positioning

Primary fit:

- Journal of Responsible Technology;
- AI and Ethics;
- AI & Society;
- Technology in Society;
- trustworthy AI / responsible AI / reproducible evaluation venues.

Positioning statement:

> This is not a second technical proof of CEIS. It is a governance and
> reproducibility paper that uses CDS-ASR as a detailed case study for sensitive
> speech AI evaluation.

### Abstract Structure

1. Problem: sensitive speech AI evidence often cannot be released row-by-row.
2. Gap: reproducibility norms often assume public data or code is enough, but
   transcript-bearing evidence needs stronger boundaries.
3. Framework: aggregate-only reproducibility with manifests, operation records,
   validation gates, privacy classes, and claim registries.
4. Case: CDS-ASR evidence layers: 258 rows, selected-300 provenance, 30 reviewed
   rows, 90 clustered assessments, aggregate replay.
5. Contribution: reviewer-visible auditability without public raw evidence.
6. Boundary: not a deployment-readiness claim and not a replacement for
   institutional review or multi-annotator validation.

### Main Contributions

1. Defines aggregate-only reproducibility for sensitive speech AI evaluation.
2. Proposes a claim-evidence governance framework linking claims, evidence
   layers, artifact privacy classes, validation gates, and release boundaries.
3. Provides a taxonomy of public aggregate artifacts, local-only sensitive
   artifacts, and controlled operational records.
4. Uses the CDS-ASR study as a case example showing how reviewers can audit a
   sensitive speech evaluation without raw transcript release.
5. Provides checklists for submission packages, artifact manifests, leak checks,
   and claim-boundary review.

## 2. Proposed 250-Word Abstract Draft

Reproducible evaluation is difficult when AI systems are tested on sensitive
speech evidence. Raw audio, transcripts, row identifiers, reviewer notes, and
runtime logs may contain private operational content, yet reviewers still need
to inspect whether reported claims are supported by traceable evidence. This
paper proposes aggregate-only reproducibility as a governance framework for
sensitive speech AI evaluation. The framework separates public aggregate
artifacts from local-only transcript-bearing materials and links each paper
claim to evidence layers, artifact manifests, validation gates, operation
records, privacy classes, and explicit release boundaries.

We develop the framework through a CDS-ASR case study in high-stakes
speech-to-decision evaluation. The case contains four distinct evidence layers:
a 258-row ASR test split for model-comparison context, selected-300 provenance
outputs for high-stakes audit-surface construction, 30 human-reviewed audit
rows yielding 90 clustered model assessments for decision-change evaluation,
and aggregate policy replay for recovery analysis. Instead of releasing raw
speech or transcript-bearing row content, the case provides reviewer-visible
auditability through aggregate tables, generated figures, claim registries,
artifact manifests, row-clustered uncertainty summaries, leave-one-row-out
sensitivity summaries, and consistency checks.

The paper contributes a practical taxonomy and submission checklist for
sensitive AI evaluation studies whose evidence cannot be fully public. The
framework does not claim deployment readiness, population prevalence, or
multi-annotator reliability. Its contribution is claim-evidence stewardship:
making bounded empirical claims auditable while preserving privacy,
institutional review, and local-only evidence boundaries.

## 3. Recommended Section Outline

1. Introduction
   - reproducibility tension in sensitive speech AI;
   - why raw release is not always appropriate;
   - reviewer-visible auditability as the target.

2. Related Work
   - reproducible ML and artifact evaluation;
   - responsible AI documentation and model/data cards;
   - privacy-preserving data release and sensitive speech evidence;
   - claim-evidence alignment and audit trails.

3. Framework: Aggregate-Only Reproducibility
   - definitions;
   - artifact privacy classes;
   - local-only boundary;
   - aggregate evidence surfaces;
   - operation records;
   - validation gates;
   - claim registry.

4. Claim-Evidence Governance Taxonomy
   - claim type;
   - evidence layer;
   - artifact class;
   - validator/check;
   - privacy boundary;
   - reviewer-visible output.

5. Case Study: CDS-ASR
   - brief speech-to-decision context;
   - evidence layers;
   - what is public;
   - what remains local-only;
   - what each aggregate artifact supports.

6. Case Evidence: Auditability Without Transcript Release
   - manifest checks;
   - claim registry;
   - consistency summaries;
   - row-clustered uncertainty;
   - leave-one-row-out sensitivity;
   - policy replay boundaries.

7. Discussion
   - reviewer trust;
   - limits of aggregate reproducibility;
   - how this differs from open data;
   - institutional review and deployment validation;
   - transfer to other sensitive domains.

8. Limitations
   - single case study;
   - no raw row-level external reproduction;
   - single-expert audit;
   - no deployment trial;
   - framework depends on honest manifests and validator discipline.

9. Checklist And Practical Recommendations
   - submission checklist;
   - artifact checklist;
   - privacy boundary checklist;
   - claim-boundary checklist.

## 4. What To Keep From Current Manuscript

Keep and reframe:

- aggregate-only release boundary;
- artifact availability statement;
- claim registry;
- artifact manifest;
- validation gate commands;
- privacy and intended-use boundary;
- evidence-layer distinctions;
- selected-300, 30-row, 90-assessment boundaries;
- limitations about thresholds, clustered assessments, and single-expert audit.

## 5. What To Remove Or Summarize

Summarize briefly:

- detailed CEIS formula and metric proof;
- full ASR metric comparison;
- recovery policy mechanics;
- predictor AUC result details;
- ASR candidate-lane details.

Remove from the main text:

- speech-journal-specific literature review;
- extended WER/CER technical discussion;
- full method proof of risk atoms and CEIS;
- any wording that makes CEIS the main contribution.

## 6. Proposed Framework / Taxonomy

Framework name:

> Aggregate-Only Claim-Evidence Governance (ACE-Gov)

Core framework layers:

1. Evidence boundary.
   - Defines which materials can be public, controlled, or local-only.
   - Keeps raw audio, raw transcripts, row identifiers, reviewer notes, and
     transcript-bearing runtime logs outside the public release boundary.
   - Separates 258 ASR test rows, selected-300 provenance outputs, 30 reviewed
     audit rows, and 90 clustered model assessments.

2. Aggregate artifact layer.
   - Releases only transcript-free statistics, tables, summaries, figures,
     manifests, validation outputs, and sensitivity summaries.
   - Uses artifact privacy classes:
     - public aggregate;
     - public source/config;
     - controlled aggregate supplement;
     - local-only transcript-bearing;
     - excluded model/checkpoint artifact.

3. Claim registry.
   - Maps each paper claim to an artifact, statistic, scope, validation layer,
     and limitation.
   - Prevents machine-status labels from becoming unsupported human-facing
     claims.

4. Operation records.
   - Record audit process and command-level reproducibility:
     - generator;
     - source inputs;
     - source commit;
     - environment;
     - timestamp;
     - checksum;
     - privacy class.

5. Reviewer audit protocol.
   - Specifies what reviewers can inspect and what remains local-only.
   - Enables review of claim-evidence alignment even when raw transcripts are
     not released.
   - Includes leak checks, manifest checks, consistency checks, citation checks,
     evidence-chain readiness, and metric-compliance checks.

Implementation taxonomy:

1. Evidence-layer map.
   - 258-row split;
   - selected-300 provenance;
   - 30 reviewed rows;
   - 90 clustered model assessments;
   - aggregate replay.

2. Artifact privacy classes.
   - public aggregate;
   - public source/config;
   - controlled aggregate supplement;
   - local-only transcript-bearing;
   - excluded model/checkpoint artifact.

3. Claim registry fields.
   - claim;
   - scope;
   - evidence artifact;
   - statistic;
   - validation layer;
   - boundary/limitation.

4. Validation gates.
   - leak checks;
   - manifest checks;
   - consistency checks;
   - citation checks;
   - evidence-chain readiness;
   - metric-compliance checks.

5. Operation-record fields.
   - generator;
   - source inputs;
   - source commit;
   - environment;
   - timestamp;
   - checksum;
   - privacy class.

6. Release boundary.
   - included aggregate artifacts;
   - excluded transcript-bearing evidence;
   - controlled local review path if needed.

## 7. Empirical Evidence Reused As Case Study

Reused case evidence:

- 258 ASR test rows: model-comparison context;
- selected-300 provenance outputs: audit-surface construction;
- 30 human-reviewed audit rows: evaluation layer;
- 90 clustered model assessments: clustered metric evidence;
- aggregate policy replay: replay evidence;
- row-clustered bootstrap and leave-one-row-out sensitivity: uncertainty layer;
- artifact manifests and claim registry: auditability layer;
- privacy boundary and leak checks: release-boundary layer.

Do not re-prove CEIS. Present it as the case-study metric whose claims are
governed by the framework.

## 8. Additional Artifacts Or Checklists To Prepare

- `paper4b_claim_registry.tsv`
- `paper4b_artifact_privacy_classes.tsv`
- `paper4b_release_boundary.md`
- `paper4b_manifest_checklist.md`
- `paper4b_submission_checklist.md`
- `paper4b_reviewer_audit_map.tsv`
- concise data availability statement;
- transcript-bearing leak-check log;
- companion-manuscript disclosure note if Paper 4-a is submitted nearby.

## 9. Claims To Soften

| Strong wording to avoid | Journal-ready wording |
| --- | --- |
| Aggregate-only reproducibility fully replaces open data | Aggregate-only reproducibility supports reviewer-visible auditability when row release is not appropriate |
| The case proves responsible AI compliance | The case demonstrates claim-evidence stewardship for a scoped sensitive speech evaluation |
| Reviewers can reproduce everything | Reviewers can audit aggregate evidence, manifests, validation gates, and claim boundaries |
| The framework solves privacy | The framework preserves a local-only boundary while supporting bounded public auditability |
| CEIS is validated generally | CEIS is one case-study metric governed by explicit evidence boundaries |

## 10. Limitations To State Clearly

- Single case study from a high-stakes speech-to-decision setting.
- Aggregate-only release limits independent row-level reproduction.
- The CDS-ASR case uses a single-expert audit; no inter-annotator agreement is
  claimed.
- 90 model assessments are clustered within 30 reviewed rows.
- selected-300 is an enriched high-stakes audit surface.
- Thresholds in the case are diagnostic operating points.
- The framework does not replace institutional review, data-use agreements, or
  deployment validation.
- Manifest and validation-gate quality depends on process discipline.

## 11. Figure And Table Plan

| Item | Role |
| --- | --- |
| Figure 1: aggregate-only reproducibility architecture | Main framework figure |
| Figure 2: evidence ladder from 258 rows to aggregate replay | Main case-study figure |
| Figure 3: release boundary map | Main governance figure |
| Figure 4: claim-evidence alignment workflow | Main framework figure |
| Table 1: artifact privacy classes | Main taxonomy table |
| Table 2: claim boundary registry excerpt | Main evidence table |
| Table 3: validation gates and failure modes | Main process table |
| Table 4: case-study evidence layers | Main case table |
| Supplement Table S1: full artifact manifest excerpt | Supplement |
| Supplement Table S2: submission checklist | Supplement or main |

## 12. Claim Boundary Table

| Claim | Evidence | Boundary |
| --- | --- | --- |
| Aggregate-only artifacts can support reviewer-visible auditability | CDS-ASR manifests, figures, tables, validation summaries | Does not provide raw row-level reproduction |
| Claim registries improve claim-evidence alignment | claim registry and evidence-layer map | Process framework, not proof of correctness |
| Local-only boundaries protect sensitive speech evidence | release-boundary policy and leak checks | Does not replace institutional governance |
| Validation gates reduce submission-risk ambiguity | consistency, metric, leak, manifest checks | Gates are only as strong as their implementation |
| CDS-ASR is a useful case study | evidence layers and aggregate replay | CEIS technical validation belongs to Paper 4-a |

## 13. Reviewer Risk Table

| Reviewer risk | Response |
| --- | --- |
| "This is just a case report." | Present ACE-Gov as a transferable framework with a detailed case demonstration. |
| "No raw data means no reproducibility." | Define aggregate-only reproducibility as a bounded reproducibility mode for sensitive evidence, not a replacement for open data. |
| "CEIS evidence is too technical." | Summarize CEIS only as case-study context; focus on claim-evidence governance. |
| "Privacy claims are too broad." | State release-boundary stewardship, not legal compliance or privacy guarantee. |
| "Single-expert audit weakens the case." | Treat it as an explicit evidence boundary and governance example. |
| "Duplicate publication with Paper 4-a." | Distinguish primary question: governance framework versus ASR evaluation method. |

## 14. Minimum Submission Checklist

- Framework figure.
- Evidence-layer table.
- Artifact privacy-class table.
- Claim boundary registry excerpt.
- Release boundary statement.
- Data availability statement.
- Companion-manuscript disclosure note if needed.
- Competing interest, funding, CRediT, acknowledgements, generative-AI
  declaration if applicable.
- Citation reciprocity check.
- Transcript-bearing leak check.
- Clear statement that raw audio, transcripts, row IDs, reviewer notes, and
  transcript-bearing logs remain outside the public release.

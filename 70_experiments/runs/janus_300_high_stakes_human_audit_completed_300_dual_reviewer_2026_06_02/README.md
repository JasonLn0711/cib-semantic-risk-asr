# Janus 300 Human Audit Completed Dual-Reviewer Record

Date: 2026-06-02

Status: 300-row dual-reviewer human audit completed, recorded from expert
completion report.

This run records the aggregate-only completion state for the CSL / CDS-ASR
human audit package:

`csl-cds-asr-human-audit-300-review-package-20260602_completed.zip`

Local completed package path:

`/home/jnln3799/Downloads/csl-cds-asr-human-audit-300-review-package-20260602_completed.zip`

The transcript-bearing reviewer sheets, merged sheets, and package zip remain
local/download artifacts and must not be committed. This tracked run records
only aggregate completion status, consistency checks, label distributions, and
reviewer-agreement statistics.

## Completed Files

Source reviewer files completed:

- `reviewer_1/human_risk_atom_audit_sheet_reviewer_1.tsv`
- `reviewer_1/model_level_review_flat_reviewer_1.tsv`
- `reviewer_2/human_risk_atom_audit_sheet_reviewer_2.tsv`
- `reviewer_2/model_level_review_flat_reviewer_2.tsv`

Post-review merged and agreement outputs produced:

- `reviewer_1/human_risk_atom_audit_sheet_reviewer_1.merged.tsv`
- `reviewer_2/human_risk_atom_audit_sheet_reviewer_2.merged.tsv`
- `aggregate_outputs_after_review/human_audit_reviewer_agreement.tsv`
- `aggregate_outputs_after_review/human_audit_reviewer_agreement_summary.json`

## Completion Checks

- Reviewer 1: 300/300 row-level complete; 900/900 model-level complete.
- Reviewer 2: 300/300 row-level complete; 900/900 model-level complete.
- Required fields have no empty values.
- Row-level `yes` rows all have at least one model-level `yes` or `uncertain`.
- Critical atoms are contained in risk atoms.
- Rows with `yes` all have expected safe action other than `none`.

## Row-Level Distribution

| Reviewer | no | yes | uncertain |
| --- | ---: | ---: | ---: |
| Reviewer 1 | 280 | 14 | 6 |
| Reviewer 2 | 285 | 14 | 1 |

## Reviewer Agreement

| Field | Cohen's Kappa |
| --- | ---: |
| `reviewer_would_asr_error_change_decision` | 0.849970 |
| `reviewer_semantic_risk_label` | 1.000000 |
| `reviewer_expected_safe_action` | 0.851426 |
| `reviewer_annotation_confidence` | 0.934274 |

## Submission Implication

The 100+ human-audit gate and dual-reviewer agreement gate are now satisfied at
the full selected-300 scope. The next CSL hardening step is CEIS ablation on the
completed reviewed surface, followed by manuscript figure/table regeneration
and claim-boundary updates from `pilot audit` to expanded dual-reviewer audit.

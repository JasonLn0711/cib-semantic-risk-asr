# CSL Human Audit Completion Record

Date: 2026-06-02

Status: expert-completed 300-row dual-reviewer audit recorded.

## Completed Review Scope

The expert review completed rows 1-300 in the CSL / CDS-ASR human audit package.
Both reviewers completed the same 300-row surface.

Completed source files:

- `reviewer_1/human_risk_atom_audit_sheet_reviewer_1.tsv`
- `reviewer_1/model_level_review_flat_reviewer_1.tsv`
- `reviewer_2/human_risk_atom_audit_sheet_reviewer_2.tsv`
- `reviewer_2/model_level_review_flat_reviewer_2.tsv`

The merge and Kappa commands from `COMMANDS_AFTER_REVIEW.md` were executed and
produced:

- `reviewer_1/human_risk_atom_audit_sheet_reviewer_1.merged.tsv`
- `reviewer_2/human_risk_atom_audit_sheet_reviewer_2.merged.tsv`
- `aggregate_outputs_after_review/human_audit_reviewer_agreement.tsv`
- `aggregate_outputs_after_review/human_audit_reviewer_agreement_summary.json`

Completed package:

- `csl-cds-asr-human-audit-300-review-package-20260602_completed.zip`
- `/home/jnln3799/Downloads/csl-cds-asr-human-audit-300-review-package-20260602_completed.zip`

## Completion Checks

- Reviewer 1: 300/300 row-level complete; 900/900 model-level complete.
- Reviewer 2: 300/300 row-level complete; 900/900 model-level complete.
- Required fields have no empty values.
- Row-level `yes` rows all have at least one model-level `yes` or `uncertain`.
- Critical atoms are contained in risk atoms.
- Rows with `yes` all have expected safe action other than `none`.

## Cohen's Kappa

| Field | Cohen's Kappa |
| --- | ---: |
| `reviewer_would_asr_error_change_decision` | 0.849970 |
| `reviewer_semantic_risk_label` | 1.000000 |
| `reviewer_expected_safe_action` | 0.851426 |
| `reviewer_annotation_confidence` | 0.934274 |

## Row-Level Distribution

| Reviewer | `no` | `yes` | `uncertain` |
| --- | ---: | ---: | ---: |
| Reviewer 1 | 280 | 14 | 6 |
| Reviewer 2 | 285 | 14 | 1 |

## Tracked Aggregate Record

The repo-safe aggregate record is stored at:

`70_experiments/runs/janus_300_high_stakes_human_audit_completed_300_dual_reviewer_2026_06_02/`

The transcript-bearing reviewer sheets, merged sheets, and completed zip remain
local/download artifacts. They should not be committed.

## Submission Implication

The human-audit expansion gate and dual-reviewer Kappa gate are now satisfied
at the full selected-300 scope. The remaining CSL hardening gate is CEIS
ablation on the completed reviewed surface, followed by manuscript table,
figure, appendix, and claim-boundary regeneration.

# Run Record: janus_300_high_stakes_human_audit_selection_2026_05_25

## Summary

- Status: audit selection created, human review pending
- Date: 2026-05-25
- Dataset: JANUS selected 300 high-stakes expansion
- Input: three-model selected-300 SRES/CEIS/downstream proxy outputs
- Candidate audio rows: `300`
- Selected human-audit audio rows: `30`
- Selected model-samples: `90`
- Human-reviewed rows: `0 / 30`
- Human-reviewed model assessments: `0 / 90`
- Local review sheet: ignored under `artifacts/human_risk_atom_audit_sheet.tsv`

## Purpose

Create the reviewer-facing human risk-atom audit gate needed before proxy
SRES/CEIS predictor and recovery results can be treated as paper-grade
evidence. The selector intentionally keeps audio IDs, transcripts, and model
hypotheses out of tracked files.

## Command

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/select_human_risk_atom_audit.py \
  --sres-scored 70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/artifacts/metric_inputs_three_model/sres_scored.tsv \
  --ceis-scored 70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/artifacts/metric_inputs_three_model/ceis_scored.tsv \
  --downstream-decisions 70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/artifacts/metric_inputs_three_model/downstream_escalation_decisions.tsv \
  --output-dir 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25 \
  --audit-size 30
```

Runtime: `0.0453` seconds.

## Aggregate Selection Results

| Item | Value |
| --- | ---: |
| Candidate audio rows | 300 |
| Selected audio rows | 30 |
| Selected model-samples | 90 |
| Selected critical-miss audio rows | 1 |
| Selected high-risk-missed audio rows | 6 |
| Selected unsafe-downrouting audio rows | 22 |
| Selected label-flip audio rows | 25 |
| Selected low-WER danger audio rows | 2 |
| Selected high proxy-risk audio rows | 25 |
| Selected model-disagreement audio rows | 22 |

Primary selection strata:

| Stratum | Target quota | Available audio | Primary selected | Selected carrying signal |
| --- | ---: | ---: | ---: | ---: |
| Critical or high-risk missed | 6 | 6 | 6 | 6 |
| Unsafe downrouting | 6 | 22 | 6 | 22 |
| Low-WER danger | 4 | 2 | 0 | 2 |
| High proxy risk | 6 | 25 | 6 | 25 |
| Model disagreement | 4 | 22 | 4 | 22 |
| Clean control | 4 | 275 | 4 | 5 |
| Risk-score fill | - | - | 4 | - |

`Primary selected` is the stratum that claimed the row first. `Selected
carrying signal` counts overlap; for example, the two low-WER danger rows were
already selected by earlier higher-priority strata.

Risk-atom coverage:

| Risk atom | Available audio | Selected audio |
| --- | ---: | ---: |
| action | 25 | 25 |
| actor | 15 | 15 |
| amount | 23 | 23 |
| negation | 14 | 14 |
| scam_pattern | 23 | 23 |

## Local-Only Human Review Sheet

The local ignored sheet contains:

- audio ID;
- split;
- reference transcript;
- per-model hypotheses and metrics;
- current proxy risk signals;
- blank reviewer fields for verified transcript, semantic-risk label, risk
  atoms, critical atoms, decision-change reason, expected safe action,
  confidence, and notes.

The tracked protocol is:
`80_semantic_risk_asr/annotation/selected_300_human_risk_atom_audit_protocol_2026_05_25.md`.

## Review Readiness Summary

The current local sheet has been summarized with:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/summarize_human_risk_atom_audit.py \
  --audit-sheet 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/human_risk_atom_audit_sheet.tsv \
  --output-dir 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25
```

Current aggregate status:

| Item | Value |
| --- | ---: |
| Audit rows | 30 |
| Reviewed rows | 0 |
| Pending rows | 30 |
| Model assessments | 90 |
| Reviewed model assessments | 0 |
| Pending model assessments | 90 |
| Missing `reviewer_semantic_risk_label` | 30 |
| Missing `reviewer_would_asr_error_change_decision` | 30 |
| Missing `reviewer_annotation_confidence` | 30 |

Tracked readiness outputs:

| File | Content |
| --- | --- |
| `human_audit_validation_summary.json` | Schema/completion validation status for the local sheet. Current status: review pending, schema valid. |
| `human_audit_validation_counts.tsv` | Aggregate validation warnings/errors and completion counts. Current warnings are pending review only. |
| `human_audit_review_summary.json` | Review completion and missing-field counts. |
| `human_audit_strata_review.tsv` | Reviewed row counts by selection stratum. |
| `human_audit_risk_atom_review.tsv` | Human-confirmed risk-atom aggregate counts after review. Currently empty because review is pending. |
| `human_audit_model_review.tsv` | Per-model reviewed-sample aggregate counts. Currently zero reviewed rows. |
| `human_audit_predictor_summary.json` | Human-reviewed predictor gate readiness. Currently review pending. |
| `human_audit_predictor_comparison.tsv` | WER/CER/SRES/CEIS vs human model-level decision-change targets after review. Currently zero reviewed samples. |
| `human_audit_predictor_model_summary.tsv` | Per-model human-reviewed predictor target counts. Currently zero reviewed samples. |

The local sheet now includes `reviewer_model_assessments_json`. This field is
needed because row-level labels can show that an audio segment contains a
dangerous ASR risk, but only model-level labels can support a reviewer-facing
claim about which ASR model is safer.

## Local Review Helper

The local helper for filling one row at a time is:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/review_human_risk_atom_audit.py \
  --audit-sheet 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/human_risk_atom_audit_sheet.tsv \
  --list-pending
```

Current safe pending summary:

- audit rows: `30`;
- pending rows: `30`;
- pending strata: `clean_control=4`,
  `critical_or_high_risk_missed=6`, `high_proxy_risk=6`,
  `model_disagreement=4`, `risk_score_fill=4`, `unsafe_downrouting=6`.

To inspect a transcript-bearing row locally, use `--show-row --row-number N`.
That output includes audio ID, reference transcript, ASR hypotheses, and
current model assessment JSON. Do not commit it, paste it into issues, or copy
it into tracked notes.

To dry-run an edit without modifying the sheet:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/review_human_risk_atom_audit.py \
  --audit-sheet 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/human_risk_atom_audit_sheet.tsv \
  --row-number N \
  --semantic-risk-label priority_review \
  --risk-atoms negation,amount \
  --critical-atoms negation \
  --asr-confusion-terms "short local note" \
  --decision-change yes \
  --decision-change-reason "routing changed" \
  --expected-safe-action priority_review \
  --confidence high \
  --model-review breeze_asr25_partial_encoder_high_stakes_300:yes:negation:priority_review:high
```

Add `--write` only after the dry-run output is valid. The helper creates a
local ignored backup under `artifacts/backups/` before writing. Tracked
evidence must still come from `validate_human_risk_atom_audit.py`,
`summarize_human_risk_atom_audit.py`, and
`analyze_human_audit_predictors.py`.

## Validation Gate

Before and after human review, validate the local sheet with:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/validate_human_risk_atom_audit.py \
  --audit-sheet 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/human_risk_atom_audit_sheet.tsv \
  --output-dir 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25 \
  --expected-rows 30
```

Current validation status:

| Item | Value |
| --- | ---: |
| Status | `review_pending` |
| Audit rows | 30 |
| Reviewed rows | 0 |
| Pending rows | 30 |
| Model assessments | 90 |
| Reviewed model assessments | 0 |
| Pending model assessments | 90 |
| Validation errors | 0 |
| Pending-row warnings | 30 |
| Pending-model warnings | 90 |

The strict completion gate is:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/validate_human_risk_atom_audit.py \
  --audit-sheet 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/human_risk_atom_audit_sheet.tsv \
  --expected-rows 30 \
  --require-complete
```

This currently fails as expected because review is not complete:
`incomplete_row_review=30`, `incomplete_model_review=90`.

After model-level review, run:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/analyze_human_audit_predictors.py \
  --audit-sheet 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/human_risk_atom_audit_sheet.tsv \
  --output-dir 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25
```

Current predictor readiness: `0 / 90` model assessments reviewed. Predictor
metrics are computed only over reviewed model-level assessments.

## Aggregate Refresh Gate

After local row/model edits, use the refresh gate instead of manually running
each aggregate step:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/refresh_human_audit_evidence.py \
  --audit-sheet 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/human_risk_atom_audit_sheet.tsv \
  --output-dir 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25 \
  --readiness-output-dir 70_experiments/runs/postdoc_evidence_chain_2026_05_25 \
  --expected-rows 30
```

This writes `human_audit_refresh_summary.json` and refreshes validation,
review-summary, predictor, and evidence-chain readiness outputs. Current
recorded result:

| Item | Value |
| --- | ---: |
| Refresh status | `review_pending` |
| Reviewed rows | `0 / 30` |
| Reviewed model assessments | `0 / 90` |
| Downstream aggregate outputs refreshed | `true` |
| Evidence-chain paper ready | `false` |

The strict post-review gate is:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/refresh_human_audit_evidence.py \
  --audit-sheet 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/human_risk_atom_audit_sheet.tsv \
  --output-dir 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25 \
  --readiness-output-dir 70_experiments/runs/postdoc_evidence_chain_2026_05_25 \
  --expected-rows 30 \
  --require-complete
```

It currently fails as expected because the local sheet is still unreviewed:
`30` incomplete row reviews and `90` incomplete model reviews.

## Boundary

This run does not complete the human audit. It creates the audit queue,
aggregate selection evidence, and aggregate review-readiness record.
Paper-facing SRES/CEIS and recovery claims remain proxy-only until the local
sheet is reviewed and aggregate human annotation statistics are recorded.

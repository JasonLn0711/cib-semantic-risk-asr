# Run Record: janus_300_high_stakes_human_audit_selection_2026_05_25

## Summary

- Status: audit selection created, human review pending
- Date: 2026-05-25
- Dataset: JANUS selected 300 high-stakes expansion
- Input: three-model selected-300 SRES/CEIS/downstream proxy outputs
- Candidate audio rows: `300`
- Selected human-audit audio rows: `30`
- Selected model-samples: `90`
- Human-reviewed risk/decision rows: `0 / 30`
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

Transcript ground truth is already human-reviewed for WER/CER scoring. This
gate should not reopen transcript review unless a future review task asks for
fields or content that differ from those accepted ground-truth transcript
fields; the pending work is risk/decision/model assessment review.

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
| `human_audit_next_review_batch_summary.json` | Repo-safe record for the next prepared local review packet. Current packet: `critical_or_high_risk_missed`, rows `1-6`, `6` rows / `18` model assessments. |
| `human_audit_next_review_batch_rows.tsv` | Repo-safe row-number and missing-field checklist for the prepared packet. No audio IDs, transcripts, hypotheses, or reviewer notes. |
| `human_audit_review_batch_log.tsv` | Append-only repo-safe preparation log for local transcript-bearing review packets. |
| `human_audit_current_review_batch_status_summary.json` | Repo-safe completion status for the current packet. Current status: `batch_pending`, `0/6` risk/decision rows and `0/18` model assessments reviewed. |
| `human_audit_current_review_batch_status_rows.tsv` | Repo-safe row-level completion checklist for the current packet. No audio IDs, transcripts, hypotheses, or reviewer notes. |
| `human_audit_batch_response_template_summary.json` | Repo-safe record for the local response TSV template. Current template has `18` response rows for rows `1-6` and optional review-timing columns. |
| `human_audit_batch_response_apply_summary.json` | Repo-safe strict dry-run/apply status for the local response TSV. Current `--require-complete` dry-run status is `response_pending`, `ok=false`, `incomplete_response=1`, with `0/6` rows, `0/18` model assessments, and `0/6` row review timings filled. |
| `human_audit_batch_response_apply_log.tsv` | Append-only repo-safe response dry-run/write log. Current first entry records the blank strict dry-run as `response_pending` with aggregate counts only. |
| `human_audit_batch_response_apply_log_summary.json` | Repo-safe audit of the response apply log. Current status: `apply_log_valid`, `2` entries, latest status `response_pending`, `0/6` rows and `0/18` model assessments filled. |
| `human_audit_reviewer_handoff_summary.json` | Repo-safe current reviewer handoff. Current status: `reviewer_input_pending`, packet rows `1-6`, response template path, latest apply status, apply-log status, and exact next commands. |

The local sheet now includes `reviewer_model_assessments_json`. This field is
needed because row-level labels can show that an audio segment contains a
dangerous ASR risk, but only model-level labels can support a reviewer-facing
claim about which ASR model is safer.

## Local Review Helper

For a one-file current-state handoff, run:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/build_human_audit_reviewer_handoff.py
```

The handoff summary does not read transcript-bearing row content. It combines
the prepared packet summary, current batch status, response template summary,
apply status, and apply-log summary into
`human_audit_reviewer_handoff_summary.json`.

Prepare the next local transcript-bearing review packet before filling rows:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/prepare_human_audit_review_batch.py \
  --audit-sheet 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/human_risk_atom_audit_sheet.tsv \
  --output-dir 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25 \
  --expected-rows 30
```

Current prepared packet:

- selection stratum: `critical_or_high_risk_missed`;
- row numbers: `1,2,3,4,5,6`;
- rows in packet: `6`;
- pending model assessments in packet: `18`;
- local packet path:
  `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/review_batches/2026-05-25T210505_0800_critical_or_high_risk_missed.md`.

The local packet contains transcripts and ASR hypotheses and remains ignored by
Git. The tracked batch summary contains only row numbers, strata, counts,
missing-field names, and the local packet path.

Audit the prepared batch completion status before and after filling rows:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/audit_human_review_batch_status.py \
  --audit-sheet 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/human_risk_atom_audit_sheet.tsv \
  --batch-summary 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_next_review_batch_summary.json \
  --output-dir 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25 \
  --expected-rows 30
```

Current batch status:

- status: `batch_pending`;
- reviewed risk/decision rows in batch: `0 / 6`;
- reviewed model assessments in batch: `0 / 18`;
- `batch_ready_for_refresh=false`.

For batch entry, use the local response TSV workflow instead of hand-editing
`reviewer_model_assessments_json`:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/apply_human_audit_batch_response.py \
  --write-template \
  --audit-sheet 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/human_risk_atom_audit_sheet.tsv \
  --batch-summary 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_next_review_batch_summary.json \
  --output-dir 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25 \
  --expected-rows 30
```

Current local response template:

```text
70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/review_responses/2026-05-25T220915_0800_critical_or_high_risk_missed_response_template.tsv
```

The response TSV includes optional timing columns:
`review_started_at`, `review_finished_at`, and `review_elapsed_seconds`.
These fields are not completion gates, but filled values are summarized as
aggregate review-time counts and seconds in the tracked apply summary.
Every dry-run or write through the workflow also appends one repo-safe row to
`human_audit_batch_response_apply_log.tsv` so failed, partial, and completed
attempts remain auditable without storing transcript-bearing row content.
`human_audit_batch_response_apply_log_summary.json` summarizes that append-only
log for quick status checks.

After a reviewer fills that ignored TSV, dry-run it first. Use
`--require-complete` as the completion gate; it should fail until all required
row-level and model-level reviewer fields are filled:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/apply_human_audit_batch_response.py \
  --require-complete \
  --response-sheet 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/review_responses/2026-05-25T220915_0800_critical_or_high_risk_missed_response_template.tsv \
  --audit-sheet 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/human_risk_atom_audit_sheet.tsv \
  --batch-summary 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_next_review_batch_summary.json \
  --output-dir 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25 \
  --expected-rows 30
```

Current strict dry-run status is `response_pending`: `ok=false`,
`incomplete_response=1`, `0/6` row decisions and `0/18` model assessments have
been filled. The timing summary currently records `0/6` rows with review-time
values. A non-strict dry-run may be used for progress inspection, but
`--require-complete` must return `response_complete` before adding `--write`.

After strict dry-run returns `response_complete`, apply and refresh the
aggregate status in one pass:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/apply_human_audit_batch_response.py \
  --require-complete \
  --write \
  --refresh-after-write \
  --prepare-next-after-write \
  --response-sheet 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/review_responses/2026-05-25T220915_0800_critical_or_high_risk_missed_response_template.tsv \
  --audit-sheet 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/human_risk_atom_audit_sheet.tsv \
  --batch-summary 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_next_review_batch_summary.json \
  --output-dir 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25 \
  --readiness-output-dir 70_experiments/runs/postdoc_evidence_chain_2026_05_25 \
  --expected-rows 30
```

This post-write path first updates the ignored local audit sheet, then writes
the current batch status outputs, and only refreshes aggregate evidence after
the batch reports `batch_complete`. Partial overall selected-300 review is
treated as in-progress, not as missing evidence. With
`--prepare-next-after-write`, the command also prepares the next local
transcript-bearing packet and response TSV template when pending rows remain.

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

## Review Progress Batches

The aggregate-only progress audit is:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/audit_human_review_progress.py \
  --audit-sheet 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/human_risk_atom_audit_sheet.tsv \
  --output-dir 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25 \
  --expected-rows 30
```

Current tracked progress:

| Item | Value |
| --- | ---: |
| Review status | `review_pending` |
| Row completion | `0 / 30` |
| Model-assessment completion | `0 / 90` |
| Recommended review batches | `6` |

Batch order:

| Order | Stratum | Pending rows | Pending model assessments |
| ---: | --- | ---: | ---: |
| 1 | `critical_or_high_risk_missed` | 6 | 18 |
| 2 | `unsafe_downrouting` | 6 | 18 |
| 3 | `high_proxy_risk` | 6 | 18 |
| 4 | `model_disagreement` | 4 | 12 |
| 5 | `risk_score_fill` | 4 | 12 |
| 6 | `clean_control` | 4 | 12 |

The model-level pending work is balanced across the three high-stakes ASR
runs: base, LoRA, and partial encoder each have `30` pending assessments.

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
review-progress, review-summary, predictor, evidence-chain readiness, and
objective-level publishable completion outputs. Current recorded result:

| Item | Value |
| --- | ---: |
| Refresh status | `review_pending` |
| Reviewed rows | `0 / 30` |
| Reviewed model assessments | `0 / 90` |
| Recommended review batches | `6` |
| Downstream aggregate outputs refreshed | `true` |
| Evidence-chain paper ready | `false` |
| Publishable evidence ready | `false` |
| Completion audit status counts | `completed=4`, `proxy_completed=2`, `review_pending=1` |

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

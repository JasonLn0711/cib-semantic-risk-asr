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
| `human_audit_batch_response_template_summary.json` | Repo-safe record for the local response TSV template. Current template has `18` response rows for rows `1-6` and review-timing columns. |
| `human_audit_batch_response_apply_summary.json` | Repo-safe strict dry-run/apply status for the local response TSV. Current `--require-complete --require-timing --require-session-start-gate` dry-run status is `response_pending`, `ok=false`, `incomplete_response=1`, `missing_review_timing=6`, with `session_start_gate.ok=true`, `0/6` rows, `0/18` model assessments, and `0/6` row review timings filled. |
| `human_audit_batch_response_apply_log.tsv` | Append-only repo-safe response dry-run/write log. Current entries record blank strict dry-runs as `response_pending` with aggregate counts only. |
| `human_audit_batch_response_apply_log_summary.json` | Repo-safe audit of the response apply log. Current status: `apply_log_valid`, `5` entries, latest status `response_pending`, `require_timing=True`, `0/6` rows, `0/18` model assessments, and `0/6` timing rows filled. |
| `human_audit_reviewer_handoff_summary.json` | Repo-safe current reviewer handoff. Current status: `reviewer_input_pending`, `freshness_status=fresh`, packet rows `1-6`, response template path, latest apply status, apply-log status, source-summary SHA-256 digests, and exact next commands. |
| `human_audit_reviewer_preflight_summary.json` | Repo-safe pre-review session preflight. Current status: `review_session_ready`, `handoff_fresh`, local packet exists, local response TSV exists, and no reviewer labels have been fabricated. |
| `human_audit_reviewer_preflight_log.tsv` | Append-only repo-safe preflight log. Current entries record the ready state for `critical_or_high_risk_missed` rows `1-6` / `18` model assessments. |
| `human_audit_reviewer_rubric_summary.json` | Repo-safe reviewer value-contract readiness. Current status: `rubric_ready`, validator constants match the strict audit validator, and the remaining scope excludes duplicate transcript review. |
| `human_audit_reviewer_value_contract.tsv` | Repo-safe allowed-value contract for row risk labels, decision-change labels, safe actions, confidence labels, and risk atoms. No audio IDs, transcripts, hypotheses, or reviewer notes. |
| `human_audit_reviewer_action_checklist_summary.json` | Repo-safe action checklist for the current reviewer batch. Current status: `reviewer_action_ready`, with `rubric_status=rubric_ready`, `6/6` packet rows, `18/18` model assessments, and `6/6` required timing rows still pending. |
| `human_audit_reviewer_action_checklist.tsv` | Repo-safe checklist rows for handoff freshness, local packet/template existence, preflight, rubric/value-contract confirmation, required row/model fields, required timing fields, strict dry-run, and post-completion write/refresh. |
| `human_audit_reviewer_session_start_summary.json` | Repo-safe one-command reviewer-session start record. Current status: `reviewer_session_started`, after refreshing handoff, preflight, rubric, and action checklist. Human review content remains pending. |
| `human_audit_reviewer_session_start_log.tsv` | Append-only repo-safe session-start log with aggregate gate statuses, pending counts, and latest apply status only. |
| `human_audit_response_closeout_summary.json` | Repo-safe response closeout checklist. Current status: `response_closeout_blocked`, with `session_start_gate.ok=true` but `0/6` row decisions, `0/18` model assessments, and `0/6` timing rows filled. |
| `human_audit_response_closeout_checklist.tsv` | Repo-safe closeout checklist rows for session start, session-gated strict dry-run, row/model completion, response status, and write/refresh readiness. |
| `human_audit_post_review_evidence_summary.json` | Repo-safe post-review paper-evidence checklist. Current status: `post_review_evidence_blocked`; blockers are response closeout, human refresh, human predictor, readiness/publishable/consequence gates, and proxy-only recovery evidence. |
| `human_audit_post_review_evidence_checklist.tsv` | Repo-safe checklist rows for the aggregate gates that must pass after response closeout/write/refresh before proxy claims can be promoted to paper-facing evidence. |

The local sheet now includes `reviewer_model_assessments_json`. This field is
needed because row-level labels can show that an audio segment contains a
dangerous ASR risk, but only model-level labels can support a reviewer-facing
claim about which ASR model is safer.

## Local Review Helper

For the normal one-command reviewer-session start gate, run:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/start_human_audit_review_session.py
```

Current session-start status: `reviewer_session_started`. The command refreshes
the aggregate handoff, records preflight, refreshes the reviewer value contract,
refreshes the action checklist, writes
`human_audit_reviewer_session_start_summary.json`, and appends
`human_audit_reviewer_session_start_log.tsv`. It does not read transcript text
or reviewer notes. The current content gate is still pending: `6/6` packet
rows, `18/18` model assessments, and `6/6` required timing rows.

The generated strict dry-run and write commands now include
`--require-timing --require-session-start-gate --session-start-summary
70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_reviewer_session_start_summary.json`.
This keeps response writes tied to the current reviewer-session gate and blocks
write/refresh unless every selected audio row has aggregate review timing.

After running the session-gated strict dry-run, build the aggregate-only
response closeout checklist:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/build_human_audit_response_closeout_checklist.py
```

Current closeout status: `response_closeout_blocked`. The session-start gate is
valid, but the local response TSV still has `0/6` row-level decisions and
`0/18` model assessments plus `0/6` timing rows filled, so the write/refresh
command remains blocked.

For a one-file current-state handoff, run:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/build_human_audit_reviewer_handoff.py
```

The handoff summary does not read transcript-bearing row content. It combines
the prepared packet summary, current batch status, response template summary,
apply status, and apply-log summary into
`human_audit_reviewer_handoff_summary.json`. The summary records SHA-256
digests for each source summary so stale handoffs can be detected without
storing row content.

Before opening the local packet or response TSV, check that the existing
handoff still matches its source summaries:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/build_human_audit_reviewer_handoff.py --check-existing
```

Current freshness check: `handoff_fresh`.

Before a human review session starts, record the aggregate-only session
preflight:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/preflight_human_audit_review_session.py
```

Current preflight status: `review_session_ready`. This means the handoff is
fresh and the local packet/response TSV paths exist; it does not mean reviewer
fields are complete.

Before filling the local response TSV, build the aggregate-only reviewer value
contract:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/build_human_audit_reviewer_rubric.py
```

Current rubric status: `rubric_ready`. The value contract mirrors the strict
validator constants for row risk labels, decision-change labels, safe actions,
confidence labels, and risk atoms. It also records that the supplied transcript
ground truth has already been human-reviewed for WER/CER scoring, so the
remaining review scope is risk, decision, safe-action, confidence, model-level
assessment, and required timing fields.

To produce a one-page aggregate action checklist for the current reviewer
batch, run:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/build_human_audit_reviewer_action_checklist.py
```

Current checklist status: `reviewer_action_ready`. The checklist confirms that
the handoff is fresh, local packet/response paths exist, and preflight is
recorded, and now requires `rubric_status=rubric_ready` before reviewer entry.
The blocking content remains `6/6` packet rows and `18/18` model-level
assessments in the ignored local response TSV. Optional timing fields are also
pending for `6/6` rows. This checklist does not read transcript text or
reviewer notes. The current strict dry-run already validates the session-start
gate and then fails only because reviewer content is still incomplete.

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

The response TSV includes timing columns:
`review_started_at`, `review_finished_at`, and `review_elapsed_seconds`.
These fields are strict response closeout gates when using the generated
`--require-timing` commands; filled values are summarized as aggregate
review-time counts and seconds in the tracked apply summary.
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

After response closeout/write/refresh, run the aggregate-only post-review
evidence checklist:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/build_post_review_evidence_checklist.py
```

Current post-review status is `post_review_evidence_blocked`: the response
closeout is not ready, human refresh/predictor outputs are still pending,
paper/publishable/consequence gates are false, and recovery evidence remains
proxy-only until human-reviewed labels are available.

## Boundary

This run does not complete the human audit. It creates the audit queue,
aggregate selection evidence, and aggregate review-readiness record.
Paper-facing SRES/CEIS and recovery claims remain proxy-only until the local
sheet is reviewed and aggregate human annotation statistics are recorded.

# Selected-300 Human Risk-Atom Audit Protocol

Date: 2026-05-25

Status: review protocol active; annotation not yet completed

## Purpose

The selected-300 proxy experiments show that SRES/CEIS can identify dangerous
decision changes that WER/CER do not fully explain. That is useful engineering
evidence, but not yet paper-grade human evidence.

This protocol defines the next gate: a bounded human audit of `30` selected
high-stakes audio rows, covering `90` model-samples from:

- `breeze_asr25_partial_encoder_high_stakes_300`
- `breeze_asr25_lora_high_stakes_300`
- `breeze_asr25_base_high_stakes_300`

## FIRST PRINCIPLE

The scarce resource is not another model run. The scarce resource is
reviewer-trustworthy evidence that an ASR error changes a downstream
high-stakes decision.

Therefore the reviewer should not mark every typo. The reviewer should mark
only decision-relevant transcript differences that could change scam escalation,
priority, manual review, or conservative machine action.

## Source And Privacy Boundary

Local ignored review sheet:

```text
70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/human_risk_atom_audit_sheet.tsv
```

Tracked files must not include:

- raw audio;
- audio IDs;
- selected sample IDs;
- full reference transcripts;
- full ASR hypotheses;
- reviewer free-text notes that reveal the call content.

Tracked files may include only:

- aggregate annotation counts;
- risk-atom category counts;
- reviewer agreement statistics;
- metric comparison summaries;
- protocol and run commands.

## Audit Unit

One row in the local sheet is one audio segment. Each row contains the reference
transcript plus the three ASR hypotheses. The reviewer should evaluate whether
any ASR hypothesis creates a decision-critical difference.

There are two review levels:

1. Row-level review: whether this audio row contains any decision-critical ASR
   risk.
2. Model-level review: which ASR hypothesis caused the decision-critical risk.

The model-level field is required for reviewer-facing claims about whether
partial encoder, LoRA, or base Breeze is safer. Without model-level review, the
audit can only support row-level risk coverage, not model comparison.

## Transcript Policy

The reference transcripts used for WER/CER scoring are already accepted as
human-reviewed ground truth. Do not route duplicate transcript review.
`reviewer_verified_transcript` is optional and correction-only: use it only if
the reviewer discovers an exception that should be explicitly recorded in the
local ignored sheet.

## Required Reviewer Fields

Fill these columns in the local sheet:

| Field | Meaning |
| --- | --- |
| `reviewer_semantic_risk_label` | Final human label: `no_escalation`, `review`, `priority_review`, or `critical_escalation`. |
| `reviewer_risk_atoms` | Comma-separated atoms present in the row. |
| `reviewer_critical_atoms` | Comma-separated atoms whose ASR corruption could change the downstream decision. |
| `reviewer_asr_confusion_terms` | Short description of the actual risky confusion, without adding unrelated narrative. |
| `reviewer_would_asr_error_change_decision` | `yes`, `no`, or `uncertain`. |
| `reviewer_decision_change_reason` | Short reason tied to escalation, priority, or conservative action. |
| `reviewer_expected_safe_action` | `none`, `manual_review`, `priority_review`, `critical_escalation`, `conservative_machine_action`, or `abstain`. |
| `reviewer_annotation_confidence` | `high`, `medium`, or `low`. |
| `reviewer_model_assessments_json` | Per-model reviewer fields for each ASR hypothesis. Fill decision-change, critical atoms, expected safe action, and confidence for every model entry. |
| `reviewer_notes` | Minimal note for unresolved ambiguity. Keep raw personal/call details out of tracked summaries. |

Optional correction field:

| Field | Meaning |
| --- | --- |
| `reviewer_verified_transcript` | Correction-only field if the accepted ground-truth reference needs an exception record; otherwise leave blank. This field is not a completion gate for `--require-complete`. |

## Risk Atom Labels

Use the taxonomy in:

```text
80_semantic_risk_asr/taxonomy/decision_critical_error_taxonomy.yaml
```

Primary labels:

- `negation`
- `amount`
- `action`
- `actor`
- `intent`
- `time`
- `uncertainty`
- `scam_pattern`

## Review Rules

1. Compare the reference transcript with each ASR hypothesis.
2. Identify only the span or phrase that can change the downstream decision.
3. Assign risk atoms to the decision-relevant span.
4. Decide whether the ASR error would change escalation or safety action.
5. Fill `reviewer_model_assessments_json` for each model hypothesis so
   model-level predictor analysis does not fall back to row-level labels.
6. If the ASR output is wrong but the downstream label would stay safe, mark
   `reviewer_would_asr_error_change_decision=no`.
7. If the reference itself is ambiguous or the audio would be needed to settle
   the decision, mark `uncertain` and set confidence to `low`.
8. Do not reward a model for being closer in CER if it loses a critical atom.
9. Do not penalize harmless wording changes that do not affect routing,
   priority, intervention, or conservative action.

## Local Review Workflow

Prepare the next local transcript-bearing batch packet first. This creates an
ignored packet under `artifacts/review_batches/` and tracked aggregate records
with only row numbers, strata, missing-field counts, and the local packet path:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/prepare_human_audit_review_batch.py \
  --audit-sheet 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/human_risk_atom_audit_sheet.tsv \
  --output-dir 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25 \
  --expected-rows 30
```

The current first packet is `critical_or_high_risk_missed`, covering row
numbers `1-6` and `18` model assessments. The packet itself is local-only and
must not be committed.

Before and after editing the local sheet, audit the current packet completion
status:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/audit_human_review_batch_status.py \
  --audit-sheet 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/human_risk_atom_audit_sheet.tsv \
  --batch-summary 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_next_review_batch_summary.json \
  --output-dir 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25 \
  --expected-rows 30
```

The status audit is aggregate-only. It must read `batch_complete` before this
packet is treated as ready for aggregate refresh.

For batch entry, generate and fill a local response TSV. This avoids manual
JSON editing while keeping reviewer decisions local-only until aggregate
refresh:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/apply_human_audit_batch_response.py \
  --write-template \
  --audit-sheet 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/human_risk_atom_audit_sheet.tsv \
  --batch-summary 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_next_review_batch_summary.json \
  --output-dir 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25 \
  --expected-rows 30
```

After filling the ignored response TSV, dry-run it with the strict completion
gate:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/apply_human_audit_batch_response.py \
  --require-complete \
  --response-sheet 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/review_responses/2026-05-25T212010_0800_critical_or_high_risk_missed_response_template.tsv \
  --audit-sheet 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/human_risk_atom_audit_sheet.tsv \
  --batch-summary 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_next_review_batch_summary.json \
  --output-dir 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25 \
  --expected-rows 30
```

Use `--write` only after strict dry-run status is `response_complete`. The
current strict template dry-run is `response_pending`, `ok=false`, with
`incomplete_response=1`, as expected before reviewer decisions are entered. A
non-strict dry-run can be used to inspect progress, but it is not the
completion gate.

When the strict dry-run passes, use `--write --refresh-after-write` so the local
sheet write, current-batch status audit, aggregate refresh, readiness audit, and
publishable completion audit are all recorded in one pass. The refresh is
non-strict at this batch stage; `partial_review` is valid progress until all
selected-300 rows and model assessments are complete.

Use the local helper to avoid hand-editing JSON in
`reviewer_model_assessments_json`:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/review_human_risk_atom_audit.py \
  --audit-sheet 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/human_risk_atom_audit_sheet.tsv \
  --list-pending
```

The safe pending summary contains row numbers and aggregate strata only. It
does not print transcripts or hypotheses.

For local review, inspect one row at a time:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/review_human_risk_atom_audit.py \
  --audit-sheet 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/human_risk_atom_audit_sheet.tsv \
  --row-number N \
  --show-row
```

`--show-row` is transcript-bearing local output. Do not paste it into tracked
docs, terminal summaries, commits, issues, or external messages.

Dry-run a row update first:

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

Repeat `--model-review` for every model whose model-level judgement is ready.
Add `--write` only after the dry-run validation output is acceptable. The
helper writes a local backup under `artifacts/backups/` before modifying the
ignored sheet.

## Minimum Aggregate Outputs After Review

First validate the local sheet:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/validate_human_risk_atom_audit.py \
  --audit-sheet 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/human_risk_atom_audit_sheet.tsv \
  --output-dir 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25 \
  --expected-rows 30
```

Before review this should pass with `status=review_pending` and only pending
review warnings. After review, the strict completion gate must pass:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/validate_human_risk_atom_audit.py \
  --audit-sheet 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/human_risk_atom_audit_sheet.tsv \
  --expected-rows 30 \
  --require-complete
```

Use:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/summarize_human_risk_atom_audit.py \
  --audit-sheet 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/human_risk_atom_audit_sheet.tsv \
  --output-dir 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25
```

Before review, this command records `review_pending` and missing required
reviewer fields. After the local sheet is reviewed, it must produce tracked
aggregate files with:

- reviewed row count;
- human-confirmed decision-change count;
- human-confirmed unsafe-downrouting count;
- human-confirmed high-risk-missed count;
- human-confirmed critical-miss count;
- risk-atom category counts;
- low-WER danger count under the reviewed labels;
- per-model human-confirmed signal counts;
- reviewer agreement check if a second reviewer is available.

Then run the human-reviewed predictor gate:

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/analyze_human_audit_predictors.py \
  --audit-sheet 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/human_risk_atom_audit_sheet.tsv \
  --output-dir 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25
```

This compares WER/CER/SRES/CEIS against model-level human decision-change
labels. It must replace proxy predictor language for reviewer-facing claims.

## Completion Criteria

This gate is complete only when:

- the local `30`-row sheet has complete risk/decision reviewer fields, not a
  duplicate transcript review;
- `validate_human_risk_atom_audit.py --require-complete --expected-rows 30`
  passes;
- tracked aggregate annotation stats exist;
- no raw transcript or selected ID leaks into tracked files;
- `analyze_metric_predictors.py` is rerun on reviewed or reviewer-adjusted
  metric inputs;
- the postdoc roadmap marks proxy claims and reviewed claims separately.

Until then, selected-300 SRES/CEIS and recovery numbers remain proxy evidence.

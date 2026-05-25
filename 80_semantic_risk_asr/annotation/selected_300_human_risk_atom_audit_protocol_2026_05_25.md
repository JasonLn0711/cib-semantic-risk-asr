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

## Required Reviewer Fields

Fill these columns in the local sheet:

| Field | Meaning |
| --- | --- |
| `reviewer_verified_transcript` | Human-checked transcript if the reference needs correction; otherwise leave blank or copy only the corrected span. |
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

## Minimum Aggregate Outputs After Review

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

## Completion Criteria

This gate is complete only when:

- the local `30`-row sheet has been reviewed;
- tracked aggregate annotation stats exist;
- no raw transcript or selected ID leaks into tracked files;
- `analyze_metric_predictors.py` is rerun on reviewed or reviewer-adjusted
  metric inputs;
- the postdoc roadmap marks proxy claims and reviewed claims separately.

Until then, selected-300 SRES/CEIS and recovery numbers remain proxy evidence.

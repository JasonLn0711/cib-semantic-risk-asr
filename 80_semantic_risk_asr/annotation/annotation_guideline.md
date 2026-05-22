# Annotation Guideline

## Goal

Annotate ASR errors that can affect downstream scam escalation decisions.

Do not mark every typo. Mark errors that change whether a reviewer, classifier,
or downstream system would understand the case correctly.

## Unit Of Annotation

Default unit: one audio segment / transcript pair.

Required inputs:

- `sample_id`
- split
- reference transcript
- ASR hypothesis
- WER/CER if available
- ASR run id

## Decision-Critical Error Types

Use the taxonomy in `../taxonomy/decision_critical_error_taxonomy.yaml`.

Primary labels:

- `negation`
- `amount`
- `action`
- `actor`
- `intent`
- `time`
- `uncertainty`
- `scam_pattern`

## Severity

Use `0-5`.

| Severity | Meaning |
| ---: | --- |
| 0 | No decision relevance. |
| 1 | Minor wording change. |
| 2 | Could affect interpretation. |
| 3 | Likely affects routing or escalation. |
| 4 | Severe decision-critical corruption. |
| 5 | Reverses or hides a critical decision fact. |

## Downstream Impact

Use `0-3`.

| Impact | Meaning |
| ---: | --- |
| 0 | No expected downstream effect. |
| 1 | May slightly change reviewer interpretation. |
| 2 | May change escalation or priority. |
| 3 | Likely causes wrong escalation, missed intervention, or false reassurance. |

## Recovery Action

Recommended labels:

- `none`
- `human_confirmation`
- `targeted_relistening`
- `clarification_question`
- `priority_review`

## Annotation Sheet

Use `sample_annotation_sheet.tsv`.

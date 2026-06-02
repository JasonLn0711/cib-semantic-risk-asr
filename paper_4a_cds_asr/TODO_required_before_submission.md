# Paper 4-a Required Before Submission

Date: 2026-06-02

Status: do not submit yet. The 100+ row human audit and dual-reviewer agreement
gates are completed at the full selected-300 scope. The remaining mandatory
evidence addition before Computer Speech \& Language submission is
aggregate-safe CEIS ablation, followed by manuscript/table/figure regeneration.
No ablation result should be fabricated.

Recommended before submission:

## 1. Human Audit Expansion

Current completed audit evidence is 300 reviewed rows per reviewer and 900
model-level assessments per reviewer. The repo-safe aggregate completion record
is `70_experiments/runs/janus_300_high_stakes_human_audit_completed_300_dual_reviewer_2026_06_02/`.

| Requirement | Current state | Required before submission |
| --- | --- |
| Reviewed rows | Completed: 300 rows per reviewer | Update manuscript from pilot wording after CEIS ablation |
| Model assessments | Completed: 900 model-level assessments per reviewer | Regenerate predictor/replay/ablation tables from expanded surface |
| Output boundary | Aggregate-only summaries | No raw audio, transcripts, row IDs, reviewer notes, hypotheses, or local response sheets in git |
| Current completion run | `70_experiments/runs/janus_300_high_stakes_human_audit_completed_300_dual_reviewer_2026_06_02/` | Use aggregate-only record; keep completed package local/download-only |

## 2. Dual Reviewer Agreement

The dual-reviewer agreement gate is complete on the same 300-row surface.

| Agreement item | Required statistic |
| --- | --- |
| Two reviewers on the same rows | Completed: Cohen's kappa for row-level decision-change and semantic-risk labels |
| More than two reviewers, if added | Fleiss' kappa for the same categorical labels |
| Reviewer disagreements | Aggregate disagreement counts by field and adjudication policy; no private row content |

Recorded Cohen's kappa values: decision change `0.849970`, semantic-risk label
`1.000000`, expected safe action `0.851426`, and annotation confidence
`0.934274`.

## 3. CEIS Ablation

| Ablation | Missing aggregate input needed |
| --- | --- |
| CEIS full | Versioned aggregate predictor and replay metrics on the expanded reviewed surface. |
| CEIS without atom weights | Recompute CEIS with risk-atom weights set to a constant. |
| CEIS without plausibility | Recompute CEIS with the plausibility term removed or set to a constant. |
| CEIS binary atom | Recompute from binary decision-change / atom-trigger presence rather than weighted distance. |
| Max versus top-k aggregation | Compare maximum aggregation and top-k aggregation over variants. |
| CEIS by atom class | Stratify aggregate metrics by risk atom class without transcript-bearing spans or row identifiers. |

If these artifacts are generated later, they should remain aggregate-only and
must not include raw audio, transcripts, row identifiers, reviewer notes, or
transcript-bearing logs.

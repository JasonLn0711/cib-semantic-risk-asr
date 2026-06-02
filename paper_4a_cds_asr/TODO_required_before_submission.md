# Paper 4-a Required Before Submission

Date: 2026-06-02

Status: required manuscript regeneration complete. The 100+ row human audit,
dual-reviewer agreement, aggregate-safe CEIS ablation, manuscript/table/figure
updates, and PDF validation are completed at the full selected-300 scope.

Recommended before submission:

## 1. Human Audit Expansion

Current completed audit evidence is 300 reviewed rows per reviewer and 900
model-level assessments per reviewer. The repo-safe aggregate completion record
is `70_experiments/runs/janus_300_high_stakes_human_audit_completed_300_dual_reviewer_2026_06_02/`.

| Requirement | Current state | Required before submission |
| --- | --- |
| Reviewed rows | Completed: 300 rows per reviewer | Manuscript updated from pilot-only wording to dual-reviewer evidence |
| Model assessments | Completed: 900 model-level assessments per reviewer | CEIS ablation and replay table added from expanded surface |
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

The CEIS ablation gate is complete. The aggregate-only run is
`70_experiments/runs/janus_300_high_stakes_ceis_ablation_dual_reviewer_2026_06_02/`.

| Ablation | Current state |
| --- | --- |
| CEIS full | Completed on 900 reviewed model-level assessments per reviewer. |
| CEIS without atom weights | Completed; AUC delta versus full CEIS is `0.000000` for strict decision-change labels. |
| CEIS without plausibility | Completed; AUC delta versus full CEIS is `0.000000` for strict decision-change labels. |
| CEIS binary atom | Completed; AUC delta versus full CEIS is approximately `0.000572`. |
| Max versus top-k aggregation | Completed with `ceis_full_top3_mean`; AUC delta versus full CEIS is approximately `0.000550`. |
| CEIS by atom class | Supported as aggregate unstable-atom counts in the run summary; transcript-bearing spans remain outside git. |

The paper-facing interpretation is contribution-first: the ablation shows that
decision-changing risk-atom instability is a stable CDS-ASR evidence signal.
Plausibility and atom weights remain explicit CEIS design components and
calibration handles for richer acoustic and domain-prior validation.

## 4. Final Submission Checks

- [x] Regenerate R figures after the updated evidence ladder and pilot predictor labels.
- [x] Rebuild LaTeX PDF.
- [x] Check citations, references, overfull boxes, and aggregate-only artifact references.
- [x] Confirm no raw audio, transcripts, row identifiers, reviewer notes,
  hypotheses, merged reviewer sheets, or completed review zip are committed.

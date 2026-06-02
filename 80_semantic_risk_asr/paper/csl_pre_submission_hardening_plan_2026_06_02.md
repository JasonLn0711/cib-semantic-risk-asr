# CSL 投稿前補強計畫

Date: 2026-06-02

Status: human audit expansion and dual-reviewer agreement completed; CEIS
ablation remains before CSL submission.

## 判斷

目前 Paper 4-a 是一份可讀、可編譯、aggregate-only 邊界清楚的 scoped
manuscript foundation。2026-06-02 expert review 已完成 selected-300 全量
human audit 與 dual-reviewer agreement，讓 100+ human audit 與 Kappa gate
升級為 completed evidence layer。正式投稿前的剩餘補強是 CEIS ablation 與
manuscript/table/figure regeneration。

## 必補 Gate

| Gate | 目前狀態 | 投稿前目標 | Repo artifact |
| --- | --- | --- | --- |
| Human audit | Completed: 300/300 rows per reviewer | 100+ completed reviewed rows | `70_experiments/runs/janus_300_high_stakes_human_audit_completed_300_dual_reviewer_2026_06_02/` |
| Dual reviewer | Completed: two reviewers on same 300-row surface | 第二位 reviewer 完成同一 100+ row surface | completed local package; tracked aggregate record |
| Reviewer agreement | Completed: Cohen's kappa recorded | Cohen's kappa；若超過兩位 reviewer 則 Fleiss' kappa | `human_audit_reviewer_agreement_summary.json`, `human_audit_reviewer_agreement.tsv` |
| CEIS ablation | 缺 aggregate-safe ablation inputs | CEIS full、without atom weights、without plausibility、binary atom | future aggregate-only ablation run |

## Human Audit Expansion

Expert review completed the full 300-row surface. Both reviewers completed
300/300 row-level fields and 900/900 model-level assessments.

保留規則：

- local review sheet 放在 ignored `artifacts/`。
- tracked outputs 只留 selection summary、stratum coverage、risk atom coverage、model signal coverage。
- Manuscript evidence can now be updated from `30 rows / 90 assessments` pilot
  wording to the completed 300-row / 900-assessment dual-reviewer surface after
  CEIS ablation and figure/table regeneration.

## Dual Reviewer Agreement

第二位 reviewer 已完成同一批 300 rows。Completed labels include:

- `reviewer_would_asr_error_change_decision`
- `reviewer_semantic_risk_label`
- `reviewer_expected_safe_action`
- `reviewer_annotation_confidence`

The aggregate-only agreement record is stored in
`70_experiments/runs/janus_300_high_stakes_human_audit_completed_300_dual_reviewer_2026_06_02/`.
Transcript-bearing merged sheets and the completed zip remain local/download
artifacts.

## CEIS Ablation

下一個 ablation run 應用 local transcript-bearing CEIS metric input 重算，但
只輸出 aggregate predictor / replay summaries。最小 ablation set：

| Variant | Definition |
| --- | --- |
| CEIS full | `plausibility * atom_weight * decision_distance` |
| without atom weights | `plausibility * 1 * decision_distance` |
| without plausibility | `1 * atom_weight * decision_distance` |
| binary atom | binary trigger from atom-level decision change / instability |

主文可以把 ablation 放在 Results 或 Appendix，但投稿版本至少要在 reviewer-facing
claim map 裡明確回答：CEIS 的訊號是否真的來自 plausibility、risk atom weight、
decision distance 的組合，而不是單一 threshold artifact。

## Manuscript Update Rule

Before CEIS ablation and regeneration, the current manuscript may still contain
stale pilot-audit wording that should be treated as pending update:

- `single-expert pilot audit`
- `30 rows / 90 clustered model assessments`
- `no inter-annotator agreement claim`
- `CEIS ablations pending`

After CEIS ablation, rebuild figures, tables, appendix, claim registry, and PDF,
then update the manuscript to the completed 300-row dual-reviewer evidence
surface and move the submission checklist toward ready.

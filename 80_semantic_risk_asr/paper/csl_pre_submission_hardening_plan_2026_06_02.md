# CSL 投稿前補強計畫

Date: 2026-06-02

Status: human audit expansion, dual-reviewer agreement, CEIS ablation, and
latest manuscript/PDF validation recorded; final full-surface table
regeneration remains before CSL submission.

## 判斷

目前 Paper 4-a 是一份可讀、可編譯、aggregate-only 邊界清楚的 scoped
manuscript foundation。2026-06-02 expert review 已完成 selected-300 全量
human audit 與 dual-reviewer agreement，讓 100+ human audit 與 Kappa gate
升級為 completed evidence layer。CEIS ablation 也已在同一 dual-reviewer
surface 上完成。Latest manuscript surfaces 已更新並可編譯。正式投稿前的
剩餘補強是從 completed selected-300 dual-reviewer evidence surface 重新產生
final predictor、recovery、CEIS ablation tables，然後做最後 PDF validation。

## 必補 Gate

| Gate | 目前狀態 | 投稿前目標 | Repo artifact |
| --- | --- | --- | --- |
| Human audit | Completed: 300/300 rows per reviewer | 100+ completed reviewed rows | `70_experiments/runs/janus_300_high_stakes_human_audit_completed_300_dual_reviewer_2026_06_02/` |
| Dual reviewer | Completed: two reviewers on same 300-row surface | 第二位 reviewer 完成同一 100+ row surface | completed local package; tracked aggregate record |
| Reviewer agreement | Completed: Cohen's kappa recorded | Cohen's kappa；若超過兩位 reviewer 則 Fleiss' kappa | `human_audit_reviewer_agreement_summary.json`, `human_audit_reviewer_agreement.tsv` |
| CEIS ablation | Completed: aggregate-safe dual-reviewer run | CEIS full、without atom weights、without plausibility、binary atom、top-3 | `70_experiments/runs/janus_300_high_stakes_ceis_ablation_dual_reviewer_2026_06_02/` |

## Human Audit Expansion

Expert review completed the full 300-row surface. Both reviewers completed
300/300 row-level fields and 900/900 model-level assessments.

保留規則：

- local review sheet 放在 ignored `artifacts/`。
- tracked outputs 只留 selection summary、stratum coverage、risk atom coverage、model signal coverage。
- Manuscript evidence is being updated from pilot wording to the completed
  300-row / 900-assessment dual-reviewer surface with CEIS ablation.

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

CEIS ablation 已應用 local-only completed review 與 CEIS metric input 重算，
tracked outputs 只保留 aggregate predictor / replay summaries：

| Variant | Definition |
| --- | --- |
| CEIS full | `plausibility * atom_weight * decision_distance` |
| without atom weights | `plausibility * 1 * decision_distance` |
| without plausibility | `1 * atom_weight * decision_distance` |
| binary atom | binary trigger from atom-level decision change / instability |
| top-3 mean | top-3 mean over full CEIS variant components |

主文已加入 Results ablation 小節與 table。貢獻導向解讀是：decision-changing
risk-atom instability 是穩定 CDS-ASR evidence signal；plausibility 與 atom
weights 是 CEIS 的 explicit calibration handles，可支撐後續更豐富的 acoustic
與 domain-prior validation。

## Manuscript Update Rule

Manuscript regeneration should verify that stale pilot-only evidence wording
has been replaced where it refers to the submission-critical evidence layer.
The text should no longer describe the main validation surface as a
single-reviewer pilot, a 30/90 assessment-only evidence layer, an agreement-free
review, or a pending-ablation state.

Latest manuscript validation is recorded in
`80_semantic_risk_asr/paper/latest_manuscript_validation_2026_06_02.md`.

Next step: regenerate final predictor, recovery, and CEIS ablation tables from
the completed selected-300 dual-reviewer evidence surface, then re-run PDF and
submission readiness validation.

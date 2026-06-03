# CSL 投稿前補強計畫

Date: 2026-06-02

Status: human audit expansion, dual-reviewer agreement, initial CEIS ablation,
latest manuscript/PDF validation, final Day-1 freeze package, and full 300/900
aggregate regeneration are recorded. The current final-CSL gate is manuscript
rewrite plus the remaining policy-distance-only CEIS ablation if the full
three-component CEIS mechanism claim is retained.

## 判斷

目前 Paper 4-a 已經從 pilot manuscript foundation 推進到 final-CSL
aggregate regeneration layer。2026-06-02 expert review 完成 selected-300 全量
human audit 與 dual-reviewer agreement，讓 100+ human audit 與 Kappa gate
升級為 completed evidence layer。2026-06-03 final run 進一步凍結 row-level
budget semantics，並用 completed package 重生 300-row / 900-assessment
aggregate predictor、fixed-budget、selection-exclusion、atom evidence、residual
unsafe breakdown 與 manifest hash。

最重要的統計結論是：row-level severe-miss positives 只有 `6`，低於預先
設定的 `20` 門檻。因此 final manuscript 必須啟動 failover：primary
endpoint 改為 decision-change AUC；severe missed-escalation frontier 只能作為
descriptive high-severity evidence。這不是退守，而是 claim-evidence alignment：
CEIS 的貢獻要寫成 counterfactual decision-stability signal，並清楚呈現它與
SRES 的互補與邊界。

## 必補 Gate

| Gate | 目前狀態 | 投稿前目標 | Repo artifact |
| --- | --- | --- | --- |
| Human audit | Completed: 300/300 rows per reviewer | 100+ completed reviewed rows | `70_experiments/runs/janus_300_high_stakes_human_audit_completed_300_dual_reviewer_2026_06_02/` |
| Dual reviewer | Completed: two reviewers on same 300-row surface | 第二位 reviewer 完成同一 100+ row surface | completed local package; tracked aggregate record |
| Reviewer agreement | Completed: Cohen's kappa recorded | Cohen's kappa；若超過兩位 reviewer 則 Fleiss' kappa | `human_audit_reviewer_agreement_summary.json`, `human_audit_reviewer_agreement.tsv` |
| CEIS ablation | Completed with claim downgrade: policy-distance-only matches full CEIS | CEIS full、without atom weights、without plausibility、binary atom、policy-distance-only、top-3 | `70_experiments/runs/janus_300_high_stakes_ceis_ablation_final_csl_2026_06_03/` |
| Final Day-1 freeze | Completed: contracts and statistical analysis plan recorded | Freeze `f`, CEIS config, variant protocol, budget denominator, tie rule, failover | `80_semantic_risk_asr/paper/final_csl_audit_package_2026_06_03/` |
| Full 300/900 regeneration | Completed: aggregate predictor/replay/stress outputs produced | 30/90 exits main claim; row-level budget is primary surface | `70_experiments/runs/janus_300_high_stakes_final_csl_2026_06_03/` |

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

Final execution note: the final-CSL ablation suite now includes
`policy-distance-only`. That variant matches full CEIS on the aggregate reviewed
surface. The manuscript must therefore narrow the CEIS mechanism claim:
decision distance carries the observed ranking on this surface, while
plausibility and atom weights remain explicit method components, calibration
handles, and interpretable linguistic/localization layers rather than proven
performance drivers.

## Final CSL Aggregate Regeneration

The 2026-06-03 regeneration run is recorded in
`70_experiments/runs/janus_300_high_stakes_final_csl_2026_06_03/`.

Key outputs:

- `final_csl_summary.json`
- `final_csl_predictor_performance.tsv`
- `final_csl_auc_delta_bootstrap.tsv`
- `final_csl_fixed_budget_frontier_row_level.tsv`
- `final_csl_selection_exclusion_sensitivity.tsv`
- `final_csl_atom_linguistic_evidence.tsv`
- `final_csl_residual_unsafe_breakdown.tsv`
- `final_csl_variant_source_coverage.tsv`
- `final_csl_manifest_hashes.tsv`

The run confirms:

- selected rows: `300`;
- model-level assessments: `900`;
- row-level decision-change yes: `14`;
- row-level decision-change yes-or-uncertain: `20`;
- row-level severe miss: `6`;
- row-level critical miss: `1`;
- row-level unsafe downrouting: `22`;
- primary endpoint status: `failover_to_decision_change_auc`.

This evidence resolves the 30/90 mismatch for aggregate regeneration, while it
also narrows the empirical claim. Severe missed-escalation remains valuable as
a descriptive high-severity replay, but the primary result should now be
decision-change prediction under the clustered analysis plan.

The variant-count/source gate is also recorded at aggregate boundary:
model-level variant count min `2`, median `4.0`, mean `3.664444`, max `5`,
with nonzero variants for all 900 model assessments. Reject-reason counts are
not available in the current CEIS scored input, so the final manuscript can
report variant-count stress testing and source coverage, while leaving
reject-reason taxonomy as a generator-log extension.

## Manuscript Update Rule

Manuscript regeneration should verify that stale pilot-only evidence wording
has been replaced where it refers to the submission-critical evidence layer.
The text should no longer describe the main validation surface as a
single-reviewer pilot, a 30/90 assessment-only evidence layer, an agreement-free
review, or a pending-ablation state.

Latest manuscript validation is recorded in
`80_semantic_risk_asr/paper/latest_manuscript_validation_2026_06_02.md`.

First-principle Round 1 pressure-test answers and derived blocking gates are
recorded in
`80_semantic_risk_asr/paper/csl_first_principle_pressure_test_round1_2026_06_03.md`.

First-principle Round 2 pressure-test answers are recorded in
`80_semantic_risk_asr/paper/csl_first_principle_pressure_test_round2_2026_06_03.md`.
Round 2 fixes the primary endpoint as severe-miss remaining at pre-specified
early fixed budgets, defines CEIS as complementary to SRES, and sets the five
hard CSL red lines for final submission.

First-principle Round 3 pressure-test answers are recorded in
`80_semantic_risk_asr/paper/csl_first_principle_pressure_test_round3_2026_06_03.md`.
Round 3 freezes the publishable claim set, experiment matrix, delete/rewrite
list, CSL narrative spine, and the remaining gate answers. The primary endpoint
is row-level severe-miss remaining at pre-specified `10-20%` fixed trigger
budgets, with decision-change AUC as failover if severe-miss positives are
fewer than `20`.

The final CSL execution plan is recorded in
`80_semantic_risk_asr/paper/csl_final_execution_plan_2026_06_03.md`.

The final freeze package is recorded in
`80_semantic_risk_asr/paper/final_csl_audit_package_2026_06_03/`.

Next step: finish table/figure regeneration around the failover endpoint,
remove all 30/90 main-result claims, keep CEIS as a scoped companion
decision-stability layer, and reflect the policy-distance-only ablation by
narrowing the CEIS mechanism claim before final PDF/submission readiness
validation.

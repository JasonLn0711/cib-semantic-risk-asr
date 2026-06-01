# CDS-ASR 主文圖表收斂策略

Date: 2026-06-01

## 結論

主文不要放 11 張圖。這篇稿件若要投頂尖期刊，主文圖表應收斂成四條線：

1. 方法：CDS-ASR pipeline、risk atom schema、evidence unit / boundary。
2. 核心證據：CEIS / SRES / WER / CER 對 human-reviewed decision-change 的 predictor evidence。
3. 風險機制：risk atom 如何連到 criticality 與 decision-change。
4. 政策 replay：risk-triggered replay 如何消除 severe missed outcomes，同時保留 residual unsafe downrouting 的 governance boundary。

目前 `generate_paper_figures.R` 產出 F1-F11，且 manuscript 的 Figure Package 表已列出完整圖包。這對 reproducibility 很好，但不適合原封不動放主文。Figure Package table 是 artifact manifest / reproducibility surface，不是 scientific result，應移到 supplement 或 repo manifest，不應佔主文頁面。

主文建議保留：

- F1 CDS-ASR Pipeline，小修成更學術的 method figure。
- F2/F6 合併成一張 `Study design and evidence boundary`，或改成 evidence ladder 表。
- F3 Predictor AUC，重畫成含 row-clustered CI 的 point-range / forest plot。
- F4 Recovery Outcomes，重畫成 residual risk facets。
- F7 Budget-Risk Frontier，重畫成 step/line plot，明確標 observed budget。
- F10 Human-Reviewed Risk-Atom Outcomes，重畫成 rate + count plot。

補充或移除：

- F8 Low-WER Danger Signals：補充；若留主文，改成 numerator/denominator dot plot。
- F9 Risk-Atom Instability Heatmap：補充。
- F5 Model Lane State：移 supplement 或刪，Table S2 足夠。
- F11 Risk-Atom Entropy Heatmap：移 supplement 或刪。稿中已說 word-level confusion entropy 不能公開，F11 只是 atom-class entropy，主文貢獻偏弱。

核心表格：

- Table 3 Predictor：必留主文。
- Table 4 Recovery Policy：必留主文。
- Table 1 Main ASR Benchmark：可留主文，但大幅縮短，刪超長 run ID。
- Table 2 Candidate Lane：移 supplement。
- Risk Atom Schema table：留主文，作為正式 Table 1 或方法定義表。
- Evaluation Units / N-ladder table：留主文或與 F2/F6 合併。
- Claim Registry table：移 appendix / supplement。
- Appendix Table A1：留 appendix，縮短小數。

## 目前最大版面問題

目前 PDF 第 10-13 頁的 Table 1-4 與 Figure Package table 字體過小，讀起來像 repo manifest，不像給 reviewer 閱讀的 scientific table。LaTeX preamble 目前曾把 `tabularx` 壓到 4pt，這是 presentation weakness。表格應由 R 產生乾淨的 `.tex` fragments，主文用 `\input{...}` 載入；主文表格字級應回到可讀大小。

建議 LaTeX table baseline：

```tex
\AtBeginEnvironment{tabularx}{\small}
\setlength{\tabcolsep}{3pt}
\renewcommand{\arraystretch}{1.12}
```

## 圖表逐項判斷

| 圖表 | 建議 | 理由 | R/排版處理 |
| --- | --- | --- | --- |
| Risk Atom Schema table | 留主文 | 方法定義；negation、amount、actor、time 等 atom 是 CEIS 概念地基。 | 改成正式 Table 1，用正常字體。 |
| Evaluation Units / N-ladder table | 留主文或與 F2/F6 合併 | 30 rows / 90 assessments 的 clustered 結構是 reviewer 會追問的核心限制。 | 改成 Study evidence ladder 表，或與 F2/F6 合併。 |
| Table 1 Main ASR Benchmark | 留，但縮短 | 258-row split 是背景 benchmark；final risk/recovery claim 不靠這張表。 | 刪超長 run ID，改用 Model family；run ID 放 supplement。 |
| Table 2 Candidate Lane | 移 supplement | 工程 gate，不是主結果；主文一句話即可。 | 變 Table S2。 |
| Table 3 Predictor | 必留主文 | CEIS AUC、recall 1.0、FN 0 是核心 claim；需保留 CEIS/SRES CI overlap 的 scope control。 | 刪 Unit 重複欄；加 AUC/F1 CI；粗體標核心最佳值。 |
| Table 4 Recovery Policy | 必留主文 | 政策 replay 主結果：SRES/CEIS severe miss 歸零，但 unsafe downrouting 還有 24。 | confidence unavailable 移 footnote；保留 residual unsafe downrouting。 |
| Figure Package table | 刪主文，移 supplement/repo manifest | Artifact manifest，不是 scientific result；佔空間且重複 caption。 | 不放 article body。 |
| F1 CDS-ASR Pipeline | 留主文，小修 | 方法總覽必要；現版偏 slide。 | 簡化顏色，增加 decision function fixed before CEIS / aggregate-only release 註記。 |
| F2 Evidence Boundary | 不單獨留；與 F6 合併 | 與 F6 都在講 evidence boundary / N ladder，功能重複。 | 合併成 Study design and evidence boundary。 |
| F3 Predictor AUC | 留主文，重畫 | 純 bar chart 缺 uncertainty；頂刊 reviewer 會問 CI。 | 改 point-range forest plot。 |
| F4 Recovery Outcomes | 留主文，重畫 | 現版 0 label 太多，policy 縮寫與順序不自然。 | facets：high-risk missed、critical miss、unsafe downrouting；直接顯示 residual risk。 |
| F5 Model Lane State | 移 supplement 或刪 | 工程狀態，不是結果，和 Table 2 重複。 | Table S2 足夠。 |
| F6 Evidence N-Ladder | 與 F2 合併或改表 | 必須交代 cluster，但不用單獨佔一張主文圖。 | 合併。 |
| F7 Budget-Risk Frontier | 留主文，重畫 | 支撐 CEIS 在低 budget 先歸零 severe misses。 | step/line plot，加 uncertainty 或至少明確標 observed budget。 |
| F8 Low-WER Danger Signals | 移 supplement，或小圖 | 支撐標題，但目前是 aggregate proxy，不是 human-reviewed core evidence，且分母差異大。 | 若留主文，改 numerator/denominator dot plot。 |
| F9 Risk-Atom Instability Heatmap | 補充 | 機制圖有用，但與 F11 資料重疊，且是 proxy count。 | Supplement Figure。 |
| F10 Human-Reviewed Risk-Atom Outcomes | 留主文，重畫 | 把 atom coverage 接到 criticality 與 decision-change，是 human-reviewed evidence，比 F9 更適合主文。 | 改 rate + count plot。 |
| F11 Risk-Atom Entropy Heatmap | 移 supplement 或刪 | 只是 atom-class entropy；主文貢獻偏弱。 | Supplement only。 |
| Claim Registry table | 移 appendix/supplement | 對 governance 有用，對主線太像 internal audit。 | 補充即可。 |
| Appendix Table A1 | 留 appendix | 支撐 F7 數值；appendix 可接受。 | 保留為 Table S/A1，縮短小數。 |

## R 生成策略

第一原則：圖本體只呈現資料，不塞 caption、source、privacy text。Source、privacy boundary、interpretation 放 LaTeX caption 或 supplement。避免圖內 title/subtitle/source 與 LaTeX caption 重複，降低閱讀成本。

第二原則：表格由 R 產生乾淨 `.tex` fragments，主文使用 `\input{...}`。不要在 LaTeX 裡用 4pt `tabularx` 壓表格。建議新增：

- `80_semantic_risk_asr/paper/tables/table1_main_asr.tex`
- `80_semantic_risk_asr/paper/tables/table3_predictor.tex`
- `80_semantic_risk_asr/paper/tables/table4_recovery.tex`
- `80_semantic_risk_asr/paper/tables/table_s2_candidates.tex`
- `80_semantic_risk_asr/paper/tables/table_a1_fixed_budget_frontier.tex`

建議 R package baseline：

```r
suppressPackageStartupMessages({
  library(tidyverse)
  library(janitor)
  library(scales)
  library(glue)
  library(knitr)
  library(kableExtra)
  library(svglite)
})

root <- "."
fig_dir <- file.path(root, "80_semantic_risk_asr/paper/figures")
tab_dir <- file.path(root, "80_semantic_risk_asr/paper/tables")
dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(tab_dir, recursive = TRUE, showWarnings = FALSE)

theme_cds <- function(base_size = 9) {
  theme_minimal(base_size = base_size, base_family = "sans") +
    theme(
      plot.title = element_text(face = "bold", size = base_size + 2),
      plot.subtitle = element_text(size = base_size, colour = "grey30"),
      axis.title = element_text(face = "bold"),
      panel.grid.minor = element_blank(),
      legend.position = "bottom",
      legend.title = element_blank(),
      strip.text = element_text(face = "bold"),
      plot.caption = element_blank()
    )
}

save_pub <- function(p, name, width = 6.8, height = 3.8) {
  ggsave(file.path(fig_dir, paste0(name, ".pdf")), p,
         width = width, height = height, device = cairo_pdf)
  svglite::svglite(file.path(fig_dir, paste0(name, ".svg")),
                   width = width, height = height)
  print(p)
  dev.off()
}

fmt_num <- function(x, digits = 3) {
  ifelse(is.na(x), "n/a", formatC(x, digits = digits, format = "f"))
}
```

## 主文建議插入順序

```tex
% Methods
\paperfigure{f1_cds_asr_pipeline.pdf}
{CDS-ASR converts audio into ASR hypotheses and runtime signals, extracts risk atoms, generates plausible variants, scores SRES/CEIS, and applies conservative action.}
{method section}

\paperfigure{f2_evidence_design.pdf}
{The study separates ASR split evidence, selected-300 provenance, 30 reviewed rows, and 90 clustered model assessments.}
{method evidence units and publishable evidence summary}

% Results
\input{80_semantic_risk_asr/paper/tables/table1_main_asr.tex}
\input{80_semantic_risk_asr/paper/tables/table3_predictor.tex}

\paperfigure{f3_predictor_auc.pdf}
{CEIS has the highest point-estimate decision-change AUC and reaches zero false negatives at the diagnostic operating point; row-clustered intervals remain overlapping with SRES.}
{human_audit_predictor_comparison.tsv and clustered CI table}

\input{80_semantic_risk_asr/paper/tables/table4_recovery.tex}

\paperfigure{f4_recovery_outcomes.pdf}
{Risk-triggered policies eliminate high-risk missed and critical miss counts in aggregate replay, while residual unsafe downrouting remains.}
{policy_comparison.tsv}

\paperfigure{f7_budget_risk_frontier.pdf}
{Fixed-budget replay shows the trigger budget needed to eliminate severe missed outcomes under scoped labels.}
{fixed_budget_recovery_frontier.tsv}

\paperfigure{f10_human_reviewed_atom_outcomes.pdf}
{Human review connects risk-atom coverage to criticality and decision-change evidence across reviewed rows.}
{human_audit_risk_atom_review.tsv}
```

## Supplement 建議插入順序

```tex
\input{80_semantic_risk_asr/paper/tables/table_s2_candidates.tex}
\input{80_semantic_risk_asr/paper/tables/table_a1_fixed_budget_frontier.tex}

\paperfigure{f8_low_wer_danger.pdf}
{Low-WER danger signals under aggregate proxy evidence.}
{low_wer_danger_summary.tsv}

\paperfigure{f9_risk_atom_instability_heatmap.pdf}
{Risk-atom instability by model under aggregate proxy evidence.}
{risk_atom_instability.tsv}

\paperfigure{f11_risk_atom_entropy_heatmap.pdf}
{Atom-class entropy from aggregate instability counts.}
{risk_atom_instability.tsv}
```

## 需要新增的分析

頂刊 reviewer 最可能攻擊 CEIS method-hardening。若有 aggregate-safe recomputation，建議新增 Supplementary Figure / Table：

- uniform-weight ablation；
- no-plausibility ablation；
- binary decision-flip ablation；
- max vs top-k mean；
- CEIS by atom class；
- 指標至少包含 AUC、F1、FN。

如果資料或 aggregate-safe recomputation 不足，不要硬畫；稿件文字要寫成 planned validation，而不是已完成。

## 下一步實作清單

1. 改 `generate_paper_figures.R`：保留完整 F1-F11 reproducibility 輸出，但主文版輸出聚焦 F1、F2 evidence design、F3、F4、F7、F10。
2. 新增 `80_semantic_risk_asr/paper/tables/`，由 R 產生主文與 supplement `.tex` fragments。
3. 修改 `manuscript_submission.tex`：移除 Figure Package table 與主文 F5/F8/F9/F11；F8/F9/F11 改 supplement；F2/F6 合併。
4. 表格字級恢復為 reviewer-readable，主表不再使用 4pt。
5. 重編 PDF，要求無 overfull hbox，並人工抽查 Table 1、Table 3、Table 4、F3、F4、F7、F10 的可讀性。
6. 若沒有 CEIS ablation aggregate-safe 資料，將 manuscript 中相關語句改成 planned validation。

整體策略：主文少圖、強圖；補充材料完整交代 audit/reproducibility。現有證據鏈可以成立，但 presentation 要從內部技術報告收斂成期刊稿。

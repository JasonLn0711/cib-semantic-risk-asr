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

## 完整 R/LaTeX 實作草稿附錄

以下保留 implementation-level 草稿。實作時仍需先用實際 TSV 欄位名稱檢查 `clean_names()` 後的欄位，必要時調整 `transmute()`。

### R package baseline

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

### Table 1: Main ASR Benchmark

```r
make_table1_main_asr <- function() {
  path <- "70_experiments/runs/janus_258_test_split_asr_cds_proxy/asr_cds_proxy_comparison.tsv"

  df <- readr::read_tsv(path, show_col_types = FALSE) %>%
    janitor::clean_names()

  out <- df %>%
    transmute(
      Model = model_family,
      Rows = rows,
      `CER zh micro` = cer_zh_micro,
      `WER zh jieba micro` = wer_zh_jieba_micro,
      `Unsafe downrouting` = unsafe_downrouting,
      `High-risk missed` = high_risk_missed,
      `Locale violations` = locale_violation_rows,
      `Paper role` = case_when(
        str_detect(str_to_lower(model_family), "partial") ~ "Strongest ASR evidence layer",
        str_detect(str_to_lower(model_family), "whisper") ~ "Comparable baseline",
        TRUE ~ "Split/model context"
      )
    ) %>%
    arrange(`CER zh micro`)

  kbl(
    out,
    format = "latex",
    booktabs = TRUE,
    escape = TRUE,
    digits = 2,
    caption = "Main ASR benchmark on the canonical 258-row split. Run identifiers are reported in the supplement."
  ) %>%
    kable_styling(
      latex_options = c("hold_position"),
      font_size = 8,
      full_width = TRUE
    ) %>%
    column_spec(1, width = "3.0cm") %>%
    column_spec(8, width = "3.0cm") %>%
    footnote(
      general = "CER zh micro is the primary ASR surface metric; WER zh jieba micro is supplemental. Unsafe downrouting and high-risk missed counts are split/model-comparison evidence, not final selected-300 human-reviewed risk claims.",
      threeparttable = TRUE
    ) %>%
    save_kable(file.path(tab_dir, "table1_main_asr.tex"))
}
```

LaTeX:

```tex
\input{80_semantic_risk_asr/paper/tables/table1_main_asr.tex}
```

### Table S2: Candidate Lane

```r
make_table_s2_candidates <- function() {
  path <- "70_experiments/runs/asr_candidate_current_recheck_2026_05_26/candidate_current_recheck_summary.tsv"

  df <- readr::read_tsv(path, show_col_types = FALSE) %>%
    janitor::clean_names()

  out <- df %>%
    transmute(
      Candidate = candidate,
      Gate = current_gate,
      Rows = rows,
      CER = cer_zh_micro,
      WER = wer_zh_jieba_micro,
      `Locale/runtime result` = locale_runtime_result,
      Decision = decision
    )

  kbl(
    out,
    format = "latex",
    booktabs = TRUE,
    escape = TRUE,
    digits = 2,
    caption = "Candidate and exploratory lane evidence."
  ) %>%
    kable_styling(latex_options = c("hold_position", "scale_down"),
                  font_size = 7) %>%
    save_kable(file.path(tab_dir, "table_s2_candidates.tex"))
}
```

### Table 3: Predictor

```r
make_table3_predictor <- function() {
  path <- "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_predictor_comparison.tsv"

  df <- readr::read_tsv(path, show_col_types = FALSE) %>%
    janitor::clean_names()

  out <- df %>%
    mutate(
      predictor = recode(predictor,
                         "SRES total" = "SRES",
                         "CEIS max" = "CEIS",
                         .default = predictor),
      `AUC` = sprintf("%.3f", auc),
      `AUC 95\\% CI` = glue("{sprintf('%.3f', row_clustered_auc_ci_low)}--{sprintf('%.3f', row_clustered_auc_ci_high)}"),
      `Threshold` = fmt_num(diagnostic_threshold, 2),
      `Best F1` = sprintf("%.3f", best_f1),
      `F1 95\\% CI` = glue("{sprintf('%.3f', row_clustered_f1_ci_low)}--{sprintf('%.3f', row_clustered_f1_ci_high)}"),
      `Precision` = sprintf("%.3f", precision),
      `Recall` = sprintf("%.3f", recall),
      `FN` = false_negative
    ) %>%
    transmute(
      Predictor = predictor,
      AUC,
      `AUC 95\\% CI`,
      Threshold,
      `Best F1`,
      `F1 95\\% CI`,
      Precision,
      Recall,
      FN,
      Role = paper_use
    )

  kbl(
    out,
    format = "latex",
    booktabs = TRUE,
    escape = FALSE,
    caption = "Predictor performance against human-reviewed decision-change labels. Unit: 90 model assessments clustered within 30 reviewed audio rows."
  ) %>%
    kable_styling(latex_options = c("hold_position"),
                  font_size = 8,
                  full_width = TRUE) %>%
    row_spec(which(out$Predictor == "CEIS"), bold = TRUE) %>%
    footnote(
      general = "Thresholds are diagnostic operating points selected on the scoped audit set, not frozen deployment thresholds. CEIS has the highest point-estimate AUC and zero false negatives at the diagnostic threshold; SRES has the highest best-threshold F1.",
      threeparttable = TRUE
    ) %>%
    save_kable(file.path(tab_dir, "table3_predictor.tex"))
}
```

### Table 4: Recovery Policy

```r
make_table4_recovery <- function() {
  path <- "70_experiments/runs/janus_300_high_stakes_recovery_human_reviewed_2026_05_26/policy_comparison.tsv"

  df <- readr::read_tsv(path, show_col_types = FALSE) %>%
    janitor::clean_names()

  out <- df %>%
    filter(!str_detect(str_to_lower(policy), "calibrated")) %>%
    mutate(
      Policy = recode(policy,
        "No recovery" = "No recovery",
        "SRES-triggered recovery" = "SRES recovery",
        "CEIS-triggered conservative action" = "CEIS conservative action",
        "CEIS ensemble arbitration" = "CEIS ensemble arbitration",
        .default = policy
      ),
      `Budget` = sprintf("%.3f", recovery_budget),
      `Budget 95\\% CI` = glue("{sprintf('%.3f', row_clustered_budget_ci_low)}--{sprintf('%.3f', row_clustered_budget_ci_high)}"),
      `Severe misses eliminated` = severe_misses_eliminated,
      `Severe misses remaining 95\\% CI` = row_clustered_severe_miss_95_ci,
      `Triggers / severe miss eliminated` = ifelse(
        is.na(triggers_per_severe_miss_eliminated),
        "n/a",
        sprintf("%.1f", triggers_per_severe_miss_eliminated)
      )
    ) %>%
    transmute(
      Policy,
      `Unsafe downrouting` = unsafe_downrouting,
      `High-risk missed` = high_risk_missed,
      `Critical miss` = critical_miss,
      Budget,
      `Budget 95\\% CI`,
      `Severe misses eliminated`,
      `Severe misses remaining 95\\% CI`,
      `Triggers / severe miss eliminated`
    )

  kbl(
    out,
    format = "latex",
    booktabs = TRUE,
    escape = FALSE,
    caption = "Aggregate policy replay under human-reviewed selected-300 labels."
  ) %>%
    kable_styling(latex_options = c("hold_position"),
                  font_size = 8,
                  full_width = TRUE) %>%
    row_spec(which(str_detect(out$Policy, "CEIS conservative")), bold = TRUE) %>%
    footnote(
      general = "Confidence-only recovery is not shown as a main policy because calibrated confidence was unavailable and produced no triggers. Residual unsafe downrouting remains after risk-triggered policies and should be treated as a separate governance issue.",
      threeparttable = TRUE
    ) %>%
    save_kable(file.path(tab_dir, "table4_recovery.tex"))
}
```

### F1: Pipeline

```r
make_f1_pipeline <- function() {
  nodes <- tribble(
    ~step, ~label, ~detail, ~x,
    1, "Audio", "speech input", 1,
    2, "ASR", "hypothesis + signals", 2,
    3, "Risk atoms", "decision-critical spans", 3,
    4, "Variants", "plausible ASR alternatives", 4,
    5, "SRES / CEIS", "risk + decision instability", 5,
    6, "Conservative action", "recover, escalate, or abstain", 6
  )

  p <- ggplot(nodes) +
    geom_rect(
      aes(xmin = x - 0.42, xmax = x + 0.42, ymin = 0, ymax = 1),
      fill = "white", colour = "grey25", linewidth = 0.5
    ) +
    geom_segment(
      data = nodes %>% filter(step < 6),
      aes(x = x + 0.42, xend = x + 0.58, y = 0.5, yend = 0.5),
      arrow = arrow(length = unit(0.08, "in")),
      linewidth = 0.35
    ) +
    geom_text(aes(x = x, y = 0.62, label = label),
              fontface = "bold", size = 3.1) +
    geom_text(aes(x = x, y = 0.38, label = detail),
              size = 2.2, lineheight = 0.9) +
    annotate(
      "text",
      x = 3.5, y = -0.22,
      label = "Human review supplies evaluation labels only; recovery policies are automatic and aggregate-evaluated.",
      size = 2.4, colour = "grey30"
    ) +
    coord_cartesian(xlim = c(0.45, 6.55), ylim = c(-0.35, 1.15), clip = "off") +
    labs(title = "CDS-ASR decision-stability pipeline") +
    theme_void(base_size = 9) +
    theme(plot.title = element_text(face = "bold", hjust = 0))

  save_pub(p, "f1_cds_asr_pipeline", width = 6.8, height = 1.8)
}
```

### F2 + F6: Study Design / Evidence Boundary

```r
make_f2_evidence_design <- function() {
  df <- tribble(
    ~layer, ~unit, ~n, ~claim,
    "ASR split", "audio rows", "258", "model-comparison context",
    "Selected provenance", "candidate rows / outputs", "300", "enriched audit surface",
    "Human-reviewed audit", "audio rows", "30", "decision-critical review unit",
    "Reviewed assessments", "model-row assessments", "90", "predictor and replay evidence"
  ) %>%
    mutate(x = row_number())

  p <- ggplot(df) +
    geom_rect(aes(xmin = x - .43, xmax = x + .43, ymin = 0, ymax = 1),
              fill = "white", colour = "grey25", linewidth = 0.45) +
    geom_segment(
      data = df %>% filter(x < max(x)),
      aes(x = x + .43, xend = x + .57, y = .5, yend = .5),
      arrow = arrow(length = unit(0.08, "in")),
      linewidth = 0.35
    ) +
    geom_text(aes(x = x, y = .76, label = layer),
              fontface = "bold", size = 2.7, lineheight = .9) +
    geom_text(aes(x = x, y = .50, label = glue("Unit: {unit}\nN = {n}")),
              size = 2.4, lineheight = .9) +
    geom_text(aes(x = x, y = .22, label = claim),
              size = 2.15, colour = "grey30", lineheight = .9) +
    annotate(
      "label",
      x = 2.5, y = -0.28,
      label = "Cluster rule: the 90 model assessments are clustered within 30 reviewed rows.",
      size = 2.5, label.size = 0.2, fill = "grey97"
    ) +
    coord_cartesian(xlim = c(.45, 4.55), ylim = c(-.5, 1.1), clip = "off") +
    labs(title = "Study evidence ladder and release boundary") +
    theme_void(base_size = 9) +
    theme(plot.title = element_text(face = "bold", hjust = 0))

  save_pub(p, "f2_evidence_design", width = 6.8, height = 2.0)
}
```

LaTeX replacement:

```tex
\paperfigure{f2_evidence_design.pdf}
{The study separates ASR split evidence, selected-300 provenance, 30 reviewed rows, and 90 clustered model assessments.}
{method evidence units and publishable evidence summary}
```

### F3: Predictor AUC with CI

```r
make_f3_predictor_auc <- function() {
  path <- "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_predictor_comparison.tsv"

  df <- readr::read_tsv(path, show_col_types = FALSE) %>%
    janitor::clean_names() %>%
    mutate(
      predictor = recode(predictor,
                         "SRES total" = "SRES",
                         "CEIS max" = "CEIS",
                         .default = predictor),
      predictor = factor(predictor, levels = c("WER", "CER", "SRES", "CEIS")),
      label = glue("AUC {sprintf('%.3f', auc)}\nRecall {sprintf('%.2f', recall)}, FN {false_negative}")
    )

  p <- ggplot(df, aes(x = auc, y = predictor)) +
    geom_errorbarh(
      aes(xmin = row_clustered_auc_ci_low,
          xmax = row_clustered_auc_ci_high),
      height = 0.16,
      linewidth = 0.45,
      colour = "grey35"
    ) +
    geom_point(size = 2.4) +
    geom_text(aes(label = label), nudge_y = 0.23, size = 2.4, hjust = 0.5) +
    scale_x_continuous(limits = c(0.5, 1.0), breaks = seq(0.5, 1.0, 0.1)) +
    labs(
      title = "Predicting human-reviewed decision change",
      subtitle = "AUC with row-clustered 95% intervals; 90 model assessments clustered within 30 rows.",
      x = "AUC",
      y = NULL
    ) +
    theme_cds()

  save_pub(p, "f3_predictor_auc", width = 6.4, height = 3.0)
}
```

### F4: Recovery Outcomes

```r
make_f4_recovery_outcomes <- function() {
  path <- "70_experiments/runs/janus_300_high_stakes_recovery_human_reviewed_2026_05_26/policy_comparison.tsv"

  df <- readr::read_tsv(path, show_col_types = FALSE) %>%
    janitor::clean_names() %>%
    filter(!str_detect(str_to_lower(policy), "calibrated")) %>%
    mutate(
      policy_short = recode(policy,
        "No recovery" = "No recovery",
        "SRES-triggered recovery" = "SRES",
        "CEIS-triggered conservative action" = "CEIS",
        "CEIS ensemble arbitration" = "CEIS ensemble",
        .default = policy
      ),
      policy_short = factor(policy_short,
                            levels = c("No recovery", "SRES", "CEIS", "CEIS ensemble"))
    ) %>%
    select(policy_short, unsafe_downrouting, high_risk_missed, critical_miss, recovery_budget) %>%
    pivot_longer(
      cols = c(unsafe_downrouting, high_risk_missed, critical_miss),
      names_to = "outcome",
      values_to = "count"
    ) %>%
    mutate(
      outcome = recode(outcome,
        unsafe_downrouting = "Unsafe downrouting",
        high_risk_missed = "High-risk missed",
        critical_miss = "Critical miss"
      ),
      outcome = factor(outcome,
                       levels = c("High-risk missed", "Critical miss", "Unsafe downrouting"))
    )

  p <- ggplot(df, aes(x = policy_short, y = count)) +
    geom_col(width = 0.62) +
    geom_text(aes(label = count), vjust = -0.25, size = 2.5) +
    facet_wrap(~ outcome, scales = "free_y", nrow = 1) +
    labs(
      title = "Residual risk after aggregate policy replay",
      subtitle = "Risk-triggered policies eliminate high-risk and critical misses, while unsafe downrouting remains.",
      x = NULL,
      y = "Count over 90 reviewed model assessments"
    ) +
    theme_cds() +
    theme(axis.text.x = element_text(angle = 25, hjust = 1))

  save_pub(p, "f4_recovery_outcomes", width = 6.8, height = 3.1)
}
```

### F7: Budget-Risk Frontier

```r
make_f7_budget_frontier <- function() {
  path <- "70_experiments/runs/janus_300_high_stakes_recovery_human_reviewed_2026_05_26/fixed_budget_recovery_frontier.tsv"

  df <- readr::read_tsv(path, show_col_types = FALSE) %>%
    janitor::clean_names() %>%
    mutate(
      score_metric = recode(score_metric,
                            "SRES total" = "SRES",
                            "CEIS" = "CEIS",
                            .default = score_metric),
      label = glue("trig {trig}\n{round(triggers_per_severe_miss_eliminated, 2)}/miss")
    )

  p <- ggplot(df, aes(x = observed_budget, y = severe_missed,
                      group = score_metric, linetype = score_metric,
                      shape = score_metric)) +
    geom_line(linewidth = 0.55) +
    geom_point(size = 2.2) +
    geom_text(aes(label = label), nudge_y = 0.32, size = 2.3, show.legend = FALSE) +
    scale_x_continuous(labels = percent_format(accuracy = 1),
                       breaks = seq(0.1, 0.4, 0.1),
                       limits = c(0.08, 0.42)) +
    scale_y_continuous(breaks = 0:7, limits = c(0, 7.4)) +
    labs(
      title = "Fixed-budget conservative replay frontier",
      subtitle = "CEIS-ranked replay reaches zero severe misses at the 10% observed budget in the scoped audit.",
      x = "Observed trigger budget",
      y = "Severe missed outcomes remaining"
    ) +
    theme_cds()

  save_pub(p, "f7_budget_risk_frontier", width = 6.4, height = 3.4)
}
```

### F8: Low-WER Danger Signals Supplement

```r
make_f8_low_wer_danger_supplement <- function() {
  path <- "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/low_wer_danger_summary.tsv"

  df <- readr::read_tsv(path, show_col_types = FALSE) %>%
    janitor::clean_names() %>%
    mutate(
      rate = low_wer_row_count / low_wer_denominator,
      signal = str_replace_all(signal, "_", " "),
      label = glue("{low_wer_row_count}/{low_wer_denominator}")
    ) %>%
    filter(low_wer_denominator > 0)

  p <- ggplot(df, aes(x = rate, y = reorder(signal, rate))) +
    geom_point(size = 2) +
    geom_text(aes(label = label), nudge_x = 0.012, size = 2.3, hjust = 0) +
    facet_wrap(~ model_family, scales = "free_y") +
    scale_x_continuous(labels = percent_format(accuracy = 1),
                       expand = expansion(mult = c(0.02, 0.25))) +
    labs(
      title = "Low-WER rows with downstream danger signals",
      subtitle = "Aggregate proxy evidence only; WER <= 10. Numerators and denominators are shown explicitly.",
      x = "Share of low-WER rows",
      y = NULL
    ) +
    theme_cds()

  save_pub(p, "f8_low_wer_danger", width = 6.8, height = 4.2)
}
```

### F9: Risk-Atom Instability Supplement

```r
make_f9_atom_instability_heatmap_supplement <- function() {
  path <- "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/risk_atom_instability.tsv"

  df <- readr::read_tsv(path, show_col_types = FALSE) %>%
    janitor::clean_names() %>%
    mutate(
      model_family = fct_reorder(model_family, unstable_variant_rate, .fun = mean),
      risk_atom = fct_reorder(risk_atom, unstable_variant_rate, .fun = mean),
      label = glue("{percent(unstable_variant_rate, accuracy = 0.1)}\n{unstable_variants}/{total_variants}")
    )

  p <- ggplot(df, aes(x = risk_atom, y = model_family, fill = unstable_variant_rate)) +
    geom_tile(colour = "white", linewidth = 0.35) +
    geom_text(aes(label = label), size = 2.4, lineheight = 0.9) +
    scale_fill_viridis_c(labels = percent_format(accuracy = 1), option = "C") +
    labs(
      title = "Risk-atom instability by model",
      subtitle = "Aggregate proxy variant rows; no transcript text or sample identifiers.",
      x = "Risk atom",
      y = NULL,
      fill = "Unstable variant rate"
    ) +
    theme_cds() +
    theme(axis.text.x = element_text(angle = 30, hjust = 1))

  save_pub(p, "f9_risk_atom_instability_heatmap", width = 6.4, height = 3.2)
}
```

### F10: Human-Reviewed Atom Outcomes

```r
make_f10_atom_outcomes <- function() {
  path <- "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_risk_atom_review.tsv"

  df <- readr::read_tsv(path, show_col_types = FALSE) %>%
    janitor::clean_names() %>%
    mutate(
      decision_change_rate = decision_change_yes / reviewed_rows,
      critical_rate = critical_atom_rows / reviewed_rows,
      atom = fct_reorder(risk_atom, decision_change_rate),
      label = glue("{decision_change_yes}/{reviewed_rows}")
    )

  p <- ggplot(df, aes(x = decision_change_rate, y = atom)) +
    geom_segment(aes(x = 0, xend = decision_change_rate, yend = atom),
                 linewidth = 0.45, colour = "grey55") +
    geom_point(aes(size = reviewed_rows, fill = critical_rate),
               shape = 21, colour = "grey20") +
    geom_text(aes(label = label), nudge_x = 0.035, size = 2.5, hjust = 0) +
    scale_x_continuous(labels = percent_format(accuracy = 1),
                       limits = c(0, max(df$decision_change_rate, na.rm = TRUE) + 0.18)) +
    scale_size_continuous(range = c(2, 6)) +
    scale_fill_viridis_c(labels = percent_format(accuracy = 1), option = "C") +
    labs(
      title = "Human-reviewed decision-change evidence by risk atom",
      subtitle = "Point size shows reviewed-row count; fill shows critical-atom share.",
      x = "Decision-change rate among reviewed rows",
      y = NULL,
      size = "Reviewed rows",
      fill = "Critical share"
    ) +
    theme_cds()

  save_pub(p, "f10_human_reviewed_atom_outcomes", width = 6.4, height = 3.4)
}
```

### F11: Entropy Supplement

```r
make_f11_entropy_supplement <- function() {
  path <- "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/risk_atom_instability.tsv"

  df <- readr::read_tsv(path, show_col_types = FALSE) %>%
    janitor::clean_names() %>%
    group_by(model_family) %>%
    mutate(
      p_atom = unstable_variants / sum(unstable_variants, na.rm = TRUE),
      entropy_contribution = if_else(p_atom > 0, -p_atom * log2(p_atom), 0),
      entropy = sum(entropy_contribution, na.rm = TRUE),
      norm_entropy = entropy / log2(n_distinct(risk_atom)),
      label = glue("{sprintf('%.2f', entropy_contribution)}\n{unstable_variants}")
    ) %>%
    ungroup()

  p <- ggplot(df, aes(x = risk_atom, y = model_family, fill = entropy_contribution)) +
    geom_tile(colour = "white", linewidth = 0.35) +
    geom_text(aes(label = label), size = 2.4, lineheight = 0.9) +
    scale_fill_viridis_c(option = "C") +
    labs(
      title = "Supplementary atom-class entropy",
      subtitle = "Entropy from aggregate atom counts; no word-level confusion lexicon is released.",
      x = "Risk atom",
      y = NULL,
      fill = "Entropy contribution"
    ) +
    theme_cds() +
    theme(axis.text.x = element_text(angle = 30, hjust = 1))

  save_pub(p, "f11_risk_atom_entropy_heatmap", width = 6.4, height = 3.2)
}
```

### Appendix Table A1

```r
make_table_a1_frontier <- function() {
  path <- "70_experiments/runs/janus_300_high_stakes_recovery_human_reviewed_2026_05_26/fixed_budget_recovery_frontier.tsv"

  df <- readr::read_tsv(path, show_col_types = FALSE) %>%
    janitor::clean_names() %>%
    mutate(
      score_metric = recode(score_metric, "SRES total" = "SRES", .default = score_metric),
      requested_budget = percent(requested_budget, accuracy = 1),
      observed_budget = percent(observed_budget, accuracy = 0.1),
      triggers_per_severe_miss_eliminated = sprintf("%.2f", triggers_per_severe_miss_eliminated)
    ) %>%
    transmute(
      Metric = score_metric,
      `Requested budget` = requested_budget,
      Triggers = trig,
      `Observed budget` = observed_budget,
      `Unsafe downrouting` = unsafe_downrouting,
      `High-risk missed` = high_risk_missed,
      `Critical miss` = critical_miss,
      `Severe missed` = severe_missed,
      `Severe misses eliminated` = severe_misses_eliminated,
      `Triggers / severe miss eliminated` = triggers_per_severe_miss_eliminated
    )

  kbl(
    df,
    format = "latex",
    booktabs = TRUE,
    escape = FALSE,
    caption = "Fixed-budget conservative replay frontier."
  ) %>%
    kable_styling(latex_options = c("hold_position"),
                  font_size = 8,
                  full_width = TRUE) %>%
    footnote(
      general = "Retrospective aggregate replay over 90 reviewed model assessments. Requested 40% budget maps to 35 eligible triggers, so the observed budget is 38.9%.",
      threeparttable = TRUE
    ) %>%
    save_kable(file.path(tab_dir, "table_a1_fixed_budget_frontier.tex"))
}
```

### R script execution order

```r
make_table1_main_asr()
make_table_s2_candidates()
make_table3_predictor()
make_table4_recovery()
make_table_a1_frontier()

make_f1_pipeline()
make_f2_evidence_design()
make_f3_predictor_auc()
make_f4_recovery_outcomes()
make_f7_budget_frontier()
make_f8_low_wer_danger_supplement()
make_f9_atom_instability_heatmap_supplement()
make_f10_atom_outcomes()
make_f11_entropy_supplement()
```

### LaTeX main-text replacement

Remove:

```tex
\AtBeginEnvironment{tabularx}{\fontsize{4}{4.5}\selectfont}
```

Use:

```tex
\AtBeginEnvironment{tabularx}{\small}
\setlength{\tabcolsep}{3pt}
\renewcommand{\arraystretch}{1.12}
```

Main-text order:

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

Supplement order:

```tex
\input{80_semantic_risk_asr/paper/tables/table_s2_candidates.tex}
\input{80_semantic_risk_asr/paper/tables/table_a1_fixed_budget_frontier.tex}

\paperfigure{f8_low_wer_danger.pdf}{Low-WER danger signals under aggregate proxy evidence.}{low_wer_danger_summary.tsv}
\paperfigure{f9_risk_atom_instability_heatmap.pdf}{Risk-atom instability by model under aggregate proxy evidence.}{risk_atom_instability.tsv}
\paperfigure{f11_risk_atom_entropy_heatmap.pdf}{Atom-class entropy from aggregate instability counts.}{risk_atom_instability.tsv}
```

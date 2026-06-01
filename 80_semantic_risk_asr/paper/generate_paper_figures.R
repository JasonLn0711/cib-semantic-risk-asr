#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(dplyr)
  library(forcats)
  library(ggplot2)
  library(grid)
  library(jsonlite)
  library(readr)
  library(scales)
  library(stringr)
  library(svglite)
  library(tidyr)
})

`%||%` <- function(x, y) if (is.null(x)) y else x

script_file <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1] %||% "80_semantic_risk_asr/paper/generate_paper_figures.R")
root <- normalizePath(file.path(dirname(script_file), "..", ".."), mustWork = TRUE)
paper_dir <- file.path(root, "80_semantic_risk_asr", "paper")
fig_dir <- file.path(paper_dir, "figures")
tab_dir <- file.path(paper_dir, "tables")
dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(tab_dir, recursive = TRUE, showWarnings = FALSE)

path <- function(...) file.path(root, ...)

asr_comparison <- path("70_experiments", "runs", "janus_258_test_split_asr_cds_proxy", "asr_cds_proxy_comparison.tsv")
candidate_table <- path("70_experiments", "runs", "asr_candidate_current_recheck_2026_05_26", "candidate_current_recheck_summary.tsv")
predictor_comparison <- path("70_experiments", "runs", "janus_300_high_stakes_human_audit_selection_2026_05_25", "human_audit_predictor_comparison.tsv")
predictor_ci <- path("70_experiments", "runs", "janus_300_high_stakes_human_audit_selection_2026_05_25", "human_audit_predictor_clustered_ci.tsv")
recovery_comparison <- path("70_experiments", "runs", "janus_300_high_stakes_recovery_human_reviewed_2026_05_26", "policy_comparison.tsv")
recovery_ci <- path("70_experiments", "runs", "janus_300_high_stakes_recovery_human_reviewed_2026_05_26", "policy_comparison_clustered_ci.tsv")
fixed_budget_frontier <- path("70_experiments", "runs", "janus_300_high_stakes_recovery_human_reviewed_2026_05_26", "fixed_budget_recovery_frontier.tsv")
low_wer_danger <- path("70_experiments", "runs", "janus_300_high_stakes_metric_predictor_proxy_2026_05_25", "low_wer_danger_summary.tsv")
risk_atom_instability <- path("70_experiments", "runs", "janus_300_high_stakes_metric_predictor_proxy_2026_05_25", "risk_atom_instability.tsv")
human_atom_review <- path("70_experiments", "runs", "janus_300_high_stakes_human_audit_selection_2026_05_25", "human_audit_risk_atom_review.tsv")

palette <- c(
  ink = "#1F2933",
  muted = "#52606D",
  grid = "#D9E2EC",
  blue = "#2F80ED",
  green = "#219653",
  orange = "#F2994A",
  red = "#D64545",
  purple = "#7B61FF",
  teal = "#0F9F9A",
  gray = "#F5F7FA"
)

theme_cds <- function(base_size = 9) {
  theme_minimal(base_size = base_size) +
    theme(
      text = element_text(family = "DejaVu Sans", color = palette[["ink"]]),
      plot.title = element_text(face = "bold", size = base_size + 2),
      plot.subtitle = element_text(size = base_size, colour = "grey30"),
      axis.title = element_text(face = "bold"),
      panel.grid.minor = element_blank(),
      legend.position = "bottom",
      legend.title = element_blank(),
      strip.text = element_text(face = "bold"),
      plot.caption = element_blank(),
      plot.margin = margin(10, 14, 10, 14)
    )
}

save_pub <- function(plot, name, width = 6.8, height = 3.8) {
  ggsave(file.path(fig_dir, paste0(name, ".svg")), plot, width = width, height = height, device = svglite, bg = "white")
  ggsave(file.path(fig_dir, paste0(name, ".pdf")), plot, width = width, height = height, device = cairo_pdf, bg = "white")
}

read_tsv_safe <- function(file) {
  read_tsv(file, show_col_types = FALSE, progress = FALSE)
}

fmt_num <- function(x, digits = 3) {
  ifelse(is.na(x), "n/a", formatC(x, digits = digits, format = "f"))
}

tex_escape <- function(x) {
  x <- as.character(x)
  x <- str_replace_all(x, "\\\\", "\\\\textbackslash{}")
  x <- str_replace_all(x, "([#$%&_{}])", "\\\\\\1")
  x
}

write_latex_table <- function(df, file, caption, label = NULL, note = NULL, align = NULL) {
  align <- align %||% c("L{1.2}", rep("R{0.9}", ncol(df) - 1))
  stopifnot(length(align) == ncol(df))
  lines <- c(
    "\\begin{table}[!htbp]",
    "\\centering",
    paste0("\\caption{", tex_escape(caption), "}"),
    if (!is.null(label)) paste0("\\label{", label, "}") else NULL,
    "\\footnotesize",
    paste0("\\begin{tabularx}{\\linewidth}{@{}",
           paste(align, collapse = ""),
           "@{}}"),
    "\\toprule",
    paste(tex_escape(names(df)), collapse = " & "),
    "\\\\",
    "\\midrule"
  )
  body <- apply(df, 1, function(row) paste(tex_escape(row), collapse = " & "))
  lines <- c(lines, paste0(body, " \\\\"), "\\bottomrule", "\\end{tabularx}")
  if (!is.null(note)) {
    lines <- c(lines, paste0("\\\\[0.4em]{\\footnotesize\\RaggedRight ", tex_escape(note), "\\par}"))
  }
  lines <- c(lines, "\\end{table}")
  writeLines(lines, file.path(tab_dir, file))
}

model_family <- function(run_id) {
  case_when(
    str_detect(run_id, "breeze_asr25_partial") ~ "Breeze-ASR-25 partial encoder",
    str_detect(run_id, "breeze_asr25_lora") ~ "Breeze-ASR-25 LoRA",
    str_detect(run_id, "breeze_asr25_base") ~ "Breeze-ASR-25 base",
    str_detect(run_id, "breeze_asr26") ~ "Breeze-ASR-26",
    str_detect(run_id, "whisper_large_v2") ~ "Whisper large-v2",
    str_detect(run_id, "whisper_large_v3_turbo") ~ "Whisper large-v3 turbo",
    str_detect(run_id, "whisper_large_v3") ~ "Whisper large-v3",
    str_detect(run_id, "whisper_small") ~ "Whisper small",
    str_detect(run_id, "sensevoice") ~ "SenseVoice small",
    str_detect(run_id, "qwen3") ~ "Qwen3-ASR 0.6B",
    TRUE ~ str_replace_all(run_id, "_", " ")
  )
}

metric_label <- function(metric) {
  recode(metric, wer = "WER", cer = "CER", sres_total = "SRES", ceis_max = "CEIS", ceis = "CEIS", .default = metric)
}

make_table1_main_asr <- function() {
  rows <- read_tsv_safe(asr_comparison) %>%
    mutate(Model = model_family(run_id)) %>%
    transmute(
      Model,
      Rows = rows,
      `CER zh micro` = fmt_num(cer_zh_micro, 2),
      `WER zh jieba micro` = fmt_num(wer_zh_jieba_micro, 2),
      `Unsafe downrouting` = unsafe_downrouting_count,
      `High-risk missed` = high_risk_missed_count,
      `Locale violations` = locale_violation_rows,
      `Paper role` = case_when(
        str_detect(Model, "partial") ~ "Strongest ASR evidence layer",
        str_detect(Model, "Whisper") ~ "Comparable baseline",
        TRUE ~ "Split/model context"
      )
    ) %>%
    arrange(as.numeric(`CER zh micro`))
  write_latex_table(
    rows,
    "table1_main_asr.tex",
    "Main ASR benchmark on the canonical 258-row split. Run identifiers are reported in the supplement.",
    "tab:main-asr",
    "CER zh micro is the primary ASR surface metric; WER zh jieba micro is supplemental. Unsafe downrouting and high-risk missed counts are split/model-comparison evidence, not final selected-300 human-reviewed risk claims.",
    align = c("L{1.15}", "R{0.55}", "R{0.72}", "R{0.80}", "R{0.72}", "R{0.72}", "R{0.70}", "L{1.60}")
  )
}

make_table_s2_candidates <- function() {
  rows <- read_tsv_safe(candidate_table) %>%
    mutate(Candidate = model_family(run_id)) %>%
    transmute(
      Candidate,
      Rows = rows,
      CER = fmt_num(cer_zh_micro, 2),
      WER = fmt_num(wer_zh_jieba_micro, 2),
      `Locale violations` = locale_violation_rows,
      Decision = "bounded exploratory lane"
    )
  write_latex_table(
    rows,
    "table_s2_candidates.tex",
    "Candidate and exploratory lane evidence.",
    "tab:s2-candidates",
    "Candidate models are engineering-gated evidence and are not promoted to the main ASR benchmark or selected-300 claims from this table.",
    align = c("L{1.35}", "R{0.55}", "R{0.55}", "R{0.55}", "R{0.75}", "L{1.25}")
  )
}

make_table3_predictor <- function() {
  base <- read_tsv_safe(predictor_comparison) %>%
    filter(scope == "overall", target == "human_decision_change_yes") %>%
    mutate(Predictor = metric_label(metric))
  ci <- read_tsv_safe(predictor_ci) %>%
    filter(scope == "overall", target == "human_decision_change_yes") %>%
    mutate(Predictor = metric_label(metric))
  rows <- base %>%
    left_join(select(ci, Predictor, auc_ci_low, auc_ci_high, best_f1_ci_low, best_f1_ci_high), by = "Predictor") %>%
    mutate(Predictor = factor(Predictor, levels = c("WER", "CER", "SRES", "CEIS"))) %>%
    arrange(Predictor) %>%
    transmute(
      Predictor = as.character(Predictor),
      AUC = fmt_num(auc, 3),
      `AUC CI` = paste0(fmt_num(auc_ci_low, 3), "--", fmt_num(auc_ci_high, 3)),
      Threshold = fmt_num(best_threshold, 2),
      `Best F1` = fmt_num(best_f1, 3),
      `F1 CI` = paste0(fmt_num(best_f1_ci_low, 3), "--", fmt_num(best_f1_ci_high, 3)),
      Precision = fmt_num(precision, 3),
      Recall = fmt_num(recall, 3),
      FN = false_negative,
      Role = if_else(Predictor == "CEIS", "Decision-stability metric", if_else(Predictor == "SRES", "Semantic-risk baseline", "Surface baseline"))
    )
  write_latex_table(
    rows,
    "table3_predictor.tex",
    "Predictor performance against human-reviewed decision-change labels. Unit: 90 model assessments clustered within 30 reviewed audio rows.",
    "tab:predictor",
    "Thresholds are diagnostic operating points selected on the scoped audit set, not frozen deployment thresholds. CEIS has the highest point-estimate AUC and zero false negatives at the diagnostic threshold; SRES has the highest best-threshold F1.",
    align = c("L{0.75}", "R{0.70}", "R{0.95}", "R{0.92}", "R{0.70}", "R{0.95}", "R{0.70}", "R{0.70}", "R{0.50}", "L{1.35}")
  )
}

make_table4_recovery <- function() {
  base <- read_tsv_safe(recovery_comparison) %>%
    filter(policy != "confidence_only_trigger")
  ci <- read_tsv_safe(recovery_ci)
  rows <- base %>%
    left_join(
      select(ci, policy, recovery_budget_rate_ci_low, recovery_budget_rate_ci_high, severe_missed_count_ci_low, severe_missed_count_ci_high),
      by = "policy"
    ) %>%
    mutate(
      Policy = recode(
        policy,
        no_recovery = "No recovery",
        sres_triggered_recovery = "SRES recovery",
        ceis_triggered_conservative_action = "CEIS conservative action",
        ceis_ensemble_arbitration = "CEIS ensemble arbitration",
        .default = policy
      ),
      severe_misses_eliminated = high_risk_missed_reduction_vs_no_recovery + critical_miss_count[policy == "no_recovery"] - critical_miss_count,
      triggers_per = if_else(severe_misses_eliminated > 0, triggered_count / severe_misses_eliminated, NA_real_)
    ) %>%
    transmute(
      Policy,
      Unsafe = unsafe_downrouting_count,
      `High-risk` = high_risk_missed_count,
      Critical = critical_miss_count,
      Budget = fmt_num(recovery_budget_rate, 3),
      `Budget CI` = paste0(fmt_num(recovery_budget_rate_ci_low, 3), "--", fmt_num(recovery_budget_rate_ci_high, 3)),
      `Severe elim.` = severe_misses_eliminated,
      `Severe rem. CI` = paste0(fmt_num(severe_missed_count_ci_low, 0), "--", fmt_num(severe_missed_count_ci_high, 0)),
      `Trig. / elim.` = fmt_num(triggers_per, 1)
    )
  write_latex_table(
    rows,
    "table4_recovery.tex",
    "Aggregate policy replay under human-reviewed selected-300 labels.",
    "tab:recovery",
    "Confidence-only recovery is not shown as a main policy because calibrated confidence was unavailable and produced no triggers. Residual unsafe downrouting remains after risk-triggered policies and should be treated as a separate governance issue.",
    align = c("L{1.35}", "R{0.55}", "R{0.55}", "R{0.55}", "R{0.60}", "R{0.85}", "R{0.70}", "R{0.75}", "R{0.75}")
  )
}

make_table_a1_frontier <- function() {
  rows <- read_tsv_safe(fixed_budget_frontier) %>%
    mutate(Metric = metric_label(score_metric)) %>%
    transmute(
      Metric,
      Requested = percent(budget_target_rate, accuracy = 1),
      Triggers = triggered_count,
      Observed = percent(observed_budget_rate, accuracy = 0.1),
      Unsafe = unsafe_downrouting_count,
      `High-risk` = high_risk_missed_count,
      Critical = critical_miss_count,
      Severe = severe_missed_count,
      Eliminated = severe_misses_eliminated_vs_no_recovery,
      `Trig. / elim.` = fmt_num(triggers_per_severe_miss_eliminated, 2)
    )
  write_latex_table(
    rows,
    "table_a1_fixed_budget_frontier.tex",
    "Fixed-budget conservative replay frontier.",
    "tab:a1-frontier",
    "Retrospective aggregate replay over 90 reviewed model assessments. Requested 40% budget maps to 35 eligible triggers, so the observed budget is 38.9%.",
    align = c("L{0.70}", "R{0.70}", "R{0.65}", "R{0.70}", "R{0.60}", "R{0.70}", "R{0.60}", "R{0.60}", "R{0.75}", "R{0.70}")
  )
}

make_f1_pipeline <- function() {
  nodes <- tibble(
    step = 1:6,
    label = c("Audio", "ASR", "Risk atoms", "Variants", "SRES / CEIS", "Conservative action"),
    detail = c("speech input", "hypothesis + signals", "decision-critical spans", "plausible ASR alternatives", "risk + decision instability", "recover, escalate, or abstain"),
    x = 1:6
  )
  p <- ggplot(nodes) +
    geom_rect(aes(xmin = x - 0.42, xmax = x + 0.42, ymin = 0, ymax = 1), fill = "white", colour = "grey25", linewidth = 0.5) +
    geom_segment(data = filter(nodes, step < 6), aes(x = x + 0.42, xend = x + 0.58, y = 0.5, yend = 0.5), arrow = arrow(length = unit(0.08, "in")), linewidth = 0.35) +
    geom_text(aes(x = x, y = 0.62, label = label), fontface = "bold", size = 3.1) +
    geom_text(aes(x = x, y = 0.38, label = detail), size = 2.2, lineheight = 0.9) +
    annotate("text", x = 3.5, y = -0.22, label = "Human review supplies evaluation labels only; recovery policies are automatic and aggregate-evaluated.", size = 2.4, colour = "grey30") +
    coord_cartesian(xlim = c(0.45, 6.55), ylim = c(-0.35, 1.15), clip = "off") +
    labs(title = "CDS-ASR decision-stability pipeline") +
    theme_void(base_size = 9) +
    theme(text = element_text(family = "DejaVu Sans", color = palette[["ink"]]), plot.title = element_text(face = "bold", hjust = 0))
  save_pub(p, "f1_cds_asr_pipeline", 6.8, 1.8)
}

make_f2_evidence_design <- function() {
  rows <- tibble(
    layer = c("ASR split", "Selected provenance", "Human-reviewed audit", "Reviewed assessments"),
    unit = c("audio rows", "candidate rows / outputs", "audio rows", "model-row assessments"),
    n = c("258", "300", "30", "90"),
    claim = c("model-comparison context", "enriched audit surface", "decision-critical review unit", "predictor and replay evidence"),
    x = 1:4
  )
  p <- ggplot(rows) +
    geom_rect(aes(xmin = x - .43, xmax = x + .43, ymin = 0, ymax = 1), fill = "white", colour = "grey25", linewidth = 0.45) +
    geom_segment(data = filter(rows, x < max(x)), aes(x = x + .43, xend = x + .57, y = .5, yend = .5), arrow = arrow(length = unit(0.08, "in")), linewidth = 0.35) +
    geom_text(aes(x = x, y = .76, label = layer), fontface = "bold", size = 2.7, lineheight = .9) +
    geom_text(aes(x = x, y = .50, label = paste0("Unit: ", unit, "\nN = ", n)), size = 2.4, lineheight = .9) +
    geom_text(aes(x = x, y = .22, label = claim), size = 2.15, colour = "grey30", lineheight = .9) +
    annotate("label", x = 2.5, y = -0.28, label = "Cluster rule: the 90 model assessments are clustered within 30 reviewed rows.", size = 2.5, label.size = 0.2, fill = "grey97") +
    coord_cartesian(xlim = c(.45, 4.55), ylim = c(-.5, 1.1), clip = "off") +
    labs(title = "Study evidence ladder and release boundary") +
    theme_void(base_size = 9) +
    theme(text = element_text(family = "DejaVu Sans", color = palette[["ink"]]), plot.title = element_text(face = "bold", hjust = 0))
  save_pub(p, "f2_evidence_design", 6.8, 2.0)
}

make_f3_predictor_auc <- function() {
  base <- read_tsv_safe(predictor_comparison) %>%
    filter(scope == "overall", target == "human_decision_change_yes") %>%
    mutate(Predictor = metric_label(metric))
  ci <- read_tsv_safe(predictor_ci) %>%
    filter(scope == "overall", target == "human_decision_change_yes") %>%
    mutate(Predictor = metric_label(metric))
  rows <- base %>%
    left_join(select(ci, Predictor, auc_ci_low, auc_ci_high), by = "Predictor") %>%
    mutate(Predictor = factor(Predictor, levels = c("WER", "CER", "SRES", "CEIS")), label = paste0("AUC ", fmt_num(auc, 3), "\nRecall ", fmt_num(recall, 2), ", FN ", false_negative))
  p <- ggplot(rows, aes(x = auc, y = Predictor)) +
    geom_errorbarh(aes(xmin = auc_ci_low, xmax = auc_ci_high), height = 0.16, linewidth = 0.45, colour = "grey35") +
    geom_point(size = 2.4) +
    geom_text(aes(label = label), nudge_y = 0.23, size = 2.4, hjust = 0.5) +
    scale_x_continuous(limits = c(0.5, 1.0), breaks = seq(0.5, 1.0, 0.1)) +
    labs(title = "Predicting human-reviewed decision change", subtitle = "AUC with row-clustered 95% intervals; 90 model assessments clustered within 30 rows.", x = "AUC", y = NULL) +
    theme_cds()
  save_pub(p, "f3_predictor_auc", 6.4, 3.0)
}

make_f4_recovery_outcomes <- function() {
  rows <- read_tsv_safe(recovery_comparison) %>%
    filter(policy != "confidence_only_trigger") %>%
    mutate(policy_short = recode(policy, no_recovery = "No recovery", sres_triggered_recovery = "SRES", ceis_triggered_conservative_action = "CEIS", ceis_ensemble_arbitration = "CEIS ensemble", .default = policy),
           policy_short = factor(policy_short, levels = c("No recovery", "SRES", "CEIS", "CEIS ensemble"))) %>%
    select(policy_short, unsafe_downrouting_count, high_risk_missed_count, critical_miss_count) %>%
    pivot_longer(cols = c(unsafe_downrouting_count, high_risk_missed_count, critical_miss_count), names_to = "outcome", values_to = "count") %>%
    mutate(outcome = recode(outcome, unsafe_downrouting_count = "Unsafe downrouting", high_risk_missed_count = "High-risk missed", critical_miss_count = "Critical miss"),
           outcome = factor(outcome, levels = c("High-risk missed", "Critical miss", "Unsafe downrouting")))
  p <- ggplot(rows, aes(x = policy_short, y = count)) +
    geom_col(width = 0.62, fill = palette[["blue"]]) +
    geom_text(aes(label = count), vjust = -0.25, size = 2.5) +
    facet_wrap(~ outcome, scales = "free_y", nrow = 1) +
    labs(title = "Residual risk after aggregate policy replay", subtitle = "Risk-triggered policies eliminate high-risk and critical misses, while unsafe downrouting remains.", x = NULL, y = "Count over 90 reviewed model assessments") +
    theme_cds() +
    theme(axis.text.x = element_text(angle = 25, hjust = 1))
  save_pub(p, "f4_recovery_outcomes", 6.8, 3.1)
}

make_f5_model_lanes <- function() {
  rows <- tibble(
    lane = c("Main comparable split", "Candidate lane", "Runtime-blocked probes"),
    status = c("Use for split/model context", "Supplement only", "Engineering gate only"),
    n = c(nrow(read_tsv_safe(asr_comparison)), nrow(read_tsv_safe(candidate_table)), 2)
  )
  p <- ggplot(rows, aes(x = reorder(lane, n), y = n)) +
    geom_col(width = 0.6, fill = palette[["muted"]]) +
    geom_text(aes(label = status), hjust = -0.05, size = 2.7) +
    coord_flip() +
    scale_y_continuous(expand = expansion(mult = c(0, 0.35))) +
    labs(title = "Supplementary model lane boundary", x = NULL, y = "Aggregate record count") +
    theme_cds()
  save_pub(p, "f5_model_lane_state", 6.4, 2.8)
}

make_f6_n_ladder <- function() {
  # Legacy compatibility output; main text should use f2_evidence_design.
  make_f2_evidence_design()
  file.copy(file.path(fig_dir, "f2_evidence_design.svg"), file.path(fig_dir, "f6_n_ladder.svg"), overwrite = TRUE)
  file.copy(file.path(fig_dir, "f2_evidence_design.pdf"), file.path(fig_dir, "f6_n_ladder.pdf"), overwrite = TRUE)
}

make_f7_budget_frontier <- function() {
  rows <- read_tsv_safe(fixed_budget_frontier) %>% mutate(Metric = metric_label(score_metric), label = paste0("trig ", triggered_count, "\n", fmt_num(triggers_per_severe_miss_eliminated, 2), "/miss"))
  p <- ggplot(rows, aes(x = observed_budget_rate, y = severe_missed_count, group = Metric, linetype = Metric, shape = Metric)) +
    geom_line(linewidth = 0.55) +
    geom_point(size = 2.2) +
    geom_text(aes(label = label), nudge_y = 0.32, size = 2.3, show.legend = FALSE) +
    scale_x_continuous(labels = percent_format(accuracy = 1), breaks = seq(0.1, 0.4, 0.1), limits = c(0.08, 0.42)) +
    scale_y_continuous(breaks = 0:7, limits = c(0, 7.4)) +
    labs(title = "Fixed-budget conservative replay frontier", subtitle = "CEIS-ranked replay reaches zero severe misses at the 10% observed budget in the scoped audit.", x = "Observed trigger budget", y = "Severe missed outcomes remaining") +
    theme_cds()
  save_pub(p, "f7_budget_risk_frontier", 6.4, 3.4)
}

make_f8_low_wer_danger <- function() {
  rows <- read_tsv_safe(low_wer_danger) %>%
    mutate(model = if_else(asr_run_id == "ALL", "ALL", model_family(asr_run_id))) %>%
    select(model, low_wer_rows, low_wer_label_flip_count, low_wer_unsafe_downrouting_count, low_wer_high_risk_missed_count, low_wer_critical_miss_count, low_wer_sres_trigger_count, low_wer_ceis_trigger_count) %>%
    pivot_longer(-c(model, low_wer_rows), names_to = "signal", values_to = "count") %>%
    mutate(signal = recode(signal, low_wer_label_flip_count = "Label flip", low_wer_unsafe_downrouting_count = "Unsafe downrouting", low_wer_high_risk_missed_count = "High-risk missed", low_wer_critical_miss_count = "Critical miss", low_wer_sres_trigger_count = "SRES trigger", low_wer_ceis_trigger_count = "CEIS trigger"),
           rate = if_else(low_wer_rows > 0, count / low_wer_rows, 0),
           label = paste0(count, "/", low_wer_rows))
  p <- ggplot(rows, aes(x = rate, y = reorder(signal, rate))) +
    geom_point(size = 2) +
    geom_text(aes(label = label), nudge_x = 0.02, size = 2.3, hjust = 0) +
    facet_wrap(~ model, scales = "free_y") +
    scale_x_continuous(labels = percent_format(accuracy = 1), expand = expansion(mult = c(0.02, 0.30))) +
    labs(title = "Low-WER rows with downstream danger signals", subtitle = "Aggregate proxy evidence only; numerators and denominators are shown explicitly.", x = "Share of low-WER rows", y = NULL) +
    theme_cds()
  save_pub(p, "f8_low_wer_danger", 6.8, 4.2)
}

make_f9_atom_instability <- function() {
  rows <- read_tsv_safe(risk_atom_instability) %>%
    mutate(model = fct_reorder(model_family(asr_run_id), unstable_variant_rate, .fun = mean), atom = fct_reorder(str_replace_all(risk_atom_type, "_", " "), unstable_variant_rate, .fun = mean), label = paste0(percent(unstable_variant_rate, accuracy = 0.1), "\n", unstable_variant_rows, "/", variant_rows))
  p <- ggplot(rows, aes(x = atom, y = model, fill = unstable_variant_rate)) +
    geom_tile(colour = "white", linewidth = 0.35) +
    geom_text(aes(label = label), size = 2.4, lineheight = 0.9) +
    scale_fill_viridis_c(labels = percent_format(accuracy = 1), option = "C") +
    labs(title = "Risk-atom instability by model", subtitle = "Aggregate proxy variant rows; no transcript text or sample identifiers.", x = "Risk atom", y = NULL, fill = "Unstable variant rate") +
    theme_cds() +
    theme(axis.text.x = element_text(angle = 30, hjust = 1))
  save_pub(p, "f9_risk_atom_instability_heatmap", 6.4, 3.2)
}

make_f10_atom_outcomes <- function() {
  rows <- read_tsv_safe(human_atom_review) %>%
    mutate(decision_change_rate = decision_change_yes_count / reviewed_row_count, critical_rate = critical_atom_row_count / reviewed_row_count, atom = fct_reorder(str_replace_all(risk_atom_type, "_", " "), decision_change_rate), label = paste0(decision_change_yes_count, "/", reviewed_row_count))
  p <- ggplot(rows, aes(x = decision_change_rate, y = atom)) +
    geom_segment(aes(x = 0, xend = decision_change_rate, yend = atom), linewidth = 0.45, colour = "grey55") +
    geom_point(aes(size = reviewed_row_count, fill = critical_rate), shape = 21, colour = "grey20") +
    geom_text(aes(label = label), nudge_x = 0.035, size = 2.5, hjust = 0) +
    scale_x_continuous(labels = percent_format(accuracy = 1), limits = c(0, max(rows$decision_change_rate, na.rm = TRUE) + 0.18)) +
    scale_size_continuous(range = c(2, 6)) +
    scale_fill_viridis_c(labels = percent_format(accuracy = 1), option = "C") +
    labs(title = "Human-reviewed decision-change evidence by risk atom", subtitle = "Point size shows reviewed-row count; fill shows critical-atom share.", x = "Decision-change rate among reviewed rows", y = NULL, size = "Reviewed rows", fill = "Critical share") +
    theme_cds()
  save_pub(p, "f10_human_reviewed_atom_outcomes", 6.4, 3.4)
}

make_f11_entropy <- function() {
  rows <- read_tsv_safe(risk_atom_instability) %>%
    mutate(model = model_family(asr_run_id), atom = str_replace_all(risk_atom_type, "_", " ")) %>%
    group_by(model) %>%
    mutate(p_atom = unstable_variant_rows / sum(unstable_variant_rows, na.rm = TRUE), entropy_contribution = if_else(p_atom > 0, -p_atom * log2(p_atom), 0), label = paste0(fmt_num(entropy_contribution, 2), "\n", unstable_variant_rows)) %>%
    ungroup()
  p <- ggplot(rows, aes(x = atom, y = model, fill = entropy_contribution)) +
    geom_tile(colour = "white", linewidth = 0.35) +
    geom_text(aes(label = label), size = 2.4, lineheight = 0.9) +
    scale_fill_viridis_c(option = "C") +
    labs(title = "Supplementary atom-class entropy", subtitle = "Entropy from aggregate atom counts; no word-level confusion lexicon is released.", x = "Risk atom", y = NULL, fill = "Entropy contribution") +
    theme_cds() +
    theme(axis.text.x = element_text(angle = 30, hjust = 1))
  save_pub(p, "f11_risk_atom_entropy_heatmap", 6.4, 3.2)
}

write_index <- function() {
  content <- c(
    "# CDS-ASR Figure And Table Package",
    "",
    "Date: 2026-06-01",
    "",
    "These manuscript figures and LaTeX table fragments are generated by R from aggregate-only evidence.",
    "They do not include transcript text, audio IDs, selected row IDs, reviewer notes, model hypotheses, or transcript-bearing runtime logs.",
    "",
    "Main-text recommendation: F1, merged F2/F6 as `f2_evidence_design`, F3, F4, F7, and F10.",
    "Supplement/repo-manifest recommendation: F5, F8, F9, F11, candidate table, fixed-budget appendix table, and the full manifest list.",
    "",
    "Generated table fragments live under `80_semantic_risk_asr/paper/tables/`."
  )
  writeLines(content, file.path(fig_dir, "README.md"))
}

main <- function() {
  make_table1_main_asr()
  make_table_s2_candidates()
  make_table3_predictor()
  make_table4_recovery()
  make_table_a1_frontier()
  make_f1_pipeline()
  make_f2_evidence_design()
  make_f3_predictor_auc()
  make_f4_recovery_outcomes()
  make_f5_model_lanes()
  make_f6_n_ladder()
  make_f7_budget_frontier()
  make_f8_low_wer_danger()
  make_f9_atom_instability()
  make_f10_atom_outcomes()
  make_f11_entropy()
  write_index()
  message("Wrote R-generated figures to ", fig_dir)
  message("Wrote R-generated tables to ", tab_dir)
}

main()

#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(dplyr)
  library(forcats)
  library(ggplot2)
  library(grid)
  library(jsonlite)
  library(patchwork)
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
out_dir <- file.path(paper_dir, "figures")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

path <- function(...) file.path(root, ...)

asr_comparison <- path(
  "70_experiments", "runs", "janus_258_test_split_asr_cds_proxy",
  "asr_cds_proxy_comparison.tsv"
)
predictor_comparison <- path(
  "70_experiments", "runs", "janus_300_high_stakes_human_audit_selection_2026_05_25",
  "human_audit_predictor_comparison.tsv"
)
recovery_comparison <- path(
  "70_experiments", "runs", "janus_300_high_stakes_recovery_human_reviewed_2026_05_26",
  "policy_comparison.tsv"
)
fixed_budget_frontier <- path(
  "70_experiments", "runs", "janus_300_high_stakes_recovery_human_reviewed_2026_05_26",
  "fixed_budget_recovery_frontier.tsv"
)
candidate_summary <- path(
  "70_experiments", "runs", "asr_candidate_current_recheck_2026_05_26",
  "summary.json"
)
candidate_table <- path(
  "70_experiments", "runs", "asr_candidate_current_recheck_2026_05_26",
  "candidate_current_recheck_summary.tsv"
)
readiness_summary <- path(
  "70_experiments", "runs", "postdoc_evidence_chain_2026_05_25",
  "publishable_evidence_completion_summary.json"
)
low_wer_danger <- path(
  "70_experiments", "runs", "janus_300_high_stakes_metric_predictor_proxy_2026_05_25",
  "low_wer_danger_summary.tsv"
)
risk_atom_instability <- path(
  "70_experiments", "runs", "janus_300_high_stakes_metric_predictor_proxy_2026_05_25",
  "risk_atom_instability.tsv"
)
human_atom_review <- path(
  "70_experiments", "runs", "janus_300_high_stakes_human_audit_selection_2026_05_25",
  "human_audit_risk_atom_review.tsv"
)

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

theme_paper <- function(base_size = 12) {
  theme_minimal(base_size = base_size) +
    theme(
      text = element_text(family = "DejaVu Sans", color = palette[["ink"]]),
      plot.title = element_text(face = "bold", size = base_size + 7, margin = margin(b = 4)),
      plot.subtitle = element_text(color = palette[["muted"]], size = base_size + 1, margin = margin(b = 12)),
      panel.grid.major = element_line(color = palette[["grid"]], linewidth = 0.35),
      panel.grid.minor = element_blank(),
      axis.title = element_text(face = "bold"),
      legend.title = element_text(face = "bold"),
      legend.position = "bottom",
      plot.margin = margin(18, 24, 18, 24)
    )
}

save_figure <- function(plot, name, width = 10, height = 5.5) {
  svg_path <- file.path(out_dir, paste0(name, ".svg"))
  pdf_path <- file.path(out_dir, paste0(name, ".pdf"))
  ggsave(svg_path, plot, width = width, height = height, device = svglite, bg = "white")
  ggsave(pdf_path, plot, width = width, height = height, device = cairo_pdf, bg = "white")
}

read_tsv_safe <- function(file) {
  read_tsv(file, show_col_types = FALSE, progress = FALSE)
}

read_json_safe <- function(file) {
  fromJSON(file, simplifyVector = TRUE)
}

wrap_label <- function(x, width = 24) {
  vapply(x, function(value) paste(strwrap(value, width = width), collapse = "\n"), character(1))
}

model_label <- function(x) {
  wrap_label(recode(
    x,
    breeze_asr25_base_high_stakes_300 = "Breeze-ASR-25 base",
    breeze_asr25_lora_high_stakes_300 = "Breeze-ASR-25 LoRA",
    breeze_asr25_partial_encoder_high_stakes_300 = "Breeze-ASR-25 partial encoder",
    .default = str_replace_all(x, "_", " ")
  ), width = 18)
}

figure_1_pipeline <- function() {
  nodes <- tibble(
    x = 1:6,
    label = c("Audio", "ASR", "Risk atoms", "Variants", "SRES / CEIS", "Recovery"),
    sub = c("speech input", "hypothesis + signals", "decision-critical spans", "plausible alternatives", "decision instability", "conservative action"),
    color = c("blue", "teal", "orange", "purple", "green", "red")
  ) %>%
    mutate(across(c(label, sub), ~ wrap_label(.x, width = 14)))
  segments <- tibble(x = 1:5, xend = 2:6)
  p <- ggplot() +
    geom_segment(
      data = segments,
      aes(x = x + 0.32, xend = xend - 0.32, y = 1, yend = 1),
      arrow = arrow(length = unit(0.18, "inches")), color = palette[["grid"]], linewidth = 1.1
    ) +
    geom_rect(
      data = nodes,
      aes(xmin = x - 0.36, xmax = x + 0.36, ymin = 0.65, ymax = 1.35, color = color),
      fill = "white", linewidth = 1.2
    ) +
    geom_rect(
      data = nodes,
      aes(xmin = x - 0.36, xmax = x + 0.36, ymin = 1.28, ymax = 1.35, fill = color),
      color = NA
    ) +
    geom_text(data = nodes, aes(x, y = 1.08, label = label), fontface = "bold", size = 4.2) +
    geom_text(data = nodes, aes(x, y = 0.88, label = sub), color = palette[["muted"]], size = 3.1) +
    scale_color_manual(values = palette[nodes$color], guide = "none") +
    scale_fill_manual(values = palette[nodes$color], guide = "none") +
    coord_cartesian(xlim = c(0.45, 6.55), ylim = c(0.25, 1.55), clip = "off") +
    labs(
      title = "F1. CDS-ASR Pipeline",
      subtitle = "Aggregate-only method diagram; no transcript or row content.",
      caption = "Human review supplies evaluation labels only; recovery policies remain automatic and aggregate-evaluated."
    ) +
    theme_void(base_size = 12) +
    theme(
      text = element_text(family = "DejaVu Sans", color = palette[["ink"]]),
      plot.title = element_text(face = "bold", size = 20),
      plot.subtitle = element_text(color = palette[["muted"]], size = 12),
      plot.caption = element_text(color = palette[["muted"]], hjust = 0, size = 11),
      plot.margin = margin(20, 28, 20, 28)
    )
  save_figure(p, "f1_cds_asr_pipeline", 11.2, 3.3)
}

figure_2_boundary <- function() {
  summary <- read_json_safe(readiness_summary)
  layers <- tibble(
    x = 1:3,
    layer = c("258-row test split", "selected-300 proxy outputs", "selected-300 human-reviewed audit"),
    role = c("split/model comparison", "selection provenance", "predictor/recovery evidence"),
    note = c("CER/WER + proxy risk metrics", "not final human-reviewed risk claim", "30 rows / 90 model assessments"),
    color = c("blue", "orange", "green")
  ) %>%
    mutate(across(c(layer, role, note), ~ wrap_label(.x, width = 18)))
  p <- ggplot(layers, aes(x, y = 1)) +
    geom_segment(
      data = tibble(x = c(1, 2), xend = c(2, 3)),
      aes(x = x + 0.35, xend = xend - 0.35, y = 1, yend = 1),
      inherit.aes = FALSE,
      arrow = arrow(length = unit(0.16, "inches")), color = palette[["grid"]], linewidth = 1.1
    ) +
    geom_rect(aes(xmin = x - 0.38, xmax = x + 0.38, ymin = 0.62, ymax = 1.38, color = color), fill = "white", linewidth = 1.2) +
    geom_text(aes(label = layer, y = 1.18), fontface = "bold", size = 3.8) +
    geom_text(aes(label = role, y = 0.98), color = palette[["muted"]], size = 3.1) +
    geom_text(aes(label = note, y = 0.82), color = palette[["muted"]], size = 3.0) +
    annotate("rect", xmin = 0.55, xmax = 3.45, ymin = 0.1, ymax = 0.42, fill = palette[["gray"]], color = "#BCCCDC") +
    annotate("text", x = 0.67, y = 0.32, label = "Release boundary", hjust = 0, fontface = "bold", size = 3.6) +
    annotate("text", x = 0.67, y = 0.2, label = wrap_label("Tracked: aggregate run records, validation summaries, metric tables, figure SVGs/PDFs. Local-only: raw audio, transcripts, selected IDs, hypotheses, reviewer sheets/notes, runtime logs, model weights.", 92), hjust = 0, color = palette[["muted"]], size = 2.9) +
    scale_color_manual(values = palette[layers$color], guide = "none") +
    coord_cartesian(xlim = c(0.45, 3.55), ylim = c(0.02, 1.55), clip = "off") +
    labs(
      title = "F2. Evidence Boundary",
      subtitle = paste0("Publishable evidence gate: ", summary$publishable_ready, " | status counts: ", paste(names(summary$status_counts), summary$status_counts, sep = "=", collapse = ", "))
    ) +
    theme_void(base_size = 12) +
    theme(
      text = element_text(family = "DejaVu Sans", color = palette[["ink"]]),
      plot.title = element_text(face = "bold", size = 20),
      plot.subtitle = element_text(color = palette[["muted"]], size = 12),
      plot.margin = margin(20, 28, 20, 28)
    )
  save_figure(p, "f2_evidence_boundary", 11.6, 3.9)
}

figure_3_predictor_auc <- function() {
  rows <- read_tsv_safe(predictor_comparison) %>%
    filter(scope == "overall", target == "human_decision_change_yes") %>%
    mutate(metric_label = recode(metric, wer = "WER", cer = "CER", sres_total = "SRES", ceis_max = "CEIS")) %>%
    mutate(metric_label = factor(metric_label, levels = c("WER", "CER", "SRES", "CEIS")))
  p <- ggplot(rows, aes(metric_label, auc, fill = metric_label)) +
    geom_col(width = 0.62) +
    geom_text(aes(label = sprintf("%.4f", auc)), vjust = -0.45, size = 3.6, fontface = "bold") +
    scale_fill_manual(values = c(WER = palette[["blue"]], CER = palette[["teal"]], SRES = palette[["orange"]], CEIS = palette[["green"]]), guide = "none") +
    scale_y_continuous(limits = c(0, 1.05), breaks = seq(0, 1, 0.25), labels = number_format(accuracy = 0.01)) +
    labs(
      title = "F3. Human-Reviewed Predictor AUC",
      subtitle = "Target: human_decision_change_yes over 90 reviewed model assessments.",
      x = NULL,
      y = "AUC",
      caption = "CEIS has the highest AUC; SRES has the best-threshold F1. Claims remain scoped to selected-300 human-reviewed aggregate evidence."
    ) +
    theme_paper()
  save_figure(p, "f3_predictor_auc", 10.8, 4.3)
}

figure_4_recovery <- function() {
  rows <- read_tsv_safe(recovery_comparison) %>%
    mutate(
      policy_label = recode(
        policy,
        no_recovery = "None",
        confidence_only_trigger = "Conf.",
        sres_triggered_recovery = "SRES",
        ceis_triggered_conservative_action = "CEIS",
        ceis_ensemble_arbitration = "CEIS ens."
      )
    ) %>%
    select(policy_label, high_risk_missed_count, critical_miss_count, triggered_count) %>%
    pivot_longer(c(high_risk_missed_count, critical_miss_count), names_to = "miss_type", values_to = "count") %>%
    mutate(miss_type = recode(miss_type, high_risk_missed_count = "High-risk missed", critical_miss_count = "Critical miss"))
  triggered <- read_tsv_safe(recovery_comparison) %>%
    mutate(policy_label = recode(policy, no_recovery = "None", confidence_only_trigger = "Conf.", sres_triggered_recovery = "SRES", ceis_triggered_conservative_action = "CEIS", ceis_ensemble_arbitration = "CEIS ens.")) %>%
    select(policy_label, triggered_count)
  p <- ggplot(rows, aes(policy_label, count, fill = miss_type)) +
    geom_col(position = position_dodge(width = 0.74), width = 0.62) +
    geom_text(aes(label = count), position = position_dodge(width = 0.74), vjust = -0.35, size = 3.2) +
    geom_text(data = triggered, aes(policy_label, -0.55, label = paste0("trig ", triggered_count)), inherit.aes = FALSE, color = palette[["muted"]], size = 3.1) +
    scale_fill_manual(values = c("High-risk missed" = palette[["orange"]], "Critical miss" = palette[["red"]])) +
    scale_y_continuous(limits = c(-1, 7.4), breaks = 0:7) +
    labs(
      title = "F4. Recovery Outcomes Under Human-Reviewed Labels",
      subtitle = "Counts over 90 reviewed model assessments; aggregate-only.",
      x = NULL,
      y = "Missed severe outcomes",
      fill = NULL,
      caption = "SRES and CEIS conservative policies both reach 0/0 at recovery budget 0.3889."
    ) +
    theme_paper()
  save_figure(p, "f4_recovery_outcomes", 11.2, 4.4)
}

figure_5_model_lanes <- function() {
  main_rows <- read_tsv_safe(asr_comparison)
  candidate_rows <- read_tsv_safe(candidate_table)
  candidate_json <- read_json_safe(candidate_summary)
  bounded_count <- length(candidate_json$bounded_probes %||% list())
  lanes <- tibble(
    x = 1:3,
    lane = c("Main comparable split", "Locale-gated candidates", "Runtime-blocked probes"),
    count = c(paste0(nrow(main_rows), " completed 258-row runs"), paste0(nrow(candidate_rows), " fixed 15-row candidates"), paste0(bounded_count, " bounded probes")),
    note = c("Used for split/model-comparison context", "No promotion until strict zh-TW gate is clean", "Qwen fetch/load timeout and Gemma runtime class block"),
    color = c("green", "orange", "red")
  ) %>%
    mutate(across(c(lane, count, note), ~ wrap_label(.x, width = 20)))
  p <- ggplot(lanes, aes(x, y = 1)) +
    geom_rect(aes(xmin = x - 0.38, xmax = x + 0.38, ymin = 0.68, ymax = 1.32, color = color), fill = "white", linewidth = 1.2) +
    geom_text(aes(label = lane, y = 1.15), fontface = "bold", size = 3.9) +
    geom_text(aes(label = count, y = 0.98), color = palette[["muted"]], size = 3.2) +
    geom_text(aes(label = note, y = 0.84), color = palette[["muted"]], size = 2.9) +
    annotate("rect", xmin = 0.55, xmax = 3.45, ymin = 0.2, ymax = 0.48, fill = palette[["gray"]], color = "#BCCCDC") +
    annotate("text", x = 0.66, y = 0.37, label = "Promotion rule", hjust = 0, fontface = "bold", size = 3.5) +
    annotate("text", x = 0.66, y = 0.27, label = wrap_label("Do not move candidates to 258-row or selected-300 until strict Taiwan Traditional Chinese locale evidence is clean or an isolated multimodal/audio runtime exists.", 88), hjust = 0, color = palette[["muted"]], size = 2.9) +
    scale_color_manual(values = palette[lanes$color], guide = "none") +
    coord_cartesian(xlim = c(0.45, 3.55), ylim = c(0.12, 1.45), clip = "off") +
    labs(
      title = "F5. Model Lane State",
      subtitle = "Main benchmark, candidate-lane, and runtime-blocked evidence are kept separate."
    ) +
    theme_void(base_size = 12) +
    theme(
      text = element_text(family = "DejaVu Sans", color = palette[["ink"]]),
      plot.title = element_text(face = "bold", size = 20),
      plot.subtitle = element_text(color = palette[["muted"]], size = 12),
      plot.margin = margin(20, 28, 20, 28)
    )
  save_figure(p, "f5_model_lane_state", 11.6, 4.1)
}

figure_6_n_ladder <- function() {
  layers <- tibble(
    x = 1:4,
    layer = c("Test split", "Selected provenance", "Human-reviewed audit", "Reviewed assessments"),
    unit = c("audio rows", "candidate rows / outputs", "audio rows", "model-row assessments"),
    n = c("258", "300", "30", "90"),
    role = c("ASR model comparison", "selection and provenance", "decision-critical review unit", "predictor and recovery replay"),
    color = c("blue", "orange", "green", "purple")
  ) %>%
    mutate(across(c(layer, unit, role), ~ wrap_label(.x, width = 18)))
  p <- ggplot(layers, aes(x, y = 1)) +
    geom_rect(aes(xmin = x - 0.38, xmax = x + 0.38, ymin = 0.66, ymax = 1.34, color = color), fill = "white", linewidth = 1.2) +
    geom_text(aes(label = layer, y = 1.17), fontface = "bold", size = 3.6) +
    geom_text(aes(label = paste("Unit:", unit), y = 1.0), color = palette[["muted"]], size = 2.9) +
    geom_text(aes(label = paste("N =", n), y = 0.86), fontface = "bold", size = 3.3) +
    geom_text(aes(label = role, y = 0.74), color = palette[["muted"]], size = 2.65) +
    annotate("rect", xmin = 0.55, xmax = 4.45, ymin = 0.24, ymax = 0.46, fill = palette[["gray"]], color = "#BCCCDC") +
    annotate("text", x = 0.67, y = 0.37, label = "Cluster rule", hjust = 0, fontface = "bold", size = 3.5) +
    annotate("text", x = 0.67, y = 0.29, label = wrap_label("The 90 reviewed assessments are clustered within 30 audio rows; uncertainty should use row-clustered bootstrap or leave-one-row-out sensitivity.", 96), hjust = 0, color = palette[["muted"]], size = 2.9) +
    scale_color_manual(values = palette[layers$color], guide = "none") +
    coord_cartesian(xlim = c(0.45, 4.55), ylim = c(0.18, 1.48), clip = "off") +
    labs(
      title = "F6. Evidence N-Ladder",
      subtitle = "Evaluation units are separated to avoid treating clustered model assessments as independent calls."
    ) +
    theme_void(base_size = 12) +
    theme(
      text = element_text(family = "DejaVu Sans", color = palette[["ink"]]),
      plot.title = element_text(face = "bold", size = 20),
      plot.subtitle = element_text(color = palette[["muted"]], size = 12),
      plot.margin = margin(20, 28, 20, 28)
    )
  save_figure(p, "f6_n_ladder", 11.8, 3.9)
}

figure_7_budget_risk_frontier <- function() {
  rows <- read_tsv_safe(fixed_budget_frontier) %>%
    mutate(metric_label = recode(score_metric, sres_total = "SRES", ceis = "CEIS"))
  p <- ggplot(rows, aes(observed_budget_rate, severe_missed_count, color = metric_label)) +
    geom_line(linewidth = 1.1) +
    geom_point(size = 3.2) +
    geom_text(aes(label = paste0("trig ", triggered_count, "\nratio ", signif(triggers_per_severe_miss_eliminated, 3))), hjust = -0.05, vjust = -0.55, size = 2.8, show.legend = FALSE) +
    scale_color_manual(values = c(SRES = palette[["orange"]], CEIS = palette[["green"]])) +
    scale_x_continuous(limits = c(0, 0.6), breaks = seq(0, 0.6, 0.2), labels = number_format(accuracy = 0.1)) +
    scale_y_continuous(limits = c(0, 7), breaks = 0:7) +
    labs(
      title = "F7. Budget-Risk Frontier In Aggregate Replay",
      subtitle = "Fixed-budget ranked replay over 90 reviewed model assessments; aggregate-only.",
      x = "Recovery budget",
      y = "Severe missed outcomes remaining",
      color = NULL,
      caption = "CEIS reaches 0 severe misses at the 10% replay budget; SRES reaches 0 severe misses when all 35 eligible triggers are used. Retrospective replay, not a deployment threshold."
    ) +
    theme_paper()
  save_figure(p, "f7_budget_risk_frontier", 11.8, 4.5)
}

figure_8_low_wer_danger <- function() {
  rows <- read_tsv_safe(low_wer_danger) %>%
    mutate(model = if_else(asr_run_id == "ALL", "ALL", model_label(asr_run_id))) %>%
    select(model, low_wer_rows, low_wer_label_flip_count, low_wer_unsafe_downrouting_count, low_wer_high_risk_missed_count, low_wer_critical_miss_count, low_wer_sres_trigger_count, low_wer_ceis_trigger_count) %>%
    pivot_longer(-c(model, low_wer_rows), names_to = "signal", values_to = "count") %>%
    mutate(
      signal = recode(
        signal,
        low_wer_label_flip_count = "Label flip",
        low_wer_unsafe_downrouting_count = "Unsafe downrouting",
        low_wer_high_risk_missed_count = "High-risk missed",
        low_wer_critical_miss_count = "Critical miss",
        low_wer_sres_trigger_count = "SRES trigger",
        low_wer_ceis_trigger_count = "CEIS trigger"
      ),
      model = fct_relevel(model, "ALL")
    )
  p <- ggplot(rows, aes(signal, count, fill = signal)) +
    geom_col(width = 0.72) +
    geom_text(aes(label = paste0(count, "/", low_wer_rows)), vjust = -0.35, size = 2.8) +
    facet_wrap(~ model, ncol = 2, scales = "free_y") +
    scale_y_continuous(breaks = breaks_width(1), expand = expansion(mult = c(0, 0.18))) +
    scale_fill_manual(values = c(
      "Label flip" = palette[["purple"]],
      "Unsafe downrouting" = palette[["red"]],
      "High-risk missed" = palette[["orange"]],
      "Critical miss" = "#8B0000",
      "SRES trigger" = palette[["teal"]],
      "CEIS trigger" = palette[["green"]]
    ), guide = "none") +
    labs(
      title = "F8. Low-WER Danger Signals",
      subtitle = "Low-WER rows can still carry decision-changing or conservative-trigger signals.",
      x = NULL,
      y = "Low-WER row count",
      caption = "Source: low_wer_danger_summary.tsv; threshold WER <= 10. Aggregate proxy evidence, not row-level transcript disclosure."
    ) +
    theme_paper(base_size = 11) +
    theme(axis.text.x = element_text(angle = 28, hjust = 1))
  save_figure(p, "f8_low_wer_danger", 12, 6.8)
}

figure_9_atom_instability <- function() {
  rows <- read_tsv_safe(risk_atom_instability) %>%
    mutate(
      model = model_label(asr_run_id),
      risk_atom_type = str_replace_all(risk_atom_type, "_", " ")
    )
  p <- ggplot(rows, aes(risk_atom_type, model, fill = unstable_variant_rate)) +
    geom_tile(color = "white", linewidth = 0.8) +
    geom_text(aes(label = paste0(percent(unstable_variant_rate, accuracy = 0.1), "\n", unstable_variant_rows, "/", variant_rows)), size = 3.0, color = palette[["ink"]]) +
    scale_fill_viridis_c(option = "C", labels = percent_format(accuracy = 1), name = "Unstable\nvariant rate") +
    labs(
      title = "F9. Risk-Atom Instability Heatmap",
      subtitle = "Instability concentrates differently by model and decision-critical atom.",
      x = "Risk atom",
      y = NULL,
      caption = "Source: risk_atom_instability.tsv. Counts are aggregate proxy variant rows; no transcript text or sample IDs."
    ) +
    theme_paper(base_size = 11) +
    theme(panel.grid = element_blank(), axis.text.x = element_text(angle = 25, hjust = 1))
  save_figure(p, "f9_risk_atom_instability_heatmap", 11.5, 5.5)
}

figure_10_human_atom_outcomes <- function() {
  rows <- read_tsv_safe(human_atom_review) %>%
    mutate(risk_atom_type = str_replace_all(risk_atom_type, "_", " ")) %>%
    pivot_longer(c(reviewed_row_count, critical_atom_row_count, decision_change_yes_count), names_to = "measure", values_to = "count") %>%
    mutate(
      measure = recode(
        measure,
        reviewed_row_count = "Reviewed rows",
        critical_atom_row_count = "Critical atom rows",
        decision_change_yes_count = "Decision-change yes"
      ),
      measure = factor(measure, levels = c("Reviewed rows", "Critical atom rows", "Decision-change yes"))
    )
  p <- ggplot(rows, aes(fct_reorder(risk_atom_type, count, .fun = max), count, fill = measure)) +
    geom_col(position = position_dodge(width = 0.78), width = 0.7) +
    geom_text(aes(label = count), position = position_dodge(width = 0.78), hjust = -0.25, size = 2.9) +
    coord_flip() +
    scale_fill_manual(values = c("Reviewed rows" = palette[["blue"]], "Critical atom rows" = palette[["orange"]], "Decision-change yes" = palette[["red"]])) +
    scale_y_continuous(expand = expansion(mult = c(0, 0.12))) +
    labs(
      title = "F10. Human-Reviewed Risk-Atom Outcomes",
      subtitle = "Human review connects atom coverage to criticality and decision-change evidence.",
      x = NULL,
      y = "Reviewed audio-row count",
      fill = NULL,
      caption = "Source: human_audit_risk_atom_review.tsv. Aggregate selected-300 audit evidence."
    ) +
    theme_paper()
  save_figure(p, "f10_human_reviewed_atom_outcomes", 11.2, 5.3)
}

figure_11_atom_entropy <- function() {
  rows <- read_tsv_safe(risk_atom_instability) %>%
    mutate(model = model_label(asr_run_id), atom = str_replace_all(risk_atom_type, "_", " ")) %>%
    group_by(model) %>%
    mutate(
      total_unstable = sum(unstable_variant_rows),
      p = if_else(total_unstable > 0, unstable_variant_rows / total_unstable, 0),
      entropy_contribution = if_else(p > 0, -p * log2(p), 0),
      entropy_bits = sum(entropy_contribution),
      normalized_entropy = entropy_bits / log2(n())
    ) %>%
    ungroup()
  labels <- rows %>%
    distinct(model, entropy_bits, normalized_entropy) %>%
    mutate(label = paste0("H=", round(entropy_bits, 2), " bits; norm=", round(normalized_entropy, 2)))
  p <- ggplot(rows, aes(atom, model, fill = entropy_contribution)) +
    geom_tile(color = "white", linewidth = 0.8) +
    geom_text(aes(label = paste0(round(entropy_contribution, 2), "\n", unstable_variant_rows)), size = 3.0) +
    geom_text(data = labels, aes(x = Inf, y = model, label = label), inherit.aes = FALSE, hjust = 1.04, vjust = -1.25, size = 2.8, color = palette[["muted"]]) +
    scale_fill_viridis_c(option = "D", name = "Entropy\ncontribution") +
    labs(
      title = "F11. Risk-Atom Entropy Heatmap",
      subtitle = "Entropy summarizes whether instability is concentrated in a few atom classes or spread across several classes.",
      x = "Risk atom",
      y = NULL,
      caption = "This is atom-class entropy from aggregate instability counts. Word-level confusion entropy should remain local-only unless converted into a redacted aggregate lexicon."
    ) +
    theme_paper(base_size = 11) +
    theme(panel.grid = element_blank(), axis.text.x = element_text(angle = 25, hjust = 1))
  save_figure(p, "f11_risk_atom_entropy_heatmap", 11.8, 5.5)
}

write_index <- function() {
  content <- c(
    "# CDS-ASR Figure Package",
    "",
    "Date: 2026-06-01",
    "",
    "These manuscript figures are generated by R from aggregate-only evidence.",
    "They do not include transcript text, audio IDs, selected row IDs, reviewer notes,",
    "model hypotheses, or transcript-bearing runtime logs.",
    "",
    "Generate with:",
    "",
    "```bash",
    "micromamba run -p ./.r-env Rscript 80_semantic_risk_asr/paper/generate_paper_figures.R",
    "```",
    "",
    "| Figure | SVG | PDF | Source | Privacy boundary |",
    "| --- | --- | --- | --- | --- |",
    "| F1. CDS-ASR pipeline | `f1_cds_asr_pipeline.svg` | `f1_cds_asr_pipeline.pdf` | method text | no row content |",
    "| F2. Evidence boundary | `f2_evidence_boundary.svg` | `f2_evidence_boundary.pdf` | publishable evidence summary | aggregate status only |",
    "| F3. Predictor AUC | `f3_predictor_auc.svg` | `f3_predictor_auc.pdf` | `human_audit_predictor_comparison.tsv` | aggregate predictor metrics |",
    "| F4. Recovery outcomes | `f4_recovery_outcomes.svg` | `f4_recovery_outcomes.pdf` | `policy_comparison.tsv` | aggregate policy counts |",
    "| F5. Model lane state | `f5_model_lane_state.svg` | `f5_model_lane_state.pdf` | main/candidate aggregate summaries | aggregate lane state |",
    "| F6. Evidence N-ladder | `f6_n_ladder.svg` | `f6_n_ladder.pdf` | method evidence units | aggregate counts only |",
    "| F7. Budget-risk frontier | `f7_budget_risk_frontier.svg` | `f7_budget_risk_frontier.pdf` | `fixed_budget_recovery_frontier.tsv` | aggregate policy counts |",
    "| F8. Low-WER danger signals | `f8_low_wer_danger.svg` | `f8_low_wer_danger.pdf` | `low_wer_danger_summary.tsv` | aggregate proxy counts |",
    "| F9. Risk-atom instability heatmap | `f9_risk_atom_instability_heatmap.svg` | `f9_risk_atom_instability_heatmap.pdf` | `risk_atom_instability.tsv` | aggregate proxy counts |",
    "| F10. Human-reviewed risk-atom outcomes | `f10_human_reviewed_atom_outcomes.svg` | `f10_human_reviewed_atom_outcomes.pdf` | `human_audit_risk_atom_review.tsv` | aggregate human-reviewed counts |",
    "| F11. Risk-atom entropy heatmap | `f11_risk_atom_entropy_heatmap.svg` | `f11_risk_atom_entropy_heatmap.pdf` | `risk_atom_instability.tsv` | aggregate entropy from atom counts |",
    "",
    "Word-level confusion or frequently-misrecognized-term entropy should stay local-only",
    "until converted into a redacted aggregate lexicon that contains no transcript spans,",
    "audio IDs, selected row IDs, hypotheses, or reviewer notes.",
    ""
  )
  writeLines(content, file.path(out_dir, "README.md"))
}

main <- function() {
  figure_1_pipeline()
  figure_2_boundary()
  figure_3_predictor_auc()
  figure_4_recovery()
  figure_5_model_lanes()
  figure_6_n_ladder()
  figure_7_budget_risk_frontier()
  figure_8_low_wer_danger()
  figure_9_atom_instability()
  figure_10_human_atom_outcomes()
  figure_11_atom_entropy()
  write_index()
  message("Wrote R-generated figures to ", out_dir)
}

main()

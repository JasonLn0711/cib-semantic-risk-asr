source(file.path(dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])), "plot_common.R"))

front <- read_tsv("70_experiments/runs/janus_300_high_stakes_recovery_human_reviewed_2026_05_26/fixed_budget_recovery_frontier.tsv")
front$metric_label <- metric_label(front$score_metric)

save_dual("fig5_fixed_budget_frontier", function() {
  par(mar = c(5, 5, 3, 1))
  plot(NA, xlim = range(front$observed_budget_rate), ylim = c(0, max(front$severe_missed_count) + 1), xlab = "Observed budget rate", ylab = "Severe missed count", main = "Fixed-budget conservative replay frontier")
  for (m in unique(front$metric_label)) {
    d <- front[front$metric_label == m, ]
    ord <- order(d$observed_budget_rate)
    lines(d$observed_budget_rate[ord], d$severe_missed_count[ord], type = "b", lwd = 2, pch = 19, col = ifelse(m == "CEIS", "#EE6C4D", "#3D5A80"))
  }
  legend("topright", legend = unique(front$metric_label), col = c("#3D5A80", "#EE6C4D")[seq_along(unique(front$metric_label))], lwd = 2, pch = 19)
}, width = 7, height = 5)

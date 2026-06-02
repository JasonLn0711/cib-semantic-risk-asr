source(file.path(dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])), "plot_common.R"))

pol <- read_tsv("70_experiments/runs/janus_300_high_stakes_recovery_human_reviewed_2026_05_26/policy_comparison.tsv")
pol$policy_label <- gsub("_", "\n", pol$policy)

save_dual("fig4_policy_replay", function() {
  par(mar = c(7, 5, 3, 1))
  mat <- rbind(pol$high_risk_missed_count, pol$critical_miss_count, pol$unsafe_downrouting_count)
  colnames(mat) <- pol$policy_label
  barplot(mat, beside = FALSE, col = c("#EE6C4D", "#BC6C25", "#3D5A80"), ylab = "Aggregate count", main = "Aggregate policy replay")
  legend("topright", legend = c("High-risk missed", "Critical miss", "Unsafe downrouting"), fill = c("#EE6C4D", "#BC6C25", "#3D5A80"), cex = 0.75)
}, width = 8.5, height = 5.5)

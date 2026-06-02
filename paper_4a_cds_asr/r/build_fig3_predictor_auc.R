source(file.path(dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])), "plot_common.R"))

pred <- read_tsv("70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_predictor_clustered_ci.tsv")
pred <- pred[pred$target == "human_decision_change_yes", ]
pred$label <- metric_label(pred$metric)
pred <- pred[match(c("WER", "CER", "SRES", "CEIS"), pred$label), ]

save_dual("fig3_predictor_auc", function() {
  par(mar = c(5, 5, 3, 1))
  y <- pred$point_auc
  bp <- barplot(y, names.arg = pred$label, col = bar_cols[1:4], ylim = c(0, 1), ylab = "AUC", main = "Predictor comparison with row-clustered intervals")
  arrows(bp, pred$auc_ci_low, bp, pred$auc_ci_high, angle = 90, code = 3, length = 0.05, lwd = 1.5)
  text(bp, pmin(0.98, y + 0.06), labels = sprintf("%.3f", y), cex = 0.85)
  mtext("Cluster unit: audio row; 30 clusters; 90 model assessments", side = 1, line = 4, cex = 0.78)
}, width = 7, height = 5)

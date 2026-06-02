source(file.path(dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])), "plot_common.R"))

save_dual("fig2_evidence_ladder", function() {
  counts <- c(258, 300, 30, 90)
  labels <- c("258 ASR\ntest rows", "selected-300\nprovenance", "30 reviewed\naudit rows", "90 clustered\nmodel assessments")
  par(mar = c(5, 5, 3, 1))
  bp <- barplot(counts, names.arg = labels, col = bar_cols[1:4], ylim = c(0, 330), ylab = "Evidence units", main = "Evidence ladder for Paper 4-a")
  text(bp, counts + 12, labels = counts, cex = 0.9)
  mtext("selected-300 is enriched; 90 assessments are clustered within 30 rows", side = 1, line = 4, cex = 0.8)
}, width = 7.5, height = 5)

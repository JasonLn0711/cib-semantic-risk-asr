source(file.path(dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])), "plot_common.R"))

save_dual("fig5_case_study_evidence_ladder", function() {
  counts <- c(258, 300, 300, 900)
  labels <- c("258 ASR\nrows", "selected-300\nprovenance", "300 reviewed\nrows", "900 model-level\nassessments")
  par(mar = c(5, 5, 3, 1))
  bp <- barplot(counts, names.arg = labels, col = cols[1:4], ylim = c(0, 980), ylab = "Evidence units", main = "CDS-ASR case-study evidence ladder")
  text(bp, counts + 35, labels = counts)
  mtext("Case evidence is aggregate-only; selected-300 is enriched and dual-reviewer agreement is reported.", side = 1, line = 4, cex = 0.8)
}, width = 7.5, height = 5)

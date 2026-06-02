source(file.path(dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])), "plot_common.R"))

save_dual("fig4_artifact_audit_map", function() {
  par(mar = c(1, 1, 3, 1))
  plot.new()
  title("Reviewer auditability map")
  left <- c("Artifact completeness", "Claim-evidence alignment", "Metric definitions", "Consistency checks", "Figure regeneration")
  right <- c("Raw transcript content", "Row-level interpretation", "Hidden local evidence")
  for (i in seq_along(left)) box_node(0.30, 0.85 - (i - 1) * 0.13, left[i], fill = cols[2], w = 0.35, h = 0.08)
  for (i in seq_along(right)) box_node(0.72, 0.75 - (i - 1) * 0.16, right[i], fill = cols[5], w = 0.35, h = 0.08)
  text(0.30, 0.12, "Reviewer can check", cex = 1.0, font = 2)
  text(0.72, 0.12, "Not public / governed locally", cex = 1.0, font = 2)
}, width = 8, height = 5)

source(file.path(dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])), "plot_common.R"))

save_dual("fig3_claim_registry_flow", function() {
  par(mar = c(1, 1, 3, 1))
  plot.new()
  title("Claim registry flow")
  labels <- c("Paper claim", "Artifact path", "Statistic", "Scope", "Limitation", "Validation status")
  x <- seq(0.1, 0.9, length.out = length(labels))
  for (i in seq_along(labels)) {
    box_node(x[i], 0.55, labels[i], fill = cols[(i - 1) %% length(cols) + 1], w = 0.13, h = 0.16)
    if (i < length(labels)) arrows(x[i] + 0.07, 0.55, x[i + 1] - 0.07, 0.55, length = 0.05, lwd = 2)
  }
  text(0.5, 0.25, "Every claim is routed through aggregate evidence and an explicit boundary.", cex = 0.9)
}, width = 8.5, height = 4)

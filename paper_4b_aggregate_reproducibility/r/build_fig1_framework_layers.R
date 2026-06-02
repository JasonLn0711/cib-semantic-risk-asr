source(file.path(dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])), "plot_common.R"))

save_dual("fig1_framework_layers", function() {
  par(mar = c(1, 1, 3, 1))
  plot.new()
  title("Five-layer aggregate-only reproducibility framework")
  labels <- c("Evidence\nboundary", "Aggregate\nartifact layer", "Claim\nregistry", "Operation records\n+ validation gates", "Reviewer\naudit protocol")
  y <- seq(0.82, 0.22, length.out = length(labels))
  for (i in seq_along(labels)) {
    box_node(0.5, y[i], labels[i], fill = cols[i], w = 0.5, h = 0.10)
    if (i < length(labels)) arrows(0.5, y[i] - 0.06, 0.5, y[i + 1] + 0.06, length = 0.06, lwd = 2)
  }
}, width = 6.5, height = 5)

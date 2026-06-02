source(file.path(dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])), "plot_common.R"))

save_dual("fig1_pipeline", function() {
  par(mar = c(1, 1, 3, 1))
  plot.new()
  title("CDS-ASR decision-stability pipeline")
  labels <- c("ASR\nhypotheses", "Risk atom\nextraction", "Plausible ASR\nvariants", "CEIS decision-\nstability score", "Conservative\naction / replay")
  x <- seq(0.1, 0.9, length.out = length(labels))
  y <- rep(0.55, length(labels))
  for (i in seq_along(labels)) {
    rect(x[i] - 0.08, y[i] - 0.12, x[i] + 0.08, y[i] + 0.12, col = bar_cols[(i - 1) %% length(bar_cols) + 1], border = NA)
    text(x[i], y[i], labels[i], col = "white", cex = 0.9, font = 2)
    if (i < length(labels)) {
      arrows(x[i] + 0.09, y[i], x[i + 1] - 0.09, y[i], length = 0.08, lwd = 2)
    }
  }
  text(0.5, 0.22, "Aggregate-only release boundary: no raw audio, transcripts, row IDs, reviewer notes, or transcript-bearing logs", cex = 0.82)
}, width = 9, height = 3.5)

source(file.path(dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])), "plot_common.R"))

save_dual("fig2_evidence_boundary", function() {
  par(mar = c(1, 1, 3, 1))
  plot.new()
  title("Evidence boundary map")
  box_node(0.28, 0.65, "Public aggregate\nfigures, tables,\nmanifests, gates", fill = cols[2], w = 0.36, h = 0.20)
  box_node(0.72, 0.65, "Local-only sensitive\nraw audio, transcripts,\nIDs, notes, logs", fill = cols[5], w = 0.36, h = 0.20)
  arrows(0.46, 0.65, 0.54, 0.65, length = 0.07, lwd = 2)
  text(0.5, 0.80, "Release boundary", cex = 1.0, font = 2)
  text(0.5, 0.33, "Reviewer-visible auditability is aggregate-only; row-level transcript evidence remains governed locally.", cex = 0.85)
}, width = 7.5, height = 4.5)

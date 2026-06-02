source(file.path(dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])), "plot_common.R"))

atoms <- read_tsv("70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_risk_atom_review.tsv")
atoms <- atoms[order(atoms$decision_change_yes_count, decreasing = TRUE), ]

save_dual("fig6_risk_atom_review", function() {
  par(mar = c(7, 5, 3, 1))
  bp <- barplot(atoms$decision_change_yes_count, names.arg = atoms$risk_atom_type, las = 2, col = "#6A994E", ylab = "Decision-change count", main = "Human-reviewed decision-change evidence by risk atom")
  text(bp, atoms$decision_change_yes_count + 0.5, labels = atoms$decision_change_yes_count, cex = 0.85)
}, width = 7, height = 5)

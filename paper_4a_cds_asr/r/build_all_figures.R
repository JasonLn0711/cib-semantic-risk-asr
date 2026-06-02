scripts <- c(
  "build_fig1_pipeline.R",
  "build_fig2_evidence_ladder.R",
  "build_fig3_predictor_auc.R",
  "build_fig4_policy_replay.R",
  "build_fig5_fixed_budget_frontier.R",
  "build_fig6_risk_atom_review.R"
)

script_dir <- dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1]))
rscript <- file.path(dirname(dirname(R.home())), "bin", "Rscript")
if (!file.exists(rscript)) rscript <- "Rscript"
for (s in scripts) {
  message("Running ", s)
  status <- system2(rscript, file.path(script_dir, s))
  if (!identical(status, 0L)) stop("Figure script failed: ", s)
}

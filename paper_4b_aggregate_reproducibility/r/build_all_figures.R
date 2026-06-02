scripts <- c(
  "build_fig1_framework_layers.R",
  "build_fig2_evidence_boundary.R",
  "build_fig3_claim_registry_flow.R",
  "build_fig4_artifact_audit_map.R",
  "build_fig5_case_study_evidence_ladder.R"
)

script_dir <- dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1]))
rscript <- file.path(dirname(dirname(R.home())), "bin", "Rscript")
if (!file.exists(rscript)) rscript <- "Rscript"
for (s in scripts) {
  message("Running ", s)
  status <- system2(rscript, file.path(script_dir, s))
  if (!identical(status, 0L)) stop("Figure script failed: ", s)
}

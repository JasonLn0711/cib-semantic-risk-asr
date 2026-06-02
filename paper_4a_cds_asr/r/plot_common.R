args <- commandArgs(FALSE)
file_arg <- grep("^--file=", args, value = TRUE)
this_file <- if (length(file_arg)) sub("^--file=", "", file_arg[[1]]) else "paper_4a_cds_asr/r/plot_common.R"
paper_dir <- normalizePath(file.path(dirname(this_file), ".."), mustWork = FALSE)
repo_root <- normalizePath(file.path(paper_dir, ".."), mustWork = FALSE)
fig_dir <- file.path(paper_dir, "figures")
dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)

read_tsv <- function(path) {
  read.delim(file.path(repo_root, path), stringsAsFactors = FALSE, check.names = FALSE)
}

save_dual <- function(name, plot_fun, width = 8, height = 5) {
  pdf(file.path(fig_dir, paste0(name, ".pdf")), width = width, height = height)
  plot_fun()
  dev.off()
  png(file.path(fig_dir, paste0(name, ".png")), width = width * 150, height = height * 150, res = 150)
  plot_fun()
  dev.off()
}

metric_label <- function(x) {
  out <- x
  out[out == "wer"] <- "WER"
  out[out == "cer"] <- "CER"
  out[out == "sres_total"] <- "SRES"
  out[out == "ceis_max"] <- "CEIS"
  out[out == "ceis"] <- "CEIS"
  out
}

bar_cols <- c("#3D5A80", "#98C1D9", "#EE6C4D", "#293241", "#6A994E", "#BC6C25")

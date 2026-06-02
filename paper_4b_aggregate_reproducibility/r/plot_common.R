args <- commandArgs(FALSE)
file_arg <- grep("^--file=", args, value = TRUE)
this_file <- if (length(file_arg)) sub("^--file=", "", file_arg[[1]]) else "paper_4b_aggregate_reproducibility/r/plot_common.R"
paper_dir <- normalizePath(file.path(dirname(this_file), ".."), mustWork = FALSE)
repo_root <- normalizePath(file.path(paper_dir, ".."), mustWork = FALSE)
fig_dir <- file.path(paper_dir, "figures")
dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)

save_dual <- function(name, plot_fun, width = 8, height = 5) {
  pdf(file.path(fig_dir, paste0(name, ".pdf")), width = width, height = height)
  plot_fun()
  dev.off()
  png(file.path(fig_dir, paste0(name, ".png")), width = width * 150, height = height * 150, res = 150)
  plot_fun()
  dev.off()
}

read_tsv <- function(path) {
  read.delim(file.path(repo_root, path), stringsAsFactors = FALSE, check.names = FALSE)
}

cols <- c("#264653", "#2A9D8F", "#E9C46A", "#F4A261", "#E76F51", "#6D6875")

box_node <- function(x, y, label, fill = "#264653", w = 0.22, h = 0.12) {
  rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, col = fill, border = NA)
  text(x, y, label, col = "white", cex = 0.82, font = 2)
}

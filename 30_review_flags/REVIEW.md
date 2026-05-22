# JANUS Ubuntu24 Review Flags

Generated: 2026-05-18T15:17:05+08:00

## Important flags

- Part `004` is missing from both source zip archives and extracted parts.
- No files were deleted by this organization pass.
- The folder contains many audio/call filenames and should be treated as sensitive local research data.
- The extracted workspace contains embedded Python virtual environments such as `.venv` and `.venvli`; these are large and usually reproducible, but they were left untouched.
- Some nested zip files appear inside the extracted project tree, including raw/dataset archives; these were left in their original extracted locations.
- 2026-05-22: top-level `.venv/` is treated as rebuildable local state and was removed if present. Embedded `.venv`/`.venvli` directories inside extracted parts remain source-archive artifacts, not active training environments.
- 2026-05-22: symlinks were rewritten from the old `/home/jnln3799/Downloads/JANUS_ubuntu24/...` absolute base to repo-relative targets so the AudioFolder dataset can be loaded from this repo location.

## Current layout

- `00_source_archives/google_drive_split_zips/`: original Google Drive split zip files.
- `10_extracted_parts/part-###/`: extracted contents for each present split part.
- `20_inventory/`: generated file inventory and size reports.
- `30_review_flags/`: notes for missing parts, sensitivity, and cleanup candidates.

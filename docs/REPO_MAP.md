# Repo Map

This repository is organized as a local JANUS ASR data workspace. Large source
assets remain in their original archive/extracted locations; downstream
fine-tuning and experiment work should use the stable overlays.

## Canonical Layers

| Path | Role | Mutability |
| --- | --- | --- |
| `00_source_archives/` | Original Google Drive split zip archives. | Read-only source evidence. |
| `10_extracted_parts/` | Extracted JANUS Ubuntu24 parts. | Read-only unless rebuilding from archives. |
| `20_inventory/` | File inventories and size reports. | Regenerate after large structural changes. |
| `30_review_flags/` | Human review notes for missing parts and cleanup candidates. | Append/update when risks change. |
| `40_breeze_asr25_finetune_dataset/` | Existing Hugging Face AudioFolder dataset built from JANUS pairs. | Stable dataset artifact. |
| `50_janus_data_library/` | Purpose-oriented symlink/catalog overlay across all JANUS data. | Navigation/index layer. |
| `60_whisper_asr_finetuning/` | Whisper-oriented working entry point, configs, and validation scripts. | Primary training workspace. |
| `70_experiments/` | Experiment registry, run records, metric templates, and reviewed outputs. | Primary experiment log. |

## Current Fine-Tuning Dataset

Use `60_whisper_asr_finetuning/datasets/janus_165_v1/` for Whisper work. It
points back to `40_breeze_asr25_finetune_dataset/` without copying audio.

Dataset snapshot:

| Split | Rows | Hours |
| --- | ---: | ---: |
| train | 4201 | 27.88 |
| validation | 508 | 3.37 |
| test | 258 | 1.72 |

The dataset has 4,967 total audio/transcript rows and uses symlinks to the
organized extracted audio under `10_extracted_parts/`.

## Data Handling Rules

- Treat JANUS audio, transcripts, filenames, and call metadata as sensitive
  local research data.
- Do not move or delete source archives or extracted parts during training
  setup.
- Top-level `.venv/` is disposable and should be rebuilt from
  `requirements-whisper.txt`.
- Embedded `.venv` and `.venvli` directories inside `10_extracted_parts/` are
  archived runtime artifacts. They are not training inputs; delete them only
  after an explicit cleanup decision because the source archive can be used to
  reconstruct them.
- Put model checkpoints and bulk predictions under `70_experiments/runs/...`
  and keep only curated metrics/run records in git.

# JANUS Old Train Legacy Import

Status: imported_pruned

Date: 2026-05-25

## Purpose

Bring the legacy `janus_old_train` export into the repository's local-only
storage layout while preserving experiment evidence and removing non-selected
large LoRA/partial-encoder parameter payloads from the repo copy.

## Source And Storage

- Original source: `/home/jnln3799/Downloads/janus_old_train`
- Local repo copy: `90_legacy_imports/janus_old_train_2026-05-25/source_copy/`
- Local manifests: `90_legacy_imports/janus_old_train_2026-05-25/manifests/`
- Curated selected model store:
  `50_janus_data_library/06_models_and_checkpoints/legacy_janus_old_train/`

The original source was not modified.

## Result

- Copied 58,152 files into the repo-local import area.
- Verified source and repo-copy file counts matched before pruning.
- Pruned 67 non-selected or duplicate large parameter/archive payloads from the
  repo copy.
- Removed 54,835,778,633 bytes from the repo copy.
- Retained scripts, configs, trainer states, model indexes, emissions, result
  files, logs, and non-parameter archives.

## Local Manifests

| Manifest | Purpose |
| --- | --- |
| `legacy_experiment_summary.tsv` | Compact legacy LoRA and partial-encoder run summary. |
| `best_model_selection.tsv` | Selected best LoRA and partial-encoder artifacts with decision basis. |
| `parameter_prune_manifest.tsv` | Deleted local-copy parameter/archive payloads and reasons. |
| `partial_encoder_shard_hashes.tsv` | Hash evidence for the reconstructed selected partial-encoder shard pair. |

## Follow-Up

1. Load-smoke the curated LoRA adapter.
2. Load-smoke the curated partial-encoder shard pair.
3. Re-evaluate both selected artifacts on the canonical repo test split.
4. Use the stronger ASR outputs as CDS-ASR baseline inputs, not as the paper
   contribution itself.

# JANUS Old Train Legacy Import

Date: 2026-05-25

This note records the local migration of the legacy training export at
`/home/jnln3799/Downloads/janus_old_train` into this repository's local-only
data layers.

## Locations

| Item | Path | Git policy |
| --- | --- | --- |
| Original source | `/home/jnln3799/Downloads/janus_old_train` | Not modified by this migration. |
| Local repo copy | `90_legacy_imports/janus_old_train_2026-05-25/source_copy/` | Ignored; local evidence only. |
| Local manifests | `90_legacy_imports/janus_old_train_2026-05-25/manifests/` | Ignored; local evidence only. |
| Curated model store | `50_janus_data_library/06_models_and_checkpoints/legacy_janus_old_train/` | Ignored; model artifacts only. |
| Tracked run records | `70_experiments/runs/*legacy*/README.md` | Aggregate metrics and provenance only. |

## Import Result

- Initial copy: 58,152 files, 575 directories, 107.30GB apparent rsync size.
- Source and repo-copy file counts matched before pruning.
- Repo copy after pruning: about 49GB.
- Curated selected model store: about 5.9GB.
- The source in `Downloads` was not changed.

## Pruning Rule

The repository copy keeps experiment evidence and removes only large parameter
payloads that are not selected as the best LoRA or partial-encoder solution.

Retained:

- training scripts and configs
- `trainer_state.json`, emissions, tokenizer/config files, model indexes, and
  final result files
- W&B/log archives and baseline result archives
- dataset/source archives that do not carry model parameter payloads
- selected best LoRA adapter
- selected best partial-encoder shard pair

Deleted from the repo copy:

- non-selected LoRA `adapter_model.safetensors`
- non-selected or duplicate partial-encoder model shards
- large detached optimizer state payloads
- legacy zip archives that contained LoRA or partial-encoder parameter payloads,
  after extracted non-parameter evidence had been retained

Detailed local evidence is in
`90_legacy_imports/janus_old_train_2026-05-25/manifests/parameter_prune_manifest.tsv`.

## Best Breeze-ASR-25 LoRA

Selected run:
`00-other_experiments-20260525T024655Z-3-001/00-other_experiments/whisper-breeze_exp7.1_rank32`

Selected artifact:
`50_janus_data_library/06_models_and_checkpoints/legacy_janus_old_train/breeze_asr25_lora_exp7_1_rank32_best/`

Decision basis:

| Metric | Value |
| --- | ---: |
| test CER | 0.2235133881998377 |
| test WER | 0.289627321013125 |
| test loss | 0.4086827039718628 |
| RTF | 0.19078642709216767 |
| trainer best checkpoint | checkpoint-360 |
| trainer best metric | 0.22503982811792045 |

This was the lowest parsed final test CER among legacy `whisper-breeze*`
Breeze-ASR-25 LoRA runs.

## Best Breeze-ASR-25 Partial Encoder

Selected run:
`whisper-partial_ft_exp11.0_encLast4_decAll_lr5e-5_breeze/checkpoint-480`

Selected artifact:
`50_janus_data_library/06_models_and_checkpoints/legacy_janus_old_train/breeze_asr25_partial_encoder_exp11_0_checkpoint480_best/`

Decision basis:

| Metric | Value |
| --- | ---: |
| eval CER norm | 0.15062168738957965 |
| eval CER raw | 0.17507466182584763 |
| eval WER | 0.20617297067573312 |
| eval loss | 0.3664558231830597 |

The legacy export detached first model shards at source root. The curated model
store reconstructs canonical shard names for the selected checkpoint. Hash
evidence is in
`90_legacy_imports/janus_old_train_2026-05-25/manifests/partial_encoder_shard_hashes.tsv`.

## Next Steps

Completed after import:

- One-row load/inference smoke tests passed for both curated artifacts.
- Fixed 15-row pilot inference passed for both curated artifacts.
- Both 15-row prediction files passed `validate_janus_asr_hypotheses.py` with
  required labels and quality signals.
- A five-model CDS-ASR bridge was recorded under
  `70_experiments/runs/janus_15_decision_stability_legacy_best/`.

Remaining next steps:

1. Evaluate both selected artifacts on the canonical `janus_165_v1` test split,
   using the same normalization used by the existing baseline records.
2. Produce a comparable table across `breeze_asr25_15_row_baseline`,
   `breeze_asr25_lora_legacy_best`, and
   `breeze_asr25_partial_encoder_legacy_best`.
3. Feed the best ASR hypothesis set into the CDS-ASR pipeline as a baseline
   input, not as the paper's main contribution.
4. Run CEIS/SRES and downstream scam-escalation stability checks on the same
   rows, then decide whether lower CER changes the decision-stability story.
5. Keep raw transcripts, model weights, predictions, and bulk outputs local.
   Track only aggregate metrics, scripts, configs, and reviewer-safe summaries.
6. If either selected artifact will be reused outside this workstation, package
   it through a controlled storage decision rather than normal git.

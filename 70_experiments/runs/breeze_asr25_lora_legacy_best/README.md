# Breeze-ASR-25 LoRA Legacy Best

Status: imported_best

Date: 2026-05-25

## Selected Artifact

- Source run:
  `90_legacy_imports/janus_old_train_2026-05-25/source_copy/00-other_experiments-20260525T024655Z-3-001/00-other_experiments/whisper-breeze_exp7.1_rank32`
- Local model store:
  `50_janus_data_library/06_models_and_checkpoints/legacy_janus_old_train/breeze_asr25_lora_exp7_1_rank32_best/`
- Base model: `MediaTek-Research/Breeze-ASR-25`
- LoRA rank: 32
- LoRA alpha: 64
- LoRA dropout: 0.2
- Target modules: `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`,
  `up_proj`, `down_proj`

## Selection Basis

This run had the lowest parsed final test CER among the legacy
`whisper-breeze*` Breeze-ASR-25 LoRA runs.

| Candidate | test CER | test WER | test loss |
| --- | ---: | ---: | ---: |
| `whisper-breeze_exp7.1_rank32` | 0.2235133881998377 | 0.289627321013125 | 0.4086827039718628 |
| `whisper-breeze_exp8.1_rank64_lr5e-6_new_dataset` | 0.3560195926785254 | 0.45755131045437447 | 0.7358750700950623 |
| `whisper-breeze_exp7.3_rank64_drop0.1` | 0.9922626637301495 | 0.9911329616785918 | 4.22874116897583 |
| `whisper-breeze_exp7.3_rank64_lr1e-6` | 0.9922626637301495 | 0.9911329616785918 | 4.229172706604004 |
| `whisper-breeze_exp7.3_rank64_lr5e-6` | 0.9922626637301495 | 0.9911329616785918 | 4.1651930809021 |

Trainer state pointed to `checkpoint-360` as the internal best checkpoint with
best metric `0.22503982811792045`. The extracted legacy artifact only retained
the final root adapter weights, which were copied into the local model store.

## Use In This Repo

Use this as an ASR baseline candidate for transcript generation and
decision-stability testing. Do not frame this as the paper's contribution.

## Next Step

Run a load and one-row inference smoke test from the local model store, then run
the canonical `janus_165_v1` test split evaluation with the same normalization
used by existing baseline records.

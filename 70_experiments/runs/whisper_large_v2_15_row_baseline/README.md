# Run Record: whisper_large_v2_15_row_baseline

## Summary

- Status: completed
- Date: 2026-05-25
- Owner: Jason Lin
- Config: `60_whisper_asr_finetuning/configs/janus-15-asr-model-candidates.yaml`
- Dataset: `janus_165_v1`
- Model: `openai/whisper-large-v2`
- Seed: `165`
- Hardware: local RTX 5080 CUDA with cuDNN disabled

## Purpose

Generate the 15-row Whisper large-v2 hypothesis baseline for the reviewed
JANUS gold subset before any LoRA or full-corpus training.

## Inputs

- Pilot manifest:
  `40_breeze_asr25_finetune_dataset/manifests/nemo_pilot_input_manifest.jsonl`
- Gold review:
  `40_breeze_asr25_finetune_dataset/reports/gold_subset_review.tsv`
- Base checkpoint: `openai/whisper-large-v2`
- Previous run: `whisper_small_15_row_baseline`

## Inference Settings

- Runtime: CUDA with `--disable-cudnn`
- Torch dtype: `float16`
- Language/task: `zh` / `transcribe`
- Max samples: `15`
- Max new tokens: `225`
- Label mode: `heuristic_v0`

## Results

| Split | CER | WER | Loss | Notes |
| --- | ---: | ---: | ---: | --- |
| janus_15_pilot_15 | 40.01 | 100.0 | n/a | CUDA inference with `--disable-cudnn`; WER is weak for unsegmented Chinese text. |

## Observations

- `validate_janus_asr_hypotheses.py --require-labels --require-quality-signal`
  passed for all 15 expected `audio_id` values.
- The run used a pilot-only heuristic `asr_label` so the SRES, CEIS, and
  downstream-impact scripts can run before a learned routing model exists.
- Raw predictions stay under ignored `predictions/`.

## Failure Or Risk Notes

- cuDNN-enabled CUDA still fails on this workstation. This run uses CUDA while
  bypassing cuDNN kernels.
- Do not interpret the heuristic labels as final downstream classification.

## Artifacts

- Metrics: `metrics.csv`
- Raw predictions: `predictions/` (ignored local)
- Summary: `artifacts/` (ignored local)

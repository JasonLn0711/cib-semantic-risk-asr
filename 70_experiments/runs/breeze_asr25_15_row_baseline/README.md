# Run Record: breeze_asr25_15_row_baseline

## Summary

- Status: completed
- Date: 2026-05-25
- Owner: Jason Lin
- Config: `60_whisper_asr_finetuning/configs/janus-15-asr-model-candidates.yaml`
- Dataset: `janus_165_v1`
- Model: `MediaTek-Research/Breeze-ASR-25`
- Seed: `165`
- Hardware: local RTX 5080 CUDA with cuDNN disabled

## Purpose

Generate the first Taiwan-facing Breeze ASR hypothesis baseline on the reviewed
15-row JANUS gold subset.

## Inputs

- Pilot manifest:
  `40_breeze_asr25_finetune_dataset/manifests/nemo_pilot_input_manifest.jsonl`
- Gold review:
  `40_breeze_asr25_finetune_dataset/reports/gold_subset_review.tsv`
- Base checkpoint: `MediaTek-Research/Breeze-ASR-25`
- Previous run: `whisper_large_v2_15_row_baseline`

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
| janus_15_pilot_15 | 36.13 | 380.0 | n/a | CUDA inference with `--disable-cudnn`; WER is weak for unsegmented Chinese text. |

## Observations

- `validate_janus_asr_hypotheses.py --require-labels --require-quality-signal`
  passed for all 15 expected `audio_id` values.
- This is the strongest 15-row CER result among the current pilot candidates,
  but the pilot remains decision-stability focused rather than CER-only.
- Raw predictions stay under ignored `predictions/`.

## Failure Or Risk Notes

- cuDNN-enabled CUDA still fails on this workstation. This run uses CUDA while
  bypassing cuDNN kernels.
- Do not interpret the heuristic labels as final downstream classification.

## Artifacts

- Metrics: `metrics.csv`
- Raw predictions: `predictions/` (ignored local)
- Summary: `artifacts/` (ignored local)

# Run Record: breeze_asr26_15_row_stress_test

## Summary

- Status: completed
- Date: 2026-05-25
- Owner: Jason Lin
- Config: `60_whisper_asr_finetuning/configs/janus-15-asr-model-candidates.yaml`
- Dataset: `janus_165_v1`
- Model: `MediaTek-Research/Breeze-ASR-26`
- Seed: `165`
- Hardware: local RTX 5080 CUDA with cuDNN disabled

## Purpose

Run the optional Breeze-ASR-26 15-row stress test on the reviewed JANUS pilot
subset.

Breeze-ASR-26 is kept as a Taigi/Taiwanese Hokkien and dialect-robustness
stress test. It should not replace Breeze-ASR-25 as the primary Taiwan Mandarin
baseline for this corpus.

## Inputs

- Pilot manifest:
  `40_breeze_asr25_finetune_dataset/manifests/nemo_pilot_input_manifest.jsonl`
- Gold review:
  `40_breeze_asr25_finetune_dataset/reports/gold_subset_review.tsv`
- Base checkpoint: `MediaTek-Research/Breeze-ASR-26`
- Previous comparable run: `breeze_asr25_15_row_baseline`

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
| janus_15_pilot_15 | 38.49 | 1493.33 | n/a | CUDA inference with `--disable-cudnn`; WER is weak for unsegmented Chinese text. |

## Observations

- `validate_janus_asr_hypotheses.py --require-labels --require-quality-signal`
  passed for all 15 expected `audio_id` values.
- CER was between Breeze-ASR-25 (`36.13`) and Whisper large-v2 (`40.01`) on
  this small pilot, but the very high WER confirms that word-level metrics are
  not useful for this unsegmented Chinese setup.
- Keep this run as an optional stress-test comparator. Primary model choice
  should still be based on Taiwan Mandarin fit, CER, CEIS, and downstream
  decision stability.

## Failure Or Risk Notes

- cuDNN-enabled CUDA still fails on this workstation. This run uses CUDA while
  bypassing cuDNN kernels.
- Do not interpret the heuristic labels as final downstream classification.

## Artifacts

- Metrics: `metrics.csv`
- Raw predictions: `predictions/` (ignored local)
- Summary: `artifacts/` (ignored local)

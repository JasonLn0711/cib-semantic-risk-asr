# Run Record: whisper_small_smoke_test

## Summary

- Status: completed
- Date: 2026-05-25
- Owner: Jason Lin
- Config: `60_whisper_asr_finetuning/configs/whisper-small-smoke-test.yaml`
- Dataset: `janus_165_v1`
- Model: `openai/whisper-small`
- Seed: `165`
- Hardware: local CPU smoke inference

## Purpose

Verify dataset loading, preprocessing, inference wiring, training-run
configuration, and metric logging before running expensive Whisper training.

## Inputs

- AudioFolder: `60_whisper_asr_finetuning/datasets/janus_165_v1/hf_audiofolder`
- Manifest: `60_whisper_asr_finetuning/datasets/janus_165_v1/manifests`
- Base checkpoint: `openai/whisper-small`
- Previous run: none

## Training Settings

- Batch size: 4
- Gradient accumulation: 1
- Learning rate: 0.00001
- Max steps: 20
- Precision: fp16
- LoRA/adapters: disabled

## Results

| Split | CER | WER | Loss | Notes |
| --- | ---: | ---: | ---: | --- |
| janus_15_pilot_smoke_1 | 65.0 | 100.0 | n/a | CPU inference smoke only; raw predictions stay under ignored `predictions/`. |

## Observations

- The smoke runner uses the same fixed 15-row pilot manifest but defaults to
  `--max-samples 1` so it only proves loading, preprocessing, generation, and
  aggregate metric logging.
- 2026-05-25 local CPU smoke passed on `janus_train_004201`; wall time was
  `80.99` seconds. The high CER/WER is not interpreted as a model comparison.
- Full 15-row Whisper comparison remains a later comparison step after this
  smoke path is verified.

## Failure Or Risk Notes

- Do not commit raw predictions or copied audio. Only aggregate `metrics.csv`
  and this run record are repo-safe.

## Artifacts

- Metrics: `metrics.csv`
- Error analysis: `error_analysis.tsv`
- Raw predictions: `predictions/` (ignored local)
- Checkpoints: `checkpoints/`
- Logs: `logs/`

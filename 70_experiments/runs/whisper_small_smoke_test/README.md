# Run Record: whisper_small_smoke_test

## Summary

- Status: planned
- Date:
- Owner:
- Config: `60_whisper_asr_finetuning/configs/whisper-small-smoke-test.yaml`
- Dataset: `janus_165_v1`
- Model: `openai/whisper-small`
- Seed: `165`
- Hardware:

## Purpose

Verify dataset loading, preprocessing, trainer wiring, and metric logging before
running expensive Whisper training.

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
| validation |  |  |  |  |

## Observations

- 

## Failure Or Risk Notes

- 

## Artifacts

- Metrics: `metrics.csv`
- Error analysis: `error_analysis.tsv`
- Checkpoints: `checkpoints/`
- Logs: `logs/`

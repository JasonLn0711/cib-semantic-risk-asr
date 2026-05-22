# Run Record: whisper_large_v2_lora_baseline

## Summary

- Status: planned
- Date:
- Owner:
- Config: `60_whisper_asr_finetuning/configs/whisper-large-v2-lora-baseline.yaml`
- Dataset: `janus_165_v1`
- Model: `openai/whisper-large-v2`
- Seed: `165`
- Hardware:

## Purpose

Establish the first comparable Whisper large-v2 LoRA baseline on JANUS 165 v1.

## Inputs

- AudioFolder: `60_whisper_asr_finetuning/datasets/janus_165_v1/hf_audiofolder`
- Manifest: `60_whisper_asr_finetuning/datasets/janus_165_v1/manifests`
- Base checkpoint: `openai/whisper-large-v2`
- Optional domain starting point: `MediaTek-Research/Breeze-ASR-25`
- Previous run: none

## Training Settings

- Batch size: 4
- Gradient accumulation: 4
- Learning rate: 0.00001
- Epochs: 3
- Precision: fp16
- LoRA/adapters: r=16, alpha=32, dropout=0.05, target q_proj/v_proj

## Results

| Split | CER | WER | Loss | Notes |
| --- | ---: | ---: | ---: | --- |
| validation |  |  |  |  |
| test |  |  |  |  |

## Observations

- 

## Failure Or Risk Notes

- 

## Artifacts

- Metrics: `metrics.csv`
- Error analysis: `error_analysis.tsv`
- Checkpoints: `checkpoints/`
- Logs: `logs/`

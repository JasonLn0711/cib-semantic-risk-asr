# Whisper ASR Fine-Tuning Workspace

This folder is the primary working entry point for Whisper ASR fine-tuning and
related JANUS experiment tracking.

It intentionally does not copy audio. Dataset links point back to the stable
dataset artifact in `../40_breeze_asr25_finetune_dataset/`, which in turn links
to the organized extracted audio under `../10_extracted_parts/`.

## Start Here

1. Rebuild the local environment from the repo root:

   ```bash
   python3 -m venv .venv
   . .venv/bin/activate
   python -m pip install -U pip
   python -m pip install -r requirements-whisper.txt
   ```

2. Validate the dataset links:

   ```bash
   python 60_whisper_asr_finetuning/scripts/validate_whisper_dataset.py
   ```

3. Pick a config:

   - `configs/whisper-small-smoke-test.yaml` for a low-cost pipeline check.
   - `configs/whisper-large-v2-lora-baseline.yaml` for the first serious LoRA baseline.

4. Create a run folder under `../70_experiments/runs/<run_id>/` and copy the
   run template from `../70_experiments/templates/run_record.md`.

5. Register the run in `../70_experiments/registry.tsv` before starting long
   training.

## Layout

| Path | Purpose |
| --- | --- |
| `datasets/janus_165_v1/` | Whisper-ready JANUS dataset view with manifests and reports. |
| `configs/` | Reproducible training/evaluation configuration drafts. |
| `scripts/` | Local validation and helper scripts. |

## Dataset Entry Point

Use this path with Hugging Face Datasets:

```text
60_whisper_asr_finetuning/datasets/janus_165_v1/hf_audiofolder
```

It exposes:

```text
hf_audiofolder/
  train/audio/*.wav
  train/metadata.csv
  validation/audio/*.wav
  validation/metadata.csv
  test/audio/*.wav
  test/metadata.csv
```

Metadata columns include `file_name`, `sentence`, `text`, `duration`,
`alignment_score`, and `id`. Use `sentence` or `text` as the transcription
target.

# Experiment Log

Use this folder for Whisper ASR experiment records and reproducibility notes.

## Required Flow

1. Choose a config from `../60_whisper_asr_finetuning/configs/`.
2. Create `runs/<run_id>/`.
3. Copy `templates/run_record.md` into `runs/<run_id>/README.md`.
4. Add or update one row in `registry.tsv`.
5. Store metric curves in `runs/<run_id>/metrics.csv`.
6. Store reviewed qualitative errors in `runs/<run_id>/error_analysis.tsv`.

Checkpoints, TensorBoard logs, W&B folders, and bulk predictions should stay
local and are ignored by `.gitignore` unless a separate packaging decision is
made.

## Folder Contract

```text
70_experiments/
  registry.tsv
  templates/
    run_record.md
    metrics.csv
    error_analysis.tsv
  runs/
    <run_id>/
      README.md
      metrics.csv
      error_analysis.tsv
      checkpoints/       # ignored
      logs/              # ignored
      predictions/       # ignored
```

## Minimum Comparable Metrics

Every completed ASR run should report:

- validation CER
- validation WER
- test CER
- test WER
- model name or checkpoint
- dataset version
- config path
- seed
- hardware notes
- failure notes, if any

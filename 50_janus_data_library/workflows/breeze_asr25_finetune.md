# Breeze-ASR-25 Fine-Tune Workflow

Use this order when preparing or training the model from this local archive.

1. Source integrity: keep `../01_source_archives/` and the original `../10_extracted_parts/` untouched.
2. Label source: inspect `../04_labels_and_transcripts/INDEX.tsv` and prefer the curated source manifest recorded in `../05_finetune_ready/`.
3. Training entry point: use `../05_finetune_ready/links/40_breeze_asr25_finetune_dataset` or the original `../../40_breeze_asr25_finetune_dataset/hf_audiofolder`.
4. Missing data: check `../../40_breeze_asr25_finetune_dataset/reports/missing_audio.tsv`; current missing rows point to `01.3-dataset_third_seg`.
5. Whisper workspace: use `../../60_whisper_asr_finetuning/` for current configs and dataset validation.
6. Experiment logs: register runs in `../../70_experiments/registry.tsv` before long training.
7. Model outputs: put future runs under `../../70_experiments/runs/<run_id>/`, then register durable model/checkpoint references in `../06_models_and_checkpoints/` via symlink or catalog update.

Top-level `.venv/` is disposable and can be rebuilt from `../../requirements-whisper.txt`. Do not delete embedded `.venv` or `.venvli` folders inside `10_extracted_parts/`, checkpoints, raw archives, or duplicate-looking audio until the catalog reports prove they are reproducible or superseded.

# Whisper ASR Fine-Tuning Workspace

This folder is the primary working entry point for Whisper ASR fine-tuning and
related JANUS experiment tracking.

Within the broader repository, ASR is the hypothesis-generation subsystem. The
paper-facing research layer lives in `../80_semantic_risk_asr/` and uses ASR
outputs to study counterfactual decision stability under plausible transcript
alternatives.

The current JANUS pilot language profile is Taiwan-used Traditional Chinese:
Taiwan Mandarin call-center speech, `zh-TW` evaluation assumptions, and
Traditional Chinese transcript output. Breeze-ASR-25 is the primary
Taiwan-facing Breeze baseline. Breeze-ASR-26 is available as an optional
Taigi/Taiwanese Hokkien stress test and should not replace Breeze-ASR-25 as the
main Mandarin baseline.

ASR text metrics must declare their text unit. Future runners default to
`metric_normalization=zh_asr` and `wer_tokenizer=jieba`, preserving Traditional
Chinese without any Traditional/Simplified conversion. Raw whitespace WER is
available only for legacy audits and should not be used as the primary metric
for unsegmented Chinese transcripts. This applies to the Whisper-family,
legacy Breeze, and NeMo Curator pilot runners.

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

3. Build the local curation artifacts before ASR model comparison:

   ```bash
   python 60_whisper_asr_finetuning/scripts/build_janus_curation_artifacts.py --sample-size 15
   ```

   This creates the canonical audio inventory, health check, gold-subset review
   sheet, gold completion summary, long-silence review sheet, NeMo pilot
   manifest, local review packet, and ASR comparison plan under ignored local
   `40_breeze_asr25_finetune_dataset/manifests/` and `reports/` paths. Existing
   gold-review columns are preserved when the script is rerun.

4. Check whether the pilot gate is ready:

   ```bash
   python 60_whisper_asr_finetuning/scripts/validate_janus_pilot_gate.py
   ```

   This is expected to fail until the 15-row gold subset and 6-row long-silence
   review are filled.

5. Fill the local review sheets before treating pilot metrics as evidence:

   ```bash
   python 60_whisper_asr_finetuning/scripts/build_janus_human_review_packet.py
   python 60_whisper_asr_finetuning/scripts/build_janus_human_review_packet.py --import-workbook ~/Downloads/janus_15_human_review_packet_<date>/review_workbook.tsv
   python 60_whisper_asr_finetuning/scripts/review_janus_pilot_gate.py --list-incomplete
   python 60_whisper_asr_finetuning/scripts/review_janus_pilot_gate.py --mode gold --reviewer <name> --play
   python 60_whisper_asr_finetuning/scripts/review_janus_pilot_gate.py --mode long-silence --reviewer <name> --play
   ```

   The packet builder writes a local Downloads folder with the guide, copied
   review audio, `audio_manifest.tsv`, and a fillable `review_workbook.tsv`.
   Importing the workbook writes only non-empty review fields back to ignored
   local TSV files. The interactive helper is still available for direct
   row-by-row review. None of these steps commits transcripts, review notes,
   audio, or audio-derived manual judgments.

6. Re-run the pilot gate:

   ```bash
   python 60_whisper_asr_finetuning/scripts/validate_janus_pilot_gate.py
   ```

7. Run the NeMo Curator pilot on the fixed 15 rows only:

   ```bash
   .venv/bin/python 60_whisper_asr_finetuning/scripts/run_janus_nemo_curator_pilot.py \
     --runtime cpu \
     --asr-run-id nemo_curator_zh_citrinet_cpu_pilot \
     --quiet
   .venv/bin/python 80_semantic_risk_asr/scoring/validate_janus_asr_hypotheses.py \
     --hypotheses 40_breeze_asr25_finetune_dataset/manifests/asr_outputs_nemo.jsonl \
     --require-quality-signal
   ```

   The script uses NeMo Curator's ASR stage and then computes CER/WER through
   the shared repo metric helper: `metric_normalization=zh_asr`,
   `wer_tokenizer=jieba`, plus explicit `cer_raw` and `wer_raw_whitespace`
   audit fields. It writes the ignored local output
   `40_breeze_asr25_finetune_dataset/manifests/asr_outputs_nemo.jsonl`.
   Use `--runtime cuda` only after the local CUDA/cuDNN wheel stack is known to
   be compatible.

8. Pick a config:

   - `configs/whisper-small-smoke-test.yaml` for a low-cost pipeline check.
   - `configs/whisper-large-v2-lora-baseline.yaml` for the first serious LoRA baseline.
   - `configs/janus-15-asr-model-candidates.yaml` for the fixed 15-row
     Whisper, NeMo, Breeze-ASR-25, and optional Breeze-ASR-26 comparison
     contract.

9. Run the Whisper small smoke test before any long training:

   ```bash
   .venv/bin/python 60_whisper_asr_finetuning/scripts/run_whisper_small_smoke.py \
     --runtime cpu
   ```

   The smoke runner defaults to one fixed pilot row. It proves model loading,
   preprocessing, generation, and aggregate metric logging; it is not a model
   comparison.

10. Generate the first full 15-row Whisper-family hypothesis file:

   ```bash
   .venv/bin/python 60_whisper_asr_finetuning/scripts/run_janus_whisper_family_pilot.py \
     --run-id whisper_small_15_row_baseline \
     --model-name openai/whisper-small \
     --runtime cuda \
     --disable-cudnn
   .venv/bin/python 80_semantic_risk_asr/scoring/validate_janus_asr_hypotheses.py \
     --hypotheses 70_experiments/runs/whisper_small_15_row_baseline/predictions/whisper_small_15_row_baseline_predictions.jsonl \
     --require-labels \
     --require-quality-signal
   ```

   The local RTX 5080 can run CUDA kernels, but cuDNN convolution currently
   fails with a sublibrary version mismatch. `--disable-cudnn` keeps GPU
   execution while bypassing the broken cuDNN path. Confirm this with:

   ```bash
   .venv/bin/python 60_whisper_asr_finetuning/scripts/check_torch_cuda_asr_runtime.py
   ```

   The runner writes raw predictions under ignored `predictions/`, a local
   summary under ignored `artifacts/`, and a repo-safe aggregate `metrics.csv`.
   The same runner is used for `openai/whisper-large-v2` and
   `MediaTek-Research/Breeze-ASR-25` in the 15-row model-comparison gate.

11. Run curated legacy Breeze-ASR-25 model checks only after the local model
    import has been recorded:

   ```bash
   .venv/bin/python 60_whisper_asr_finetuning/scripts/run_legacy_breeze_asr25_smoke.py \
     --model-kind lora \
     --run-id breeze_asr25_lora_legacy_best_15_row \
     --runtime cuda \
     --disable-cudnn \
     --max-samples 15
   .venv/bin/python 60_whisper_asr_finetuning/scripts/run_legacy_breeze_asr25_smoke.py \
     --model-kind partial_encoder \
     --run-id breeze_asr25_partial_encoder_legacy_best_15_row \
     --runtime cuda \
     --disable-cudnn \
     --max-samples 15
   ```

   This runner writes ignored local predictions, summaries, and a JSONL runtime
   log with `smoke_start`, `load_model_*`, `sample_*`, and `summary_written`
   events. Record the exact command and pass/fail result in the corresponding
   `70_experiments/runs/*legacy_best/README.md` before using the outputs in
   CDS-ASR scoring.

12. Create a run folder under `../70_experiments/runs/<run_id>/` and copy the
   run template from `../70_experiments/templates/run_record.md`.

13. Register the run in `../70_experiments/registry.tsv` before starting long
   training.

## Layout

| Path | Purpose |
| --- | --- |
| `datasets/janus_165_v1/` | Whisper-ready JANUS dataset view with manifests and reports. |
| `configs/` | Reproducible training/evaluation configuration drafts. |
| `scripts/` | Local validation and helper scripts. |

See `../docs/janus_165_audio_curation_workflow.md` before using NeMo Curator or
expanding any ASR comparison beyond the selected gold subset.

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

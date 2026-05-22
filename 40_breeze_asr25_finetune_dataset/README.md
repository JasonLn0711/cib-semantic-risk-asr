# Breeze-ASR-25 Fine-Tune Dataset

Generated: 2026-05-18T15:23:17+08:00

This folder repackages the local JANUS audio/transcript pairs for fine-tuning `MediaTek-Research/Breeze-ASR-25`, which is a Whisper-large-v2 based ASR model optimized for Taiwanese Mandarin and Mandarin-English code switching.

No audio was copied. Audio files in `hf_audiofolder/*/audio/` are symlinks back to the organized JANUS export under `10_extracted_parts/`.

## Recommended Entry Point

Use this Hugging Face `AudioFolder` layout:

```text
40_breeze_asr25_finetune_dataset/
  hf_audiofolder/
    train/
      audio/*.wav
      metadata.csv
    validation/
      audio/*.wav
      metadata.csv
    test/
      audio/*.wav
      metadata.csv
  manifests/
    train.jsonl
    validation.jsonl
    test.jsonl
  reports/
```

The `metadata.csv` files use `file_name` to point to audio and include both `sentence` and `text` transcript columns so either local scripts or Hugging Face loaders can consume them.

Reference docs:

- Breeze-ASR-25 model card: https://huggingface.co/MediaTek-Research/Breeze-ASR-25
- Hugging Face AudioFolder dataset format: https://huggingface.co/docs/datasets/audio_dataset

## Split Summary

| Split | Usable rows | Duration seconds | Duration hours |
| --- | ---: | ---: | ---: |
| train | 4201 | 100376.96 | 27.88 |
| validation | 508 | 12132.02 | 3.37 |
| test | 258 | 6181.30 | 1.72 |

## Source And Filtering

- Source manifest: `10_extracted_parts/part-005/JANUS_ubuntu24/JANUS_165/cleaning_audio/02.2.1-ground_truth_dataset`.
- Source rows scanned: 6834.
- Usable matched rows: 4967.
- Dropped rows: 1867 because audio files were not found in the organized extract.
- Missing-audio parent directories: 01.3-dataset_third_seg: 1867.
- Exact duplicate rows skipped: 0.

The dropped rows are mostly references to the unavailable third-segment directory. This is consistent with the current export missing part `004`.

## Load Example

```python
from datasets import Audio, load_dataset

ds = load_dataset("audiofolder", data_dir="60_whisper_asr_finetuning/datasets/janus_165_v1/hf_audiofolder")
ds = ds.cast_column("audio", Audio(sampling_rate=16000))
print(ds)
print(ds["train"][0].keys())
```

## Reports

- `reports/missing_audio.tsv`: source manifest rows not included because the referenced WAV could not be found.
- `reports/duplicate_audio_resolution.tsv`: rows where the same basename existed in multiple extracted parts and the builder chose one canonical source.
- `manifests/*_with_sources.tsv`: audit maps from stable training IDs back to local source audio.

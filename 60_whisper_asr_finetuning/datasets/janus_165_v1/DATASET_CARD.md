# JANUS 165 Whisper Dataset v1

## Purpose

Fine-tuning and evaluating Whisper-family ASR models on JANUS 165 call-center
audio/transcript pairs.

## Physical Storage

This dataset view is an overlay:

- `hf_audiofolder` links to `../../../40_breeze_asr25_finetune_dataset/hf_audiofolder`
- `manifests` links to `../../../40_breeze_asr25_finetune_dataset/manifests`
- `reports` links to `../../../40_breeze_asr25_finetune_dataset/reports`

Audio files are symlinks into `../../../10_extracted_parts/`; no audio is
duplicated here.

## Snapshot

| Split | Rows | Duration seconds | Duration hours |
| --- | ---: | ---: | ---: |
| train | 4201 | 100376.955 | 27.88 |
| validation | 508 | 12132.017 | 3.37 |
| test | 258 | 6181.295 | 1.72 |

Total usable rows: 4,967.

## Known Gaps

- 1,867 source manifest rows were dropped because their audio could not be
  found in the organized extract.
- The missing rows point to `01.3-dataset_third_seg`, consistent with missing
  archive part `004`.
- Some original audio basenames had multiple local candidates; the existing
  dataset builder selected one canonical source and recorded the count in
  `manifests/*_with_sources.tsv`.

## Recommended Target Column

Use `sentence` as the primary ASR target. The `text` column currently mirrors
`sentence` and is kept for compatibility with common Whisper/Hugging Face
training scripts.

## Sensitive Data

This dataset contains call-center audio and transcript content. Keep raw audio,
transcripts, predictions, and error analysis local unless a separate redaction
or publication decision is made.

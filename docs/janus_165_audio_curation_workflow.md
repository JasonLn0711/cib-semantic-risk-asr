# JANUS 165 Audio Curation Workflow

Generated for the 2026-05-24 curation pass.

This document is safe to track in git. Bulk audio, transcripts, full manifests,
NeMo outputs, and detailed review sheets stay local under ignored dataset
directories.

## Scope Decision

`JANUS_165` refers to the JANUS 165 anti-fraud hotline corpus. The current
canonical ASR unit in this repo is not every duplicated wav under
`10_extracted_parts/`; it is the 4,967-row AudioFolder dataset exposed at:

```text
60_whisper_asr_finetuning/datasets/janus_165_v1/hf_audiofolder
```

That overlay points back to source audio under `10_extracted_parts/` without
copying audio.

## FIRST PRINCIPLE Next Gate

The scarce resource is not another ASR-cleaning pass or a full fine-tune. The
scarce resource is a small, auditable decision-stability sample that can show
whether plausible ASR alternatives change a downstream scam-escalation decision.

Therefore:

- Audio health checks are a preflight, not the research contribution.
- The 15-row gold subset must be human-verified before NeMo Curator output is
  treated as evaluation evidence.
- NeMo Curator is a pilot comparison and metadata/ASR-quality tool, not a
  replacement for the gold subset.
- Full 4,967-row ASR comparison and long Whisper/Breeze fine-tuning wait until
  the 15-row pilot joins cleanly by `audio_id` and produces WER/CER plus
  semantic-risk/CEIS-ready outputs.
- The first publishable unit is a reviewed decision-stability sample, not a
  broad dataset-cleaning report or small WER/CER improvement.

## Generated Artifacts

Regenerate the local curation outputs from the repo root:

```bash
python 60_whisper_asr_finetuning/scripts/build_janus_curation_artifacts.py --sample-size 15
```

The script writes:

| Artifact | Purpose | Git status |
| --- | --- | --- |
| `40_breeze_asr25_finetune_dataset/reports/raw_audio_preservation.md` | Records source locations, date range, and no-copy/no-overwrite decision. | ignored local |
| `40_breeze_asr25_finetune_dataset/manifests/audio_inventory.csv` | Canonical manifest with `audio_id`, path, duration, sample rate, channels, format, context, source, hash, notes. | ignored local |
| `40_breeze_asr25_finetune_dataset/reports/audio_health_check.csv` | Row-level basic audio health check. | ignored local |
| `40_breeze_asr25_finetune_dataset/reports/audio_health_check_summary.md` | Aggregate health summary. | ignored local |
| `40_breeze_asr25_finetune_dataset/reports/gold_subset_review.tsv` | 15-row human review sheet with candidate transcript and empty gold fields. | ignored local |
| `40_breeze_asr25_finetune_dataset/reports/gold_subset_completion_summary.md` | Completion summary for required gold-review fields. | ignored local |
| `40_breeze_asr25_finetune_dataset/reports/long_silence_review.tsv` | 6-row bounded review sheet for long-silence health flags. | ignored local |
| `40_breeze_asr25_finetune_dataset/reports/gold_review_packet.md` | Local row-by-row listening packet with audio playback commands and fill-in guidance. | ignored local |
| `40_breeze_asr25_finetune_dataset/reports/asr_evaluation_task.md` | Task definition for ASR-to-CDS evaluation beyond WER/CER. | ignored local |
| `40_breeze_asr25_finetune_dataset/manifests/nemo_pilot_input_manifest.jsonl` | Custom manifest for NeMo Curator pilot. | ignored local |
| `40_breeze_asr25_finetune_dataset/reports/nemo_curator_pilot_runbook.md` | NeMo pilot gate and output contract. | ignored local |
| `40_breeze_asr25_finetune_dataset/reports/asr_comparison_plan.tsv` | Candidate ASR systems and comparison checks. | ignored local |

## Nine-Step Execution State

1. Raw audio preservation: complete for this pass.
   No raw audio was copied, overwritten, normalized, or converted. Source
   locations remain `00_source_archives/`, `10_extracted_parts/`, and the
   `50_janus_data_library/02_raw_audio/` overlay.

2. Canonical manifest: complete for the current ASR unit.
   `audio_inventory.csv` covers 4,967 rows and includes the required fields:
   `audio_id`, `path`, `duration_sec`, `sample_rate`, `channels`, `format`,
   `speaker/context`, `source`, `hash`, and `notes`.

3. Basic audio health check: complete for the current ASR unit.
   The 2026-05-24 run found all rows at 8 kHz mono and flagged only 6 rows for
   long-silence review. It did not find empty files, ultra-short files, channel
   inconsistency, sample-rate inconsistency, or manifest duration mismatch.

4. Gold subset: selected, pending human review.
   `gold_subset_review.tsv` has 15 rows. The existing transcript is only a
   candidate reference. A row becomes gold after `human_verified_transcript`,
   `semantic_risk_label`, `risk_atoms`, `asr_confusion_terms`, and
   `would_asr_error_change_decision` are filled. The curation builder preserves
   existing review fields when rerun.

5. Task definition: complete for the first pass.
   `asr_evaluation_task.md` defines keyword miss rate, risk phrase
   mistranscription rate, escalation label flip rate, interpretation-impact
   rate, and CEIS readiness.

6. NeMo Curator pilot: staged, not yet run.
   `nemo_pilot_input_manifest.jsonl` contains the 15 selected rows. The pilot
   should wait until the gold subset has been reviewed and a NeMo Curator audio
   environment is installed.

7. ASR comparison plan: complete as a run plan.
   `asr_comparison_plan.tsv` compares NeMo ASR, Whisper small, Whisper
   large-v2 LoRA, Breeze-ASR-25, and optional faster-whisper/WhisperX on the
   same gold subset.

8. Full 4,967-row run: blocked by the pilot gate.
   Do not expand to the full dataset until NeMo output joins back to `audio_id`
   and the reviewed gold subset produces WER/CER plus semantic-risk metrics.

9. Data layering: complete as a contract.
   This repo keeps raw/extracted audio local, uses the AudioFolder overlay for
   ASR, writes generated manifests/reports under ignored dataset directories,
   and records reviewed aggregate experiment outputs under `70_experiments/`.

## Immediate Execution Order

1. Commit this curation workflow and script as the repo-safe reproducibility
   layer.
2. Review only the 15 rows in `gold_subset_review.tsv` first.
3. Fill `human_verified_transcript`, `semantic_risk_label`, `risk_atoms`,
   `asr_confusion_terms`, and `would_asr_error_change_decision`.
4. Inspect the 6 `long_silence` rows as a bounded quality check; do not reopen
   all 4,967 rows unless a pattern appears.
5. Build a local Downloads review packet with copied gate audio:
   `python 60_whisper_asr_finetuning/scripts/build_janus_human_review_packet.py`.
6. Use `gold_review_packet.md` or the Downloads review packet as the row-by-row
   listening guide if manually filling the local review sheets, or use the
   interactive helper:
   `python 60_whisper_asr_finetuning/scripts/review_janus_pilot_gate.py --mode gold --reviewer <name> --play`.
7. Fill the 6 long-silence rows with:
   `python 60_whisper_asr_finetuning/scripts/review_janus_pilot_gate.py --mode long-silence --reviewer <name> --play`.
8. Run `python 60_whisper_asr_finetuning/scripts/validate_janus_pilot_gate.py`
   and expect it to pass before NeMo/Whisper/Breeze pilot metrics are treated
   as evaluation evidence.
9. Run the NeMo Curator pilot only on `nemo_pilot_input_manifest.jsonl`.
10. Verify NeMo output joins back to the gold subset through `audio_id`.
11. Run the same 15-row subset through Whisper small, Whisper large-v2 or LoRA,
    Breeze-ASR-25, and optional faster-whisper/WhisperX if available.
12. Build the local metric-input bridge for SRES, CEIS, and downstream checks:
    `python 80_semantic_risk_asr/scoring/build_janus_pilot_metric_inputs.py --hypotheses <asr_hypotheses.tsv-or-jsonl>`.
13. Produce WER/CER plus risk-atom error and downstream label-flip checks.
14. Generate counterfactual variants and compute CEIS for the same reviewed
    subset.
15. Expand to 300-500 high-stakes segments only after the 15-row gate shows a
    usable decision-stability signal.

## NeMo Reference Points

Official NeMo Curator audio documentation describes audio curation around
local/custom manifest ingest, ASR inference, WER/CER quality assessment,
duration and format validation, metadata extraction, and export. Its manifest
concepts require `audio_filepath` and commonly use optional `text`, `duration`,
`language`, `speaker_id`, and custom metadata fields. The generated pilot
manifest follows that shape while preserving this repo's `audio_id` join key.

Reference:

- https://docs.nvidia.com/nemo/curator/curate-audio
- https://docs.nvidia.com/nemo/curator/about/concepts/audio/manifests-ingest

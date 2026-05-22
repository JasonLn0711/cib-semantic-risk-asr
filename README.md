# JANUS Counterfactual Decision-Stability ASR Workspace

Generated: 2026-05-18T15:17:05+08:00

This repository is a local research workspace for JANUS high-stakes call-center
ASR data.

The single short-term paper axis is **Counterfactual Decision-Stability ASR
(CDS-ASR)**.

The paper is not about fine-tuning Whisper as the main contribution. Whisper and
Breeze-ASR baselines provide ASR hypotheses. The main contribution is a way to
test whether downstream decisions remain stable under plausible ASR
alternatives.

The guardrail is explicit: do not sell this as another ASR benchmark, small CER
improvement, or human-review workflow. Sell it as decision stability under
plausible transcript alternatives in high-stakes conversational decision
systems.

```text
audio
-> ASR transcript + confidence / n-best / timestamps
-> risk atom extraction
-> plausible counterfactual transcript variants
-> downstream decision stability / CEIS
-> automatic constrained recovery or conservative machine action
```

The original downloaded zip files were kept, and the extracted folders were
moved into stable `part-###` names. Large audio/transcript assets remain local.

## Layout

| Path | Purpose |
| --- | --- |
| `00_source_archives/google_drive_split_zips/` | Original downloaded split zip archives. Keep these as source evidence. |
| `10_extracted_parts/part-###/` | Extracted contents from each present archive part. |
| `20_inventory/` | Generated inventory files for search, review, and cleanup planning. |
| `30_review_flags/` | Human-readable notes about missing parts and risk areas. |
| `40_breeze_asr25_finetune_dataset/` | Existing Hugging Face AudioFolder dataset with JANUS audio/transcript pairs. |
| `50_janus_data_library/` | Purpose/type overlay for navigating source, audio, labels, models, environments, and reports. |
| `60_whisper_asr_finetuning/` | Primary Whisper ASR fine-tuning workspace, dataset entry point, configs, and validation scripts. |
| `70_experiments/` | Experiment registry, run records, metric templates, and reviewed ASR outputs. |
| `80_semantic_risk_asr/` | Main paper axis: CDS-ASR, risk atoms, counterfactual variants, CEIS scoring, downstream scam escalation, and automatic recovery policy. |
| `docs/` | Repo-level data map and handling rules. |

## Inventory files

| File | Use |
| --- | --- |
| `20_inventory/archive_parts.tsv` | Source zip list with sizes and matching extracted-part status. |
| `20_inventory/extracted_parts.tsv` | One-row summary per extracted part. |
| `20_inventory/file_inventory.tsv` | Full file inventory with relative paths, sizes, extensions, and modified times. |
| `20_inventory/extension_counts.tsv` | File type counts. |
| `20_inventory/largest_files.tsv` | Largest files for storage review. |
| `20_inventory/moves.tsv` | Audit trail for this organization pass. |

## Notes

- Missing expected part: `004`.
- The 2026-05-18 archive organization pass performed no data deletion.
- Treat audio/call data and filenames as sensitive.
- If storage cleanup is needed later, review `30_review_flags/REVIEW.md` and `20_inventory/largest_files.tsv` first.

## 2026-05-22 Whisper ASR Workspace Update

- Top-level `.venv/` is treated as disposable and should be rebuilt from `requirements-whisper.txt`.
- All old symlinks that pointed at `/home/jnln3799/Downloads/JANUS_ubuntu24/...` were rewritten to repo-relative targets.
- The training entry point is now `60_whisper_asr_finetuning/datasets/janus_165_v1/hf_audiofolder`.
- Experiment records should be registered in `70_experiments/registry.tsv` before long training runs.

## Purpose-Oriented Library

A complete purpose/type overlay is available at `50_janus_data_library/`.

Use it to navigate the archive by goal:

- source archives
- raw audio
- segmented audio
- labels and transcripts
- Breeze-ASR-25 fine-tune-ready dataset
- models and checkpoints
- code and pipelines
- runtime environments
- evaluation and reports
- inventory and audit

For Whisper-specific work, start with `docs/REPO_MAP.md` and
`60_whisper_asr_finetuning/README.md`.

For the paper-facing research frame, start with
`80_semantic_risk_asr/README.md` and
`80_semantic_risk_asr/paper/story_outline.md`.

## Automated Version Control

This repo uses SemVer-style automated versioning. Current version:

```text
v2.5.9
```

Source of truth:

- `VERSION`
- `version_manifest.json`
- `CHANGELOG.md`
- `version_history.jsonl`
- `VERSIONING.md`

Install the local git hook once per checkout:

```bash
python3 scripts/install_version_hooks.py
```

After installation, every commit that stages versioned repo content runs
`scripts/auto_version.py --stage`, bumps the version, updates the manifest, and
records a human-readable plus JSONL version log.

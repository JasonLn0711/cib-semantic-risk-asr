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
| `90_legacy_imports/` | Local-only legacy import area for old JANUS training exports, including pruned manifests and provenance records. |
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
- The 2026-05-25 `janus_old_train` import is local-only under
  `90_legacy_imports/`; non-selected LoRA and partial-encoder parameter files
  were pruned from the repo copy while experiment metadata and analysis records
  were retained.
- The 2026-05-25 canonical 258-row test split comparison now has aggregate
  six-model evidence under
  `70_experiments/runs/janus_258_test_split_asr_cds_proxy/`: legacy partial
  encoder, legacy LoRA, Breeze-ASR-25 base, Breeze-ASR-26, Whisper large-v2,
  and Whisper small. The partial encoder remains the current ASR hypothesis
  generator candidate.
- The expanded ASR candidate matrix is recorded in
  `docs/asr_candidate_expansion_2026_05_25.md` and
  `60_whisper_asr_finetuning/configs/janus-15-asr-model-candidates.yaml`.
  New candidates must pass smoke, 15-row hypothesis contract, runtime logging,
  and Taiwan Traditional Chinese locale gates before any full split run.
- The postdoc-level roadmap after the 258-row gate is recorded in
  `docs/postdoc_next_steps_2026_05_25.md`. It defines the next sequence:
  complete comparable 258-row baselines, add split-aware metric inputs, run the
  300-row high-stakes main experiment, then evaluate recovery policies.
- Split-aware metric-input generation now lives at
  `80_semantic_risk_asr/scoring/build_janus_metric_inputs.py`, with validation
  recorded in
  `70_experiments/runs/janus_split_aware_metric_inputs_2026_05_25/`. Full
  manifest transcripts are available for `4967` rows, but full human-reviewed
  CDS ground truth currently covers the 15-row gold subset only.
- The first automatic recovery policy gate now lives at
  `80_semantic_risk_asr/recovery/evaluate_recovery_policies.py`, with the
  six-model 258-row proxy result recorded in
  `70_experiments/runs/janus_258_recovery_policy_proxy_2026_05_25/`. Treat it
  as engineering evidence only until the selected 300-row high-stakes and
  human risk-atom audit gates run.
- The 2026-05-25 WER audit is recorded in
  `70_experiments/runs/wer_metric_audit_2026_05_25/`. The latest audit checks
  six 258-row hypothesis files against the canonical manifest, records package
  versions, and cross-checks zh-jieba corpus WER against `jiwer`. Pre-audit WER
  fields are legacy raw whitespace-token values; paper-facing ASR tables should
  use the `cer_zh_micro` aggregate column as the primary surface metric and
  `wer_zh_jieba_micro` only as a supplemental segmented word metric.
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
`80_semantic_risk_asr/paper/story_outline.md`. For the current postdoc-level
execution sequence, start with `docs/postdoc_next_steps_2026_05_25.md`.

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

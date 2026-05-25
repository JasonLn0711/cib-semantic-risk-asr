# Repo Map

This repository is organized as a local JANUS Counterfactual Decision-Stability
ASR research workspace. Large source assets remain in their original
archive/extracted locations; downstream fine-tuning and CDS-ASR experiments
should use the stable overlays.

The paper-facing research object is narrow: conventional WER/CER can miss
decision-unstable ASR outputs in high-stakes call-center conversations.

## Canonical Layers

| Path | Role | Mutability |
| --- | --- | --- |
| `00_source_archives/` | Original Google Drive split zip archives. | Read-only source evidence. |
| `10_extracted_parts/` | Extracted JANUS Ubuntu24 parts. | Read-only unless rebuilding from archives. |
| `20_inventory/` | File inventories and size reports. | Regenerate after large structural changes. |
| `30_review_flags/` | Human review notes for missing parts and cleanup candidates. | Append/update when risks change. |
| `40_breeze_asr25_finetune_dataset/` | Existing Hugging Face AudioFolder dataset built from JANUS pairs. | Stable dataset artifact. |
| `50_janus_data_library/` | Purpose-oriented symlink/catalog overlay across all JANUS data. | Navigation/index layer. |
| `60_whisper_asr_finetuning/` | Whisper-oriented working entry point, configs, and validation scripts. | Primary training workspace. |
| `70_experiments/` | Experiment registry, run records, metric templates, and reviewed outputs. | Primary experiment log. |
| `80_semantic_risk_asr/` | CDS-ASR design, risk atom schema, counterfactual variants, CEIS scoring, downstream scam escalation task, and automatic constrained recovery policy. | Primary paper workspace. |
| `90_legacy_imports/` | Local-only imports from legacy training exports, including copy manifests, pruning logs, and source-provenance evidence. | Local append-only evidence; never commit raw exports or weights. |
| `VERSION`, `version_manifest.json`, `CHANGELOG.md`, `version_history.jsonl`, `VERSIONING.md` | Automated SemVer version-control state, human log, machine log, and rules. | Updated automatically by local git hook. |

## Current Fine-Tuning Dataset

Use `60_whisper_asr_finetuning/datasets/janus_165_v1/` for Whisper work. It
points back to `40_breeze_asr25_finetune_dataset/` without copying audio.

For the curation workflow that prepares the canonical manifest, health check,
gold subset review table, NeMo pilot manifest, and ASR comparison plan, use
`docs/janus_165_audio_curation_workflow.md`.

Dataset snapshot:

| Split | Rows | Hours |
| --- | ---: | ---: |
| train | 4201 | 27.88 |
| validation | 508 | 3.37 |
| test | 258 | 1.72 |

The dataset has 4,967 total audio/transcript rows and uses symlinks to the
organized extracted audio under `10_extracted_parts/`.

## Data Handling Rules

- Treat JANUS audio, transcripts, filenames, and call metadata as sensitive
  local research data.
- Do not move or delete source archives or extracted parts during training
  setup.
- Top-level `.venv/` is disposable and should be rebuilt from
  `requirements-whisper.txt`.
- Embedded `.venv` and `.venvli` directories inside `10_extracted_parts/` are
  archived runtime artifacts. They are not training inputs; delete them only
  after an explicit cleanup decision because the source archive can be used to
  reconstruct them.
- The repo-level `.gitignore` intentionally excludes raw audio/video, compressed
  corpora, generated dataset tables/arrays, model weights, checkpoints,
  experiment artifacts, and local caches. Track source docs, configs, scripts,
  small samples, and reviewed aggregate records instead.
- Keep legacy imports under `90_legacy_imports/` local-only. For the
  2026-05-25 `janus_old_train` migration, the original
  `/home/jnln3799/Downloads/janus_old_train` source was not modified; only the
  repo copy was pruned.
- Put model checkpoints and bulk predictions under `70_experiments/runs/...`
  and keep only curated metrics/run records in git.
- Version-control automation lives in `scripts/auto_version.py` and
  `.githooks/pre-commit`; install it with
  `python3 scripts/install_version_hooks.py` in each local checkout.

## Research-Framing Rules

- Do not frame the paper as only Whisper, LoRA, or CER/WER optimization.
- Treat WER/CER and SRES as baseline metrics, not the main contribution.
- Evaluate ASR by whether downstream decisions remain stable under plausible
  transcript alternatives.
- Use risk atoms first: negation, amount, action, actor, intent, time,
  uncertainty, and scam-pattern corruption.
- Use one downstream task first: scam escalation classification.
- Use one automatic recovery mechanism first: high-CEIS span alignment,
  constrained re-decoding, ASR ensemble arbitration, decision interval
  estimation, and conservative machine action.
- For reviewer-facing metric analysis, compare WER/CER/SRES/CEIS against
  downstream label flips, unsafe downrouting, high-risk misses, low-WER danger
  counts, and risk-atom instability. Keep predictor outputs aggregate-only.

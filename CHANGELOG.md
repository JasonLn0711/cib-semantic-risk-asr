# Version Log

This file is maintained by `scripts/auto_version.py`.

Every automatic bump is also recorded as a machine-readable JSON line in
`version_history.jsonl`.

## v2.5.10 - 2026-05-24T23:59:55+08:00

- Bump: `patch`
- Trigger: `pre-commit`
- Base commit: `acf742b`
- Branch: `main`
- Summary: Add reproducible JANUS curation artifact builder.
- Changed files:
  - `60_whisper_asr_finetuning/scripts/build_janus_curation_artifacts.py`

## v2.5.9 - 2026-05-22T18:50:42+08:00

- Bump: `initial`
- Trigger: `bootstrap`
- Base commit: `264b4a5`
- Branch: `main`
- Summary: Bootstrap automated repo version control.
- Changed files:
  - `VERSION`
  - `version_manifest.json`
  - `CHANGELOG.md`
  - `version_history.jsonl`
  - `VERSIONING.md`
  - `README.md`
  - `docs/REPO_MAP.md`
  - `scripts/auto_version.py`
  - `scripts/install_version_hooks.py`
  - `.githooks/pre-commit`

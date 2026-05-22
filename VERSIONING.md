# Automated Version Control

This repository uses SemVer-style automatic versioning.

Current version source of truth:

- `VERSION`
- `version_manifest.json`
- `CHANGELOG.md`
- `version_history.jsonl`

## Version Format

Use:

```text
vMAJOR.MINOR.PATCH
```

Example:

```text
v2.5.9
```

## FIRST PRINCIPLE Rule

The version should answer:

> What changed in the repo, and can a future reader reconstruct when and why it
> changed?

Therefore, every version bump must update:

- the current version;
- a human-readable changelog entry;
- a machine-readable JSONL history entry;
- the manifest fields needed to identify changed files and trigger reason.

## Automatic Trigger

The tracked git hook `.githooks/pre-commit` runs:

```bash
python3 scripts/auto_version.py --stage
```

The hook inspects staged changes. If staged changes include versioned repo
content, it bumps the version and stages:

- `VERSION`
- `version_manifest.json`
- `CHANGELOG.md`
- `version_history.jsonl`

## Versioned Content

By default, any staged tracked repo file can trigger a version bump, except:

- generated version files themselves;
- ignored raw-data / archive / model-output paths already covered by
  `.gitignore`;
- git-internal paths.

This means document updates, paper notes, experiment records, configs, and
scripts all create an auditable version.

## Bump Rules

Default bump:

- `patch`: ordinary document, config, script, run-record, or experiment-log
  updates.

Manual override:

```bash
VERSION_BUMP=minor git commit -m "..."
VERSION_BUMP=major git commit -m "..."
```

Use:

- `major`: paper-axis change, data contract break, incompatible workflow change,
  or governance/routing rule change that changes how the repo should be used.
- `minor`: new module, new experiment workflow, new scoring script, new dataset
  contract, or new paper section family.
- `patch`: all ordinary updates and corrections.

Skip only when intentionally making version-system repairs:

```bash
SKIP_AUTO_VERSION=1 git commit -m "..."
```

## Manual Commands

Install hooks:

```bash
python3 scripts/install_version_hooks.py
```

Run a dry-run style check of staged changes:

```bash
python3 scripts/auto_version.py --dry-run
```

Run and stage manually:

```bash
python3 scripts/auto_version.py --stage
```

Validate version files:

```bash
python3 scripts/auto_version.py --check
```

## Log Policy

`CHANGELOG.md` is for humans.

`version_history.jsonl` is append-only machine-readable history. Each line
records:

- version;
- timestamp;
- bump type;
- trigger;
- branch;
- base commit;
- summary;
- changed files.

Do not put sensitive raw audio, full transcripts, or local-only evidence into
the version log. File paths and aggregate summaries are allowed.


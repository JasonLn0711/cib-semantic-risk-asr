# Privacy Boundary

Date: 2026-05-26

Scope: CDS-ASR submission-prep artifact and reviewer package boundary

## Release Principle

This project treats transcript-bearing speech data as sensitive operational
content. Reviewer-visible reproducibility is provided through aggregate
validation artifacts, operation records, evidence matrices, manifests, and
consistency audits rather than public row-level release.

## Allowed In Repo / Reviewer Package

- aggregate run records;
- validation summaries;
- metric tables;
- evidence matrices;
- claim registry;
- artifact manifests and SHA256 checksums;
- aggregate figure files;
- paper-facing method/configuration documents;
- operation records that do not include transcript text, audio IDs, selected
  sample IDs, hypotheses, or reviewer notes.

## Local-Only / Ignored

- raw audio;
- reference transcripts;
- raw transcripts;
- selected sample IDs;
- audio IDs;
- ASR hypothesis text;
- transcript-bearing runtime logs;
- reviewer response sheets;
- reviewer notes;
- local reviewer packets and zip files;
- model weights, checkpoints, and adapters.

## Reviewer-Facing Reproducibility Statement

The public package does not claim full row-level reproducibility. It provides
privacy-preserving aggregate reproducibility: scoped evidence summaries,
operation records, validation gates, consistency checks, and checksum manifests
for aggregate artifacts.

## Stop Rule

If a candidate artifact contains transcript text, audio IDs, selected sample
IDs, raw hypotheses, local response sheets, reviewer notes, or transcript-
bearing runtime logs, it must stay local/ignored and must not enter the
reviewer-visible package.

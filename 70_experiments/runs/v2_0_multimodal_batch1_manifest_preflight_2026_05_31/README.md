# v2.0 Batch 1 Manifest Preflight

Date: 2026-05-31

Status: aggregate manifest preflight recorded; local-only manifest content is
not tracked

本紀錄只保存 manifest count/status，不保存任何逐字稿或私有音訊內容。

## Purpose

This Gate A record checks whether the local-only manifests needed for the v2.0
Batch 1 multimodal experiment exist. It records only aggregate status, row
counts, field counts, and the next required action.

## Privacy Boundary

The local manifest files may contain protected row selectors or local audio
locators. Those files must remain ignored by git. This tracked record does not
store manifest field names, row IDs, audio IDs, transcript text, hypotheses,
reviewer notes, or local file paths.

## Current Result

```text
manifest_specs=6
manifest_files_present=1
missing_required_next=False
next_gate=run_real_one_row_transcript_only_smoke_adapters
```

## Next Step

Create or attach `one_row_smoke_manifest.local.tsv` locally, then run the real
one-row transcript-only smoke adapters. Do not track the local manifest.

# v2.0 Batch 1 Candidate Discovery

Date: 2026-05-31

Status: Gate 0 complete; no model inference was run

本紀錄只保存公開模型中繼資料與治理決策，不保存任何逐字稿或私有音訊內容。

## Purpose

This run records the live metadata, license/runtime decision, and first-gate
status for the v2.0 Batch 1 audio-capable multimodal model set. It is an
aggregate-only discovery artifact. It does not contain raw audio, row IDs,
transcripts, model hypotheses, reviewer notes, runtime logs with transcript
text, or model weights.

## Batch 1 Families

The scientific Batch 1 scope remains:

```text
Kimi-Audio-7B-Instruct
Qwen2.5-Omni-7B
Step-Audio-2-mini
MOSS-Audio-4B/8B
MiniCPM-o 4.5
```

MiniCPM-o 2.6 and MiniCPM-o 2.6 int4 are recorded only as fallback/runtime
variants. They are not sixth Batch 1 scientific models.

## Generated Artifacts

```text
candidate_snapshot.tsv
candidate_snapshot_summary.json
README.md
```

The snapshot was generated with:

```bash
python3 scripts/collect_v2_0_batch1_candidate_snapshot.py
```

The generator reads public Hugging Face model metadata with `?blobs=true` and
uses static Batch 1 governance annotations from the v2.0 runbook. It records
weight-file storage estimates from public model-file metadata; it does not
download model weights.

## Gate 0 Results

| Family | Model / variant | Gate 0 decision | Next gate |
| --- | --- | --- | --- |
| Kimi-Audio | `moonshotai/Kimi-Audio-7B-Instruct` | `metadata_pending_size_boundary` | explicit size-boundary decision before runtime smoke |
| Qwen2.5-Omni | `Qwen/Qwen2.5-Omni-7B` | `runtime_ready_after_artifact_check` | isolated transcript-only runtime smoke |
| Step-Audio 2 mini | `stepfun-ai/Step-Audio-2-mini` | `runtime_ready_after_artifact_check` | isolated transcript-only runtime smoke |
| MOSS-Audio | `OpenMOSS-Team/MOSS-Audio-4B-Instruct` | `runtime_ready_after_artifact_check` | isolated transcript-only runtime smoke |
| MOSS-Audio | `OpenMOSS-Team/MOSS-Audio-8B-Instruct` | `runtime_ready_after_4b_smoke` | run only after 4B environment and prompt contract are interpretable |
| MOSS-Audio | `OpenMOSS-Team/MOSS-Audio-4B-Thinking` | `defer_until_instruct_transcript_gate` | reasoning variant after Instruct gate |
| MOSS-Audio | `OpenMOSS-Team/MOSS-Audio-8B-Thinking` | `defer_until_instruct_transcript_gate` | reasoning variant after Instruct gate |
| MiniCPM-o | `openbmb/MiniCPM-o-4_5` | `runtime_ready_after_artifact_check` | isolated transcript-only runtime smoke |
| MiniCPM-o | `openbmb/MiniCPM-o-2_6` | `fallback_only_not_batch1_main` | optional fallback only |
| MiniCPM-o | `openbmb/MiniCPM-o-2_6-int4` | `fallback_only_not_scientific_model` | runtime fallback only |

## Important Gate 0 Decisions

- Kimi-Audio remains a primary scientific candidate, but the public metadata
  needs explicit scope handling before runtime promotion: the model family and
  card text identify `Kimi-Audio-7B-Instruct`, while the current Hugging Face
  widget reports `10B params`.
- Qwen2.5-Omni, Step-Audio-2-mini, MOSS-Audio 4B Instruct, and MiniCPM-o 4.5
  are metadata-clean enough for isolated runtime smoke after artifact checks.
- MOSS-Audio 8B Instruct should run only after MOSS-Audio 4B proves the local
  environment and transcript-only prompt contract.
- MOSS-Audio Thinking variants are reasoning variants. They remain deferred
  until the corresponding Instruct transcript gate is interpretable.
- MiniCPM-o 2.6 and int4 remain fallback-only. They do not expand Batch 1.

## Source Seeds

- Kimi-Audio:
  <https://huggingface.co/moonshotai/Kimi-Audio-7B-Instruct>
- Qwen2.5-Omni:
  <https://huggingface.co/Qwen/Qwen2.5-Omni-7B>
- Step-Audio 2 mini:
  <https://huggingface.co/stepfun-ai/Step-Audio-2-mini>
- MOSS-Audio:
  <https://github.com/OpenMOSS/MOSS-Audio>
- MiniCPM-o 4.5:
  <https://huggingface.co/openbmb/MiniCPM-o-4_5>

## Privacy Boundary

This run is metadata-only. It tracks public model metadata, source URLs,
revision SHAs, license/runtime decisions, and aggregate governance status. It
does not track private JANUS rows or transcript-bearing material.

## Next Gate

The next gate is isolated one-row transcript-only runtime smoke for
metadata-clean Batch 1 models. Kimi-Audio requires a documented size-boundary
decision first.

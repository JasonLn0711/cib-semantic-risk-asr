# v2.0 Batch 1 completion audit

Date: 2026-06-01

This aggregate-only audit closes the first raw Batch 1 gate chain for the
primary zh-TW audio LLM lane. It does not record raw audio, row identifiers,
transcripts, references, model hypotheses, reviewer notes, local paths, model
outputs, transcript-bearing logs, or model cache paths.

## FIRST PRINCIPLE decision

The scarce resource is clean gate evidence, not a longer model list or larger
compute spend. A model earns the next CDS-ASR budget only after the previous
gate proves transcript validity, ASR-boundary behavior, and Taiwan Traditional
Chinese locale fitness.

## Result

The raw Batch 1 gate chain is complete and has no scientific winner. Qwen2.5-
Omni is the only model that reached fixed 15-row transcript scoring, but it
failed the raw zh-TW locale gate. MOSS-Audio-4B and MiniCPM-o 4.5 passed the
one-row transcript-like contract but failed sentinel behavior controls.
Step-Audio-2-mini failed the one-row transcript contract. Kimi-Audio is blocked
by the isolated flash_attn / CUDA-toolchain dependency boundary. MOSS-Audio-8B
is blocked by the local 16GB single-GPU resource boundary.

Taiwan utility/subgroup, human-reviewed 30-row CDS, promoted 258-row, and
selected-300 gates are skipped by gate policy for this raw run. The next
scientific action is bounded repair planning, not larger inference.

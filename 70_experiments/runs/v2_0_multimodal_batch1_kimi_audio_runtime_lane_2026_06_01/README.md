# Kimi-Audio Runtime Lane Preparation

Date: 2026-06-01

Status: ready_for_kimi_audio_one_row_smoke_with_dependency_caveat

本紀錄只保存 Kimi-Audio runtime/cache lane aggregate status，不保存任何逐字稿、
私有音訊內容、row ID、hypothesis、模型輸出或 model cache path。

## Size Boundary

Kimi-Audio remains in the v2.0 Batch 1 primary zh-TW audio LLM lane because the
public model label is `Kimi-Audio-7B-Instruct`. The Hugging Face widget reports
`10B params`, so the experiment keeps an explicit size-boundary validation
layer and records runtime feasibility separately from scientific quality.

## Result

```text
model_id=moonshotai/Kimi-Audio-7B-Instruct
model_revision_sha=9a82a84c37ad9eb1307fb6ed8d7b397862ef9e6b
official_repo_head=349251e1d8f4f98d58fda59246381faecd7392e0
model_cache_present=True
expected_snapshot_present=True
runtime_import_blockers=[]
transcript_only_snapshot_policy=download_main_model_and_whisper_excluding_audio_detokenizer_and_vocoder
next_gate=run_kimi_audio_one_row_transcript_only_smoke_and_classify_flash_attn_or_memory_boundary
```

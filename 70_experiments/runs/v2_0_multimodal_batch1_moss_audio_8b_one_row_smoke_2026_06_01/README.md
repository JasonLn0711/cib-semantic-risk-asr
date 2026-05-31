# MOSS-Audio-8B One-Row Transcript-Only Smoke

Date: 2026-06-01

Status: moss_audio_8b_one_row_smoke_classified_runtime_boundary

本紀錄只保存 MOSS-Audio-8B one-row smoke aggregate status。模型輸出、音檔
路徑、row ID、逐字稿與 hypothesis 均保存在 ignored local runtime lane，不進入 git。

## Runtime Boundary

MOSS-Audio-8B is evaluated after MOSS-Audio-4B proved the transcript-only
prompt contract is interpretable. On this local 16GB GPU, a failed one-row
attempt is treated as a resource/runtime gate, not a transcript-quality result.

## Result

```text
model_id=OpenMOSS-Team/MOSS-Audio-8B-Instruct
smoke_status=failed:RuntimeError
valid_text_outputs=0
raw_transcript_like_outputs=0
failure_mode=resource_error:cuda_out_of_memory
promotion_decision=blocked_runtime_resource
```

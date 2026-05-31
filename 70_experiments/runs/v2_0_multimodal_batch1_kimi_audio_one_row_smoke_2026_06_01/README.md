# Kimi-Audio One-Row Transcript-Only Smoke

Date: 2026-06-01

Status: kimi_audio_one_row_smoke_classified_runtime_boundary

本紀錄只保存 Kimi-Audio one-row smoke aggregate status。模型輸出、音檔
路徑、row ID、逐字稿與 hypothesis 均保存在 ignored local runtime lane，不進入 git。

## Runtime Boundary

Kimi-Audio is kept in the primary zh-TW audio LLM lane because its public label
is `Kimi-Audio-7B-Instruct`; the HF widget `10B params` marker remains an
explicit size-boundary validation layer. The transcript-only attempt used the
official model snapshot while excluding TTS detokenizer/vocoder artifacts.

## Result

```text
model_id=moonshotai/Kimi-Audio-7B-Instruct
smoke_status=failed:RuntimeError
runtime_dependency_boundary=flash_attn_required_but_isolated_env_source_build_failed_without_usr_local_cuda_nvcc
valid_text_outputs=0
raw_transcript_like_outputs=0
failure_mode=runtime_dependency_error:flash_attn_required_by_official_main_model_remote_code
promotion_decision=blocked_runtime_dependency
```

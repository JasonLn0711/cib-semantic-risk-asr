# Qwen2.5-Omni One-Row Transcript-Only Smoke

Date: 2026-05-31

Status: qwen_one_row_smoke_complete

本紀錄只保存 Qwen one-row smoke aggregate status。模型輸出、音檔路徑、row ID、
逐字稿與 hypothesis 均保存在 ignored local runtime lane，不進入 git。

## Result

```text
model_id=Qwen/Qwen2.5-Omni-7B
smoke_status=completed
valid_text_outputs=1
raw_transcript_like_outputs=1
failure_mode=none
promotion_decision=promote_to_sentinel
```

## Next Gate

If promotion_decision is `promote_to_sentinel`, run Qwen sentinel controls.
Otherwise fix the recorded failure mode and rerun one-row transcript-only smoke.

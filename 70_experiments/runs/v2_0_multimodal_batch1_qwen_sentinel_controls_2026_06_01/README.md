# Qwen2.5-Omni Sentinel Controls

Date: 2026-06-01

Status: qwen_sentinel_controls_complete

本紀錄只保存 Qwen sentinel aggregate status。音檔路徑、row ID、逐字稿、
hypothesis 與模型輸出均保存在 ignored local runtime lane，不進入 git。

## Result

```text
sentinel_rows=6
sentinel_pass_rows=6
hallucination_on_no_speech_rows=0
instruction_followed_rows=0
promotion_decision=promote_to_15_row_candidate_pool
```

## Next Gate

If promotion_decision is `promote_to_15_row_candidate_pool`, Qwen can enter the
fixed 15-row transcript gate after the remaining Batch 1 one-row smoke order is
kept moving. If not, review the local-only outputs and adjust the transcript
contract before rerunning sentinel controls.

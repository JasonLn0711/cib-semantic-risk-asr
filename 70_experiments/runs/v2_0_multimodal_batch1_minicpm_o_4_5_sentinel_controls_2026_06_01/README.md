# MiniCPM-o 4.5 Sentinel Controls

Date: 2026-06-01

Status: minicpm_o_4_5_sentinel_controls_complete

本紀錄只保存 MiniCPM-o 4.5 sentinel aggregate status。音檔路徑、row ID、
逐字稿、hypothesis 與模型輸出均保存在 ignored local runtime lane，不進入 git。

## Runtime Boundary

This gate uses the same 4-bit NF4 local-feasibility boundary as the one-row
smoke because full-bf16 single-GPU loading exceeds the local 16GB GPU boundary.

## Result

```text
sentinel_rows=6
sentinel_pass_rows=3
hallucination_on_no_speech_rows=1
instruction_followed_rows=0
promotion_decision=do_not_promote
```

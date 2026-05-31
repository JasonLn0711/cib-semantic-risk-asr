# MiniCPM-o 4.5 One-Row Transcript-Only Smoke

Date: 2026-06-01

Status: minicpm_o_4_5_one_row_smoke_complete

本紀錄只保存 MiniCPM-o 4.5 one-row smoke aggregate status。模型輸出、音檔
路徑、row ID、逐字稿與 hypothesis 均保存在 ignored local runtime lane，不進入 git。

## Runtime Boundary

This smoke uses 4-bit NF4 quantized inference because full-bf16 single-GPU
loading exceeded the local 16GB GPU memory boundary. This record is a local
deployment feasibility and transcript-contract smoke, not full-bf16 quality
evidence.

## Result

```text
model_id=openbmb/MiniCPM-o-4_5
smoke_status=completed
quantization_policy=4bit_nf4_bfloat16_compute
valid_text_outputs=1
raw_transcript_like_outputs=1
summary_or_answer_outputs=0
failure_mode=none
promotion_decision=promote_to_sentinel
```

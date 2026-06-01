# MiniCPM-o 4.5 Guarded Fixed-15 Transcript Gate

Date: 2026-06-01

Status: minicpm_guarded_fixed_15_complete

This record runs MiniCPM-o 4.5 behind the deterministic acoustic guard for the
fixed-15 transcript and zh-TW locale gate. It is deployment-repair evidence
under the existing 4-bit NF4 local-feasibility boundary, not raw full-bf16 model
capability. Transcript-bearing row outputs remain in the ignored local runtime
lane.

## Result

```text
rows=15
guard_no_speech_rows=0
pass_to_model_rows=15
valid_output_rate=100.0
cer_zh_micro=63.8135
wer_zh_jieba_micro=68.0492
simplified_char_rate=15.2322
locale_violation_rows=14
promotion_decision=do_not_promote
```

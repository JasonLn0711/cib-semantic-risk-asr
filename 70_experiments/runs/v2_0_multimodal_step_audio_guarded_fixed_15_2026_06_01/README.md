# Step-Audio Guarded Fixed-15 Transcript Gate

Date: 2026-06-01

Status: step_audio_guarded_fixed_15_complete

This record runs Step-Audio-2-mini behind the deterministic acoustic guard for
the fixed-15 transcript and zh-TW locale gate. It is deployment-repair evidence,
not raw model capability. Transcript-bearing row outputs remain in the ignored
local runtime lane.

## Result

```text
model_id=stepfun-ai/Step-Audio-2-mini
rows=15
guard_no_speech_rows=0
pass_to_model_rows=15
valid_output_rate=100.0
cer_zh_micro=99.0953
wer_zh_jieba_micro=99.1551
simplified_char_rate=0.0
locale_violation_rows=0
promotion_decision=promote_to_semantic_damage_proxy
```

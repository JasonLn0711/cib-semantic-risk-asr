# MOSS-Audio-4B Sentinel Repair

Date: 2026-06-01

Status: moss_audio_4b_sentinel_repair_complete

This is a repaired sentinel rerun for MOSS-Audio-4B. It tests whether a stricter
transcript-only/no-speech prompt reduces no-speech and non-speech hallucination.
Transcript-bearing outputs remain in the ignored runtime lane.

## Result

```text
sentinel_rows=6
sentinel_pass_rows=3
hallucination_on_no_speech_rows=3
instruction_followed_rows=0
promotion_decision=do_not_promote
```

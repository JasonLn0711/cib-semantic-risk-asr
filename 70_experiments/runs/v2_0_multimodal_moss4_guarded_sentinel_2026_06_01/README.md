# moss4 Guarded Sentinel Controls

Source run: `v2_0_multimodal_batch1_moss_audio_4b_sentinel_repair_2026_06_01`

This record applies the deterministic acoustic guard to no-speech / non-speech rows and reuses existing aggregate behavior for pass-through speech rows.

```text
sentinel_pass_rows=6
hallucination_on_no_speech_rows=0
promotion_decision=promote_to_fixed_15_candidate_pool
```

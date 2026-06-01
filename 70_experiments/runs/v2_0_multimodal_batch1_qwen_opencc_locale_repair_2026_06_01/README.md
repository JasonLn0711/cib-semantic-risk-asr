# Qwen2.5-Omni OpenCC Locale Repair

Date: 2026-06-01

Status: qwen_opencc_locale_repair_complete

This tracked record scores OpenCC / Taiwan-term repair as deployment pipeline
evidence. It does not relabel repaired text as raw model capability.

## Result

```text
raw_locale_violation_rows=15
repaired_locale_violation_rows=7
raw_simplified_char_rate=17.8466
repaired_simplified_char_rate=0.5882
semantic_damage_proxy_rows=0
promotion_decision=repaired_pipeline_review_candidate
```

Transcript-bearing raw and repaired payloads remain in the ignored runtime lane.
The tracked controlled artifact manifest records only artifact class, count,
sensitivity, storage policy, hash, and supporting gate.

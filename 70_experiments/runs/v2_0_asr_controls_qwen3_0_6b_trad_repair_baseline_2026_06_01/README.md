# Qwen3-ASR-0.6B Traditional Chinese Repair Baseline

Date: 2026-06-01

Status: `qwen3_0_6b_traditional_chinese_repair_baseline_complete`

This tracked record evaluates deterministic Simplified-to-Traditional deployment repair on the existing Qwen3-ASR-0.6B fixed-15 candidate. It keeps raw ASR capability separate from repaired deployment evidence and tracks only aggregate metrics plus controlled artifact hash/status records.

## Result

```text
raw_locale_violation_rows=15
repaired_locale_violation_rows=8
raw_simplified_char_rate=22.6253
repaired_simplified_char_rate=0.6579
semantic_damage_blocker_rows=8
promotion_decision=do_not_promote_repaired_pipeline
```

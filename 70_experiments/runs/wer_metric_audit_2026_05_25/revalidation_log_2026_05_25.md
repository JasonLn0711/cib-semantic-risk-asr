# WER Strict Revalidation Log

Date: 2026-05-25

Scope: repo-safe recheck of ASR WER calculation after repeated concern that
historical WER values were strange.

## First-Principle Question

Does this repo compute WER in a way that is formula-compatible with
international ASR practice, and does it report that WER in a way that is valid
for Taiwan Mandarin / Traditional Chinese transcripts?

## Evidence Checked

- Shared metric helper:
  `60_whisper_asr_finetuning/scripts/asr_text_metrics.py`
- WER audit runner:
  `80_semantic_risk_asr/scoring/audit_asr_text_metrics.py`
- Split-level aggregate summarizer:
  `80_semantic_risk_asr/scoring/summarize_janus_asr_test_split.py`
- Current ASR runner paths:
  `run_janus_whisper_family_pilot.py`,
  `run_legacy_breeze_asr25_smoke.py`,
  `run_whisper_small_smoke.py`,
  `run_janus_nemo_curator_pilot.py`
- Tracked aggregate audit outputs under this run folder.
- Ignored local prediction JSONL files under `70_experiments/runs/*/predictions/`.

## Validation Commands

```bash
.venv/bin/python -m py_compile \
  60_whisper_asr_finetuning/scripts/asr_text_metrics.py \
  80_semantic_risk_asr/scoring/audit_asr_text_metrics.py \
  80_semantic_risk_asr/scoring/summarize_janus_asr_test_split.py \
  60_whisper_asr_finetuning/scripts/run_janus_whisper_family_pilot.py \
  60_whisper_asr_finetuning/scripts/run_legacy_breeze_asr25_smoke.py \
  60_whisper_asr_finetuning/scripts/run_whisper_small_smoke.py \
  60_whisper_asr_finetuning/scripts/run_janus_nemo_curator_pilot.py
```

Result: passed.

```bash
.venv/bin/python - <<'PY'
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import tempfile

root = Path.cwd()

def load(name, rel):
    spec = spec_from_file_location(name, root / rel)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

t1 = load("test_asr_text_metrics", "tests/test_asr_text_metrics.py")
t2 = load("test_wer_metric_audit", "tests/test_wer_metric_audit.py")
for fn in [
    t1.test_zh_asr_preserves_traditional_chinese_without_spaces,
    t1.test_raw_whitespace_wer_is_legacy_for_unsegmented_chinese,
    t1.test_jieba_units_can_be_cross_checked_with_jiwer,
]:
    fn()
with tempfile.TemporaryDirectory() as tmp:
    t2.test_audit_summary_flags_zero_reference_units(Path(tmp))
print("direct_test_functions_ok")
PY
```

Result: passed. The local `.venv` did not have `pytest`, so test functions were
imported directly.

```bash
.venv/bin/python 80_semantic_risk_asr/scoring/audit_asr_text_metrics.py \
  --expected-manifest 40_breeze_asr25_finetune_dataset/manifests/nemo_pilot_input_manifest.jsonl \
  --expected-rows 15 \
  --hypotheses 70_experiments/runs/breeze_asr25_15_row_baseline/predictions/breeze_asr25_15_row_baseline_predictions.jsonl \
    70_experiments/runs/breeze_asr25_lora_legacy_best_15_row/predictions/breeze_asr25_lora_legacy_best_15_row_predictions.jsonl \
    70_experiments/runs/breeze_asr25_partial_encoder_legacy_best_15_row/predictions/breeze_asr25_partial_encoder_legacy_best_15_row_predictions.jsonl \
    70_experiments/runs/breeze_asr26_15_row_stress_test/predictions/breeze_asr26_15_row_stress_test_predictions.jsonl \
    70_experiments/runs/whisper_large_v2_15_row_baseline/predictions/whisper_large_v2_15_row_baseline_predictions.jsonl \
    70_experiments/runs/whisper_small_15_row_baseline/predictions/whisper_small_15_row_baseline_predictions.jsonl \
  --output-tsv /tmp/cib_wer_recheck/legacy_15_row_metric_audit.tsv \
  --summary-json /tmp/cib_wer_recheck/legacy_15_row_summary.json
```

Result: `ok=true`.

```bash
.venv/bin/python 80_semantic_risk_asr/scoring/audit_asr_text_metrics.py \
  --expected-manifest 40_breeze_asr25_finetune_dataset/manifests/test.jsonl \
  --expected-rows 258 \
  --hypotheses 70_experiments/runs/breeze_asr25_partial_encoder_legacy_best_test_split/predictions/breeze_asr25_partial_encoder_legacy_best_test_split_predictions.jsonl \
    70_experiments/runs/breeze_asr25_lora_legacy_best_test_split/predictions/breeze_asr25_lora_legacy_best_test_split_predictions.jsonl \
    70_experiments/runs/breeze_asr25_base_test_split/predictions/breeze_asr25_base_test_split_predictions.jsonl \
    70_experiments/runs/whisper_large_v2_test_split/predictions/whisper_large_v2_test_split_predictions.jsonl \
    70_experiments/runs/whisper_small_test_split/predictions/whisper_small_test_split_predictions.jsonl \
    70_experiments/runs/breeze_asr26_test_split/predictions/breeze_asr26_test_split_predictions.jsonl \
  --output-tsv /tmp/cib_wer_recheck/text_metric_audit.tsv \
  --summary-json /tmp/cib_wer_recheck/summary.json
```

Result: `ok=true`.

```bash
.venv/bin/python 80_semantic_risk_asr/scoring/audit_asr_text_metrics.py \
  --expected-manifest 70_experiments/runs/janus_300_500_high_stakes_expansion/artifacts/high_stakes_300_manifest.jsonl \
  --expected-rows 300 \
  --hypotheses 70_experiments/runs/breeze_asr25_partial_encoder_high_stakes_300/predictions/breeze_asr25_partial_encoder_high_stakes_300_predictions.jsonl \
    70_experiments/runs/breeze_asr25_base_high_stakes_300/predictions/breeze_asr25_base_high_stakes_300_predictions.jsonl \
    70_experiments/runs/breeze_asr25_lora_high_stakes_300/predictions/breeze_asr25_lora_high_stakes_300_predictions.jsonl \
  --output-tsv /tmp/cib_wer_recheck/high_stakes_300_metric_audit.tsv \
  --summary-json /tmp/cib_wer_recheck/high_stakes_300_summary.json
```

Result: `ok=true`.

```bash
cmp -s /tmp/cib_wer_recheck/legacy_15_row_metric_audit.tsv \
  70_experiments/runs/wer_metric_audit_2026_05_25/legacy_15_row_metric_audit.tsv
cmp -s /tmp/cib_wer_recheck/text_metric_audit.tsv \
  70_experiments/runs/wer_metric_audit_2026_05_25/text_metric_audit.tsv
cmp -s /tmp/cib_wer_recheck/high_stakes_300_metric_audit.tsv \
  70_experiments/runs/wer_metric_audit_2026_05_25/high_stakes_300_metric_audit.tsv
```

Result: all comparisons returned exit code `0`, so the revalidation TSV files
matched the tracked TSV files byte-for-byte.

## Verdict

- Formula: compliant with conventional edit-distance WER when the word unit is
  explicitly declared.
- Current paper-facing WER profile: compliant as a supplemental Chinese WER
  because it uses fixed `zh_asr` normalization and fixed `jieba` segmentation.
- Primary Chinese ASR surface metric: `cer_zh_micro`, not WER.
- Legacy raw whitespace WER: not compliant as model-quality evidence for
  unsegmented Chinese; keep it only for audit/reproducibility.
- Current tracked audits: valid for reporting because they have manifest
  alignment, zero missing references, zero missing hypotheses, zero missing or
  extra IDs, zero reference mismatches, zero zero-reference-unit rows, package
  versions, and `jiwer` corpus-WER agreement.

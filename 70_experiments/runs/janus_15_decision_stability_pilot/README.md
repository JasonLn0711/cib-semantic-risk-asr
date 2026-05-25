# Run Record: janus_15_decision_stability_pilot

## Summary

- Status: planned
- Date:
- Owner:
- Config: `80_semantic_risk_asr/scoring/build_janus_pilot_metric_inputs.py`
- Dataset: `janus_165_v1`
- Model: cross-ASR metric bridge
- Seed: not applicable
- Hardware: local CPU for metric-input building

## Purpose

Convert the reviewed 15-row JANUS gold subset plus ASR hypotheses into the
three paper-facing metric inputs needed before any full-dataset run:

- SRES annotation rows;
- CEIS counterfactual variant rows;
- downstream escalation decision rows.

This is the first CDS-ASR evidence gate. It is not a Whisper fine-tuning run
and should not be used to justify a full 4,967-row run until the reviewed pilot
shows a usable decision-stability signal.

## Inputs

- Gold review: `40_breeze_asr25_finetune_dataset/reports/gold_subset_review.tsv`
- Long-silence gate: `40_breeze_asr25_finetune_dataset/reports/long_silence_review.tsv`
- ASR hypotheses: local TSV/CSV/JSONL files passed with `--hypotheses`
- Previous run: none

## Gate Prerequisites

- `validate_janus_pilot_gate.py` returns `ok: true`.
- The same 15 `audio_id` values are used across NeMo, Whisper, Breeze, and any
  optional ASR candidate.
- Each ASR hypothesis row has `audio_id`, hypothesis text, and a downstream
  ASR escalation label.

## Execution

```bash
python 80_semantic_risk_asr/scoring/build_janus_pilot_metric_inputs.py \
  --hypotheses <asr_hypotheses.tsv-or-jsonl>
python 80_semantic_risk_asr/scoring/semantic_risk_score.py \
  70_experiments/runs/janus_15_decision_stability_pilot/artifacts/metric_inputs/sres_annotation.tsv
python 80_semantic_risk_asr/scoring/counterfactual_escalation_instability.py \
  70_experiments/runs/janus_15_decision_stability_pilot/artifacts/metric_inputs/counterfactual_variants.tsv
python 80_semantic_risk_asr/downstream/evaluate_downstream_impact.py \
  70_experiments/runs/janus_15_decision_stability_pilot/artifacts/metric_inputs/downstream_escalation_decisions.tsv
```

## Results

| Metric Family | Status | Notes |
| --- | --- | --- |
| SRES | pending | Requires reviewed gold rows and ASR hypotheses. |
| CEIS | pending | Requires counterfactual rows from the metric-input bridge. |
| Downstream escalation impact | pending | Requires ASR and recovered labels. |

## Observations

-

## Failure Or Risk Notes

- Current blocker is the local human review gate, not audio health.
- Keep raw audio, full transcripts, ASR bulk predictions, and generated metric
  inputs under ignored local paths.

## Artifacts

- Local metric inputs: `artifacts/metric_inputs/`
- Aggregate metrics: pending
- Publication-safe case examples: pending

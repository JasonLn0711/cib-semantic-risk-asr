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
- NeMo Curator pilot hypotheses:
  `40_breeze_asr25_finetune_dataset/manifests/asr_outputs_nemo.jsonl`
- Other ASR hypotheses: local TSV/CSV/JSONL files passed with `--hypotheses`
- First Whisper-family 15-row run:
  `70_experiments/runs/whisper_small_15_row_baseline/predictions/whisper_small_15_row_baseline_predictions.jsonl`
- Additional 15-row model hypotheses:
  `whisper_large_v2_15_row_baseline` and `breeze_asr25_15_row_baseline`
  prediction files under ignored local `predictions/` directories.
- Previous run: none

## Gate Prerequisites

- `validate_janus_pilot_gate.py` returns `ok: true`.
- The same 15 `audio_id` values are used across NeMo, Whisper, Breeze, and any
  optional ASR candidate.
- Each ASR hypothesis row has `audio_id`, hypothesis text, and a downstream
  ASR escalation label.
- `validate_janus_asr_hypotheses.py` accepts every hypothesis file before the
  metric-input bridge is run.
- No second required listening review is needed before the 15-row model
  comparison. Use the local Downloads spot-check guide only after model outputs
  disagree on decision-critical spans or labels.

## Execution

```bash
python 60_whisper_asr_finetuning/scripts/run_janus_nemo_curator_pilot.py \
  --runtime cpu \
  --asr-run-id nemo_curator_zh_citrinet_cpu_pilot \
  --quiet
python 80_semantic_risk_asr/scoring/validate_janus_asr_hypotheses.py \
  --hypotheses 40_breeze_asr25_finetune_dataset/manifests/asr_outputs_nemo.jsonl \
  --require-quality-signal
python 80_semantic_risk_asr/scoring/validate_janus_asr_hypotheses.py \
  --hypotheses <asr_hypotheses.tsv-or-jsonl> \
  --require-labels
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
| ASR comparison | first-pass complete | NeMo output-contract check plus Whisper-small, Whisper-large-v2, and Breeze-ASR-25 on the same 15 rows. See `asr_model_comparison.tsv`. |
| SRES | first-pass complete | Three labeled model runs produced 156 rows, total SRES `4868.0`, mean SRES `31.205`. |
| CEIS | first-pass complete | Three labeled model runs produced 156 variant rows across 45 model-samples; 17 were unstable, max CEIS `15.0`, mean CEIS `2.1778`. |
| Downstream escalation impact | first-pass complete | 45 model-sample rows; ASR mismatch rate `0.3778`; high-risk missed by ASR `3`; recovery not yet applied. |

## Observations

- 2026-05-25: the human gate passed and the 15-row NeMo Curator pilot ran
  locally through `InferenceAsrNemoStage` on CPU. The output joins cleanly to
  the reviewed gold set by `audio_id` and includes `wer`/`cer` fields.
- The `nvidia/stt_zh_citrinet_1024_gamma_0_25` pilot is not a usable quality
  baseline for these Taiwanese 165 calls: aggregate WER was `100.0`; CER ranged
  from `74.32` to `89.81` with mean `83.66`. Treat it as an output-contract
  check before the Whisper/Breeze smoke comparisons.
- 2026-05-25: `openai/whisper-small` completed the fixed 15-row inference pass
  on local CUDA with cuDNN disabled. The output passed the hypothesis validator
  with labels and WER/CER quality fields, then built SRES, CEIS, and downstream
  metric inputs without unmatched IDs or missing hypothesis text.
- 2026-05-25: `openai/whisper-large-v2` and
  `MediaTek-Research/Breeze-ASR-25` completed the same 15-row pass on CUDA with
  cuDNN disabled. Breeze-ASR-25 had the best pilot CER (`36.13`), followed by
  Whisper large-v2 (`40.01`) and Whisper small (`53.08`). NeMo remains an
  output-contract comparison only (`83.66` mean CER).

## Failure Or Risk Notes

- The local NeMo Curator `JsonlReader -> InferenceAsrNemoStage` path passed
  `audio_filepath` as a pandas Series, so the repo runner feeds explicit
  `AudioTask` rows to the same Curator ASR stage.
- CUDA runtime failed on this environment with
  `CUDNN_STATUS_SUBLIBRARY_VERSION_MISMATCH` when cuDNN kernels are enabled.
  PyTorch CUDA convolution passes with cuDNN disabled, and the Whisper-small
  15-row pass used `--runtime cuda --disable-cudnn`. Do not start full-dataset
  GPU work until this remains stable across the next model candidate.
- Keep raw audio, full transcripts, ASR bulk predictions, and generated metric
  inputs under ignored local paths.

## Artifacts

- Local metric inputs: `artifacts/metric_inputs/`
- Aggregate metric outputs: `artifacts/metric_outputs/` (ignored local)
- Publication-safe case examples: pending

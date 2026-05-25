# Breeze-ASR-25 Partial Encoder Legacy Best

Status: imported_best

Date: 2026-05-25

## Selected Artifact

- Source metadata run:
  `90_legacy_imports/janus_old_train_2026-05-25/source_copy/whisper-partial_ft_exp11.0_encLast4_decAll_lr5e-5_breeze-20260525T025116Z-3-005/whisper-partial_ft_exp11.0_encLast4_decAll_lr5e-5_breeze/checkpoint-480`
- Source second shard:
  `90_legacy_imports/janus_old_train_2026-05-25/source_copy/whisper-partial_ft_exp11.0_encLast4_decAll_lr5e-5_breeze-20260525T025116Z-3-007/whisper-partial_ft_exp11.0_encLast4_decAll_lr5e-5_breeze/checkpoint-480/model-00002-of-00002.safetensors`
- Source first shard:
  `90_legacy_imports/janus_old_train_2026-05-25/source_copy/model-00001-of-00002-008.safetensors`
- Local model store:
  `50_janus_data_library/06_models_and_checkpoints/legacy_janus_old_train/breeze_asr25_partial_encoder_exp11_0_checkpoint480_best/`
- Base model: `MediaTek-Research/Breeze-ASR-25`

## Selection Basis

The available partial-encoder trainer state selected checkpoint 480 as the
best checkpoint. Checkpoint 546 had the same recorded `best_metric` pointer but
its own last evaluation was worse.

| Checkpoint | eval CER norm | eval CER raw | eval WER | eval loss |
| --- | ---: | ---: | ---: | ---: |
| `checkpoint-480` | 0.15062168738957965 | 0.17507466182584763 | 0.20617297067573312 | 0.3664558231830597 |
| `checkpoint-546` last eval | 0.1589052968432281 | 0.18535164256016864 | 0.21581491712707182 | 0.367048054933548 |

The telephony partial-encoder export had model/config files but no comparable
`trainer_state.json`, so it was not selected over checkpoint 480.

## Shard Note

The legacy Google Drive export detached `model-00001-of-00002.safetensors`
files at the source root. The curated store reconstructs the selected
checkpoint with canonical shard names. Hash evidence for the selected copied
pair is local-only at
`90_legacy_imports/janus_old_train_2026-05-25/manifests/partial_encoder_shard_hashes.tsv`.

## Use In This Repo

Use this as the current best legacy ASR model candidate, then test whether its
lower CER also improves downstream decision stability.

## Next Step

Run a local model-load smoke test first. If the reconstructed shard pair loads
cleanly, evaluate the canonical `janus_165_v1` test split and compare both
CER/WER and CDS-ASR decision-stability metrics against the selected LoRA and
existing baselines.

## Smoke-Test Record

Planned one-row command:

```bash
.venv/bin/python 60_whisper_asr_finetuning/scripts/run_legacy_breeze_asr25_smoke.py \
  --model-kind partial_encoder \
  --run-id breeze_asr25_partial_encoder_legacy_best_smoke \
  --runtime cuda \
  --disable-cudnn \
  --max-samples 1
```

Expected local artifacts:

- `70_experiments/runs/breeze_asr25_partial_encoder_legacy_best_smoke/predictions/`
- `70_experiments/runs/breeze_asr25_partial_encoder_legacy_best_smoke/artifacts/`
- runtime log:
  `70_experiments/runs/breeze_asr25_partial_encoder_legacy_best_smoke/artifacts/breeze_asr25_partial_encoder_legacy_best_smoke_runtime_log.jsonl`

Result: passed on 2026-05-25.

- Runtime: CUDA, cuDNN disabled, `torch_dtype=float16`.
- Rows: 1.
- Audio ID: `janus_train_004201`.
- Output contract: `audio_id`, `hypothesis_text`, `wer`, `cer`, `asr_label`,
  `asr_run_id`, and `runtime` all present.
- Smoke CER: `20.0`.
- Smoke WER: `50.0`.
- ASR label: `critical_escalation`.
- Wall time: `7.03` seconds.
- Summary:
  `70_experiments/runs/breeze_asr25_partial_encoder_legacy_best_smoke/artifacts/breeze_asr25_partial_encoder_legacy_best_smoke_summary.json`
- Runtime log:
  `70_experiments/runs/breeze_asr25_partial_encoder_legacy_best_smoke/artifacts/breeze_asr25_partial_encoder_legacy_best_smoke_runtime_log.jsonl`
- Predictions:
  `70_experiments/runs/breeze_asr25_partial_encoder_legacy_best_smoke/predictions/breeze_asr25_partial_encoder_legacy_best_smoke_predictions.jsonl`

## 15-Row Pilot Record

Command:

```bash
.venv/bin/python 60_whisper_asr_finetuning/scripts/run_legacy_breeze_asr25_smoke.py \
  --model-kind partial_encoder \
  --run-id breeze_asr25_partial_encoder_legacy_best_15_row \
  --runtime cuda \
  --disable-cudnn \
  --max-samples 15
```

Validation:

```bash
.venv/bin/python 80_semantic_risk_asr/scoring/validate_janus_asr_hypotheses.py \
  --hypotheses 70_experiments/runs/breeze_asr25_partial_encoder_legacy_best_15_row/predictions/breeze_asr25_partial_encoder_legacy_best_15_row_predictions.jsonl \
  --require-labels \
  --require-quality-signal
```

Result: passed on 2026-05-25.

- Rows: 15.
- Validator: `ok=true`; no missing IDs, duplicate IDs, missing hypothesis text,
  missing ASR labels, or missing quality signals.
- Runtime: CUDA, cuDNN disabled, `torch_dtype=float16`.
- Mean CER: `12.77`.
- Mean WER: `83.33`.
- Wall time: `18.81` seconds.
- Summary:
  `70_experiments/runs/breeze_asr25_partial_encoder_legacy_best_15_row/artifacts/breeze_asr25_partial_encoder_legacy_best_15_row_summary.json`
- Validation:
  `70_experiments/runs/breeze_asr25_partial_encoder_legacy_best_15_row/artifacts/breeze_asr25_partial_encoder_legacy_best_15_row_validation.json`

# Postdoc Evidence-Chain Execution Log

Status: in_progress

Date: 2026-05-25

## Purpose

Track the step-by-step transition from completed legacy data/model organization
to a publishable CDS-ASR evidence chain. This record is repo-safe: raw audio,
full transcripts, model weights, predictions, and runtime JSONL logs stay in
ignored local paths.

## Logging Contract

- Every research operation gets a short note here with command intent, evidence,
  and result.
- Every model experiment writes ignored local runtime artifacts under its run
  folder: `artifacts/`, `predictions/`, and explicit JSON/JSONL summaries.
- Tracked files contain only aggregate metrics, commands, paths, and
  publication-safe observations.

## Operation Log

| Step | Operation | Evidence | Result |
| --- | --- | --- | --- |
| 0.1 | Inspected dirty worktree after legacy import. | `git status --short --branch`; `git diff --stat`; `git diff --check`. | Worktree contained only repo-safe migration docs/run records and `.gitignore` updates; diff check passed after removing trailing blank EOF lines. |
| 0.2 | Committed the migration checkpoint before smoke tests. | Commit `405328c docs: record legacy ASR model import`. | Research state is now reproducible; version hook advanced repo version to `v2.5.30`; branch is `main` ahead of `origin/main` by 1 commit. |
| 1.1 | Designed a legacy Breeze-ASR-25 smoke runner using the existing JANUS pilot contract. | `60_whisper_asr_finetuning/scripts/run_janus_whisper_family_pilot.py`; `70_experiments/runs/*legacy_best/README.md`. | New runner targets the curated LoRA adapter and partial-encoder model store without changing raw data or model artifacts. |
| 1.2 | Added runtime logging to the legacy smoke runner. | `60_whisper_asr_finetuning/scripts/run_legacy_breeze_asr25_smoke.py`. | Each smoke run will write `smoke_start`, `load_model_*`, `sample_*`, and `summary_written` events to ignored JSONL runtime logs. |
| 1.3 | Validated smoke runner CLI and local CUDA runtime before model load. | `.venv/bin/python -m py_compile ...`; `run_legacy_breeze_asr25_smoke.py --help`; `check_torch_cuda_asr_runtime.py`. | Script compiles and exposes expected arguments. CUDA is available on RTX 5080; cuDNN convolution still fails with `CUDNN_STATUS_SUBLIBRARY_VERSION_MISMATCH`, so smoke tests must use `--disable-cudnn`. |
| 1.4 | Ran one-row LoRA legacy-best smoke test. | `run_legacy_breeze_asr25_smoke.py --model-kind lora --run-id breeze_asr25_lora_legacy_best_smoke --runtime cuda --disable-cudnn --max-samples 1`; local summary/runtime log/prediction artifacts. | Passed. Loaded base `MediaTek-Research/Breeze-ASR-25` plus curated LoRA adapter, emitted one prediction for `janus_train_004201`, all required hypothesis fields were present, CER `25.0`, WER `100.0`, wall time `253.53` seconds. |
| 1.5 | Ran one-row partial-encoder legacy-best smoke test. | `run_legacy_breeze_asr25_smoke.py --model-kind partial_encoder --run-id breeze_asr25_partial_encoder_legacy_best_smoke --runtime cuda --disable-cudnn --max-samples 1`; local summary/runtime log/prediction artifacts. | Passed. Loaded reconstructed two-shard local model store, emitted one prediction for `janus_train_004201`, all required hypothesis fields were present, CER `20.0`, WER `50.0`, wall time `7.03` seconds. |
| 2.1 | Ran LoRA legacy-best fixed 15-row pilot and validator. | `run_legacy_breeze_asr25_smoke.py --model-kind lora --run-id breeze_asr25_lora_legacy_best_15_row --max-samples 15`; `validate_janus_asr_hypotheses.py --require-labels --require-quality-signal`. | Passed. 15 IDs matched the reviewed pilot set with no missing fields. Mean CER `30.99`, mean WER `100.00`, wall time `44.42` seconds. |
| 2.2 | Ran partial-encoder legacy-best fixed 15-row pilot and validator. | `run_legacy_breeze_asr25_smoke.py --model-kind partial_encoder --run-id breeze_asr25_partial_encoder_legacy_best_15_row --max-samples 15`; `validate_janus_asr_hypotheses.py --require-labels --require-quality-signal`. | Passed. 15 IDs matched the reviewed pilot set with no missing fields. Mean CER `12.77`, mean WER `83.33`, wall time `18.81` seconds. |
| 3.1 | Rebuilt CDS-ASR 15-row metric inputs with five model hypotheses. | `build_janus_pilot_metric_inputs.py` with Whisper small, Whisper large-v2, Breeze-ASR-25 base, legacy LoRA, and legacy partial encoder. | Passed. Output had 15 gold rows, 5 hypothesis files, 260 SRES rows, 260 CEIS rows, 75 downstream rows, and no unmatched hypotheses. |
| 3.2 | Ran SRES, CEIS, and downstream impact scoring for the five-model bridge. | `semantic_risk_score.py`; `counterfactual_escalation_instability.py`; `evaluate_downstream_impact.py`. | Completed. Partial encoder had best CER/WER and matched base Breeze decision-stability profile; LoRA improved CER over base but was worse on CEIS and high-risk-miss behavior. |
| 4.1 | Generalized ASR runner path handling for canonical test split manifests. | `run_janus_whisper_family_pilot.py`; `run_legacy_breeze_asr25_smoke.py`; `validate_janus_asr_hypotheses.py`. | Added support for `id`/`audio` manifest fields, relative audio paths, split names, and non-pilot expected-ID validation. Regression validation on existing 15-row partial predictions stayed `ok=true`. |
| 4.2 | Ran canonical 258-row test split with the legacy partial encoder. | `run_legacy_breeze_asr25_smoke.py --model-kind partial_encoder --run-id breeze_asr25_partial_encoder_legacy_best_test_split --manifest .../test.jsonl --max-samples 258`; local summary/runtime/prediction artifacts. | Passed. Rows `258`, CER `18.24`, WER `100.0`, wall time `213.79` seconds, `0.829` sec/row, `1.207` rows/sec, CUDA, cuDNN disabled, `torch_dtype=float16`. Validator: `ok=true`, no missing/duplicate IDs, no missing text/label/quality signal. |
| 4.3 | Ran canonical 258-row test split with the legacy LoRA. | `run_legacy_breeze_asr25_smoke.py --model-kind lora --run-id breeze_asr25_lora_legacy_best_test_split --manifest .../test.jsonl --max-samples 258`; local summary/runtime/prediction artifacts. | Passed. Rows `258`, CER `22.86`, WER `100.0`, wall time `403.37` seconds, `1.563` sec/row, `0.640` rows/sec, CUDA, cuDNN disabled, `torch_dtype=float16`. Validator: `ok=true`, no missing/duplicate IDs, no missing text/label/quality signal. |
| 4.4 | Produced tracked aggregate ASR/CDS proxy comparison for the 258-row split. | `summarize_janus_asr_test_split.py`; `70_experiments/runs/janus_258_test_split_asr_cds_proxy/`. | Completed. Partial encoder beat LoRA on CER, runtime, unsafe downrouting, high-risk misses, risk-atom error rate, negation flips, amount distortion, and action confusion. Both candidates had `simplified_char_count=0` and `locale_violation_rows=0`. |
| 4.5 | Added expanded ASR candidate matrix and locale contract. | `60_whisper_asr_finetuning/configs/janus-15-asr-model-candidates.yaml`; `docs/asr_candidate_expansion_2026_05_25.md`. | Added Whisper large-v3, Whisper large-v3 turbo, FunASR SenseVoice, Qwen3-ASR 0.6B/1.7B, and Gemma 4 E2B/E4B audio candidates. All new candidates are planned behind smoke, 15-row contract, runtime logging, and Taiwan Traditional Chinese locale gates. |
| 4.6 | Wrote the postdoc-level next-step roadmap after the 258-row gate. | `docs/postdoc_next_steps_2026_05_25.md`. | Completed. The roadmap defines the next ordered gates: comparable 258-row baselines, new runner smoke/15-row contracts, split-aware metric input builder, human risk-atom audit, 300-row high-stakes main experiment, recovery experiment, and paper packaging. |
| 5.1 | Added split-aware metric input builder. | `80_semantic_risk_asr/scoring/build_janus_metric_inputs.py`; `70_experiments/runs/janus_split_aware_metric_inputs_2026_05_25/README.md`. | Completed. Human-reviewed 15-row validation reproduced `260` SRES rows, `260` CEIS rows, `75` downstream rows, SRES total `8106.0`, CEIS mean `1.92`, downstream mismatch `0.3467`, and high-risk missed `4`. Proxy 258-row validation loaded `258/258` references and `516` hypotheses, producing `1057` SRES/CEIS rows and `516` downstream rows. |
| 5.2 | Audited WER calculation for publication readiness. | `asr_text_metrics.py`; `audit_asr_text_metrics.py`; `wer_metric_audit_2026_05_25/text_metric_audit.tsv`. | Completed. Found two incompatible WER definitions: current inference used raw whitespace WER, while legacy training used normalized `jieba` WER. Future runners now default to `zh_asr` normalization plus `jieba` WER, preserve legacy raw whitespace WER as an audit field, and keep Traditional Chinese without simplified conversion. |

## Next Operations

1. Treat pre-audit `wer` values as legacy compatibility fields. For paper-facing
   tables, use `cer_zh_normalized` corpus-level micro rate as the primary ASR
   surface metric and `wer_zh_jieba` only as a supplemental metric.
2. Complete comparable 258-row baselines for the already-gated ASR models:
   Whisper small, Whisper large-v2, Breeze-ASR-25 base, optional Breeze-ASR-26,
   legacy LoRA, and legacy partial encoder.
3. Run Whisper large-v3 and Whisper large-v3 turbo through smoke, 15-row
   contract, locale gate, and then 258-row if they pass.
4. Build smoke/15-row runners for FunASR SenseVoice and Qwen3-ASR, with strict
   Taiwan Traditional Chinese locale gates.
5. Build a separate multimodal prompted-ASR runner for Gemma 4 E2B/E4B only
   after the prompt, audio-length, hallucination, runtime, and locale logging
   contract is explicit.
6. Use `build_janus_metric_inputs.py` to regenerate metric inputs for the
   expanded 258-row baseline set.
7. Create a small human-reviewed risk-atom audit set so proxy metrics do not
   become overstated as formal CDS evidence.
8. Run the selected 300-row high-stakes experiment only after the expanded
   258-row baseline set and audit boundary are clear.

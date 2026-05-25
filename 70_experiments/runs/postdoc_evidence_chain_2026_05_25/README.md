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
| 4.4 | Produced tracked aggregate ASR/CDS proxy comparison for the 258-row split. | `summarize_janus_asr_test_split.py`; `70_experiments/runs/janus_258_test_split_asr_cds_proxy/`. | Completed. Partial encoder beat LoRA and Breeze-ASR-25 base on paper-facing zh CER micro, unsafe downrouting, high-risk misses, risk-atom error rate, and locale behavior. All three candidates had `simplified_char_count=0` and `locale_violation_rows=0`. |
| 4.5 | Added expanded ASR candidate matrix and locale contract. | `60_whisper_asr_finetuning/configs/janus-15-asr-model-candidates.yaml`; `docs/asr_candidate_expansion_2026_05_25.md`. | Added Whisper large-v3, Whisper large-v3 turbo, FunASR SenseVoice, Qwen3-ASR 0.6B/1.7B, and Gemma 4 E2B/E4B audio candidates. All new candidates are planned behind smoke, 15-row contract, runtime logging, and Taiwan Traditional Chinese locale gates. |
| 4.6 | Wrote the postdoc-level next-step roadmap after the 258-row gate. | `docs/postdoc_next_steps_2026_05_25.md`. | Completed. The roadmap defines the next ordered gates: comparable 258-row baselines, new runner smoke/15-row contracts, split-aware metric input builder, human risk-atom audit, 300-row high-stakes main experiment, recovery experiment, and paper packaging. |
| 5.1 | Added split-aware metric input builder. | `80_semantic_risk_asr/scoring/build_janus_metric_inputs.py`; `70_experiments/runs/janus_split_aware_metric_inputs_2026_05_25/README.md`. | Completed. Human-reviewed 15-row validation reproduced `260` SRES rows, `260` CEIS rows, `75` downstream rows, SRES total `8106.0`, CEIS mean `1.92`, downstream mismatch `0.3467`, and high-risk missed `4`. Proxy 258-row validation loaded `258/258` references and `516` hypotheses, producing `1057` SRES/CEIS rows and `516` downstream rows. |
| 5.2 | Audited WER calculation for publication readiness. | `asr_text_metrics.py`; `audit_asr_text_metrics.py`; `wer_metric_audit_2026_05_25/text_metric_audit.tsv`. | Completed. Found two incompatible WER definitions: earliest inference used raw whitespace WER, while legacy training used normalized `jieba` WER. Future runners now default to `zh_asr` normalization plus `jieba` WER, preserve legacy raw whitespace WER as an audit field, and keep Traditional Chinese without simplified conversion. |
| 5.3 | Promoted paper-facing zh ASR metrics into the 258-row aggregate summarizer. | `summarize_janus_asr_test_split.py`; `janus_258_test_split_asr_cds_proxy/asr_cds_proxy_comparison.tsv`. | Completed. The aggregate table now carries `cer_zh_micro` as the primary surface metric, `wer_zh_jieba_micro` as supplemental, and legacy stored `cer_mean`/`wer_mean` only for reproducibility. |
| 5.4 | Generalized hypothesis validation beyond the fixed 15-row gate. | `validate_janus_asr_hypotheses.py --expected-manifest ... --expected-rows 258`. | Completed. The validator can now read expected IDs from a split manifest for 258-row and future split-level runs while preserving the original gold+nemo 15-row gate behavior. |
| 5.5 | Ran canonical 258-row Whisper small and Whisper large-v2 comparators. | `run_janus_whisper_family_pilot.py --run-id whisper_small_test_split`; `run_janus_whisper_family_pilot.py --run-id whisper_large_v2_test_split`; local ignored predictions/validation artifacts. | Completed. Whisper small: `cer_zh_micro=34.86`, `wer_zh_jieba_micro=43.44`, wall time `152.92s`, unsafe downrouting `76`, high-risk missed `70`, locale violation rows `4`. Whisper large-v2: `cer_zh_micro=24.72`, `wer_zh_jieba_micro=32.23`, wall time `523.49s`, unsafe downrouting `33`, high-risk missed `28`, locale violation rows `1`. |
| 5.6 | Rebuilt the 258-row proxy bridge over five model hypotheses. | `summarize_janus_asr_test_split.py`; `build_janus_metric_inputs.py`; `semantic_risk_score.py`; `counterfactual_escalation_instability.py`; `evaluate_downstream_impact.py`. | Completed. Five-model aggregate: SRES rows `2648`, CEIS rows `2648`, downstream rows `1290`, SRES total `24120.0`, CEIS unstable samples `164`, CEIS mean `1.184`, downstream mismatch `0.1287`, high-risk missed by ASR `139`. Partial encoder remains the best current ASR hypothesis generator. |
| 5.7 | Ran canonical 258-row Breeze-ASR-26 comparator. | `run_janus_whisper_family_pilot.py --run-id breeze_asr26_test_split --model-name MediaTek-Research/Breeze-ASR-26 --metric-normalization zh_asr --wer-tokenizer jieba`; local ignored predictions/validation artifacts. | Completed. `258/258` IDs validated. Stored CER `24.87`, stored WER `33.12`, `cer_zh_micro=24.27`, `wer_zh_jieba_micro=32.29`, wall time `187.25s`, unsafe downrouting `27`, high-risk missed `22`, locale violation rows `0`. Raw whitespace WER micro was `1054.79`, confirming it is audit-only for unsegmented Chinese. |
| 5.8 | Rebuilt WER audit and 258-row proxy bridge over six model hypotheses. | `audit_asr_text_metrics.py --expected-manifest ... --expected-rows 258`; `summarize_janus_asr_test_split.py`; `build_janus_metric_inputs.py`; SRES/CEIS/downstream scorers. | Completed. WER audit: all six runs have `0` missing references, `0` missing hypotheses, `0` missing expected IDs, `0` extra IDs, and `0` reference mismatches; zh-jieba corpus WER matched `jiwer` exactly. Six-model bridge: SRES rows `3184`, CEIS rows `3184`, downstream rows `1548`, SRES total `27810.0`, CEIS unstable samples `192`, CEIS mean `1.1461`, downstream mismatch `0.126`, high-risk missed by ASR `161`. |
| 5.9 | Added and ran the first automatic recovery policy gate. | `evaluate_recovery_policies.py`; `70_experiments/runs/janus_258_recovery_policy_proxy_2026_05_25/`; local ignored per-sample policy detail. | Completed. Five conditions compared over `1548` proxy model-samples. No recovery: unsafe downrouting `187`, high-risk missed `161`, critical miss `9`. Confidence-only had no calibrated confidence values and stayed no-trigger. CEIS conservative action reduced unsafe downrouting to `75` and high-risk misses to `41` with budget `0.0969`; CEIS+ensemble reduced them to `46` and `12` with abstention burden `468`. |
| 5.10 | Completed Breeze-family 300-row high-stakes ASR comparator passes. | `breeze_asr25_partial_encoder_high_stakes_300`; `breeze_asr25_base_high_stakes_300`; `breeze_asr25_lora_high_stakes_300`; local ignored predictions/runtime artifacts. | Completed. All three runs passed `300/300` manifest validation with quality fields. Paper-facing micro metrics: partial encoder `cer_zh_micro=6.86`, `wer_zh_jieba_micro=9.38`, wall time `275.74s`; LoRA `15.97`, `21.91`, `481.25s`; base `21.44`, `28.10`, `214.96s`. |
| 5.11 | Re-ran WER audit over the three high-stakes 300-row hypotheses. | `70_experiments/runs/wer_metric_audit_2026_05_25/high_stakes_300_metric_audit.tsv`; `high_stakes_300_summary.json`. | Completed. All three runs had `0` missing references, `0` missing hypotheses, `0` missing expected IDs, `0` extra IDs, `0` reference mismatches, and `0.0` zh-jieba `jiwer` delta. Raw whitespace WER remained audit-only: partial encoder `93.16`, LoRA `101.30`, base `271.66`. |

## Next Operations

1. Treat pre-audit `wer` values as legacy compatibility fields. For paper-facing
   tables, use `cer_zh_micro` as the primary ASR surface metric and
   `wer_zh_jieba_micro` only as supplemental.
2. Run Whisper large-v3 and Whisper large-v3 turbo through smoke, 15-row
   contract, locale gate, and then 258-row if they pass.
3. Build smoke/15-row runners for FunASR SenseVoice and Qwen3-ASR, with strict
   Taiwan Traditional Chinese locale gates.
4. Build a separate multimodal prompted-ASR runner for Gemma 4 E2B/E4B only
   after the prompt, audio-length, hallucination, runtime, and locale logging
   contract is explicit.
5. Use `build_janus_metric_inputs.py` to regenerate metric inputs for each
   expanded 258-row baseline set.
6. Create a small human-reviewed risk-atom audit set so proxy metrics do not
   become overstated as formal CDS evidence.
7. Build the 300-row high-stakes CDS-ASR metric inputs from the completed
   partial-encoder, LoRA, and base hypotheses, then rerun SRES, CEIS,
   downstream impact, and recovery policy comparison.

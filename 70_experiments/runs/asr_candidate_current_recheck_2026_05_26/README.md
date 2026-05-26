# ASR Candidate Current Recheck

Date: 2026-05-26

## FIRST PRINCIPLE

The useful test is not whether a new model name exists. A candidate should move
to 258-row or selected-300 runtime only if it can pass the same JANUS field
contract, timing record, metric policy, and strict Taiwan Traditional Chinese
locale gate used by the current evidence chain.

## Scope

This recheck answers the user question about whether the remaining ASR and
multimodal Gemma 4 candidates should now be tested. It revalidated the existing
fixed 15-row candidates and reran bounded runtime probes for the blocked lanes:

- `openai/whisper-large-v3`
- `openai/whisper-large-v3-turbo`
- `FunAudioLLM/SenseVoiceSmall`
- `Qwen/Qwen3-ASR-0.6B`
- `Qwen/Qwen3-ASR-1.7B`
- `unsloth/gemma-4-E2B`
- `unsloth/gemma-4-E4B`

## Commands

```bash
/usr/bin/time -f 'elapsed_seconds=%e max_rss_kb=%M exit_status=%x' \
  .venv/bin/python 80_semantic_risk_asr/scoring/validate_janus_asr_hypotheses.py \
  --hypotheses 70_experiments/runs/whisper_large_v3_15_row_baseline/predictions/whisper_large_v3_15_row_baseline_predictions.jsonl \
  --hypotheses 70_experiments/runs/whisper_large_v3_turbo_15_row_baseline/predictions/whisper_large_v3_turbo_15_row_baseline_predictions.jsonl \
  --hypotheses 70_experiments/runs/sensevoice_small_15_row_candidate/predictions/sensevoice_small_15_row_candidate_predictions.jsonl \
  --hypotheses 70_experiments/runs/qwen3_asr_0_6b_15_row_candidate/predictions/qwen3_asr_0_6b_15_row_candidate_predictions.jsonl \
  --require-labels \
  --require-quality-signal \
  --expected-rows 15 \
  --output-json 70_experiments/runs/asr_candidate_current_recheck_2026_05_26/artifacts/15_row_contract_validation_2026_05_26.json

/usr/bin/time -f 'elapsed_seconds=%e max_rss_kb=%M exit_status=%x' \
  .venv/bin/python 80_semantic_risk_asr/scoring/summarize_janus_asr_test_split.py \
  --manifest 40_breeze_asr25_finetune_dataset/manifests/nemo_pilot_input_manifest.jsonl \
  --hypotheses 70_experiments/runs/whisper_large_v3_15_row_baseline/predictions/whisper_large_v3_15_row_baseline_predictions.jsonl \
  --hypotheses 70_experiments/runs/whisper_large_v3_turbo_15_row_baseline/predictions/whisper_large_v3_turbo_15_row_baseline_predictions.jsonl \
  --hypotheses 70_experiments/runs/sensevoice_small_15_row_candidate/predictions/sensevoice_small_15_row_candidate_predictions.jsonl \
  --hypotheses 70_experiments/runs/qwen3_asr_0_6b_15_row_candidate/predictions/qwen3_asr_0_6b_15_row_candidate_predictions.jsonl \
  --output-tsv 70_experiments/runs/asr_candidate_current_recheck_2026_05_26/candidate_current_recheck_summary.tsv \
  --summary-json 70_experiments/runs/asr_candidate_current_recheck_2026_05_26/summary.json

/usr/bin/time -f 'elapsed_seconds=%e max_rss_kb=%M exit_status=%x' \
  timeout 60 \
  .venv/bin/python 60_whisper_asr_finetuning/scripts/run_janus_qwen3_asr_pilot.py \
  --run-id qwen3_asr_1_7b_current_recheck_1_row \
  --model-name Qwen/Qwen3-ASR-1.7B \
  --runtime cuda \
  --device-map cuda:0 \
  --torch-dtype bfloat16 \
  --language Chinese \
  --max-samples 1 \
  --max-new-tokens 256 \
  --max-inference-batch-size 1 \
  --disable-cudnn \
  --metric-normalization zh_asr \
  --wer-tokenizer jieba

/usr/bin/time -f 'elapsed_seconds=%e max_rss_kb=%M exit_status=%x' \
  .venv/bin/python -c 'import json, transformers; result={"transformers": transformers.__version__, "has_AutoModelForMultimodalLM": hasattr(transformers, "AutoModelForMultimodalLM"), "has_Gemma4ForConditionalGeneration": hasattr(transformers, "Gemma4ForConditionalGeneration")}; print(json.dumps(result, ensure_ascii=False, indent=2))'
```

## Results

| Candidate | Gate | Result | Evidence |
| --- | --- | --- | --- |
| Whisper large-v3 | 15-row contract and locale summary | contract valid; locale not clean | `candidate_current_recheck_summary.tsv` |
| Whisper large-v3 turbo | 15-row contract and locale summary | contract valid; locale not clean | `candidate_current_recheck_summary.tsv` |
| SenseVoiceSmall | 15-row contract and locale summary | contract valid; locale failed | `candidate_current_recheck_summary.tsv` |
| Qwen3-ASR-0.6B | 15-row contract and locale summary | contract valid; locale failed | `candidate_current_recheck_summary.tsv` |
| Qwen3-ASR-1.7B | 60-second 1-row load gate | timeout before inference at fetch/load | terminal timing: `60.08s`, exit `124` |
| Gemma 4 E2B/E4B | local multimodal class gate | blocked before inference | `transformers 4.57.6` lacks `AutoModelForMultimodalLM` and `Gemma4ForConditionalGeneration` |

The four available 15-row hypothesis files all matched the fixed pilot manifest:
`15/15` rows, no missing expected IDs, no extra IDs, no missing references, and
no reference mismatches. The aggregate recheck command finished in `0.36s`;
the field-contract validator finished in `0.02s`. The Gemma runtime class probe
finished in `1.30s`.

## 2026-05-26 03:43 CST Follow-Up

The same bounded decision gate was rerun after the user again asked whether to
test the remaining ASR and multimodal Gemma 4 models now.

Additional live checks:

- Hugging Face metadata still reports all seven requested model pages as public
  and ungated. Current SHA prefixes are `06f233fe06e7`, `41f01f3fe87f`,
  `716d31dbfd64`, `5eb144179a02`, `7278e1e70fe2`, `ed37665cc131`, and
  `5bf6a20911f0`.
- The four existing 15-row hypothesis files still pass the fixed field-contract
  validator in `0.02s`.
- The aggregate locale/metric summary rebuild finishes in `0.38s` and still
  shows the same locale blockers.
- Qwen3-ASR-1.7B still times out before inference after `60.07s` at fetch/load
  with exit status `124`.
- Local `transformers 4.57.6` still lacks `AutoModelForMultimodalLM` and
  `Gemma4ForConditionalGeneration`; a config probe also fails because this
  runtime does not recognize `model_type=gemma4`.

This follow-up used `/tmp` output paths for transient validation artifacts.
Tracked conclusions remain aggregate-only; raw predictions, runtime logs, and
model caches remain ignored/local.

## 2026-05-26 05:19 CST Live Recheck

The same bounded gate was rerun before deciding whether to spend full-split
runtime on the remaining ASR and multimodal Gemma 4 candidates.

Additional live checks:

- Hugging Face metadata still reports all seven requested model pages as public
  and ungated. Current SHA prefixes are `06f233fe06e7`, `41f01f3fe87f`,
  `716d31dbfd64`, `5eb144179a02`, `7278e1e70fe2`, `ed37665cc131`, and
  `5bf6a20911f0`.
- The four existing 15-row hypothesis files still pass the fixed field-contract
  validator in `0.02s`.
- The aggregate locale/metric summary rebuild finishes in `0.39s` and still
  shows the same locale blockers: Whisper large-v3 has `2/15` locale-violation
  rows, Whisper large-v3 turbo has `4/15`, SenseVoiceSmall has `14/15`, and
  Qwen3-ASR-0.6B has `15/15`.
- Qwen3-ASR-1.7B still times out before inference after `60.07s` at fetch/load
  with exit status `124`.
- Local `transformers 4.57.6` still lacks `AutoModelForMultimodalLM` and
  `Gemma4ForConditionalGeneration`; a config probe for both Gemma 4 checkpoints
  still fails because this runtime does not recognize `model_type=gemma4`.

This follow-up also used `/tmp` output paths for transient validation artifacts.
Tracked conclusions remain aggregate-only.

## 2026-05-26 06:45 CST Response-Time Validation

After the renewed question about whether to test the remaining ASR and
multimodal Gemma 4 models now, the tracked 15-row files were revalidated without
starting a new full inference run.

Additional bounded checks:

- The four existing 15-row hypothesis files still pass the fixed field-contract
  validator: `ok=true`, `15/15` rows each, no missing expected IDs, no extra
  IDs, no duplicate IDs, no missing references, and no reference mismatches.
- The aggregate summary rebuilt to `/tmp` and still shows the same locale
  blockers: Whisper large-v3 has `2/15` locale-violation rows, Whisper
  large-v3 turbo has `4/15`, SenseVoiceSmall has `14/15`, and Qwen3-ASR-0.6B
  has `15/15`.
- Local `transformers 4.57.6` still exposes no `AutoModelForMultimodalLM` and
  no `Gemma4ForConditionalGeneration`.
- Qwen3-ASR-1.7B was not rerun in this response-time check because the current
  tracked gate already has repeated bounded `60.07s` fetch/load timeouts, and
  Qwen3-ASR-0.6B still fails strict Taiwan Traditional Chinese locale control.

This validation again used `/tmp` output paths for transient artifacts:
`/tmp/cib_asr_candidate_contract_validation_now.json`,
`/tmp/cib_asr_candidate_recheck_summary_now.tsv`, and
`/tmp/cib_asr_candidate_recheck_summary_now.json`.

## 2026-05-26 07:24 CST Bounded Recheck

After the user again asked whether the remaining ASR and multimodal Gemma 4
models should be tested, the bounded gate was rerun instead of starting an
uncontrolled full-split inference pass.

Additional bounded checks:

- Hugging Face metadata still reports all seven requested model pages as public
  and ungated. SHA prefixes remain `06f233fe06e7`, `41f01f3fe87f`,
  `716d31dbfd64`, `5eb144179a02`, `7278e1e70fe2`, `ed37665cc131`, and
  `5bf6a20911f0`.
- The four existing 15-row hypothesis files still pass the fixed field-contract
  validator in `0.03s`.
- The aggregate summary rebuilt to `/tmp` in `0.38s` and still shows the same
  locale blockers: Whisper large-v3 has `2/15` locale-violation rows, Whisper
  large-v3 turbo has `4/15`, SenseVoiceSmall has `14/15`, and Qwen3-ASR-0.6B
  has `15/15`.
- Local `transformers 4.57.6` still exposes no `AutoModelForMultimodalLM` and
  no `Gemma4ForConditionalGeneration`; the class probe finished in `1.31s`.
- Qwen3-ASR-1.7B was not rerun in this response-time check because repeated
  tracked bounded gates already timed out at fetch/load, and Qwen3-ASR-0.6B
  still fails strict Taiwan Traditional Chinese locale control.

This validation used `/tmp` output paths for transient artifacts:
`/tmp/cib_asr_candidate_contract_validation_2026_05_26_0724.json`,
`/tmp/cib_asr_candidate_recheck_summary_2026_05_26_0724.tsv`, and
`/tmp/cib_asr_candidate_recheck_summary_2026_05_26_0724.json`.

## 2026-05-26 07:45 CST Response-Time Verification

After the same model-test question was raised again, the safe bounded gate was
rerun without starting a new full inference pass.

Additional bounded checks:

- The four existing 15-row hypothesis files still pass the fixed field-contract
  validator.
- The aggregate summary rebuilt to `/tmp` and still shows the same locale
  blockers: Whisper large-v3 has `2/15` locale-violation rows, Whisper
  large-v3 turbo has `4/15`, SenseVoiceSmall has `14/15`, and Qwen3-ASR-0.6B
  has `15/15`.
- Hugging Face metadata still reports all seven requested model pages as public
  and ungated. SHA prefixes remain `06f233fe06e7`, `41f01f3fe87f`,
  `716d31dbfd64`, `5eb144179a02`, `7278e1e70fe2`, `ed37665cc131`, and
  `5bf6a20911f0`.
- Local `transformers 4.57.6` still exposes no `AutoModelForMultimodalLM` and
  no `Gemma4ForConditionalGeneration`.
- Qwen3-ASR-1.7B was not rerun because repeated tracked bounded gates already
  timed out at fetch/load, and Qwen3-ASR-0.6B still fails strict Taiwan
  Traditional Chinese locale control.

This validation used `/tmp` output paths for transient artifacts:
`/tmp/cib_asr_candidate_contract_validation_latest.json`,
`/tmp/cib_asr_candidate_recheck_summary_latest.tsv`, and
`/tmp/cib_asr_candidate_recheck_summary_latest.json`.

## 2026-05-26 08:25 CST Bounded Verification

After the user again asked whether the remaining ASR and multimodal Gemma 4
models should be tested now, the safe gate was rerun before any full-split
promotion.

Additional bounded checks:

- The four existing 15-row hypothesis files still pass the fixed field-contract
  validator in `0.02s`.
- The aggregate summary rebuilt to `/tmp` in `0.39s` and still shows the same
  locale blockers: Whisper large-v3 has `2/15` locale-violation rows, Whisper
  large-v3 turbo has `4/15`, SenseVoiceSmall has `14/15`, and Qwen3-ASR-0.6B
  has `15/15`.
- Hugging Face metadata still reports all seven requested model pages as public
  and ungated. SHA prefixes remain `06f233fe06e7`, `41f01f3fe87f`,
  `716d31dbfd64`, `5eb144179a02`, `7278e1e70fe2`, `ed37665cc131`, and
  `5bf6a20911f0`.
- Qwen3-ASR-1.7B was rerun as a bounded 60-second load gate and still timed out
  before inference at `60.07s`, exit status `124`, while still at
  `Fetching 2 files: 0/2`.
- Local `transformers 4.57.6` still exposes no `AutoModelForMultimodalLM` and
  no `Gemma4ForConditionalGeneration`; both Gemma 4 config probes still fail
  because this runtime does not recognize `model_type=gemma4`.

This validation used `/tmp` output paths for transient aggregate artifacts and
ignored local logs under this run directory. No new prediction file was created
for Qwen3-ASR-1.7B, and no transcript-bearing artifact is tracked.

## Decision

Do not run these candidates on the 258-row test split or selected-300 main
experiment right now. Whisper large-v3 and large-v3-turbo are already measured
at 15 rows but are not clean under the strict Taiwan Traditional Chinese locale
gate. SenseVoiceSmall and Qwen3-ASR-0.6B also pass the field contract but fail
locale. Qwen3-ASR-1.7B still cannot reach inference under a bounded gate.
Gemma 4 E2B/E4B need an isolated official multimodal/audio runtime before any
prompted-ASR test can be compared with pure-ASR baselines.

The next model-side step is one of:

1. reject these candidates from the pure-ASR paper table;
2. approve and audit a post-decode Traditional Chinese conversion/reporting
   policy;
3. build an isolated Gemma 4 multimodal runner that can log prompt, audio
   length, hallucination/repetition checks, timing, and locale violations.

Until one of those changes happens, the main repo objective remains the
selected-300 human risk/decision/model/timing review and post-review refresh.

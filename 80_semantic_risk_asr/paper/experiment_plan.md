# Experiment Plan

Canonical detailed design:

- `q1_paper_design.md`
- `../../docs/postdoc_next_steps_2026_05_25.md` for the current postdoc-level
  sequence after the 258-row gate.

## FIRST PRINCIPLE Gate

The first publishable unit is not another long fine-tune. It is a small,
auditable decision-stability sample that tests whether plausible ASR
alternatives change downstream escalation decisions.

Do not start a long model run until this gate exists:

1. Complete the reviewed 15-row JANUS pilot gate. Done locally on 2026-05-25.
2. Generate baseline ASR hypotheses, confidence signals, timestamps, and
   ordinary WER/CER.
   NeMo Curator produced a 15-row CPU pilot output with joinable `audio_id`,
   WER, and CER fields on 2026-05-25; it is an output-contract check, not a
   quality baseline. Whisper small also passed a 1-row CPU smoke test for
   loading, preprocessing, generation, and aggregate metric logging. The full
   15-row Whisper-small hypothesis pass also completed on 2026-05-25 using
   CUDA with cuDNN disabled; it passed the hypothesis validator with WER/CER and
   heuristic ASR labels. The first 15-row model comparison now includes NeMo
   Curator, Whisper-small, Whisper-large-v2, Breeze-ASR-25, and optional
   Breeze-ASR-26 stress test.
3. Build metric inputs with
   `80_semantic_risk_asr/scoring/build_janus_pilot_metric_inputs.py`.
4. Extract risk atoms from top-1 transcripts and reference transcripts.
5. Generate plausible ASR counterfactual variants.
6. Compute SRES as the semantic-risk baseline.
7. Compute CEIS as the proposed decision-stability metric.
8. Run the downstream escalation impact check.
   First three-model pass: SRES rows `156`, total SRES `4868.0`, CEIS unstable
   model-samples `17 / 45`, max CEIS `15.0`, downstream ASR mismatch rate
   `0.3778`, and high-risk missed by ASR `3`.
   Legacy best-model extension on 2026-05-25: the fixed 15-row bridge now also
   includes `breeze_asr25_lora_legacy_best_15_row` and
   `breeze_asr25_partial_encoder_legacy_best_15_row`. The five-model pass
   produced SRES rows `260`, CEIS rows `260`, downstream rows `75`, CEIS
   unstable model-samples `26 / 75`, max CEIS `15.0`, downstream ASR mismatch
   rate `0.3467`, and high-risk missed by ASR `4`.
9. Expand to `300-500` high-stakes call segments only if the 15-row pilot
   produces usable decision-stability signal.
   Current local status: selected `300` expansion candidates from `2704`
   eligible risk/scenario rows with train/validation/test split `240/30/30`.
   Candidate IDs remain local under ignored artifacts.
10. Store only reviewed aggregate outputs and small safe samples in git.

Publication-safe output path:

- put scored summaries and aggregate metrics under `70_experiments/`;
- keep raw audio, full transcripts, checkpoints, bulk predictions, and large
  generated files local unless a separate controlled-data or Git LFS decision
  is made.

## Experiment 1: ASR Baseline And Risk-Atom Error Profile

Models:

- `openai/whisper-small`
- `openai/whisper-large-v2`
- `openai/whisper-large-v3`
- `openai/whisper-large-v3-turbo`
- `MediaTek-Research/Breeze-ASR-25`
- optional `MediaTek-Research/Breeze-ASR-26` as a Taigi/Taiwanese Hokkien
  stress test, not as the primary Taiwan Mandarin baseline. Local 15-row status
  on 2026-05-25: completed, CER `38.49`, WER `1493.33`, CUDA with cuDNN
  disabled.
- `FunAudioLLM/SenseVoiceSmall` after a FunASR runner emits the standard
  hypothesis contract.
- `Qwen/Qwen3-ASR-0.6B` first, then `Qwen/Qwen3-ASR-1.7B` only if the smaller
  model passes the 15-row smoke/contract gate.
- `unsloth/gemma-4-E2B` and `unsloth/gemma-4-E4B` as prompted multimodal audio
  candidates, not as pure ASR baselines, after a separate prompt/locale/runtime
  runner exists.

Language and script rule:

- Target locale is `zh-TW`.
- Output must be Taiwan Traditional Chinese transcription only.
- Do not accept Simplified Chinese output as a passing result.
- Record simplified character count, simplified character rate, and locale
  violation rows for every model.
- Whisper-family models may use `language=zh` because there is no `zh-TW`
  token, but they still require the Traditional Chinese locale gate.

Metrics:

- CER;
- WER;
- risk atom error rate;
- negation flip rate;
- amount distortion rate;
- action confusion rate.
- unsafe downrouting count;
- high-risk missed count;
- over-escalation count;
- wall time seconds;
- seconds per row;
- rows per second;
- locale violations.

Purpose:

Establish ordinary ASR performance on `janus_165_v1`, then show that ordinary
metrics do not explain which models are stable on risk atoms.

Current 15-row signal: the legacy partial encoder is the strongest transcript
candidate on legacy stored CER/WER (`12.77` CER, `83.33` WER) and matches base
Breeze-ASR-25 on mean CEIS, unstable-sample count, downstream mismatch, and
high-risk misses.
The legacy LoRA improves CER over base Breeze-ASR-25 (`30.99` vs `36.13`) but
is worse on CEIS and downstream safety counts. Treat this as early evidence
that lower CER alone is not sufficient for the paper claim.

Current 258-row test-split signal: partial encoder remains stronger than LoRA,
Breeze-ASR-25 base, Whisper large-v2, and Whisper small. Partial encoder
produced `cer_zh_micro=15.04` in `213.79` seconds (`0.829` sec/row), with
unsafe downrouting `7`, high-risk misses `4`, risk-atom proxy error rate
`0.0431`, and locale violations `0`.
LoRA produced `cer_zh_micro=18.23` in `403.37` seconds (`1.563` sec/row), with
unsafe downrouting `10`, high-risk misses `7`, risk-atom proxy error rate
`0.0613`, and locale violations `0`. Breeze-ASR-25 base produced
`cer_zh_micro=22.72`, unsafe downrouting `34`, high-risk misses `30`, and
locale violations `0`. Whisper large-v2 produced `cer_zh_micro=24.72`,
unsafe downrouting `33`, high-risk misses `28`, and `1` locale-violation row.
Whisper small produced `cer_zh_micro=34.86`, unsafe downrouting `76`,
high-risk misses `70`, and `4` locale-violation rows.

The five-model split-aware proxy bridge produced `2648` SRES rows, `2648`
CEIS variant rows, and `1290` downstream rows. Aggregate SRES total was
`24120.0`; CEIS unstable samples were `164`; downstream ASR mismatch rate was
`0.1287`; high-risk missed by ASR was `139`.

Decision: promote the legacy partial encoder as the current ASR hypothesis
generator for the next split-aware CDS metric builder. Keep LoRA as contrast
evidence, not the next primary hypothesis generator. Treat pre-audit `wer`
values as legacy raw whitespace fields. Paper-facing ASR tables should use the
aggregate `cer_zh_micro` column as the primary surface metric and
`wer_zh_jieba_micro` only as a supplemental segmented word metric.

Current execution priority after the 258-row gate:

1. Complete remaining comparable 258-row baselines for optional Breeze-ASR-26,
   Whisper large-v3, and Whisper large-v3 turbo under the `zh_asr` metric
   profile.
2. Build new SenseVoice and Qwen3-ASR runners only through smoke and 15-row
   contract before full split runs.
3. Keep Gemma 4 E2B/E4B as a separate prompted multimodal ASR lane, not as a
   pure ASR baseline.
4. Use the split-aware `build_janus_metric_inputs.py` so 15-row, 258-row, and
   300-row experiments share the same metric-input contract. Current local
   validation: the script reproduces the 15-row human-reviewed legacy bridge
   counts and can process the five-model 258-row proxy comparison.
5. Run the selected 300-row high-stakes expansion as the main experiment only
   after the split-aware builder is validated.

## Experiment 2: Counterfactual Generation Quality

Sample:

- first the reviewed 15-row gate;
- then the selected `300` high-stakes call segments from train/validation/test
  after the pilot shows a usable signal.

Signals:

- ASR confidence / token log probability if available;
- n-best hypotheses if available;
- timestamp-aligned unstable spans;
- Mandarin phonetic confusion sets;
- fraud-domain slot ontology for amount, action, actor, time, intent, and scam
  pattern.

Metrics:

- counterfactual coverage;
- risk atom coverage;
- plausible variant recall against reference-risk differences;
- acoustic plausibility distribution.

Purpose:

Show that the generated alternatives are not arbitrary paraphrases. They are
plausible ASR variants concentrated around decision-critical atoms.

## Experiment 3: WER/CER/Semantic Metrics/SRES/CEIS Comparison

Prediction target:

```text
downstream label changed = yes/no
```

Comparisons:

- WER thresholding with declared tokenizer/normalization only;
- CER thresholding, preferably the aggregate `cer_zh_micro` rate;
- semantic distance or ASD if implemented;
- ASR confidence;
- SRES;
- CEIS.

Outcome:

- AUC;
- F1;
- Recall@HighRisk;
- Precision@RecoveryBudget;
- Critical Miss Rate;
- False Safe Rate;
- examples where WER is low but CEIS is high;
- examples where semantic distance is low but CEIS is high;
- examples where confidence is high but CEIS is high.

Expected contribution:

Show that CEIS is better aligned with decision instability than transcript
similarity alone.

## Experiment 4: Automatic Recovery

Conditions:

1. No recovery.
2. Confidence-only LLM correction.
3. SRES-triggered recovery.
4. CDS-ASR constrained re-decoding.
5. CDS-ASR constrained re-decoding plus decision interval estimation.

Automatic CDS-ASR recovery path:

```text
high-CEIS span
-> span-level forced alignment
-> constrained re-decoding over risk-atom grammar
-> ASR ensemble arbitration
-> decision interval estimation
-> conservative automatic action
```

Metrics:

- Critical Miss Rate;
- Unsafe Down-Routing Rate;
- Over-Escalation Rate;
- Automatic Recovery Budget;
- Machine Abstention Rate;
- Conservative Escalation Cost;
- Decision Stability Gain;
- compute cost.

Expected contribution:

Show that counterfactual decision testing plus constrained acoustic recovery can
reduce unsafe low-risk decisions without using human review as the proposed
method.

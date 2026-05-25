# Experiment Plan

Canonical detailed design:

- `q1_paper_design.md`

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
   loading, preprocessing, generation, and aggregate metric logging.
3. Build metric inputs with
   `80_semantic_risk_asr/scoring/build_janus_pilot_metric_inputs.py`.
4. Extract risk atoms from top-1 transcripts and reference transcripts.
5. Generate plausible ASR counterfactual variants.
6. Compute SRES as the semantic-risk baseline.
7. Compute CEIS as the proposed decision-stability metric.
8. Run the downstream escalation impact check.
9. Expand to `300-500` high-stakes call segments only if the 15-row pilot
   produces usable decision-stability signal.
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
- `MediaTek-Research/Breeze-ASR-25`

Metrics:

- CER;
- WER;
- risk atom error rate;
- negation flip rate;
- amount distortion rate;
- action confusion rate.

Purpose:

Establish ordinary ASR performance on `janus_165_v1`, then show that ordinary
metrics do not explain which models are stable on risk atoms.

## Experiment 2: Counterfactual Generation Quality

Sample:

- first the reviewed 15-row gate;
- then `300-500` high-stakes call segments from train/validation/test after
  the pilot shows a usable signal.

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

- WER thresholding;
- CER thresholding;
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

# Experiment Plan

Canonical detailed design:

- `q1_paper_design.md`

## Experiment 1: ASR Baseline

Models:

- `openai/whisper-small`
- `openai/whisper-large-v2`
- `MediaTek-Research/Breeze-ASR-25`

Metrics:

- CER
- WER

Purpose:

Establish ordinary ASR baseline performance on `janus_165_v1`.

## Experiment 2: Semantic-Risk Annotation

Sample:

- 300-500 call segments from train/validation/test.

Labels:

- decision-critical error exists: yes/no;
- error type;
- severity;
- downstream impact;
- recommended recovery action.

Artifact:

- `annotation/sample_annotation_sheet.tsv` as the schema.

## Experiment 3: WER/CER vs SRES

Question:

Does SRES identify downstream-failure cases better than WER/CER?

Comparison:

- WER thresholding;
- CER thresholding;
- SRES thresholding.

Outcome:

- best F1 for downstream failure detection;
- high-risk miss rate;
- examples where WER is low but SRES is high.

## Experiment 4: Recovery Evaluation

Conditions:

1. No recovery.
2. Confidence-only recovery.
3. Semantic-risk-aware recovery.

Metrics:

- escalation accuracy;
- high-risk miss rate;
- reviewer workload;
- recovery-trigger rate.

Expected contribution:

Show that semantic-risk-aware recovery catches decision-critical ASR failures
that conventional transcript similarity metrics under-prioritize.

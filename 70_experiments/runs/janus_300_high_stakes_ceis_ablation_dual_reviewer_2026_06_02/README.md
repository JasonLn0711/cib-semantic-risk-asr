# CEIS Ablation On Dual-Reviewer Audit

Date: 2026-06-02

Status: `ceis_ablation_complete`.

This run tests the paper's core mechanism: CDS-ASR evaluates speech
systems by downstream decision stability, and CEIS operationalizes that
mechanism through plausibility, risk-atom weighting, and decision
distance. The completed selected-300 dual-reviewer audit gives the
ablation a reviewer-trustworthy validation surface.

## Variants

- `ceis_full`: plausibility * risk-atom weight * decision distance.
- `ceis_without_atom_weights`: plausibility * decision distance.
- `ceis_without_plausibility`: risk-atom weight * decision distance.
- `ceis_binary_atom`: binary atom-level instability trigger.
- `ceis_full_top3_mean`: top-3 mean over full CEIS variant components.

## Outputs

- `ceis_ablation_summary.json`
- `ceis_ablation_predictor_summary.tsv`
- `ceis_ablation_policy_replay.tsv`
- `ceis_ablation_model_summary.tsv`
- `ceis_ablation_delta_summary.tsv`

## Interpretation

On this selected-300 surface, the ablation isolates the central paper
contribution: decision-changing risk-atom instability is the evidence
signal that transcript-level ASR metrics miss. Plausibility and atom
weights remain explicit CEIS design components and calibration handles;
their separate lift should be interpreted from the delta summary rather
than assumed.

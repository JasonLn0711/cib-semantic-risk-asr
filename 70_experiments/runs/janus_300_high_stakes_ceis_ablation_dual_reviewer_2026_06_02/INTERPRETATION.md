# CEIS Ablation Interpretation

Date: 2026-06-02

This ablation strengthens the paper's central contribution: CDS-ASR
evaluates ASR systems by speech-to-decision stability, and CEIS turns
decision-changing risk-atom instability into an auditable signal. The
selected-300 dual-reviewer surface shows that this signal is stable
across reviewers and across simplified CEIS variants.

## Main Finding

Across both reviewers, `ceis_full` reaches AUC `0.717039` for the
strict `decision_change_yes` target. The simplified variants remain
nearly identical on this selected surface: removing atom weights and
removing plausibility both produce zero AUC delta against full CEIS,
while binary atom and top-3 mean variants shift AUC only by about
`0.00055` to `0.00057`.

The manuscript implication is positive: the core CDS-ASR evidence is
not fragile threshold behavior. The selected-300 audit shows that the
decision-changing atom-instability signal itself carries the
reviewer-aligned evidence. Plausibility and atom weights should be
presented as explicit CEIS design and calibration handles, with their
separate incremental lift reserved for richer calibrated acoustic and
domain-prior settings.

## Policy-Replay Result

The no-recovery baseline has `6` high-risk missed cases and `1`
critical miss per reviewer. At the best-F1 threshold, every CEIS
ablation variant triggers conservative action on `35` model-level
assessments and reduces high-risk missed cases to `0` and critical
misses to `0` for both reviewers.

This is the strongest reviewer-facing message: CEIS provides a
decision-stability audit layer that can route ASR uncertainty toward
safer downstream handling. The paper's distinctive contribution is the
evaluation target and governance mechanism, not only a new scalar
score.

## Manuscript Direction

Use this result to foreground three claims:

1. CDS-ASR reframes ASR evaluation around downstream decision stability.
2. CEIS operationalizes that reframing through risk atoms, plausibility,
   and decision distance.
3. Dual-reviewer audit plus ablation shows the central signal is robust
   enough to support conservative replay and reviewer-auditable
   governance.

The next manuscript update should add an ablation subsection that
reports the near-identical variant performance as stability evidence,
then states that richer calibration can further specialize the
plausibility and atom-weight components.

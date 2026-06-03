# Data And Code Availability

The repository provides aggregate artifacts, scripts, manifests, validation
records, and release-candidate documentation for reviewer-visible auditability.
The final manuscript release-candidate tag is `final-csl-rc-2026-06-03-r2`, which peels
to commit `86ce0b8c7e9a75cf23ed54b36126b5888811b3cb`. The r3 submission
package preserves that scientific boundary and adds provenance and figure-label polish.

Available aggregate artifacts include the final selected-300 / 900-assessment
predictor table, AUC delta bootstrap, SRES residual-gain diagnostic,
row-level positive counts, fixed-budget replay frontier, residual unsafe
breakdown, CEIS ablation summaries, table and figure generation scripts, and
manifest hashes.

Raw audio, raw transcripts, selected row identifiers, audio identifiers, model
hypotheses, transcript-bearing runtime logs, reviewer response sheets, reviewer
notes, completed transcript-bearing review packages, model caches, and model
weights are not released because they may contain sensitive call or review
content. The paper therefore supports aggregate-only reproducibility rather than
row-level external reproduction.

Validation status for the r3 submission package polish pass: clean clone HEAD and clean tree
verified, manuscript claim grep passed, manifest hash check passed,
transcript-bearing leak scan passed, LaTeX rebuild passed, Python compile passed,
and repository smoke checks passed. `pytest` is unavailable in the clean
execution environment (`No module named pytest`); pytest is not part of the
required artifact gate unless development dependencies are installed.

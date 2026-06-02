# Paper 4-a Changelog

Date: 2026-06-02

- Created a new standalone speech-technology manuscript directory.
- Rewrote the current manuscript focus around CDS-ASR, risk atoms, plausible
  ASR variants, CEIS, WER/CER/SRES comparison, human-reviewed labels, and
  aggregate policy replay.
- Moved long artifact availability, operation records, validation gate
  commands, and aggregate-only governance framework material to appendix or
  Paper 4-b scope.
- Updated the submission-critical evidence layer from pilot-only wording to the
  completed selected-300 dual-reviewer audit: 300 reviewed rows and 900
  model-level assessments per reviewer.
- Added Cohen's kappa reporting and framed reviewer agreement as a validation
  layer over the same selected-300 audit surface.
- Added CEIS ablation reporting for full CEIS, without atom weights, without
  plausibility, binary atom, and top-3 aggregation variants.
- Preserved claim-evidence alignment: no deployment readiness claim,
  diagnostic thresholds only, selected-300 as an enriched audit surface, and
  model-level assessments clustered within selected rows.
- Updated R figure-generation scripts for the 300-row / 900-assessment evidence
  ladder and pilot predictor labeling.

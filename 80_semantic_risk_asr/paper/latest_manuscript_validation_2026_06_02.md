# Latest Manuscript Validation

Date: 2026-06-02

Status: latest manuscript surfaces updated and rebuilt.

## Scope

This pass applied the completed selected-300 dual-reviewer human audit,
Cohen's kappa agreement evidence, and CEIS ablation framing to the current
manuscript surfaces:

- `80_semantic_risk_asr/paper/manuscript_submission.tex`
- `80_semantic_risk_asr/paper/manuscript_draft.md`
- `80_semantic_risk_asr/paper/computer_speech_language_submission_notes_2026_06_02.md`
- `paper_4b_aggregate_reproducibility/`

The manuscript now presents the human audit as a completed 300-row
dual-reviewer evidence layer with 900 model-level assessments per reviewer.
Reviewer agreement is paper-facing aggregate evidence: Cohen's kappa is
0.849970 for decision-change, 1.000000 for semantic-risk label, 0.851426 for
expected safe action, and 0.934274 for annotation confidence.

## Build Validation

- Paper 4-b figures regenerated with `.r-env/bin/Rscript paper_4b_aggregate_reproducibility/r/build_all_figures.R`.
- Paper 4-b compiled with `latexmk -pdf -interaction=nonstopmode -halt-on-error -output-directory=/tmp/paper4b_build main.tex`.
- Paper 4-b PDF copied to `paper_4b_aggregate_reproducibility/paper_4b_aggregate_reproducibility.pdf`.
- `80_semantic_risk_asr/paper/manuscript_submission.tex` compiled with `latexmk -pdf -interaction=nonstopmode -halt-on-error -output-directory=/tmp/semantic80_build 80_semantic_risk_asr/paper/manuscript_submission.tex`.
- `80` manuscript PDF copied to `80_semantic_risk_asr/paper/manuscript_submission.pdf`.

## Log Scan

- No LaTeX fatal errors.
- No undefined citations or unresolved references found in the scan.
- Paper 4-b compiled to 9 pages.
- `80` manuscript compiled to 27 pages.
- The `80` log still contains existing table underfull-box warnings, PDF 1.7
  inclusion warnings for generated figures, and one small overfull vbox
  warning. These are layout warnings, not build blockers.

## Next Validation Layer

The next CSL-facing validation step is to regenerate final predictor,
recovery, and CEIS ablation tables from the completed selected-300
dual-reviewer evidence surface, then re-run the manuscript/PDF validation.

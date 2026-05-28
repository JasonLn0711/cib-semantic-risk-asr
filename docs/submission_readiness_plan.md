# Submission Readiness Plan

Date: 2026-05-26
Latest status update: 2026-05-28

Scope: CDS-ASR paper and aggregate artifact package

## Current Verdict

The next project step is not selected-300 human-review expansion and not a new
full-split ASR run. The active lane is converting the frozen evidence chain
into a submission-ready manuscript and aggregate artifact package.

Current gate state:

- roadmap completion: `roadmap_complete=true`, `blocking_gate=none`;
- publishable evidence: `publishable_ready=true`;
- evidence-chain consistency: `26/26` pass, `failed_checks=[]`.

2026-05-28 Route A update:

- Route A remains the active path: direct submission without waiting for a
  second-reviewer blinded transcript-bearing spot-check.
- The manuscript introduction has been revised into the attention-led sequence:
  cited real-world speech-to-decision problem, cited current solution
  landscape, remaining decision-stability gap, CDS-ASR contribution, scoped
  evidence, and validation boundary.
- The LaTeX submission tables now use automatic wrapping and proportional
  column widths so long model names, artifact names, and reviewer-facing notes
  stay readable without changing the evidence claims.
- The rendered PDF and aggregate-only submission package were rebuilt locally:
  `/tmp/cib_tex_build/manuscript_submission.pdf` and
  `/tmp/cib_submission_route_a_2026_05_28.zip`.
- Latest pushed domain-repo commit before this planning refresh:
  `4734cd9` (`docs: refresh manifests after introduction polish`).

## Scope Control

Do not reopen transcript review unless the accepted reference transcript itself
is challenged.

Do not rerun new full-split ASR experiments. Candidate models can move to
258-row or selected-300 only after strict Taiwan Traditional Chinese locale
promotion or an isolated Gemma 4 multimodal runtime exists.

Do not commit transcript-bearing artifacts: raw audio, raw/reference
transcripts, selected sample IDs, audio IDs, ASR hypothesis text, reviewer
notes, runtime logs, local response sheets, or model weights.

## Immediate Priority Order

1. Keep validation gates clean.
2. Run `scripts/check_transcript_bearing_leaks.sh` before packaging.
3. Maintain `claim_registry.tsv`.
4. Keep Table 3/Table 4 language aligned with diagnostic threshold and policy
   replay wording.
5. Maintain row-clustered bootstrap / leave-one-row-out sensitivity outputs.
6. Freeze CEIS method spec, risk atom weights, downstream decision contract,
   and config.
7. Maintain selected-300 selection provenance.
8. Maintain aggregate-only counterfactual variant coverage audit; current
   status reports CEIS top-atom proxy coverage and explicitly marks unavailable
   source-specific variant-generation logs.
9. Maintain fixed-budget recovery frontier for reviewer-visible budget tradeoff
   analysis.
10. Keep Limitations and Ethics/Privacy/Intended Use visible in the manuscript.
11. Maintain checksum manifests and artifact privacy classes.
12. Run hostile-reviewer checklist before submission packaging.
13. For venue-specific submission, adjust formatting, cover-letter wording, and
    bibliography style only; keep the frozen evidence boundary unchanged.

## Submission Package Boundary

Include:

- manuscript submission draft;
- bibliography;
- aggregate figures;
- claim registry;
- artifact manifest;
- predictor and recovery aggregate tables;
- clustered CI tables when generated;
- leave-one-row-out sensitivity tables;
- fixed-budget recovery frontier;
- counterfactual variant coverage summary;
- consequence evidence matrix;
- publishable evidence and consistency summaries;
- privacy boundary and intended-use statements.

Exclude:

- raw audio;
- transcripts;
- ASR hypothesis text;
- audio IDs;
- selected row IDs;
- reviewer notes;
- local response sheets;
- transcript-bearing runtime logs;
- model weights.

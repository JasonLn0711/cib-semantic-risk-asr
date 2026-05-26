# Submission Readiness Plan

Date: 2026-05-26

Scope: CDS-ASR paper and aggregate artifact package

## Current Verdict

The next project step is not selected-300 human-review expansion and not a new
full-split ASR run. The active lane is converting the frozen evidence chain
into a submission-ready manuscript and aggregate artifact package.

Current gate state:

- roadmap completion: `roadmap_complete=true`, `blocking_gate=none`;
- publishable evidence: `publishable_ready=true`;
- evidence-chain consistency: `26/26` pass, `failed_checks=[]`.

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
8. Complete aggregate-only counterfactual variant coverage audit; current
   status table records pending variant-count recomputation.
9. Keep Limitations and Ethics/Privacy/Intended Use visible in the manuscript.
10. Maintain checksum manifests and artifact privacy classes.
11. Run hostile-reviewer checklist before submission packaging.

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

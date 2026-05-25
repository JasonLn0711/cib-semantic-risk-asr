# JANUS Counterfactual Decision-Stability ASR Workspace

Generated: 2026-05-18T15:17:05+08:00

This repository is a local research workspace for JANUS high-stakes call-center
ASR data.

The single short-term paper axis is **Counterfactual Decision-Stability ASR
(CDS-ASR)**.

The paper is not about fine-tuning Whisper as the main contribution. Whisper and
Breeze-ASR baselines provide ASR hypotheses. The main contribution is a way to
test whether downstream decisions remain stable under plausible ASR
alternatives.

The guardrail is explicit: do not sell this as another ASR benchmark, small CER
improvement, or human-review workflow. Sell it as decision stability under
plausible transcript alternatives in high-stakes conversational decision
systems.

```text
audio
-> ASR transcript + confidence / n-best / timestamps
-> risk atom extraction
-> plausible counterfactual transcript variants
-> downstream decision stability / CEIS
-> automatic constrained recovery or conservative machine action
```

The original downloaded zip files were kept, and the extracted folders were
moved into stable `part-###` names. Large audio/transcript assets remain local.

## Layout

| Path | Purpose |
| --- | --- |
| `00_source_archives/google_drive_split_zips/` | Original downloaded split zip archives. Keep these as source evidence. |
| `10_extracted_parts/part-###/` | Extracted contents from each present archive part. |
| `20_inventory/` | Generated inventory files for search, review, and cleanup planning. |
| `30_review_flags/` | Human-readable notes about missing parts and risk areas. |
| `40_breeze_asr25_finetune_dataset/` | Existing Hugging Face AudioFolder dataset with JANUS audio/transcript pairs. |
| `50_janus_data_library/` | Purpose/type overlay for navigating source, audio, labels, models, environments, and reports. |
| `60_whisper_asr_finetuning/` | Primary Whisper ASR fine-tuning workspace, dataset entry point, configs, and validation scripts. |
| `70_experiments/` | Experiment registry, run records, metric templates, and reviewed ASR outputs. |
| `80_semantic_risk_asr/` | Main paper axis: CDS-ASR, risk atoms, counterfactual variants, CEIS scoring, downstream scam escalation, and automatic recovery policy. |
| `90_legacy_imports/` | Local-only legacy import area for old JANUS training exports, including pruned manifests and provenance records. |
| `docs/` | Repo-level data map and handling rules. |

## Inventory files

| File | Use |
| --- | --- |
| `20_inventory/archive_parts.tsv` | Source zip list with sizes and matching extracted-part status. |
| `20_inventory/extracted_parts.tsv` | One-row summary per extracted part. |
| `20_inventory/file_inventory.tsv` | Full file inventory with relative paths, sizes, extensions, and modified times. |
| `20_inventory/extension_counts.tsv` | File type counts. |
| `20_inventory/largest_files.tsv` | Largest files for storage review. |
| `20_inventory/moves.tsv` | Audit trail for this organization pass. |

## Notes

- Missing expected part: `004`.
- The 2026-05-18 archive organization pass performed no data deletion.
- The 2026-05-25 `janus_old_train` import is local-only under
  `90_legacy_imports/`; non-selected LoRA and partial-encoder parameter files
  were pruned from the repo copy while experiment metadata and analysis records
  were retained.
- The 2026-05-25 canonical 258-row test split comparison now has aggregate
  six-model evidence under
  `70_experiments/runs/janus_258_test_split_asr_cds_proxy/`: legacy partial
  encoder, legacy LoRA, Breeze-ASR-25 base, Breeze-ASR-26, Whisper large-v2,
  and Whisper small. The partial encoder remains the current ASR hypothesis
  generator candidate.
- The expanded ASR candidate matrix is recorded in
  `docs/asr_candidate_expansion_2026_05_25.md` and
  `60_whisper_asr_finetuning/configs/janus-15-asr-model-candidates.yaml`.
  New candidates must pass smoke, 15-row hypothesis contract, runtime logging,
  and Taiwan Traditional Chinese locale gates before any full split run.
  The 2026-05-25 runtime gate is recorded in
  `70_experiments/runs/asr_candidate_runtime_gate_2026_05_25/`: Whisper
  large-v3 and large-v3-turbo completed the 15-row gate but had locale
  violations. The 2026-05-26 extension in
  `70_experiments/runs/asr_candidate_15_row_extension_2026_05_26/` promoted
  SenseVoiceSmall and Qwen3-ASR-0.6B to the fixed 15-row gate; both passed the
  field contract but failed the strict zh-TW locale gate (`14/15` and `15/15`
  locale-violation rows). Qwen3-ASR-1.7B still times out before inference at
  fetch/load, and Gemma 4 E2B/E4B remain blocked until an isolated multimodal
  runtime exposes `AutoModelForMultimodalLM`. A 2026-05-26 query-time
  verification rechecked the registry, reran SenseVoice/Qwen 0.6B hypothesis
  validators, and confirmed the local Transformers runtime still lacks the
  Gemma 4 multimodal model classes. Later 2026-05-26 02:03 and 02:44 CST live
  checks also confirmed all requested model pages remain public and ungated,
  SenseVoice/Qwen3-ASR-0.6B 15-row validators still pass, and the local
  Gemma 4 multimodal classes are still absent. The current 2026-05-26 bounded
  recheck in
  `70_experiments/runs/asr_candidate_current_recheck_2026_05_26/` validated
  Whisper large-v3, Whisper large-v3-turbo, SenseVoiceSmall, and
  Qwen3-ASR-0.6B against the fixed 15-row contract, reran a 60-second
  Qwen3-ASR-1.7B load gate, and repeated the Gemma 4 class probe. Decision:
  no remaining requested candidate should move to full-split runtime before
  locale/runtime policy changes. A follow-up live check at 2026-05-26 03:43
  CST confirmed the same decision: public model metadata is still available,
  the four 15-row candidates still validate, Qwen3-ASR-1.7B still times out at
  fetch/load, and Gemma 4 still needs an isolated runtime because local
  Transformers does not recognize `model_type=gemma4`. The 2026-05-26 05:19
  CST live recheck repeated the same bounded gate: four 15-row candidate files
  still pass field-contract validation, Qwen3-ASR-1.7B still times out at
  fetch/load after `60.07s`, and Gemma 4 remains runtime-blocked. No
  full-split promotion is justified until locale/runtime policy changes. A
  response-time validation at 2026-05-26 06:45 CST revalidated the four
  existing 15-row hypothesis files and the local Gemma class probe without
  starting a new full inference run; the decision remains unchanged. A 2026-05-26
  07:24 CST bounded recheck again validated the four 15-row files, confirmed the
  seven model pages remain public/ungated, confirmed local Gemma multimodal
  classes are still absent, and intentionally did not rerun Qwen3-ASR-1.7B
  because repeated tracked bounded gates already timed out before inference.
- The postdoc-level roadmap after the 258-row gate is recorded in
  `docs/postdoc_next_steps_2026_05_25.md`. It defines the next sequence:
  complete comparable 258-row baselines, add split-aware metric inputs, run the
  300-row high-stakes main experiment, then evaluate recovery policies.
- The machine-checkable evidence-chain readiness gate is
  `80_semantic_risk_asr/scoring/check_evidence_chain_readiness.py`, with the
  current aggregate output under
  `70_experiments/runs/postdoc_evidence_chain_2026_05_25/`. Current status:
  `ok=true`, `paper_ready=false`, because the selected-300 human risk-atom
  audit remains `0/30` risk/decision row reviews and `0/90` model assessments
  reviewed. Transcript ground truth is already accepted for WER/CER scoring
  and is not the pending gate. The readiness summary now also reports the
  current reviewer action gate: `reviewer_action_ready` for
  `critical_or_high_risk_missed`, with `6/6` packet rows and `18/18` model
  assessments still pending in the ignored local response TSV. The selected-300
  validator and response-apply path now enforce decision consistency: a
  decision-change `yes` needs at least one critical atom and a non-`none` safe
  action, and critical atoms must be present in the row risk-atom set. The
  reviewer handoff and response closeout path now also require per-row review
  timing in the strict dry-run/write commands, so the current live closeout
  reports both `incomplete_response` and `missing_review_timing` until the
  local response TSV records row/model decisions plus timing coverage. The
  apply summary and response closeout now also expose
  `response_gap_summary_by_row`, a row-number-only gap map that lists missing
  row fields, model-assessment gaps, and timing gaps without audio IDs,
  transcript text, hypotheses, or reviewer notes. The current packet reports
  `6/6` rows with gaps, `48` row fields missing, `18` model assessments
  missing, and `72` model-assessment fields missing. The closeout command now
  also writes `human_audit_response_gap_checklist.tsv` as the tracked
  row-number-only TSV checklist for the same gaps, with per-row timing
  start/finish helper commands copied from the fresh reviewer handoff. It also
  writes `human_audit_response_action_items.tsv`, a field-level action list for
  the current packet: `126` pending items, split into `48` row-field items,
  `72` model-field items, and `6` timing items. The normal refresh path now
  also writes `human_audit_review_work_order.tsv` and
  `human_audit_review_work_order_summary.json`, an aggregate-only row-by-row
  reviewer work order with `33` steps for the current `6` packet rows: start
  timing, open the local row, fill row fields, fill model fields, finish
  timing, then run strict dry-run, closeout, and the post-review sequence
  runner. The sequence runner is the only packet-level route after closeout; it
  preserves write/refresh, strict human-reviewed recovery, post-review
  checklist, and objective audit order. This work order records only row
  numbers, commands, field names, counts, status, privacy boundaries, and
  runtime; it does not track audio IDs, transcripts, hypotheses, selected
  sample IDs, local row content, or reviewer notes.
  Normal refresh also writes
  `human_audit_post_review_sequence_summary.json` and
  `human_audit_post_review_sequence.tsv`, a plan-only post-review sequence gate
  for the strict order after response closeout: strict dry-run, response
  closeout, write/refresh/prepare-next, aggregate refresh, strict
  human-reviewed recovery, post-review checklist, and objective requirements
  audit. Current status is `post_review_sequence_blocked` with `0` executed
  steps because the local response TSV still lacks row/model/timing reviewer
  fields.
  The high-level readiness,
  publishable, roadmap, post-review, consequence, and refresh summaries now
  surface the same timing blocker so the paper-readiness path cannot
  accidentally treat row/model fields as sufficient without review elapsed-time
  evidence.
  The aggregate consistency audit
  `80_semantic_risk_asr/scoring/audit_evidence_chain_consistency.py` now checks
  these summaries together, including reviewer handoff freshness and timing
  awareness, per-row timing-helper command coverage, the response gap/action
  TSVs, the aggregate review work order, the post-review sequence gate, and
  the post-review command plan.
  Current status is `ok=true` with `22/22` checks passing:
  transcript ground truth is not reopened, remaining review scope includes
  row/model/timing fields, proxy evidence is not promoted to paper claims, and
  expanded ASR/Gemma candidates remain behind locale/runtime gates. It also
  checks that post-review recovery is rerun strictly, without the
  pending-summary allowance, that timing helper commands cover current packet
  rows `1-6`, and that the response gap TSV carries the same per-row timing
  helper commands before objective completion can be claimed. Check `C069`
  additionally requires the action-items TSV to match the closeout gap counts
  before local review is routed from tracked records. Check `C071` requires the
  work-order TSV to cover the current row/model/timing actions and packet
  closeout order before reviewer work is treated as operationally routed.
  Check `C074` requires the work-order packet step after closeout to route
  through `run_post_review_evidence_sequence.py --execute`, so reviewer
  operations cannot bypass the strict sequence runner. Check `C075` requires the
  work-order packet strict dry-run to preserve `--require-complete`,
  `--require-timing`, and `--require-session-start-gate` without write-mode
  flags, so local reviewer work cannot skip timing/session gates. Check `C076`
  applies the same strict dry-run command safety to the post-review sequence TSV
  before any write/refresh or human-reviewed recovery route can be treated as
  executable.
  Check `C072` requires the post-review sequence TSV to preserve the strict
  post-review order and to keep the human-reviewed recovery rerun free of
  `--allow-pending-summary`. Check `C073` requires the original-objective audit
  to record the current post-review sequence status and to route objective
  completion through `run_post_review_evidence_sequence.py --execute`.
  The normal `refresh_human_audit_evidence.py` path now also refreshes this
  consistency status and records `consistency_audit_ok=true` in
  `human_audit_refresh_summary.json`.
  The local response timing helper
  `80_semantic_risk_asr/annotation/mark_human_audit_response_timing.py` now
  supports dry-run or write-mode updates to the ignored response TSV timing
  columns. Current live dry-run proves row `1` timing can be proposed without
  modifying the local response file; closeout still reports `0/6` timing rows
  filled until a reviewer actually writes timing during review.
  The post-review evidence checklist
  `80_semantic_risk_asr/annotation/build_post_review_evidence_checklist.py`
  now records the aggregate gates that must pass after response closeout,
  write, and refresh; current status is `post_review_evidence_blocked`
  because human refresh/predictor outputs are incomplete and recovery evidence
  is still proxy-only. Its summary now also carries a post-review command plan:
  complete the current response closeout first, then run aggregate refresh,
  strict human-reviewed recovery, post-review checklist, and objective
  requirements audit in order. Normal `refresh_human_audit_evidence.py` now
  updates this post-review evidence status in
  `human_audit_refresh_summary.json`.
  A stricter objective-by-objective publication audit is
  `80_semantic_risk_asr/scoring/audit_publishable_evidence_chain.py`; its
  current output records `publishable_ready=false` with objective `5`
  `review_pending`, objectives `4`/`6` still proxy-only, and the same reviewer
  action gate surfaced as the next execution state, including `6/6` timing rows
  still pending for the current packet.
  The explicit original-objective requirements audit
  `80_semantic_risk_asr/scoring/audit_postdoc_objective_requirements.py`
  now verifies the named 0-6 requirements directly. Current status:
  `objective_requirements_ready=false`, with `8` requirements satisfied, `5`
  proxy-satisfied, and `2` still review-pending. This is the completion audit
  for the postdoc objective: it proves the repo has strong proxy evidence, but
  not yet paper-ready human-reviewed CDS-ASR evidence. Requirement `6.3` now
  also records the strict post-review sequence status, so the final route
  cannot skip response closeout, write/refresh, strict human-reviewed recovery,
  post-review checklist, or objective audit order. The normal
  `refresh_human_audit_evidence.py` path refreshes the sequence summary before
  this audit and records `objective_requirements_ready=false` in
  `human_audit_refresh_summary.json`.
- Split-aware metric-input generation now lives at
  `80_semantic_risk_asr/scoring/build_janus_metric_inputs.py`, with validation
  recorded in
  `70_experiments/runs/janus_split_aware_metric_inputs_2026_05_25/`. Manifest
  transcripts used as WER/CER scoring references are treated as already
  human-reviewed ground truth. CDS/risk-atom labels are a separate review
  surface; do not reopen transcript review unless the requested human-review
  fields differ from the provided ground-truth transcript fields.
- The first automatic recovery policy gate now lives at
  `80_semantic_risk_asr/recovery/evaluate_recovery_policies.py`, with the
  six-model 258-row proxy result recorded in
  `70_experiments/runs/janus_258_recovery_policy_proxy_2026_05_25/`. Treat it
  as engineering evidence only until the selected 300-row high-stakes and
  human risk-atom audit gates run.
- The selected-300 human-reviewed recovery rerun path now lives at
  `80_semantic_risk_asr/recovery/evaluate_human_reviewed_recovery_policies.py`,
  with the current pending aggregate summary recorded in
  `70_experiments/runs/janus_300_high_stakes_recovery_human_reviewed_2026_05_26/`.
  Normal human-audit refresh updates this summary before the post-review
  checklist; current status is `review_pending`, so recovery remains
  proxy-only for paper claims.
- The selected-300 metric-predictor proxy gate now lives at
  `80_semantic_risk_asr/scoring/analyze_metric_predictors.py`, with aggregate
  output recorded in
  `70_experiments/runs/janus_300_high_stakes_metric_predictor_proxy_2026_05_25/`.
  It compares WER/CER/SRES/CEIS against downstream label flips, unsafe
  downrouting, high-risk misses, and low-WER danger counts without tracking
  transcript or sample-level rows.
- The selected-300 human risk-atom audit queue now lives at
  `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/`.
  The tracked protocol is
  `80_semantic_risk_asr/annotation/selected_300_human_risk_atom_audit_protocol_2026_05_25.md`.
  The transcript-bearing audit sheet remains local-only under ignored
  `artifacts/`; review is still pending. The local sheet is validated by
  `80_semantic_risk_asr/annotation/validate_human_risk_atom_audit.py`, whose
  strict `--require-complete` mode currently fails as expected until all
  `30` risk/decision row-review fields and `90` model assessments are reviewed;
  this is not a duplicate transcript-review requirement. Aggregate review status
  is produced by
  `80_semantic_risk_asr/annotation/summarize_human_risk_atom_audit.py`, and
  model-level reviewer assessments are required before making model-comparison
  claims from the human audit. Human-reviewed WER/CER/SRES/CEIS predictor
  tables are produced by
  `80_semantic_risk_asr/annotation/analyze_human_audit_predictors.py` after
  review. Local row-by-row review support lives in
  `80_semantic_risk_asr/annotation/review_human_risk_atom_audit.py`; its
  `--show-row` output is transcript-bearing and must stay local-only. The next
  local review batch is prepared by
  `80_semantic_risk_asr/annotation/prepare_human_audit_review_batch.py`; current
  tracked batch records point to the ignored `critical_or_high_risk_missed`
  packet for rows `1-6` and `18` model assessments. Current batch completion is
  audited by
  `80_semantic_risk_asr/annotation/audit_human_review_batch_status.py` and
  remains `batch_pending`: `0/6` rows and `0/18` model assessments reviewed.
  Local TSV response entry is handled by
  `80_semantic_risk_asr/annotation/apply_human_audit_batch_response.py`; the
  current ignored response template has `18` rows and its blank dry-run status
  is `response_pending`. The template now has optional review-timing columns,
  and the tracked apply summary records aggregate timing coverage without
  exposing row content. The response workflow also appends a repo-safe apply
  log row for every dry-run/write attempt and writes a machine-readable
  apply-log summary. A one-file reviewer handoff is available from
  `80_semantic_risk_asr/annotation/build_human_audit_reviewer_handoff.py`;
  current handoff status is `reviewer_input_pending` and
  `freshness_status=fresh`. The handoff records source-summary SHA-256 digests;
  run the same tool with `--check-existing` before reviewer work and require
  `handoff_fresh`. Before opening local review files, run
  `80_semantic_risk_asr/annotation/preflight_human_audit_review_session.py`;
  current preflight status is `review_session_ready`, with both local paths
  present. The reviewer value contract is generated by
  `80_semantic_risk_asr/annotation/build_human_audit_reviewer_rubric.py`;
  current rubric status is `rubric_ready`, validator constants match the strict
  audit validator, and the contract records that transcript ground truth is not
  re-reviewed for WER/CER. The aggregate reviewer action checklist is generated by
  `80_semantic_risk_asr/annotation/build_human_audit_reviewer_action_checklist.py`;
  current checklist status is `reviewer_action_ready` with
  `rubric_status=rubric_ready`, `6/6` packet rows, and `18/18` model
  assessments still pending in the ignored local response TSV. The normal
  reviewer-session start command is
  `80_semantic_risk_asr/annotation/start_human_audit_review_session.py`; current
  start status is `reviewer_session_started`, with a tracked aggregate
  session-start summary/log and no change to human-review completion. The
  strict dry-run/write commands generated from the handoff now require
  `--require-session-start-gate` against that session-start summary; the live
  strict dry-run records `session_start_gate.ok=true` and still fails only
  because reviewer response content is incomplete. Response closeout is tracked
  by `80_semantic_risk_asr/annotation/build_human_audit_response_closeout_checklist.py`;
  current closeout status is `response_closeout_blocked` because `0/6` row
  decisions and `0/18` model assessments are filled; the closeout summary now
  names the per-row aggregate gaps by row number only.
  The strict
  `--require-complete` dry-run currently
  exits nonzero as expected with `ok=false` and `incomplete_response=1`; this is
  the completion gate before any `--write`. After strict dry-run passes, use
  `--write --refresh-after-write` to update the ignored local sheet, audit the
  current batch, and refresh aggregate readiness/publishable status in one pass.
  Add `--prepare-next-after-write` when the same command should also prepare
  the next local review packet and response TSV template.
  After
  review edits, use
  `80_semantic_risk_asr/annotation/refresh_human_audit_evidence.py` to rerun
  validation, aggregate review-progress counts, aggregate review summaries,
  human-reviewed predictor outputs, the evidence-chain readiness gate, and the
  objective-level publishable completion audit, and the roadmap completion
  audit in one recorded pass. Current refresh status is still
  `review_pending`: `0/30` risk/decision row reviews and `0/90` model
  assessments reviewed; `paper_ready=false`, `publishable_ready=false`, and
  `roadmap_complete=false`. The progress audit recommends six batches,
  starting with `critical_or_high_risk_missed` and `unsafe_downrouting`.
  Batch-by-batch `partial_review` is treated as in-progress evidence, not as
  missing evidence.
- The roadmap-level completion audit
  `80_semantic_risk_asr/scoring/audit_postdoc_roadmap_completion.py` maps the
  original postdoc objective steps `0-6` plus the human-review/publishable
  gate to tracked aggregate evidence. Current output:
  `roadmap_complete=false`, `publishable_ready=false`, `paper_ready=false`,
  `post_review_evidence_ready=false`, and blocking gate
  `selected_300_human_review_and_post_review_refresh`. It also records that the
  expanded ASR/Gemma candidates should not be promoted while strict zh-TW
  locale or multimodal runtime gates remain unresolved.
- The 2026-05-25 WER audit is recorded in
  `70_experiments/runs/wer_metric_audit_2026_05_25/`. The latest audit checks
  legacy 15-row, six 258-row, and high-stakes 300-row hypothesis files against
  canonical manifests, records package versions, fails paper-facing summaries
  on zero-reference metric units, and cross-checks zh-jieba corpus WER against
  `jiwer`. Pre-audit WER fields are legacy raw whitespace-token values;
  paper-facing ASR tables should use the `cer_zh_micro` aggregate column as the
  primary surface metric and `wer_zh_jieba_micro` only as a supplemental
  segmented word metric. `audit_wer_journal_compliance.py` records the current
  journal-compliance verdict: paper reporting is compliant under that policy,
  while not all stored legacy `wer` fields are journal-compliant evidence.
- Treat audio/call data and filenames as sensitive.
- If storage cleanup is needed later, review `30_review_flags/REVIEW.md` and `20_inventory/largest_files.tsv` first.

## 2026-05-22 Whisper ASR Workspace Update

- Top-level `.venv/` is treated as disposable and should be rebuilt from `requirements-whisper.txt`.
- All old symlinks that pointed at `/home/jnln3799/Downloads/JANUS_ubuntu24/...` were rewritten to repo-relative targets.
- The training entry point is now `60_whisper_asr_finetuning/datasets/janus_165_v1/hf_audiofolder`.
- Experiment records should be registered in `70_experiments/registry.tsv` before long training runs.

## Purpose-Oriented Library

A complete purpose/type overlay is available at `50_janus_data_library/`.

Use it to navigate the archive by goal:

- source archives
- raw audio
- segmented audio
- labels and transcripts
- Breeze-ASR-25 fine-tune-ready dataset
- models and checkpoints
- code and pipelines
- runtime environments
- evaluation and reports
- inventory and audit

For Whisper-specific work, start with `docs/REPO_MAP.md` and
`60_whisper_asr_finetuning/README.md`.

For the paper-facing research frame, start with
`80_semantic_risk_asr/README.md` and
`80_semantic_risk_asr/paper/story_outline.md`. For the current postdoc-level
execution sequence, start with `docs/postdoc_next_steps_2026_05_25.md`.

## Automated Version Control

This repo uses SemVer-style automated versioning. Current version:

```text
v2.5.9
```

Source of truth:

- `VERSION`
- `version_manifest.json`
- `CHANGELOG.md`
- `version_history.jsonl`
- `VERSIONING.md`

Install the local git hook once per checkout:

```bash
python3 scripts/install_version_hooks.py
```

After installation, every commit that stages versioned repo content runs
`scripts/auto_version.py --stage`, bumps the version, updates the manifest, and
records a human-readable plus JSONL version log.

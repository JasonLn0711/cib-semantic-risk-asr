# 投稿準備包：CDS-ASR 論文下一步

Date: 2026-05-26

Status: manuscript packaging and submission-readiness work plan

Canonical draft:

- `80_semantic_risk_asr/paper/manuscript_draft.md`

Second-reviewer decision record:

- `80_semantic_risk_asr/paper/second_reviewer_evidence_boundary_review_2026_05_26.md`

Primary rule:

> 目前不新增 full-split ASR 實驗。下一步是把已完成的 evidence chain 轉成可投稿的 manuscript、表格、圖、appendix、artifact statement 與 reviewer-facing claim map。

## 1. Current Gate Verdict

目前 evidence gate 已經可以支撐 scoped paper-ready manuscript package：

| Gate | Current status | Paper meaning | Evidence |
| --- | --- | --- | --- |
| Roadmap completion | `roadmap_complete=true`, `blocking_gate=none` | 原先 0-6 研究路線已完成 | `postdoc_roadmap_completion_summary.json` |
| Publishable evidence | `publishable_ready=true` | 主要論文證據可依 scoped claims 使用 | `publishable_evidence_completion_summary.json` |
| Consistency audit | `26/26` pass | reviewer workflow、candidate boundary、proxy/human-reviewed boundary 一致 | `evidence_chain_consistency_summary.json` |
| Selected-300 human audit | `review_complete` | 30/30 rows、90/90 model assessments 可支撐 paper-grade risk claims | `human_audit_refresh_summary.json` |
| Human-reviewed recovery | `human_reviewed_complete` | recovery claims 可使用 reviewed labels | `janus_300_high_stakes_recovery_human_reviewed_2026_05_26/summary.json` |
| Candidate ASR/Gemma lane | bounded, no promotion | 候選模型是 exploratory/runtime evidence，不進 main table | `asr_candidate_current_recheck_2026_05_26/summary.json` |

Immediate implication:

> 下一個完整步驟不是「再跑模型」，而是完成 manuscript expansion、table/figure package、citation coverage、artifact appendix、submission checklist。

Second reviewer verdict:

> `conditional pass with manuscript revisions`。selected-300 人工審查不用重開；稿件可以進入 submission-prep，但需要做 claim tightening、citation completion、method operationalization、limitations 補強。現在不是資料或實驗 gate 卡住，而是論文表述還沒完全達到 reviewer-proof。

## 2. Frozen Evidence Boundary

這篇稿件的 claim boundary 固定如下：

| Evidence layer | Use in manuscript | Claim level |
| --- | --- | --- |
| 258-row test split | main ASR benchmark and split/model-comparison context | scope-controlled split/model-comparison evidence |
| selected-300 proxy outputs | input provenance, high-stakes row-selection, engineering traceability | provenance evidence, not final risk claim |
| selected-300 human-reviewed predictor outputs | WER/CER/SRES/CEIS predictor claims | paper-grade risk/predictor evidence |
| selected-300 human-reviewed recovery outputs | recovery and intervention claims | paper-grade recovery evidence |
| candidate ASR/Gemma gates | model-lane boundary and future validation plan | bounded feasibility / runtime / locale evidence |

Do not reopen:

- accepted reference transcript review for WER/CER;
- selected-300 local response review;
- full-split promotion for candidate models.

Do not commit:

- raw audio;
- raw transcripts;
- audio IDs;
- selected sample IDs;
- local response sheets;
- reviewer notes;
- raw hypotheses and predictions;
- transcript-bearing runtime logs;
- model weights, checkpoints, adapters;
- downloaded reviewer packets or zip files.

## 3. Manuscript Expansion Tasks

The current `manuscript_draft.md` has the correct section scaffold and four
paper-facing tables. The next writing pass should expand it section by section.

### 3.1 Abstract

Current role:

- State the real-world speech-to-decision problem.
- State CDS-ASR as the contribution.
- State the scoped evidence chain.
- State the headline result: CEIS aligns better with human-reviewed decision
  change than WER/CER by AUC/conservative recall, and risk-triggered policies
  eliminate high-risk missed and critical miss counts in aggregate replay under
  the selected-300 boundary.

Next edit:

1. Keep it to 180-250 words for journal style.
2. Add the four evidence units in one sentence:
   `six-model 258-row split`, `selected-300 provenance`, `30-row/90-assessment human audit`, `five-policy recovery`.
3. Avoid claiming general deployment readiness. Use "in this scoped high-stakes
   audit" or "under the selected-300 evidence boundary".

### 3.2 Introduction

Teacher-feedback rule:

> 論文不能只是四平八穩；開場要先讓讀者看到一個有 citation 支撐的現實世界問題或可信近未來問題，再公平交代既有解法與 citation，接著提出這些解法仍留下的 claim-evidence gap，最後把 CDS-ASR 寫成解決開場問題的新觀點與方法。

Use the sequence from `attention_led_introduction_blueprint.md`:

```text
real-world speech-to-decision workflow
-> citation-backed operational setting
-> current ASR metric / semantic metric / correction landscape
-> decision-stability gap
-> CDS-ASR viewpoint
-> evidence chain and scope controls
```

Required paragraph map:

| Paragraph | Job | Required evidence/citation |
| --- | --- | --- |
| P1 | Contact-center speech is operational input | AWS Contact Lens / Amazon Connect analytics |
| P2 | Anti-fraud calls make the risk high-stakes | Taiwan NPA 165 page, FBI/IC3 fraud context |
| P3 | WER/CER and semantic ASR metrics enable better ASR evaluation | Kim 2021, Rugayan 2023 |
| P4 | Confidence-aware correction is useful but transcript-centered | Naderi 2024 |
| P5 | Decision-stability gap | this repo's CDS-ASR framing and human-reviewed evidence |
| P6 | Contributions | risk atoms, counterfactual variants, CEIS, recovery, evidence chain |

Positive-scope wording:

> Semantic ASR metrics and confidence-aware correction make transcript evaluation and repair more informative. CDS-ASR adds the high-stakes decision test: whether plausible transcript alternatives would change escalation, routing, or conservative machine action.

### 3.3 Related Work

Use three groups, not a long survey:

1. Transcript-centered ASR metrics and Chinese ASR reporting.
2. Semantic and downstream-aware ASR evaluation.
3. ASR correction / confidence-aware repair / safety-oriented decision systems.

Claim discipline:

- First state what prior work enables.
- Then state the remaining decision-stability target.
- Avoid "prior work fails"; use "CDS-ASR adds".

### 3.4 Method

Required subsections:

1. Problem formulation: speech-to-decision system and escalation labels.
2. Risk atom schema: negation, amount, action, actor, time, intent,
   uncertainty, scam pattern.
3. Counterfactual variant contract: acoustically and semantically plausible ASR
   alternatives, not generic paraphrases.
4. SRES baseline and CEIS proposed metric.
5. Recovery policies: no recovery, confidence-only trigger, SRES-triggered,
   CEIS-triggered conservative action, CEIS ensemble arbitration.
6. Reproducibility and privacy boundary.

Required method language:

> Human review is the evaluation and governance layer. The recovery method itself remains automatic and machine-bounded.

### 3.5 Experiments

The experiment section should be evidence-layered:

| Experiment | Dataset/evidence | Purpose | Claim boundary |
| --- | --- | --- | --- |
| E1 main ASR benchmark | six comparable 258-row runs | show ASR fidelity and decision-risk context | split/model-comparison only |
| E2 selected-300 provenance | selected high-stakes proxy outputs | establish high-stakes audit surface | input provenance |
| E3 human-reviewed predictor | 30 rows / 90 model assessments | compare WER/CER/SRES/CEIS against decision-change labels | paper-grade predictor claim |
| E4 human-reviewed recovery | same reviewed assessment layer | compare five recovery policies | paper-grade recovery claim |
| E5 candidate lane | bounded 15-row / runtime gates | show why new candidates are not promoted | future validation boundary |

E5 should be optional or appendix-facing, not a main result.

### 3.6 Results

Current table package is already drafted in `manuscript_draft.md`. The next
results pass should add one paragraph per table:

| Table | Main result sentence | Evidence source |
| --- | --- | --- |
| Main ASR benchmark | Partial encoder has the strongest 258-row `cer_zh_micro` and lowest dangerous-decision proxy counts among the six comparable runs. | `asr_cds_proxy_comparison.tsv` |
| Candidate lane | New ASR/Gemma candidates have bounded gate evidence but no promotion path until locale/runtime gates change. | `candidate_current_recheck_summary.tsv`, `summary.json` |
| Predictor table | CEIS has the strongest reviewed decision-change AUC among WER/CER/SRES/CEIS in the selected-300 audit. | `human_audit_predictor_comparison.tsv` |
| Recovery table | SRES-triggered recovery and CEIS-triggered conservative action both eliminate high-risk missed and critical miss counts in aggregate replay under human-reviewed labels. | `policy_comparison.tsv`, `summary.json` |

### 3.7 Discussion

Use this order:

1. Correct WER/CER reporting is necessary.
2. High-stakes safety needs decision-stability evidence.
3. Stronger ASR helps, but downstream risk does not reduce to model ranking.
4. Human-reviewed selected-300 evidence supports the paper-grade risk/recovery
   claims.
5. Candidate models are already bounded; the next work is locale/runtime
   validation.
6. Artifact boundary protects transcript-bearing material while preserving
   aggregate reproducibility.

Avoid:

- "The model set is insufficient."
- "The result is only proxy."
- "We cannot claim safety."

Use:

- "The evidence supports scoped selected-300 claims."
- "The candidate lane is separated by validation state."
- "The next validation layer is locale/runtime promotion."

## 4. Paper-Facing Tables And Figures

### Table Package

| Table ID | Title | Source | Current status | Next action |
| --- | --- | --- | --- | --- |
| T1 | Main ASR Benchmark on 258-row Split | `asr_cds_proxy_comparison.tsv` | drafted | Add caption and one result paragraph |
| T2 | Candidate / Exploratory Lane Boundary | `candidate_current_recheck_summary.tsv` | drafted | Add caption explaining no-promotion decision |
| T3 | Human-Reviewed Predictor Comparison | `human_audit_predictor_comparison.tsv` | drafted | Add caption: CEIS AUC 0.9117, recall 1.0 |
| T4 | Human-Reviewed Recovery Policies | `policy_comparison.tsv` | drafted | Add caption: SRES/CEIS replay policies tie at 0 high-risk missed and 0 critical miss |

Second-reviewer table nuance:

- T3: CEIS has the highest AUC and zero false negatives, while SRES has the
  highest best-threshold F1 and fewer false positives. Do not write that CEIS
  universally outperforms all baselines.
- T4: SRES-triggered recovery and CEIS-triggered conservative action tie on
  high-risk missed, critical miss, trigger count, and budget. Do not imply CEIS
  conservative action dominates SRES-triggered recovery at the policy layer.

### Figure Package

Recommended figures:

| Figure ID | Figure | Source | Purpose |
| --- | --- | --- | --- |
| F1 | CDS-ASR pipeline diagram | method text | Show audio -> ASR -> risk atoms -> variants -> CEIS -> recovery |
| F2 | Evidence boundary diagram | this file + readiness summaries | Show 258-row, selected-300 proxy, human-reviewed predictor/recovery layers |
| F3 | Predictor AUC bar chart | `human_audit_predictor_comparison.tsv` | Visualize WER/CER/SRES/CEIS contrast |
| F4 | Recovery policy outcome chart | `policy_comparison.tsv` | Show high-risk missed / critical miss reduction |
| F5 | Model lane state diagram | `docs/model_evaluation_state.md` and candidate summary | Show main table vs candidate vs runtime-blocked lanes |
| F6 | Evidence N-ladder | method evidence units | Show 258 split, selected-300, 30 rows, and 90 clustered assessments |
| F7 | Budget-risk frontier | `policy_comparison.tsv` | Show trigger budget versus severe missed outcomes in replay |

No figure should expose transcript text, sample IDs, audio IDs, reviewer notes,
or row-level predictions.

Generated figure package:

- `80_semantic_risk_asr/paper/generate_paper_figures.py`
- `80_semantic_risk_asr/paper/figures/README.md`
- `80_semantic_risk_asr/paper/figures/f1_cds_asr_pipeline.svg`
- `80_semantic_risk_asr/paper/figures/f2_evidence_boundary.svg`
- `80_semantic_risk_asr/paper/figures/f3_predictor_auc.svg`
- `80_semantic_risk_asr/paper/figures/f4_recovery_outcomes.svg`
- `80_semantic_risk_asr/paper/figures/f5_model_lane_state.svg`
- `80_semantic_risk_asr/paper/figures/f6_n_ladder.svg`
- `80_semantic_risk_asr/paper/figures/f7_budget_risk_frontier.svg`

## 5. Claim-To-Evidence Matrix

| Manuscript claim | Supported wording | Evidence | Boundary |
| --- | --- | --- | --- |
| WER/CER are necessary but not enough for high-stakes decision safety | "Correct WER/CER reporting is necessary but transcript similarity alone does not capture decision instability." | `consequence_evidence_matrix.tsv`, `human_audit_predictor_comparison.tsv` | Human-reviewed selected-300 predictor evidence |
| CEIS better aligns with decision change than WER/CER in this audit | "CEIS reaches AUC 0.9117 against human-reviewed decision-change labels, compared with WER 0.6964 and CER 0.7276." | `human_audit_predictor_comparison.tsv` | 90 reviewed model assessments clustered within 30 reviewed rows |
| Recovery can eliminate severe missed outcomes in replay | "SRES-triggered recovery and CEIS-triggered conservative action both eliminate high-risk missed and critical miss counts in aggregate policy replay." | `policy_comparison.tsv` | selected-300 reviewed labels; replay not live deployment |
| Stronger ASR helps but does not replace decision-stability evaluation | "The partial encoder is strongest on split metrics, while risk and recovery claims use reviewed downstream labels." | `asr_cds_proxy_comparison.tsv`, `human_audit_predictor_model_summary.tsv` | split evidence plus human-reviewed evidence |
| Candidate models are not ready for main table | "Candidate models remain bounded by strict zh-TW locale or runtime gates." | `candidate_current_recheck_summary.tsv`, `docs/model_evaluation_state.md` | exploratory lane only |
| Artifact sharing is aggregate-safe | "The repo tracks aggregate evidence while transcript-bearing inputs remain local or ignored." | `human_audit_refresh_summary.json`, operation-record summaries | privacy-preserving reproducibility |

## 6. Hostile-Reviewer Hardening Gate

目前最重要的 reviewer 攻防不是再補 selected-300 人工審查，而是把四條防線寫進稿件與 appendix：

| Defense line | Manuscript action | Current state | Remaining analysis |
| --- | --- | --- | --- |
| Clustered statistics | 明講 90 model assessments clustered within 30 rows，不當成 90 independent calls | 已加入 N-ladder、Table 3 說明、Limitations | 補 row-clustered bootstrap CI 或 leave-one-row-out sensitivity |
| Selection enrichment | 明講 selected-300 是 enriched high-stakes audit surface，不是 prevalence sample | 已加入 Selection Provenance | 若要更強，排除 CEIS/SRES-selected rows 做 sensitivity |
| Threshold policy | 把 best threshold 改成 diagnostic threshold，不當 deployment threshold | 已改 Table 3 與 Limitations | 補 threshold-budget frontier 與 fixed-budget FN 表 |
| Governance boundary | 新增 Ethics, Privacy, Intended Use，限制 allowed/disallowed uses | 已加入 manuscript，補 NIH/NIST/EU citations | 投稿前補 IRB/exemption/DUA、retention、encryption、access-control 狀態 |

新增 manuscript 防守面：

- N-ladder table：258 split、selected-300 provenance、30 reviewed rows、90 clustered assessments。
- Claim registry：每個核心 claim 對應 scope、artifact、statistic、limitation。
- Table 4 replay language：使用 aggregate policy replay，不寫成 live causal intervention。
- Recovery workload：35 triggers / 7 severe missed outcomes = 5.0 triggers per severe miss eliminated；CEIS ensemble 47 / 7 = 6.7。
- Residual risk：SRES/CEIS conservative replay 之後 unsafe downrouting 仍為 24，另需 governance。
- Intended-use boundary：只支援 audit、risk-aware routing、manual review prioritization、abstention、conservative escalation；不支援自動定罪、凍結、拒絕服務或無人工覆核的執法通報。

Analysis backlog for submission polish:

1. Row-clustered bootstrap or leave-one-row-out sensitivity for AUC/F1/recall/precision/recovery budget。
2. Threshold-budget frontier table：固定 10%、20%、30%、40% budget 下的 FN / severe misses。
3. Aggregate-only variant coverage audit：variant counts by source and atom, rejected variants, no-risk controls。
4. CEIS ablations：no plausibility、uniform atom weights、binary flip only、max vs top-k mean、by-atom class。
5. Artifact manifest：path、role、privacy class、generated_by、source inputs、sha256、source git commit、timestamp、environment。第一版已由 `build_artifact_manifest.py` 產生。
6. Optional 5-10 row blinded second-reviewer spot-check，不重開 selected-300 review。

## 7. Citation Completion Checklist

Citation seed file:

- `80_semantic_risk_asr/paper/citation_seed.md`
- `80_semantic_risk_asr/paper/references.bib`

Required citation groups before submission:

| Citation group | Current seed | Need before submission |
| --- | --- | --- |
| Contact-center analytics | AWS Contact Lens / Amazon Connect analytics | Seed verified 2026-05-26; final pass should convert to target-journal style |
| Anti-fraud hotline | Taiwan NPA 165 page | Seed verified 2026-05-26 with official access date and page update date |
| Fraud scale | FBI/IC3 fraud context | Seed verified 2026-05-26 using 2025 IC3 report context and FBI press release |
| WER limitation / semantic ASR metric | Kim et al. 2021 | BibTeX added; contribution sentence present |
| ASD / semantic severity | Rugayan et al. 2023 | BibTeX added; contribution sentence present |
| LLM ASR correction | Naderi et al. 2024 | BibTeX added; contribution sentence present |
| High-stakes speech decision systems | Miner et al. 2020 | BibTeX added; use as scoped clinical ASR safety-monitoring neighbor |
| Safety / abstention / conservative decision | Chow 1970; Geifman and El-Yaniv 2017/2019; Angelopoulos and Bates 2021 | BibTeX added; use for reject option, selective prediction, and uncertainty-set framing |
| Ethics / privacy / AI governance | NIH human-subjects definition; NIST AI RMF; EU AI Act | BibTeX added; use for sensitive transcript-bearing data, intended-use boundary, and risk-based governance framing |

Second-reviewer citation note:

- The reviewer-provided source anchors should be treated as citation candidates
  to verify before final submission. Use official source URLs, remove tracking
  query parameters, record access dates, and avoid long direct quotations.
- Current manuscript pass has replaced the Introduction citation placeholders
  with citation keys and records the source register in `references.bib`.

Submission rule:

> Do not finalize the introduction until every real-world claim has a citation and every empirical claim points to a tracked aggregate artifact.

## 8. Artifact Availability Statement

Current manuscript text:

```text
The repository release includes aggregate run records, validation summaries,
metric tables, evidence matrices, figure-generation code, and paper-facing
documentation. Raw audio, raw transcripts, selected row identifiers, audio
identifiers, model hypotheses, transcript-bearing runtime logs, reviewer
response sheets, reviewer notes, and model weights are not released because
they may contain sensitive call or review content.
```

Reviewer-reproducible tracked artifacts:

- `70_experiments/registry.tsv`
- `80_semantic_risk_asr/paper/artifact_manifest.tsv`
- `80_semantic_risk_asr/paper/build_artifact_manifest.py`
- `70_experiments/runs/janus_258_test_split_asr_cds_proxy/asr_cds_proxy_comparison.tsv`
- `70_experiments/runs/wer_metric_audit_2026_05_25/journal_compliance_summary.json`
- `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_refresh_summary.json`
- `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_predictor_comparison.tsv`
- `70_experiments/runs/janus_300_high_stakes_recovery_human_reviewed_2026_05_26/policy_comparison.tsv`
- `70_experiments/runs/postdoc_evidence_chain_2026_05_25/publishable_evidence_completion_summary.json`
- `70_experiments/runs/postdoc_evidence_chain_2026_05_25/consequence_evidence_matrix.tsv`
- `70_experiments/runs/postdoc_evidence_chain_2026_05_25/evidence_chain_consistency_summary.json`
- `70_experiments/runs/asr_candidate_current_recheck_2026_05_26/summary.json`

## 9. Immediate Execution Checklist

Execute in this order:

1. Expand `manuscript_draft.md` Abstract to journal length.
2. Expand Introduction using the six-paragraph map.
3. Add Related Work bullets under the three citation groups.
4. Add Method subsections and preserve the automatic-recovery / human-review
   boundary.
5. Add one explanatory paragraph under each Results table.
6. Generate the aggregate-only figure package F1-F7.
7. Replace citation placeholders with citation keys backed by
   `references.bib`.
8. Copy the Artifact Availability statement into the manuscript appendix.
9. Run validation gates to confirm evidence state is unchanged.
10. Inspect `git status --short` and confirm only paper-facing markdown,
    aggregate figure, and aggregate manifest files changed.

## 10. Validation Commands

Run after every manuscript packaging pass:

```bash
.venv/bin/python 80_semantic_risk_asr/scoring/audit_postdoc_roadmap_completion.py --output-json /tmp/cib_roadmap_completion_check.json --output-tsv /tmp/cib_roadmap_completion_check.tsv
.venv/bin/python 80_semantic_risk_asr/scoring/audit_publishable_evidence_chain.py --output-json /tmp/cib_publishable_check.json --output-tsv /tmp/cib_publishable_check.tsv
.venv/bin/python 80_semantic_risk_asr/scoring/audit_evidence_chain_consistency.py --output-json /tmp/cib_consistency_check.json --output-tsv /tmp/cib_consistency_check.tsv
```

Expected results:

- `roadmap_complete=true`
- `blocking_gate=none`
- `publishable_ready=true`
- `status_counts.completed=7`
- `status_counts.pass=26`
- `failed_checks=[]`

## 11. Stop Rules

Stop manuscript expansion and repair evidence first if any of these occur:

1. A validation gate reports `ok=false`.
2. `publishable_ready` changes away from `true`.
3. consistency checks drop below `26/26`.
4. A paper-facing claim lacks either a citation or aggregate evidence pointer.
5. A tracked file introduces raw audio, transcript text, audio IDs, selected
   row IDs, raw predictions, local response sheets, runtime logs, or model
   weights.
6. A candidate model is moved toward 258-row or selected-300 without a clean
   strict Taiwan Traditional Chinese locale gate or isolated Gemma 4
   multimodal runtime.

## 12. Definition Of Done For The Next Manuscript Pass

The next pass is complete when:

- `manuscript_draft.md` has full paragraphs for Abstract, Introduction,
  Related Work, Method, Experiments, Results, Discussion, and Appendix.
- `second_reviewer_evidence_boundary_review_2026_05_26.md` is preserved as the
  reviewer decision record for claim tightening and no-review-reopen scope.
- Every table has a caption, evidence source, and one result paragraph.
- Table 3 explicitly states CEIS AUC/recall strength and SRES F1/false-positive
  strength.
- Table 4 explicitly states the SRES-triggered and CEIS-triggered policy tie.
- Every real-world claim has a citation TODO or final citation.
- Every empirical claim has an aggregate artifact pointer.
- Artifact Availability text is in the appendix.
- Limitations / Threats to Validity is present.
- Candidate-lane models remain explicitly out of the main benchmark table.
- The three validation commands pass.
- `git status --short` shows only intended paper-facing markdown, aggregate
  figure, and aggregate manifest changes.

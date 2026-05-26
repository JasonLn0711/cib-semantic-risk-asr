# 博士後視角的下一步研究路線圖

Date: 2026-05-25

Status: scoped paper-ready roadmap; selected-300 human audit is `review_complete`

## 2026-05-26 Scoped Paper-Ready Addendum

目前這個 roadmap 的執行狀態已從「分批人工審查中」推進為「可依明確範圍撰寫論文主張」。
最新 aggregate audit 顯示：readiness `paper_ready=true`、publishable
`publishable_ready=true`、consequence matrix `paper_claims_ready=true`、
objective requirements `objective_requirements_ready=true`、roadmap
`roadmap_complete=true` 且 `blocking_gate=none`、consistency `ok=true`
with `26/26` checks passing。selected-300 human audit 已完成 `30/30`
risk/decision rows 與 `90/90` model assessments，並保留 per-row review
timing；transcript ground truth 仍維持既有 human-reviewed WER/CER reference，
沒有重新開啟 transcript 審查。

現在的論文證據邊界如下：258-row evidence 作為 scope-controlled
split/model-comparison evidence；selected-300 proxy outputs 作為 input
provenance；selected-300 human-reviewed predictor 與 human-reviewed recovery
outputs 作為 paper-grade risk/recovery claims。這個邊界讓文章可以自信地
主張 CDS-ASR/CEIS 對高風險決策穩定性的價值，同時清楚保留每一種證據的
適用層級。

接下來的實作重點轉為論文敘事與投稿包裝：

1. Introduction 依「現實世界問題 -> 既有解法 -> 缺口 -> 我們的觀點」組織，並為每個現實問題與既有方法補 citation。
2. Methods 明確描述 zh-TW ASR metric normalization、WER/CER 國際可重現計算、SRES/CEIS/downstream gate、human-reviewed selected-300 protocol。
3. Results 分開呈現 main benchmark table、candidate/exploratory lane、human-reviewed CDS-ASR predictor、human-reviewed recovery policy。
4. Discussion 使用正向、自信、範圍清楚的語氣：我們說明證據支持的主張範圍，也說明候選 ASR/Gemma lane 的下一步 runtime/locale gate。
5. Appendix/Artifact Availability 保留所有 operation logs、runtime summaries、registry rows、aggregate-only privacy boundary，讓 reviewer 可以重現每一步。

## 核心判斷

以資訊工程學系博士後研究員的角度，這個 repo 現在不該再被定義成
「ASR fine-tuning repo」。它已經走到更有發表價值的階段：

```text
高風險語音通話
-> 多個 ASR hypothesis
-> risk atom 層級錯誤
-> downstream escalation decision 是否改變
-> CEIS / CDS-ASR 是否比 CER/WER 更能預測危險決策
-> recovery policy 是否能降低 unsafe decision
```

接下來的主張不是「某個模型 CER 最低」，而是：

> 在高風險客服或詐騙通話場景中，傳統 ASR 指標無法充分預測下游決策
> 風險；CDS-ASR 用 decision-stability evidence 找出 CER/WER 掩蓋的危
> 險錯誤，並能觸發保守動作或 constrained recovery 來降低 unsafe
> downrouting。

這個方向比單純 fine-tuning 更像一篇可投稿的資工研究：它有問題定義、
新指標、系統 pipeline、實驗對照、失敗案例、recovery intervention，
也能解釋為什麼一般 ASR benchmark 不夠。

## 2026-05-26 Current Review Update

第一到第六個人工審查 packet 已完成並寫回 ignored local audit sheet。第二包
使用 `/home/jnln3799/Downloads/cib_asr_human_review_completed_package_batch2_2026-05-26(1).zip`
作為權威來源；第三包使用
`/home/jnln3799/Downloads/cib_asr_human_review_completed_package_batch3_2026-05-26.zip`；
第四包使用
`/home/jnln3799/Downloads/cib_asr_human_review_completed_package_batch4_2026-05-26.zip`；
第五包使用
`/home/jnln3799/Downloads/cib_asr_human_review_completed_package_batch5_2026-05-26.zip`；
第六包使用
`/home/jnln3799/Downloads/cib_asr_human_review_completed_package_batch6_2026-05-26.zip`。

目前 selected-300 狀態是 `review_complete`：`30/30` risk/decision rows
與 `90/90` model assessments 已 reviewed，並包含 per-row review timing。
Evidence-chain consistency 維持 `ok=true`、`26/26` checks passing。這個狀態
已進入 scoped paper-ready：258-row 作為 split/model-comparison evidence，
selected-300 proxy outputs 作為 input provenance，selected-300
human-reviewed predictor/recovery outputs 作為 paper-grade risk/recovery
claims。

## 目前證據狀態

已完成且可作為下一步依據的 gate：

1. `15`-row human-reviewed gate 已完成。
2. Whisper small、Whisper large-v2、Breeze-ASR-25、optional Breeze-ASR-26、
   legacy LoRA、legacy partial encoder 都已接過同一個 15-row contract。
3. 五模型 15-row CDS-ASR bridge 已完成，證明 LoRA 雖然改善 CER，卻讓
   CEIS/downstream behavior 變差。
4. Legacy partial encoder、LoRA、Breeze-ASR-25 base、Breeze-ASR-26、Whisper
   small、Whisper large-v2 已完成 canonical `258`-row test split。
5. 258-row aggregate proxy 指標支持 partial encoder 優於 LoRA、Breeze base、
   Breeze-ASR-26 與 Whisper-family baseline：

| Run | zh CER micro | zh-jieba WER micro | Stored CER | Wall time | Sec/row | Unsafe downrouting | High-risk missed | Risk-atom proxy error | Locale violations |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Legacy partial encoder | `15.04` | `21.53` | `18.24` | `213.79s` | `0.829` | `7` | `4` | `0.0431` | `0` |
| Legacy LoRA | `18.23` | `25.59` | `22.86` | `403.37s` | `1.563` | `10` | `7` | `0.0613` | `0` |
| Breeze-ASR-25 base | `22.72` | `30.39` | `33.11` | `164.41s` | `0.637` | `34` | `30` | `0.1145` | `0` |
| Breeze-ASR-26 | `24.27` | `32.29` | `24.87` | `187.25s` | `0.726` | `27` | `22` | `0.1034` | `0` |
| Whisper large-v2 | `24.72` | `32.23` | `24.92` | `523.49s` | `2.029` | `33` | `28` | `0.1276` | `1` |
| Whisper small | `34.86` | `43.44` | `36.11` | `152.92s` | `0.593` | `76` | `70` | `0.2542` | `4` |

6. 六模型 split-aware proxy bridge 已跑完：SRES rows `3184`、CEIS rows
   `3184`、downstream rows `1548`、SRES total `27810.0`、CEIS unstable samples
   `192`、downstream ASR mismatch rate `0.126`、high-risk missed by ASR
   `161`。
7. 300-row high-stakes Breeze-family ASR comparator 已完成 partial encoder、
   LoRA、base 三個 hypotheses，且三者都通過 manifest `300/300` 驗證與
   `jiwer` WER 交叉驗算：

| High-stakes run | zh CER micro | zh-jieba WER micro | Stored WER | Raw whitespace WER micro | Wall time |
| --- | ---: | ---: | ---: | ---: | ---: |
| Legacy partial encoder | `6.86` | `9.38` | `9.55` | `93.16` | `275.74s` |
| Legacy LoRA | `15.97` | `21.91` | `22.15` | `101.30` | `481.25s` |
| Breeze-ASR-25 base | `21.44` | `28.10` | `28.74` | `271.66` | `214.96s` |

8. Selected-300 proxy metric predictor gate 已完成：

| Target | WER AUC | CER AUC | SRES total AUC | CEIS max AUC |
| --- | ---: | ---: | ---: | ---: |
| Unsafe downrouting | `0.7683` | `0.7739` | `0.9954` | `0.9971` |
| High-risk missed | `0.6871` | `0.7138` | `0.9826` | `0.9973` |
| Danger event | `0.7629` | `0.7676` | `1.0000` | `1.0000` |

同一個 gate 也確認：在 row-level WER `<= 10.0` 的 `237` 個 model-samples
中，仍有 `2` 個 label flip / unsafe downrouting 風險訊號。這支持「WER
計算要正確，但正確 WER 仍不足以判斷高風險下游安全」的主張。

9. Selected-300 human risk-atom audit queue 已建立，但尚未完成審查：

| Item | Value |
| --- | ---: |
| Candidate audio rows | `300` |
| Selected audit audio rows | `30` |
| Selected model-samples | `90` |
| Selected high-risk-missed audio rows | `6` |
| Selected unsafe-downrouting audio rows | `22` |
| Selected low-WER danger audio rows | `2` |
| Selected high proxy-risk audio rows | `25` |
| Selected model-disagreement audio rows | `22` |

本地人審 sheet 放在 ignored `artifacts/`，tracked repo 只保留 aggregate
selection stats 與 protocol。這一步把「需要 human audit」從提醒變成可執
行 gate，但尚不能宣稱 human-reviewed CDS evidence 已完成。

10. Human audit aggregate summarizer 已建立：

- Script:
  `80_semantic_risk_asr/annotation/summarize_human_risk_atom_audit.py`。
- Current tracked readiness status:
  `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_review_summary.json`。
- Current state: `30` audit rows、`30` risk/decision row reviews completed、
  `0` pending risk/decision row reviews、`90` model-level assessments、`90`
  reviewed model-level assessments。Transcript ground truth 已接受為 WER/CER
  reference，不是這個 gate 的審查項目。

這表示 selected-300 human annotation stats 已可作為論文證據鏈的一部分；
下一步是把這些 aggregate outputs 寫進 Results 與 Appendix，而不是重審
transcript。

11. Human-reviewed predictor gate 已建立：

- Script:
  `80_semantic_risk_asr/annotation/analyze_human_audit_predictors.py`。
- Current tracked readiness status:
  `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_predictor_summary.json`。
- Current state: `90` model-level assessments、`90` reviewed、`0` pending。

這支工具已把 WER/CER/SRES/CEIS 對上 model-level human decision-change
labels。論文主表可以使用 reviewed subset predictor table；selected-300
proxy AUC 則保留為 input-provenance/engineering context。

12. Human audit aggregate refresh gate 已建立：

- Script:
  `80_semantic_risk_asr/annotation/refresh_human_audit_evidence.py`。
- Current tracked refresh status:
  `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_refresh_summary.json`。
- Current state: normal refresh `ok=true` with `review_complete`；`30/30`
  risk/decision row reviews、`90/90` model assessments reviewed、evidence-chain
  `paper_ready=true`、publishable completion `publishable_ready=true`、
  post-review evidence `post_review_evidence_ready`。
- Strict post-review mode:
  `--require-complete` 目前通過，並同步記錄 publishable、consequence、
  roadmap、objective requirements、consistency 等 aggregate gates。

這支工具把 validator、progress audit、aggregate review summary、
human-reviewed predictor gate、evidence-chain readiness、publishable
completion audit、roadmap completion audit、post-review evidence checklist
串成同一個可重跑操作。人工審閱已在 local ignored sheet 完成；refresh gate
負責把完成後的 aggregate evidence 同步到 tracked outputs，並保留
aggregate-only privacy boundary。

13. Publishable evidence completion audit 已建立：

- Script:
  `80_semantic_risk_asr/scoring/audit_publishable_evidence_chain.py`。
- Current tracked audit:
  `70_experiments/runs/postdoc_evidence_chain_2026_05_25/publishable_evidence_completion_summary.json`。
- Current state: `ok=true` and `publishable_ready=true`；objective `0-6`
  completed under scoped paper claims。
- The audit now also records consequence-matrix alignment. Current consequence
  state is `ok=true` and `paper_claims_ready=true`。
- FIRST PRINCIPLE decision: 主要資源轉向論文主張、citation、artifact
  packaging、candidate-lane runtime/locale policy，而不是盲目增加 ASR
  fine-tuning。

這個 audit 是 requirement-to-evidence matrix：它不新增實驗結論，只是把
「哪些項目真的完成」與「哪些是 scoped proxy/provenance」分開，讓後續論文
包裝可以自信且精準地呈現 evidence level。

14. Human review progress audit 已建立：

- Script:
  `80_semantic_risk_asr/annotation/audit_human_review_progress.py`。
- Current tracked status:
  `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_progress_summary.json`。
- Current state: `review_complete`；`30/30` risk/decision row reviews、`90/90`
  model assessments reviewed。
- Recommended batch order:
  1. `critical_or_high_risk_missed`：6 rows / 18 model assessments；
  2. `unsafe_downrouting`：6 / 18；
  3. `high_proxy_risk`：6 / 18；
  4. `model_disagreement`：4 / 12；
  5. `risk_score_fill`：4 / 12；
  6. `clean_control`：4 / 12。

這個 audit 把 reviewer time 作為可追溯實驗資源記錄。實作上它已經接進
`refresh_human_audit_evidence.py`，所以每次 local sheet 更新後，同一個
refresh gate 會同步更新 validation、progress、summary、predictor、
readiness、publishable completion outputs。

15. Postdoc roadmap completion audit 已建立：

- Script:
  `80_semantic_risk_asr/scoring/audit_postdoc_roadmap_completion.py`。
- Current tracked audit:
  `70_experiments/runs/postdoc_evidence_chain_2026_05_25/postdoc_roadmap_completion_summary.json`。
- Current state: `ok=true` and `roadmap_complete=true`；
  `publishable_ready=true`、`paper_ready=true`、
  `post_review_evidence_ready=true`。狀態計數是 `completed=8`。
- Blocking gate:
  `none`。
- Current selected-300 review count is `30/30` risk/decision row reviews and
  `90/90` model assessments reviewed。

這個 audit 的用途是回答「原始 0-6 roadmap 是否真的完成」，而不是只回答
某個子 gate 是否已經存在。它明確把 completed、scoped proxy/provenance、
human-reviewed evidence 分開，讓 publishable human-reviewed evidence 的
邊界可以被 reviewer 直接檢查。Normal
`refresh_human_audit_evidence.py` 現在會同步更新這個 audit；只有需要單獨
檢查 roadmap 狀態時才直接跑 `audit_postdoc_roadmap_completion.py`。

16. Original-objective requirements audit 已建立：

- Script:
  `80_semantic_risk_asr/scoring/audit_postdoc_objective_requirements.py`。
- Current tracked audit:
  `70_experiments/runs/postdoc_evidence_chain_2026_05_25/postdoc_objective_requirements_summary.json`。
- Current state: `objective_requirements_ready=true`；
  status counts are `satisfied=15`。
- Normal refresh:
  `80_semantic_risk_asr/annotation/refresh_human_audit_evidence.py` now
  refreshes the strict post-review sequence summary before this audit, then
  records `objective_requirements_ready` in `human_audit_refresh_summary.json`。
- What it verifies:
  legacy checkpoint / ignore boundary、LoRA and partial-encoder smoke、
  15-row contract、15-row CDS bridge、six-model 258-row decision-risk columns、
  selected-300 proxy predictor evidence、five recovery conditions and safety
  metrics。
- Paper-grade scope:
  selected-300 non-transcript risk/decision/model/timing review and
  human-reviewed recovery rerun are complete; 258-row split evidence and
  selected-300 proxy outputs are scoped as model-comparison/provenance evidence.

這個 audit 是 completion audit，不是 status 摘要。之後如果要說「0-6
objective 已完成」，這個 audit 是主要 machine-checkable gate。

17. Human-reviewed recovery rerun path 已建立：

- Script:
  `80_semantic_risk_asr/recovery/evaluate_human_reviewed_recovery_policies.py`。
- Current tracked audit:
  `70_experiments/runs/janus_300_high_stakes_recovery_human_reviewed_2026_05_26/summary.json`。
- Current state: `status=human_reviewed_complete`、
  `evidence_mode=human_reviewed`、five policies emitted。
- Normal refresh:
  `80_semantic_risk_asr/annotation/refresh_human_audit_evidence.py` now
  refreshes this human-recovery summary before
  `build_post_review_evidence_checklist.py`。
- Completion gate:
  complete selected-300 row/model/timing review produces
  `evidence_mode=human_reviewed` and supports scoped paper-facing intervention
  claims。

這個路徑讓 objective `6` 的 recovery experiment 有明確 post-review rerun
入口；目前可使用 human-reviewed recovery outputs 撰寫 intervention claim。

18. Post-review command plan 已寫入 checklist summary：

- Source:
  `80_semantic_risk_asr/annotation/build_post_review_evidence_checklist.py`。
- Current tracked field:
  `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_post_review_evidence_summary.json`
  的 `post_review_command_plan`。
- Current first action: `ready_for_paper_claim_review`。
- Post-write order:
  `refresh_human_audit_evidence.py`、
  `evaluate_human_reviewed_recovery_policies.py`、
  `build_post_review_evidence_checklist.py`、
  `audit_postdoc_objective_requirements.py`。
- 這是執行順序 guardrail，不是人工審查完成證據；它的功能是避免
  selected-300 local response 寫入後漏掉 human-reviewed recovery 與 objective
  audit。

19. Post-review command plan 已納入 consistency audit：

- Source:
  `80_semantic_risk_asr/scoring/audit_evidence_chain_consistency.py`。
- New check: `C066`。
- Current state:
  `70_experiments/runs/postdoc_evidence_chain_2026_05_25/evidence_chain_consistency_summary.json`
  現在是 `ok=true`、`26/26` checks passing、`failed_checks=[]`。
- 檢查內容：post-review command plan 必須先完成 response closeout；post-write
  order 必須是 refresh、strict human-reviewed recovery、post-review checklist、
  objective audit；strict recovery command 不能帶
  `--allow-pending-summary`。

20. Local response timing helper 已建立：

- Source:
  `80_semantic_risk_asr/annotation/mark_human_audit_response_timing.py`。
- Current tracked dry-run:
  `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_response_timing_summary.json`。
- Current state: dry-run only；row `23` 的 timing proposal 可讓 coverage 變成
  `1/4`，但 local response TSV 沒有被寫入，closeout 仍是 actual `0/4`
  timing rows filled。
- Reviewer handoff、action checklist、session-start summary 現在提供
  `timing_start_write_by_row` 和 `timing_finish_write_by_row`，涵蓋目前
  packet rows `23-26`；row `23` 的 `timing_start_write` /
  `timing_finish_write` 仍保留作為 compatibility alias。這是 timing
  capture support，不是 human review completion。

21. Per-row timing helper command coverage 已納入 consistency audit：

- Source:
  `80_semantic_risk_asr/scoring/audit_evidence_chain_consistency.py`。
- New check: `C067`。
- Current state:
  `70_experiments/runs/postdoc_evidence_chain_2026_05_25/evidence_chain_consistency_summary.json`
  現在是 `ok=true`、`26/26` checks passing、`failed_checks=[]`。
- 檢查內容：reviewer handoff、action checklist、session-start summary 都必須
  提供 `timing_start_write_by_row` 和 `timing_finish_write_by_row`，且涵蓋
  目前 packet rows `23-26`；first-row compatibility alias 也必須和 by-row map
  對齊。

22. Response gap TSV timing-command alignment 已納入 consistency audit：

- Source:
  `80_semantic_risk_asr/scoring/audit_evidence_chain_consistency.py`。
- New check: `C068`。
- Current state:
  `70_experiments/runs/postdoc_evidence_chain_2026_05_25/evidence_chain_consistency_summary.json`
  現在是 `ok=true`、`26/26` checks passing、`failed_checks=[]`。
- 檢查內容：`human_audit_response_gap_checklist.tsv` 必須和 closeout JSON 的
  current packet rows 對齊，且每列的 `timing_start_write_command` /
  `timing_finish_write_command` 必須和 fresh reviewer handoff 的 by-row
  timing helper commands 一致。這讓 reviewer 可以從 tracked gap TSV 直接
  取得 row/model/timing 缺口與 timing helper command，同時不追蹤 audio IDs、
  transcripts、hypotheses 或 reviewer notes。

23. Response action-items TSV 已納入 consistency audit：

- Source:
  `80_semantic_risk_asr/scoring/audit_evidence_chain_consistency.py`。
- New check: `C069`。
- Current state:
  `70_experiments/runs/postdoc_evidence_chain_2026_05_25/evidence_chain_consistency_summary.json`
  現在是 `ok=true`、`26/26` checks passing、`failed_checks=[]`。
- 檢查內容：`human_audit_response_action_items.tsv` 必須和 closeout JSON 的
  gap counts 對齊，action IDs 必須唯一，且 timing action items 必須含有
  對應的 start/finish timing helper commands。Current live packet 有 `84`
 pending action items：`32` row-field items、`48` model-field items、`4`
  timing items；仍不追蹤 audio IDs、transcripts、hypotheses、selected sample
  IDs、local row content 或 reviewer notes。

24. Aggregate review work-order TSV 已納入 normal refresh 與 consistency audit：

- Source:
  `80_semantic_risk_asr/annotation/build_human_audit_review_work_order.py`。
- Refresh integration:
  `80_semantic_risk_asr/annotation/refresh_human_audit_evidence.py` 會在
  consistency audit 前重建 work-order summary / TSV。
- Checks: `C071`, `C074`, `C075`, and `C078`。
- Current tracked outputs:
  `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_review_work_order_summary.json`
  和
  `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_review_work_order.tsv`。
- Current state:
  work order 是 `review_work_order_ready`，current packet 有 `4` rows、
  `23` ordered steps、`84` pending action items；consistency 現在是
  `ok=true`、`26/26` checks passing、`failed_checks=[]`。
  Summary field `next_reviewer_operation` 現在指出下一個安全操作：
  `row-23:01-mark-timing-start`，以及下一個 local-only row-open 操作：
  `row-23:02-open-local-row`。
- 檢查內容：`C071` 要求 work-order TSV 的 row coverage 和 closeout row gaps
  對齊，action item count 和 closeout count 對齊，必須包含 row-level timing
  start/open/fill/finish steps 以及 packet-level strict dry-run、closeout、
  `post_review_sequence_execute`，並且不能追蹤 audio IDs、transcripts、
  hypotheses、selected sample IDs、local row content 或 reviewer notes。
  `C074` 進一步要求 packet closeout 後的 work-order command 必須包含
  `run_post_review_evidence_sequence.py --execute`，所以 reviewer route 不會
  繞過 strict sequence runner。`C075` 進一步要求 packet-level strict dry-run
  command 必須包含 `--require-complete`、`--require-timing`、
  `--require-session-start-gate`，且不能包含 `--write`、
  `--refresh-after-write` 或 `--prepare-next-after-write`。`C078` 進一步要求
  work-order summary 暴露 next reviewer operation：先記錄 timing start，
  再用 local-only `review_human_risk_atom_audit.py --show-row` 開啟同一列；
  command output 會含 transcript-bearing row content，不能複製進 tracked
  files。這是 reviewer
  操作路線與 timing/session record 的
  guardrail，不是 human review completion。

25. Aggregate operation-record audit 已納入 normal refresh 與 consistency audit：

- Source:
  `80_semantic_risk_asr/annotation/audit_human_audit_operation_records.py`。
- Refresh integration:
  `80_semantic_risk_asr/annotation/refresh_human_audit_evidence.py` 會在
  consistency audit 前重建 operation-record summary / TSV。
- New check: `C079`。
- Current tracked outputs:
  `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_operation_record_summary.json`
  和
  `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_operation_record_audit.tsv`。
- Current state:
  operation records 是 `operation_records_ready`，`6/6` required logs aligned；
  consistency 現在是 `ok=true`、`26/26` checks passing、`failed_checks=[]`。
- 檢查內容：`C079` 要求 current review batch、preflight、
  reviewer-session start、strict apply dry-run、timing helper、post-review
  sequence 這六個 append-only aggregate logs 都存在，且 latest log row 和
  目前 `6` packet rows、`18` model assessments、`6` pending timing rows、
  `row-7:01-mark-timing-start` 下一步一致。這是 operation provenance
  guardrail，不是 human review completion。

26. Strict post-review sequence gate 已納入 normal refresh 與 consistency audit：

- Source:
  `80_semantic_risk_asr/annotation/run_post_review_evidence_sequence.py`。
- Refresh integration:
  `80_semantic_risk_asr/annotation/refresh_human_audit_evidence.py` 會在
  post-review evidence checklist 後重建 sequence summary / TSV，然後讓
  objective requirements audit 讀取目前 sequence status，最後再跑
  consistency audit。
- New checks: `C072`, `C076`, and `C077`。
- Current tracked outputs:
  `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_post_review_sequence_summary.json`,
  `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_post_review_sequence.tsv`,
  和 append-only
  `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_post_review_sequence_log.tsv`。
- Current state:
  sequence 是 `post_review_sequence_blocked`、`mode=plan_only`、
  `executed_step_count=0`，因為 current response closeout 還不是
  `response_complete_ready_to_write`；consistency 現在是 `ok=true`、`26/26`
  checks passing、`failed_checks=[]`。
- 檢查內容：`C072` 要求 sequence TSV 保持嚴格順序：
  strict dry-run、response closeout、write/refresh/prepare-next、aggregate
  refresh、strict human-reviewed recovery、post-review checklist、objective
  requirements audit。Human-reviewed recovery command 不能帶
  `--allow-pending-summary`。`C076` 要求 sequence TSV 的 strict dry-run command
  保留 `--require-complete`、`--require-timing`、
  `--require-session-start-gate`，且不能帶 write-mode flags。`C077` 要求
  sequence summary 明確記錄 `--execute` 在任何 blocked gate 前停止，並留下
  `executed_step_count` 與 `stopped_step` accounting，避免 reviewer closeout
  尚未完成時誤把 sequence runner 視為可寫入。這是 post-review
  execution-order guardrail，不是 human review completion。

27. Objective sequence-routing evidence 已納入 consistency audit：

- Source:
  `80_semantic_risk_asr/scoring/audit_evidence_chain_consistency.py`。
- New check: `C073`。
- Current tracked outputs:
  `70_experiments/runs/postdoc_evidence_chain_2026_05_25/evidence_chain_consistency_summary.json`
  和
  `70_experiments/runs/postdoc_evidence_chain_2026_05_25/evidence_chain_consistency.tsv`。
- Current state:
  consistency 現在是 `ok=true`、`26/26` checks passing、`failed_checks=[]`。
- 檢查內容：`C073` 要求 original-objective requirement `6.3` 同時記錄
  `human_audit_post_review_sequence_summary.json`、目前的
  `post_review_sequence_status`、`post_review_sequence_ok`、
  `post_review_sequence_executed_step_count`，並且要求 requirement-level
  `next_action` 與 top-level `next_decision` 都把 final completion route 指向
  `run_post_review_evidence_sequence.py --execute`。這是防止 objective audit
  在 sequence gate 之外被單獨宣告完成的 guardrail，不是 human review
  completion。

28. Local row access-log route 已納入 work-order、operation-record audit、consistency audit：

- Source:
  `80_semantic_risk_asr/annotation/review_human_risk_atom_audit.py`、
  `80_semantic_risk_asr/annotation/build_human_audit_review_work_order.py`、
  `80_semantic_risk_asr/annotation/audit_human_audit_operation_records.py`、
  `80_semantic_risk_asr/scoring/audit_evidence_chain_consistency.py`。
- New check: `C081`。
- Current tracked outputs:
  `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_review_work_order_summary.json`、
  `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_review_work_order.tsv`、
  `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_operation_record_summary.json`、
  `70_experiments/runs/postdoc_evidence_chain_2026_05_25/evidence_chain_consistency_summary.json`。
- Current state:
  work-order local row-open command 已包含 `--access-log
  70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_local_row_access_log.tsv`；
  operation-record summary 記錄 `route_ok=true`、
  `status=planned_not_yet_recorded`、`exists=false`、`row_count=0`、
  `required_fields_present=false`、`latest_record_ok=false`；access-log file
  尚不存在，因為這一輪沒有開啟任何 transcript-bearing row。
- 檢查內容：`C081` 要求 local-only `--show-row` command 在印出
  transcript-bearing row content 前，先有 repo-safe access-log route。Log
  schema 只記錄 row number、selection stratum、reference label、hypothesis
  count、model-assessment count、access status 和 audit sheet path；不記錄
  audio IDs、transcripts、hypotheses、selected sample IDs、local row content
  或 reviewer notes。現在同一個檢查也區分兩種合法狀態：尚未開 row 時必須是
  explicit planned state；如果 access-log file 已存在，latest row 必須是
  `show_local_row`、`access_status=shown`，且 row number 必須對齊下一個
  local row-open operation。這是 local row-access provenance guardrail，不是
  human review completion。

目前最重要的下一步：

- 258-row 現在是 scope-controlled split/model-comparison evidence；
  selected-300 proxy outputs 是 input provenance；paper-grade risk/recovery
  claims 由 selected-300 human-reviewed predictor/recovery outputs 支撐。
- Evidence-chain readiness gate 已建立：
  `80_semantic_risk_asr/scoring/check_evidence_chain_readiness.py`。目前輸出
  `ok=true` 且 `paper_ready=true`，因為 selected-300 human audit 已是
  `30/30` risk/decision row reviews、`90/90` model assessments reviewed；
  transcript ground truth 不是重新審查項目。這個 gate 是維持 scoped
  paper-claim boundary 的主要 guardrail。
- 2026-05-25 WER audit 確認：舊推論欄位是 raw whitespace WER，
  公式形式正確但不適合作為未斷詞中文主指標；最新 audit 已用 canonical
  manifest 驗證 legacy 15-row、六個 258-row run、三個 high-stakes 300-row
  run，並用 `jiwer` 交叉驗算 zh-jieba corpus WER。這次重檢也補上
  zero-reference-unit gate；目前所有 audit profile 都是 `0`。在重新擔心
  WER 數據異常後，已再次重跑 15-row、258-row、300-row audit，三個 TSV
  revalidation outputs 都與 tracked audit TSV byte-for-byte 相同。投稿主表
  應用 aggregate `cer_zh_micro` 欄位，`wer_zh_jieba_micro` 只能作為補充指標。
  新增 journal-compliance gate 後，結論更明確：paper reporting 在
  `cer_zh_micro` primary、`wer_zh_jieba_micro` supplemental 的政策下合規；
  但舊 `metrics.csv` stored WER 欄位不是全部合規，只能保留作 provenance /
  audit-only。
- Ground-truth transcript 邊界：manifest/reference transcripts 已視為經過
  human review 的 WER/CER scoring reference；除非新的人工審查欄位不是這些
  transcript 欄位與內容，否則不要重開 transcript 人審。selected-300 的
  risk-atom、decision-change、per-model assessment、review timing 已完成。
- Whisper large-v3、large-v3 turbo、SenseVoice、Qwen3-ASR、Gemma 4 audio
  候選已加入矩陣。Whisper large-v3 / turbo、SenseVoiceSmall、
  Qwen3-ASR-0.6B 都已有固定小 gate evidence；Qwen3-ASR-1.7B 仍是
  fetch/load timeout；Gemma 4 E2B/E4B 仍是 multimodal runtime-class gate
  blocked。沒有任何新增候選應在 strict zh-TW locale 或 runtime policy
  解決前升到 258-row。
- 300 high-stakes ASR hypotheses、SRES/CEIS/downstream、metric-predictor、
  recovery 都已完成三個 Breeze-family comparator 的 main evidence path。
  Human-reviewed predictor 與 human-reviewed recovery outputs 已完成並通過
  post-review sequence；validator、refresh、readiness、publishable、
  consequence、roadmap、objective requirements、consistency gates 均已對齊。
  Response closeout summary currently reports `response_complete_ready_to_write`
  with zero row/model/timing gaps, and post-review sequence reports
  `post_review_sequence_complete`。

26. Original-objective audit 已改成 sequence-aware completion audit：

- `80_semantic_risk_asr/scoring/audit_postdoc_objective_requirements.py`
  現在讀取 `human_audit_post_review_sequence_summary.json`。
- Requirement `6.3` 記錄 `recovery_human_ready=True`、
  `post_review_sequence_status=post_review_sequence_complete`、
  `post_review_sequence_ok=True`。
- Top-level `next_decision` 現在指向 scoped paper claims：write/refresh、
  human predictor refresh、strict human-reviewed recovery、post-review
  checklist、objective audit 的順序已被記錄並完成。
- Current state 是 `objective_requirements_ready=true`、`satisfied=15`。
  新增
  `human_audit_reviewer_handoff_summary.json` 把 current packet、response TSV、
  batch gate、apply-log status、下一步 commands 聚合成一個 safe handoff；
  目前 handoff status 是 `reviewer_input_pending`，且
  `freshness_status=fresh`。這個 handoff 也記錄每個 source summary 的
  SHA-256 digest；reviewer 開始前先跑
  `build_human_audit_reviewer_handoff.py --check-existing`，要求回報
  `handoff_fresh`，再跑
  `preflight_human_audit_review_session.py` 留下 aggregate-only session-start
  record；這些 workflow records 現在作為完成後 provenance 使用。
  嚴格 `--require-complete` refresh 已通過，local sheet write、current batch
  status、aggregate refresh、readiness、publishable completion 已在 recorded
  pass 中更新。
- 258-row recovery proxy、300-row high-stakes recovery proxy、selected-300
  human-reviewed recovery 都已完成；下一個工作是論文寫作、citation 補強、
  artifact packaging，而不是再調 WER 定義。

## FIRST PRINCIPLE

稀缺資源不是 GPU time，也不是更多模型參數。稀缺資源是：

1. 可追溯的 split-level evidence；
2. 能說服審稿人的 decision-stability 指標；
3. 能證明 intervention 有用的 recovery 結果；
4. 不洩漏敏感音檔、逐字稿、候選 ID、模型權重的 repo-safe 記錄。

因此所有下一步都要遵守同一個決策規則：

- 沒有通過 smoke，就不跑 15-row。
- 沒有通過 15-row hypothesis contract，就不跑 258-row。
- 沒有 aggregate runtime / locale / validation record，就不進論文表格。
- 沒有 split-aware metric builder，就不跑 300-row main experiment。
- 沒有 recovery baseline，就不要宣稱 CDS-ASR 是完整系統貢獻。

## Phase 1: 先補齊 258-row 可比較 baseline

### 目的

目前 258-row 已比較 legacy partial encoder、legacy LoRA、Breeze-ASR-25
base、Breeze-ASR-26、Whisper small、Whisper large-v2。這足以支持 partial
encoder 仍是下一個 hypothesis generator，但還不足以做正式 paper table。
正式比較還需要：

- Whisper large-v3；
- Whisper large-v3 turbo；
- candidate-family runner gates for SenseVoice、Qwen3-ASR、Gemma 4 audio。

### 操作順序

1. Whisper large-v3 與 large-v3 turbo 已完成 1-row smoke 與 15-row
   contract；兩者 hypothesis contract 通過，但 locale gate 不是 clean，因此
   暫時不升 258-row。
2. SenseVoiceSmall 與 Qwen3-ASR-0.6B 已於 2026-05-26 補跑固定 15-row；
   兩者 hypothesis contract 通過，但 strict zh-TW locale gate failed，因此
   也暫時不升 258-row。
3. Qwen3-ASR-1.7B 已做 60 秒 bounded load retry，仍停在 fetch/load，未進
   inference；下一步不是擴大實驗，而是先有 isolated cache/download plan。
4. 所有 run 都使用同一個 manifest：
   `40_breeze_asr25_finetune_dataset/manifests/test.jsonl`。
5. 所有 run 都使用同一個 locale rule：
   `zh-TW` Taiwan Traditional Chinese output only。
6. 每個 run 都要通過：
   `validate_janus_asr_hypotheses.py --expected-manifest 40_breeze_asr25_finetune_dataset/manifests/test.jsonl --expected-rows 258 --require-labels --require-quality-signal`。
7. 完成後重跑：
   `summarize_janus_asr_test_split.py`。

### 必須記錄的資料

每個 258-row run 至少要記：

- model id；
- run id；
- git commit；
- manifest path；
- gold/source join table；
- runtime；
- device；
- dtype；
- cuDNN 是否 disabled；
- wall time seconds；
- seconds per row；
- rows per second；
- model load time，如果 runner 能拆出來；
- peak GPU memory，如果能取到；
- CER；
- WER：必須標明 tokenizer / normalization / macro or micro；舊 raw
  whitespace WER 只能作為 legacy audit field；
- unsafe downrouting count；
- high-risk missed count；
- over-escalation count；
- risk atom proxy error；
- negation flip rate；
- amount distortion rate；
- action confusion rate；
- actor confusion rate；
- scam-pattern confusion rate；
- simplified character count；
- simplified character rate；
- locale violation rows；
- validator result；
- interpretation；
- next gate decision。

### 完成條件

- `70_experiments/registry.tsv` 有每個 258-row run 的 aggregate row。
- raw predictions、runtime logs、validation JSON 仍在 ignored local path。
- tracked repo 只留下 aggregate TSV/JSON、README、metrics、分析。
- 產出一張 paper-facing table draft，明確顯示 CER/WER 與 decision metrics
  不一定一致。

## Phase 2: 建立新模型候選的 runner gate

### 目的

新模型不是用來堆 leaderboard，而是測「不同 ASR family 是否改變
decision-stability evidence」。

候選模型：

- `openai/whisper-large-v3`
- `openai/whisper-large-v3-turbo`
- `FunAudioLLM/SenseVoiceSmall`
- `Qwen/Qwen3-ASR-0.6B`
- `Qwen/Qwen3-ASR-1.7B`
- `unsloth/gemma-4-E2B`
- `unsloth/gemma-4-E4B`

### Whisper large-v3 / turbo

優先原因：

- 最容易接上現有 Transformers runner；
- 可補齊 reviewer 會期待的 strong Whisper baseline；
- large-v3 turbo 可以提供速度/品質 tradeoff。

2026-05-25 current status：

- `openai/whisper-large-v3` 1-row CUDA smoke 已通過，`zh_asr` + `jieba`
  metric、float16、cuDNN disabled、locale violation rows `0`，wall time
  `271.91s`。
- `openai/whisper-large-v3-turbo` 1-row CUDA smoke 已通過，locale
  violation rows `0`，wall time `144.77s`。
- `openai/whisper-large-v3` 15-row gate 已通過 hypothesis contract；CER
  `33.77`、WER `43.18`、wall time `14.59s`，但 locale violation rows `2`。
- `openai/whisper-large-v3-turbo` 15-row gate 已通過 hypothesis contract；CER
  `41.33`、WER `52.52`、wall time `7.68s`，但 locale violation rows `4`。
- 這些結果證明 runner/contract feasibility，但因為 strict Taiwan
  Traditional Chinese gate 不 clean，暫不進 258-row 或論文主表。

下一步只在我們明確接受 audited post-decode conversion/reporting policy，或
找到能讓 locale gate clean 的解碼策略時才做 258-row。

### SenseVoice

研究價值：

- 代表非 Whisper/Breeze family；
- 可以測快速 ASR 是否犧牲 decision stability；
- 需要明確記錄 VAD、ITN、batching、toolkit version。

完成條件：

- SenseVoice runner 已新增：
  `60_whisper_asr_finetuning/scripts/run_janus_sensevoice_pilot.py`。
- `funasr 1.3.3` / `modelscope 1.37.1` 已明確記錄安裝。
- 1-row smoke 已通過 hypothesis contract；CER `65.88`、WER `81.25`、
  cached runner wall time `2.15s`。
- 但 strict locale gate failed：locale violation rows `1`、simplified
  character count `11`。
- 2026-05-26 固定 15-row 已完成：CER `63.83`、WER `79.97`、runner wall
  time `2.60s`、outer wall time `6.32s`，hypothesis contract 通過。
- 15-row strict locale gate failed：locale violation rows `14`、simplified
  character count `209`。
- 下一步不是 258-row；下一步是先設計並審核繁中輸出控制或 post-decode
  reporting policy，否則從 pure-ASR paper table 排除。

### Qwen3-ASR

研究價值：

- 測較新 ASR family 對台灣繁中電話語音的可行性；
- `0.6B` 先測 install/runtime/latency；
- `1.7B` 只有在 `0.6B` runner 穩定後才跑。

完成條件：

- 官方 `qwen-asr 0.0.6` 已明確記錄安裝。
- Qwen3-ASR runner 已新增：
  `60_whisper_asr_finetuning/scripts/run_janus_qwen3_asr_pilot.py`。
- `Qwen/Qwen3-ASR-0.6B` 第一次 CUDA attempt 因
  `CUDNN_STATUS_SUBLIBRARY_VERSION_MISMATCH` 失敗；停用 cuDNN 後 1-row
  smoke 通過 hypothesis contract。
- 0.6B 結果：CER `74.12`、WER `95.83`、cached runner wall time `6.45s`、
  locale violation rows `1`、simplified character count `13`。
- 2026-05-26 固定 15-row 已完成：CER `64.93`、WER `82.70`、runner wall
  time `17.97s`、outer wall time `21.57s`，hypothesis contract 通過。
- 15-row strict locale gate failed：locale violation rows `15`、simplified
  character count `260`。
- `Qwen/Qwen3-ASR-1.7B` 2026-05-26 bounded retry 仍停在 model file
  fetch/load；60 秒 timed gate 的 exit status 是 `124`，未進 inference。
- 2026-05-26 08:25 CST 再跑 bounded 60 秒 load gate，結果仍是
  `Fetching 2 files: 0/2` 後 timeout；elapsed `60.07s`、exit status `124`、
  未進 inference、沒有新增 prediction 檔。
- 下一步不是 258-row；下一步是先解決繁中 locale gate，或建立 isolated
  cache/download plan 後才重試 1.7B。

### Gemma 4 E2B/E4B multimodal

這兩個不能當成純 ASR baseline。它們應該被定義成 prompted multimodal
ASR / decision-text comparator。

必須先設計：

- prompt；
- max audio length；
- hallucination/repetition detector；
- verbosity constraint；
- locale gate；
- refusal / non-transcription handling；
- output cleaning rule。

完成條件：

- 不把 Gemma output 混入純 ASR baseline table；
- 另開 multimodal prompted-ASR table；
- 只在 prompt/locale/runtime contract 清楚後跑 15-row。

2026-05-25 runner gate：

- 本機 `transformers 4.57.6` 不提供 `AutoModelForMultimodalLM`；
- `unsloth/gemma-4-E2B` 與 `unsloth/gemma-4-E4B` config 宣告
  `transformers_version=5.5.0.dev0`，且有 audio config；
- 因此 Gemma 4 是 runtime blocked，不是 evaluation completed；
- 2026-05-26 08:25 CST recheck：本機 `transformers 4.57.6` 仍沒有
  `AutoModelForMultimodalLM` / `Gemma4ForConditionalGeneration`，而且
  `AutoConfig.from_pretrained(..., trust_remote_code=True)` 仍無法辨識
  `model_type=gemma4`；
- 下一步是獨立建立 Gemma 4 multimodal runtime，不要污染純 ASR baseline。

## Phase 3: 把 15-row builder 泛化成 split-aware metric builder

### 目的

目前 `build_janus_pilot_metric_inputs.py` 是 pilot-first。下一步不能把
258-row 或 300-row 硬塞進 pilot script；應該新增或重構成：

```text
80_semantic_risk_asr/scoring/build_janus_metric_inputs.py
```

建議 CLI：

```bash
.venv/bin/python 80_semantic_risk_asr/scoring/build_janus_metric_inputs.py \
  --split test \
  --gold-review <review_or_source_table.tsv> \
  --manifest <manifest.jsonl> \
  --hypotheses <model_a_predictions.jsonl> \
  --hypotheses <model_b_predictions.jsonl> \
  --output-dir <run_dir>/artifacts/metric_inputs
```

支援 split：

- `pilot_15`
- `test_258`
- `high_stakes_300`

### 設計重點

新 builder 應該拆開兩種模式：

1. human-reviewed mode：
   - 有 `human_verified_transcript`；
   - 有 `semantic_risk_label`；
   - 有 `risk_atoms`；
   - 有 `would_asr_error_change_decision`；
   - 可正式跑 SRES / CEIS / downstream。
2. proxy mode：
   - 只有 reference transcript 或 heuristic label；
   - 可產出 proxy risk-atom summary；
   - 不能在論文中說成 human-reviewed CDS evidence。

### 完成條件

- `build_janus_pilot_metric_inputs.py` 保留或變成 wrapper；
- 新 script 能處理不同 split；
- missing IDs、duplicate IDs、missing text、missing labels 都會 fail fast；
- output metadata 寫清楚 `human_reviewed=true/false`；
- 15-row 舊結果可重現；
- 258-row 可用同一套 interface 產出 metric inputs。

## Phase 4: 建立 human-reviewed risk-atom audit set

### 為什麼這一步很重要

這是目前最容易被忽略、但審稿人會在意的缺口。258-row proxy metrics
可以支持工程判斷，但如果要做論文主張，至少要有一個較小的人審
risk-atom audit set。

建議不要直接人工審 300 rows。先做分層 audit：

- 15-row gold set：已完成；
- 30-row 258-test audit：從 258-row 中抽高風險、高 disagreement、low-CER/high-risk-error cases；
- 30-row 300-high-stakes audit：從 selected 300 中抽最可能造成決策改變的 cases。

### 標註欄位

每列至少要有：

- `audio_id`
- `human_verified_transcript`
- `semantic_risk_label`
- `risk_atoms`
- `critical_atoms`
- `asr_confusion_terms`
- `would_asr_error_change_decision`
- `decision_change_reason`
- `expected_safe_action`
- `annotation_confidence`
- `reviewer_notes`

### 完成條件

- audit set 放在 local/ignored path，tracked 只放 aggregate annotation stats；
- 寫一份 repo-safe annotation protocol；
- 能回報 risk atom coverage 與 disagreement types；
- 若有第二 reviewer，至少抽 10 rows 做 agreement check。

## Phase 5: 把 300 high-stakes expansion 變成主實驗

### 目的

300 rows 不是 ASR benchmark，而是 paper main experiment。它要回答：

1. CER/WER/SRES/CEIS 哪個最能預測 downstream label flip？
2. CEIS 是否能抓出 low-CER danger cases？
3. 哪些 risk atom 最容易導致決策不穩定？
4. partial encoder 的優勢是否在高風險 subset 仍成立？
5. 新 ASR family 是否改變 unsafe downrouting / high-risk missed pattern？

### 操作順序

1. 確認 selected 300 IDs 仍在 ignored artifacts，不進 git。
2. 為 selected 300 建 manifest 或 resolver。
3. 先跑 current primary candidate：legacy partial encoder。
4. 加入必要 comparator：
   - Breeze-ASR-25 base；
   - Whisper large-v3 或 large-v3 turbo；
   - legacy LoRA；
   - 其他只有在 258-row 有價值才加入。
5. 用 split-aware builder 產出 SRES/CEIS/downstream inputs。Done in proxy
   mode on 2026-05-25.
6. 跑 scoring。Done in proxy mode on 2026-05-25.
7. 產出 aggregate tables。Done for ASR, SRES/CEIS/downstream, recovery, and
   metric-predictor proxy gates.
8. 建立 selected-300 human risk-atom audit subset。
9. 用 human-reviewed subset 重跑 metric predictor analysis。

### 主實驗 metric

- downstream label flip；
- false safe rate；
- unsafe downrouting rate；
- high-risk missed rate；
- critical miss rate；
- CEIS mean/max/top decile；
- low-CER/high-CEIS count；
- risk atom category breakdown；
- model family breakdown；
- runtime and throughput；
- locale violations；
- abstention/recovery eligibility。

### 完成條件

- 300-row run record 有完整 commands、runtime、validation、aggregate metrics；
- 300-row raw predictions 不進 git；
- 至少產出三張 paper-facing table：
  1. ASR quality vs decision metrics；
  2. risk atom error breakdown；
  3. low-CER/high-CEIS failure cases aggregate。

### 目前 proxy gate 狀態

2026-05-25 已完成 selected-300 proxy metric predictor gate：

- Script:
  `80_semantic_risk_asr/scoring/analyze_metric_predictors.py`。
- Run record:
  `70_experiments/runs/janus_300_high_stakes_metric_predictor_proxy_2026_05_25/`。
- Input: partial encoder、Breeze-ASR-25 base、legacy LoRA 三個 selected-300
  hypothesis families。
- Rows: `900` model-samples。
- Aggregate-only outputs:
  `metric_predictor_comparison.tsv`、`risk_atom_instability.tsv`、
  `low_wer_danger_summary.tsv`、`metric_predictor_summary.json`。

Key result:

| Comparison | WER | CER | SRES total | CEIS max |
| --- | ---: | ---: | ---: | ---: |
| AUC for unsafe downrouting | `0.7683` | `0.7739` | `0.9954` | `0.9971` |
| AUC for high-risk missed | `0.6871` | `0.7138` | `0.9826` | `0.9973` |
| AUC for danger event | `0.7629` | `0.7676` | `1.0000` | `1.0000` |

Interpretation:

- WER/CER 已經修正為可審核的中文 ASR 計算政策，但它們仍不是下游安全
  的充分代理指標。
- SRES/CEIS 在 proxy gate 的分辨力很高，表示 risk-aware scoring 是有研
  究價值的路線。
- 但是 SRES/CEIS 目前由 proxy risk rows 產生，不能直接把 AUC `1.0000`
  包裝成 human-reviewed paper claim。
- 下一個 gate 必須是完成 selected-300 human risk-atom audit，而不是再重
  複改 WER 定義，也不是重審已經 human-reviewed 的 transcript ground truth。

## Phase 6: Recovery experiment

### 目的

這是工程貢獻的核心。CDS-ASR 不能只會打分數；它要能降低危險決策。

至少比較五組：

1. no recovery；
2. confidence-only trigger；
3. SRES-triggered recovery；
4. CEIS-triggered conservative action；
5. CEIS + ASR ensemble arbitration。

### Recovery policy design

建議先做保守、可重現的 policy，不要一開始就做複雜 LLM correction：

```text
if CEIS high and risk atom belongs to amount/action/actor/negation:
    abstain or conservative escalation
elif ASR models disagree on high-risk label:
    conservative escalation or manual review flag
else:
    keep original ASR decision
```

Ensemble arbitration 可以先用：

- Breeze-ASR-25 base；
- legacy LoRA；
- legacy partial encoder；
- strongest Whisper baseline。

### Metric

- Critical Miss Rate；
- Unsafe Down-Routing Rate；
- Over-Escalation Rate；
- Machine Abstention Rate；
- Decision Stability Gain；
- Recovery Budget；
- Conservative Escalation Cost；
- latency overhead；
- rows requiring human review。

### 完成條件

- recovery script 可從 metric inputs 直接產出 policy outputs；
- 每個 condition 都有 aggregate table；
- 至少證明 CEIS-triggered policy 比 confidence-only 更能降低 unsafe
  downrouting 或 critical misses；
- 也要誠實回報代價：over-escalation、abstention、runtime。

### 目前 proxy gate 狀態

2026-05-25 已完成第一個 runnable recovery gate：

- Script:
  `80_semantic_risk_asr/recovery/evaluate_recovery_policies.py`。
- Run record:
  `70_experiments/runs/janus_258_recovery_policy_proxy_2026_05_25/`。
- Input: 六模型 258-row split-aware proxy metric inputs。
- Rows: `1548` model-samples。
- Confidence values present: `0`，所以 confidence-only 目前是 no-trigger
  control，不可當作已校準 confidence baseline。

結果：

| Policy | Unsafe downrouting | High-risk missed | Critical miss | Over-escalation | Budget | Abstention |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| no recovery | `187` | `161` | `9` | `8` | `0.0000` | `0` |
| confidence-only | `187` | `161` | `9` | `8` | `0.0000` | `0` |
| SRES-triggered | `34` | `0` | `0` | `9` | `0.1311` | `0` |
| CEIS-triggered | `75` | `41` | `0` | `9` | `0.0969` | `0` |
| CEIS + ensemble | `46` | `12` | `0` | `29` | `0.3230` | `468` |

Interpretation:

- CEIS-triggered conservative action already beats the available
  confidence-only baseline on unsafe downrouting and high-risk misses.
- CEIS + ensemble is stronger on safety counts, but has a much larger
  abstention / review-burden cost.
- SRES-triggered looks strongest on this proxy input, but because the 258-row
  risk-atom rows are proxy-generated, it must not be overclaimed before the
  300-row main experiment and human risk-atom audit.

## Phase 7: 論文封裝

### 建議論文 claim

不要寫：

> We fine-tune ASR for Taiwanese call-center speech.

應該寫：

> We show that transcript-level ASR metrics are insufficient for high-stakes
> conversational decision systems, and introduce CDS-ASR, a decision-stability
> evaluation and recovery framework that identifies and mitigates ASR errors
> that change downstream scam-escalation decisions.

### 必備表格

1. Dataset / split / privacy boundary table。
2. Model comparison table：CER/WER/runtime/locale。
3. Decision-stability table：SRES/CEIS/downstream flips。
4. Low-CER/high-CEIS case category table。
5. Risk atom breakdown table。
6. Recovery comparison table。
7. Ablation table：without CEIS, without risk atoms, without ensemble。

### 必備圖

1. CDS-ASR pipeline diagram。
2. CER vs CEIS scatter plot。
3. Risk atom confusion heatmap。
4. Recovery tradeoff curve：unsafe downrouting vs over-escalation / abstention。

### 必備限制

- private high-stakes call data cannot be released raw；
- proxy 258-row metrics are not identical to human-reviewed risk-atom evidence；
- Chinese WER is weak without a declared segmentation policy and should not be
  the primary surface metric；即使要列 WER，也必須同時列 tokenizer、
  normalization、macro/micro scope、manifest alignment、package versions、
  zero-reference-unit status；
- WER/CER reference transcript 已視為 human-reviewed ground truth；人工審查
  待辦只適用於另行定義的 risk-atom / decision-change / model-assessment 欄位；
- model outputs depend on prompt/runtime/backend settings；
- conservative escalation can increase review burden。

## 最佳下一步順序

如果只能照順序做，建議如下：

1. 完成 selected-300 human risk-atom audit protocol 所產生的 30-row local
   sheet 中「不是 transcript ground truth」的欄位：risk atoms、
   decision-change、expected safe action、confidence、per-model assessment。
   下一步從已準備好的 `clean_control` packet rows `23-26` 開始，
   填寫 ignored local response TSV，用
   `apply_human_audit_batch_response.py --require-complete --require-timing`
   dry-run 到
   `response_complete` 後再用 `--write --refresh-after-write`；若 reviewer
   填完 row/model 欄位，也必須填 review timing 欄位，讓 tracked summary
   保留 aggregate review-time coverage 與 elapsed seconds，並讓 apply log 留下每次
   dry-run/write attempt 與 apply-log summary。正常入口先跑
   `start_human_audit_review_session.py`，確認 `reviewer_session_started`；
   這會刷新 handoff、preflight、rubric/value contract、action checklist，並留下
   aggregate session-start summary/log。之後 strict dry-run/write command 會帶
   `--require-timing --require-session-start-gate`，所以寫入 local sheet 前必須
   對上目前 session-start summary 並完成 timing coverage。每次 session-gated
   strict dry-run 後，跑
   `build_human_audit_response_closeout_checklist.py`，只有
   `response_complete_ready_to_write` 才能進入 write/refresh。若要分步檢查，再看
   `human_audit_reviewer_handoff_summary.json` 取得目前 packet、response TSV
   與正確命令，並在 reviewer 開始前跑
   `build_human_audit_reviewer_handoff.py --check-existing` 確認
   `handoff_fresh`，接著跑
   `preflight_human_audit_review_session.py` 確認 `review_session_ready` 並
   留下 session-start record。再跑
   `build_human_audit_reviewer_rubric.py` 產生 reviewer value contract 並確認
   `rubric_ready`；這個 contract 只固定 risk/decision/safe-action/confidence/risk-atom
   的可用值，不重新審查已接受的 transcript ground truth。再跑
   `build_human_audit_reviewer_action_checklist.py` 產生 aggregate action
   checklist；目前狀態應是 `reviewer_action_ready` 且
   `rubric_status=rubric_ready`，但 `4/4` rows、
   `12/12` model assessments 與 `4/4` required timing rows 仍待填。需要連續產生下一批時加
   `--prepare-next-after-write`。
   這會寫入 local sheet、重跑 batch status audit、並在 `batch_complete` 後刷新
   aggregate readiness / publishable completion。
   現在 `evidence_chain_readiness_summary.json` 與
   `publishable_evidence_completion_summary.json` 都會把
   `reviewer_action_gate.status=reviewer_action_ready` 顯示在最高層：
   current stratum 是 `clean_control`，`4/4` rows 與
   `12/12` model assessments 仍待填，latest apply status 是
   `response_pending`。這代表 reviewer workflow ready，不代表 human audit
   complete。完成 response closeout、write、refresh 之後，還要跑
   `build_post_review_evidence_checklist.py`；目前 status 是
   `post_review_evidence_blocked`，因為 response closeout、human refresh、
   human predictor、paper/publishable/consequence gates，以及 human-reviewed
   recovery evidence 都尚未完成。
2. 跑
   `validate_human_risk_atom_audit.py --require-complete --expected-rows 30`；
   通過後才產出 aggregate human annotation stats，確認沒有 selected IDs 或 transcript
   進入 tracked files。
3. 用 human-reviewed subset 重跑 metric predictor analysis，檢查 proxy
   AUC 是否仍成立。
4. Whisper large-v3 / large-v3 turbo 已做 smoke 與 15-row；因 locale gate
   不 clean，暫不做 258-row。
5. 用新 builder 重現 expanded 258-row proxy bridge。
6. SenseVoice/Qwen3-ASR-0.6B 已補跑 15-row；兩者 contract pass 但
   strict zh-TW locale gate failed，因此不升 258-row。下一步先決定要排除
   這兩個 family，或建立 audited post-decode conversion/reporting policy。
7. 建立 Gemma 4 isolated multimodal runtime gate；只做 prompted multimodal
   table，不混入 pure ASR table。
8. locale gate clean 之後，才將 best additional comparator 加入 300-row
   ASR/CDS proxy lane。
9. 重跑 300-row SRES/CEIS/downstream/recovery/predictor aggregate tables。
10. 產出 paper tables / figures / limitation memo。

## Scope-Focused Work Selection

- Long fine-tuning runs become valuable after the current model-comparison
  table shows a clear ASR-family coverage gap.
- New ASR and multimodal candidates progress through smoke, 15-row contract,
  zh-TW locale gate, and runtime gate before 258-row or 300-row promotion.
- Gemma multimodal outputs belong in a dedicated exploratory multimodal-audio
  lane with its own runtime and hallucination controls.
- CER/WER stay in the ASR fidelity table; safety claims use CDS-ASR,
  decision-stability, human-reviewed predictor, and recovery evidence.
- Raw audio, raw transcripts, selected candidate IDs, runtime logs, raw
  predictions, and model weights stay in ignored local storage.
- Proxy SRES/CEIS values stay labelled as proxy/provenance evidence; reviewed
  selected-300 outputs support paper-grade risk/recovery claims.
- CDS-ASR system claims now use the completed selected-300 human audit and
  human-reviewed recovery outputs as the paper-facing evidence layer.

## 下一個 code gate 狀態

第一個 code gate 已經從 roadmap 轉成實作：

```text
feat: add split-aware JANUS metric input builder
```

完成內容：

- 新增 `build_janus_metric_inputs.py`；
- 保留舊 pilot builder 的相容性；
- 支援 `pilot_15`、`test_258`、`high_stakes_300`；
- 讓 output metadata 標記 `human_reviewed` 或 `proxy_only`；
- 加上 15-row human-reviewed compatibility validation；
- 加上 258-row proxy-mode validation；
- 更新 run log。

這會把 repo 從「已經有幾個成功實驗」推進到「可以穩定產生主實驗」。
下一個實驗 gate 已更新：優先把 scoped paper-ready evidence 寫入 manuscript
與 artifact package；新增模型則先把 strict Taiwan Traditional Chinese
locale gate 與 runtime gate 建乾淨，再依序升級。新增 candidate 的 runtime
gate aggregate record 位於
`70_experiments/runs/asr_candidate_runtime_gate_2026_05_25/`。

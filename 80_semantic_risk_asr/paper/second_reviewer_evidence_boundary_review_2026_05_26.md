# 第二 Reviewer Evidence-Boundary Review

Date: 2026-05-26

Reviewed artifact:

- `80_semantic_risk_asr/paper/manuscript_draft.md`

Review status:

> conditional pass with manuscript revisions

Reviewer conclusion:

> selected-300 人工審查不用重開；稿件可以進入 submission-prep，但需要做 claim tightening、citation completion、method operationalization、limitations 補強。現在不是資料或實驗 gate 卡住，而是論文表述還沒完全達到 reviewer-proof。

## 1. 審查總判定

稿件的主要 evidence boundary 是穩的。它明確把 258-row test split 放在
model-comparison / split evidence，把 selected-300 proxy outputs 放在
provenance / row-selection evidence，把 selected-300 human-reviewed
predictor/recovery outputs 放在 paper-grade risk/recovery evidence。
Reference transcripts 也被鎖定為 WER/CER scoring ground truth，不重開
transcript review。這個邊界是對的。

不建議做的事：

- 重開 selected-300 row-level review。
- 把 transcript-bearing artifacts 放進 repo、README、Slack、ChatGPT 或
  reviewer-visible package。
- 因為 candidate model 好奇心再跑 full-split。
- 把 CEIS recovery 寫成全面優於 SRES。
- 把 258-row proxy risk counts 寫成最終 human-reviewed risk claim。

現在該做的事：

- 把 claims 改成「scoped selected-300 human-reviewed evidence」。
- 補齊 real-world citation 與 access date。
- 補 method 細節，尤其是 CEIS 的 `P(v | audio)`、
  variant generation、RiskAtomWeight、DecisionDistance、threshold selection。
- 補 limitations / threats to validity。
- 修正 Table 3 / Table 4 的詮釋語氣。
- 保留 aggregate-only artifact policy。

## 2. Evidence Boundary 審查

判定：pass。

稿件已經清楚說明三層 evidence chain：

1. 258-row split 是 scope-controlled model-comparison evidence。
2. selected-300 proxy outputs 是 input provenance 與 row-selection evidence。
3. selected-300 human-reviewed predictor/recovery outputs 才是 paper-grade
   risk and recovery evidence。

這個切法能防止 reviewer 把 proxy table 誤讀成最終安全結論。

selected-300 human audit 的狀態也寫清楚：aggregate status 是
`review_complete`，30/30 reviewed rows，90/90 reviewed model assessments。
稿件還明確說 local transcript-bearing audit sheet ignored，review scope 是
risk atoms、decision-change labels、expected safe action、confidence、
per-model assessment fields 與 timing。這符合前面定義的人審完成狀態。

需要小修：

> Human review supplies evaluation labels only. The proposed recovery policies are automatic, aggregate-evaluated policies; no transcript-bearing row content is required for paper-facing claims.

這句應該放在 Results 前，避免 reviewer 以為 human reviewer 是 intervention
pipeline 的一部分。

## 3. Table 1：Main ASR Benchmark 審查

判定：mostly pass，有一個 consistency 風險。

表格本身的數字與文字詮釋一致。Breeze-ASR-25 partial encoder 在六個
comparable 258-row runs 裡有最低 `cer_zh_micro`、最低
`wer_zh_jieba_micro`、最低 unsafe downrouting、最低 high-risk missed，稱為
「strongest current hypothesis generator on the 258-row split」可以成立。

風險點：strict locale gate 的文字可能和 Table 1 衝突。

Method/Reproducibility Layer 寫「Model outputs must pass the strict locale
gate before promotion to larger splits」，但 Table 1 裡 Whisper large-v2 有
1 row locale violation，Whisper small 有 4 rows locale violations，卻仍被列為
comparable ASR baselines。這會被 reviewer 抓。

建議替換：

> New candidate models must pass the strict Taiwan Traditional Chinese locale gate before promotion. Previously completed comparable baselines are retained only as disclosed baselines, with locale-violation counts reported and no promotion claim attached.

## 4. Table 2：Candidate / Exploratory Lane 審查

判定：pass。

Candidate lane 的邊界寫得清楚：Whisper large-v3、large-v3-turbo、
SenseVoiceSmall、Qwen3-ASR-0.6B 只停在 fixed 15-row contract；Qwen3-ASR-1.7B
是 load/fetch timeout；Gemma 4 E2B/E4B 是 local multimodal runtime support
block。稿件也明確說這些模型不進 main ASR benchmark table。

需要小修：

把 Whisper large-v3-turbo 的「Speed/quality feasibility only」改成更精準的
paper language：

> Retain as bounded feasibility evidence only; no split-level or selected-300 claim.

## 5. Table 3：Human-Reviewed Predictor Table 審查

判定：pass，但詮釋需要降火。

內部 arithmetic 一致：

| Metric | TP | FP | FN | Recall | Precision | F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| WER | 9 | 14 | 7 | 0.5625 | 0.3913 | 0.4615 |
| CER | 14 | 32 | 2 | 0.8750 | 0.3043 | 0.4516 |
| SRES | 14 | 13 | 2 | 0.8750 | 0.5185 | 0.6512 |
| CEIS | 16 | 19 | 0 | 1.0000 | 0.4571 | 0.6275 |

重要修正：CEIS 不是每個 threshold metric 都贏。

- CEIS 有最高 AUC：0.9117。
- CEIS 有最高 recall：1.0000。
- CEIS 有 0 false negative。
- SRES 有最高 F1：0.6512，高於 CEIS 的 0.6275。
- SRES 的 false positive 較少：13，比 CEIS 的 19 少。

建議寫法：

> CEIS achieves the strongest AUC and the only zero-false-negative operating point in this scoped audit, while SRES attains the highest best-threshold F1. This supports CEIS as a conservative decision-stability signal rather than a universally dominant classifier.

避免寫：

> CEIS outperforms all baselines.

## 6. Table 4：Human-Reviewed Recovery Policy Table 審查

判定：pass，但 claim 必須更精準。

Table 4 的 budget arithmetic 一致。35/90 = 0.3889；47/90 = 0.5222。
No recovery 與 confidence-only trigger 都是 0 triggered，unsafe downrouting
29、high-risk missed 6、critical miss 1。SRES-triggered recovery、
CEIS-triggered conservative action 都把 high-risk missed 與 critical miss
降到 0，triggered count 都是 35，recovery budget 都是 0.3889。
CEIS ensemble arbitration 也維持 0/0，但 budget 較高，且加入 18 machine
abstentions。

最大的 claim 風險：CEIS recovery 沒有在 Table 4 上獨贏 SRES。

可以說：

> CEIS-triggered conservative action reduces high-risk missed and critical miss counts to zero under the selected-300 human-reviewed boundary.

不能暗示：

> CEIS-triggered conservative action improves over SRES-triggered recovery on high-risk missed, critical miss, trigger count, or budget.

建議寫法：

> At the policy layer, both SRES-triggered recovery and CEIS-triggered conservative action eliminate high-risk missed and critical miss counts at the same 0.3889 budget. CEIS's distinct contribution appears in the predictor layer, where it achieves the highest AUC and zero false negatives at its selected operating point.

## 7. Abstract 審查

判定：方向正確，但需要 scoped language。

建議修兩處。

原句：

> Human-reviewed predictor evidence shows CEIS better aligns with decision change than WER/CER

建議：

> Human-reviewed predictor evidence shows CEIS better aligns with decision change than WER/CER by AUC and reaches a zero-false-negative operating point in the scoped audit.

原句：

> CEIS-triggered action reduces high-risk missed and critical miss counts to zero

建議：

> Risk-triggered recovery policies, including CEIS-triggered conservative action, reduce high-risk missed and critical miss counts to zero under the scoped selected-300 claim boundary.

原因：Table 4 裡 SRES-triggered recovery 也達成 0/0。

## 8. Method 審查

判定：conceptual pass，operational detail 不夠。

CDS-ASR pipeline、risk atom schema、counterfactual variant contract、recovery
policies 都有雛形。Risk atoms 包含 negation、amount、action、actor、time、
intent、uncertainty、scam pattern，和人審方法一致。

要補四個核心定義：

1. `P(v | audio)` 過度暗示有 acoustic likelihood。若實作來自 model
   disagreement、slot alternatives、phonetic confusion 或 proxy plausibility，
   不要寫成真的 acoustic posterior。建議改成：

   > `Plausibility(v | x)` denotes a bounded proxy plausibility score derived from model disagreement, Mandarin phonetic ambiguity, domain-slot alternatives, and available ASR/runtime signals.

2. RiskAtomWeight 要定義來源：人工設定、validation tuned、risk atom class
   mapping，或 equal weights。

3. DecisionDistance 要定義 label space：routine review -> priority review ->
   critical escalation 是否 ordinal；critical miss 的 penalty 是否加權。

4. Threshold selection 要交代。Table 3 有 best threshold，但要說明 threshold
   是同一 90 assessments 上找出，或 frozen from dev/proxy。若是在同一
   evaluation set 上選 best threshold，要寫成 exploratory / diagnostic，不要
   寫成 deployed threshold performance。

## 9. Related Work / Citation 審查

判定：目前是 citation scaffold，還沒 submission-ready。

稿件自己已承認 Introduction 的 real-world claims 需要 final citation 與
access date。這是正確的自我標註。

Reviewer-provided citation anchors to verify before submission:

| Claim area | Source anchor | Review note |
| --- | --- | --- |
| AWS contact-center / speech-to-decision workflow | AWS Amazon Connect conversational analytics documentation and product page | Supports automatic categorization, redaction, contact summaries, and contact-center analytics claims. |
| Taiwan anti-fraud setting | National Police Agency 165 Anti-fraud Hotline page | Supports the official hotline setting, event-detail recording, and public guidance role. |
| Fraud scale | IC3 annual reports and FBI press releases | Use the current official report year and exact number wording before final submission. |
| Semantic ASR metrics | Kim et al. 2021 | Supports the claim that WER can be a weak indicator for downstream NLU tasks. |
| ASD / semantic severity | Rugayan et al. 2023 | Supports semantic metric comparison against WER for human/task-oriented assessment. |
| Confidence-aware ASR correction | Naderi et al. 2024 | Supports LLM post-hoc ASR correction with confidence-based filtering. |

Reviewer-provided source URLs to preserve for citation completion:

| ID | Source candidate | URL |
| --- | --- | --- |
| [1] | AWS Connect conversational analytics documentation | `https://docs.aws.amazon.com/connect/latest/adminguide/enable-analytics.html` |
| [2] | Amazon Connect conversational analytics product page | `https://aws.amazon.com/products/connect/customer/conversational-analytics/` |
| [3] | National Police Agency 165 Anti-fraud Hotline | `https://www.npa.gov.tw/en/app/artwebsite/view?id=8035&module=artwebsite&serno=ed2427e1-de0a-4f6f-8f68-8f83b604e89b` |
| [4] | IC3 Annual Reports | `https://www.ic3.gov/annualreport/reports` |
| [5] | FBI annual internet crime report press release | `https://www.fbi.gov/news/press-releases/fbi-releases-annual-internet-crime-report` |
| [6] | FBI cryptocurrency and AI scams press release | `https://www.fbi.gov/news/press-releases/cryptocurrency-and-ai-scams-bilk-americans-of-billions` |
| [7] | Kim et al. 2021, Semantic Distance | `https://arxiv.org/abs/2104.02138` |
| [8] | Rugayan et al. 2023, Aligned Semantic Distance | `https://www.isca-archive.org/interspeech_2023/rugayan23_interspeech.html` |
| [9] | Naderi et al. 2024, LLM ASR correction | `https://www.isca-archive.org/interspeech_2024/naderi24_interspeech.pdf` |

These URLs are recorded from the reviewer memo as citation candidates. Before
submission, remove tracking query parameters, verify official current wording,
record access dates, and cite through the manuscript's final bibliography
format.

Need before submission:

- final citation format;
- access dates;
- quote-free paraphrases;
- 3-5 additional high-stakes speech decision / selective prediction /
  abstention sources.

## 10. Artifact Availability / Privacy 審查

判定：pass。

稿件清楚寫出 release aggregate run records、validation summaries、metric
tables、paper-facing evidence matrices；raw audio、raw transcripts、
selected row IDs、model hypotheses、transcript-bearing runtime logs、reviewer
response sheets、reviewer notes、model weights 不釋出。這符合高風險語音資料的
privacy boundary。

Operation Records 也只提供 command-level reproducibility，不暴露 transcript
或 row content。這很重要，因為 reviewer 仍能看到 closeout、apply logs、
work order、post-review sequence、operation-record audit 與 consistency audit。

建議補一句 reviewer-facing tradeoff：

> Because transcript-bearing materials may contain sensitive call content, reproducibility is provided through aggregate validation artifacts, operation records, manifest checks, and consistency audits rather than through raw row release.

## 11. Validation Gate / Stop Rule 審查

判定：pass。

稿件列出三個 validation gate commands：roadmap completion、publishable
evidence chain、evidence chain consistency。Expected state 是
`roadmap_complete=true`、`publishable_ready=true`、consistency audit `26/26`
pass。

Stop Rule 也明確說不要跑 new full-split ASR experiments，candidate models
只能在通過 Taiwan Traditional Chinese locale policy 或 isolated Gemma 4
multimodal runtime 後才移動。

唯一建議：

把 `Stop Rule` 改成學術語氣：

> Scope Control for Additional Experiments

## 12. 必補 Limitations / Threats to Validity

正式稿件需要一節 Limitations / Threats to Validity，至少包含：

1. Human-reviewed evidence is scoped to 30 rows and 90 model assessments. It
   supports a focused high-stakes audit claim, not a population-level deployment
   claim.
2. Positive decision-change cases are limited: Table 3 has 16 positive model
   assessments. AUC and threshold behavior should be interpreted with
   uncertainty.
3. Thresholds reported as best thresholds can overstate deployment performance
   unless threshold selection is frozen on a separate development set.
4. Recovery evidence is aggregate-only. This protects privacy, but limits
   external row-level reproducibility.
5. CEIS depends on generated plausible variants and risk atom weights. Missed
   variants or misweighted atoms can affect instability scoring.
6. Taiwan Traditional Chinese locale policy is strict by design. Candidate
   model rejection may reflect deployment-locale mismatch, not universal ASR
   inferiority.
7. Recovery policies reduce high-risk missed and critical miss counts, but
   Table 4 still leaves unsafe downrouting count at 24 after SRES/CEIS
   conservative recovery. Do not imply all safety risk is eliminated.

## 13. 建議直接替換的關鍵句

Abstract final sentence:

> Across the scoped selected-300 human-reviewed audit, CEIS achieves the highest decision-change AUC and a zero-false-negative operating point. In recovery-policy evaluation, risk-triggered policies, including CEIS-triggered conservative action, reduce high-risk missed and critical miss counts to zero under the aggregate-only claim boundary.

Results / Table 3 conclusion:

> CEIS has the strongest AUC and reaches recall 1.0 at the selected threshold, while SRES achieves the highest best-threshold F1. This supports CEIS as a conservative decision-stability signal rather than a replacement for all semantic-risk metrics.

Results / Table 4 conclusion:

> SRES-triggered recovery and CEIS-triggered conservative action both reduce high-risk missed and critical miss counts to zero at the same 0.3889 budget. CEIS ensemble arbitration preserves this 0/0 result while introducing abstention behavior at a higher 0.5222 budget.

Locale policy:

> New candidate models must satisfy the strict Taiwan Traditional Chinese locale gate before promotion. Previously completed comparable baselines are retained only as disclosed baselines, with locale-violation counts reported.

Artifact statement:

> Transcript-bearing files are excluded from release because they may contain sensitive call content; aggregate operation records and consistency audits provide the reviewer-visible reproducibility layer.

## 14. 最終審查清單

可以進投稿前打包的條件：

- selected-300 row-level review 不重開。
- Table 3 補上 CEIS/SRES nuance：CEIS AUC/recall 贏；SRES F1/FP 較好。
- Table 4 補上 SRES 與 CEIS conservative action tie。
- 修正 strict locale gate 與 Table 1 Whisper locale violations 的表面矛盾。
- Method 補 `P(v|audio)` proxy 定義、RiskAtomWeight、DecisionDistance、
  threshold selection。
- Introduction 與 Related Work 補正式 citations 和 access dates。
- 加 Limitations / Threats to Validity。
- Stop Rule 改成學術語氣的 scope-control section。
- Artifact availability 保持 aggregate-only，不放 transcript-bearing
  artifacts。

Final review judgment:

> 稿件的 evidence architecture 是可 defend 的；現在要修的是 reviewer 會攻擊的過度詮釋與方法細節。不要再跑 full-split，不要重開 selected-300 transcript review。

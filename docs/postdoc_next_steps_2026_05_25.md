# 博士後視角的下一步研究路線圖

Date: 2026-05-25

Status: active roadmap after the six-model 258-row gate and WER audit

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
- Current state: `30` audit rows、`0` reviewed rows、`30` pending rows、
  `90` model-level assessments、`0` reviewed model-level assessments。

這表示下一步很明確：不是再產生 proxy table，而是填完 local audit sheet，
包含 row-level 與 per-model reviewer assessment，再用同一支 summarizer 產
出 aggregate human annotation stats。

11. Human-reviewed predictor gate 已建立：

- Script:
  `80_semantic_risk_asr/annotation/analyze_human_audit_predictors.py`。
- Current tracked readiness status:
  `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_predictor_summary.json`。
- Current state: `90` model-level assessments、`0` reviewed、`90` pending。

這支工具會在 review 完成後，把 WER/CER/SRES/CEIS 對上 model-level human
decision-change labels。換句話說，proxy AUC 不能直接進 paper；reviewed
subset predictor table 要由這支工具重算。

目前最重要的限制：

- 258-row 現在是 proxy risk-atom summary，還不是完整 human-reviewed CDS
  evidence。
- 2026-05-25 WER audit 確認：舊推論欄位是 raw whitespace WER，
  公式形式正確但不適合作為未斷詞中文主指標；最新 audit 已用 canonical
  manifest 驗證六個 258-row run，並用 `jiwer` 交叉驗算 zh-jieba corpus WER。
  投稿主表應用 aggregate `cer_zh_micro` 欄位，`wer_zh_jieba_micro` 只能作為
  補充指標。
- Whisper large-v3、large-v3 turbo、SenseVoice、Qwen3-ASR、Gemma 4 audio
  候選已加入矩陣，但尚未有完整 runner、smoke、15-row contract、或
  258-row evidence。
- 300 high-stakes ASR hypotheses、SRES/CEIS/downstream、metric-predictor、
  recovery 都已完成三個 Breeze-family comparator 的 proxy mode；human audit
  queue、aggregate summarizer、human-reviewed predictor gate 已建立，但目前
  `0/30` rows reviewed、`0/90` model assessments reviewed，所以還不能宣稱
  paper-grade main experiment 完成。
- 258-row recovery proxy 與 300-row high-stakes recovery proxy 都已完成；下
  一個缺口是 selected-300 human risk-atom audit，而不是再調 WER 定義。

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

1. Whisper large-v3 與 large-v3 turbo 先做 1-2 row smoke，再做 15-row
   contract，通過後才跑 258-row。
2. 所有 run 都使用同一個 manifest：
   `40_breeze_asr25_finetune_dataset/manifests/test.jsonl`。
3. 所有 run 都使用同一個 locale rule：
   `zh-TW` Taiwan Traditional Chinese output only。
4. 每個 run 都要通過：
   `validate_janus_asr_hypotheses.py --expected-manifest 40_breeze_asr25_finetune_dataset/manifests/test.jsonl --expected-rows 258 --require-labels --require-quality-signal`。
5. 完成後重跑：
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

先做：

1. 1-2 row smoke；
2. 15-row contract；
3. locale gate；
4. 258-row run。

### SenseVoice

研究價值：

- 代表非 Whisper/Breeze family；
- 可以測快速 ASR 是否犧牲 decision stability；
- 需要明確記錄 VAD、ITN、batching、toolkit version。

完成條件：

- 新增 SenseVoice runner；
- 輸出同一個 hypothesis schema；
- 先跑 1-2 row smoke；
- 再跑 15-row；
- 通過 validation 後再決定是否進 258-row。

### Qwen3-ASR

研究價值：

- 測較新 ASR family 對台灣繁中電話語音的可行性；
- `0.6B` 先測 install/runtime/latency；
- `1.7B` 只有在 `0.6B` runner 穩定後才跑。

完成條件：

- runner 能固定輸出繁中逐字稿；
- 不輸出摘要或翻譯；
- runtime、latency、locale violations 都被記錄；
- 15-row contract pass 之後才考慮 258-row。

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
  複改 WER 定義。

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
  the primary surface metric；
- model outputs depend on prompt/runtime/backend settings；
- conservative escalation can increase review burden。

## 最佳下一步順序

如果只能照順序做，建議如下：

1. 完成 selected-300 human risk-atom audit protocol 所產生的 30-row local
   sheet。
2. 產出 aggregate human annotation stats，確認沒有 selected IDs 或 transcript
   進入 tracked files。
3. 用 human-reviewed subset 重跑 metric predictor analysis，檢查 proxy
   AUC 是否仍成立。
4. Whisper large-v3 / large-v3 turbo 做 smoke、15-row、258-row，補強
   reviewer 會期待的 strong Whisper baseline。
5. 用新 builder 重現 expanded 258-row proxy bridge。
6. 做 SenseVoice/Qwen3-ASR smoke 與 15-row runner gate。
7. 將 best Whisper comparator 加入 300-row ASR/CDS proxy lane。
8. 重跑 300-row SRES/CEIS/downstream/recovery/predictor aggregate tables。
9. 產出 paper tables / figures / limitation memo。

## 不建議現在做的事

- 不要再開長時間 fine-tuning，除非現有模型比較證明 ASR family coverage
  不足。
- 不要把所有新模型直接跑 258-row 或 300-row。
- 不要把 Gemma multimodal output 和純 ASR baseline 混成同一張表。
- 不要用 CER/WER 宣稱模型安全性。
- 不要把 raw audio、raw transcripts、selected candidate IDs、runtime logs、
  raw predictions、model weights 放進 git。
- 不要把 proxy SRES/CEIS AUC `1.0000` 寫成 formal human-reviewed evidence。
- 不要在沒有 human risk-atom audit 前，把 CDS-ASR 說成完整防護系統。

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
下一個實驗 gate 是補齊 Whisper large-v3 / large-v3 turbo comparable
baseline，然後用同一個 split-aware builder 重建 expanded metric inputs。

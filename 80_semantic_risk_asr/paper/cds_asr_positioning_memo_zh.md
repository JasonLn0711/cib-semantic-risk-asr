# CDS-ASR 中文定位備忘錄

## 核心升級

論文主軸從 **SRA-ASR: Semantic-Risk-Aware ASR** 升級成
**CDS-ASR: Counterfactual Decision-Stability ASR**。

SRA-ASR 的價值是指出低 WER / CER 的逐字稿仍可能含有高風險語意錯誤。
CDS-ASR 再往前推一步：

> 不只問逐字稿錯了多少，也不只問錯在哪裡；直接問在合理的 ASR
> 替代版本下，最終決策會不會翻盤。

一句話：

> CDS-ASR 不是判斷逐字稿是否漂亮，而是檢查在合理的語音辨識替代版本下，
> 決策會不會翻盤。

投稿 hook：

> A transcript is unsafe when a plausible ASR alternative changes the decision.

## 現實世界問題

語音正在變成決策入口。現代 contact-center AI 已經把通話逐字稿拿去做
sentiment analysis、issue detection、自動分類、摘要、合規監測與即時提醒。
AWS Contact Lens / Amazon Connect Customer 文件可以支撐這個現實問題設定。

反詐騙場景更尖銳。台灣警政署 165 反詐騙專線的官方說明指出，民眾接到
詐騙電話可撥打 165，接線人員會記錄事件細節並提供資訊。FBI / IC3 的
cyber-enabled fraud 統計則支撐詐騙規模正在擴大的問題背景。

論文入口：

> 高風險語音系統的真正危險，不是逐字稿看起來有幾個字錯，而是錯字剛好
> 落在「決策支點」上。

例子：

```text
我沒有匯款
-> 我有匯款

三萬元
-> 三十萬元

我只是想問
-> 我要報案

昨天接到電話
-> 今天接到電話
```

WER / CER 可能很低，但是決策狀態已經變了。

## 現有方法的不足

### WER / CER

傳統 ASR 評估把 substitution、insertion、deletion 幾乎當成同質錯誤。
Kim et al. 已指出，WER 只看 literal correctness，不能充分反映 downstream
semantic correctness。

### Semantic Metrics

Semantic Distance、Aligned Semantic Distance 等方法比 WER 更接近語意與
下游任務表現。Kim et al. 與 Rugayan et al. 都是本論文的重要鄰近工作。

### LLM Correction

LLM post-hoc correction 可以把逐字稿修得更通順。Naderi et al. 用
confidence-based filtering 降低 LLM 對原本正確逐字稿引入新錯誤的風險。

### 仍然沒有打到核心

上述方法都有價值，但主要仍是在修 transcript 或評估 transcript。高風險
場景真正需要的是 decision safety。

缺口句：

> Existing semantic ASR metrics improve over WER by measuring meaning
> preservation, yet they do not explicitly test whether plausible transcription
> alternatives would change a downstream high-stakes decision.

## 方法核心

CDS-ASR pipeline：

```text
Audio
-> ASR transcript + confidence / n-best / token timestamps
-> Risk Atom Extraction
-> ASR Counterfactual Generator
-> Downstream Decision Model
-> Decision-Stability Score
-> Automatic Risk Recovery
```

### Risk Atom

把逐字稿切成會影響決策的「決策原子」。

| Risk atom | 中文例子 | 決策風險 |
| --- | --- | --- |
| Negation | 有 / 沒有、是 / 不是 | 事件狀態翻轉 |
| Amount | 三萬 / 三十萬 / 三百萬 | 損失等級改變 |
| Action | 匯款 / 提款 / 報案 / 詢問 | 案件階段改變 |
| Actor | 銀行 / 警察 / 家人 / 客服 | 詐騙劇本判斷改變 |
| Time | 今天 / 昨天 / 剛剛 / 下週 | 緊急程度改變 |
| Intent | 我只是問 / 我要報案 | 分流與升級改變 |
| Scam pattern | 投資詐騙 / 假檢警 / 解除分期 | 案件類型改變 |

### Counterfactual Variant

不要只看 ASR top-1 transcript。系統要產生「合理可能聽錯」的版本。

```text
原始 ASR：
我今天匯了三萬元給對方

反事實版本：
我昨天匯了三萬元給對方
我今天匯了三十萬元給對方
我今天沒有匯款給對方
我今天只是問匯款的事情
```

Variant 來源：

- Acoustic ambiguity: ASR confidence、token logprob、n-best hypotheses、
  timestamp alignment。
- Mandarin phonetic confusion: 同音、近音、聲調、數字單位、短功能詞。
- Domain ontology: 165-style 詐騙場景中的金額、帳戶、付款方式、詐騙類型、
  來電者身份、是否已轉帳。

### CEIS

新指標：

```text
CEIS(x) = max over v in V(x) [
    P(v | audio) * RiskAtomWeight(v) * DecisionDistance(f(x), f(v))
]
```

直覺版：

```text
CEIS = plausible ASR alternative 的最大決策翻盤風險
```

CEIS 可以和 WER / CER、SemDist、ASD、SRES、confidence baseline 比較。

## Recovery 原則

不要把 human review 當方法。Recovery 必須是機器化流程：

```text
High CEIS span
-> span-level forced alignment
-> constrained re-decoding
-> ASR ensemble arbitration
-> decision interval estimation
-> conservative automatic action
```

例子：

- 金額：在 `三千 / 三萬 / 三十萬 / 三百萬` 等 grammar 內重解碼。
- 否定：在 `有 / 沒有 / 還沒 / 已經` 等候選內重解碼。
- 決策區間：當合理 variants 落在 `review ~ critical_escalation`，就不能輸出
  `no_escalation`。

這仍是自動流程。系統本身承認某個 slot 無法安全決定，並避免把高風險案件
降級。

## 實驗主軸

### Experiment 1: ASR Baseline

比較 Whisper-small、Whisper-large-v2 / LoRA、Breeze-ASR-25。

指標：

```text
WER
CER
Risk Atom Error Rate
Negation Flip Rate
Amount Distortion Rate
Action Confusion Rate
```

### Experiment 2: Counterfactual Generation Quality

指標：

```text
Counterfactual Coverage
Plausible Variant Recall
Risk Atom Coverage
Acoustic Plausibility Score
```

### Experiment 3: Metric Comparison

比較：

```text
WER / CER / SemDist / ASD / SRES / CEIS
```

預測目標：

```text
downstream label changed = yes/no
```

重點 evidence table：

```text
低 WER + 高 CEIS
低 SemDist + 高 CEIS
高 confidence + 高 CEIS
```

### Experiment 4: Automatic Recovery

比較條件：

```text
No recovery
Confidence-only LLM correction
SRS-triggered recovery
CDS-ASR constrained re-decoding
CDS-ASR + decision interval
```

指標：

```text
Critical Miss Rate
Unsafe Down-routing Rate
Over-escalation Rate
Compute Cost
Decision Stability Gain
Automatic Recovery Budget
Machine Abstention Rate
Conservative Escalation Cost
```

## 最終主張

原本說法：

```text
Low-WER transcripts can still contain high-SRS, decision-critical errors.
```

升級後說法：

```text
Low-WER transcripts become unsafe when plausible ASR alternatives produce
different downstream decisions.
```

結論句：

> CDS-ASR reframes ASR evaluation from transcript accuracy to decision
> robustness. In high-stakes call-center conversations, the safest transcript is
> not necessarily the one with the lowest WER; it is the one whose downstream
> decision remains stable under plausible acoustic-semantic alternatives.

## Source Anchors

- AWS Contact Lens documentation:
  https://docs.aws.amazon.com/connect/latest/adminguide/analyze-conversations.html
- AWS conversational analytics:
  https://aws.amazon.com/products/connect/customer/conversational-analytics/
- Taiwan National Police Agency 165:
  https://www.npa.gov.tw/en/app/artwebsite/view?id=8035&module=artwebsite&serno=ed2427e1-de0a-4f6f-8f68-8f83b604e89b
- FBI cyber-enabled fraud / IC3 press release:
  https://www.fbi.gov/news/press-releases/cryptocurrency-and-ai-scams-bilk-americans-of-billions
- Kim et al. 2021:
  https://www.isca-archive.org/interspeech_2021/kim21e_interspeech.html
- Rugayan et al. 2023:
  https://www.isca-archive.org/interspeech_2023/rugayan23_interspeech.html
- Naderi et al. 2024:
  https://www.isca-archive.org/interspeech_2024/naderi24_interspeech.html

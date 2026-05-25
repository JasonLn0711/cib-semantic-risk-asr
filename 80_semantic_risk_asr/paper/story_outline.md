# Paper Story Outline

Canonical detailed design:

- `q1_paper_design.md`

## Proposed Title

When Low WER Becomes Dangerous: Counterfactual Semantic Risk Detection for
Speech-Driven Decision Systems

## One-Sentence Claim

High-stakes ASR should be evaluated by whether downstream decisions remain
stable under plausible transcript alternatives, not by transcript similarity
alone.

## Story Line

### 1. Real-World Problem

Speech is becoming an operational input to contact-center analytics and
decision workflows. Commercial systems already use transcripts for sentiment
analysis, issue detection, categorization, summaries, compliance monitoring,
and real-time alerts. Anti-fraud hotlines also depend on callers describing
events, money movement, identity cues, and urgency.

The risk is not that every word is wrong. The risk is that a small ASR
difference lands on a decision atom:

```text
I did not transfer money.
-> I transferred money.
```

or:

```text
30,000
-> 300,000
```

The WER/CER can be low while the downstream escalation state is no longer safe.

### 2. Existing Work

Prior work already shows that WER is insufficient for downstream semantic
understanding. Kim et al. propose Semantic Distance because WER measures
literal correctness rather than semantic correctness for downstream NLU tasks.
Rugayan et al. show that WER does not provide error-severity information and
that Aligned Semantic Distance can better align with human perception and
downstream NLP tasks. Naderi et al. explore LLM-based ASR post-hoc correction
with confidence-based filtering.

These directions are valuable, but they still mostly evaluate or repair the
transcript.

### 3. Gap

For high-stakes calls, the central question is not only:

> Is the hypothesis close to the reference?

It is:

> Would a plausible ASR alternative change the downstream decision?

Existing semantic metrics can say that two transcripts are meaningfully close or
far. LLM correction can make a transcript more fluent. Confidence filtering can
avoid some harmful corrections. None of these directly asks whether the
decision remains stable under acoustically and semantically plausible
alternatives.

### 4. Proposed View

We propose CDS-ASR:

```text
audio
-> ASR transcript + confidence / n-best / timestamps
-> risk atom extraction
-> plausible counterfactual transcript variants
-> downstream decision model
-> decision-stability score
-> automatic constrained recovery
```

The key move is to shift from transcript accuracy to decision robustness.

### 4.1 Execution Gate

The first empirical unit is the reviewed 15-row JANUS decision-stability pilot,
not the full 4,967-row corpus and not a long Whisper fine-tune. The gate must
show that ASR hypotheses can join back to `audio_id`, expose decision-critical
risk atoms, produce SRES/CEIS/downstream-impact outputs, and yield interpretable
examples.

Current local evidence: the reviewed 15-row gate is complete, and a NeMo Curator
CPU pilot has produced a 15-row `audio_id`-joinable hypothesis file with WER/CER
fields. Its high CER confirms that this pass is only a pipeline/output-contract
check. Whisper small, Whisper large-v2, and Breeze-ASR-25 have now completed
the same fixed 15-row hypothesis pass with CUDA and cuDNN disabled. The first
metric bridge pass produced SRES, CEIS, and downstream-impact outputs for the
three labeled model runs. Breeze-ASR-25 is currently the strongest CER candidate
on this pilot, but the next decision is based on interpretable decision flips
and CEIS cases, not CER alone. Breeze-ASR-26 remains an optional
Taigi/Taiwanese Hokkien stress test, not a direct replacement for the Mandarin
baseline.

Only after that pilot shows a usable decision-stability signal should the study
expand to `300-500` high-stakes segments selected for risk-term coverage, split
balance, duration, health flags, and scam-scenario diversity.

### 5. Contributions

1. A risk atom schema for high-stakes call-center ASR decisions.
2. A counterfactual ASR variant contract that combines acoustic ambiguity,
   Mandarin phonetic confusion, and fraud-domain slot ontology.
3. Counterfactual Escalation Instability Score (CEIS), which measures the
   maximum decision-flip risk among plausible ASR variants.
4. An automatic recovery policy using span-level constrained re-decoding, ASR
   ensemble arbitration, decision intervals, and conservative machine action.
5. An empirical comparison against WER/CER, semantic metrics, confidence-only
   approaches, and SRES.

## Main Research Question

Can counterfactual decision-stability evaluation better identify unsafe ASR
outputs than transcript-similarity metrics in high-stakes anti-fraud
call-center conversations?

## Citation Seed

- AWS Contact Lens / Amazon Connect Customer documentation for the real-world
  contact-center analytics premise:
  https://docs.aws.amazon.com/connect/latest/adminguide/analyze-conversations.html
- AWS conversational analytics product page for transcript-based categories,
  summaries, sentiment, and real-time alerts:
  https://aws.amazon.com/products/connect/customer/conversational-analytics/
- Taiwan National Police Agency 165 anti-fraud hotline page:
  https://www.npa.gov.tw/en/app/artwebsite/view?id=8035&module=artwebsite&serno=ed2427e1-de0a-4f6f-8f68-8f83b604e89b
- FBI 2025 cyber-enabled fraud / IC3 press release:
  https://www.fbi.gov/news/press-releases/cryptocurrency-and-ai-scams-bilk-americans-of-billions
- Kim et al. (2021), "Semantic Distance: A New Metric for ASR Performance
  Analysis Towards Spoken Language Understanding",
  https://www.isca-archive.org/interspeech_2021/kim21e_interspeech.html
- Rugayan et al. (2023), "Perceptual and Task-Oriented Assessment of a Semantic
  Metric for ASR Evaluation",
  https://www.isca-archive.org/interspeech_2023/rugayan23_interspeech.html
- Naderi et al. (2024), "Towards interfacing large language models with ASR
  systems using confidence measures and prompting",
  https://www.isca-archive.org/interspeech_2024/naderi24_interspeech.html

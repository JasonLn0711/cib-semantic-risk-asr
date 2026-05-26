# Citation Seed

These are starting citations for the CDS-ASR paper framing. Expand them with
domain-specific high-stakes ASR, contact-center, medical, financial, and
anti-fraud sources before submission.

Use this file together with:

- `attention_led_introduction_blueprint.md`
- `framing_guardrail.md`
- `story_outline.md`

The introduction should follow this citation-backed sequence:

```text
real-world speech-to-decision problem
-> current solution landscape
-> remaining decision-stability gap
-> CDS-ASR contribution
```

## Real-World Contact-Center Analytics Are Speech-To-Decision Systems

AWS documentation for Amazon Connect Customer Contact Lens says conversational
analytics analyzes customer-agent and customer-conversational-AI conversations
across voice, chat, and email using NLP, including sentiment analysis, issue
detection, and automatic categorization.

- Source: https://docs.aws.amazon.com/connect/latest/adminguide/analyze-conversations.html

AWS also describes AI-powered contact-center analytics that use transcripts,
sentiment analysis, categories, summaries, compliance monitoring, and real-time
alerts. This supports the premise that transcripts are already operational
inputs, not just archival text.

- Source: https://aws.amazon.com/products/connect/customer/conversational-analytics/

## Anti-Fraud Calls Are High-Stakes Decision Inputs

Taiwan's National Police Agency describes the 165 anti-fraud hotline as a place
where fraud-call recipients can call, have incident details recorded, and
receive information. This anchors the paper's anti-fraud call-center setting.

- Source: https://www.npa.gov.tw/en/app/artwebsite/view?id=8035&module=artwebsite&serno=ed2427e1-de0a-4f6f-8f68-8f83b604e89b

The FBI reported that IC3 received `1,008,597` complaints in its 2025 Internet
Crime Report context, with approximately `453,000` cyber-enabled fraud
complaints and losses exceeding `$17.7 billion`. This supports the claim that
fraud triage is a large and growing operational problem.

- Source: https://www.fbi.gov/news/press-releases/cryptocurrency-and-ai-scams-bilk-americans-of-billions

## WER Is Not Enough For Downstream Semantics

Kim et al. (2021) propose Semantic Distance as an ASR evaluation metric because
WER measures literal correctness and can fail to reflect downstream semantic
correctness for intent recognition, slot filling, semantic parsing, and named
entity recognition.

- Source: https://www.isca-archive.org/interspeech_2021/kim21e_interspeech.html
- DOI: `10.21437/Interspeech.2021-1929`

## Semantic Metrics Can Better Reflect Practical Error Severity

Rugayan et al. (2023) evaluate Aligned Semantic Distance against WER and report
that WER does not provide error-severity information, while semantic metrics can
better correlate with human judgments and downstream NLP tasks.

- Source: https://www.isca-archive.org/interspeech_2023/rugayan23_interspeech.html
- DOI: `10.21437/Interspeech.2023-1778`

## LLM Correction Still Remains Transcript-Centered

Naderi et al. (2024) study post-hoc ASR transcript correction using LLMs and
confidence-based filtering to reduce the risk of introducing errors into likely
accurate transcripts. This is a useful baseline, but it still focuses on
correcting transcripts rather than directly measuring decision stability under
plausible ASR alternatives.

- Source: https://www.isca-archive.org/interspeech_2024/naderi24_interspeech.html
- DOI: `10.21437/Interspeech.2024-989`

## Gap For This Paper

The existing literature motivates semantic and downstream-aware ASR evaluation.
CDS-ASR narrows the gap further:

> High-stakes call-center ASR should evaluate whether downstream decisions are
> stable under acoustically and semantically plausible transcript alternatives.

This is different from transcript similarity, general semantic similarity, and
post-hoc transcript correction.

Human-facing drafts should present this as a positive extension:

> Semantic ASR metrics and transcript correction make the evidence chain more
> informative. CDS-ASR adds the high-stakes decision test: whether plausible ASR
> alternatives change escalation, routing, or conservative machine action.

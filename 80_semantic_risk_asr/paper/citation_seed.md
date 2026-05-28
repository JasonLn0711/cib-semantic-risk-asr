# Citation Seed

These are verified citation seeds for the CDS-ASR paper framing as of
2026-05-28. The manuscript bibliography lives in `references.bib`. Before final
submission, re-check source wording, target-journal style, and access dates.

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
detection, and automatic categorization. It also describes real-time and
post-call analytics for customer issues, trends, self-service interactions, and
agent compliance.

- Source: https://docs.aws.amazon.com/connect/latest/adminguide/analyze-conversations.html
- Access date: 2026-05-28
- BibTeX key: `aws_contact_lens_analytics_2026`

AWS also describes AI-powered contact-center analytics that use transcripts,
sentiment analysis, categories, summaries, compliance monitoring, and real-time
alerts. This supports the premise that transcripts are already operational
inputs, not just archival text.

- Source: https://aws.amazon.com/products/connect/customer/conversational-analytics/
- Access date: 2026-05-28
- BibTeX key: `aws_connect_contact_lens_2026`

## Anti-Fraud Calls Are High-Stakes Decision Inputs

Taiwan's National Police Agency describes the 165 anti-fraud hotline as a place
where fraud-call recipients can call, have incident details recorded, and
receive information. This anchors the paper's anti-fraud call-center setting.

- Source: https://www.npa.gov.tw/en/app/artwebsite/view?id=8035&module=artwebsite&serno=ed2427e1-de0a-4f6f-8f68-8f83b604e89b
- Page update date: 2024-10-18
- Access date: 2026-05-28
- BibTeX key: `npa_165_antifraud_hotline_2024`

The FBI reported that IC3 received `1,008,597` complaints in its 2025 Internet
Crime Report context, with cyber-enabled crimes defrauding Americans of nearly
`$21 billion`, approximately `453,000` cyber-enabled fraud complaints, and
losses exceeding `$17.7 billion`. This supports the claim that fraud triage is
a large and growing operational problem.

- Source: https://www.fbi.gov/news/press-releases/cryptocurrency-and-ai-scams-bilk-americans-of-billions
- Publication date: 2026-04-06
- Access date: 2026-05-28
- BibTeX key: `fbi_crypto_ai_scams_2026`
- Report source: https://www.fbi.gov/file-repository/2025_ic3report.pdf
- BibTeX key: `fbi_ic3_2025_report_2026`

## WER Is Not Enough For Downstream Semantics

Kim et al. (2021) propose Semantic Distance as an ASR evaluation metric because
WER measures literal correctness and can fail to reflect downstream semantic
correctness for intent recognition, slot filling, semantic parsing, and named
entity recognition.

- Source: https://www.isca-archive.org/interspeech_2021/kim21e_interspeech.html
- DOI: `10.21437/Interspeech.2021-1929`
- Access date: 2026-05-28
- BibTeX key: `kim2021semanticdistance`

## Semantic Metrics Can Better Reflect Practical Error Severity

Rugayan et al. (2023) evaluate Aligned Semantic Distance against WER and report
that WER does not provide error-severity information, while semantic metrics can
better correlate with human judgments and downstream NLP tasks.

- Source: https://www.isca-archive.org/interspeech_2023/rugayan23_interspeech.html
- DOI: `10.21437/Interspeech.2023-1778`
- Access date: 2026-05-28
- BibTeX key: `rugayan2023asd`

## LLM Correction Still Remains Transcript-Centered

Naderi et al. (2024) study post-hoc ASR transcript correction using LLMs and
confidence-based filtering to reduce the risk of introducing errors into likely
accurate transcripts. This is a useful baseline, but it still focuses on
correcting transcripts rather than directly measuring decision stability under
plausible ASR alternatives.

- Source: https://www.isca-archive.org/interspeech_2024/naderi24_interspeech.html
- DOI: `10.21437/Interspeech.2024-989`
- Access date: 2026-05-28
- BibTeX key: `naderi2024llmconfidence`

## High-Stakes ASR Supports Consequence-Aware Evaluation

Miner et al. (2020) evaluate ASR for psychotherapy and explicitly distinguish
population-level language analysis from individual-level safety monitoring.
This supports the CDS-ASR claim that ASR evidence should be scoped to the
downstream decision use case.

- Source: https://www.nature.com/articles/s41746-020-0285-8
- DOI: `10.1038/s41746-020-0285-8`
- Access date: 2026-05-28
- BibTeX key: `miner2020psychotherapy_asr`

## Selective Prediction And Abstention Support Conservative Action

Chow's reject-option result gives the classical error-reject tradeoff for
recognition systems. This is the conceptual ancestor for conservative machine
action when prediction risk is high.

- Source: https://research.ibm.com/publications/on-optimum-recognition-error-and-reject-tradeoff
- DOI: `10.1109/TIT.1970.1054406`
- Access date: 2026-05-28
- BibTeX key: `chow1970reject`

Geifman and El-Yaniv (2017) adapt selective classification to deep neural
networks and frame risk control through a coverage tradeoff. SelectiveNet
extends this idea with an integrated reject option optimized end to end.

- Source: https://papers.neurips.cc/paper/7073-selective-classification-for-deep-neural-networks
- Access date: 2026-05-28
- BibTeX key: `geifman2017selective`
- Source: https://proceedings.mlr.press/v97/geifman19a.html
- Access date: 2026-05-28
- BibTeX key: `geifman2019selectivenet`

Angelopoulos and Bates present conformal prediction as a distribution-free
uncertainty framework for high-risk settings. This supports the broader
positioning of CDS-ASR as an uncertainty-aware decision-evidence layer rather
than a transcript-only score.

- Source: https://arxiv.org/abs/2107.07511
- Access date: 2026-05-28
- BibTeX key: `angelopoulos2021conformal`

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

# Citation Seed

These are starting citations for the paper framing. They should be expanded
with domain-specific high-stakes ASR, call-center, medical, financial, and
anti-fraud sources before submission.

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

## ASR Errors Affect Downstream SLU

Ruan et al. (2020) frame a standard SLU pipeline in which ASR transforms speech
to text and NLU consumes the text, making downstream NLU susceptible to upstream
ASR errors.

- Source: https://www.amazon.science/publications/towards-an-asr-error-robust-spoken-language-understanding-system

## Gap For This Paper

The existing literature motivates semantic and downstream-aware ASR evaluation.
This paper narrows the gap further: high-stakes call-center ASR should evaluate
whether errors alter decision-critical fields and whether recovery policies
reduce missed escalation or wrong routing.

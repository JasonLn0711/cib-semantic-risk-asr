# Attention-Led Introduction Blueprint

Date: 2026-05-26

This note turns the paper voice into an actionable introduction design. The
goal is a steady article that also gives readers a strong reason to continue:
speech-to-decision systems are becoming operational, and CDS-ASR offers a
decision-stability view that complements transcript-centered ASR evaluation.

## Core Narrative

Use this sequence for the abstract, introduction, cover letter, and talk track:

```text
real-world speech-to-decision workflow
-> cited evidence that the workflow is already operational or near deployment
-> cited solution landscape
-> decision-stability gap
-> CDS-ASR viewpoint
-> evidence chain and scope controls
```

Write the gap as a positive extension:

```text
Existing ASR metrics, semantic ASR metrics, and transcript-correction methods
make ASR evaluation more informative. CDS-ASR adds the high-stakes decision
question: whether plausible transcript alternatives change the downstream
decision.
```

## Problem-First Claim Map

| Introduction move | Claim | Citation or evidence anchor | Paper function |
| --- | --- | --- | --- |
| Real-world setting | Contact-center AI already analyzes voice conversations and transcripts for operational signals. | AWS Contact Lens documentation; AWS conversational analytics page. | Establish that transcripts are decision inputs. |
| High-stakes domain | Anti-fraud hotlines record incident details and provide guidance to victims. | Taiwan National Police Agency 165 anti-fraud hotline page. | Ground the paper in a concrete call-center decision setting. |
| Scale and urgency | Fraud reporting and losses are large enough to justify safer triage infrastructure. | FBI 2025 IC3 reporting context. | Show why safer speech-driven triage matters. |
| Existing ASR metric baseline | WER measures literal correctness and can diverge from downstream semantic correctness. | Kim et al. 2021. | Motivate semantic and downstream-aware ASR evaluation. |
| Existing semantic metric baseline | ASD gives severity-aware and downstream-task-aware ASR evidence beyond WER. | Rugayan et al. 2023. | Position CDS-ASR next to semantic ASR metrics. |
| Existing correction baseline | LLM post-hoc correction with confidence filtering improves transcript repair for suitable ASR settings. | Naderi et al. 2024. | Position recovery baselines fairly. |
| Our contribution | High-stakes ASR also needs a direct test of decision stability under plausible alternatives. | This repo's reviewed selected-300 predictor/recovery evidence and CEIS/SRES analyses. | Define CDS-ASR as the new viewpoint. |

## Four-Paragraph Introduction Skeleton

### Paragraph 1: Real-World Problem

Speech-driven contact-center systems increasingly transform conversations into
operational signals: categories, summaries, alerts, compliance checks, routing,
and escalation cues. In anti-fraud calls, the spoken details include money
movement, negation, actor identity, account status, timing, and caller intent.
These details are decision atoms: when they change, the downstream response can
change as well.

Citation anchors:

- AWS Contact Lens / Amazon Connect Customer documentation.
- AWS conversational analytics product page.
- Taiwan National Police Agency 165 anti-fraud hotline.
- FBI 2025 IC3 reporting context.

### Paragraph 2: Current Solution Landscape

ASR evaluation has a mature transcript-accuracy baseline, and recent work has
made it more semantic and task-aware. Kim et al. motivate Semantic Distance by
showing that WER focuses on literal correctness while downstream NLU often
depends on semantic correctness. Rugayan et al. show that Aligned Semantic
Distance better captures error severity and downstream task behavior. Naderi et
al. show that LLM-based transcript correction can be guided by confidence
signals to improve selected ASR outputs.

Citation anchors:

- Kim et al. 2021, Interspeech.
- Rugayan et al. 2023, Interspeech.
- Naderi et al. 2024, Interspeech.

### Paragraph 3: Decision-Stability Gap

These lines of work make transcript evaluation and transcript repair stronger.
High-stakes speech-driven decision systems add one more target: a transcript is
operationally safe when plausible ASR alternatives preserve the downstream
decision. A low edit distance, a close semantic embedding, or a fluent
correction can still leave uncertainty around a decision atom such as negation,
amount, action, actor, time, or intent. The research question is therefore
decision-centered:

```text
Would a plausible ASR alternative change the downstream high-stakes decision?
```

### Paragraph 4: CDS-ASR Contribution

We propose Counterfactual Decision-Stability ASR (CDS-ASR), a framework that
extracts risk atoms, generates acoustically and semantically plausible
transcript alternatives, measures decision instability with CEIS, and applies
constrained recovery or conservative machine action for high-risk spans. This
positions WER/CER, semantic metrics, SRES, confidence, and LLM correction as
comparison layers, while the paper's central contribution is the
decision-stability test.

## Claim-Evidence Discipline

Use these rules when drafting:

1. Every real-world claim gets an external citation.
2. Every prior-method summary names what the method enables before stating the
   remaining decision-stability target.
3. Every empirical claim points to a reviewed aggregate run, summary JSON/TSV,
   figure, or table.
4. Every scope boundary is written as claim-evidence alignment.
5. Chinese-language notes use Taiwan Traditional Chinese and positive,
   confident, evidence-led phrasing.

## Phrasing Guide

Prefer:

```text
Semantic ASR metrics make transcript evaluation more task-aware; CDS-ASR adds
an explicit decision-stability test for high-stakes workflows.
```

Prefer:

```text
LLM correction is a valuable transcript-repair baseline. CDS-ASR evaluates the
decision interval that remains when plausible ASR alternatives affect risk
atoms.
```

Prefer:

```text
The paper starts from an operational problem, situates existing ASR evaluation
and correction methods, and then introduces CDS-ASR as the decision-centered
extension.
```

## Citation Seed Links

- AWS Contact Lens / Amazon Connect Customer documentation:
  https://docs.aws.amazon.com/connect/latest/adminguide/analyze-conversations.html
- AWS conversational analytics:
  https://aws.amazon.com/products/connect/customer/conversational-analytics/
- Taiwan National Police Agency 165 anti-fraud hotline:
  https://www.npa.gov.tw/en/app/artwebsite/view?id=8035&module=artwebsite&serno=ed2427e1-de0a-4f6f-8f68-8f83b604e89b
- FBI cyber-enabled fraud / IC3 press release:
  https://www.fbi.gov/news/press-releases/cryptocurrency-and-ai-scams-bilk-americans-of-billions
- Kim et al. (2021), Semantic Distance:
  https://www.isca-archive.org/interspeech_2021/kim21e_interspeech.html
- Rugayan et al. (2023), Aligned Semantic Distance:
  https://www.isca-archive.org/interspeech_2023/rugayan23_interspeech.html
- Naderi et al. (2024), LLM correction with confidence filtering:
  https://www.isca-archive.org/interspeech_2024/naderi24_interspeech.html

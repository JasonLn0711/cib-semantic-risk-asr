# Framing Guardrail

## Do Not Write A Plain ASR Paper

This paper must not be framed as:

- Whisper fine-tuning;
- LoRA on a domain corpus;
- CER/WER improvement by a small margin;
- Taiwan Mandarin benchmark construction;
- post-processing for better transcript quality.

That framing makes the work look like an ordinary ASR paper. Generic ASR is
already strong, benchmark fatigue is real, and reviewers are unlikely to care
about another small transcription-accuracy improvement unless the work changes
the decision problem.

## Correct Frame

The paper is about:

> ASR failure consequence in high-stakes conversational decision systems.

The hook is:

> Low WER can still cause high-risk decision failure.

ASR is a subsystem. The protagonist is not the model. The protagonist is the
downstream failure created when a semantically critical transcript error enters
a high-stakes decision workflow.

## Bad Version

```text
We use Whisper-large-v2 with LoRA on the 165 corpus and improve CER by 2.3%.
```

This is not enough. It sounds like ordinary transcription optimization.

## Good Version

```text
Existing ASR evaluation assumes that transcription errors are largely
interchangeable. In high-stakes conversational decision systems, however, a
small number of semantically critical errors can cause downstream escalation
misclassification. We show that low-WER transcripts can still be operationally
dangerous and propose a semantic-risk-aware ASR evaluation and recovery
framework to identify and mitigate decision-critical transcription failures.
```

## Introduction Rule

The first two pages should prioritize:

- high-stakes conversational decision systems;
- operational downstream risk;
- semantic corruption;
- human review and escalation;
- failure recovery.

ASR should enter as the upstream subsystem where this problem becomes concrete.
Do not start the paper with Whisper, LoRA, or model architecture.

## What Reviewers Should Remember

The one memorable line:

> A transcript can be nearly correct and still operationally dangerous.

The one contribution frame:

> We evaluate ASR by whether its errors can change high-stakes downstream
> decisions, not only by whether its words match the reference transcript.

## Investment Rule

Do not invest the first paper in making transcription slightly more accurate.
Invest it in identifying which transcription errors can break a decision and
which recovery action catches them with acceptable review workload.

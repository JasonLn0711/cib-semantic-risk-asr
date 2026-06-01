# v2.0 ASR Controls: Qwen3-ASR / FireRedASR LoRA Plan

Date: 2026-06-01

Status: `plan_recorded_no_human_review_lora_grid_ready`

This record designs the next ASR-control and fine-tuning experiment lane for:

- `Qwen/Qwen3-ASR-0.6B`
- `Qwen/Qwen3-ASR-1.7B`
- FireRedASR AED / LLM families, with FireRedASR2 treated as a metadata-gated
  newer branch

It is a repo-safe planning and execution record. It does not contain raw audio,
row identifiers, transcripts, references, hypotheses, repaired text, model
outputs, reviewer notes, expert notes, local paths, transcript-bearing logs,
adapter weights, or model cache paths.

## FIRST PRINCIPLE Diagnosis

The previous v2.0 failures show that the scarce resource is clean
claim-evidence alignment, not more model names or larger runs. A model can help
the CDS-ASR research question only if it can produce Taiwan Traditional Chinese
transcripts that remain semantically useful under high-stakes call-center
decisions. Therefore the ASR-control lane must separate four evidence types:

1. raw ASR capability;
2. deterministic Traditional Chinese conversion and Taiwan-term deployment
   repair;
3. automatic no-human semantic-damage proxy;
4. LoRA fine-tuning evidence.

The existing accepted ground-truth transcripts can support training and metric
scoring without new human review. They do not remove the need for leakage
control, locale gates, automatic semantic-damage proxies, and strict train /
validation / test separation.

## Diagnostic And LoRA Rationale Rule

LoRA is not the default response to an imperfect CER/WER score. The first
experiment should be diagnostic whenever the purpose is model selection or
promotion:

```text
runtime validity
-> raw one-row transcript contract
-> raw fixed-15 CER/WER and locale profile
-> Traditional Chinese deployment-repair view
-> automatic semantic-damage proxy
-> subgroup error taxonomy
-> LoRA necessity decision
```

This diagnostic route is not a mandatory precondition for every LoRA experiment.
LoRA may also be run as a bounded intervention probe when the research question
is to measure the result and consequence of fine-tuning itself. In that case,
the run must explicitly record the intervention rationale, expected target,
risk, frozen comparison baseline, and post-LoRA consequence checks before
training starts.

Two LoRA routes are therefore allowed:

1. `diagnostic_triggered_lora`: baseline evidence shows a plausibly learnable
   failure such as stable Simplified Chinese output that survives semantic
   proxy, recurring Taiwan terminology substitutions, consistent English
   abbreviation errors, or repeatable domain lexical omissions.
2. `research_probe_lora`: LoRA is run deliberately to test whether
   fine-tuning helps or harms, even before all larger diagnostics are complete.
   It must stay bounded, local-only, and separately reported as intervention
   evidence, not as a promoted ASR-control result.

Runtime failures, duration-limit failures, semantic hallucination, unstable
empty output, severe low-overlap transcripts, or errors fixed cleanly by
deterministic conversion are not enough by themselves to justify promotion.
They may still motivate a research-probe LoRA only if the expected consequence
test is stated in advance.

## Why These Models

Qwen3-ASR is a focused ASR family rather than a general audio LLM. The current
public model cards describe `0.6B` and `1.7B` variants, Apache-2.0 licensing,
ASR and language identification for 52 languages and dialects, and support for
30 languages plus 22 Chinese dialects. The model card also documents
transformers and vLLM backends, manual local downloads, streaming / offline
inference, and optional forced alignment. This makes Qwen3-ASR the strongest
next ASR-control candidate for Chinese / dialect / code-switching experiments,
but the repo already records that `0.6B` fails the strict zh-TW locale gate and
that `1.7B` still needs an isolated cache/runtime retry.

FireRedASR is a Chinese-centered ASR family. The original FireRedASR public
repo describes AED and LLM variants, Mandarin benchmark strength, Chinese
dialect / English support, and practical usage warnings: AED input is intended
for short audio and LLM input is even shorter. FireRedASR2 extends this family
with VAD, LID, punctuation, Mandarin / 20+ dialects, English, code-switching,
speech, and singing transcription. That makes FireRedASR useful for Taiwan
Mandarin, mixed English terms, and Mandarin-dialect stress tests, but it must
enter through runtime / license / duration gates before any claim.

Sources:

- Qwen3-ASR model card: https://huggingface.co/Qwen/Qwen3-ASR-0.6B
- Qwen3-ASR technical report: https://arxiv.org/abs/2601.21337
- FireRedASR repo: https://github.com/FireRedTeam/FireRedASR
- FireRedASR paper: https://arxiv.org/abs/2501.14350
- FireRedASR2S repo: https://github.com/FireRedTeam/FireRedASR2S

## Current Evidence Before This Plan

| Model | Current repo evidence | Current decision |
| --- | --- | --- |
| Qwen3-ASR-0.6B | 15-row candidate run exists; strict locale failed on all rows | do not promote raw output; enter OpenCC / Taiwan-term repair then LoRA feasibility |
| Qwen3-ASR-1.7B | runtime check exists; timeout before first inference row | isolated cache/runtime retry before 15-row or LoRA |
| FireRedASR-AED | no repo run yet | metadata, license, runtime, one-row, then fixed-15 |
| FireRedASR-LLM | no repo run yet | short-audio runtime gate; likely heavier LoRA/resource boundary |
| FireRedASR2 | no repo run yet | optional metadata-gated newer branch after FireRedASR baseline route |

## Experiment Contract

All outputs are evaluated in two explicitly separated views:

1. `raw_capability_view`: model output exactly as produced, with raw simplified
   character rate and raw CER/WER.
2. `deployment_repair_view`: output after deterministic Simplified-to-
   Traditional conversion, Taiwan lexical normalization, punctuation
   normalization, and approved non-semantic formatting cleanup.

The deployment view may support operational utility claims only if an automatic
semantic-damage proxy is clean. It must not be reported as raw model
capability.

## Main Hypotheses

| Hypothesis | Evidence required | Stop rule |
| --- | --- | --- |
| H1: Qwen3-ASR-0.6B can become a usable zh-TW ASR control after deterministic conversion | fixed-15 deployment view passes locale and does not worsen CER/WER or semantic proxy | stop if locale residuals or semantic blockers remain |
| H2: Qwen3-ASR-1.7B improves raw or repaired quality enough to justify larger gates | one-row runtime success, fixed-15 raw and repaired metrics, clean proxy | stop before fixed-15 if first inference row cannot be produced |
| H3: FireRedASR-AED is an efficient Chinese-ASR control for short Taiwan Mandarin clips | one-row, fixed-15, duration-bound subgroup, repaired locale gate | stop if duration gate or locale gate fails |
| H4: FireRedASR-LLM / FireRedASR2-LLM adds value for code-switching and dialect stress rows | metadata / license / runtime gate, short-audio fixed-15, subgroup proxy | stop if resource or max-duration boundary blocks reproducible runs |
| H5: LoRA can reduce zh-TW locale and critical-term errors without hurting transcript fidelity, or can reveal the consequence of fine-tuning on a bounded probe | intervention rationale, smoke adapter, post-LoRA one-row, fixed-15, automatic proxy, frozen baseline comparison | stop if adapter cannot train/reload, proxy worsens, or consequence cannot be measured |

## Completion Definition

This lane is complete when one of these states is recorded:

1. `asr_control_scoped_survivor`: at least one model/pipeline passes one-row,
   fixed-15 raw/repaired scoring, automatic semantic-damage proxy, limited
   subgroup utility proxy, and LoRA comparison when applicable.
2. `asr_control_no_human_no_winner`: every feasible raw, repaired, and LoRA
   route is stopped by runtime, locale, semantic-proxy, leakage, or resource
   gates, with a final aggregate audit explaining why larger runs remain
   closed.

## What Must Not Happen

- No new human review is implemented.
- No raw audio is tracked.
- No row IDs, transcripts, references, hypotheses, repaired text, model
  outputs, local paths, or adapter weights are tracked.
- No 258-row, selected-300, or paper-facing claim opens from model reputation.
- No LoRA adapter is evaluated on train rows only.
- No OpenCC/Taiwan-term repaired output is mixed with raw capability evidence.
- No LoRA starts only because CER/WER is imperfect. Before LoRA, record either
  a diagnostic-triggered reason or a research-probe reason with expected
  consequence checks.
- No full-grid LoRA sweep runs before one tiny adapter can train, save, reload,
  and pass one-row evaluation.

# v2.0 Failure-Informed Full Completion Roadmap

Date: 2026-06-01

Status: `roadmap_recorded_next_gate_guarded_fixed_15`

This record answers the planning question: from all failed v2.0 multimodal
experiences so far, what exact steps are still required to complete all new
experiments without adding human review.

It is a repo-safe planning and execution record only. It does not contain raw
audio, row identifiers, transcripts, references, hypotheses, repaired text,
model outputs, reviewer notes, local paths, transcript-bearing logs, adapter
weights, or model cache paths.

## FIRST PRINCIPLE Diagnosis

The repeated failures now identify the real bottleneck. The project does not
need a longer model list or immediate larger subsets. It needs each remaining
route to prove that it can answer the CDS-ASR research question before it is
allowed to spend the next unit of GPU, annotation, or reporting budget.

The useful completion path is therefore:

```text
failure cluster
-> targeted non-human repair or bounded runtime route
-> one-row / sentinel proof
-> fixed-15 transcript and zh-TW locale proof
-> deterministic semantic-damage proxy
-> limited Taiwan utility/subgroup proxy
-> final scoped winner or no-winner closeout
```

## Failure Lessons

| Failure cluster | Evidence learned | Next implication |
| --- | --- | --- |
| Qwen repaired output | CER/WER improved, but expert review found semantic and critical-term damage | Do not treat OpenCC/Taiwan-term repair as final transcript evidence; any no-human route must use automatic blocker proxies and stop on residual locale/semantic damage |
| Step LoRA iteration 1 | Adapter training and adapter loading work, but sentinel no-speech/non-speech hallucination remains | Do not repeat the same LoRA intervention; only a changed negative-target design can justify iteration 2 |
| MOSS 4B / MiniCPM / Step sentinel failures | Main failure concentrates on silence, tone, noise, and ASR-boundary behavior | Deterministic acoustic guard is the first repair layer because it targets the observed failure directly |
| Kimi-Audio | Runtime path is blocked by `flash_attn` / CUDA-toolchain dependency | Kimi stays in an isolated external/prebuilt runtime route and cannot bypass one-row or sentinel gates |
| MOSS 8B | Local 16GB single-GPU route is blocked by resource limits | MOSS 8B needs quantized or external-GPU evidence before any quality claim |

## Current Gate

The deterministic acoustic guard route produced three guarded sentinel
survivors under deployment-repair scope:

```text
Step-Audio-2-mini
MOSS-Audio-4B-Instruct
MiniCPM-o 4.5
```

These survivors have not completed the experiment. They have only earned the
next gate:

```text
guarded fixed-15 transcript + zh-TW locale scoring
```

The guarded route remains deployment-repair evidence, not raw model capability.
It cannot open Taiwan utility, 30-row CDS, 258-row, or selected-300 until
fixed-15 and automatic semantic-damage proxy gates pass.

## Completion Definition

All new v2.0 multimodal experiments are complete only when one of these states
is recorded:

1. `scoped_non_human_survivor`: a guarded or fine-tuned pipeline passes
   one-row, sentinel, fixed-15 transcript/locale, automatic semantic-damage
   proxy, and limited Taiwan utility/subgroup proxy, with claim boundaries
   recorded as deployment-repair or fine-tuning evidence.
2. `final_no_human_no_winner`: every feasible no-human route is exhausted or
   explicitly deferred by bounded runtime/resource policy, with a final
   aggregate closeout explaining the failure clusters and why larger CDS-ASR
   gates remain closed.

## What Must Not Happen

- No additional human review is implemented.
- No model advances because it is famous, interesting, or recently released.
- No fixed-15 run happens before one-row and sentinel gates pass.
- No Taiwan utility/subgroup proxy happens before fixed-15 and automatic
  semantic-damage proxy pass.
- No 30-row CDS, 258-row, or selected-300 run happens without a new non-human
  claim-evidence gate that proves the larger run can answer the research
  question.
- No raw model, deployment repair, automatic proxy, and fine-tuning evidence is
  mixed into one undifferentiated claim.

## Required Next Action

The next concrete action is Phase 8 in `full_completion_steps.tsv`:

```text
run guarded fixed-15 transcript and zh-TW locale gates for the three guarded survivors
```

If that gate passes for any survivor, run deterministic automatic
semantic-damage proxy. If every survivor fails fixed-15/locale or the proxy,
close the guarded route and decide whether Step LoRA iteration 2 is still worth
the compute. If LoRA iteration 2 fails sentinel again, write the final
no-human no-winner closeout instead of widening the experiment.

# v2.0 No-Human Final Completion Audit

Date: 2026-06-01

Status: `final_no_human_no_winner`

This final audit closes the no-human v2.0 multimodal completion route defined
in
`70_experiments/runs/v2_0_multimodal_failure_informed_no_human_completion_plan_2026_06_01/codex_goal_prompt.md`.

No additional human review was implemented. Raw audio, row identifiers,
transcripts, references, hypotheses, repaired text, model outputs, expert
notes, reviewer notes, local paths, transcript-bearing logs, adapter weights,
and model cache paths remain outside Git. Git tracks only aggregate summaries,
validators, registry rows, gate decisions, run README files, and artifact
manifests.

## Final Decision

The no-human route has no promoted winner.

The deterministic acoustic guard produced three guarded sentinel survivors:
Step-Audio-2-mini, MOSS-Audio-4B-Instruct, and MiniCPM-o 4.5. Phase 10
guarded fixed-15 and phase 11 proxy evidence then closed the route:

- Step-Audio-2-mini passed fixed-15 output/locale form but failed the automatic
  semantic-damage proxy with `semantic_damage_blocker_rows=77`.
- MOSS-Audio-4B-Instruct failed the fixed-15 zh-TW locale gate with
  `locale_violation_rows=5` and `simplified_char_rate=1.8868`.
- MiniCPM-o 4.5 failed the fixed-15 transcript/locale gate with
  `raw_transcript_like_outputs=14/15`, `locale_violation_rows=14`, and
  `simplified_char_rate=15.2322`.

Taiwan utility/subgroup, human-reviewed 30-row CDS, 258-row, and selected-300
remain closed. The evidence supports a final no-human no-winner conclusion
rather than widening the experiment.

## Claim Boundary

This audit preserves separation among:

```text
raw model capability
deterministic deployment repair capability
automatic proxy capability
fine-tuning capability
runtime/resource feasibility
```

The deterministic guard is useful deployment-repair evidence for sentinel
no-speech / non-speech behavior. It is not sufficient transcript-quality
evidence for CDS-ASR claims.

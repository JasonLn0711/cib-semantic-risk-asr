# Codex Goal Prompt

```text
Using FIRST PRINCIPLE, execute only the fine-tuning readiness gate for the
v2.0 multimodal audio LLM lane in
/home/jnln3799/every_on_git_ubuntu/cib-semantic-risk-asr.

Start from:
- 70_experiments/runs/v2_0_multimodal_repair_chain_completion_audit_2026_06_01/
- 70_experiments/runs/v2_0_multimodal_remaining_completion_plan_2026_06_01/
- 70_experiments/runs/v2_0_multimodal_finetuning_readiness_design_2026_06_01/

Core rule:
- Do not fine-tune immediately.
- Raw audio is never tracked in Git.
- Keep raw model capability, deployment repair capability, and fine-tuned
  adapter capability separate.
- Track only repo-safe aggregate summaries, validators, registry rows, gate
  decisions, and manifest/hash/status records.
- Any audio, transcript-bearing, row-level, adapter-weight, or model-output
  payload stays local or controlled-store unless explicitly redacted/approved.

Execute in order:
1. confirm Qwen repaired pipeline still waits for human semantic-damage review;
2. confirm no behavior-clean repaired sentinel survivor exists;
3. choose at most one future LoRA feasibility candidate, preferring
   Step-Audio-2-mini only if the target is no-speech / non-speech sentinel
   hallucination;
4. write the bounded training question before preparing data;
5. prepare only a local/private payload manifest and tracked hash/status record;
6. freeze pre-training one-row and sentinel baselines;
7. run a tiny LoRA smoke train only after the manifest, baseline, runtime,
   privacy, and stop rules pass;
8. evaluate post-training one-row first, then sentinel controls;
9. promote to fixed-15 only if post-training sentinel reaches 6/6 and
   hallucination_on_no_speech_rows=0;
10. stop and write a no-train decision if any gate fails.

Validation:
- run py_compile and lane validators;
- run TSV width checks;
- run git diff --check;
- run scripts/check_transcript_bearing_leaks.sh;
- commit logical slices separately and push non-force to origin main.
```

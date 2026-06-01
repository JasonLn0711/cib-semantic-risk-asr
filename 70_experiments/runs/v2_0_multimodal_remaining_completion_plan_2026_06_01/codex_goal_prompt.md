# Codex Goal Prompt

```text
Using FIRST PRINCIPLE, finish the remaining v2.0 multimodal new-experiment
closeout in /home/jnln3799/every_on_git_ubuntu/cib-semantic-risk-asr.

Start from these records:
- 70_experiments/runs/v2_0_multimodal_repair_chain_completion_audit_2026_06_01/
- 70_experiments/runs/v2_0_multimodal_remaining_completion_plan_2026_06_01/
- 70_experiments/runs/v2_0_multimodal_batch1_qwen_opencc_locale_repair_2026_06_01/
- docs/model_evaluation_state.md
- docs/v2_0_multimodal_batch1_full_completion_plan.md

Core rule:
- Raw audio is never tracked in Git.
- Repo-safe aggregate experiment records, validators, registry rows, gate
  decisions, run README files, and manifest/hash/status records must be tracked.
- Non-audio row-level or transcript-bearing payloads may be tracked only after
  redaction/approval. Otherwise keep them local or controlled-store and track
  artifact class, count, sensitivity, storage policy, hash/manifest status, and
  supporting gate decision.
- Raw model capability and deployment repair capability must remain separate.
- Do not run fixed-15, Taiwan utility, 30-row CDS, 258-row, or selected-300
  unless the prior gate opens by evidence.

Execute the remaining steps in order:
1. confirm the current closeout state: phases 1-9 complete, no behavior-clean
   repaired sentinel survivor, Qwen repaired pipeline pending human semantic
   review;
2. prepare a local-only Qwen repaired-pipeline human semantic-damage review
   packet from the existing fixed-15 raw/repaired local payloads;
3. track only the packet manifest/hash/status and reviewer instructions in Git;
4. run or apply the human semantic-damage review;
5. if review fails or is declined, write final no-winner stop synthesis and
   close all larger gates;
6. if review passes, run Qwen repaired-pipeline Taiwan utility/subgroup audit;
7. only if Taiwan utility passes, run human-reviewed 30-row CDS for the
   repaired-pipeline question with every artifact labeled repaired-pipeline;
8. refresh ASR controls only if needed for calibration or final framing;
9. only if 30-row CDS produces a stable, licensed, claim-relevant scientific
   winner, run promoted 258-row and then selected-300;
10. if the team approves a new bounded repair design for MOSS/MiniCPM/Step/Kimi
    or MOSS 8B, write the design first, then require one-row and sentinel gates
    before fixed-15 or larger gates;
11. write final synthesis proving either promoted-winner evidence or final
    no-winner stop status;
12. update docs/model_evaluation_state.md,
    docs/v2_0_multimodal_batch1_execution_runbook.md,
    docs/v2_0_multimodal_batch1_full_completion_plan.md,
    docs/v2_0_multimodal_batch1_repair_first_experiment_guide.md,
    70_experiments/registry.tsv, and planning bridge notes;
13. run py_compile, validators, TSV width checks, git diff --check, and the
    transcript-bearing leak scan;
14. commit logical slices separately and push non-force to origin main while
    preserving local and remote commits.

Stop rule:
- If Qwen human semantic-damage review is not passed and no new bounded repair
  design is explicitly approved, finish with a final no-winner stop record.
- Do not advance because a model is famous or interesting. Advance only when
  the prior gate proves the next experiment can answer the CDS-ASR research
  question with claim-evidence alignment.
```

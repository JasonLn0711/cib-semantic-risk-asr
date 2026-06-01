# Codex Goal Prompt

```text
Using FIRST PRINCIPLE, complete all remaining v2.0 multimodal new experiments
in /home/jnln3799/every_on_git_ubuntu/cib-semantic-risk-asr.

Start from these records:
- 70_experiments/runs/v2_0_multimodal_batch1_completion_audit_2026_06_01/
- 70_experiments/runs/v2_0_multimodal_batch1_repair_first_design_2026_06_01/
- 70_experiments/runs/v2_0_multimodal_all_new_experiments_completion_plan_2026_06_01/
- docs/v2_0_multimodal_batch1_repair_first_experiment_guide.md

Core rule:
- Raw audio is never tracked in Git.
- Every repo-safe experiment record must be tracked.
- Aggregate summaries, validators, registry rows, gate decisions, repair configs,
  run README files, and artifact manifests must be tracked.
- Non-audio row-level or transcript-bearing payloads may be tracked only after
  redaction/approval. If a payload stays local or controlled-store, track its
  artifact class, count, sensitivity, storage policy, hash/manifest status, and
  supporting gate decision.
- Raw model capability and deployment repair capability must remain separate.

Execute the phases in order:
1. lock governance and tracking policy;
2. create controlled-artifact manifest/hash/status records;
3. run Qwen2.5-Omni OpenCC / Taiwan-term fixed-15 locale repair;
4. run MOSS-Audio-4B sentinel behavior repair;
5. run MiniCPM-o 4.5 sentinel behavior repair with quantized/full-bf16 scope;
6. run Step-Audio-2-mini transcript-contract repair;
7. run Kimi-Audio flash_attn/CUDA-toolchain runtime repair;
8. run MOSS-Audio-8B resource-route repair;
9. rerun one-row and sentinel chains only for repaired survivors;
10. run fixed-15 raw and repaired locale gates only for sentinel survivors;
11. run Taiwan utility/subgroup audit only for fixed-15 survivors;
12. run human-reviewed 30-row CDS only for Taiwan-utility survivors;
13. refresh ASR controls only as calibration;
14. run promoted 258-row split only for scientific winners;
15. run selected-300 only for stable, licensed, claim-relevant scientific winners;
16. write final synthesis and closeout audit proving either promoted-winner
    evidence or no-winner stop status.

For every phase:
- inspect git status first;
- preserve local and remote commits;
- keep repo-wide .venv unchanged unless explicitly approved;
- write aggregate-only tracked run records;
- add or update validators;
- update docs/model_evaluation_state.md,
  docs/v2_0_multimodal_batch1_execution_runbook.md,
  docs/v2_0_multimodal_batch1_full_completion_plan.md,
  docs/v2_0_multimodal_batch1_repair_first_experiment_guide.md,
  70_experiments/registry.tsv, and planning bridge notes as needed;
- run py_compile, validators, TSV width checks, git diff --check, and
  transcript-bearing leak scan;
- commit logical slices separately and push non-force to origin main while
  preserving both local and remote commits.

Do not advance to 30-row, 258-row, or selected-300 because a model is famous or
interesting. Advance only when the prior gate proves that the next experiment
can answer the CDS-ASR research question with claim-evidence alignment.
```

# Codex Goal Prompt

```text
Using FIRST PRINCIPLE, complete the v2.0 multimodal new-experiment closeout
without implementing human review in
/home/jnln3799/every_on_git_ubuntu/cib-semantic-risk-asr.

Start from:
- 70_experiments/runs/v2_0_multimodal_repair_chain_completion_audit_2026_06_01/
- 70_experiments/runs/v2_0_multimodal_remaining_completion_plan_2026_06_01/
- 70_experiments/runs/v2_0_multimodal_auto_only_completion_plan_2026_06_01/
- 70_experiments/runs/v2_0_multimodal_batch1_qwen_opencc_locale_repair_2026_06_01/
- 70_experiments/runs/v2_0_multimodal_finetuning_readiness_design_2026_06_01/

Core rule:
- Do not implement human semantic-damage review.
- Raw audio is never tracked in Git.
- Do not track row IDs, transcripts, references, hypotheses, repaired text,
  model outputs, reviewer notes, local paths, transcript-bearing logs, or model
  cache paths.
- Track repo-safe aggregate summaries, validators, registry rows, gate
  decisions, and manifest/hash/status records.
- Keep raw model capability, deployment repair capability, automatic proxy
  capability, and fine-tuning readiness separate.

Execute in order:
1. confirm the no-human-review constraint and current repair-chain closeout;
2. design a deterministic Qwen automatic semantic-damage proxy using only
   local raw/repaired payloads and tracked aggregate counts;
3. the proxy must check at minimum: CER/WER worsened rows, new hallucination
   proxy rows, critical term/proper-noun changes, abbreviation changes,
   suspicious length-ratio changes, empty-output changes, and locale residuals;
4. run the proxy locally and track only aggregate counts plus manifest/hash
   status;
5. if any semantic-damage proxy blocker is nonzero, write final
   auto-only no-winner stop synthesis and keep all larger gates closed;
6. if proxy is clean, run an automatic Taiwan utility/subgroup proxy only under
   a limited repaired-pipeline deployment claim;
7. do not run human-reviewed 30-row CDS, 258-row, or selected-300 unless a new
   non-human evidence design proves claim-evidence alignment first;
8. do not fine-tune immediately. Recheck fine-tuning readiness only if proxy
   fails and the team explicitly wants a bounded LoRA feasibility design;
9. update docs/model_evaluation_state.md,
   docs/v2_0_multimodal_batch1_execution_runbook.md,
   docs/v2_0_multimodal_batch1_full_completion_plan.md,
   docs/v2_0_multimodal_batch1_repair_first_experiment_guide.md,
   70_experiments/registry.tsv, and planning bridge notes;
10. run py_compile, validators, TSV width checks, git diff --check, and
    scripts/check_transcript_bearing_leaks.sh;
11. commit logical slices separately and push non-force to origin main.

Stop rule:
- Without human review, claims must stay automatic-proxy scoped.
- If automatic semantic-damage proxy is not clean, finish with
  auto_only_no_winner_stop.
- Do not advance to larger gates because a model is famous or interesting.
```

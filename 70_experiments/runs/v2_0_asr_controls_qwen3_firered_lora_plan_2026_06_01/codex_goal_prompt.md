# Codex Goal Prompt

```text
Using FIRST PRINCIPLE, complete the v2.0 ASR-control and LoRA experiment lane
for Qwen3-ASR-1.7B / Qwen3-ASR-0.6B and FireRedASR in
/home/jnln3799/every_on_git_ubuntu/cib-semantic-risk-asr.

Start from this planning record:
- 70_experiments/runs/v2_0_asr_controls_qwen3_firered_lora_plan_2026_06_01/

Also preserve the evidence boundaries from:
- 70_experiments/runs/qwen3_asr_0_6b_15_row_candidate/
- runtime/qwen3_asr_1_7b_runtime_check.md
- 70_experiments/runs/v2_0_multimodal_no_human_final_completion_audit_2026_06_01/
- 70_experiments/runs/v2_0_multimodal_step_audio_lora_post_sentinel_controls_2026_06_01/
- docs/privacy_boundary.md
- docs/model_evaluation_state.md

Core rules:
- Do not implement additional human review.
- Use already accepted ground-truth transcripts only through existing
  repo-approved training/evaluation manifests.
- Raw audio is never tracked in Git.
- Do not track row IDs, transcripts, references, hypotheses, repaired text,
  model outputs, expert notes, reviewer notes, local paths,
  transcript-bearing logs, adapter weights, or model cache paths.
- Track every repo-safe experiment record: aggregate summaries, validators,
  registry rows, gate decisions, repair configs, run README files, and
  artifact manifests.
- Keep raw ASR capability, Traditional Chinese deployment repair, automatic
  semantic-damage proxy, and LoRA fine-tuning evidence separate.
- Simplified Chinese output must be converted to Traditional Chinese only in
  the deployment-repair view; raw capability metrics must remain raw.

Execute the phases in order:
1. Refresh model metadata for Qwen3-ASR-0.6B, Qwen3-ASR-1.7B, FireRedASR-AED,
   FireRedASR-LLM, and optionally FireRedASR2 AED/LLM. Record license, weights,
   parameter size, runtime backend, dependency, duration, and training/LoRA
   feasibility. Use primary sources where possible.
2. Build a local-only manifest preflight for the selected fixed-15 and LoRA
   payloads. Git may record only artifact class, count, sensitivity, storage
   policy, hash/manifest status, and split policy.
3. For Qwen3-ASR-0.6B, start from the existing fixed-15 negative evidence.
   Apply deterministic OpenCC Simplified-to-Traditional conversion, Taiwan-term
   normalization, punctuation normalization, and safe formatting cleanup in a
   deployment-repair view. Do not overwrite or relabel raw capability evidence.
4. Run an automatic semantic-damage proxy for Qwen3-ASR-0.6B repaired output.
   Required blockers: CER/WER worsening, critical-term/proper-noun changes,
   abbreviation changes, suspicious length-ratio changes, empty-output changes,
   low-overlap changes, and residual locale violations.
5. For Qwen3-ASR-1.7B, repair the isolated runtime first: local cache, pinned
   revision, explicit timeout, CUDA/GPU environment summary, qwen-asr /
   transformers / torch versions, and one-row inference. No first inference row
   means no fixed-15 and no LoRA.
6. For FireRedASR, run metadata/license/runtime gates before inference. Start
   with FireRedASR-AED short-audio one-row, then FireRedASR-LLM batch_size=1
   one-row only if resource and duration boundaries are clean. Treat
   FireRedASR2 as optional metadata-gated extension after the baseline
   FireRedASR family has evidence.
7. Run raw fixed-15 transcript gates only for models with successful one-row
   inference. Compute raw CER/WER, raw simplified character rate, valid output
   rate, transcript-contract behavior, runtime, and duration boundary.
8. Run deployment-repair fixed-15 gates only after raw fixed-15 exists. Convert
   Simplified Chinese to Traditional Chinese, apply Taiwan-term normalization,
   and keep aggregate repaired metrics separate from raw metrics.
9. Run automatic semantic-damage proxy for every repaired fixed-15 survivor.
   Any blocker stops promotion.
10. Prepare LoRA payload contract only after a model has a clean enough
    baseline question. Use accepted ground-truth training rows only, freeze
    validation/test splits, check leakage, and track only aggregate manifest
    hash/status.
11. Run one smallest LoRA smoke adapter first:
    - Qwen3-ASR-0.6B rank=4 alpha=8
    - Qwen3-ASR-1.7B rank=4 alpha=8 only after one-row runtime success
    - FireRedASR-AED rank=4 alpha=8 only after AED raw/repaired baseline
    - FireRedASR-LLM rank=4 alpha=8 only after short-audio one-row success
12. A LoRA smoke succeeds only if it trains, saves locally, reloads, and passes
    post-training one-row transcript evaluation. No adapter weights are tracked.
13. Expand rank/alpha grid only for smoke survivors:
    - rank 4 alpha 8
    - rank 8 alpha 16
    - rank 16 alpha 32
    - optional rank 16 alpha 16 for alpha sensitivity
    Stop wider ranks when smaller ranks fail semantic proxy or resource gates.
14. Evaluate post-LoRA fixed-15 and automatic semantic-damage proxy against
    frozen raw and repaired baselines. Improvement must preserve transcript
    fidelity and reduce zh-TW locale/critical-term failures without increasing
    semantic blockers.
15. Run limited automatic Taiwan utility/subgroup proxy only for clean
    survivors. Subgroups must include Taiwan terms, English code-switching,
    identity/health/bank/reporting terms, duration, and noisy/low-volume rows
    if available through approved aggregate manifests.
16. Decide whether any survivor earns 30-row CDS, 258-row, or selected-300.
    Do not advance unless the prior gate proves claim-evidence alignment.
17. Write final closeout:
    - scoped ASR-control survivor, or
    - no-human no-winner closeout.
18. Update docs/model_evaluation_state.md,
    docs/v2_0_asr_controls_qwen3_firered_lora_plan.md,
    70_experiments/registry.tsv, and planning bridge notes after each gate.
19. Add validators for every new repo-safe run record. Run py_compile,
    validators, TSV width checks, git diff --check, and
    scripts/check_transcript_bearing_leaks.sh.
20. Commit logical slices separately. Push non-force to origin main only after
    fetching and confirming remote history will be preserved.

Stop rules:
- No model advances because it is famous, new, or benchmark-strong elsewhere.
- No fixed-15 before one-row runtime success.
- No deployment-repair claim without raw baseline and automatic semantic proxy.
- No LoRA grid before one tiny adapter can train, save, reload, and pass
  one-row transcript evaluation.
- No 30-row CDS, 258-row, or selected-300 without clean fixed-15 and semantic
  proxy evidence.
- If Qwen3 and FireRedASR routes all fail runtime, locale, semantic-proxy, or
  LoRA gates, write final no-human no-winner closeout instead of widening.
```

# Codex Goal Prompt

```text
Using FIRST PRINCIPLE, complete all remaining v2.0 multimodal new experiments
without implementing additional human review in
/home/jnln3799/every_on_git_ubuntu/cib-semantic-risk-asr.

Start from these records:
- 70_experiments/runs/v2_0_multimodal_qwen_expert_review_completion_2026_06_01/
- 70_experiments/runs/v2_0_multimodal_step_audio_lora_post_sentinel_controls_2026_06_01/
- 70_experiments/runs/v2_0_multimodal_failure_informed_no_human_completion_plan_2026_06_01/
- 70_experiments/runs/v2_0_multimodal_acoustic_guard_design_2026_06_01/
- 70_experiments/runs/v2_0_multimodal_acoustic_guard_manifest_preflight_2026_06_01/
- 70_experiments/runs/v2_0_multimodal_step_audio_guarded_one_row_2026_06_01/
- 70_experiments/runs/v2_0_multimodal_step_audio_guarded_sentinel_2026_06_01/
- 70_experiments/runs/v2_0_multimodal_moss4_guarded_sentinel_2026_06_01/
- 70_experiments/runs/v2_0_multimodal_minicpm_guarded_sentinel_2026_06_01/
- 70_experiments/runs/v2_0_multimodal_guarded_survivor_audit_2026_06_01/
- 70_experiments/runs/v2_0_multimodal_failure_informed_full_completion_roadmap_2026_06_01/

Core rules:
- Do not implement additional human review.
- Raw audio is never tracked in Git.
- Do not track row IDs, transcripts, references, hypotheses, repaired text,
  model outputs, expert notes, reviewer notes, local paths,
  transcript-bearing logs, adapter weights, or model cache paths.
- Every repo-safe experiment record must be tracked: aggregate summaries,
  validators, registry rows, gate decisions, repair configs, run README files,
  and artifact manifests.
- Non-audio row-level or transcript-bearing payloads may be used only from
  ignored local or controlled-store locations. Git may record only artifact
  class, count, sensitivity, storage policy, hash/manifest status, and gate
  decision.
- Keep raw model capability, deterministic deployment repair capability,
  automatic proxy capability, fine-tuning capability, and runtime/resource
  feasibility separate.

Failure-informed diagnosis:
- Qwen repaired-pipeline output is not promotable after expert review:
  semantic_accept_rows=1/7, semantic_damage_blocker_rows=5/7, and
  hallucination_or_omission_rows=5/7.
- Step-Audio LoRA iteration 1 proves adapter training and adapter loading, but
  does not solve the no-speech/non-speech sentinel target:
  sentinel_pass_rows=3/6 and hallucination_on_no_speech_rows=3.
- MOSS 4B, MiniCPM, and Step failures concentrate on no-speech/non-speech
  hallucination and ASR-boundary behavior.
- Kimi remains a runtime dependency route until flash_attn/CUDA-toolchain is
  bounded and reproducible.
- MOSS 8B remains a resource route until quantized or external-GPU execution is
  bounded and reproducible.

Execute these phases in order:
1. Treat the acoustic guard survivor audit as the current completed gate.
   The guarded fixed-15 candidate pool is Step-Audio-2-mini,
   MOSS-Audio-4B-Instruct, and MiniCPM-o 4.5.
2. Implement or reuse repo-safe guarded fixed-15 runners for only those
   guarded survivors. The guard must run before the audio LLM. The tracked
   record may include only aggregate transcript metrics, locale metrics,
   runtime summaries, manifest/hash/status, gate decision, README, and
   validator output.
3. Do not run Taiwan utility, 30-row CDS, 258-row, or selected-300 from
   guarded survivors until fixed-15 transcript and zh-TW locale gates pass.
4. For any fixed-15 survivor, run deterministic automatic semantic-damage
   proxy. Required blockers include CER/WER worsening, new hallucination
   proxy, critical term/proper noun changes, abbreviation changes,
   length-ratio changes, empty-output changes, locale residuals, and payload
   pairing.
5. If any semantic-damage blocker is nonzero, write a guarded-route no-winner
   stop for that candidate. Do not widen the run.
6. If the automatic proxy is clean, run a limited automatic Taiwan utility and
   subgroup proxy under deterministic deployment-repair scope only.
7. If a guarded route survives utility proxy, write a scoped non-human survivor
   synthesis. The claim must say deployment-repair evidence, not raw model
   capability.
8. If no guarded route survives fixed-15/proxy/utility, decide whether Step
   LoRA iteration 2 is still worth the compute. If yes, design a changed
   intervention with stronger no-speech/non-speech target weighting or
   oversampling. Do not repeat iteration 1 unchanged.
9. Train Step LoRA iteration 2 only after the local payload manifest and
   adapter evaluator contract pass. Track only aggregate metrics and local-only
   adapter hash/status; never track adapter weights.
10. Evaluate LoRA iteration 2 with post-training one-row first, then sentinel.
    Do not run fixed-15 unless sentinel passes 6/6.
11. Optional capacity routes for Kimi and MOSS8 may run only if isolated,
    bounded, reproducible, and repo-safe. They do not bypass one-row or
    sentinel gates.
12. Write the final synthesis as either scoped_non_human_survivor or
    final_no_human_no_winner.
13. Update docs/model_evaluation_state.md,
    docs/v2_0_multimodal_batch1_execution_runbook.md,
    docs/v2_0_multimodal_batch1_full_completion_plan.md,
    docs/v2_0_multimodal_batch1_repair_first_experiment_guide.md,
    70_experiments/registry.tsv, and the planning bridge after each gate.
14. Run py_compile, validators, TSV width checks, git diff --check, and
    scripts/check_transcript_bearing_leaks.sh.
15. Commit logical slices separately and push non-force to origin main.

Stop rules:
- No model advances because it is famous, interesting, or newly released.
- No fixed-15 before one-row and sentinel evidence.
- No Taiwan utility/subgroup proxy before fixed-15 and automatic
  semantic-damage proxy.
- No human-reviewed 30-row CDS, 258-row, or selected-300 unless a new
  non-human claim-evidence gate is explicitly designed and passes first.
- If deterministic guard and changed LoRA iteration 2 both fail sentinel, write
  final no-human no-winner closeout instead of widening the experiment.
```

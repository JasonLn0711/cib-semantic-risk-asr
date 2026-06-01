# Codex Goal Prompt

```text
Using FIRST PRINCIPLE, complete all remaining v2.0 multimodal new experiments
without implementing additional human review in
/home/jnln3799/every_on_git_ubuntu/cib-semantic-risk-asr.

Start from these current evidence records:
- 70_experiments/runs/v2_0_multimodal_batch1_completion_audit_2026_06_01/
- 70_experiments/runs/v2_0_multimodal_repair_chain_completion_audit_2026_06_01/
- 70_experiments/runs/v2_0_multimodal_qwen_auto_semantic_damage_proxy_2026_06_01/
- 70_experiments/runs/v2_0_multimodal_auto_only_no_winner_stop_2026_06_01/
- 70_experiments/runs/v2_0_multimodal_qwen_expert_review_completion_2026_06_01/
- 70_experiments/runs/v2_0_multimodal_step_audio_lora_post_sentinel_controls_2026_06_01/
- 70_experiments/runs/v2_0_multimodal_failure_informed_no_human_completion_plan_2026_06_01/

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
  automatic proxy capability, and fine-tuning capability separate.

FIRST PRINCIPLE diagnosis:
- Qwen repaired-pipeline output is blocked by expert review: 1/7 directly
  acceptable residual rows, 5/7 major critical-term damage, and 5/7
  hallucination/omission.
- Step-Audio LoRA iteration 1 proves adapter training and adapter evaluation,
  but does not solve the target no-speech/non-speech sentinel failure:
  sentinel_pass_rows=3/6 and hallucination_on_no_speech_rows=3.
- MOSS 4B, MiniCPM, and Step repeatedly fail on no-speech/non-speech
  hallucination or behavior-control sentinels.
- Kimi is blocked by flash_attn/CUDA-toolchain dependency.
- MOSS 8B is blocked by local 16GB GPU resource limits.

Execute this route in order:
1. Freeze the current negative evidence and privacy boundary.
2. Design a deterministic acoustic no-speech/non-speech guard before the audio
   LLM. The guard must use audio-only aggregate features and may output only a
   fixed safe transcript such as "無法辨識" for silence/tone/noise classes.
3. Add a repo-safe guard design record and validator. Do not track raw audio,
   row-level payloads, local paths, transcripts, model outputs, or expert notes.
4. Confirm local-only one-row and sentinel manifests remain ignored, and track
   only manifest/hash/status records.
5. Run the guarded Step-Audio one-row transcript-contract gate.
6. If Step guarded one-row passes, run guarded Step sentinel controls.
7. Run guarded MOSS 4B sentinel controls because MOSS 4B already passed one-row
   before sentinel failure.
8. Run guarded MiniCPM-o 4.5 sentinel controls under explicit quantized/full
   bf16 scope.
9. Create a guarded survivor audit. Only models with sentinel_pass_rows=6/6,
   hallucination_on_no_speech_rows=0, no instruction-following, no summary,
   no translation, no TTS-only output, no invented timestamps, and no invented
   speaker labels may advance.
10. For guarded survivors only, run fixed-15 transcript and zh-TW locale gates.
11. For fixed-15 survivors only, run deterministic automatic semantic-damage
    proxy. Required blockers include CER/WER worsening, new hallucination
    proxy, critical term/proper noun changes, abbreviation changes,
    length-ratio changes, empty-output changes, locale residuals, and payload
    pairing.
12. If the proxy is clean, run a limited automatic Taiwan utility/subgroup
    proxy and label the claim as deterministic deployment-repair evidence.
13. If guarded repair has no survivor, design Step-Audio LoRA iteration 2 with
    a changed intervention. Do not repeat iteration 1 unchanged. Use stronger
    no-speech/non-speech target weighting or oversampling, keep accepted
    transcript anchors only for transcript-contract preservation, and track
    only local payload hash/status.
14. Train Step-Audio LoRA iteration 2 only after the payload manifest and
    adapter evaluator contract pass.
15. Evaluate any iteration 2 adapter with post-training one-row first, then
    post-training sentinel. Do not run fixed-15 unless sentinel passes 6/6.
16. Optional capacity lanes: Kimi external/prebuilt flash_attn runtime and
    MOSS8 quantized/external-GPU route may run only if isolated, bounded,
    reproducible, and repo-safe. They do not bypass one-row or sentinel gates.
17. Write the final synthesis:
    - If a non-human repaired or fine-tuned survivor passes all gates, record a
      scoped winner under deterministic deployment-repair or fine-tuning
      evidence.
    - If no route passes, record final no-human no-winner closeout and explain
      which failure clusters were exhausted.
18. Update docs/model_evaluation_state.md,
    docs/v2_0_multimodal_batch1_execution_runbook.md,
    docs/v2_0_multimodal_batch1_full_completion_plan.md,
    docs/v2_0_multimodal_batch1_repair_first_experiment_guide.md,
    70_experiments/registry.tsv, and planning bridge notes after each gate.
19. Run py_compile, validators, TSV width checks, git diff --check, and
    scripts/check_transcript_bearing_leaks.sh.
20. Commit logical slices separately and push non-force to origin main.

Stop rules:
- No model advances because it is famous or interesting.
- No fixed-15 runs before one-row and sentinel gates pass.
- No Taiwan utility/subgroup proxy before fixed-15 and automatic
  semantic-damage proxy pass.
- No human-reviewed 30-row CDS, 258-row, or selected-300 unless a new non-human
  claim-evidence gate is explicitly designed and passes first.
- If deterministic guard and changed LoRA iteration 2 both fail sentinel, write
  final no-human no-winner closeout instead of widening the experiment.
```

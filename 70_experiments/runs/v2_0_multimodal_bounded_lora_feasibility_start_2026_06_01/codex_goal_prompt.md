# Codex Goal Prompt

```text
Using FIRST PRINCIPLE, continue the bounded v2.0 multimodal LoRA feasibility lane in /home/jnln3799/every_on_git_ubuntu/cib-semantic-risk-asr.

Start from:
- 70_experiments/runs/v2_0_multimodal_auto_only_no_winner_stop_2026_06_01/
- 70_experiments/runs/v2_0_multimodal_bounded_lora_feasibility_start_2026_06_01/
- 70_experiments/runs/v2_0_multimodal_finetuning_readiness_design_2026_06_01/

Core rule:
- Raw audio, row IDs, transcripts, references, hypotheses, local paths, model outputs, transcript-bearing logs, and adapter weights are not tracked in Git.
- Training evidence must remain separate from raw model capability, deployment repair, and automatic-proxy evidence.
- The first candidate is Step-Audio-2-mini and the only initial target is sentinel no-speech / non-speech hallucination reduction.

Execute in order:
1. prepare a local-only training payload manifest with aggregate count, sensitivity, storage policy, and hash/status only;
2. add or document the LoRA adapter-loading contract for the Step post-training one-row and sentinel evaluators;
3. freeze the Step pre-training one-row and sentinel aggregate baselines;
4. run a tiny LoRA smoke only after the payload manifest and adapter evaluator contract pass;
5. evaluate post-training one-row first, then sentinel controls;
6. promote to fixed-15 only if post-training sentinel reaches 6/6 and no-speech hallucination is 0;
7. write aggregate-only run records, validators, registry rows, docs, and planning bridge updates;
8. run py_compile, validators, TSV checks, git diff --check, and transcript-bearing leak scan;
9. commit logical slices separately and push non-force to origin main.

Stop rule:
- If local payload manifest, adapter-loading contract, or post-training evaluator cannot be proven without privacy leakage, stop with a no-train feasibility record.
```

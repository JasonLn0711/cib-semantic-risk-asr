#!/usr/bin/env python3
"""Prepare the bounded LoRA feasibility start gate after auto-only closeout."""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any

from run_v2_0_qwen_opencc_locale_repair import privacy_record


RUN_ID = "v2_0_multimodal_bounded_lora_feasibility_start_2026_06_01"
DEFAULT_OUT_DIR = Path("70_experiments/runs") / RUN_ID
SOURCE_STOP_RUN_ID = "v2_0_multimodal_auto_only_no_winner_stop_2026_06_01"
SOURCE_READINESS_RUN_ID = "v2_0_multimodal_finetuning_readiness_design_2026_06_01"
PRIMARY_CANDIDATE = "Step-Audio-2-mini"
TRAINING_TARGET = "sentinel_no_speech_non_speech_hallucination_reduction"


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    generated_at = int(time.time())

    gate_rows = [
        {
            "gate_order": 1,
            "gate_name": "training_question_lock",
            "required_condition": "single_failure_target_from_auto_only_closeout",
            "current_evidence": TRAINING_TARGET,
            "status": "passed",
            "blocking_reason": "none",
            "next_action": "freeze_candidate_and_payload_manifest_requirements",
        },
        {
            "gate_order": 2,
            "gate_name": "candidate_selection",
            "required_condition": "one_candidate_with_repairable_behavior_failure",
            "current_evidence": PRIMARY_CANDIDATE,
            "status": "passed",
            "blocking_reason": "none",
            "next_action": "use_step_audio_first_because_transcript_contract_repair_passed",
        },
        {
            "gate_order": 3,
            "gate_name": "local_private_training_payload",
            "required_condition": "manifested_private_training_payload_with_hash_status",
            "current_evidence": "not_present_in_repo_safe_records",
            "status": "blocked",
            "blocking_reason": "no_training_payload_manifest_or_count_is_available",
            "next_action": "prepare_local_only_payload_manifest_before_training",
        },
        {
            "gate_order": 4,
            "gate_name": "frozen_pretraining_baseline",
            "required_condition": "one_row_and_sentinel_baselines_exist",
            "current_evidence": "step_one_row_repair_passed_and_step_sentinel_failed_3_of_6",
            "status": "passed",
            "blocking_reason": "none",
            "next_action": "copy_baseline_aggregate_ids_into_training_run_record",
        },
        {
            "gate_order": 5,
            "gate_name": "post_training_evaluator",
            "required_condition": "post_training_one_row_and_sentinel_eval_defined",
            "current_evidence": "existing_step_one_row_and_sentinel_scripts_can_be_reused_after_adapter_hook",
            "status": "needs_adapter_hook",
            "blocking_reason": "no_lora_adapter_loading_contract_yet",
            "next_action": "add_adapter_loading_contract_before_training",
        },
        {
            "gate_order": 6,
            "gate_name": "training_execution",
            "required_condition": "payload_manifest_ready_and_adapter_eval_contract_ready",
            "current_evidence": "not_ready",
            "status": "not_started",
            "blocking_reason": "pretraining_gates_3_and_5_are_not_complete",
            "next_action": "do_not_launch_lora_until_payload_manifest_and_adapter_hook_exist",
        },
    ]
    write_tsv(
        args.out_dir / "lora_pretraining_gate.tsv",
        gate_rows,
        [
            "gate_order",
            "gate_name",
            "required_condition",
            "current_evidence",
            "status",
            "blocking_reason",
            "next_action",
        ],
    )

    candidate_rows = [
        {
            "rank": 1,
            "model": PRIMARY_CANDIDATE,
            "selection_reason": "transcript_contract_repair_passed_but_sentinel_no_speech_hallucination_remained",
            "training_target": TRAINING_TARGET,
            "training_scope": "tiny_lora_feasibility_not_quality_claim",
            "current_training_status": "not_started_pretraining_gates_incomplete",
        },
        {
            "rank": 2,
            "model": "MiniCPM-o 4.5",
            "selection_reason": "sentinel_repair_improved_to_5_of_6_but_quantized_scope_needs_separate_training_contract",
            "training_target": TRAINING_TARGET,
            "training_scope": "fallback_after_step_or_explicit_quantized_scope",
            "current_training_status": "deferred",
        },
        {
            "rank": 3,
            "model": "MOSS-Audio-4B",
            "selection_reason": "sentinel_repair_still_3_of_6_after_prompt_repair",
            "training_target": TRAINING_TARGET,
            "training_scope": "fallback_after_step_minicpm",
            "current_training_status": "deferred",
        },
    ]
    write_tsv(
        args.out_dir / "lora_candidate_selection.tsv",
        candidate_rows,
        [
            "rank",
            "model",
            "selection_reason",
            "training_target",
            "training_scope",
            "current_training_status",
        ],
    )

    write_tsv(
        args.out_dir / "controlled_artifact_manifest.tsv",
        [
            {
                "artifact_class": "future_lora_training_payload",
                "artifact_count": 0,
                "sensitivity": "would_be_audio_or_transcript_bearing_local_only",
                "storage_policy": "not_prepared_not_tracked",
                "tracked_payload": "false",
                "sha256": "not_available",
                "manifest_status": "missing_required_before_training",
                "supporting_gate_decision": RUN_ID,
            },
            {
                "artifact_class": "future_lora_adapter_weights",
                "artifact_count": 0,
                "sensitivity": "model_adapter_artifact_local_or_release_gated",
                "storage_policy": "not_created_not_tracked",
                "tracked_payload": "false",
                "sha256": "not_available",
                "manifest_status": "not_created_training_not_started",
                "supporting_gate_decision": RUN_ID,
            },
        ],
        [
            "artifact_class",
            "artifact_count",
            "sensitivity",
            "storage_policy",
            "tracked_payload",
            "sha256",
            "manifest_status",
            "supporting_gate_decision",
        ],
    )

    summary = {
        "run_id": RUN_ID,
        "generated_at_unix": generated_at,
        "status": "bounded_lora_feasibility_start_recorded_training_not_started",
        "source_auto_only_stop_run_id": SOURCE_STOP_RUN_ID,
        "source_readiness_run_id": SOURCE_READINESS_RUN_ID,
        "primary_candidate": PRIMARY_CANDIDATE,
        "training_target": TRAINING_TARGET,
        "training_question_locked": True,
        "training_execution_started": False,
        "training_execution_status": "not_started_pretraining_gates_incomplete",
        "blocking_gates": [
            "local_private_training_payload",
            "post_training_evaluator_adapter_hook",
        ],
        "required_next_actions": [
            "prepare_local_only_payload_manifest_with_hash_status",
            "add_or_document_lora_adapter_loading_contract_for_step_evaluators",
            "freeze_step_pretraining_one_row_and_sentinel_baseline_aggregate_records",
            "run_tiny_lora_smoke_only_after_pretraining_gates_pass",
        ],
        "claim_boundary": "fine_tuning_feasibility_start_not_training_result",
        "privacy": privacy_record(),
    }
    (args.out_dir / "bounded_lora_feasibility_start_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.out_dir / "README.md").write_text(
        "\n".join(
            [
                "# v2.0 Multimodal Bounded LoRA Feasibility Start",
                "",
                "This record starts the post-auto-only-stop fine-tuning lane without mixing training evidence into the no-winner closeout.",
                "",
                "## Decision",
                "",
                f"- Primary candidate: `{PRIMARY_CANDIDATE}`",
                f"- Training target: `{TRAINING_TARGET}`",
                "- Status: `bounded_lora_feasibility_start_recorded_training_not_started`",
                "- Training execution is not launched because the local private training payload manifest and LoRA adapter-loading evaluator contract are not ready.",
                "",
                "## FIRST PRINCIPLE",
                "",
                "Fine-tuning starts from a narrow failure mode and a measurable post-training gate. The current target is Step-Audio no-speech / non-speech sentinel hallucination, because Step passed the repaired one-row transcript contract but failed sentinel controls.",
                "",
                "## Required Next Action",
                "",
                "Prepare the local-only training payload manifest and adapter-loading evaluator contract, then run a tiny LoRA smoke only after those pretraining gates pass.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (args.out_dir / "codex_goal_prompt.md").write_text(
        "\n".join(
            [
                "# Codex Goal Prompt",
                "",
                "```text",
                "Using FIRST PRINCIPLE, continue the bounded v2.0 multimodal LoRA feasibility lane in /home/jnln3799/every_on_git_ubuntu/cib-semantic-risk-asr.",
                "",
                "Start from:",
                "- 70_experiments/runs/v2_0_multimodal_auto_only_no_winner_stop_2026_06_01/",
                "- 70_experiments/runs/v2_0_multimodal_bounded_lora_feasibility_start_2026_06_01/",
                "- 70_experiments/runs/v2_0_multimodal_finetuning_readiness_design_2026_06_01/",
                "",
                "Core rule:",
                "- Raw audio, row IDs, transcripts, references, hypotheses, local paths, model outputs, transcript-bearing logs, and adapter weights are not tracked in Git.",
                "- Training evidence must remain separate from raw model capability, deployment repair, and automatic-proxy evidence.",
                "- The first candidate is Step-Audio-2-mini and the only initial target is sentinel no-speech / non-speech hallucination reduction.",
                "",
                "Execute in order:",
                "1. prepare a local-only training payload manifest with aggregate count, sensitivity, storage policy, and hash/status only;",
                "2. add or document the LoRA adapter-loading contract for the Step post-training one-row and sentinel evaluators;",
                "3. freeze the Step pre-training one-row and sentinel aggregate baselines;",
                "4. run a tiny LoRA smoke only after the payload manifest and adapter evaluator contract pass;",
                "5. evaluate post-training one-row first, then sentinel controls;",
                "6. promote to fixed-15 only if post-training sentinel reaches 6/6 and no-speech hallucination is 0;",
                "7. write aggregate-only run records, validators, registry rows, docs, and planning bridge updates;",
                "8. run py_compile, validators, TSV checks, git diff --check, and transcript-bearing leak scan;",
                "9. commit logical slices separately and push non-force to origin main.",
                "",
                "Stop rule:",
                "- If local payload manifest, adapter-loading contract, or post-training evaluator cannot be proven without privacy leakage, stop with a no-train feasibility record.",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"bounded_lora_feasibility_start_recorded {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

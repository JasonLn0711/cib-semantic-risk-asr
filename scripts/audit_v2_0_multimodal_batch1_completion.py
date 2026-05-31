#!/usr/bin/env python3
"""Write an aggregate-only completion audit for v2.0 Batch 1 multimodal gates."""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from typing import Any


RUN_DIR = Path("70_experiments/runs/v2_0_multimodal_batch1_completion_audit_2026_06_01")

EVIDENCE = {
    "candidate_discovery": Path(
        "70_experiments/runs/v2_0_multimodal_batch1_candidate_discovery_2026_05_31/"
        "candidate_snapshot_summary.json"
    ),
    "kimi_size_boundary": Path(
        "70_experiments/runs/v2_0_multimodal_batch1_kimi_size_boundary_2026_05_31/"
        "kimi_size_boundary_summary.json"
    ),
    "runtime_smoke_preflight": Path(
        "70_experiments/runs/v2_0_multimodal_batch1_runtime_smoke_preflight_2026_05_31/gate_summary.json"
    ),
    "manifest_preflight": Path(
        "70_experiments/runs/v2_0_multimodal_batch1_manifest_preflight_2026_05_31/"
        "manifest_preflight_summary.json"
    ),
    "adapter_preflight": Path(
        "70_experiments/runs/v2_0_multimodal_batch1_adapter_preflight_2026_05_31/"
        "adapter_preflight_summary.json"
    ),
    "qwen_one_row": Path(
        "70_experiments/runs/v2_0_multimodal_batch1_qwen_one_row_smoke_2026_05_31/"
        "gate_summary.json"
    ),
    "qwen_sentinel": Path(
        "70_experiments/runs/v2_0_multimodal_batch1_qwen_sentinel_controls_2026_06_01/"
        "gate_summary.json"
    ),
    "qwen_fixed_15": Path(
        "70_experiments/runs/v2_0_multimodal_batch1_qwen_fixed_15_row_transcript_gate_2026_06_01/"
        "gate_summary.json"
    ),
    "step_one_row": Path(
        "70_experiments/runs/v2_0_multimodal_batch1_step_audio_one_row_smoke_2026_06_01/"
        "gate_summary.json"
    ),
    "moss4_one_row": Path(
        "70_experiments/runs/v2_0_multimodal_batch1_moss_audio_4b_one_row_smoke_2026_06_01/"
        "gate_summary.json"
    ),
    "moss4_sentinel": Path(
        "70_experiments/runs/v2_0_multimodal_batch1_moss_audio_4b_sentinel_controls_2026_06_01/"
        "gate_summary.json"
    ),
    "minicpm_one_row": Path(
        "70_experiments/runs/v2_0_multimodal_batch1_minicpm_o_4_5_one_row_smoke_2026_06_01/"
        "gate_summary.json"
    ),
    "minicpm_sentinel": Path(
        "70_experiments/runs/v2_0_multimodal_batch1_minicpm_o_4_5_sentinel_controls_2026_06_01/"
        "gate_summary.json"
    ),
    "kimi_one_row": Path(
        "70_experiments/runs/v2_0_multimodal_batch1_kimi_audio_one_row_smoke_2026_06_01/"
        "gate_summary.json"
    ),
    "moss8_one_row": Path(
        "70_experiments/runs/v2_0_multimodal_batch1_moss_audio_8b_one_row_smoke_2026_06_01/"
        "gate_summary.json"
    ),
}

PRIVACY = {
    "raw_audio_tracked": False,
    "row_ids_tracked": False,
    "transcripts_tracked": False,
    "references_tracked": False,
    "hypotheses_tracked": False,
    "reviewer_notes_tracked": False,
    "local_paths_tracked": False,
    "transcript_bearing_runtime_logs_tracked": False,
    "model_cache_paths_tracked": False,
}


def load_json(evidence_id: str) -> dict[str, Any]:
    path = EVIDENCE[evidence_id]
    if not path.exists():
        raise SystemExit(f"missing_evidence:{evidence_id}:{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def metric(payload: dict[str, Any], key: str, default: Any = "") -> Any:
    return payload.get(key, default)


def main() -> int:
    payloads = {evidence_id: load_json(evidence_id) for evidence_id in EVIDENCE}
    RUN_DIR.mkdir(parents=True, exist_ok=True)

    decisions = [
        {
            "model_family": "Kimi-Audio",
            "model_id": "moonshotai/Kimi-Audio-7B-Instruct",
            "primary_batch1_member": "true",
            "highest_gate_completed": "one_row_runtime_dependency_boundary",
            "key_aggregate_evidence": (
                "size_boundary_recorded; runtime/cache lane complete; one-row attempt blocked by flash_attn "
                "dependency without local CUDA nvcc"
            ),
            "final_batch1_decision": metric(payloads["kimi_one_row"], "promotion_decision"),
            "next_eligible_action": "flash_attn_cuda_toolchain_repair_then_one_row_rerun",
            "larger_gate_policy": "skip_sentinel_15_row_30_row_258_selected300_until_runtime_dependency_repaired",
        },
        {
            "model_family": "Qwen2.5-Omni",
            "model_id": "Qwen/Qwen2.5-Omni-7B",
            "primary_batch1_member": "true",
            "highest_gate_completed": "fixed_15_row_transcript_gate",
            "key_aggregate_evidence": (
                f"sentinel_pass_rows={metric(payloads['qwen_sentinel'], 'sentinel_pass_rows')}/6; "
                f"valid_output_rate={metric(payloads['qwen_fixed_15'], 'valid_output_rate')}; "
                f"locale_violation_rows={metric(payloads['qwen_fixed_15'], 'locale_violation_rows')}; "
                f"simplified_char_rate={metric(payloads['qwen_fixed_15'], 'simplified_char_rate')}"
            ),
            "final_batch1_decision": metric(payloads["qwen_fixed_15"], "promotion_decision"),
            "next_eligible_action": "bounded_prompt_locale_repair_then_repeat_fixed_gate_chain",
            "larger_gate_policy": "skip_taiwan_utility_30_row_258_selected300_from_raw_run_due_locale_violation",
        },
        {
            "model_family": "Step-Audio",
            "model_id": "stepfun-ai/Step-Audio-2-mini",
            "primary_batch1_member": "true",
            "highest_gate_completed": "one_row_transcript_only_smoke",
            "key_aggregate_evidence": (
                f"valid_text_outputs={metric(payloads['step_one_row'], 'valid_text_outputs')}; "
                f"raw_transcript_like_outputs={metric(payloads['step_one_row'], 'raw_transcript_like_outputs')}; "
                f"repetition_outputs={metric(payloads['step_one_row'], 'repetition_outputs')}"
            ),
            "final_batch1_decision": metric(payloads["step_one_row"], "promotion_decision"),
            "next_eligible_action": "prompt_runtime_repair_then_one_row_rerun",
            "larger_gate_policy": "skip_sentinel_15_row_30_row_258_selected300_until_transcript_contract_passes",
        },
        {
            "model_family": "MOSS-Audio",
            "model_id": "OpenMOSS-Team/MOSS-Audio-4B-Instruct",
            "primary_batch1_member": "true",
            "highest_gate_completed": "sentinel_controls",
            "key_aggregate_evidence": (
                f"one_row_raw_transcript_like_outputs={metric(payloads['moss4_one_row'], 'raw_transcript_like_outputs')}; "
                f"sentinel_pass_rows={metric(payloads['moss4_sentinel'], 'sentinel_pass_rows')}/6; "
                f"hallucination_on_no_speech_rows={metric(payloads['moss4_sentinel'], 'hallucination_on_no_speech_rows')}"
            ),
            "final_batch1_decision": metric(payloads["moss4_sentinel"], "promotion_decision"),
            "next_eligible_action": "sentinel_behavior_repair_then_sentinel_rerun",
            "larger_gate_policy": "skip_15_row_30_row_258_selected300_until_sentinel_passes",
        },
        {
            "model_family": "MOSS-Audio",
            "model_id": "OpenMOSS-Team/MOSS-Audio-8B-Instruct",
            "primary_batch1_member": "true",
            "highest_gate_completed": "one_row_runtime_resource_boundary",
            "key_aggregate_evidence": (
                "runtime/cache lane complete; one-row attempt blocked by local 16GB single-GPU memory boundary"
            ),
            "final_batch1_decision": metric(payloads["moss8_one_row"], "promotion_decision"),
            "next_eligible_action": "bounded_resource_route_then_one_row_rerun",
            "larger_gate_policy": "skip_sentinel_15_row_30_row_258_selected300_until_resource_route_passes",
        },
        {
            "model_family": "MiniCPM-o",
            "model_id": "openbmb/MiniCPM-o-4_5",
            "primary_batch1_member": "true",
            "highest_gate_completed": "sentinel_controls_quantized",
            "key_aggregate_evidence": (
                f"one_row_raw_transcript_like_outputs={metric(payloads['minicpm_one_row'], 'raw_transcript_like_outputs')}; "
                f"sentinel_pass_rows={metric(payloads['minicpm_sentinel'], 'sentinel_pass_rows')}/6; "
                f"hallucination_on_no_speech_rows={metric(payloads['minicpm_sentinel'], 'hallucination_on_no_speech_rows')}; "
                f"summary_or_answer_rows={metric(payloads['minicpm_sentinel'], 'summary_or_answer_rows')}; "
                f"translation_rows={metric(payloads['minicpm_sentinel'], 'translation_rows')}"
            ),
            "final_batch1_decision": metric(payloads["minicpm_sentinel"], "promotion_decision"),
            "next_eligible_action": "sentinel_behavior_repair_then_quantized_or_full_bf16_scoped_rerun",
            "larger_gate_policy": "skip_15_row_30_row_258_selected300_until_sentinel_passes",
        },
    ]

    requirement_rows = [
        {
            "requirement_id": "R1_primary_batch1_model_scope",
            "requirement": "All first-batch primary zh-TW audio LLM models are represented with MOSS 4B and 8B split.",
            "status": "satisfied",
            "evidence": "six model decision rows covering five requested primary families",
            "next_action": "repair-only follow-up for blocked or failed models",
        },
        {
            "requirement_id": "R2_kimi_size_boundary",
            "requirement": "Kimi 7B label and current HF 10B widget boundary are explicitly recorded before runtime claims.",
            "status": "satisfied",
            "evidence": metric(payloads["kimi_size_boundary"], "decision"),
            "next_action": "loaded-parameter evidence only if strict under-10B loaded-count claim is needed",
        },
        {
            "requirement_id": "R3_isolated_runtime_smoke",
            "requirement": "Runtime smoke scaffolding and isolated family lanes avoid modifying repo-wide .venv.",
            "status": "satisfied",
            "evidence": f"adapter_preflight_ready={metric(payloads['adapter_preflight'], 'models_ready_for_smoke')}",
            "next_action": "keep future repair lanes isolated",
        },
        {
            "requirement_id": "R4_one_row_gate_chain",
            "requirement": "Every Batch 1 model receives one-row smoke or a classified one-row runtime/resource boundary.",
            "status": "satisfied",
            "evidence": "Qwen, Step, MOSS 4B, MiniCPM, Kimi, and MOSS 8B all have aggregate one-row records",
            "next_action": "rerun only after bounded repair",
        },
        {
            "requirement_id": "R5_sentinel_policy",
            "requirement": "Sentinel controls run only for one-row transcript-like survivors.",
            "status": "satisfied",
            "evidence": "Qwen passed sentinel; MOSS 4B and MiniCPM failed sentinel; Step/Kimi/MOSS8 skipped by gate policy",
            "next_action": "future sentinel reruns only after repair",
        },
        {
            "requirement_id": "R6_fixed_15_policy",
            "requirement": "Fixed 15-row transcript gate runs only for sentinel survivors.",
            "status": "satisfied",
            "evidence": "Qwen completed fixed 15-row and failed raw zh-TW locale gate",
            "next_action": "future fixed 15-row only after sentinel pass",
        },
        {
            "requirement_id": "R7_taiwan_utility_and_cds_stop_rule",
            "requirement": "Taiwan utility/subgroup and 30-row CDS gates run only after a clean fixed 15-row raw transcript gate.",
            "status": "satisfied_skipped_by_gate_policy",
            "evidence": "no raw Batch 1 model passed fixed 15-row locale gate",
            "next_action": "bounded repair planning before any larger CDS gate",
        },
        {
            "requirement_id": "R8_large_gate_stop_rule",
            "requirement": "258-row and selected-300 gates are reserved for scientific winners.",
            "status": "satisfied_skipped_by_gate_policy",
            "evidence": "zero scientific winners in raw Batch 1 gate chain",
            "next_action": "do not run larger gates until a repaired model becomes a scientific winner",
        },
        {
            "requirement_id": "R9_privacy_boundary",
            "requirement": "Tracked audit contains aggregate decisions only.",
            "status": "satisfied",
            "evidence": "privacy flags false; no row identifiers, transcript text, model outputs, or local paths emitted",
            "next_action": "continue leak scans after docs updates",
        },
    ]

    stop_rows = [
        {
            "gate": "Taiwan utility/subgroup audit",
            "status": "skipped_by_gate_policy",
            "why": "Qwen fixed 15-row failed locale gate; no other model reached fixed 15-row",
            "resume_condition": "a repaired or future model passes one-row, sentinel, and fixed 15-row locale gates",
        },
        {
            "gate": "human_reviewed_30_row_cds",
            "status": "skipped_by_gate_policy",
            "why": "no clean fixed 15-row survivor",
            "resume_condition": "clean fixed 15-row survivor with raw transcript validity and zh-TW locale behavior",
        },
        {
            "gate": "promoted_258_row",
            "status": "skipped_by_gate_policy",
            "why": "no scientific winner after the raw Batch 1 gate chain",
            "resume_condition": "30-row CDS evidence is interpretable and improves the CDS-ASR research question",
        },
        {
            "gate": "selected_300_high_stakes",
            "status": "skipped_by_gate_policy",
            "why": "selected-300 is only for stable, licensed, scientific winners",
            "resume_condition": "promoted model passes 258-row and is claim-relevant for high-stakes evidence",
        },
    ]

    summary = {
        "run_id": RUN_DIR.name,
        "generated_at_unix": int(time.time()),
        "gate": "v2.0 Batch 1 completion audit",
        "status": "batch1_gate_chain_complete_no_scientific_winner",
        "first_principle_decision": (
            "The scarce resource is clean gate evidence. Larger CDS-ASR compute is spent only after "
            "a model passes the prior transcript, sentinel, and zh-TW locale gates."
        ),
        "primary_families_requested": 5,
        "primary_model_rows_audited": len(decisions),
        "runtime_or_one_row_records_complete": 6,
        "sentinel_models_attempted": 3,
        "fixed_15_row_models_attempted": 1,
        "scientific_winners": 0,
        "taiwan_utility_subgroup_status": "skipped_by_gate_policy_no_fixed_15_survivor",
        "human_reviewed_30_row_cds_status": "skipped_by_gate_policy_no_fixed_15_survivor",
        "promoted_258_row_status": "skipped_by_gate_policy_no_scientific_winner",
        "selected_300_status": "skipped_by_gate_policy_no_scientific_winner",
        "next_research_action": (
            "open bounded repair lanes: Qwen prompt/locale, MOSS 4B sentinel behavior, "
            "MiniCPM sentinel behavior, Step transcript contract, Kimi flash_attn/CUDA toolchain, "
            "and MOSS 8B resource route"
        ),
        "privacy": PRIVACY,
    }

    write_tsv(
        RUN_DIR / "model_gate_decisions.tsv",
        decisions,
        [
            "model_family",
            "model_id",
            "primary_batch1_member",
            "highest_gate_completed",
            "key_aggregate_evidence",
            "final_batch1_decision",
            "next_eligible_action",
            "larger_gate_policy",
        ],
    )
    write_tsv(
        RUN_DIR / "objective_requirement_audit.tsv",
        requirement_rows,
        ["requirement_id", "requirement", "status", "evidence", "next_action"],
    )
    write_tsv(
        RUN_DIR / "stop_rule_summary.tsv",
        stop_rows,
        ["gate", "status", "why", "resume_condition"],
    )
    (RUN_DIR / "completion_audit_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (RUN_DIR / "README.md").write_text(
        """# v2.0 Batch 1 completion audit

Date: 2026-06-01

This aggregate-only audit closes the first raw Batch 1 gate chain for the
primary zh-TW audio LLM lane. It does not record raw audio, row identifiers,
transcripts, references, model hypotheses, reviewer notes, local paths, model
outputs, transcript-bearing logs, or model cache paths.

## FIRST PRINCIPLE decision

The scarce resource is clean gate evidence, not a longer model list or larger
compute spend. A model earns the next CDS-ASR budget only after the previous
gate proves transcript validity, ASR-boundary behavior, and Taiwan Traditional
Chinese locale fitness.

## Result

The raw Batch 1 gate chain is complete and has no scientific winner. Qwen2.5-
Omni is the only model that reached fixed 15-row transcript scoring, but it
failed the raw zh-TW locale gate. MOSS-Audio-4B and MiniCPM-o 4.5 passed the
one-row transcript-like contract but failed sentinel behavior controls.
Step-Audio-2-mini failed the one-row transcript contract. Kimi-Audio is blocked
by the isolated flash_attn / CUDA-toolchain dependency boundary. MOSS-Audio-8B
is blocked by the local 16GB single-GPU resource boundary.

Taiwan utility/subgroup, human-reviewed 30-row CDS, promoted 258-row, and
selected-300 gates are skipped by gate policy for this raw run. The next
scientific action is bounded repair planning, not larger inference.
""",
        encoding="utf-8",
    )
    print(f"completion_audit_written {RUN_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Record FireRedASR-LLM resource gate, LoRA decisions, and final closeout."""

from __future__ import annotations

import json
from pathlib import Path

from run_v2_0_asr_controls_baseline_gates import DATE, privacy_record, write_json, write_tsv


ROOT = Path(".")
RUNS = ROOT / "70_experiments/runs"

FIRERED_LLM_RUN = "v2_0_asr_controls_firered_llm_resource_gate_2026_06_01"
LORA_DECISION_RUN = "v2_0_asr_controls_lora_intervention_decisions_2026_06_01"
FINAL_RUN = "v2_0_asr_controls_final_no_human_closeout_2026_06_01"


def read_gate(run_id: str) -> dict:
    return json.loads((RUNS / run_id / "gate_summary.json").read_text(encoding="utf-8"))


def firered_llm_resource_gate() -> None:
    out_dir = RUNS / FIRERED_LLM_RUN
    rows = [
        {
            "model_family": "FireRedASR",
            "model_id": "FireRedASR-LLM-L",
            "source_repo": "https://github.com/FireRedTeam/FireRedASR",
            "hf_model": "FireRedTeam/FireRedASR-LLM-L",
            "hf_revision": "9837461f78d15ee66565d00aaec0bc5497d7fbc1",
            "license": "apache-2.0",
            "declared_parameter_size": "8.3B",
            "declared_input_length_max_seconds": 30,
            "downloaded_model_files": "not_downloaded",
            "required_extra_base_model": "Qwen/Qwen2-7B-Instruct",
            "local_gpu_name": "NVIDIA GeForce RTX 5080",
            "local_gpu_memory_bytes": "16602497024",
            "runtime_decision": "do_not_run_one_row",
            "resource_reason": "llm_route_requires_firered_llm_weights_plus_qwen2_7b_instruct;resource_boundary_not_clean_for_16gb_single_gpu",
            "gate_decision": "blocked_runtime_resource_before_inference",
        }
    ]
    artifacts = [
        {
            "artifact_id": "firered_llm_model_weights",
            "artifact_class": "future_local_model_weight",
            "artifact_count": 0,
            "content_sensitivity": "large_model_weight_binary",
            "storage_policy": "not_downloaded_not_tracked",
            "hash_status": "not_created",
            "tracked_payload": "false",
        },
        {
            "artifact_id": "qwen2_7b_required_base_model",
            "artifact_class": "future_local_model_weight_dependency",
            "artifact_count": 0,
            "content_sensitivity": "large_model_weight_binary",
            "storage_policy": "not_downloaded_not_tracked",
            "hash_status": "not_created",
            "tracked_payload": "false",
        },
    ]
    summary = {
        "run_id": FIRERED_LLM_RUN,
        "date": DATE,
        "status": "firered_llm_resource_gate_blocked_before_inference",
        "model_id": "FireRedASR-LLM-L",
        "rows": 0,
        "one_row_inference_run": False,
        "reason": rows[0]["resource_reason"],
        "promotion_decision": "do_not_promote",
        "larger_gates_open": False,
        "lora_open": False,
        "claim_boundary": "resource_metadata_gate_only_no_transcript_quality_evidence",
        "privacy": privacy_record(),
    }
    write_tsv(out_dir / "resource_gate_summary.tsv", rows)
    write_tsv(out_dir / "controlled_artifact_manifest.tsv", artifacts)
    write_json(out_dir / "gate_summary.json", summary)
    (out_dir / "README.md").write_text(
        "# FireRedASR-LLM Resource Gate\n\n"
        f"Date: {DATE}\n\n"
        "Status: `firered_llm_resource_gate_blocked_before_inference`\n\n"
        "FireRedASR-LLM-L remains metadata/resource-gated. The route requires "
        "the FireRedASR-LLM weights plus `Qwen/Qwen2-7B-Instruct`; the local "
        "single 16GB GPU boundary is not clean enough to justify a one-row LLM "
        "run. No transcript-quality evidence, fixed-15 gate, or LoRA gate is "
        "opened from this route.\n",
        encoding="utf-8",
    )


def lora_decisions() -> None:
    out_dir = RUNS / LORA_DECISION_RUN
    qwen06 = read_gate("v2_0_asr_controls_qwen3_0_6b_trad_repair_baseline_2026_06_01")
    qwen17 = read_gate("v2_0_asr_controls_qwen3_1_7b_trad_repair_baseline_2026_06_01")
    fire_aed = read_gate("v2_0_asr_controls_firered_aed_trad_repair_baseline_2026_06_01")
    fire_llm = read_gate(FIRERED_LLM_RUN)
    rows = [
        {
            "route_id": "qwen3_0_6b_lora_probe",
            "model_id": "Qwen/Qwen3-ASR-0.6B",
            "intervention_rationale_type": "not_opened",
            "baseline_status": qwen06["promotion_decision"],
            "blocker_rows": qwen06["semantic_damage_blocker_rows"],
            "decision": "do_not_train_lora",
            "reason": "repaired_pipeline_has_nonzero_semantic_or_locale_blockers;no_clean_candidate_for_post_lora_claim",
            "rank_alpha_grid_open": "false",
        },
        {
            "route_id": "qwen3_1_7b_lora_probe",
            "model_id": "Qwen/Qwen3-ASR-1.7B",
            "intervention_rationale_type": "not_opened",
            "baseline_status": qwen17["promotion_decision"],
            "blocker_rows": qwen17["semantic_damage_blocker_rows"],
            "decision": "do_not_train_lora",
            "reason": "runtime_repaired_but_fixed15_repair_has_nonzero_blockers;no_larger_gate_or_lora_survivor",
            "rank_alpha_grid_open": "false",
        },
        {
            "route_id": "firered_aed_lora_probe",
            "model_id": "FireRedASR-AED-L",
            "intervention_rationale_type": "not_opened",
            "baseline_status": fire_aed["promotion_decision"],
            "blocker_rows": fire_aed["semantic_damage_blocker_rows"],
            "decision": "do_not_train_lora",
            "reason": "aed_runtime_and_fixed15_succeeded_but_repair_proxy_has_nonzero_blockers;no_clean_post_training_question",
            "rank_alpha_grid_open": "false",
        },
        {
            "route_id": "firered_llm_lora_probe",
            "model_id": "FireRedASR-LLM-L",
            "intervention_rationale_type": "not_opened",
            "baseline_status": fire_llm["promotion_decision"],
            "blocker_rows": "",
            "decision": "do_not_train_lora",
            "reason": "llm_route_resource_blocked_before_one_row;no_raw_or_repaired_baseline",
            "rank_alpha_grid_open": "false",
        },
    ]
    summary = {
        "run_id": LORA_DECISION_RUN,
        "date": DATE,
        "status": "lora_intervention_decisions_complete_no_training_opened",
        "routes_considered": len(rows),
        "lora_training_routes_opened": 0,
        "rank_alpha_grid_routes_opened": 0,
        "decision": "do_not_train_lora_for_current_asr_control_evidence",
        "reason": "no route has clean enough baseline/proxy/resource evidence for a claim-aligned LoRA consequence test",
        "privacy": privacy_record(),
    }
    write_tsv(out_dir / "lora_intervention_decisions.tsv", rows)
    write_json(out_dir / "lora_decision_summary.json", summary)
    (out_dir / "README.md").write_text(
        "# ASR-Control LoRA Intervention Decisions\n\n"
        f"Date: {DATE}\n\n"
        "Status: `lora_intervention_decisions_complete_no_training_opened`\n\n"
        "LoRA is not opened for this evidence state. The current baselines "
        "either have nonzero automatic semantic/locale blockers or remain "
        "resource-blocked before raw one-row inference. Therefore rank/alpha "
        "smoke adapters are not justified under the claim-evidence gate.\n",
        encoding="utf-8",
    )


def final_closeout() -> None:
    out_dir = RUNS / FINAL_RUN
    evidence_rows = [
        {
            "route_id": "qwen3_0_6b",
            "model_id": "Qwen/Qwen3-ASR-0.6B",
            "highest_gate": "fixed15_repair_proxy",
            "decision": "do_not_promote_repaired_pipeline",
            "larger_gates_open": "false",
        },
        {
            "route_id": "qwen3_1_7b",
            "model_id": "Qwen/Qwen3-ASR-1.7B",
            "highest_gate": "fixed15_repair_proxy_after_runtime_repair",
            "decision": "do_not_promote_repaired_pipeline",
            "larger_gates_open": "false",
        },
        {
            "route_id": "firered_aed",
            "model_id": "FireRedASR-AED-L",
            "highest_gate": "fixed15_repair_proxy_after_runtime_repair",
            "decision": "do_not_promote_repaired_pipeline",
            "larger_gates_open": "false",
        },
        {
            "route_id": "firered_llm",
            "model_id": "FireRedASR-LLM-L",
            "highest_gate": "resource_metadata_gate",
            "decision": "blocked_runtime_resource_before_inference",
            "larger_gates_open": "false",
        },
        {
            "route_id": "fireredasr2_optional",
            "model_id": "FireRedASR2-AED/LLM",
            "highest_gate": "metadata_gated_optional",
            "decision": "defer_until_baseline_fireredasr_survivor",
            "larger_gates_open": "false",
        },
    ]
    summary = {
        "run_id": FINAL_RUN,
        "date": DATE,
        "status": "final_no_human_no_winner_closeout",
        "final_outcome": "no_human_no_winner_closeout",
        "models_or_routes_recorded": len(evidence_rows),
        "larger_gates_open": False,
        "lora_training_routes_opened": 0,
        "thirty_row_cds_open": False,
        "split_258_open": False,
        "selected_300_open": False,
        "simplified_to_traditional_helped": True,
        "simplified_to_traditional_boundary": "improved locale/CER/WER form metrics but left nonzero automatic semantic/locale blockers",
        "supported_claim_boundary": "ASR-control runtime and deployment-repair evidence only; no winner for downstream CDS-ASR claims without additional evidence",
        "privacy": privacy_record(),
    }
    write_tsv(out_dir / "final_route_decisions.tsv", evidence_rows)
    write_json(out_dir / "final_closeout_summary.json", summary)
    (out_dir / "README.md").write_text(
        "# Final ASR-Control No-Human Closeout\n\n"
        f"Date: {DATE}\n\n"
        "Status: `final_no_human_no_winner_closeout`\n\n"
        "The v2.0 ASR-control Qwen3-ASR / FireRedASR lane completed the "
        "available no-additional-human-review gates. Deterministic "
        "Simplified-to-Traditional repair improved form and aggregate error "
        "metrics for Qwen3-ASR-0.6B, Qwen3-ASR-1.7B, and FireRedASR-AED, but "
        "all repaired fixed-15 routes retained nonzero automatic blockers. "
        "FireRedASR-LLM remains resource-gated before inference. No route opens "
        "LoRA, Taiwan utility, 30-row CDS, 258-row, or selected-300.\n",
        encoding="utf-8",
    )


def main() -> int:
    firered_llm_resource_gate()
    lora_decisions()
    final_closeout()
    print("v2_0_asr_controls_lora_and_closeout_complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

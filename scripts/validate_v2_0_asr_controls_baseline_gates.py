#!/usr/bin/env python3
"""Validate v2.0 ASR-control baseline gate records."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(".")
RUNS = ROOT / "70_experiments/runs"
RUNTIME_PAYLOAD = (
    ROOT
    / "70_experiments/runtime_lanes/asr_controls/local_outputs/"
    "v2_0_asr_controls_qwen3_0_6b_trad_repair_baseline_2026_06_01/"
    "qwen3_0_6b_trad_repair_outputs.local.jsonl"
)
QWEN17_RUNTIME_PAYLOAD = (
    ROOT
    / "70_experiments/runtime_lanes/asr_controls/local_outputs/"
    "v2_0_asr_controls_qwen3_1_7b_fixed_15_raw_2026_06_01/"
    "predictions/v2_0_asr_controls_qwen3_1_7b_fixed_15_raw_2026_06_01_predictions.jsonl"
)
FIRERED_AED_PAYLOAD = (
    ROOT / "70_experiments/runtime_lanes/asr_controls/firered/local_outputs/firered_aed_fixed15_disable_cudnn.txt"
)

REQUIRED_RUN_FILES = {
    "v2_0_asr_controls_metadata_refresh_2026_06_01": [
        "README.md",
        "model_metadata_summary.tsv",
        "metadata_refresh_summary.json",
    ],
    "v2_0_asr_controls_manifest_preflight_2026_06_01": [
        "README.md",
        "controlled_artifact_manifest.tsv",
        "manifest_preflight_summary.json",
    ],
    "v2_0_asr_controls_baseline_matrix_record_2026_06_01": [
        "README.md",
        "baseline_matrix_decisions.tsv",
        "baseline_matrix_summary.json",
    ],
    "v2_0_asr_controls_qwen3_0_6b_trad_repair_baseline_2026_06_01": [
        "README.md",
        "repair_config_summary.tsv",
        "repair_metric_summary.tsv",
        "repair_delta_summary.tsv",
        "subgroup_baseline_summary.tsv",
        "controlled_artifact_manifest.tsv",
        "gate_summary.json",
    ],
    "v2_0_asr_controls_qwen3_1_7b_runtime_retry_2026_06_01": [
        "README.md",
        "runtime_summary.tsv",
        "controlled_artifact_manifest.tsv",
        "gate_summary.json",
    ],
    "v2_0_asr_controls_qwen3_1_7b_fixed_15_raw_2026_06_01": [
        "README.md",
        "raw_fixed15_summary.tsv",
        "controlled_artifact_manifest.tsv",
        "gate_summary.json",
    ],
    "v2_0_asr_controls_qwen3_1_7b_trad_repair_baseline_2026_06_01": [
        "README.md",
        "repair_metric_summary.tsv",
        "repair_delta_summary.tsv",
        "subgroup_baseline_summary.tsv",
        "controlled_artifact_manifest.tsv",
        "gate_summary.json",
    ],
    "v2_0_asr_controls_firered_aed_runtime_gate_2026_06_01": [
        "README.md",
        "runtime_summary.tsv",
        "controlled_artifact_manifest.tsv",
        "gate_summary.json",
    ],
    "v2_0_asr_controls_firered_aed_fixed_15_raw_2026_06_01": [
        "README.md",
        "raw_fixed15_summary.tsv",
        "controlled_artifact_manifest.tsv",
        "gate_summary.json",
    ],
    "v2_0_asr_controls_firered_aed_trad_repair_baseline_2026_06_01": [
        "README.md",
        "repair_metric_summary.tsv",
        "repair_delta_summary.tsv",
        "subgroup_baseline_summary.tsv",
        "controlled_artifact_manifest.tsv",
        "gate_summary.json",
    ],
    "v2_0_asr_controls_firered_llm_resource_gate_2026_06_01": [
        "README.md",
        "resource_gate_summary.tsv",
        "controlled_artifact_manifest.tsv",
        "gate_summary.json",
    ],
    "v2_0_asr_controls_lora_intervention_decisions_2026_06_01": [
        "README.md",
        "lora_intervention_decisions.tsv",
        "lora_decision_summary.json",
    ],
    "v2_0_asr_controls_final_no_human_closeout_2026_06_01": [
        "README.md",
        "final_route_decisions.tsv",
        "final_closeout_summary.json",
    ],
}

PROHIBITED_TRACKED_TOKENS = [
    "\treference_text\t",
    "\thypothesis_text\t",
    "\trepaired_text\t",
    "\taudio_filepath\t",
    "\tlocal_audio_path\t",
    "\taudio_path\t",
    "\tcache_path\t",
    "\tadapter_path\t",
    "\texpert_note\t",
    "\treviewer_note\t",
    '"reference_text"',
    '"hypothesis_text"',
    '"repaired_text"',
    '"audio_filepath"',
    '"local_audio_path"',
    '"audio_path"',
    '"cache_path"',
    '"adapter_path"',
    '"expert_note"',
    '"reviewer_note"',
]

EXPECTED_PRIVACY_FALSE_KEYS = {
    "raw_audio_tracked",
    "row_ids_tracked",
    "transcripts_tracked",
    "references_tracked",
    "hypotheses_tracked",
    "repaired_text_tracked",
    "model_outputs_tracked",
    "expert_notes_tracked",
    "reviewer_notes_tracked",
    "local_paths_tracked",
    "transcript_bearing_runtime_logs_tracked",
    "adapter_weights_tracked",
    "model_cache_paths_tracked",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_privacy_clean(path: Path) -> None:
    payload = read_json(path)
    privacy = payload.get("privacy", {})
    missing = sorted(EXPECTED_PRIVACY_FALSE_KEYS - set(privacy))
    if missing:
        fail(f"{path} missing privacy keys: {missing}")
    bad = sorted(key for key in EXPECTED_PRIVACY_FALSE_KEYS if privacy.get(key) is not False)
    if bad:
        fail(f"{path} has non-false privacy keys: {bad}")


def assert_no_tracked_leaks() -> None:
    for run_id, files in REQUIRED_RUN_FILES.items():
        for filename in files:
            path = RUNS / run_id / filename
            text = path.read_text(encoding="utf-8").lower()
            for token in PROHIBITED_TRACKED_TOKENS:
                if token in text:
                    fail(f"prohibited tracked token {token!r} in {path}")
            if "/home/" in text:
                fail(f"local absolute path found in {path}")


def assert_runtime_payload_ignored() -> None:
    for payload in [RUNTIME_PAYLOAD, QWEN17_RUNTIME_PAYLOAD, FIRERED_AED_PAYLOAD]:
        if not payload.exists():
            fail(f"missing local runtime payload: {payload}")
        result = subprocess.run(
            ["git", "check-ignore", "-q", str(payload)],
            cwd=ROOT,
            check=False,
        )
        if result.returncode != 0:
            fail(f"runtime transcript-bearing payload is not git-ignored: {payload}")


def main() -> None:
    for run_id, files in REQUIRED_RUN_FILES.items():
        run_dir = RUNS / run_id
        if not run_dir.exists():
            fail(f"missing run dir: {run_dir}")
        for filename in files:
            path = run_dir / filename
            if not path.exists():
                fail(f"missing required file: {path}")

    metadata = read_tsv(RUNS / "v2_0_asr_controls_metadata_refresh_2026_06_01/model_metadata_summary.tsv")
    if len(metadata) != 6:
        fail(f"expected 6 metadata rows, found {len(metadata)}")
    if {row["license"] for row in metadata} != {"apache-2.0"}:
        fail("expected all metadata rows to record apache-2.0 source license")
    if any(row["metadata_verification"] != "primary_source_verified_2026_06_01" for row in metadata):
        fail("metadata verification status mismatch")

    manifest = read_tsv(
        RUNS / "v2_0_asr_controls_manifest_preflight_2026_06_01/controlled_artifact_manifest.tsv"
    )
    if len(manifest) != 6:
        fail(f"expected 6 manifest rows, found {len(manifest)}")
    if any(row["storage_policy"] == "tracked_transcript_bearing_payload" for row in manifest):
        fail("manifest allows tracked transcript-bearing payload")

    matrix = read_tsv(
        RUNS / "v2_0_asr_controls_baseline_matrix_record_2026_06_01/baseline_matrix_decisions.tsv"
    )
    if len(matrix) != 12:
        fail(f"expected 12 baseline decisions, found {len(matrix)}")
    if any(row["current_decision"] == "ready_existing_evidence" and "qwen3_0_6b" not in row["baseline_id"] for row in matrix):
        fail("only Qwen3-ASR-0.6B existing routes may be ready from current evidence")

    metrics = read_tsv(
        RUNS / "v2_0_asr_controls_qwen3_0_6b_trad_repair_baseline_2026_06_01/repair_metric_summary.tsv"
    )
    if len(metrics) != 4:
        fail(f"expected 4 repair metric rows, found {len(metrics)}")
    if {row["repair_variant"] for row in metrics} != {"raw", "opencc_s2tw", "opencc_s2twp", "opencc_s2twp_terms"}:
        fail("repair variants mismatch")
    if any(row["rows"] != "15" for row in metrics):
        fail("each repair variant must aggregate 15 rows")

    gate = read_json(
        RUNS / "v2_0_asr_controls_qwen3_0_6b_trad_repair_baseline_2026_06_01/gate_summary.json"
    )
    if gate["rows"] != 15:
        fail("Qwen3 repair gate must summarize 15 rows")
    if gate["promotion_decision"] != "do_not_promote_repaired_pipeline":
        fail("Qwen3 repair gate should remain closed")
    if gate["larger_gates_open"] is not False:
        fail("larger gates must remain closed")
    if gate["semantic_damage_blocker_rows"] <= 0:
        fail("semantic damage proxy must record blocker rows for no-promotion decision")

    qwen17_runtime = read_json(
        RUNS / "v2_0_asr_controls_qwen3_1_7b_runtime_retry_2026_06_01/gate_summary.json"
    )
    if qwen17_runtime["rows"] != 1 or qwen17_runtime["first_successful_inference_rows"] != 1:
        fail("Qwen3-ASR-1.7B runtime retry must record one successful inference row")
    if qwen17_runtime["promotion_decision"] != "promote_to_fixed_15_raw_gate":
        fail("Qwen3-ASR-1.7B runtime retry promotion decision mismatch")

    qwen17_raw = read_json(
        RUNS / "v2_0_asr_controls_qwen3_1_7b_fixed_15_raw_2026_06_01/gate_summary.json"
    )
    if qwen17_raw["rows"] != 15:
        fail("Qwen3-ASR-1.7B raw gate must summarize 15 rows")
    if qwen17_raw["locale_violation_rows"] != 15:
        fail("Qwen3-ASR-1.7B raw gate should preserve strict locale failure evidence")
    if qwen17_raw["larger_gates_open"] is not False:
        fail("Qwen3-ASR-1.7B raw gate must not open larger gates")

    qwen17_metrics = read_tsv(
        RUNS / "v2_0_asr_controls_qwen3_1_7b_trad_repair_baseline_2026_06_01/repair_metric_summary.tsv"
    )
    if len(qwen17_metrics) != 4:
        fail(f"expected 4 Qwen3-ASR-1.7B repair metric rows, found {len(qwen17_metrics)}")
    if any(row["rows"] != "15" for row in qwen17_metrics):
        fail("each Qwen3-ASR-1.7B repair variant must aggregate 15 rows")
    qwen17_repair = read_json(
        RUNS / "v2_0_asr_controls_qwen3_1_7b_trad_repair_baseline_2026_06_01/gate_summary.json"
    )
    if qwen17_repair["promotion_decision"] != "do_not_promote_repaired_pipeline":
        fail("Qwen3-ASR-1.7B repair gate should remain closed")
    if qwen17_repair["semantic_damage_blocker_rows"] <= 0:
        fail("Qwen3-ASR-1.7B repair proxy must record blocker rows")
    if qwen17_repair["larger_gates_open"] is not False:
        fail("Qwen3-ASR-1.7B repair gate must not open larger gates")

    firered_runtime = read_json(
        RUNS / "v2_0_asr_controls_firered_aed_runtime_gate_2026_06_01/gate_summary.json"
    )
    if firered_runtime["rows"] != 1 or firered_runtime["promotion_decision"] != "promote_to_short_fixed_15_raw_gate":
        fail("FireRedASR-AED runtime gate must promote to short fixed-15 raw gate")

    firered_raw = read_json(
        RUNS / "v2_0_asr_controls_firered_aed_fixed_15_raw_2026_06_01/gate_summary.json"
    )
    if firered_raw["rows"] != 15 or firered_raw["locale_violation_rows"] != 15:
        fail("FireRedASR-AED raw fixed-15 gate must preserve 15-row locale-failed evidence")
    if firered_raw["larger_gates_open"] is not False:
        fail("FireRedASR-AED raw fixed-15 gate must not open larger gates")

    firered_repair = read_json(
        RUNS / "v2_0_asr_controls_firered_aed_trad_repair_baseline_2026_06_01/gate_summary.json"
    )
    if firered_repair["promotion_decision"] != "do_not_promote_repaired_pipeline":
        fail("FireRedASR-AED repair gate should remain closed")
    if firered_repair["semantic_damage_blocker_rows"] <= 0:
        fail("FireRedASR-AED repair proxy must record blocker rows")
    if firered_repair["larger_gates_open"] is not False:
        fail("FireRedASR-AED repair gate must not open larger gates")

    firered_llm = read_json(
        RUNS / "v2_0_asr_controls_firered_llm_resource_gate_2026_06_01/gate_summary.json"
    )
    if firered_llm["one_row_inference_run"] is not False or firered_llm["lora_open"] is not False:
        fail("FireRedASR-LLM must remain blocked before inference and LoRA")

    lora = read_json(
        RUNS / "v2_0_asr_controls_lora_intervention_decisions_2026_06_01/lora_decision_summary.json"
    )
    if lora["lora_training_routes_opened"] != 0 or lora["rank_alpha_grid_routes_opened"] != 0:
        fail("LoRA decisions must keep training and rank/alpha grid closed")

    final = read_json(
        RUNS / "v2_0_asr_controls_final_no_human_closeout_2026_06_01/final_closeout_summary.json"
    )
    if final["final_outcome"] != "no_human_no_winner_closeout":
        fail("final closeout outcome mismatch")
    if final["larger_gates_open"] is not False:
        fail("final closeout must keep larger gates closed")
    if final["lora_training_routes_opened"] != 0:
        fail("final closeout must not open LoRA training")

    for run_id, files in REQUIRED_RUN_FILES.items():
        for filename in files:
            if filename.endswith("_summary.json") or filename == "gate_summary.json":
                assert_privacy_clean(RUNS / run_id / filename)

    assert_no_tracked_leaks()
    assert_runtime_payload_ignored()
    print("OK: v2.0 ASR-control baseline gates are valid")


if __name__ == "__main__":
    main()

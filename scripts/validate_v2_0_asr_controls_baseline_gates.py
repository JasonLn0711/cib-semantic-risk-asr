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
    if not RUNTIME_PAYLOAD.exists():
        fail(f"missing local runtime payload: {RUNTIME_PAYLOAD}")
    result = subprocess.run(
        ["git", "check-ignore", "-q", str(RUNTIME_PAYLOAD)],
        cwd=ROOT,
        check=False,
    )
    if result.returncode != 0:
        fail(f"runtime transcript-bearing payload is not git-ignored: {RUNTIME_PAYLOAD}")


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

    for run_id, files in REQUIRED_RUN_FILES.items():
        for filename in files:
            if filename.endswith("_summary.json") or filename == "gate_summary.json":
                assert_privacy_clean(RUNS / run_id / filename)

    assert_no_tracked_leaks()
    assert_runtime_payload_ignored()
    print("OK: v2.0 ASR-control baseline gates are valid")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Validate v2.0 deterministic acoustic-guard aggregate records."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


RUNS = [
    "v2_0_multimodal_acoustic_guard_design_2026_06_01",
    "v2_0_multimodal_acoustic_guard_manifest_preflight_2026_06_01",
    "v2_0_multimodal_step_audio_guarded_one_row_2026_06_01",
    "v2_0_multimodal_step_audio_guarded_sentinel_2026_06_01",
    "v2_0_multimodal_moss4_guarded_sentinel_2026_06_01",
    "v2_0_multimodal_minicpm_guarded_sentinel_2026_06_01",
    "v2_0_multimodal_guarded_survivor_audit_2026_06_01",
]
PROHIBITED_KEYS = {
    "audio_id",
    "row_id",
    "sample_id",
    "reference_text",
    "transcript",
    "transcript_text",
    "hypothesis",
    "hypothesis_text",
    "local_audio_path",
    "raw_audio_path",
    "reviewer_notes",
    "expert_notes",
    "cache_path",
    "output_text",
    "prompt",
    "audio_path",
    "path",
    "local_path",
}


def check_json_keys(value: Any, key_path: str = "root") -> list[str]:
    violations: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in PROHIBITED_KEYS:
                violations.append(f"{key_path}.{key}")
            violations.extend(check_json_keys(child, f"{key_path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            violations.extend(check_json_keys(child, f"{key_path}[{index}]"))
    return violations


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = reader.fieldnames or []
        prohibited = sorted(set(fields) & PROHIBITED_KEYS)
        if prohibited:
            raise SystemExit(f"prohibited_tsv_fields:{path}:{','.join(prohibited)}")
        return list(reader)


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    violations = check_json_keys(payload)
    if violations:
        raise SystemExit(f"prohibited_json_keys:{path}:{','.join(violations)}")
    if any(payload.get("privacy", {}).values()):
        raise SystemExit(f"privacy_boundary_failed:{path}")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dir", type=Path, default=Path("70_experiments/runs"))
    args = parser.parse_args()

    for run_id in RUNS:
        run_dir = args.base_dir / run_id
        if not run_dir.exists():
            raise SystemExit(f"missing_run_dir:{run_id}")
        if not (run_dir / "README.md").exists():
            raise SystemExit(f"missing_readme:{run_id}")

    design = read_json(args.base_dir / RUNS[0] / "acoustic_guard_design_summary.json")
    if design.get("status") != "acoustic_guard_design_recorded":
        raise SystemExit("unexpected_guard_design_status")
    if len(read_tsv(args.base_dir / RUNS[0] / "acoustic_guard_config.tsv")) != 3:
        raise SystemExit("guard_config_must_have_three_rules")

    manifest = read_json(args.base_dir / RUNS[1] / "guard_manifest_preflight_summary.json")
    if manifest.get("guard_no_speech_rows") != 3 or manifest.get("pass_to_model_rows") != 3:
        raise SystemExit("guard_manifest_expected_three_guard_three_pass")
    if len(read_tsv(args.base_dir / RUNS[1] / "acoustic_guard_feature_summary.tsv")) != 6:
        raise SystemExit("feature_summary_must_have_six_rows")

    one_row = read_json(args.base_dir / RUNS[2] / "gate_summary.json")
    if one_row.get("promotion_decision") != "promote_to_sentinel":
        raise SystemExit("step_guarded_one_row_must_promote_to_sentinel")
    read_tsv(args.base_dir / RUNS[2] / "behavior_summary.tsv")
    read_tsv(args.base_dir / RUNS[2] / "guard_application_summary.tsv")

    for run_id in RUNS[3:6]:
        summary = read_json(args.base_dir / run_id / "gate_summary.json")
        if summary.get("promotion_decision") != "promote_to_fixed_15_candidate_pool":
            raise SystemExit(f"guarded_sentinel_must_promote:{run_id}")
        if summary.get("sentinel_pass_rows") != 6:
            raise SystemExit(f"guarded_sentinel_must_pass_6:{run_id}")
        if summary.get("hallucination_on_no_speech_rows") != 0:
            raise SystemExit(f"guarded_sentinel_hallucination_must_be_zero:{run_id}")
        if len(read_tsv(args.base_dir / run_id / "behavior_summary.tsv")) != 6:
            raise SystemExit(f"guarded_behavior_must_have_six_rows:{run_id}")
        read_tsv(args.base_dir / run_id / "guard_application_summary.tsv")

    audit = read_json(args.base_dir / RUNS[6] / "guarded_survivor_audit_summary.json")
    if audit.get("behavior_clean_survivors") != 3:
        raise SystemExit("expected_three_guarded_survivors")
    if len(read_tsv(args.base_dir / RUNS[6] / "guarded_survivor_decisions.tsv")) != 3:
        raise SystemExit("survivor_decisions_must_have_three_rows")
    print("acoustic_guard_gates_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate the aggregate-only v2.0 Batch 1 multimodal completion audit."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


RUN_DIR = Path("70_experiments/runs/v2_0_multimodal_batch1_completion_audit_2026_06_01")
REQUIRED_FILES = {
    "README.md",
    "completion_audit_summary.json",
    "model_gate_decisions.tsv",
    "objective_requirement_audit.tsv",
    "stop_rule_summary.tsv",
}
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
    "cache_path",
    "output_text",
    "prompt",
    "audio_path",
    "path",
}


def check_json_keys(obj: Any, key_path: str = "root") -> list[str]:
    violations: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in PROHIBITED_KEYS:
                violations.append(f"{key_path}.{key}")
            violations.extend(check_json_keys(value, f"{key_path}.{key}"))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            violations.extend(check_json_keys(value, f"{key_path}[{index}]"))
    return violations


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = reader.fieldnames or []
        prohibited_fields = sorted(set(fields) & PROHIBITED_KEYS)
        if prohibited_fields:
            raise SystemExit(f"prohibited_tsv_fields:{path.name}:{','.join(prohibited_fields)}")
        return list(reader)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", nargs="?", type=Path, default=RUN_DIR)
    args = parser.parse_args()

    missing = sorted(name for name in REQUIRED_FILES if not (args.run_dir / name).exists())
    if missing:
        raise SystemExit(f"missing_required_files:{','.join(missing)}")

    summary = json.loads((args.run_dir / "completion_audit_summary.json").read_text(encoding="utf-8"))
    violations = check_json_keys(summary)
    if violations:
        raise SystemExit(f"prohibited_json_keys:{','.join(violations)}")

    privacy = summary.get("privacy", {})
    if any(privacy.get(key) for key in privacy):
        raise SystemExit("privacy_boundary_failed")
    if summary.get("status") != "batch1_gate_chain_complete_no_scientific_winner":
        raise SystemExit("unexpected_completion_status")
    if int(summary.get("scientific_winners", -1)) != 0:
        raise SystemExit("scientific_winners_must_be_zero_for_this_audit")
    for key in [
        "taiwan_utility_subgroup_status",
        "human_reviewed_30_row_cds_status",
        "promoted_258_row_status",
        "selected_300_status",
    ]:
        if not str(summary.get(key, "")).startswith("skipped_by_gate_policy"):
            raise SystemExit(f"{key}_must_be_skipped_by_gate_policy")

    decisions = read_tsv(args.run_dir / "model_gate_decisions.tsv")
    if len(decisions) != 6:
        raise SystemExit("model_decision_row_count_must_be_6")
    expected_model_ids = {
        "moonshotai/Kimi-Audio-7B-Instruct",
        "Qwen/Qwen2.5-Omni-7B",
        "stepfun-ai/Step-Audio-2-mini",
        "OpenMOSS-Team/MOSS-Audio-4B-Instruct",
        "OpenMOSS-Team/MOSS-Audio-8B-Instruct",
        "openbmb/MiniCPM-o-4_5",
    }
    found_model_ids = {row["model_id"] for row in decisions}
    if found_model_ids != expected_model_ids:
        raise SystemExit(f"model_id_mismatch:{sorted(found_model_ids)}")
    promoted = [
        row
        for row in decisions
        if row["final_batch1_decision"].startswith("promote")
        and row["final_batch1_decision"] != "promote_to_repair_lane"
    ]
    if promoted:
        raise SystemExit("raw_batch1_must_have_no_promoted_scientific_winner")

    requirements = read_tsv(args.run_dir / "objective_requirement_audit.tsv")
    if len(requirements) != 9:
        raise SystemExit("requirement_row_count_must_be_9")
    if any(row["status"].startswith("missing") for row in requirements):
        raise SystemExit("requirement_missing_status_present")

    stops = read_tsv(args.run_dir / "stop_rule_summary.tsv")
    if len(stops) != 4:
        raise SystemExit("stop_rule_row_count_must_be_4")
    if any(row["status"] != "skipped_by_gate_policy" for row in stops):
        raise SystemExit("all_stop_rules_must_be_skipped_by_gate_policy")

    print(f"multimodal_batch1_completion_audit_ok {args.run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate aggregate-only Qwen auto semantic-damage proxy records."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


RUN_DIR = Path("70_experiments/runs/v2_0_multimodal_qwen_auto_semantic_damage_proxy_2026_06_01")
STOP_DIR = Path("70_experiments/runs/v2_0_multimodal_auto_only_no_winner_stop_2026_06_01")
REQUIRED_PROXY_FILES = {
    "README.md",
    "auto_semantic_damage_proxy_summary.json",
    "proxy_metric_summary.tsv",
    "proxy_blocker_summary.tsv",
    "controlled_artifact_manifest.tsv",
}
REQUIRED_STOP_FILES = {
    "README.md",
    "final_auto_only_summary.json",
    "blocked_gate_summary.tsv",
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
    "local_path",
    "raw_text",
    "repaired_text",
}
REQUIRED_CHECKS = {
    "cer_worsening_rows",
    "wer_worsening_rows",
    "new_hallucination_proxy_rows",
    "critical_term_or_proper_noun_change_rows",
    "abbreviation_change_rows",
    "suspicious_length_ratio_rows",
    "empty_output_change_rows",
    "locale_residual_rows",
    "raw_payload_pair_mismatch_rows",
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
            raise SystemExit(f"prohibited_tsv_fields:{path.name}:{','.join(prohibited)}")
        return list(reader)


def require_files(directory: Path, required: set[str]) -> None:
    missing = sorted(name for name in required if not (directory / name).exists())
    if missing:
        raise SystemExit(f"missing_required_files:{directory}:{','.join(missing)}")


def validate_proxy(run_dir: Path) -> dict[str, Any]:
    require_files(run_dir, REQUIRED_PROXY_FILES)
    summary = json.loads((run_dir / "auto_semantic_damage_proxy_summary.json").read_text(encoding="utf-8"))
    violations = check_json_keys(summary)
    if violations:
        raise SystemExit(f"prohibited_json_keys:{','.join(violations)}")
    if summary.get("status") != "qwen_auto_semantic_damage_proxy_complete":
        raise SystemExit("unexpected_proxy_status")
    if summary.get("claim_boundary") != "repaired_pipeline_automatic_proxy_only_not_raw_model_capability":
        raise SystemExit("proxy_claim_boundary_missing")
    if summary.get("human_review_status") != "not_run_disallowed_by_auto_only_plan":
        raise SystemExit("human_review_status_mismatch")
    if any(summary.get("privacy", {}).values()):
        raise SystemExit("privacy_boundary_failed")
    checks = summary.get("proxy_checks", {})
    if set(checks) != REQUIRED_CHECKS:
        raise SystemExit(f"proxy_checks_mismatch:{sorted(checks)}")
    if int(summary.get("rows", 0)) != 15:
        raise SystemExit("proxy_must_have_15_rows")

    metrics = read_tsv(run_dir / "proxy_metric_summary.tsv")
    if len(metrics) != 2:
        raise SystemExit("proxy_metric_summary_must_have_two_rows")
    blockers = read_tsv(run_dir / "proxy_blocker_summary.tsv")
    if {row["check_name"] for row in blockers} != REQUIRED_CHECKS:
        raise SystemExit("proxy_blocker_summary_checks_mismatch")
    blocker_sum = sum(int(row["blocked_rows"]) for row in blockers)
    if blocker_sum != int(summary["semantic_damage_blocker_rows"]):
        raise SystemExit("proxy_blocker_sum_mismatch")

    artifacts = read_tsv(run_dir / "controlled_artifact_manifest.tsv")
    if len(artifacts) != 2:
        raise SystemExit("controlled_artifact_manifest_must_have_two_rows")
    if any(row["tracked_payload"] != "false" for row in artifacts):
        raise SystemExit("transcript_bearing_payloads_must_not_be_tracked")
    if any(len(row["sha256"]) != 64 for row in artifacts):
        raise SystemExit("artifact_sha256_required")
    return summary


def validate_stop(stop_dir: Path, proxy_summary: dict[str, Any]) -> None:
    require_files(stop_dir, REQUIRED_STOP_FILES)
    summary = json.loads((stop_dir / "final_auto_only_summary.json").read_text(encoding="utf-8"))
    violations = check_json_keys(summary)
    if violations:
        raise SystemExit(f"prohibited_stop_json_keys:{','.join(violations)}")
    if summary.get("status") != "auto_only_no_winner_stop":
        raise SystemExit("unexpected_stop_status")
    if summary.get("source_proxy_run_id") != proxy_summary.get("run_id"):
        raise SystemExit("stop_source_proxy_mismatch")
    if int(summary.get("semantic_damage_blocker_rows", 0)) <= 0:
        raise SystemExit("stop_requires_nonzero_blocker")
    if summary.get("taiwan_utility_proxy_status") != "not_run_because_semantic_damage_proxy_not_clean":
        raise SystemExit("taiwan_utility_proxy_status_mismatch")
    if summary.get("fine_tuning_execution_status") != "not_started":
        raise SystemExit("fine_tuning_must_not_be_started")
    if any(summary.get("privacy", {}).values()):
        raise SystemExit("stop_privacy_boundary_failed")
    blocked = read_tsv(stop_dir / "blocked_gate_summary.tsv")
    if len(blocked) != 2:
        raise SystemExit("blocked_gate_summary_must_have_two_rows")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", nargs="?", type=Path, default=RUN_DIR)
    parser.add_argument("--stop-dir", type=Path, default=STOP_DIR)
    args = parser.parse_args()

    proxy_summary = validate_proxy(args.run_dir)
    if int(proxy_summary["semantic_damage_blocker_rows"]) > 0:
        validate_stop(args.stop_dir, proxy_summary)
    print(f"qwen_auto_semantic_damage_proxy_record_ok {args.run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate aggregate-only Qwen OpenCC/Taiwan-term locale repair records."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


RUN_DIR = Path("70_experiments/runs/v2_0_multimodal_batch1_qwen_opencc_locale_repair_2026_06_01")
REQUIRED_FILES = {
    "README.md",
    "repair_config_summary.tsv",
    "repair_metric_summary.tsv",
    "repair_delta_summary.tsv",
    "controlled_artifact_manifest.tsv",
    "gate_summary.json",
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", nargs="?", type=Path, default=RUN_DIR)
    args = parser.parse_args()

    missing = sorted(name for name in REQUIRED_FILES if not (args.run_dir / name).exists())
    if missing:
        raise SystemExit(f"missing_required_files:{','.join(missing)}")

    summary = json.loads((args.run_dir / "gate_summary.json").read_text(encoding="utf-8"))
    violations = check_json_keys(summary)
    if violations:
        raise SystemExit(f"prohibited_json_keys:{','.join(violations)}")
    privacy = summary.get("privacy", {})
    if any(privacy.get(key) for key in privacy):
        raise SystemExit("privacy_boundary_failed")
    if summary.get("status") != "qwen_opencc_locale_repair_complete":
        raise SystemExit("unexpected_status")
    if summary.get("claim_boundary") != "deployment_repair_pipeline_only_not_raw_model_capability":
        raise SystemExit("claim_boundary_missing")

    metrics = read_tsv(args.run_dir / "repair_metric_summary.tsv")
    variants = {row["repair_variant"] for row in metrics}
    expected = {"raw", "opencc_s2tw", "opencc_s2twp", "opencc_s2twp_terms"}
    if variants != expected:
        raise SystemExit(f"variant_mismatch:{sorted(variants)}")
    if any(int(row["rows"]) != 15 for row in metrics):
        raise SystemExit("all_variants_must_have_15_rows")

    artifact_rows = read_tsv(args.run_dir / "controlled_artifact_manifest.tsv")
    if len(artifact_rows) != 2:
        raise SystemExit("controlled_artifact_manifest_must_have_2_rows")
    if any(row["tracked_payload"] != "false" for row in artifact_rows):
        raise SystemExit("transcript_bearing_payloads_must_not_be_tracked")
    if any(len(row["sha256"]) != 64 for row in artifact_rows):
        raise SystemExit("artifact_sha256_required")

    delta = read_tsv(args.run_dir / "repair_delta_summary.tsv")
    if len(delta) != 1:
        raise SystemExit("repair_delta_summary_must_have_one_row")
    print(f"qwen_opencc_locale_repair_record_ok {args.run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

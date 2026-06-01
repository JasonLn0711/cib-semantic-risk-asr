#!/usr/bin/env python3
"""Validate repo-safe Qwen expert-review completion records."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


RUN_DIR = Path("70_experiments/runs/v2_0_multimodal_qwen_expert_review_completion_2026_06_01")
REQUIRED_FILES = {
    "README.md",
    "expert_review_completion_summary.json",
    "expert_review_aggregate_counts.tsv",
    "expert_review_value_counts.tsv",
    "expert_review_output_file_hashes.tsv",
    "controlled_artifact_manifest.tsv",
}
PROHIBITED_KEYS = {
    "audio_id",
    "review_item_id",
    "source_order",
    "row_id",
    "reference_text",
    "raw_hypothesis_text",
    "repaired_hypothesis_text",
    "hypothesis",
    "transcript",
    "expert_notes",
    "local_path",
    "path",
    "output_text",
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

    summary = json.loads((args.run_dir / "expert_review_completion_summary.json").read_text(encoding="utf-8"))
    violations = check_json_keys(summary)
    if violations:
        raise SystemExit(f"prohibited_json_keys:{','.join(violations)}")
    expected = {
        "status": "qwen_expert_review_completed_local_only",
        "review_row_count": 7,
        "semantic_accept_rows": 1,
        "semantic_minor_issue_rows": 2,
        "semantic_reject_rows": 4,
        "critical_major_rows": 5,
        "critical_minor_rows": 2,
        "hallucination_or_omission_rows": 5,
        "final_transcript_usable_rows": 1,
        "semantic_damage_blocker_rows": 5,
        "promotion_decision": "do_not_promote_repaired_pipeline",
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            raise SystemExit(f"unexpected_summary_value:{key}:{summary.get(key)!r}")
    if len(summary.get("zip_sha256", "")) != 64:
        raise SystemExit("zip_sha256_required")
    if any(summary.get("privacy", {}).values()):
        raise SystemExit("privacy_boundary_failed")

    aggregate = read_tsv(args.run_dir / "expert_review_aggregate_counts.tsv")
    value_counts = read_tsv(args.run_dir / "expert_review_value_counts.tsv")
    file_hashes = read_tsv(args.run_dir / "expert_review_output_file_hashes.tsv")
    manifest = read_tsv(args.run_dir / "controlled_artifact_manifest.tsv")
    if len(aggregate) < 9:
        raise SystemExit("aggregate_counts_incomplete")
    if len(value_counts) != 9:
        raise SystemExit("value_counts_must_have_9_rows")
    if len(file_hashes) != 4:
        raise SystemExit("expected_four_zip_members")
    if len(manifest) != 1 or manifest[0].get("tracked_payload") != "false":
        raise SystemExit("controlled_manifest_boundary_failed")

    print(f"qwen_expert_review_completion_ok {args.run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

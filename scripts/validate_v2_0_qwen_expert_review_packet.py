#!/usr/bin/env python3
"""Validate the repo-safe Qwen expert review packet manifest."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


RUN_DIR = Path("70_experiments/runs/v2_0_multimodal_qwen_expert_review_packet_2026_06_01")
REQUIRED_FILES = {
    "README.md",
    "expert_review_packet_summary.json",
    "controlled_artifact_manifest.tsv",
    "packet_file_hashes.tsv",
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
    summary = json.loads((args.run_dir / "expert_review_packet_summary.json").read_text(encoding="utf-8"))
    violations = check_json_keys(summary)
    if violations:
        raise SystemExit(f"prohibited_json_keys:{','.join(violations)}")
    if summary.get("status") != "qwen_expert_review_packet_prepared_local_only":
        raise SystemExit("unexpected_status")
    if summary.get("review_row_count") != 7:
        raise SystemExit("review_row_count_must_be_7")
    if summary.get("human_review_status") != "packet_prepared_review_not_executed":
        raise SystemExit("review_must_not_be_marked_executed")
    if summary.get("claim_boundary") != "expert_review_packet_only_not_review_result":
        raise SystemExit("claim_boundary_missing")
    if any(summary.get("privacy", {}).values()):
        raise SystemExit("privacy_boundary_failed")
    if len(summary.get("packet_zip_sha256", "")) != 64:
        raise SystemExit("packet_zip_sha256_required")

    manifest = read_tsv(args.run_dir / "controlled_artifact_manifest.tsv")
    if len(manifest) != 2:
        raise SystemExit("controlled_artifact_manifest_must_have_two_rows")
    if any(row["tracked_payload"] != "false" for row in manifest):
        raise SystemExit("packet_payload_must_not_be_tracked")
    if any(row["row_count"] != "7" for row in manifest):
        raise SystemExit("manifest_row_count_must_be_7")
    hashes = read_tsv(args.run_dir / "packet_file_hashes.tsv")
    if len(hashes) != 3:
        raise SystemExit("packet_file_hashes_must_have_three_rows")
    if any(row["tracked_payload"] != "false" for row in hashes):
        raise SystemExit("packet_files_must_not_be_tracked")
    if any(len(row["sha256"]) != 64 for row in hashes):
        raise SystemExit("packet_file_sha256_required")
    print(f"qwen_expert_review_packet_manifest_ok {args.run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

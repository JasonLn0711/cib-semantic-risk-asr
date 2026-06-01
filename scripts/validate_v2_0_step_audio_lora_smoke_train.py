#!/usr/bin/env python3
"""Validate Step-Audio bounded LoRA smoke-train records."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


RUN_DIR = Path("70_experiments/runs/v2_0_multimodal_step_audio_lora_smoke_train_2026_06_01")
REQUIRED_FILES = {
    "README.md",
    "lora_smoke_train_summary.json",
    "training_metric_summary.tsv",
    "controlled_artifact_manifest.tsv",
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
    "target_text",
    "source_audio_path",
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
    summary = json.loads((args.run_dir / "lora_smoke_train_summary.json").read_text(encoding="utf-8"))
    violations = check_json_keys(summary)
    if violations:
        raise SystemExit(f"prohibited_json_keys:{','.join(violations)}")
    if summary.get("status") not in {
        "step_audio_lora_smoke_train_complete",
        "step_audio_lora_smoke_train_failed",
    }:
        raise SystemExit("unexpected_status")
    if summary.get("payload_rows") != 4:
        raise SystemExit("payload_rows_must_be_4")
    if summary.get("training_execution_started") is not True:
        raise SystemExit("training_execution_must_start_for_smoke_train")
    if any(summary.get("privacy", {}).values()):
        raise SystemExit("privacy_boundary_failed")
    metrics = read_tsv(args.run_dir / "training_metric_summary.tsv")
    manifest = read_tsv(args.run_dir / "controlled_artifact_manifest.tsv")
    if len(manifest) != 1:
        raise SystemExit("controlled_artifact_manifest_must_have_one_row")
    if manifest[0]["tracked_payload"] != "false":
        raise SystemExit("adapter_payload_must_not_be_tracked")
    if summary["status"] == "step_audio_lora_smoke_train_complete":
        if summary.get("adapter_saved") is not True:
            raise SystemExit("complete_train_must_save_adapter")
        if len(summary.get("adapter_sha256", "")) != 64:
            raise SystemExit("adapter_sha256_required")
        if len(metrics) < 4:
            raise SystemExit("complete_train_metrics_required")
    print(f"step_audio_lora_smoke_train_ok {args.run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

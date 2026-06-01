#!/usr/bin/env python3
"""Audit the bounded MOSS-Audio-8B resource repair route."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import time
from pathlib import Path


RUN_ID = "v2_0_multimodal_batch1_moss_audio_8b_resource_repair_2026_06_01"
OUT_DIR = Path("70_experiments/runs") / RUN_ID
VENV_PYTHON = Path("70_experiments/runtime_lanes/moss_audio/.venv/bin/python")


def gpu_memory() -> tuple[str, str, str]:
    proc = subprocess.run(
        ["nvidia-smi", "--query-gpu=name,memory.total,memory.free", "--format=csv,noheader,nounits"],
        check=False,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return "unknown", "0", "0"
    parts = [part.strip() for part in proc.stdout.strip().splitlines()[0].split(",")]
    return parts[0], parts[1], parts[2]


def bitsandbytes_available() -> bool:
    if not VENV_PYTHON.exists():
        return False
    code = "import importlib.util; print(bool(importlib.util.find_spec('bitsandbytes')))"
    proc = subprocess.run([str(VENV_PYTHON), "-c", code], check=False, text=True, capture_output=True)
    return proc.stdout.strip() == "True"


def write_readme(out_dir: Path, summary: dict[str, object]) -> None:
    text = f"""# MOSS-Audio-8B Resource Repair Audit

Date: 2026-06-01

Status: {summary['status']}

This bounded Phase 8 audit checks whether the local single-GPU lane has a
credible resource route after the MOSS-Audio-8B one-row attempt failed with
CUDA out-of-memory. It records deployment feasibility only and does not create
transcript-quality evidence.

## Result

```text
gpu_memory_total_mib={summary['gpu_memory_total_mib']}
model_artifact_storage_gib={summary['model_artifact_storage_gib']}
bitsandbytes_available={summary['bitsandbytes_available']}
promotion_decision={summary['promotion_decision']}
```
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    gpu_name, total_mib, free_mib = gpu_memory()
    bnb = bitsandbytes_available()
    artifact_gib = 16.87
    single_gpu_route_feasible = bnb and float(total_mib or 0) >= artifact_gib * 1024
    summary = {
        "run_id": RUN_ID,
        "generated_at_unix": int(time.time()),
        "gate": "Phase 8 MOSS-Audio-8B bounded resource-route repair",
        "status": "moss_audio_8b_resource_repair_blocked",
        "model_id": "OpenMOSS-Team/MOSS-Audio-8B-Instruct",
        "source_run_id": "v2_0_multimodal_batch1_moss_audio_8b_one_row_smoke_2026_06_01",
        "gpu_name": gpu_name,
        "gpu_memory_total_mib": total_mib,
        "gpu_memory_free_mib": free_mib,
        "model_artifact_storage_gib": artifact_gib,
        "bitsandbytes_available": bnb,
        "repo_wide_venv_modified": False,
        "external_gpu_route_used": False,
        "single_gpu_resource_route_feasible": single_gpu_route_feasible,
        "repair_decision": "no_bounded_local_single_gpu_resource_route_proven",
        "failure_mode": "local_16gb_gpu_oom_and_no_quantized_runtime_route_available",
        "promotion_decision": "blocked_runtime_resource",
        "privacy": {
            "raw_audio_tracked": False,
            "row_ids_tracked": False,
            "transcripts_tracked": False,
            "hypotheses_tracked": False,
            "reviewer_notes_tracked": False,
            "local_paths_tracked": False,
            "transcript_bearing_runtime_logs_tracked": False,
            "model_cache_paths_tracked": False,
        },
        "next_gate": "external_gpu_or_approved_quantized_resource_route_before_one_row_rerun",
    }
    (args.out_dir / "resource_repair_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.out_dir / "resource_probe.tsv").write_text(
        "gpu_memory_total_mib\tgpu_memory_free_mib\tmodel_artifact_storage_gib\tbitsandbytes_available\tpromotion_decision\n"
        f"{total_mib}\t{free_mib}\t{artifact_gib}\t{str(bnb).lower()}\t{summary['promotion_decision']}\n",
        encoding="utf-8",
    )
    write_readme(args.out_dir, summary)
    print(f"moss_audio_8b_resource_repair_audit_written {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

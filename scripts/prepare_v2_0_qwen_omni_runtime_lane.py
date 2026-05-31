#!/usr/bin/env python3
"""Prepare aggregate-only Qwen2.5-Omni runtime/cache lane evidence.

This script does not install packages, download model weights, or run model
inference. It records the exact local blockers that must be resolved before
Gate C one-row transcript-only smoke can start with Qwen2.5-Omni.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import time
from pathlib import Path
from typing import Any


RUN_ID = "v2_0_multimodal_batch1_qwen_runtime_lane_2026_05_31"
DEFAULT_OUT_DIR = Path("70_experiments/runs") / RUN_ID
QWEN_MODEL_ID = "Qwen/Qwen2.5-Omni-7B"
QWEN_CACHE_DIR = "models--Qwen--Qwen2.5-Omni-7B"


def module_probe(name: str) -> dict[str, str]:
    spec = importlib.util.find_spec(name)
    if spec is None:
        return {"present": "false", "version": "missing", "import_status": "missing"}
    try:
        module = __import__(name)
        return {
            "present": "true",
            "version": str(getattr(module, "__version__", "present")),
            "import_status": "ok",
        }
    except Exception as exc:
        return {
            "present": "true",
            "version": "present_but_import_failed",
            "import_status": f"import_error:{type(exc).__name__}",
        }


def gpu_summary() -> dict[str, str]:
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,driver_version",
                "--format=csv,noheader",
            ],
            text=True,
            stderr=subprocess.STDOUT,
            timeout=10,
        ).strip()
    except Exception:
        return {"gpu_present": "false", "gpu_name": "not_available", "gpu_memory_total_mib": "", "driver_version": ""}
    first = out.splitlines()[0] if out else ""
    parts = [part.strip() for part in first.split(",")]
    return {
        "gpu_present": "true" if parts else "false",
        "gpu_name": parts[0] if parts else "not_available",
        "gpu_memory_total_mib": parts[1].replace(" MiB", "") if len(parts) > 1 else "",
        "driver_version": parts[2] if len(parts) > 2 else "",
    }


def cache_probe(cache_root: Path) -> dict[str, Any]:
    model_cache = cache_root / QWEN_CACHE_DIR
    snapshots = model_cache / "snapshots"
    snapshot_count = sum(1 for child in snapshots.iterdir() if child.is_dir()) if snapshots.exists() else 0
    return {
        "cache_present": model_cache.exists(),
        "snapshot_count": snapshot_count,
    }


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""# Qwen2.5-Omni Runtime Lane Preparation

Date: 2026-05-31

Status: runtime/cache lane blockers recorded; no package install, weight
download, or model inference was run

本紀錄只保存 Qwen runtime lane aggregate status，不保存任何逐字稿或私有音訊內容。

## Purpose

This record prepares the first Gate C model, Qwen2.5-Omni-7B. It keeps the
existing repo `.venv` unchanged and records the isolated runtime/cache work
needed before real one-row transcript-only smoke can run.

## Result

```text
model_id={summary['model_id']}
qwen_omni_utils_import_status={summary['qwen_omni_utils_import_status']}
torchvision_present={summary['torchvision_present']}
model_cache_present={summary['model_cache_present']}
runtime_lane_status={summary['status']}
```

## Next Step

Create an ignored isolated Qwen runtime/cache lane, install the missing
runtime module there, download or attach the Qwen2.5-Omni-7B cache in that
lane, then rerun adapter preflight before one-row transcript-only inference.
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--hf-cache", type=Path, default=Path.home() / ".cache/huggingface/hub")
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    probes = {name: module_probe(name) for name in [
        "torch",
        "torchvision",
        "transformers",
        "accelerate",
        "huggingface_hub",
        "soundfile",
        "qwen_omni_utils",
    ]}
    gpu = gpu_summary()
    cache = cache_probe(args.hf_cache)
    qwen_import = probes["qwen_omni_utils"]["import_status"]
    torchvision_present = probes["torchvision"]["present"] == "true"
    cache_present = bool(cache["cache_present"])

    blockers: list[str] = []
    if qwen_import != "ok":
        blockers.append("qwen_omni_utils_import_blocked")
    if not torchvision_present:
        blockers.append("missing_torchvision")
    if not cache_present:
        blockers.append("missing_qwen_model_cache")

    status = "ready_for_qwen_one_row_smoke" if not blockers else "blocked_before_qwen_one_row_smoke"
    summary = {
        "run_id": RUN_ID,
        "generated_at_unix": int(time.time()),
        "gate": "Qwen2.5-Omni isolated runtime/cache lane preparation",
        "status": status,
        "model_id": QWEN_MODEL_ID,
        "runtime_lane_class": "ignored_isolated_qwen_runtime_lane",
        "repo_venv_modified_by_this_run": False,
        "package_install_run": False,
        "model_weights_downloaded_by_this_run": False,
        "model_inference_run": False,
        "gpu_present": gpu["gpu_present"] == "true",
        "gpu_name": gpu["gpu_name"],
        "gpu_memory_total_mib": gpu["gpu_memory_total_mib"],
        "torch_version": probes["torch"]["version"],
        "transformers_version": probes["transformers"]["version"],
        "huggingface_hub_version": probes["huggingface_hub"]["version"],
        "qwen_omni_utils_import_status": qwen_import,
        "torchvision_present": torchvision_present,
        "model_cache_present": cache_present,
        "model_cache_snapshot_count": cache["snapshot_count"],
        "blockers": blockers,
        "next_gate": "create_ignored_qwen_runtime_cache_lane_then_rerun_adapter_preflight",
        "privacy": {
            "raw_audio_tracked": False,
            "row_ids_tracked": False,
            "transcripts_tracked": False,
            "hypotheses_tracked": False,
            "reviewer_notes_tracked": False,
            "local_paths_tracked": False,
            "model_cache_paths_tracked": False,
        },
    }
    (out_dir / "qwen_runtime_lane_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_readme(out_dir, summary)
    print(f"wrote {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

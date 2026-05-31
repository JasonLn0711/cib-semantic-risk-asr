#!/usr/bin/env python3
"""Record aggregate-only MiniCPM-o 4.5 runtime/cache lane readiness."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import time
from pathlib import Path
from typing import Any


RUN_ID = "v2_0_multimodal_batch1_minicpm_o_4_5_runtime_lane_2026_06_01"
DEFAULT_OUT_DIR = Path("70_experiments/runs") / RUN_ID
MODEL_ID = "openbmb/MiniCPM-o-4_5"
MODEL_REVISION_SHA = "4382fcae8a551b54d18f18462db974ff312aa7f3"
CACHE_DIR = "models--openbmb--MiniCPM-o-4_5"


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
    parts = [part.strip() for part in out.splitlines()[0].split(",")] if out else []
    return {
        "gpu_present": "true" if parts else "false",
        "gpu_name": parts[0] if parts else "not_available",
        "gpu_memory_total_mib": parts[1].replace(" MiB", "") if len(parts) > 1 else "",
        "driver_version": parts[2] if len(parts) > 2 else "",
    }


def cache_probe(cache_root: Path) -> dict[str, Any]:
    model_cache = cache_root / CACHE_DIR
    snapshots = model_cache / "snapshots"
    snapshot_count = sum(1 for child in snapshots.iterdir() if child.is_dir()) if snapshots.exists() else 0
    expected_snapshot = snapshots / MODEL_REVISION_SHA
    return {
        "cache_present": model_cache.exists(),
        "snapshot_count": snapshot_count,
        "expected_snapshot_present": expected_snapshot.exists(),
    }


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""# MiniCPM-o 4.5 Runtime Lane Preparation

Date: 2026-06-01

Status: {summary['status']}

本紀錄只保存 MiniCPM-o 4.5 runtime lane aggregate status，不保存任何逐字稿、
私有音訊內容、row ID、hypothesis 或 model cache path。

## Result

```text
model_id={summary['model_id']}
model_revision_sha={summary['model_revision_sha']}
model_cache_present={summary['model_cache_present']}
model_cache_snapshot_count={summary['model_cache_snapshot_count']}
runtime_import_blockers={summary['runtime_import_blockers']}
inference_policy={summary['inference_policy']}
full_bf16_single_gpu_boundary={summary['full_bf16_single_gpu_boundary']}
next_gate={summary['next_gate']}
```
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--hf-cache", type=Path, default=Path("70_experiments/runtime_lanes/minicpm_o/hf_cache/hub"))
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    module_names = [
        "torch",
        "transformers",
        "accelerate",
        "huggingface_hub",
        "librosa",
        "soundfile",
        "bitsandbytes",
        "pkg_resources",
        "minicpmo",
    ]
    probes = {name: module_probe(name) for name in module_names}
    gpu = gpu_summary()
    cache = cache_probe(args.hf_cache)
    missing = sorted(name for name, probe in probes.items() if probe["import_status"] != "ok")
    if not cache["cache_present"] or not cache["expected_snapshot_present"]:
        missing.append("missing_minicpm_o_4_5_model_cache")

    status = "ready_for_minicpm_o_4_5_quantized_one_row_smoke" if not missing else "blocked_before_minicpm_o_4_5_one_row_smoke"
    summary = {
        "run_id": RUN_ID,
        "generated_at_unix": int(time.time()),
        "gate": "MiniCPM-o 4.5 isolated runtime/cache lane preparation",
        "status": status,
        "model_id": MODEL_ID,
        "model_revision_sha": MODEL_REVISION_SHA,
        "runtime_lane_class": "ignored_isolated_minicpm_o_runtime_lane",
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
        "bitsandbytes_version": probes["bitsandbytes"]["version"],
        "model_cache_present": bool(cache["cache_present"]),
        "model_cache_snapshot_count": cache["snapshot_count"],
        "expected_snapshot_present": bool(cache["expected_snapshot_present"]),
        "runtime_import_blockers": missing,
        "audio_loader_policy": "librosa_16000_mono_matches_official_audio_understanding_example",
        "inference_policy": "4bit_nf4_transcript_only_smoke_on_16gb_gpu",
        "full_bf16_single_gpu_boundary": "cpu_model_initialization_ok_but_full_bf16_cuda_move_oom_on_16gb_gpu",
        "cpu_offload_boundary": "accelerate_device_map_auto_loads_but_audio_encoder_forward_hit_meta_tensor_boundary",
        "next_gate": "run_minicpm_o_4_5_quantized_one_row_transcript_only_smoke" if status == "ready_for_minicpm_o_4_5_quantized_one_row_smoke" else "fix_minicpm_o_4_5_runtime_lane_then_rerun_preflight",
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
    (args.out_dir / "minicpm_o_4_5_runtime_lane_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_readme(args.out_dir, summary)
    print(f"wrote {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

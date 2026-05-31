#!/usr/bin/env python3
"""Record aggregate-only Kimi-Audio runtime/cache lane readiness."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import time
from pathlib import Path
from typing import Any


RUN_ID = "v2_0_multimodal_batch1_kimi_audio_runtime_lane_2026_06_01"
DEFAULT_OUT_DIR = Path("70_experiments/runs") / RUN_ID
MODEL_ID = "moonshotai/Kimi-Audio-7B-Instruct"
MODEL_REVISION_SHA = "9a82a84c37ad9eb1307fb6ed8d7b397862ef9e6b"
OFFICIAL_REPO_HEAD = "349251e1d8f4f98d58fda59246381faecd7392e0"
CACHE_DIR = "models--moonshotai--Kimi-Audio-7B-Instruct"


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
    text = f"""# Kimi-Audio Runtime Lane Preparation

Date: 2026-06-01

Status: {summary['status']}

本紀錄只保存 Kimi-Audio runtime/cache lane aggregate status，不保存任何逐字稿、
私有音訊內容、row ID、hypothesis、模型輸出或 model cache path。

## Size Boundary

Kimi-Audio remains in the v2.0 Batch 1 primary zh-TW audio LLM lane because the
public model label is `Kimi-Audio-7B-Instruct`. The Hugging Face widget reports
`10B params`, so the experiment keeps an explicit size-boundary validation
layer and records runtime feasibility separately from scientific quality.

## Result

```text
model_id={summary['model_id']}
model_revision_sha={summary['model_revision_sha']}
official_repo_head={summary['official_repo_head']}
model_cache_present={summary['model_cache_present']}
expected_snapshot_present={summary['expected_snapshot_present']}
runtime_import_blockers={summary['runtime_import_blockers']}
transcript_only_snapshot_policy={summary['transcript_only_snapshot_policy']}
next_gate={summary['next_gate']}
```
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--hf-cache", type=Path, default=Path("70_experiments/runtime_lanes/kimi_audio/hf_cache/hub"))
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    module_names = [
        "torch",
        "transformers",
        "accelerate",
        "huggingface_hub",
        "soundfile",
        "librosa",
        "kimia_infer",
    ]
    probes = {name: module_probe(name) for name in module_names}
    flash_attn_probe = module_probe("flash_attn")
    gpu = gpu_summary()
    cache = cache_probe(args.hf_cache)
    missing = sorted(name for name, probe in probes.items() if probe["import_status"] != "ok")
    if not cache["cache_present"] or not cache["expected_snapshot_present"]:
        missing.append("missing_kimi_audio_model_cache")

    status = "ready_for_kimi_audio_one_row_smoke_with_dependency_caveat" if not missing else "blocked_before_kimi_audio_one_row_smoke"
    summary = {
        "run_id": RUN_ID,
        "generated_at_unix": int(time.time()),
        "gate": "Kimi-Audio isolated runtime/cache lane preparation",
        "status": status,
        "model_id": MODEL_ID,
        "public_model_label": "Kimi-Audio-7B-Instruct",
        "hf_widget_parameter_marker": "10B params",
        "model_revision_sha": MODEL_REVISION_SHA,
        "official_repo_head": OFFICIAL_REPO_HEAD,
        "runtime_lane_class": "ignored_isolated_kimi_audio_runtime_lane",
        "repo_venv_modified_by_this_run": False,
        "package_install_run": True,
        "model_weights_downloaded_by_this_run": True,
        "model_inference_run": False,
        "gpu_present": gpu["gpu_present"] == "true",
        "gpu_name": gpu["gpu_name"],
        "gpu_memory_total_mib": gpu["gpu_memory_total_mib"],
        "torch_version": probes["torch"]["version"],
        "transformers_version": probes["transformers"]["version"],
        "huggingface_hub_version": probes["huggingface_hub"]["version"],
        "flash_attn_import_status": flash_attn_probe["import_status"],
        "flash_attn_install_boundary": "pip_source_build_failed_without_usr_local_cuda_nvcc",
        "model_cache_present": bool(cache["cache_present"]),
        "model_cache_snapshot_count": cache["snapshot_count"],
        "expected_snapshot_present": bool(cache["expected_snapshot_present"]),
        "runtime_import_blockers": missing,
        "transcript_only_snapshot_policy": "download_main_model_and_whisper_excluding_audio_detokenizer_and_vocoder",
        "local_runtime_patch_policy": "ignored_runtime_lane_lazy_detokenizer_import_and_whisper_sdpa_fallback_only",
        "next_gate": "run_kimi_audio_one_row_transcript_only_smoke_and_classify_flash_attn_or_memory_boundary",
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
    (args.out_dir / "kimi_audio_runtime_lane_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_readme(args.out_dir, summary)
    print(f"wrote {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

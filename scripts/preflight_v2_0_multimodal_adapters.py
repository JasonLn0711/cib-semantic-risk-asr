#!/usr/bin/env python3
"""Preflight v2.0 multimodal model adapters without model inference.

The check is intentionally aggregate-only: it verifies package/runtime/cache
readiness and the local one-row manifest boundary without printing or tracking
row-level manifest values.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import platform
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


RUN_ID = "v2_0_multimodal_batch1_adapter_preflight_2026_05_31"
DEFAULT_OUT_DIR = Path("70_experiments/runs") / RUN_ID
DEFAULT_MANIFEST = Path("one_row_smoke_manifest.local.tsv")


@dataclass(frozen=True)
class AdapterSpec:
    execution_order: int
    family: str
    model_id: str
    cache_dir_name: str
    runtime_lane: str
    required_modules: tuple[str, ...]
    gate_condition: str


ADAPTERS = [
    AdapterSpec(
        1,
        "Qwen2.5-Omni",
        "Qwen/Qwen2.5-Omni-7B",
        "models--Qwen--Qwen2.5-Omni-7B",
        "ignored_isolated_qwen_omni_runtime_lane",
        ("torch", "transformers", "accelerate", "huggingface_hub", "soundfile", "qwen_omni_utils"),
        "metadata_clean_manifest_ready",
    ),
    AdapterSpec(
        2,
        "Step-Audio 2 mini",
        "stepfun-ai/Step-Audio-2-mini",
        "models--stepfun-ai--Step-Audio-2-mini",
        "ignored_isolated_step_audio_runtime_lane",
        ("torch", "transformers", "accelerate", "huggingface_hub", "soundfile"),
        "metadata_clean_manifest_ready",
    ),
    AdapterSpec(
        3,
        "MOSS-Audio",
        "OpenMOSS-Team/MOSS-Audio-4B-Instruct",
        "models--OpenMOSS-Team--MOSS-Audio-4B-Instruct",
        "ignored_isolated_moss_audio_runtime_lane",
        ("torch", "transformers", "accelerate", "huggingface_hub", "soundfile"),
        "metadata_clean_manifest_ready",
    ),
    AdapterSpec(
        4,
        "MiniCPM-o",
        "openbmb/MiniCPM-o-4_5",
        "models--openbmb--MiniCPM-o-4_5",
        "ignored_isolated_minicpm_o_runtime_lane",
        ("torch", "transformers", "accelerate", "huggingface_hub", "soundfile"),
        "metadata_clean_manifest_ready",
    ),
    AdapterSpec(
        5,
        "Kimi-Audio",
        "moonshotai/Kimi-Audio-7B-Instruct",
        "models--moonshotai--Kimi-Audio-7B-Instruct",
        "ignored_isolated_kimi_audio_runtime_lane",
        ("torch", "transformers", "accelerate", "huggingface_hub", "soundfile"),
        "size_boundary_decision_recorded_manifest_ready",
    ),
    AdapterSpec(
        6,
        "MOSS-Audio",
        "OpenMOSS-Team/MOSS-Audio-8B-Instruct",
        "models--OpenMOSS-Team--MOSS-Audio-8B-Instruct",
        "ignored_isolated_moss_audio_runtime_lane",
        ("torch", "transformers", "accelerate", "huggingface_hub", "soundfile"),
        "after_moss_4b_smoke_is_interpretable",
    ),
]


def module_version(name: str) -> str:
    spec = importlib.util.find_spec(name)
    if spec is None:
        return "missing"
    try:
        module = __import__(name)
        return str(getattr(module, "__version__", "present"))
    except Exception as exc:  # pragma: no cover - defensive environment check
        return f"import_error:{type(exc).__name__}"


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
    if not out:
        return {"gpu_present": "false", "gpu_name": "not_available", "gpu_memory_total_mib": "", "driver_version": ""}
    first = out.splitlines()[0]
    parts = [part.strip() for part in first.split(",")]
    memory = parts[1].replace(" MiB", "") if len(parts) > 1 else ""
    return {
        "gpu_present": "true",
        "gpu_name": parts[0] if parts else "",
        "gpu_memory_total_mib": memory,
        "driver_version": parts[2] if len(parts) > 2 else "",
    }


def manifest_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"manifest_exists": False, "manifest_rows": 0, "manifest_field_count": 0}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = reader.fieldnames or []
        rows = sum(1 for _ in reader)
    return {"manifest_exists": True, "manifest_rows": rows, "manifest_field_count": len(fields)}


def cache_status(cache_roots: list[Path], cache_dir_name: str) -> dict[str, Any]:
    matched = next((root / cache_dir_name for root in cache_roots if (root / cache_dir_name).exists()), None)
    if matched is None:
        return {"cache_present": False, "snapshot_count": 0}
    snapshots = matched / "snapshots"
    count = sum(1 for child in snapshots.iterdir() if child.is_dir()) if snapshots.exists() else 0
    return {"cache_present": True, "snapshot_count": count}


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    if summary["models_ready_for_smoke"] >= 6:
        next_step = (
            "All six Batch 1 adapter/cache lanes have now reached the "
            "pre-inference readiness contract. Interpret readiness with the "
            "one-row smoke records: Qwen2.5-Omni, MOSS-Audio-4B, and MiniCPM-o "
            "4.5 are sentinel candidates; Step-Audio-2-mini is in a prompt/runtime "
            "repair lane; Kimi-Audio is blocked by the official flash_attn "
            "dependency boundary; and MOSS-Audio-8B is blocked by the local "
            "16GB single-GPU memory boundary. Continue with sentinel controls "
            "for MOSS-Audio-4B and MiniCPM-o 4.5 before any fixed 15-row gate."
        )
    elif summary["models_ready_for_smoke"] >= 5:
        next_step = (
            "Qwen2.5-Omni, MOSS-Audio-4B, MiniCPM-o 4.5, and Kimi-Audio have "
            "ignored model-cache/runtime lanes, while Step-Audio-2-mini has "
            "separate one-row evidence and remains in a prompt/runtime repair "
            "lane. Interpret Kimi's adapter readiness together with its "
            "one-row smoke record because the official main-model remote code "
            "requires flash_attn on this local machine. Continue with MOSS-Audio-8B "
            "setup only after this dependency boundary is recorded, then run "
            "sentinel controls for transcript-like candidates. Keep local "
            "manifest values, hypotheses, logs, and model caches outside git."
        )
    elif summary["models_ready_for_smoke"] >= 4:
        next_step = (
            "Qwen2.5-Omni, MOSS-Audio-4B, and MiniCPM-o 4.5 have one-row "
            "smoke evidence, while Step-Audio-2-mini is in a prompt/runtime "
            "repair lane. Continue with Kimi-Audio isolated model-cache/runtime "
            "setup, then decide whether MOSS-Audio-8B should run before or "
            "after sentinel controls for the current transcript-like candidates. "
            "Keep local manifest values, hypotheses, logs, and model caches "
            "outside git."
        )
    elif summary["models_ready_for_smoke"] >= 3:
        next_step = (
            "Qwen2.5-Omni and MOSS-Audio-4B have one-row smoke evidence, "
            "while Step-Audio-2-mini is in a prompt/runtime repair lane. "
            "Continue the remaining one-row order by preparing MiniCPM-o 4.5 "
            "and Kimi isolated model-cache/download lanes. Keep local manifest "
            "values, hypotheses, logs, and model caches outside git."
        )
    elif summary["models_ready_for_smoke"] > 0:
        next_step = (
            "Run one-row transcript-only smoke for ready models, starting with "
            "Qwen2.5-Omni-7B, and prepare isolated model-cache/download lanes for "
            "the remaining planned model order. Keep local manifest values, "
            "hypotheses, logs, and model caches outside git."
        )
    else:
        next_step = (
            "Prepare isolated model-cache/download lanes for the planned model "
            "order, then run one-row transcript-only smoke starting with "
            "Qwen2.5-Omni-7B. Keep local manifest values, hypotheses, logs, and "
            "model caches outside git."
        )
    text = f"""# v2.0 Batch 1 Adapter Preflight

Date: 2026-05-31

Status: adapter preflight complete; no model inference was run

本紀錄只保存 adapter readiness，不保存任何逐字稿或私有音訊內容。

## Purpose

This Gate B record checks whether the local runtime can start real one-row
transcript-only smoke for the v2.0 Batch 1 multimodal models. It does not
download model weights and does not run model inference.

## Result

```text
models_checked={summary['models_checked']}
models_ready_for_smoke={summary['models_ready_for_smoke']}
models_blocked_by_missing_runtime_modules={summary['models_blocked_by_missing_runtime_modules']}
models_blocked_by_missing_cache={summary['models_blocked_by_missing_cache']}
models_deferred_by_gate_order={summary['models_deferred_by_gate_order']}
manifest_exists={summary['manifest_exists']}
gpu_present={summary['gpu_present']}
```

## Next Step

{next_step}
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--hf-cache",
        type=Path,
        action="append",
        default=None,
        help="HF cache root. May be passed multiple times for isolated runtime lanes.",
    )
    args = parser.parse_args()
    hf_cache_roots = args.hf_cache or [Path.home() / ".cache/huggingface/hub"]

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    gpu = gpu_summary()
    manifest = manifest_status(args.manifest)
    rows: list[dict[str, Any]] = []
    for spec in ADAPTERS:
        versions = {name: module_version(name) for name in spec.required_modules}
        missing_modules = sorted(name for name, version in versions.items() if version == "missing" or version.startswith("import_error:"))
        cache = cache_status(hf_cache_roots, spec.cache_dir_name)
        if not manifest["manifest_exists"] or manifest["manifest_rows"] < 1:
            gate_status = "blocked_missing_local_manifest"
        elif missing_modules:
            gate_status = "blocked_missing_runtime_modules"
        elif not cache["cache_present"]:
            gate_status = "blocked_missing_model_cache"
        else:
            gate_status = "adapter_preflight_ready_for_one_row_smoke"

        rows.append(
            {
                "execution_order": spec.execution_order,
                "model_family": spec.family,
                "model_id": spec.model_id,
                "runtime_lane": spec.runtime_lane,
                "gate_condition": spec.gate_condition,
                "python_executable_class": "repo_venv_or_current_interpreter",
                "python_version": platform.python_version(),
                "gpu_present": gpu["gpu_present"],
                "gpu_name": gpu["gpu_name"],
                "gpu_memory_total_mib": gpu["gpu_memory_total_mib"],
                "manifest_exists": str(manifest["manifest_exists"]).lower(),
                "manifest_rows": manifest["manifest_rows"],
                "manifest_field_names_tracked": "false",
                "required_modules_count": len(spec.required_modules),
                "missing_modules_count": len(missing_modules),
                "cache_present": str(cache["cache_present"]).lower(),
                "snapshot_count": cache["snapshot_count"],
                "weights_downloaded_by_this_run": "false",
                "model_inference_run": "false",
                "gate_status": gate_status,
            }
        )

    fields = [
        "execution_order",
        "model_family",
        "model_id",
        "runtime_lane",
        "gate_condition",
        "python_executable_class",
        "python_version",
        "gpu_present",
        "gpu_name",
        "gpu_memory_total_mib",
        "manifest_exists",
        "manifest_rows",
        "manifest_field_names_tracked",
        "required_modules_count",
        "missing_modules_count",
        "cache_present",
        "snapshot_count",
        "weights_downloaded_by_this_run",
        "model_inference_run",
        "gate_status",
    ]
    write_tsv(out_dir / "adapter_preflight.tsv", rows, fields)

    summary = {
        "run_id": RUN_ID,
        "generated_at_unix": int(time.time()),
        "gate": "Gate B adapter preflight",
        "status": "adapter_preflight_complete_no_inference",
        "python_version": platform.python_version(),
        "gpu_present": gpu["gpu_present"] == "true",
        "gpu_name": gpu["gpu_name"],
        "gpu_memory_total_mib": gpu["gpu_memory_total_mib"],
        "manifest_exists": manifest["manifest_exists"],
        "manifest_rows": manifest["manifest_rows"],
        "models_checked": len(rows),
        "models_ready_for_smoke": sum(1 for row in rows if row["gate_status"] == "adapter_preflight_ready_for_one_row_smoke"),
        "models_blocked_by_missing_runtime_modules": sum(1 for row in rows if row["gate_status"] == "blocked_missing_runtime_modules"),
        "models_blocked_by_missing_cache": sum(1 for row in rows if row["gate_status"] == "blocked_missing_model_cache"),
        "models_deferred_by_gate_order": sum(1 for row in rows if row["gate_status"] == "defer_until_moss_4b_smoke"),
        "weights_downloaded_by_this_run": False,
        "model_inference_run": False,
        "tracked_manifest_field_names": False,
        "tracked_row_level_values": False,
        "privacy": {
            "raw_audio_tracked": False,
            "row_ids_tracked": False,
            "transcripts_tracked": False,
            "hypotheses_tracked": False,
            "reviewer_notes_tracked": False,
            "local_paths_tracked": False,
            "model_cache_paths_tracked": False,
        },
        "next_gate": (
            "run_sentinel_controls_for_moss_audio_4b_and_minicpm_o_4_5; "
            "hold_qwen_moss_audio_4b_and_minicpm_o_4_5_as_sentinel_candidates; "
            "keep_step_audio_kimi_audio_and_moss_audio_8b_in_repair_or_resource_lanes"
        )
    }
    (out_dir / "adapter_preflight_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_readme(out_dir, summary)
    print(f"wrote {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

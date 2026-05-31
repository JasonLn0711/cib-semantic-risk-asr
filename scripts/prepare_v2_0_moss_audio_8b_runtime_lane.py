#!/usr/bin/env python3
"""Record aggregate-only MOSS-Audio-8B runtime/cache lane readiness."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from prepare_v2_0_moss_audio_runtime_lane import git_head, gpu_summary, module_probe


RUN_ID = "v2_0_multimodal_batch1_moss_audio_8b_runtime_lane_2026_06_01"
DEFAULT_OUT_DIR = Path("70_experiments/runs") / RUN_ID
MODEL_ID = "OpenMOSS-Team/MOSS-Audio-8B-Instruct"
MODEL_REVISION_SHA = "cb7369a8094b5f1c818e384a8d76596c0e2138bd"
CACHE_DIR = "models--OpenMOSS-Team--MOSS-Audio-8B-Instruct"
OFFICIAL_REPO_DIR = Path("70_experiments/runtime_lanes/moss_audio/MOSS-Audio")


def cache_probe(cache_root: Path) -> dict[str, object]:
    model_cache = cache_root / CACHE_DIR
    snapshots = model_cache / "snapshots"
    snapshot_count = sum(1 for child in snapshots.iterdir() if child.is_dir()) if snapshots.exists() else 0
    expected_snapshot = snapshots / MODEL_REVISION_SHA
    return {
        "cache_present": model_cache.exists(),
        "snapshot_count": snapshot_count,
        "expected_snapshot_present": expected_snapshot.exists(),
    }


def write_readme(out_dir: Path, summary: dict[str, object]) -> None:
    text = f"""# MOSS-Audio-8B Runtime Lane Preparation

Date: 2026-06-01

Status: {summary['status']}

本紀錄只保存 MOSS-Audio-8B runtime lane aggregate status，不保存任何逐字稿、
私有音訊內容、row ID、hypothesis 或 model cache path。

## Result

```text
model_id={summary['model_id']}
model_revision_sha={summary['model_revision_sha']}
model_cache_present={summary['model_cache_present']}
model_cache_snapshot_count={summary['model_cache_snapshot_count']}
runtime_import_blockers={summary['runtime_import_blockers']}
memory_boundary={summary['memory_boundary']}
next_gate={summary['next_gate']}
```
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--hf-cache", type=Path, default=Path("70_experiments/runtime_lanes/moss_audio/hf_cache/hub"))
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    module_names = ["torch", "transformers", "accelerate", "huggingface_hub", "soundfile", "scipy", "src"]
    probes = {name: module_probe(name) for name in module_names}
    gpu = gpu_summary()
    cache = cache_probe(args.hf_cache)
    missing = sorted(name for name, probe in probes.items() if probe["import_status"] != "ok")
    if not cache["cache_present"] or not cache["expected_snapshot_present"]:
        missing.append("missing_moss_audio_8b_model_cache")
    if not OFFICIAL_REPO_DIR.exists():
        missing.append("missing_openmoss_moss_audio_repo")

    status = "ready_for_moss_audio_8b_one_row_smoke" if not missing else "blocked_before_moss_audio_8b_one_row_smoke"
    summary = {
        "run_id": RUN_ID,
        "generated_at_unix": int(time.time()),
        "gate": "MOSS-Audio-8B isolated runtime/cache lane preparation",
        "status": status,
        "model_id": MODEL_ID,
        "model_revision_sha": MODEL_REVISION_SHA,
        "runtime_lane_class": "ignored_isolated_moss_audio_runtime_lane",
        "official_repo_head": git_head(OFFICIAL_REPO_DIR),
        "repo_venv_modified_by_this_run": False,
        "package_install_run": False,
        "model_weights_downloaded_by_this_run": True,
        "model_inference_run": False,
        "gpu_present": gpu["gpu_present"] == "true",
        "gpu_name": gpu["gpu_name"],
        "gpu_memory_total_mib": gpu["gpu_memory_total_mib"],
        "torch_version": probes["torch"]["version"],
        "transformers_version": probes["transformers"]["version"],
        "huggingface_hub_version": probes["huggingface_hub"]["version"],
        "model_artifact_storage_gib": 16.87,
        "model_cache_present": bool(cache["cache_present"]),
        "model_cache_snapshot_count": cache["snapshot_count"],
        "expected_snapshot_present": bool(cache["expected_snapshot_present"]),
        "runtime_import_blockers": missing,
        "audio_loader_policy": "soundfile_scipy_resample_avoids_torchaudio_torchcodec_dependency",
        "memory_boundary": "8b_artifact_is_larger_than_4b_and_may_exceed_local_16gb_single_gpu",
        "next_gate": "run_moss_audio_8b_one_row_transcript_only_smoke" if status == "ready_for_moss_audio_8b_one_row_smoke" else "fix_moss_audio_8b_runtime_lane_then_rerun_preflight",
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
    (args.out_dir / "moss_audio_8b_runtime_lane_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_readme(args.out_dir, summary)
    print(f"wrote {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

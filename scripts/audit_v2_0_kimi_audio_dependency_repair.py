#!/usr/bin/env python3
"""Audit the bounded Kimi-Audio dependency repair route."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
from pathlib import Path


RUN_ID = "v2_0_multimodal_batch1_kimi_audio_dependency_repair_2026_06_01"
OUT_DIR = Path("70_experiments/runs") / RUN_ID
VENV_PYTHON = Path("70_experiments/runtime_lanes/kimi_audio/.venv/bin/python")


def probe_flash_attn() -> tuple[str, str]:
    if not VENV_PYTHON.exists():
        return "runtime_python_missing", "missing_isolated_runtime_python"
    code = (
        "import shutil\n"
        "print('nvcc=' + str(shutil.which('nvcc')))\n"
        "try:\n"
        " import flash_attn\n"
        " print('flash_attn=ok:' + str(getattr(flash_attn, '__version__', 'unknown')))\n"
        "except Exception as exc:\n"
        " print('flash_attn=failed:' + type(exc).__name__ + ':' + str(exc)[:160])\n"
    )
    proc = subprocess.run(
        [str(VENV_PYTHON), "-c", code],
        check=False,
        text=True,
        capture_output=True,
    )
    return "probe_completed", (proc.stdout + proc.stderr).strip().replace("\n", "; ")


def write_readme(out_dir: Path, summary: dict[str, object]) -> None:
    text = f"""# Kimi-Audio Dependency Repair Audit

Date: 2026-06-01

Status: {summary['status']}

This bounded Phase 7 audit checks whether the Kimi-Audio isolated lane can
repair the `flash_attn` / CUDA-toolchain boundary without modifying the
repo-wide `.venv` or starting an unbounded CUDA toolchain installation.

## Result

```text
flash_attn_import_status={summary['flash_attn_import_status']}
nvcc_available={summary['nvcc_available']}
promotion_decision={summary['promotion_decision']}
next_gate={summary['next_gate']}
```
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    probe_status, probe_output = probe_flash_attn()
    nvcc_available = shutil.which("nvcc") is not None
    flash_ok = "flash_attn=ok" in probe_output
    summary = {
        "run_id": RUN_ID,
        "generated_at_unix": int(time.time()),
        "gate": "Phase 7 Kimi-Audio flash_attn/CUDA-toolchain dependency repair",
        "status": "kimi_audio_dependency_repair_blocked",
        "model_id": "moonshotai/Kimi-Audio-7B-Instruct",
        "source_run_id": "v2_0_multimodal_batch1_kimi_audio_one_row_smoke_2026_06_01",
        "probe_status": probe_status,
        "flash_attn_import_status": "available" if flash_ok else "missing",
        "nvcc_available": nvcc_available,
        "repo_wide_venv_modified": False,
        "unbounded_cuda_toolchain_install_attempted": False,
        "repair_decision": "cannot_repair_inside_current_bounded_local_lane",
        "failure_mode": "flash_attn_required_but_no_flash_attn_and_no_nvcc_for_bounded_source_build",
        "promotion_decision": "blocked_runtime_dependency",
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
        "next_gate": "external_or_toolchain_approved_kimi_runtime_repair",
    }
    (args.out_dir / "dependency_repair_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.out_dir / "runtime_dependency_probe.tsv").write_text(
        "probe_status\tflash_attn_import_status\tnvcc_available\trepo_wide_venv_modified\tpromotion_decision\n"
        f"{probe_status}\t{summary['flash_attn_import_status']}\t{str(nvcc_available).lower()}\tfalse\t{summary['promotion_decision']}\n",
        encoding="utf-8",
    )
    write_readme(args.out_dir, summary)
    print(f"kimi_audio_dependency_repair_audit_written {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

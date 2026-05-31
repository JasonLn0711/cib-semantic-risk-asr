#!/usr/bin/env python3
"""Create v2.0 multimodal one-row smoke aggregate run records.

This script intentionally does not download model weights or run inference.
It scaffolds the isolated runtime-smoke gate so the real local-only manifest
and model adapters can be attached without changing the repo-wide environment
or tracking transcript-bearing content.
"""

from __future__ import annotations

import argparse
import csv
import json
import platform
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


RUN_ID = "v2_0_multimodal_batch1_runtime_smoke_preflight_2026_05_31"
DEFAULT_OUT_DIR = Path("70_experiments/runs") / RUN_ID

PROHIBITED_TRACKED_FIELDS = {
    "audio_id",
    "row_id",
    "sample_id",
    "transcript_text",
    "hypothesis_text",
    "local_audio_path",
    "raw_audio_path",
    "reviewer_notes",
}


@dataclass(frozen=True)
class ModelPlan:
    execution_order: int
    family: str
    model_id: str
    planned_gate: str
    gate_condition: str
    prompt_policy: str
    runtime_lane: str
    promotion_policy: str


MODEL_PLANS = [
    ModelPlan(
        1,
        "Qwen2.5-Omni",
        "Qwen/Qwen2.5-Omni-7B",
        "one_row_transcript_only_smoke",
        "metadata_clean_after_artifact_check",
        "text_only_no_tts_no_timestamp_no_speaker_label",
        "isolated_qwen_omni_runtime",
        "promote_to_sentinel_only_if_output_is_raw_transcript_like",
    ),
    ModelPlan(
        2,
        "Step-Audio 2 mini",
        "stepfun-ai/Step-Audio-2-mini",
        "one_row_transcript_only_smoke",
        "metadata_clean_after_artifact_check",
        "text_only_no_tts_no_tool_no_conversation",
        "isolated_step_audio_runtime",
        "promote_to_sentinel_only_if_output_is_raw_transcript_like",
    ),
    ModelPlan(
        3,
        "MOSS-Audio",
        "OpenMOSS-Team/MOSS-Audio-4B-Instruct",
        "one_row_transcript_only_smoke",
        "metadata_clean_after_artifact_check",
        "text_only_instruct_transcript_first",
        "isolated_moss_audio_runtime",
        "promote_8b_setup_only_after_4b_prompt_contract_is_interpretable",
    ),
    ModelPlan(
        4,
        "MiniCPM-o",
        "openbmb/MiniCPM-o-4_5",
        "one_row_transcript_only_smoke",
        "metadata_clean_after_artifact_check",
        "text_only_no_tts_no_speech_response",
        "isolated_minicpm_o_runtime",
        "promote_to_sentinel_only_if_output_is_raw_transcript_like",
    ),
    ModelPlan(
        5,
        "Kimi-Audio",
        "moonshotai/Kimi-Audio-7B-Instruct",
        "one_row_transcript_only_smoke",
        "allowed_after_size_boundary_decision",
        "text_only_no_tts_no_audio_qa",
        "isolated_kimi_audio_runtime",
        "report_as_7b_labeled_candidate_with_size_boundary_validation_layer",
    ),
    ModelPlan(
        6,
        "MOSS-Audio",
        "OpenMOSS-Team/MOSS-Audio-8B-Instruct",
        "one_row_transcript_only_smoke",
        "after_moss_4b_smoke_is_interpretable",
        "text_only_instruct_transcript_first",
        "isolated_moss_audio_runtime",
        "promote_to_sentinel_only_if_4b_and_8b_outputs_are_interpretable",
    ),
]


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def read_manifest_summary(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "manifest_provided": False,
            "manifest_rows": 0,
            "manifest_field_count": 0,
            "prohibited_fields_present": [],
            "manifest_status": "local_only_manifest_required_before_inference",
        }

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = reader.fieldnames or []
        prohibited = sorted(set(fields) & PROHIBITED_TRACKED_FIELDS)
        rows = sum(1 for _ in reader)

    return {
        "manifest_provided": True,
        "manifest_rows": rows,
        "manifest_field_count": len(fields),
        "prohibited_fields_present": prohibited,
        "manifest_status": "local_manifest_header_checked",
    }


def environment_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for plan in MODEL_PLANS:
        rows.append(
            {
                "model_family": plan.family,
                "model_id": plan.model_id,
                "execution_order": plan.execution_order,
                "runtime_lane": plan.runtime_lane,
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "torch_version": "not_imported_preflight",
                "transformers_version": "not_imported_preflight",
                "cuda_version": "not_queried_preflight",
                "gpu_name": "not_queried_preflight",
                "dtype": "not_set_preflight",
                "trust_remote_code": "not_set_preflight",
                "timeout_seconds": "not_set_preflight",
                "exit_status": "not_run_preflight_only",
            }
        )
    return rows


def behavior_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for plan in MODEL_PLANS:
        rows.append(
            {
                "model_family": plan.family,
                "model_id": plan.model_id,
                "execution_order": plan.execution_order,
                "planned_gate": plan.planned_gate,
                "gate_condition": plan.gate_condition,
                "prompt_policy": plan.prompt_policy,
                "smoke_status": "not_run_preflight_only",
                "output_rows": 0,
                "valid_text_outputs": 0,
                "raw_transcript_like_outputs": 0,
                "summary_or_answer_outputs": 0,
                "translation_outputs": 0,
                "tts_only_outputs": 0,
                "invented_timestamp_outputs": 0,
                "invented_speaker_label_outputs": 0,
                "failure_mode": "awaiting_local_manifest_and_runtime_adapter",
                "promotion_policy": plan.promotion_policy,
                "promotion_decision": "not_evaluated",
            }
        )
    return rows


def write_readme(out_dir: Path, manifest_summary: dict[str, Any]) -> None:
    text = f"""# v2.0 Batch 1 Runtime Smoke Preflight

Date: 2026-05-31

Status: runtime smoke scaffolding ready; no model inference was run

本紀錄只保存 aggregate runtime-smoke scaffolding，不保存任何逐字稿或私有音訊內容。

## Purpose

This run prepares the isolated one-row transcript-only runtime-smoke gate for
the v2.0 Batch 1 multimodal audio LLM experiment. It records the planned model
order, runtime-lane separation, prompt-output policy, and aggregate output
schemas before any model weights, local audio, or transcript-bearing outputs are
used.

## Files

```text
runtime_environment_summary.tsv
behavior_summary.tsv
gate_summary.json
README.md
```

## Execution Order

1. Qwen2.5-Omni-7B
2. Step-Audio-2-mini
3. MOSS-Audio-4B-Instruct
4. MiniCPM-o 4.5
5. Kimi-Audio-7B-Instruct after size-boundary decision
6. MOSS-Audio-8B-Instruct after MOSS 4B

## Manifest State

```text
manifest_provided={manifest_summary['manifest_provided']}
manifest_rows={manifest_summary['manifest_rows']}
manifest_status={manifest_summary['manifest_status']}
```

The actual one-row audio manifest must remain local-only. Tracked summaries may
record counts and gate decisions, but not audio IDs, row IDs, transcript text,
model hypotheses, reviewer notes, or local file paths.

## Next Gate

Attach a local-only one-row manifest and model-family runtime adapters, then run
the first transcript-only smoke for metadata-clean Batch 1 models. Only models
with raw transcript-like text output can proceed to sentinel negative controls.
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--manifest", type=Path, default=None)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_summary = read_manifest_summary(args.manifest)
    if manifest_summary["prohibited_fields_present"]:
        fields = ", ".join(manifest_summary["prohibited_fields_present"])
        raise SystemExit(f"local manifest contains prohibited tracked fields: {fields}")

    env_fields = [
        "model_family",
        "model_id",
        "execution_order",
        "runtime_lane",
        "python_version",
        "platform",
        "torch_version",
        "transformers_version",
        "cuda_version",
        "gpu_name",
        "dtype",
        "trust_remote_code",
        "timeout_seconds",
        "exit_status",
    ]
    behavior_fields = [
        "model_family",
        "model_id",
        "execution_order",
        "planned_gate",
        "gate_condition",
        "prompt_policy",
        "smoke_status",
        "output_rows",
        "valid_text_outputs",
        "raw_transcript_like_outputs",
        "summary_or_answer_outputs",
        "translation_outputs",
        "tts_only_outputs",
        "invented_timestamp_outputs",
        "invented_speaker_label_outputs",
        "failure_mode",
        "promotion_policy",
        "promotion_decision",
    ]

    write_tsv(out_dir / "runtime_environment_summary.tsv", environment_rows(), env_fields)
    write_tsv(out_dir / "behavior_summary.tsv", behavior_rows(), behavior_fields)

    summary = {
        "run_id": RUN_ID,
        "generated_at_unix": int(time.time()),
        "gate": "Gate 1 runtime smoke preflight scaffolding",
        "status": "scaffolding_ready_no_inference",
        "model_count": len(MODEL_PLANS),
        "planned_models": [plan.model_id for plan in MODEL_PLANS],
        "manifest_summary": manifest_summary,
        "privacy": {
            "raw_audio_tracked": False,
            "row_ids_tracked": False,
            "transcripts_tracked": False,
            "hypotheses_tracked": False,
            "reviewer_notes_tracked": False,
            "transcript_bearing_runtime_logs_tracked": False,
            "model_weights_downloaded": False,
            "local_model_cache_paths_tracked": False,
        },
        "next_gate": "attach local-only manifest and run model-family adapters for one-row transcript-only smoke",
    }
    (out_dir / "gate_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_readme(out_dir, manifest_summary)

    print(f"wrote {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

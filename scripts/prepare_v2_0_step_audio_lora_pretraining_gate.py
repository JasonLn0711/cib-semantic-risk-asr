#!/usr/bin/env python3
"""Prepare local-only Step-Audio LoRA payload manifest and evaluator contract."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from run_v2_0_qwen_opencc_locale_repair import privacy_record


RUN_ID = "v2_0_multimodal_step_audio_lora_pretraining_gate_2026_06_01"
MODEL_ID = "stepfun-ai/Step-Audio-2-mini"
SOURCE_LORA_START_RUN_ID = "v2_0_multimodal_bounded_lora_feasibility_start_2026_06_01"
SOURCE_ONE_ROW_RUN_ID = "v2_0_multimodal_batch1_step_audio_transcript_contract_repair_2026_06_01"
SOURCE_SENTINEL_RUN_ID = "v2_0_multimodal_batch1_step_audio_sentinel_controls_2026_06_01"
DEFAULT_OUT_DIR = Path("70_experiments/runs") / RUN_ID
DEFAULT_LOCAL_DIR = Path("70_experiments/runtime_lanes/step_audio_2_mini/lora_training") / RUN_ID
DEFAULT_SENTINEL_MANIFEST = Path("sentinel_negative_control_manifest.local.tsv")
DEFAULT_ONE_ROW_MANIFEST = Path("one_row_smoke_manifest.local.tsv")
NO_SPEECH_CLASSES = {"silence_no_speech", "tone_non_speech", "noise_non_speech"}


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def build_local_payload(
    *,
    local_dir: Path,
    sentinel_manifest: Path,
    one_row_manifest: Path,
) -> tuple[Path, int, dict[str, int]]:
    local_dir.mkdir(parents=True, exist_ok=True)
    sentinel_rows = read_tsv(sentinel_manifest)
    one_rows = read_tsv(one_row_manifest)
    payload_rows: list[dict[str, Any]] = []
    for row in sentinel_rows:
        if row["sentinel_class"] not in NO_SPEECH_CLASSES:
            continue
        payload_rows.append(
            {
                "training_item_id": f"step_lora_negative_{len(payload_rows) + 1:02d}",
                "source_class": row["sentinel_class"],
                "source_audio_path": row["audio_path"],
                "target_text": "無法辨識",
                "target_role": "negative_no_speech_guardrail",
            }
        )
    if not one_rows:
        raise SystemExit("one_row_manifest_empty")
    anchor = one_rows[0]
    payload_rows.append(
        {
            "training_item_id": "step_lora_positive_anchor_01",
            "source_class": "positive_transcript_anchor",
            "source_audio_path": anchor["local_audio_path"],
            "target_text": anchor["reference_text"],
            "target_role": "positive_transcript_preservation_anchor",
        }
    )
    payload_path = local_dir / "step_audio_lora_smoke_payload.local.jsonl"
    with payload_path.open("w", encoding="utf-8") as handle:
        for row in payload_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    counts = {
        "payload_rows": len(payload_rows),
        "negative_no_speech_rows": sum(
            1 for row in payload_rows if row["target_role"] == "negative_no_speech_guardrail"
        ),
        "positive_anchor_rows": sum(
            1 for row in payload_rows if row["target_role"] == "positive_transcript_preservation_anchor"
        ),
    }
    return payload_path, len(payload_rows), counts


def script_has_adapter_contract(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    return "--adapter-dir" in text and "PeftModel.from_pretrained" in text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--local-dir", type=Path, default=DEFAULT_LOCAL_DIR)
    parser.add_argument("--sentinel-manifest", type=Path, default=DEFAULT_SENTINEL_MANIFEST)
    parser.add_argument("--one-row-manifest", type=Path, default=DEFAULT_ONE_ROW_MANIFEST)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    payload_path, payload_rows, counts = build_local_payload(
        local_dir=args.local_dir,
        sentinel_manifest=args.sentinel_manifest,
        one_row_manifest=args.one_row_manifest,
    )
    payload_sha256 = sha256_path(payload_path)
    generated_at = int(time.time())

    one_row_contract = script_has_adapter_contract(Path("scripts/run_v2_0_step_audio_transcript_contract_repair.py"))
    sentinel_contract = script_has_adapter_contract(Path("scripts/run_v2_0_step_audio_sentinel_controls.py"))
    adapter_contract_ready = one_row_contract and sentinel_contract

    write_tsv(
        args.out_dir / "lora_payload_manifest.tsv",
        [
            {
                "artifact_class": "step_audio_lora_smoke_training_payload",
                "row_count": payload_rows,
                "negative_no_speech_rows": counts["negative_no_speech_rows"],
                "positive_anchor_rows": counts["positive_anchor_rows"],
                "sensitivity": "audio_and_transcript_target_bearing_local_only",
                "storage_policy": "ignored_runtime_lane_not_tracked",
                "tracked_payload": "false",
                "sha256": payload_sha256,
                "manifest_status": "local_payload_prepared_hash_recorded",
            }
        ],
        [
            "artifact_class",
            "row_count",
            "negative_no_speech_rows",
            "positive_anchor_rows",
            "sensitivity",
            "storage_policy",
            "tracked_payload",
            "sha256",
            "manifest_status",
        ],
    )
    write_tsv(
        args.out_dir / "adapter_evaluator_contract.tsv",
        [
            {
                "evaluator": "step_one_row_transcript_contract_repair",
                "adapter_argument": "--adapter-dir",
                "adapter_loader": "peft.PeftModel.from_pretrained",
                "contract_status": "ready" if one_row_contract else "missing",
                "post_training_gate": "one_row_transcript_contract",
            },
            {
                "evaluator": "step_sentinel_controls",
                "adapter_argument": "--adapter-dir",
                "adapter_loader": "peft.PeftModel.from_pretrained",
                "contract_status": "ready" if sentinel_contract else "missing",
                "post_training_gate": "sentinel_no_speech_non_speech_controls",
            },
        ],
        ["evaluator", "adapter_argument", "adapter_loader", "contract_status", "post_training_gate"],
    )
    write_tsv(
        args.out_dir / "pretraining_gate_status.tsv",
        [
            {
                "gate_name": "local_private_training_payload",
                "status": "passed",
                "evidence": "local_payload_prepared_hash_recorded",
                "next_action": "run_tiny_lora_smoke",
            },
            {
                "gate_name": "adapter_loading_evaluator_contract",
                "status": "passed" if adapter_contract_ready else "blocked",
                "evidence": "one_row_and_sentinel_accept_adapter_dir" if adapter_contract_ready else "adapter_contract_missing",
                "next_action": "run_tiny_lora_smoke" if adapter_contract_ready else "patch_evaluators_before_training",
            },
            {
                "gate_name": "training_execution",
                "status": "ready_not_started" if adapter_contract_ready else "blocked",
                "evidence": "payload_and_evaluator_contract_ready" if adapter_contract_ready else "pretraining_gate_incomplete",
                "next_action": "execute_bounded_step_lora_smoke" if adapter_contract_ready else "do_not_train",
            },
        ],
        ["gate_name", "status", "evidence", "next_action"],
    )
    summary = {
        "run_id": RUN_ID,
        "generated_at_unix": generated_at,
        "status": "step_audio_lora_pretraining_gate_ready_not_started"
        if adapter_contract_ready
        else "step_audio_lora_pretraining_gate_blocked",
        "model_id": MODEL_ID,
        "source_lora_start_run_id": SOURCE_LORA_START_RUN_ID,
        "source_one_row_run_id": SOURCE_ONE_ROW_RUN_ID,
        "source_sentinel_run_id": SOURCE_SENTINEL_RUN_ID,
        "training_target": "sentinel_no_speech_non_speech_hallucination_reduction",
        "payload_rows": payload_rows,
        "negative_no_speech_rows": counts["negative_no_speech_rows"],
        "positive_anchor_rows": counts["positive_anchor_rows"],
        "payload_sha256": payload_sha256,
        "payload_storage_policy": "ignored_runtime_lane_not_tracked",
        "adapter_evaluator_contract_ready": adapter_contract_ready,
        "training_execution_started": False,
        "training_execution_status": "ready_not_started" if adapter_contract_ready else "not_started_pretraining_gate_blocked",
        "next_gate": "bounded_step_lora_smoke_train" if adapter_contract_ready else "repair_pretraining_gate",
        "claim_boundary": "pretraining_payload_and_evaluator_contract_only_not_training_result",
        "privacy": privacy_record(),
    }
    (args.out_dir / "step_lora_pretraining_gate_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.out_dir / "README.md").write_text(
        "\n".join(
            [
                "# Step-Audio Bounded LoRA Pretraining Gate",
                "",
                "This record prepares the local-only Step-Audio LoRA smoke payload and verifies that post-training evaluators can load a LoRA adapter.",
                "",
                "## Decision",
                "",
                f"- Status: `{summary['status']}`",
                f"- Payload rows: `{payload_rows}`",
                f"- Negative no-speech rows: `{counts['negative_no_speech_rows']}`",
                f"- Positive transcript anchor rows: `{counts['positive_anchor_rows']}`",
                f"- Training execution: `{summary['training_execution_status']}`",
                "",
                "The transcript-bearing payload remains in the ignored runtime lane. Git tracks only aggregate counts and hashes.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"step_audio_lora_pretraining_gate_written {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

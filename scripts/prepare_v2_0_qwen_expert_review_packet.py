#!/usr/bin/env python3
"""Prepare a local-only Qwen expert review packet.

Transcript-bearing review files are written to ~/Downloads and are not tracked
in Git. The repo receives only aggregate status and hash/manifest records.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import time
from pathlib import Path
from typing import Any

from run_v2_0_qwen_opencc_locale_repair import (
    MODEL_ID,
    count_simplified,
    edit_counts,
    privacy_record,
)


RUN_ID = "v2_0_multimodal_qwen_expert_review_packet_2026_06_01"
SOURCE_PROXY_RUN_ID = "v2_0_multimodal_qwen_auto_semantic_damage_proxy_2026_06_01"
SOURCE_RAW_RUN_ID = "v2_0_multimodal_batch1_qwen_fixed_15_row_transcript_gate_2026_06_01"
SOURCE_REPAIR_RUN_ID = "v2_0_multimodal_batch1_qwen_opencc_locale_repair_2026_06_01"
DEFAULT_RAW_INPUT = (
    Path("70_experiments/runtime_lanes/qwen_omni/local_outputs")
    / SOURCE_RAW_RUN_ID
    / "qwen_fixed_15_row_outputs.local.jsonl"
)
DEFAULT_REPAIRED_INPUT = (
    Path("70_experiments/runtime_lanes/qwen_omni/local_outputs")
    / SOURCE_REPAIR_RUN_ID
    / "qwen_opencc_locale_repair_outputs.local.jsonl"
)
DEFAULT_OUT_DIR = Path("70_experiments/runs") / RUN_ID
DEFAULT_DOWNLOADS_DIR = Path.home() / "Downloads"
REPAIRED_VARIANT = "opencc_s2twp_terms"


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_review_rows(raw_rows: list[dict[str, Any]], repaired_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raw_by_id = {row["audio_id"]: row for row in raw_rows}
    repaired_by_id = {row["audio_id"]: row for row in repaired_rows}
    if set(raw_by_id) != set(repaired_by_id):
        raise SystemExit("raw_and_repaired_row_sets_differ")
    review_rows: list[dict[str, Any]] = []
    for order, audio_id in enumerate(sorted(raw_by_id), start=1):
        raw_row = raw_by_id[audio_id]
        repaired_text = repaired_by_id[audio_id]["variants"][REPAIRED_VARIANT]
        simplified_count, cjk_count, simplified_rate = count_simplified(repaired_text)
        if simplified_count == 0:
            continue
        reference = raw_row["reference_text"]
        raw_text = raw_row["hypothesis_text"]
        _, _, repaired_cer = edit_counts(reference, repaired_text, unit="char")
        _, _, repaired_wer = edit_counts(reference, repaired_text, unit="word")
        review_rows.append(
            {
                "review_item_id": f"qwen_locale_residual_{len(review_rows) + 1:02d}",
                "source_order": order,
                "audio_id": audio_id,
                "split": raw_row.get("split", ""),
                "model_id": raw_row.get("model_id", MODEL_ID),
                "reference_text": reference,
                "raw_hypothesis_text": raw_text,
                "repaired_hypothesis_text": repaired_text,
                "raw_cer": raw_row.get("cer", ""),
                "raw_wer": raw_row.get("wer", ""),
                "repaired_cer": repaired_cer,
                "repaired_wer": repaired_wer,
                "repaired_simplified_char_count": simplified_count,
                "repaired_cjk_char_count": cjk_count,
                "repaired_simplified_char_rate": simplified_rate,
                "expert_semantic_acceptability": "",
                "expert_locale_acceptability": "",
                "expert_critical_term_damage": "",
                "expert_hallucination_or_omission": "",
                "expert_notes": "",
            }
        )
    return review_rows


def write_packet(packet_dir: Path, review_rows: list[dict[str, Any]]) -> list[Path]:
    packet_dir.mkdir(parents=True, exist_ok=True)
    fields = [
        "review_item_id",
        "source_order",
        "audio_id",
        "split",
        "model_id",
        "reference_text",
        "raw_hypothesis_text",
        "repaired_hypothesis_text",
        "raw_cer",
        "raw_wer",
        "repaired_cer",
        "repaired_wer",
        "repaired_simplified_char_count",
        "repaired_cjk_char_count",
        "repaired_simplified_char_rate",
        "expert_semantic_acceptability",
        "expert_locale_acceptability",
        "expert_critical_term_damage",
        "expert_hallucination_or_omission",
        "expert_notes",
    ]
    review_tsv = packet_dir / "qwen_locale_residual_expert_review.tsv"
    write_tsv(review_tsv, review_rows, fields)
    readme = packet_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# Qwen Repaired-Pipeline Expert Review Packet",
                "",
                "Purpose: expert review of the Qwen OpenCC/Taiwan-term repaired output rows that still have Traditional Chinese locale residuals after deterministic automatic proxy screening.",
                "",
                "Review scope:",
                "- Review only the included locale-residual rows.",
                "- Compare reference text, raw Qwen hypothesis, and repaired hypothesis.",
                "- Fill the expert columns in the TSV.",
                "",
                "Suggested labels:",
                "- expert_semantic_acceptability: accept / minor_issue / reject",
                "- expert_locale_acceptability: accept / minor_locale_residual / reject",
                "- expert_critical_term_damage: none / minor / major",
                "- expert_hallucination_or_omission: none / hallucination / omission / both",
                "",
                "Boundary:",
                "- This packet contains transcript-bearing text and must stay outside Git.",
                "- No raw audio is included.",
                "- The Git-tracked repo records only aggregate packet status and hashes.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    schema = packet_dir / "review_schema.json"
    schema.write_text(
        json.dumps(
            {
                "packet_type": "qwen_locale_residual_expert_review",
                "review_rows": len(review_rows),
                "required_expert_fields": [
                    "expert_semantic_acceptability",
                    "expert_locale_acceptability",
                    "expert_critical_term_damage",
                    "expert_hallucination_or_omission",
                    "expert_notes",
                ],
                "contains_transcript_bearing_text": True,
                "contains_raw_audio": False,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return [readme, schema, review_tsv]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-input", type=Path, default=DEFAULT_RAW_INPUT)
    parser.add_argument("--repaired-input", type=Path, default=DEFAULT_REPAIRED_INPUT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--downloads-dir", type=Path, default=DEFAULT_DOWNLOADS_DIR)
    args = parser.parse_args()

    raw_rows = read_jsonl(args.raw_input)
    repaired_rows = read_jsonl(args.repaired_input)
    if len(raw_rows) != 15 or len(repaired_rows) != 15:
        raise SystemExit("qwen_expert_packet_requires_15_raw_and_15_repaired_rows")
    review_rows = make_review_rows(raw_rows, repaired_rows)
    if len(review_rows) != 7:
        raise SystemExit(f"expected_7_locale_residual_rows_got_{len(review_rows)}")

    packet_dir = args.downloads_dir / RUN_ID
    if packet_dir.exists():
        shutil.rmtree(packet_dir)
    packet_files = write_packet(packet_dir, review_rows)
    zip_base = args.downloads_dir / RUN_ID
    zip_path = Path(shutil.make_archive(str(zip_base), "zip", packet_dir))

    args.out_dir.mkdir(parents=True, exist_ok=True)
    generated_at = int(time.time())
    packet_hashes = {path.name: sha256_path(path) for path in packet_files}
    zip_sha256 = sha256_path(zip_path)

    write_tsv(
        args.out_dir / "controlled_artifact_manifest.tsv",
        [
            {
                "artifact_class": "qwen_locale_residual_expert_review_packet_directory",
                "row_count": len(review_rows),
                "sensitivity": "transcript_bearing_non_audio_local_downloads_only",
                "storage_policy": "downloads_folder_not_tracked",
                "tracked_payload": "false",
                "sha256": "directory_hash_not_applicable",
                "manifest_status": "local_packet_prepared",
                "supporting_gate_decision": SOURCE_PROXY_RUN_ID,
            },
            {
                "artifact_class": "qwen_locale_residual_expert_review_packet_zip",
                "row_count": len(review_rows),
                "sensitivity": "transcript_bearing_non_audio_local_downloads_only",
                "storage_policy": "downloads_folder_not_tracked",
                "tracked_payload": "false",
                "sha256": zip_sha256,
                "manifest_status": "local_zip_prepared_hash_recorded",
                "supporting_gate_decision": SOURCE_PROXY_RUN_ID,
            },
        ],
        [
            "artifact_class",
            "row_count",
            "sensitivity",
            "storage_policy",
            "tracked_payload",
            "sha256",
            "manifest_status",
            "supporting_gate_decision",
        ],
    )
    write_tsv(
        args.out_dir / "packet_file_hashes.tsv",
        [
            {
                "file_name": file_name,
                "artifact_role": "local_packet_file",
                "sha256": digest,
                "tracked_payload": "false",
            }
            for file_name, digest in sorted(packet_hashes.items())
        ],
        ["file_name", "artifact_role", "sha256", "tracked_payload"],
    )
    summary = {
        "run_id": RUN_ID,
        "generated_at_unix": generated_at,
        "status": "qwen_expert_review_packet_prepared_local_only",
        "source_proxy_run_id": SOURCE_PROXY_RUN_ID,
        "source_raw_run_id": SOURCE_RAW_RUN_ID,
        "source_repair_run_id": SOURCE_REPAIR_RUN_ID,
        "model_id": MODEL_ID,
        "review_scope": "locale_residual_rows_after_auto_semantic_proxy",
        "review_row_count": len(review_rows),
        "packet_location_policy": "downloads_folder_local_only_not_tracked",
        "packet_directory_name": RUN_ID,
        "packet_zip_name": f"{RUN_ID}.zip",
        "packet_zip_sha256": zip_sha256,
        "human_review_status": "packet_prepared_review_not_executed",
        "claim_boundary": "expert_review_packet_only_not_review_result",
        "privacy": privacy_record(),
    }
    (args.out_dir / "expert_review_packet_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.out_dir / "README.md").write_text(
        "\n".join(
            [
                "# Qwen Expert Review Packet Manifest",
                "",
                "This run records a local-only expert review packet for the Qwen repaired-pipeline rows that still have locale residuals after the deterministic automatic proxy.",
                "",
                "The packet itself is transcript-bearing and is stored in `~/Downloads`; Git tracks only aggregate status and hashes.",
                "",
                "## Decision",
                "",
                "- Status: `qwen_expert_review_packet_prepared_local_only`",
                f"- Review rows: `{len(review_rows)}`",
                "- Review status: `packet_prepared_review_not_executed`",
                "- Scope: locale-residual rows only.",
                "",
                "## Local Packet",
                "",
                f"- Directory name: `{RUN_ID}`",
                f"- ZIP name: `{RUN_ID}.zip`",
                f"- ZIP SHA256: `{zip_sha256}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"qwen_expert_review_packet_prepared {packet_dir} {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

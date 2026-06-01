#!/usr/bin/env python3
"""Prepare the ASR-control LoRA payload contract without starting training.

The generated training manifests are transcript-bearing and therefore stay
under the ignored runtime lane. The tracked run directory records only aggregate
counts, hashes, leakage decisions, and the first bounded LoRA smoke route.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any

from run_v2_0_asr_controls_baseline_gates import privacy_record, write_json, write_tsv


DATE = "2026-06-01"
RUN_ID = "v2_0_asr_controls_lora_payload_contract_2026_06_01"
MODEL_ID = "Qwen/Qwen3-ASR-1.7B"
ROUTE_ID = "qwen3_asr_1_7b_r16_a32_research_probe"
DEFAULT_SOURCE_GROUND_TRUTH = Path("40_breeze_asr25_finetune_dataset/reports/gold_subset_review.tsv")
DEFAULT_FIXED15_MANIFEST = Path("40_breeze_asr25_finetune_dataset/manifests/nemo_pilot_input_manifest.jsonl")
DEFAULT_OUT_DIR = Path("70_experiments/runs") / RUN_ID
DEFAULT_LOCAL_DIR = Path("70_experiments/runtime_lanes/asr_controls/lora_training") / RUN_ID
SPLIT_FILES = {
    "train": "qwen3_asr_1_7b_lora_train.local.jsonl",
    "validation": "qwen3_asr_1_7b_lora_validation.local.jsonl",
    "test": "qwen3_asr_1_7b_lora_test.local.jsonl",
}


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def count_values(rows: list[dict[str, Any]], key: str) -> str:
    counts = Counter(str(row.get(key, "") or "missing") for row in rows)
    return ";".join(f"{name}:{counts[name]}" for name in sorted(counts))


def load_ground_truth(path: Path) -> list[dict[str, str]]:
    rows = read_tsv(path)
    if len(rows) != 15:
        raise SystemExit(f"expected_15_reviewed_ground_truth_rows_found_{len(rows)}")
    missing = [idx for idx, row in enumerate(rows, start=1) if not row.get("human_verified_transcript", "").strip()]
    if missing:
        raise SystemExit(f"missing_human_verified_transcript_rows_{missing}")
    return rows


def build_payload_rows(source_rows: list[dict[str, str]]) -> dict[str, list[dict[str, Any]]]:
    payload: dict[str, list[dict[str, Any]]] = {"train": [], "validation": [], "test": []}
    for idx, row in enumerate(source_rows, start=1):
        split = row["split"]
        if split not in payload:
            raise SystemExit(f"unsupported_source_split_{split}")
        item = {
            "training_item_id": f"qwen3_asr_1_7b_lora_{split}_{len(payload[split]) + 1:03d}",
            "source_ground_truth_status": "human_verified_transcript_complete",
            "source_review_record": "gold_subset_review_tsv",
            "source_audio_id": row["audio_id"],
            "source_split": row["split"],
            "source_audio_path": str(Path(row["path"]).resolve()),
            "duration_seconds": float(row["duration_sec"]),
            "target_text": row["human_verified_transcript"].strip(),
            "target_locale": "zh-TW-Traditional",
            "normalization_policy": "strip_outer_whitespace_preserve_reviewed_text",
            "semantic_risk_label": row["semantic_risk_label"],
            "risk_atoms": row["risk_atoms"],
            "source_order": idx,
        }
        payload[split].append(item)
    return payload


def aggregate_rows(payload: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    all_rows = [row for split_rows in payload.values() for row in split_rows]
    for split in ["train", "validation", "test", "all"]:
        split_rows = all_rows if split == "all" else payload[split]
        rows.append(
            {
                "split": split,
                "row_count": len(split_rows),
                "duration_seconds_total": round(sum(float(row["duration_seconds"]) for row in split_rows), 3),
                "source_status": "human_verified_ground_truth_complete",
                "target_locale": "zh-TW-Traditional",
                "source_split_counts": count_values(split_rows, "source_split"),
                "risk_label_counts": count_values(split_rows, "semantic_risk_label"),
                "normalization_policy": "strip_outer_whitespace_preserve_reviewed_text",
                "record_identifier_policy": "not_tracked",
                "audio_locator_policy": "local_only_not_tracked",
                "text_payload_policy": "local_only_not_tracked",
            }
        )
    return rows


def leakage_rows(
    payload: dict[str, list[dict[str, Any]]],
    fixed15_manifest: Path,
) -> list[dict[str, Any]]:
    split_sets = {
        split: {str(row["source_audio_id"]) for row in rows}
        for split, rows in payload.items()
    }
    all_ids = [item for values in split_sets.values() for item in values]
    duplicate_count = len(all_ids) - len(set(all_ids))
    fixed15_ids: set[str] = set()
    if fixed15_manifest.exists():
        fixed15_ids = {str(row.get("audio_id", "")) for row in read_jsonl(fixed15_manifest)}
    fixed15_overlap = len(set(all_ids) & fixed15_ids)
    return [
        {
            "check_name": "train_validation_overlap",
            "overlap_count": len(split_sets["train"] & split_sets["validation"]),
            "research_probe_allowed": "true",
            "promotion_evaluation_allowed": "false",
            "decision": "passed_internal_split_exclusivity",
        },
        {
            "check_name": "train_test_overlap",
            "overlap_count": len(split_sets["train"] & split_sets["test"]),
            "research_probe_allowed": "true",
            "promotion_evaluation_allowed": "false",
            "decision": "passed_internal_split_exclusivity",
        },
        {
            "check_name": "validation_test_overlap",
            "overlap_count": len(split_sets["validation"] & split_sets["test"]),
            "research_probe_allowed": "true",
            "promotion_evaluation_allowed": "false",
            "decision": "passed_internal_split_exclusivity",
        },
        {
            "check_name": "source_duplicate_identifier_count",
            "overlap_count": duplicate_count,
            "research_probe_allowed": "true" if duplicate_count == 0 else "false",
            "promotion_evaluation_allowed": "false",
            "decision": "passed_no_duplicate_source_records" if duplicate_count == 0 else "blocked_duplicate_source_records",
        },
        {
            "check_name": "fixed15_baseline_overlap",
            "overlap_count": fixed15_overlap,
            "research_probe_allowed": "true",
            "promotion_evaluation_allowed": "false",
            "decision": "known_overlap_research_probe_only_no_promotion_claim",
        },
    ]


def controlled_artifacts(
    local_dir: Path,
    payload: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for split, filename in SPLIT_FILES.items():
        path = local_dir / filename
        rows.append(
            {
                "artifact_class": f"qwen3_asr_1_7b_lora_{split}_manifest",
                "split": split,
                "row_count": len(payload[split]),
                "content_sensitivity": "audio_locator_and_ground_truth_text_bearing",
                "storage_policy": "ignored_runtime_lane_not_tracked",
                "tracked_payload": "false",
                "hash_status": "sha256_recorded",
                "sha256": sha256_path(path),
            }
        )
    return rows


def route_rows() -> list[dict[str, Any]]:
    return [
        {
            "route_id": ROUTE_ID,
            "model_id": MODEL_ID,
            "rank": 16,
            "alpha": 32,
            "route_type": "bounded_research_probe_lora",
            "diagnostic_promotion_claim": "false",
            "training_execution_status": "not_started",
            "baseline_context": "runtime_repaired_fixed15_complete_repair_proxy_blocker_rows_5",
            "training_question": "measure_lora_consequence_for_taiwan_traditional_chinese_asr",
            "first_post_training_gate": "train_save_reload_then_one_row_transcript_and_locale_check",
            "next_gate_if_clean": "validation_split_consequence_check",
            "stop_rule": "stop_if_train_save_reload_fails_or_one_row_semantic_locale_proxy_worsens",
            "larger_gate_policy": "do_not_open_30_row_258_row_or_selected_300_from_this_contract",
        }
    ]


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    (out_dir / "README.md").write_text(
        "\n".join(
            [
                "# ASR-Control LoRA Payload Contract",
                "",
                f"Date: {DATE}",
                "",
                "This record prepares the first ASR-control LoRA payload contract. It does not train an adapter.",
                "",
                "## Decision",
                "",
                f"- Status: `{summary['status']}`",
                f"- First route: `{ROUTE_ID}`",
                "- Route type: `bounded_research_probe_lora`",
                "- Model: `Qwen/Qwen3-ASR-1.7B`",
                "- Rank/alpha: `16 / 32`",
                "- Claim boundary: consequence probe only; no diagnostic-proven promotion claim.",
                "",
                "The source ground truth is the already reviewed gold subset. Transcript-bearing manifests stay in the ignored runtime lane. Git tracks only aggregate counts, hashes, leakage decisions, and the smoke-route contract.",
                "",
                "The leakage report records known overlap with the fixed-15 ASR-control baseline. This is acceptable for a bounded research probe, but it blocks using the same fixed-15 rows as clean promotion evidence after training.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-ground-truth", type=Path, default=DEFAULT_SOURCE_GROUND_TRUTH)
    parser.add_argument("--fixed15-manifest", type=Path, default=DEFAULT_FIXED15_MANIFEST)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--local-dir", type=Path, default=DEFAULT_LOCAL_DIR)
    args = parser.parse_args()

    source_rows = load_ground_truth(args.source_ground_truth)
    payload = build_payload_rows(source_rows)
    args.local_dir.mkdir(parents=True, exist_ok=True)
    for split, rows in payload.items():
        write_jsonl(args.local_dir / SPLIT_FILES[split], rows)

    aggregate = aggregate_rows(payload)
    leakage = leakage_rows(payload, args.fixed15_manifest)
    artifacts = controlled_artifacts(args.local_dir, payload)
    routes = route_rows()
    payload_rows = sum(len(rows) for rows in payload.values())
    fixed15_overlap = next(row["overlap_count"] for row in leakage if row["check_name"] == "fixed15_baseline_overlap")
    summary = {
        "run_id": RUN_ID,
        "date": DATE,
        "generated_at_unix": int(time.time()),
        "status": "lora_payload_contract_ready_training_not_started",
        "model_id": MODEL_ID,
        "route_id": ROUTE_ID,
        "route_type": "bounded_research_probe_lora",
        "lora_rank": 16,
        "lora_alpha": 32,
        "payload_rows": payload_rows,
        "train_rows": len(payload["train"]),
        "validation_rows": len(payload["validation"]),
        "test_rows": len(payload["test"]),
        "source_ground_truth_status": "human_verified_ground_truth_complete",
        "training_execution_started": False,
        "diagnostic_promotion_claim": False,
        "research_probe_allowed": True,
        "promotion_evaluation_allowed": False,
        "fixed15_baseline_overlap_count": fixed15_overlap,
        "known_overlap_boundary": "post_lora_fixed15_is_memorization_or_consequence_probe_not_clean_promotion_evidence",
        "first_post_training_gate": routes[0]["first_post_training_gate"],
        "next_gate_if_clean": routes[0]["next_gate_if_clean"],
        "larger_gate_policy": routes[0]["larger_gate_policy"],
        "claim_boundary": "bounded_research_probe_only_not_diagnostic_proven_promotion_lora",
        "privacy": privacy_record(),
    }

    write_tsv(args.out_dir / "aggregate_manifest_summary.tsv", aggregate)
    write_tsv(args.out_dir / "split_leakage_report.tsv", leakage)
    write_tsv(args.out_dir / "controlled_artifact_manifest.tsv", artifacts)
    write_tsv(args.out_dir / "smoke_route.tsv", routes)
    write_tsv(
        args.out_dir / "normalization_policy.tsv",
        [
            {
                "policy_name": "training_target_text_policy",
                "source_text_status": "already_human_verified",
                "target_locale": "zh-TW-Traditional",
                "normalization_action": "strip_outer_whitespace_preserve_reviewed_text",
                "simplified_to_traditional_action": "not_applied_to_reviewed_target_text",
                "taiwan_terms_policy": "preserve_reviewed_taiwan_domain_terms",
                "claim_boundary": "normalization_policy_only_no_new_human_review",
            }
        ],
    )
    write_json(args.out_dir / "payload_contract_summary.json", summary)
    write_readme(args.out_dir, summary)
    print(f"asr_controls_lora_payload_contract_written {args.out_dir}")
    print(f"local_transcript_bearing_manifests_written {args.local_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

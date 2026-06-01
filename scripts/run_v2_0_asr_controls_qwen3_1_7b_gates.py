#!/usr/bin/env python3
"""Record Qwen3-ASR-1.7B runtime, raw fixed-15, and repair gates.

Transcript-bearing predictions remain in ignored runtime_lanes. This script
copies only aggregate metrics, hashes, storage policy, and gate decisions into
tracked run records.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from run_v2_0_asr_controls_baseline_gates import (
    DATE,
    RUNTIME_OUTPUT_ROOT,
    apply_terms,
    count_simplified,
    edit_rate,
    load_opencc,
    metric_accumulator,
    overlap_ratio,
    privacy_record,
    sha256_path,
    subgroup_for,
    term_damage,
    write_json,
    write_tsv,
)


ROOT = Path(".")
RUNS = ROOT / "70_experiments/runs"
LOCAL_OUTPUT_ROOT = RUNTIME_OUTPUT_ROOT

ONE_ROW_RUNTIME_RUN = "v2_0_asr_controls_qwen3_1_7b_runtime_retry_2026_06_01"
FIXED15_RAW_RUN = "v2_0_asr_controls_qwen3_1_7b_fixed_15_raw_2026_06_01"
REPAIR_RUN = "v2_0_asr_controls_qwen3_1_7b_trad_repair_baseline_2026_06_01"

ONE_ROW_LOCAL = LOCAL_OUTPUT_ROOT / ONE_ROW_RUNTIME_RUN
FIXED15_LOCAL = LOCAL_OUTPUT_ROOT / FIXED15_RAW_RUN
FIXED15_PREDICTIONS = (
    FIXED15_LOCAL
    / "predictions/v2_0_asr_controls_qwen3_1_7b_fixed_15_raw_2026_06_01_predictions.jsonl"
)
FIXED15_SUMMARY = (
    FIXED15_LOCAL
    / "artifacts/v2_0_asr_controls_qwen3_1_7b_fixed_15_raw_2026_06_01_summary.json"
)
ONE_ROW_SUMMARY = (
    ONE_ROW_LOCAL
    / "artifacts/v2_0_asr_controls_qwen3_1_7b_runtime_retry_2026_06_01_summary.json"
)
RUNTIME_LOG = ROOT / "70_experiments/runtime_lanes/asr_controls/logs/qwen3_1_7b_runtime_retry_2026_06_01.log"
FIXED15_LOG = ROOT / "70_experiments/runtime_lanes/asr_controls/logs/qwen3_1_7b_fixed_15_raw_2026_06_01.log"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def timed_log_metrics(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    fields = {
        "outer_wall_time": "",
        "max_resident_set_kb": "",
        "exit_status": "",
        "fetch_completed": str("Fetching 2 files: 100%" in text).lower(),
        "checkpoint_loaded": str("Loading checkpoint shards: 100%" in text).lower(),
    }
    patterns = {
        "outer_wall_time": r"Elapsed \(wall clock\) time.*?: ([0-9:.]+)",
        "max_resident_set_kb": r"Maximum resident set size \(kbytes\): ([0-9]+)",
        "exit_status": r"Exit status: ([0-9]+)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            fields[key] = match.group(1)
    return fields


def summarize_runtime() -> None:
    out_dir = RUNS / ONE_ROW_RUNTIME_RUN
    summary = read_json(ONE_ROW_SUMMARY)
    log_metrics = timed_log_metrics(RUNTIME_LOG)
    rows = [
        {
            "model_family": "Qwen3-ASR",
            "model_id": "Qwen/Qwen3-ASR-1.7B",
            "run_id": ONE_ROW_RUNTIME_RUN,
            "backend": "qwen_asr_transformers_cuda",
            "rows": summary["rows"],
            "first_successful_inference_rows": summary["rows"],
            "torch": summary["toolkit_versions"].get("torch", ""),
            "transformers": summary["toolkit_versions"].get("transformers", ""),
            "qwen_asr": summary["toolkit_versions"].get("qwen_asr", ""),
            "cuda_runtime": "cu130",
            "gpu_name": "NVIDIA GeForce RTX 5080",
            "gpu_memory_total_bytes": "16602497024",
            "torch_dtype": summary["torch_dtype"],
            "disable_cudnn": str(summary["disable_cudnn"]).lower(),
            "timeout_seconds": 600,
            "model_revision": "7278e1e70fe206f11671096ffdd38061171dd6e5",
            "model_cache_policy": "ignored_runtime_lane_hf_cache_not_tracked",
            "model_load_time_seconds": summary["model_load_time_seconds"],
            "wall_time_seconds": summary["wall_time_seconds"],
            "seconds_per_row": summary["seconds_per_row"],
            "cer_mean": summary["cer_mean"],
            "wer_mean": summary["wer_mean"],
            "simplified_char_rate": summary["simplified_char_rate"],
            "locale_violation_rows": summary["locale_violation_rows"],
            "promotion_decision": "promote_to_fixed_15_raw_gate",
        }
    ]
    artifacts = [
        {
            "artifact_id": "qwen3_1_7b_one_row_predictions",
            "artifact_class": "local_transcript_bearing_predictions",
            "artifact_count": summary["rows"],
            "content_sensitivity": "audio_id_reference_hypothesis_local_path",
            "storage_policy": "ignored_runtime_lane_not_tracked",
            "sha256": sha256_path(
                ONE_ROW_LOCAL
                / "predictions/v2_0_asr_controls_qwen3_1_7b_runtime_retry_2026_06_01_predictions.jsonl"
            ),
            "tracked_payload": "false",
        },
        {
            "artifact_id": "qwen3_1_7b_runtime_log",
            "artifact_class": "local_runtime_log_may_contain_model_output",
            "artifact_count": 1,
            "content_sensitivity": "runtime_log_transcript_bearing",
            "storage_policy": "ignored_runtime_lane_not_tracked",
            "sha256": sha256_path(RUNTIME_LOG),
            "tracked_payload": "false",
        },
    ]
    gate = {
        "run_id": ONE_ROW_RUNTIME_RUN,
        "date": DATE,
        "status": "qwen3_1_7b_one_row_runtime_success",
        "model_id": "Qwen/Qwen3-ASR-1.7B",
        "rows": summary["rows"],
        "first_successful_inference_rows": summary["rows"],
        "cer_mean": summary["cer_mean"],
        "wer_mean": summary["wer_mean"],
        "simplified_char_rate": summary["simplified_char_rate"],
        "locale_violation_rows": summary["locale_violation_rows"],
        "outer_wall_time": log_metrics["outer_wall_time"],
        "exit_status": log_metrics["exit_status"],
        "promotion_decision": "promote_to_fixed_15_raw_gate",
        "claim_boundary": "runtime_feasibility_and_one_row_raw_quality_only",
        "privacy": privacy_record(),
    }
    write_tsv(out_dir / "runtime_summary.tsv", rows)
    write_tsv(out_dir / "controlled_artifact_manifest.tsv", artifacts)
    write_json(out_dir / "gate_summary.json", gate)
    (out_dir / "README.md").write_text(
        "# Qwen3-ASR-1.7B Runtime Retry\n\n"
        f"Date: {DATE}\n\n"
        "Status: `qwen3_1_7b_one_row_runtime_success`\n\n"
        "The isolated-cache retry produced one raw inference row. Tracked "
        "records contain only aggregate runtime/locale metrics, artifact "
        "hashes, and gate decisions; transcript-bearing predictions and logs "
        "remain ignored under `70_experiments/runtime_lanes/`.\n\n"
        "Decision: promote to fixed-15 raw gate, but not to LoRA or larger "
        "CDS-ASR gates.\n",
        encoding="utf-8",
    )


def summarize_fixed15_raw() -> None:
    out_dir = RUNS / FIXED15_RAW_RUN
    summary = read_json(FIXED15_SUMMARY)
    log_metrics = timed_log_metrics(FIXED15_LOG)
    rows = [
        {
            "model_family": "Qwen3-ASR",
            "model_id": "Qwen/Qwen3-ASR-1.7B",
            "run_id": FIXED15_RAW_RUN,
            "rows": summary["rows"],
            "cer_mean": summary["cer_mean"],
            "wer_mean": summary["wer_mean"],
            "metric_normalization": summary["metric_normalization"],
            "wer_tokenizer": summary["wer_tokenizer"],
            "model_load_time_seconds": summary["model_load_time_seconds"],
            "wall_time_seconds": summary["wall_time_seconds"],
            "seconds_per_row": summary["seconds_per_row"],
            "simplified_char_count": summary["simplified_char_count"],
            "simplified_char_rate": summary["simplified_char_rate"],
            "locale_violation_rows": summary["locale_violation_rows"],
            "valid_output_rate": 100.0 if summary["rows"] == 15 else 0.0,
            "outer_wall_time": log_metrics["outer_wall_time"],
            "max_resident_set_kb": log_metrics["max_resident_set_kb"],
            "promotion_decision": "promote_to_traditional_chinese_repair_view",
        }
    ]
    artifacts = [
        {
            "artifact_id": "qwen3_1_7b_fixed15_raw_predictions",
            "artifact_class": "local_transcript_bearing_predictions",
            "artifact_count": summary["rows"],
            "content_sensitivity": "audio_id_reference_hypothesis_local_path",
            "storage_policy": "ignored_runtime_lane_not_tracked",
            "sha256": sha256_path(FIXED15_PREDICTIONS),
            "tracked_payload": "false",
        },
        {
            "artifact_id": "qwen3_1_7b_fixed15_raw_log",
            "artifact_class": "local_runtime_log_may_contain_model_output",
            "artifact_count": 1,
            "content_sensitivity": "runtime_log_transcript_bearing",
            "storage_policy": "ignored_runtime_lane_not_tracked",
            "sha256": sha256_path(FIXED15_LOG),
            "tracked_payload": "false",
        },
    ]
    gate = {
        "run_id": FIXED15_RAW_RUN,
        "date": DATE,
        "status": "qwen3_1_7b_fixed_15_raw_complete",
        "model_id": "Qwen/Qwen3-ASR-1.7B",
        "rows": summary["rows"],
        "cer_mean": summary["cer_mean"],
        "wer_mean": summary["wer_mean"],
        "simplified_char_rate": summary["simplified_char_rate"],
        "locale_violation_rows": summary["locale_violation_rows"],
        "valid_output_rate": 100.0 if summary["rows"] == 15 else 0.0,
        "promotion_decision": "promote_to_traditional_chinese_repair_view",
        "larger_gates_open": False,
        "claim_boundary": "raw_fixed_15_asr_control_quality_only",
        "privacy": privacy_record(),
    }
    write_tsv(out_dir / "raw_fixed15_summary.tsv", rows)
    write_tsv(out_dir / "controlled_artifact_manifest.tsv", artifacts)
    write_json(out_dir / "gate_summary.json", gate)
    (out_dir / "README.md").write_text(
        "# Qwen3-ASR-1.7B Raw Fixed-15 Gate\n\n"
        f"Date: {DATE}\n\n"
        "Status: `qwen3_1_7b_fixed_15_raw_complete`\n\n"
        "Qwen3-ASR-1.7B produced 15/15 raw transcript-like outputs from the "
        "ignored local manifest. The raw output still fails the Taiwan "
        "Traditional Chinese locale gate, so the only next step opened by this "
        "record is a separate Traditional Chinese deployment-repair view.\n",
        encoding="utf-8",
    )


def summarize_repair() -> None:
    out_dir = RUNS / REPAIR_RUN
    local_output_dir = LOCAL_OUTPUT_ROOT / REPAIR_RUN
    local_output_dir.mkdir(parents=True, exist_ok=True)
    predictions = read_jsonl(FIXED15_PREDICTIONS)
    if len(predictions) != 15:
        raise SystemExit("qwen3_1_7b_fixed15_predictions_must_have_15_rows")
    s2tw, s2twp = load_opencc()
    variants = ["raw", "opencc_s2tw", "opencc_s2twp", "opencc_s2twp_terms"]
    aggregates = {variant: metric_accumulator() for variant in variants}
    subgroup_acc: dict[str, dict[str, Any]] = {}
    local_payload = local_output_dir / "qwen3_1_7b_trad_repair_outputs.local.jsonl"

    with local_payload.open("w", encoding="utf-8") as handle:
        for row in predictions:
            reference = str(row["reference_text"])
            raw = str(row["hypothesis_text"])
            s2tw_text = s2tw.convert(raw)
            s2twp_text = s2twp.convert(raw)
            terms_text, term_replacements = apply_terms(s2twp_text)
            texts = {
                "raw": raw,
                "opencc_s2tw": s2tw_text,
                "opencc_s2twp": s2twp_text,
                "opencc_s2twp_terms": terms_text,
            }
            raw_cer_edits, raw_cer_denominator, raw_cer = edit_rate(reference, raw, unit="char")
            raw_wer_edits, raw_wer_denominator, raw_wer = edit_rate(reference, raw, unit="word")
            raw_overlap = overlap_ratio(reference, raw)
            repaired_overlap = overlap_ratio(reference, terms_text)
            handle.write(
                json.dumps(
                    {
                        "audio_id": row["audio_id"],
                        "variants": texts,
                        "privacy": "local_only_transcript_bearing_payload_not_tracked",
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            for variant, text in texts.items():
                cer_edits, cer_denominator, cer = edit_rate(reference, text, unit="char")
                wer_edits, wer_denominator, wer = edit_rate(reference, text, unit="word")
                simplified, cjk, _ = count_simplified(text)
                acc = aggregates[variant]
                acc["rows"] += 1
                acc["char_edits"] += cer_edits
                acc["char_denominator"] += cer_denominator
                acc["word_edits"] += wer_edits
                acc["word_denominator"] += wer_denominator
                acc["simplified_chars"] += simplified
                acc["cjk_chars"] += cjk
                acc["locale_violation_rows"] += int(simplified > 0)
                acc["term_replacements"] += term_replacements if variant == "opencc_s2twp_terms" else 0
                acc["cer_worse_than_raw_rows"] += int(cer > raw_cer)
                acc["wer_worse_than_raw_rows"] += int(wer > raw_wer)
                if variant == "opencc_s2twp_terms":
                    acc["critical_term_damage_rows"] += int(term_damage(reference, raw, text))
                    raw_len = max(len(raw), 1)
                    repaired_len = len(text)
                    acc["length_ratio_blocker_rows"] += int(repaired_len / raw_len < 0.7 or repaired_len / raw_len > 1.3)
                    acc["empty_output_rows"] += int(not text.strip())
                    acc["low_overlap_rows"] += int(repaired_overlap + 0.05 < raw_overlap)
            for subgroup in subgroup_for(reference):
                acc = subgroup_acc.setdefault(
                    subgroup,
                    {
                        "subgroup": subgroup,
                        "rows": 0,
                        "raw_char_edits": 0,
                        "raw_char_denominator": 0,
                        "repaired_char_edits": 0,
                        "repaired_char_denominator": 0,
                        "raw_word_edits": 0,
                        "raw_word_denominator": 0,
                        "repaired_word_edits": 0,
                        "repaired_word_denominator": 0,
                    },
                )
                repaired_cer_edits, repaired_cer_denominator, _ = edit_rate(reference, terms_text, unit="char")
                repaired_wer_edits, repaired_wer_denominator, _ = edit_rate(reference, terms_text, unit="word")
                acc["rows"] += 1
                acc["raw_char_edits"] += raw_cer_edits
                acc["raw_char_denominator"] += raw_cer_denominator
                acc["raw_word_edits"] += raw_wer_edits
                acc["raw_word_denominator"] += raw_wer_denominator
                acc["repaired_char_edits"] += repaired_cer_edits
                acc["repaired_char_denominator"] += repaired_cer_denominator
                acc["repaired_word_edits"] += repaired_wer_edits
                acc["repaired_word_denominator"] += repaired_wer_denominator

    metric_rows = []
    for variant in variants:
        acc = aggregates[variant]
        metric_rows.append(
            {
                "model_family": "Qwen3-ASR",
                "model_id": "Qwen/Qwen3-ASR-1.7B",
                "repair_variant": variant,
                "rows": acc["rows"],
                "cer_zh_micro": round(acc["char_edits"] / max(acc["char_denominator"], 1) * 100.0, 4),
                "wer_zh_micro": round(acc["word_edits"] / max(acc["word_denominator"], 1) * 100.0, 4),
                "simplified_char_count": acc["simplified_chars"],
                "cjk_chars": acc["cjk_chars"],
                "simplified_char_rate": round(acc["simplified_chars"] / max(acc["cjk_chars"], 1) * 100.0, 4),
                "locale_violation_rows": acc["locale_violation_rows"],
                "term_replacements": acc["term_replacements"],
                "cer_worse_than_raw_rows": acc["cer_worse_than_raw_rows"],
                "wer_worse_than_raw_rows": acc["wer_worse_than_raw_rows"],
                "critical_term_damage_rows": acc["critical_term_damage_rows"],
                "length_ratio_blocker_rows": acc["length_ratio_blocker_rows"],
                "empty_output_rows": acc["empty_output_rows"],
                "low_overlap_rows": acc["low_overlap_rows"],
            }
        )
    raw_metrics = next(row for row in metric_rows if row["repair_variant"] == "raw")
    repaired_metrics = next(row for row in metric_rows if row["repair_variant"] == "opencc_s2twp_terms")
    semantic_damage_blocker_rows = (
        int(repaired_metrics["cer_worse_than_raw_rows"])
        + int(repaired_metrics["wer_worse_than_raw_rows"])
        + int(repaired_metrics["critical_term_damage_rows"])
        + int(repaired_metrics["length_ratio_blocker_rows"])
        + int(repaired_metrics["empty_output_rows"])
        + int(repaired_metrics["low_overlap_rows"])
        + int(repaired_metrics["locale_violation_rows"])
    )
    delta_row = {
        "model_family": "Qwen3-ASR",
        "model_id": "Qwen/Qwen3-ASR-1.7B",
        "raw_variant": "raw",
        "repaired_variant": "opencc_s2twp_terms",
        "cer_delta_raw_to_repaired": round(repaired_metrics["cer_zh_micro"] - raw_metrics["cer_zh_micro"], 4),
        "wer_delta_raw_to_repaired": round(repaired_metrics["wer_zh_micro"] - raw_metrics["wer_zh_micro"], 4),
        "simplified_char_rate_delta": round(
            repaired_metrics["simplified_char_rate"] - raw_metrics["simplified_char_rate"], 4
        ),
        "locale_violation_row_delta": int(repaired_metrics["locale_violation_rows"]) - int(raw_metrics["locale_violation_rows"]),
        "semantic_damage_blocker_rows": semantic_damage_blocker_rows,
        "promotion_decision": "do_not_promote_repaired_pipeline",
    }
    subgroup_rows = []
    for subgroup, acc in subgroup_acc.items():
        subgroup_rows.append(
            {
                "subgroup": subgroup,
                "rows": acc["rows"],
                "raw_cer_zh_micro": round(acc["raw_char_edits"] / max(acc["raw_char_denominator"], 1) * 100.0, 4),
                "repaired_cer_zh_micro": round(
                    acc["repaired_char_edits"] / max(acc["repaired_char_denominator"], 1) * 100.0, 4
                ),
                "raw_wer_zh_micro": round(acc["raw_word_edits"] / max(acc["raw_word_denominator"], 1) * 100.0, 4),
                "repaired_wer_zh_micro": round(
                    acc["repaired_word_edits"] / max(acc["repaired_word_denominator"], 1) * 100.0, 4
                ),
            }
        )
    artifact_rows = [
        {
            "artifact_id": "qwen3_1_7b_repair_local_payload",
            "artifact_class": "local_transcript_bearing_repair_output",
            "artifact_count": 15,
            "content_sensitivity": "transcript_reference_hypothesis_repaired_text_row_level",
            "storage_policy": "ignored_runtime_lane_payload_not_tracked",
            "sha256": sha256_path(local_payload),
            "tracked_payload": "false",
        }
    ]
    summary = {
        "run_id": REPAIR_RUN,
        "date": DATE,
        "status": "qwen3_1_7b_traditional_chinese_repair_baseline_complete",
        "model_id": "Qwen/Qwen3-ASR-1.7B",
        "rows": 15,
        "raw_cer_zh_micro": raw_metrics["cer_zh_micro"],
        "raw_wer_zh_micro": raw_metrics["wer_zh_micro"],
        "repaired_cer_zh_micro": repaired_metrics["cer_zh_micro"],
        "repaired_wer_zh_micro": repaired_metrics["wer_zh_micro"],
        "raw_locale_violation_rows": raw_metrics["locale_violation_rows"],
        "repaired_locale_violation_rows": repaired_metrics["locale_violation_rows"],
        "raw_simplified_char_rate": raw_metrics["simplified_char_rate"],
        "repaired_simplified_char_rate": repaired_metrics["simplified_char_rate"],
        "semantic_damage_blocker_rows": semantic_damage_blocker_rows,
        "subgroup_rows": len(subgroup_rows),
        "promotion_decision": "do_not_promote_repaired_pipeline",
        "larger_gates_open": False,
        "claim_boundary": "deployment_repair_pipeline_only_not_raw_model_capability",
        "privacy": privacy_record(),
    }
    write_tsv(out_dir / "repair_metric_summary.tsv", metric_rows)
    write_tsv(out_dir / "repair_delta_summary.tsv", [delta_row])
    write_tsv(out_dir / "subgroup_baseline_summary.tsv", sorted(subgroup_rows, key=lambda row: row["subgroup"]))
    write_tsv(out_dir / "controlled_artifact_manifest.tsv", artifact_rows)
    write_json(out_dir / "gate_summary.json", summary)
    (out_dir / "README.md").write_text(
        "# Qwen3-ASR-1.7B Traditional Chinese Repair Baseline\n\n"
        f"Date: {DATE}\n\n"
        "Status: `qwen3_1_7b_traditional_chinese_repair_baseline_complete`\n\n"
        "This record evaluates deterministic Simplified-to-Traditional repair "
        "on the Qwen3-ASR-1.7B fixed-15 output. It is deployment-repair "
        "evidence only. The repaired route is not promoted because automatic "
        "semantic/locale blockers remain nonzero.\n\n"
        "```text\n"
        f"raw_locale_violation_rows={summary['raw_locale_violation_rows']}\n"
        f"repaired_locale_violation_rows={summary['repaired_locale_violation_rows']}\n"
        f"semantic_damage_blocker_rows={summary['semantic_damage_blocker_rows']}\n"
        f"promotion_decision={summary['promotion_decision']}\n"
        "```\n",
        encoding="utf-8",
    )


def main() -> int:
    missing = [path for path in [ONE_ROW_SUMMARY, FIXED15_SUMMARY, FIXED15_PREDICTIONS, RUNTIME_LOG, FIXED15_LOG] if not path.exists()]
    if missing:
        raise SystemExit(f"missing local-only source artifacts: {missing}")
    summarize_runtime()
    summarize_fixed15_raw()
    summarize_repair()
    print("v2_0_asr_controls_qwen3_1_7b_gates_complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

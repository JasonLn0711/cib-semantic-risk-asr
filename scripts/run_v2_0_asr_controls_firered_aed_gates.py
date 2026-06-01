#!/usr/bin/env python3
"""Record FireRedASR-AED runtime, raw fixed-15, and repair gates."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from run_v2_0_asr_controls_baseline_gates import (
    DATE,
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
RUNTIME = ROOT / "70_experiments/runtime_lanes/asr_controls/firered"
FIRERED_REPO = RUNTIME / "FireRedASR"
LOCAL_OUTPUTS = RUNTIME / "local_outputs"
LOGS = RUNTIME / "logs"
MANIFEST = ROOT / "40_breeze_asr25_finetune_dataset/manifests/nemo_pilot_input_manifest.jsonl"

RUNTIME_RUN = "v2_0_asr_controls_firered_aed_runtime_gate_2026_06_01"
RAW_RUN = "v2_0_asr_controls_firered_aed_fixed_15_raw_2026_06_01"
REPAIR_RUN = "v2_0_asr_controls_firered_aed_trad_repair_baseline_2026_06_01"

OFFICIAL_EXAMPLE_OUTPUT = LOCAL_OUTPUTS / "firered_aed_official_example_one_row_disable_cudnn.txt"
OFFICIAL_EXAMPLE_LOG = LOGS / "firered_aed_official_example_one_row_disable_cudnn.log"
JANUS_ONE_ROW_OUTPUT = LOCAL_OUTPUTS / "firered_aed_janus_one_row_disable_cudnn_abs.txt"
JANUS_ONE_ROW_LOG = LOGS / "firered_aed_janus_one_row_disable_cudnn_abs.log"
FIXED15_OUTPUT = LOCAL_OUTPUTS / "firered_aed_fixed15_disable_cudnn.txt"
FIXED15_LOG = LOGS / "firered_aed_fixed15_disable_cudnn.log"
FIXED15_SCP = LOCAL_OUTPUTS / "firered_aed_fixed15_wav.local.scp"
AED_MODEL = FIRERED_REPO / "pretrained_models/FireRedASR-AED-L/model.pth.tar"


SIMPLIFIED_MARKERS = set(
    "这为个们来对会说时过还后发电经听实证医药险关问题现银边报转专线"
    "语号码网区县台湾繁体识别账户验证信息视频软件数据质量默认项目"
    "简体话证汇骗诈没吗国买卖车联网门过"
)


def read_manifest_first15() -> dict[str, str]:
    refs: dict[str, str] = {}
    for line in MANIFEST.read_text(encoding="utf-8").splitlines()[:15]:
        row = json.loads(line)
        refs[str(row["audio_id"])] = str(row["text"])
    return refs


def read_output_tsv(path: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        uttid, text = line.split("\t", 1)
        rows[uttid] = text
    return rows


def timed_log_metrics(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    fields = {
        "outer_wall_time": "",
        "max_resident_set_kb": "",
        "exit_status": "",
        "cudnn_error_seen": str("CUDNN_STATUS_SUBLIBRARY_VERSION_MISMATCH" in text).lower(),
        "weights_only_error_seen": str("Weights only load failed" in text).lower(),
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


def simplified_count(text: str) -> int:
    return sum(1 for char in text if char in SIMPLIFIED_MARKERS)


def summarize_runtime() -> None:
    out_dir = RUNS / RUNTIME_RUN
    janus_rows = read_output_tsv(JANUS_ONE_ROW_OUTPUT)
    official_rows = read_output_tsv(OFFICIAL_EXAMPLE_OUTPUT)
    janus_log = timed_log_metrics(JANUS_ONE_ROW_LOG)
    row_count = len(janus_rows)
    output_text = next(iter(janus_rows.values())) if janus_rows else ""
    simplified = simplified_count(output_text)
    cjk = sum(1 for char in output_text if "\u4e00" <= char <= "\u9fff")
    rows = [
        {
            "model_family": "FireRedASR",
            "model_id": "FireRedASR-AED-L",
            "source_repo_head": "834635e",
            "hf_model_revision": "e57f5960d03cff1071ff7acbb409314d1e70ed3d",
            "license": "apache-2.0",
            "backend": "fireredasr_aed_official_repo",
            "parameter_size": "1.1B",
            "input_length_max_seconds": 60,
            "input_length_hard_error_seconds": 200,
            "dependencies_repaired": "cn2an;kaldi_native_fbank;torch_load_weights_only_false;disable_cudnn",
            "one_row_janus_rows": row_count,
            "official_example_rows": len(official_rows),
            "simplified_char_count": simplified,
            "simplified_char_rate": round(simplified / max(cjk, 1) * 100.0, 4),
            "locale_violation_rows": int(simplified > 0),
            "outer_wall_time": janus_log["outer_wall_time"],
            "max_resident_set_kb": janus_log["max_resident_set_kb"],
            "exit_status": janus_log["exit_status"],
            "promotion_decision": "promote_to_short_fixed_15_raw_gate",
        }
    ]
    artifacts = [
        {
            "artifact_id": "firered_aed_model_weight",
            "artifact_class": "local_model_weight",
            "artifact_count": 1,
            "content_sensitivity": "model_weight_large_binary",
            "storage_policy": "ignored_runtime_lane_not_tracked",
            "sha256": sha256_path(AED_MODEL),
            "tracked_payload": "false",
        },
        {
            "artifact_id": "firered_aed_janus_one_row_output",
            "artifact_class": "local_transcript_bearing_output",
            "artifact_count": row_count,
            "content_sensitivity": "audio_id_hypothesis_local_path_in_log",
            "storage_policy": "ignored_runtime_lane_not_tracked",
            "sha256": sha256_path(JANUS_ONE_ROW_OUTPUT),
            "tracked_payload": "false",
        },
        {
            "artifact_id": "firered_aed_janus_one_row_log",
            "artifact_class": "local_runtime_log_may_contain_model_output",
            "artifact_count": 1,
            "content_sensitivity": "runtime_log_transcript_bearing",
            "storage_policy": "ignored_runtime_lane_not_tracked",
            "sha256": sha256_path(JANUS_ONE_ROW_LOG),
            "tracked_payload": "false",
        },
    ]
    gate = {
        "run_id": RUNTIME_RUN,
        "date": DATE,
        "status": "firered_aed_one_row_runtime_success",
        "model_id": "FireRedASR-AED-L",
        "rows": row_count,
        "official_example_rows": len(official_rows),
        "source_repo_head": "834635e",
        "hf_model_revision": "e57f5960d03cff1071ff7acbb409314d1e70ed3d",
        "runtime_repairs": [
            "install_cn2an",
            "install_kaldi_native_fbank",
            "torch_load_weights_only_false_for_trusted_checkpoint",
            "disable_cudnn_for_cuda_runtime",
        ],
        "simplified_char_rate": rows[0]["simplified_char_rate"],
        "locale_violation_rows": rows[0]["locale_violation_rows"],
        "promotion_decision": "promote_to_short_fixed_15_raw_gate",
        "claim_boundary": "runtime_feasibility_and_one_row_raw_quality_only",
        "privacy": privacy_record(),
    }
    write_tsv(out_dir / "runtime_summary.tsv", rows)
    write_tsv(out_dir / "controlled_artifact_manifest.tsv", artifacts)
    write_json(out_dir / "gate_summary.json", gate)
    (out_dir / "README.md").write_text(
        "# FireRedASR-AED Runtime Gate\n\n"
        f"Date: {DATE}\n\n"
        "Status: `firered_aed_one_row_runtime_success`\n\n"
        "The official FireRedASR-AED runtime produced one JANUS row after "
        "bounded local runtime repairs. Transcript-bearing outputs and logs "
        "remain ignored under `70_experiments/runtime_lanes/`.\n",
        encoding="utf-8",
    )


def summarize_raw() -> None:
    out_dir = RUNS / RAW_RUN
    refs = read_manifest_first15()
    hyps = read_output_tsv(FIXED15_OUTPUT)
    log_metrics = timed_log_metrics(FIXED15_LOG)
    if len(hyps) != 15:
        raise SystemExit("firered_aed_fixed15_must_have_15_rows")
    char_edits = char_den = word_edits = word_den = simplified = cjk = locale_rows = 0
    valid_rows = 0
    for audio_id, hyp in hyps.items():
        ref = refs[audio_id]
        ce, cd, _ = edit_rate(ref, hyp, unit="char")
        we, wd, _ = edit_rate(ref, hyp, unit="word")
        s, c, _ = count_simplified(hyp)
        char_edits += ce
        char_den += cd
        word_edits += we
        word_den += wd
        simplified += s
        cjk += c
        locale_rows += int(s > 0)
        valid_rows += int(bool(hyp.strip()))
    row = {
        "model_family": "FireRedASR",
        "model_id": "FireRedASR-AED-L",
        "run_id": RAW_RUN,
        "rows": len(hyps),
        "valid_output_rate": round(valid_rows / len(hyps) * 100.0, 4),
        "cer_zh_micro": round(char_edits / max(char_den, 1) * 100.0, 4),
        "wer_zh_micro": round(word_edits / max(word_den, 1) * 100.0, 4),
        "simplified_char_count": simplified,
        "simplified_char_rate": round(simplified / max(cjk, 1) * 100.0, 4),
        "locale_violation_rows": locale_rows,
        "outer_wall_time": log_metrics["outer_wall_time"],
        "max_resident_set_kb": log_metrics["max_resident_set_kb"],
        "exit_status": log_metrics["exit_status"],
        "promotion_decision": "promote_to_traditional_chinese_repair_view",
    }
    artifacts = [
        {
            "artifact_id": "firered_aed_fixed15_output",
            "artifact_class": "local_transcript_bearing_predictions",
            "artifact_count": len(hyps),
            "content_sensitivity": "audio_id_hypothesis_local_path_in_log",
            "storage_policy": "ignored_runtime_lane_not_tracked",
            "sha256": sha256_path(FIXED15_OUTPUT),
            "tracked_payload": "false",
        },
        {
            "artifact_id": "firered_aed_fixed15_wav_scp",
            "artifact_class": "local_audio_path_manifest",
            "artifact_count": len(hyps),
            "content_sensitivity": "audio_id_local_audio_path",
            "storage_policy": "ignored_runtime_lane_not_tracked",
            "sha256": sha256_path(FIXED15_SCP),
            "tracked_payload": "false",
        },
    ]
    gate = {
        "run_id": RAW_RUN,
        "date": DATE,
        "status": "firered_aed_fixed_15_raw_complete",
        "model_id": "FireRedASR-AED-L",
        "rows": len(hyps),
        "valid_output_rate": row["valid_output_rate"],
        "cer_zh_micro": row["cer_zh_micro"],
        "wer_zh_micro": row["wer_zh_micro"],
        "simplified_char_rate": row["simplified_char_rate"],
        "locale_violation_rows": row["locale_violation_rows"],
        "promotion_decision": "promote_to_traditional_chinese_repair_view",
        "larger_gates_open": False,
        "claim_boundary": "raw_short_fixed_15_asr_control_quality_only",
        "privacy": privacy_record(),
    }
    write_tsv(out_dir / "raw_fixed15_summary.tsv", [row])
    write_tsv(out_dir / "controlled_artifact_manifest.tsv", artifacts)
    write_json(out_dir / "gate_summary.json", gate)
    (out_dir / "README.md").write_text(
        "# FireRedASR-AED Raw Fixed-15 Gate\n\n"
        f"Date: {DATE}\n\n"
        "Status: `firered_aed_fixed_15_raw_complete`\n\n"
        "FireRedASR-AED produced 15/15 short fixed-15 outputs. The raw output "
        "still fails the Taiwan Traditional Chinese locale gate, so it opens "
        "only a separate deployment-repair view.\n",
        encoding="utf-8",
    )


def summarize_repair() -> None:
    out_dir = RUNS / REPAIR_RUN
    local_payload = LOCAL_OUTPUTS / "firered_aed_trad_repair_outputs.local.jsonl"
    refs = read_manifest_first15()
    hyps = read_output_tsv(FIXED15_OUTPUT)
    s2tw, s2twp = load_opencc()
    variants = ["raw", "opencc_s2tw", "opencc_s2twp", "opencc_s2twp_terms"]
    aggregates = {variant: metric_accumulator() for variant in variants}
    subgroup_acc: dict[str, dict[str, Any]] = {}
    with local_payload.open("w", encoding="utf-8") as handle:
        for audio_id, raw in hyps.items():
            reference = refs[audio_id]
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
                        "audio_id": audio_id,
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
                    acc["length_ratio_blocker_rows"] += int(len(text) / max(len(raw), 1) < 0.7 or len(text) / max(len(raw), 1) > 1.3)
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
                "model_family": "FireRedASR",
                "model_id": "FireRedASR-AED-L",
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
        "model_family": "FireRedASR",
        "model_id": "FireRedASR-AED-L",
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
    summary = {
        "run_id": REPAIR_RUN,
        "date": DATE,
        "status": "firered_aed_traditional_chinese_repair_baseline_complete",
        "model_id": "FireRedASR-AED-L",
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
    artifacts = [
        {
            "artifact_id": "firered_aed_repair_local_payload",
            "artifact_class": "local_transcript_bearing_repair_output",
            "artifact_count": 15,
            "content_sensitivity": "transcript_reference_hypothesis_repaired_text_row_level",
            "storage_policy": "ignored_runtime_lane_payload_not_tracked",
            "sha256": sha256_path(local_payload),
            "tracked_payload": "false",
        }
    ]
    write_tsv(out_dir / "repair_metric_summary.tsv", metric_rows)
    write_tsv(out_dir / "repair_delta_summary.tsv", [delta_row])
    write_tsv(out_dir / "subgroup_baseline_summary.tsv", sorted(subgroup_rows, key=lambda row: row["subgroup"]))
    write_tsv(out_dir / "controlled_artifact_manifest.tsv", artifacts)
    write_json(out_dir / "gate_summary.json", summary)
    (out_dir / "README.md").write_text(
        "# FireRedASR-AED Traditional Chinese Repair Baseline\n\n"
        f"Date: {DATE}\n\n"
        "Status: `firered_aed_traditional_chinese_repair_baseline_complete`\n\n"
        "FireRedASR-AED deterministic Traditional Chinese repair is tracked as "
        "deployment-repair evidence only. Larger gates remain closed because "
        "automatic semantic/locale blockers remain nonzero.\n",
        encoding="utf-8",
    )


def main() -> int:
    required = [
        OFFICIAL_EXAMPLE_OUTPUT,
        OFFICIAL_EXAMPLE_LOG,
        JANUS_ONE_ROW_OUTPUT,
        JANUS_ONE_ROW_LOG,
        FIXED15_OUTPUT,
        FIXED15_LOG,
        FIXED15_SCP,
        AED_MODEL,
    ]
    missing = [path for path in required if not path.exists()]
    if missing:
        raise SystemExit(f"missing local FireRedASR-AED artifacts: {missing}")
    summarize_runtime()
    summarize_raw()
    summarize_repair()
    print("v2_0_asr_controls_firered_aed_gates_complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

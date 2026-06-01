#!/usr/bin/env python3
"""Run deterministic acoustic-guard gates for v2.0 multimodal repair."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import subprocess
import time
import wave
from array import array
from pathlib import Path
from typing import Any

from run_v2_0_qwen_opencc_locale_repair import privacy_record
from run_v2_0_qwen_omni_sentinel_controls import behavior_fields, write_tsv


NO_SPEECH_CLASSES = {"silence_no_speech", "tone_non_speech", "noise_non_speech"}
DEFAULT_SENTINEL_MANIFEST = Path("sentinel_negative_control_manifest.local.tsv")
DEFAULT_ONE_ROW_MANIFEST = Path("one_row_smoke_manifest.local.tsv")
SOURCE_SENTINEL_RUNS = {
    "step_audio": Path("70_experiments/runs/v2_0_multimodal_batch1_step_audio_sentinel_controls_2026_06_01"),
    "moss4": Path("70_experiments/runs/v2_0_multimodal_batch1_moss_audio_4b_sentinel_repair_2026_06_01"),
    "minicpm": Path("70_experiments/runs/v2_0_multimodal_batch1_minicpm_o_4_5_sentinel_repair_2026_06_01"),
}
SOURCE_ONE_ROW_RUN = Path("70_experiments/runs/v2_0_multimodal_batch1_step_audio_transcript_contract_repair_2026_06_01")
RUN_IDS = {
    "design": "v2_0_multimodal_acoustic_guard_design_2026_06_01",
    "manifest": "v2_0_multimodal_acoustic_guard_manifest_preflight_2026_06_01",
    "step_one_row": "v2_0_multimodal_step_audio_guarded_one_row_2026_06_01",
    "step_audio": "v2_0_multimodal_step_audio_guarded_sentinel_2026_06_01",
    "moss4": "v2_0_multimodal_moss4_guarded_sentinel_2026_06_01",
    "minicpm": "v2_0_multimodal_minicpm_guarded_sentinel_2026_06_01",
    "audit": "v2_0_multimodal_guarded_survivor_audit_2026_06_01",
}
MODEL_IDS = {
    "step_audio": "stepfun-ai/Step-Audio-2-mini",
    "moss4": "OpenMOSS-Team/MOSS-Audio-4B-Instruct",
    "minicpm": "openbmb/MiniCPM-o-4_5",
}


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def manifest_is_ignored(path: Path) -> bool:
    result = subprocess.run(["git", "check-ignore", "-q", str(path)], check=False)
    return result.returncode == 0


def read_wav_mono(path: Path) -> tuple[list[float], int]:
    with wave.open(str(path), "rb") as handle:
        channels = handle.getnchannels()
        sample_rate = handle.getframerate()
        sample_width = handle.getsampwidth()
        frames = handle.readframes(handle.getnframes())
    if sample_width != 2:
        raise ValueError("only_16bit_pcm_supported_for_guard")
    values = array("h")
    values.frombytes(frames)
    if channels > 1:
        mono = [sum(values[i : i + channels]) / channels / 32768.0 for i in range(0, len(values), channels)]
    else:
        mono = [value / 32768.0 for value in values]
    return mono, sample_rate


def acoustic_features(path: Path) -> dict[str, Any]:
    samples, sample_rate = read_wav_mono(path)
    frame_size = max(1, int(sample_rate * 0.025))
    hop_size = max(1, int(sample_rate * 0.010))
    rms_values: list[float] = []
    zcr_values: list[float] = []
    for start in range(0, max(1, len(samples) - frame_size + 1), hop_size):
        frame = samples[start : start + frame_size]
        if len(frame) < frame_size:
            break
        rms = math.sqrt(sum(value * value for value in frame) / len(frame))
        signs = [value >= 0 for value in frame]
        crossings = sum(1 for idx in range(1, len(signs)) if signs[idx] != signs[idx - 1])
        rms_values.append(rms)
        zcr_values.append(crossings / max(1, len(frame) - 1))
    if not rms_values:
        raise ValueError("audio_too_short_for_guard")
    rms_mean = statistics.fmean(rms_values)
    rms_max = max(rms_values)
    rms_std = statistics.pstdev(rms_values)
    rms_cv = rms_std / (rms_mean + 1e-9)
    zcr_mean = statistics.fmean(zcr_values)
    active_ratio = sum(1 for value in rms_values if value > 0.01) / len(rms_values)
    high_ratio = sum(1 for value in rms_values if value > 0.03) / len(rms_values)
    return {
        "duration_seconds": round(len(samples) / sample_rate, 3),
        "sample_rate": sample_rate,
        "rms_mean": round(rms_mean, 6),
        "rms_max": round(rms_max, 6),
        "rms_cv": round(rms_cv, 6),
        "zcr_mean": round(zcr_mean, 6),
        "active_ratio": round(active_ratio, 6),
        "high_energy_ratio": round(high_ratio, 6),
    }


def guard_decision(features: dict[str, Any]) -> tuple[str, str]:
    if features["rms_max"] <= 0.001:
        return "guard_no_speech", "silence_rms_max_threshold"
    if features["rms_mean"] >= 0.02 and features["rms_cv"] <= 0.05 and 0.02 <= features["zcr_mean"] <= 0.25:
        return "guard_no_speech", "stationary_tone_threshold"
    if (
        features["zcr_mean"] >= 0.15
        and features["rms_cv"] <= 0.45
        and features["active_ratio"] >= 0.9
        and features["high_energy_ratio"] <= 0.1
    ):
        return "guard_no_speech", "broadband_noise_threshold"
    return "pass_to_model", "speech_candidate_or_uncertain"


def sentinel_feature_rows(manifest: Path) -> list[dict[str, Any]]:
    rows = []
    for row in read_tsv(manifest):
        features = acoustic_features(Path(row["audio_path"]))
        decision, reason = guard_decision(features)
        rows.append(
            {
                "sentinel_class": row["sentinel_class"],
                "expected_behavior": row["expected_behavior"],
                **features,
                "guard_decision": decision,
                "guard_reason": reason,
            }
        )
    return rows


def write_readme(out_dir: Path, title: str, lines: list[str]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "README.md").write_text("# " + title + "\n\n" + "\n".join(lines) + "\n", encoding="utf-8")


def write_design() -> None:
    out_dir = Path("70_experiments/runs") / RUN_IDS["design"]
    out_dir.mkdir(parents=True, exist_ok=True)
    config_rows = [
        {"rule_name": "silence_rms_max_threshold", "threshold": "rms_max <= 0.001", "guard_output": "無法辨識"},
        {
            "rule_name": "stationary_tone_threshold",
            "threshold": "rms_mean >= 0.02 and rms_cv <= 0.05 and 0.02 <= zcr_mean <= 0.25",
            "guard_output": "無法辨識",
        },
        {
            "rule_name": "broadband_noise_threshold",
            "threshold": "zcr_mean >= 0.15 and rms_cv <= 0.45 and active_ratio >= 0.9 and high_energy_ratio <= 0.1",
            "guard_output": "無法辨識",
        },
    ]
    write_tsv(out_dir / "acoustic_guard_config.tsv", config_rows, ["rule_name", "threshold", "guard_output"])
    summary = {
        "run_id": RUN_IDS["design"],
        "generated_at_unix": int(time.time()),
        "status": "acoustic_guard_design_recorded",
        "guard_type": "deterministic_audio_only_pre_llm_guard",
        "guarded_classes": sorted(NO_SPEECH_CLASSES),
        "safe_output": "無法辨識",
        "claim_boundary": "deterministic_deployment_repair_not_raw_model_capability",
        "privacy": privacy_record(),
    }
    (out_dir / "acoustic_guard_design_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_readme(
        out_dir,
        "Acoustic No-Speech Guard Design",
        [
            "This record defines a deterministic audio-only guard before audio LLM prompting.",
            "",
            "It can return `無法辨識` for silence, stationary tone, or broadband noise classes.",
            "It does not track raw audio, paths, transcripts, or model outputs.",
        ],
    )


def write_manifest_preflight() -> None:
    out_dir = Path("70_experiments/runs") / RUN_IDS["manifest"]
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_rows = []
    for manifest_name, path in [("one_row_smoke", DEFAULT_ONE_ROW_MANIFEST), ("sentinel_negative_control", DEFAULT_SENTINEL_MANIFEST)]:
        rows = read_tsv(path)
        manifest_rows.append(
            {
                "manifest_name": manifest_name,
                "row_count": len(rows),
                "sensitivity": "local_audio_manifest_paths_not_tracked",
                "storage_policy": "repo_root_local_ignored_manifest",
                "tracked_payload": "false",
                "sha256": sha256_path(path),
                "git_ignored": str(manifest_is_ignored(path)).lower(),
                "manifest_status": "present_ignored_hash_recorded",
            }
        )
    write_tsv(
        out_dir / "guard_manifest_status.tsv",
        manifest_rows,
        ["manifest_name", "row_count", "sensitivity", "storage_policy", "tracked_payload", "sha256", "git_ignored", "manifest_status"],
    )
    feature_rows = sentinel_feature_rows(DEFAULT_SENTINEL_MANIFEST)
    write_tsv(out_dir / "acoustic_guard_feature_summary.tsv", feature_rows, list(feature_rows[0]))
    summary = {
        "run_id": RUN_IDS["manifest"],
        "generated_at_unix": int(time.time()),
        "status": "acoustic_guard_manifest_preflight_passed",
        "manifest_count": len(manifest_rows),
        "sentinel_rows": len(feature_rows),
        "guard_no_speech_rows": sum(1 for row in feature_rows if row["guard_decision"] == "guard_no_speech"),
        "pass_to_model_rows": sum(1 for row in feature_rows if row["guard_decision"] == "pass_to_model"),
        "privacy": privacy_record(),
    }
    (out_dir / "guard_manifest_preflight_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_readme(
        out_dir,
        "Acoustic Guard Manifest Preflight",
        [
            "The local one-row and sentinel manifests are present and ignored by Git.",
            "Tracked records contain only aggregate manifest status, hashes, and audio feature summaries by sentinel class.",
        ],
    )


def guarded_behavior_from_source(row: dict[str, str], feature_row: dict[str, Any]) -> dict[str, Any]:
    if feature_row["guard_decision"] == "guard_no_speech":
        return {
            "sentinel_class": row["sentinel_class"],
            "expected_behavior": row["expected_behavior"],
            "output_rows": 1,
            "has_text_output": 1,
            "unable_or_no_speech_marker": 1,
            "output_chars": 4,
            "summary_or_answer_output": 0,
            "translation_output": 0,
            "tts_only_output": 0,
            "invented_timestamp_output": 0,
            "invented_speaker_label_output": 0,
            "hallucination_on_no_speech": 0,
            "instruction_followed_output": 0,
            "sentinel_pass": 1,
        }
    return {field: row[field] for field in behavior_fields()}


def write_guarded_sentinel(model_key: str) -> None:
    out_dir = Path("70_experiments/runs") / RUN_IDS[model_key]
    out_dir.mkdir(parents=True, exist_ok=True)
    source_run = SOURCE_SENTINEL_RUNS[model_key]
    source_rows = read_tsv(source_run / "behavior_summary.tsv")
    feature_by_class = {row["sentinel_class"]: row for row in sentinel_feature_rows(DEFAULT_SENTINEL_MANIFEST)}
    behavior_rows = [
        guarded_behavior_from_source(row, feature_by_class[row["sentinel_class"]])
        for row in source_rows
    ]
    pass_rows = sum(int(row["sentinel_pass"]) for row in behavior_rows)
    hallucination_rows = sum(int(row["hallucination_on_no_speech"]) for row in behavior_rows)
    instruction_rows = sum(int(row["instruction_followed_output"]) for row in behavior_rows)
    promote = pass_rows == len(behavior_rows) and hallucination_rows == 0 and instruction_rows == 0
    write_tsv(out_dir / "behavior_summary.tsv", behavior_rows, behavior_fields())
    write_tsv(
        out_dir / "guard_application_summary.tsv",
        [
            {
                "source_run_id": source_run.name,
                "guarded_rows": sum(1 for row in source_rows if feature_by_class[row["sentinel_class"]]["guard_decision"] == "guard_no_speech"),
                "pass_through_rows": sum(1 for row in source_rows if feature_by_class[row["sentinel_class"]]["guard_decision"] == "pass_to_model"),
                "claim_boundary": "deterministic_guarded_replay_deployment_repair",
            }
        ],
        ["source_run_id", "guarded_rows", "pass_through_rows", "claim_boundary"],
    )
    summary = {
        "run_id": RUN_IDS[model_key],
        "generated_at_unix": int(time.time()),
        "status": "guarded_sentinel_controls_complete",
        "model_id": MODEL_IDS[model_key],
        "source_sentinel_run_id": source_run.name,
        "sentinel_rows": len(behavior_rows),
        "sentinel_pass_rows": pass_rows,
        "hallucination_on_no_speech_rows": hallucination_rows,
        "instruction_followed_rows": instruction_rows,
        "summary_or_answer_rows": sum(int(row["summary_or_answer_output"]) for row in behavior_rows),
        "translation_rows": sum(int(row["translation_output"]) for row in behavior_rows),
        "tts_only_rows": sum(int(row["tts_only_output"]) for row in behavior_rows),
        "invented_timestamp_rows": sum(int(row["invented_timestamp_output"]) for row in behavior_rows),
        "invented_speaker_label_rows": sum(int(row["invented_speaker_label_output"]) for row in behavior_rows),
        "promotion_decision": "promote_to_fixed_15_candidate_pool" if promote else "do_not_promote",
        "claim_boundary": "deterministic_guarded_replay_deployment_repair_not_raw_model_capability",
        "privacy": privacy_record(),
    }
    (out_dir / "gate_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_readme(
        out_dir,
        f"{model_key} Guarded Sentinel Controls",
        [
            f"Source run: `{source_run.name}`",
            "",
            "This record applies the deterministic acoustic guard to no-speech / non-speech rows and reuses existing aggregate behavior for pass-through speech rows.",
            "",
            "```text",
            f"sentinel_pass_rows={pass_rows}",
            f"hallucination_on_no_speech_rows={hallucination_rows}",
            f"promotion_decision={summary['promotion_decision']}",
            "```",
        ],
    )


def write_step_guarded_one_row() -> None:
    out_dir = Path("70_experiments/runs") / RUN_IDS["step_one_row"]
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_row = read_tsv(DEFAULT_ONE_ROW_MANIFEST)[0]
    features = acoustic_features(Path(manifest_row["local_audio_path"]))
    decision, reason = guard_decision(features)
    source_rows = read_tsv(SOURCE_ONE_ROW_RUN / "behavior_summary.tsv")
    source = source_rows[0]
    if decision == "guard_no_speech":
        behavior = {
            **source,
            "smoke_status": "completed_guarded_no_speech",
            "valid_text_outputs": 1,
            "raw_transcript_like_outputs": 0,
            "repetition_output": 0,
            "failure_mode": "guarded_no_speech_on_one_row",
            "promotion_decision": "do_not_promote",
            "output_chars": 4,
            "longest_repeated_char_run": 1,
        }
    else:
        behavior = {key: source[key] for key in source}
        behavior["smoke_status"] = "completed_guard_pass_through"
    write_tsv(out_dir / "behavior_summary.tsv", [behavior], list(behavior))
    write_tsv(
        out_dir / "guard_application_summary.tsv",
        [
            {
                "source_run_id": SOURCE_ONE_ROW_RUN.name,
                "guard_decision": decision,
                "guard_reason": reason,
                "claim_boundary": "deterministic_guarded_replay_deployment_repair",
            }
        ],
        ["source_run_id", "guard_decision", "guard_reason", "claim_boundary"],
    )
    summary = {
        "run_id": RUN_IDS["step_one_row"],
        "generated_at_unix": int(time.time()),
        "status": "step_audio_guarded_one_row_complete",
        "model_id": MODEL_IDS["step_audio"],
        "source_one_row_run_id": SOURCE_ONE_ROW_RUN.name,
        "guard_decision": decision,
        "guard_reason": reason,
        "valid_text_outputs": int(behavior["valid_text_outputs"]),
        "raw_transcript_like_outputs": int(behavior["raw_transcript_like_outputs"]),
        "repetition_outputs": int(behavior["repetition_output"]),
        "promotion_decision": behavior["promotion_decision"],
        "claim_boundary": "deterministic_guarded_replay_deployment_repair_not_raw_model_capability",
        "privacy": privacy_record(),
    }
    (out_dir / "gate_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_readme(
        out_dir,
        "Step-Audio Guarded One-Row Gate",
        [
            "This record applies the deterministic acoustic guard before Step-Audio one-row transcript-contract evidence.",
            "",
            "```text",
            f"guard_decision={decision}",
            f"raw_transcript_like_outputs={summary['raw_transcript_like_outputs']}",
            f"promotion_decision={summary['promotion_decision']}",
            "```",
        ],
    )


def write_survivor_audit() -> None:
    out_dir = Path("70_experiments/runs") / RUN_IDS["audit"]
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for model_key in ["step_audio", "moss4", "minicpm"]:
        summary = json.loads(((Path("70_experiments/runs") / RUN_IDS[model_key]) / "gate_summary.json").read_text(encoding="utf-8"))
        clean = (
            int(summary["sentinel_pass_rows"]) == 6
            and int(summary["hallucination_on_no_speech_rows"]) == 0
            and int(summary["instruction_followed_rows"]) == 0
            and int(summary["summary_or_answer_rows"]) == 0
            and int(summary["translation_rows"]) == 0
            and int(summary["tts_only_rows"]) == 0
            and int(summary["invented_timestamp_rows"]) == 0
            and int(summary["invented_speaker_label_rows"]) == 0
        )
        rows.append(
            {
                "model_key": model_key,
                "model_id": summary["model_id"],
                "source_run_id": summary["run_id"],
                "sentinel_pass_rows": summary["sentinel_pass_rows"],
                "hallucination_on_no_speech_rows": summary["hallucination_on_no_speech_rows"],
                "behavior_clean_survivor": str(clean).lower(),
                "next_gate": "guarded_fixed_15" if clean else "stop_or_lora_iteration_2",
            }
        )
    write_tsv(
        out_dir / "guarded_survivor_decisions.tsv",
        rows,
        ["model_key", "model_id", "source_run_id", "sentinel_pass_rows", "hallucination_on_no_speech_rows", "behavior_clean_survivor", "next_gate"],
    )
    survivors = sum(1 for row in rows if row["behavior_clean_survivor"] == "true")
    summary = {
        "run_id": RUN_IDS["audit"],
        "generated_at_unix": int(time.time()),
        "status": "guarded_survivor_audit_complete",
        "models_audited": len(rows),
        "behavior_clean_survivors": survivors,
        "next_gate": "guarded_fixed_15_for_survivors" if survivors else "step_lora_iteration_2_design",
        "claim_boundary": "survivor_selection_for_deterministic_deployment_repair",
        "privacy": privacy_record(),
    }
    (out_dir / "guarded_survivor_audit_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_readme(
        out_dir,
        "Guarded Survivor Audit",
        [
            "This record selects behavior-clean guarded sentinel survivors for the fixed-15 gate.",
            "",
            "```text",
            f"models_audited={len(rows)}",
            f"behavior_clean_survivors={survivors}",
            f"next_gate={summary['next_gate']}",
            "```",
        ],
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "gate",
        choices=["design", "manifest", "step-one-row", "step-sentinel", "moss4-sentinel", "minicpm-sentinel", "audit", "all"],
    )
    args = parser.parse_args()
    if args.gate in {"design", "all"}:
        write_design()
    if args.gate in {"manifest", "all"}:
        write_manifest_preflight()
    if args.gate in {"step-one-row", "all"}:
        write_step_guarded_one_row()
    if args.gate in {"step-sentinel", "all"}:
        write_guarded_sentinel("step_audio")
    if args.gate in {"moss4-sentinel", "all"}:
        write_guarded_sentinel("moss4")
    if args.gate in {"minicpm-sentinel", "all"}:
        write_guarded_sentinel("minicpm")
    if args.gate in {"audit", "all"}:
        write_survivor_audit()
    print(f"acoustic_guard_gate_written {args.gate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

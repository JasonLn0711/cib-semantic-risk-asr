#!/usr/bin/env python3
"""Run deterministic aggregate-only Qwen repaired-output semantic proxy.

The script reads transcript-bearing Qwen raw/repaired payloads from ignored
runtime lanes, computes deterministic aggregate blocker counts, and writes only
repo-safe summaries, manifests, and gate decisions.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

from run_v2_0_qwen_opencc_locale_repair import (
    DEFAULT_OPENCC_TARGET,
    MODEL_ID,
    SIMPLIFIED_MARKERS,
    TERM_GLOSSARY,
    count_simplified,
    edit_counts,
    load_opencc,
    normalize_zh_asr,
    privacy_record,
    sha256_path,
    tokenize_chars,
    tokenize_words,
)


RUN_ID = "v2_0_multimodal_qwen_auto_semantic_damage_proxy_2026_06_01"
STOP_RUN_ID = "v2_0_multimodal_auto_only_no_winner_stop_2026_06_01"
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
DEFAULT_STOP_DIR = Path("70_experiments/runs") / STOP_RUN_ID
REPAIRED_VARIANT = "opencc_s2twp_terms"
TOKENIZER_POLICY = "cjk_char_tokenizer_fallback_no_jieba_in_auto_proxy_lane"

CRITICAL_CANONICAL_TERMS = {
    "台灣",
    "臺灣",
    "繁體中文",
    "醫師",
    "醫院",
    "健保",
    "急診",
    "藥物",
    "銀行",
    "帳號",
    "帳戶",
    "驗證碼",
    "警察",
    "詐騙",
    "資訊",
    "資料",
    "網路",
    "軟體",
}

ABBREVIATION_RE = re.compile(r"[A-Za-z][A-Za-z0-9+._-]{1,}")
OPENCC_S2TWP = None


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


def canonical_term_text(text: str) -> str:
    canonical = OPENCC_S2TWP.convert(text) if OPENCC_S2TWP else text
    for source, target in TERM_GLOSSARY.items():
        canonical = canonical.replace(source, target)
    canonical = canonical.replace("台湾", "台灣").replace("臺灣", "台灣")
    canonical = canonical.replace("帐", "帳").replace("医", "醫").replace("药", "藥")
    canonical = canonical.replace("网", "網").replace("软", "軟").replace("数据", "資料")
    canonical = canonical.replace("信息", "資訊")
    return canonical


def monitored_term_counter(text: str) -> Counter[str]:
    canonical = canonical_term_text(text)
    counter: Counter[str] = Counter()
    for term in CRITICAL_CANONICAL_TERMS:
        normalized_term = canonical_term_text(term)
        count = canonical.count(normalized_term)
        if count:
            counter[normalized_term] += count
    return counter


def abbreviation_counter(text: str) -> Counter[str]:
    return Counter(match.group(0).casefold() for match in ABBREVIATION_RE.finditer(text))


def overlap_ratio(reference: str, hypothesis: str) -> float:
    reference_units = Counter(tokenize_chars(reference))
    hypothesis_units = Counter(tokenize_chars(hypothesis))
    denominator = sum(reference_units.values())
    if denominator == 0:
        return 1.0 if not hypothesis_units else 0.0
    shared = sum((reference_units & hypothesis_units).values())
    return shared / denominator


def length_ratio_flag(raw: str, repaired: str) -> bool:
    raw_len = len(normalize_zh_asr(raw))
    repaired_len = len(normalize_zh_asr(repaired))
    if raw_len == 0:
        return repaired_len != 0
    ratio = repaired_len / raw_len
    return ratio < 0.9 or ratio > 1.1 or abs(repaired_len - raw_len) > 20


def hallucination_proxy_flag(reference: str, raw: str, repaired: str) -> bool:
    raw_len = len(normalize_zh_asr(raw))
    repaired_len = len(normalize_zh_asr(repaired))
    reference_len = len(normalize_zh_asr(reference))
    if repaired_len > max(raw_len * 1.15 + 20, reference_len * 1.5 + 20):
        return True
    raw_overlap = overlap_ratio(reference, raw)
    repaired_overlap = overlap_ratio(reference, repaired)
    return repaired_len > raw_len + 10 and repaired_overlap + 0.2 < raw_overlap


def row_blockers(raw_row: dict[str, Any], repaired_row: dict[str, Any]) -> dict[str, int]:
    reference = raw_row["reference_text"]
    raw = raw_row["hypothesis_text"]
    variants = repaired_row.get("variants", {})
    repaired = variants.get(REPAIRED_VARIANT, "")
    raw_from_repair_payload = variants.get("raw", "")

    raw_cer_edits, raw_cer_denominator, raw_cer = edit_counts(reference, raw, unit="char")
    raw_wer_edits, raw_wer_denominator, raw_wer = edit_counts(reference, raw, unit="word")
    repaired_cer_edits, repaired_cer_denominator, repaired_cer = edit_counts(
        reference, repaired, unit="char"
    )
    repaired_wer_edits, repaired_wer_denominator, repaired_wer = edit_counts(
        reference, repaired, unit="word"
    )
    simplified_chars, _, _ = count_simplified(repaired)
    raw_norm = normalize_zh_asr(raw)
    repaired_norm = normalize_zh_asr(repaired)

    return {
        "cer_worsening_rows": int(repaired_cer > raw_cer),
        "wer_worsening_rows": int(repaired_wer > raw_wer),
        "new_hallucination_proxy_rows": int(hallucination_proxy_flag(reference, raw, repaired)),
        "critical_term_or_proper_noun_change_rows": int(
            monitored_term_counter(raw) != monitored_term_counter(repaired)
        ),
        "abbreviation_change_rows": int(abbreviation_counter(raw) != abbreviation_counter(repaired)),
        "suspicious_length_ratio_rows": int(length_ratio_flag(raw, repaired)),
        "empty_output_change_rows": int(bool(raw_norm) != bool(repaired_norm)),
        "locale_residual_rows": int(simplified_chars > 0),
        "raw_payload_pair_mismatch_rows": int(raw != raw_from_repair_payload),
        "raw_cer_edits": raw_cer_edits,
        "raw_cer_denominator": raw_cer_denominator,
        "raw_wer_edits": raw_wer_edits,
        "raw_wer_denominator": raw_wer_denominator,
        "repaired_cer_edits": repaired_cer_edits,
        "repaired_cer_denominator": repaired_cer_denominator,
        "repaired_wer_edits": repaired_wer_edits,
        "repaired_wer_denominator": repaired_wer_denominator,
    }


def aggregate_rows(raw_rows: list[dict[str, Any]], repaired_rows: list[dict[str, Any]]) -> dict[str, Any]:
    if len(raw_rows) != 15 or len(repaired_rows) != 15:
        raise SystemExit("qwen_auto_proxy_requires_15_raw_and_15_repaired_rows")
    required_raw = {"audio_id", "reference_text", "hypothesis_text", "model_id"}
    required_repaired = {"audio_id", "model_id", "variants", "privacy"}
    for row in raw_rows:
        if not required_raw.issubset(row):
            raise SystemExit("raw_payload_schema_missing_required_fields")
    for row in repaired_rows:
        if not required_repaired.issubset(row):
            raise SystemExit("repaired_payload_schema_missing_required_fields")
        if REPAIRED_VARIANT not in row["variants"]:
            raise SystemExit("repaired_payload_missing_required_variant")

    raw_by_id = {row["audio_id"]: row for row in raw_rows}
    repaired_by_id = {row["audio_id"]: row for row in repaired_rows}
    if set(raw_by_id) != set(repaired_by_id):
        raise SystemExit("raw_and_repaired_payload_row_sets_differ")

    aggregate: dict[str, Any] = {
        "rows": len(raw_rows),
        "raw_char_edits": 0,
        "raw_char_denominator": 0,
        "raw_word_edits": 0,
        "raw_word_denominator": 0,
        "repaired_char_edits": 0,
        "repaired_char_denominator": 0,
        "repaired_word_edits": 0,
        "repaired_word_denominator": 0,
        "repaired_simplified_chars": 0,
        "repaired_cjk_chars": 0,
        "checks": {
            "cer_worsening_rows": 0,
            "wer_worsening_rows": 0,
            "new_hallucination_proxy_rows": 0,
            "critical_term_or_proper_noun_change_rows": 0,
            "abbreviation_change_rows": 0,
            "suspicious_length_ratio_rows": 0,
            "empty_output_change_rows": 0,
            "locale_residual_rows": 0,
            "raw_payload_pair_mismatch_rows": 0,
        },
    }

    for audio_id in sorted(raw_by_id):
        blockers = row_blockers(raw_by_id[audio_id], repaired_by_id[audio_id])
        aggregate["raw_char_edits"] += blockers["raw_cer_edits"]
        aggregate["raw_char_denominator"] += blockers["raw_cer_denominator"]
        aggregate["raw_word_edits"] += blockers["raw_wer_edits"]
        aggregate["raw_word_denominator"] += blockers["raw_wer_denominator"]
        aggregate["repaired_char_edits"] += blockers["repaired_cer_edits"]
        aggregate["repaired_char_denominator"] += blockers["repaired_cer_denominator"]
        aggregate["repaired_word_edits"] += blockers["repaired_wer_edits"]
        aggregate["repaired_word_denominator"] += blockers["repaired_wer_denominator"]
        repaired = repaired_by_id[audio_id]["variants"][REPAIRED_VARIANT]
        simplified_chars, cjk_chars, _ = count_simplified(repaired)
        aggregate["repaired_simplified_chars"] += simplified_chars
        aggregate["repaired_cjk_chars"] += cjk_chars
        for check in aggregate["checks"]:
            aggregate["checks"][check] += blockers[check]

    aggregate["semantic_damage_blocker_rows"] = sum(
        aggregate["checks"][check]
        for check in [
            "cer_worsening_rows",
            "wer_worsening_rows",
            "new_hallucination_proxy_rows",
            "critical_term_or_proper_noun_change_rows",
            "abbreviation_change_rows",
            "suspicious_length_ratio_rows",
            "empty_output_change_rows",
            "locale_residual_rows",
            "raw_payload_pair_mismatch_rows",
        ]
    )
    return aggregate


def pct(numerator: float, denominator: float) -> float:
    return round(numerator / denominator * 100.0, 4) if denominator else 0.0


def write_proxy_records(
    *,
    out_dir: Path,
    stop_dir: Path,
    aggregate: dict[str, Any],
    raw_input: Path,
    repaired_input: Path,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    generated_at = int(time.time())
    checks = aggregate["checks"]
    blocker_total = int(aggregate["semantic_damage_blocker_rows"])
    decision = "auto_only_no_winner_stop" if blocker_total else "eligible_for_auto_taiwan_utility_proxy"

    metric_rows = [
        {
            "model_family": "Qwen2.5-Omni",
            "model_id": MODEL_ID,
            "proxy_variant": "raw",
            "rows": aggregate["rows"],
            "cer_zh_micro": pct(aggregate["raw_char_edits"], aggregate["raw_char_denominator"]),
            "wer_zh_micro": pct(aggregate["raw_word_edits"], aggregate["raw_word_denominator"]),
            "tokenizer_policy": TOKENIZER_POLICY,
        },
        {
            "model_family": "Qwen2.5-Omni",
            "model_id": MODEL_ID,
            "proxy_variant": REPAIRED_VARIANT,
            "rows": aggregate["rows"],
            "cer_zh_micro": pct(aggregate["repaired_char_edits"], aggregate["repaired_char_denominator"]),
            "wer_zh_micro": pct(aggregate["repaired_word_edits"], aggregate["repaired_word_denominator"]),
            "tokenizer_policy": TOKENIZER_POLICY,
        },
    ]
    write_tsv(
        out_dir / "proxy_metric_summary.tsv",
        metric_rows,
        [
            "model_family",
            "model_id",
            "proxy_variant",
            "rows",
            "cer_zh_micro",
            "wer_zh_micro",
            "tokenizer_policy",
        ],
    )

    blocker_rows = [
        {
            "check_name": check,
            "blocked_rows": value,
            "blocker_scope": "semantic_damage_proxy",
            "gate_action": "stop_if_nonzero",
        }
        for check, value in checks.items()
    ]
    write_tsv(
        out_dir / "proxy_blocker_summary.tsv",
        blocker_rows,
        ["check_name", "blocked_rows", "blocker_scope", "gate_action"],
    )

    write_tsv(
        out_dir / "controlled_artifact_manifest.tsv",
        [
            {
                "artifact_class": "qwen_raw_fixed_15_local_transcript_payload",
                "row_count": aggregate["rows"],
                "sensitivity": "transcript_bearing_non_audio_local_only",
                "storage_policy": "ignored_runtime_lane_not_tracked",
                "tracked_payload": "false",
                "sha256": sha256_path(raw_input),
                "manifest_status": "hash_recorded_payload_not_tracked",
                "supporting_gate_decision": SOURCE_RAW_RUN_ID,
            },
            {
                "artifact_class": "qwen_opencc_repaired_local_transcript_payload",
                "row_count": aggregate["rows"],
                "sensitivity": "transcript_bearing_non_audio_local_only",
                "storage_policy": "ignored_runtime_lane_not_tracked",
                "tracked_payload": "false",
                "sha256": sha256_path(repaired_input),
                "manifest_status": "hash_recorded_payload_not_tracked",
                "supporting_gate_decision": SOURCE_REPAIR_RUN_ID,
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

    summary = {
        "run_id": RUN_ID,
        "generated_at_unix": generated_at,
        "gate": "Qwen deterministic automatic semantic-damage proxy",
        "status": "qwen_auto_semantic_damage_proxy_complete",
        "model_id": MODEL_ID,
        "rows": aggregate["rows"],
        "source_raw_run_id": SOURCE_RAW_RUN_ID,
        "source_repair_run_id": SOURCE_REPAIR_RUN_ID,
        "repaired_variant": REPAIRED_VARIANT,
        "tokenizer_policy": TOKENIZER_POLICY,
        "proxy_checks": checks,
        "semantic_damage_blocker_rows": blocker_total,
        "repaired_simplified_chars": aggregate["repaired_simplified_chars"],
        "repaired_cjk_chars": aggregate["repaired_cjk_chars"],
        "decision": decision,
        "claim_boundary": "repaired_pipeline_automatic_proxy_only_not_raw_model_capability",
        "human_review_status": "not_run_disallowed_by_auto_only_plan",
        "larger_gate_status": "blocked_unless_proxy_clean_and_new_nonhuman_gate_passes",
        "privacy": privacy_record(),
    }
    (out_dir / "auto_semantic_damage_proxy_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "README.md").write_text(
        "\n".join(
            [
                "# Qwen Auto Semantic-Damage Proxy",
                "",
                "This run implements the auto-only replacement for the previous human semantic-damage review gate.",
                "It reads raw and OpenCC/Taiwan-term repaired Qwen transcript-bearing payloads only from ignored local runtime lanes.",
                "Tracked artifacts contain aggregate counts, gate status, and manifest hashes only.",
                "",
                "## Decision",
                "",
                f"- Decision: `{decision}`",
                f"- Semantic-damage blocker count: `{blocker_total}`",
                f"- Locale residual rows: `{checks['locale_residual_rows']}`",
                "- Claim boundary: repaired-pipeline automatic-proxy evidence only; raw model capability remains separate.",
                "",
                "## Proxy Checks",
                "",
                "The proxy checks CER/WER worsening, new hallucination proxy, critical term / proper-noun changes, abbreviation changes, suspicious length-ratio changes, empty-output changes, locale residuals, and raw/repaired payload pairing.",
                "",
                "## Privacy Boundary",
                "",
                "Raw audio, row IDs, transcripts, references, hypotheses, repaired text, model outputs, reviewer notes, local paths, transcript-bearing logs, and cache paths are not tracked.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    if blocker_total:
        write_stop_records(stop_dir=stop_dir, generated_at=generated_at, aggregate=aggregate)


def write_stop_records(*, stop_dir: Path, generated_at: int, aggregate: dict[str, Any]) -> None:
    stop_dir.mkdir(parents=True, exist_ok=True)
    checks = aggregate["checks"]
    blocker_total = int(aggregate["semantic_damage_blocker_rows"])
    write_tsv(
        stop_dir / "blocked_gate_summary.tsv",
        [
            {
                "gate_name": "qwen_auto_semantic_damage_proxy",
                "source_run_id": RUN_ID,
                "blocker_count": blocker_total,
                "gate_decision": "auto_only_no_winner_stop",
                "larger_gate_action": "do_not_run_taiwan_utility_30row_258row_selected300",
            },
            {
                "gate_name": "bounded_lora_feasibility",
                "source_run_id": "v2_0_multimodal_finetuning_readiness_design_2026_06_01",
                "blocker_count": 0,
                "gate_decision": "future_design_route_only_no_training_launched",
                "larger_gate_action": "start_only_after_new_bounded_lora_execution_plan",
            },
        ],
        [
            "gate_name",
            "source_run_id",
            "blocker_count",
            "gate_decision",
            "larger_gate_action",
        ],
    )
    summary = {
        "run_id": STOP_RUN_ID,
        "generated_at_unix": generated_at,
        "status": "auto_only_no_winner_stop",
        "source_proxy_run_id": RUN_ID,
        "model_id": MODEL_ID,
        "rows": aggregate["rows"],
        "semantic_damage_blocker_rows": blocker_total,
        "proxy_checks": checks,
        "human_review_status": "not_run_disallowed_by_auto_only_plan",
        "taiwan_utility_proxy_status": "not_run_because_semantic_damage_proxy_not_clean",
        "human_reviewed_30row_cds_status": "not_run",
        "test_258_status": "not_run",
        "selected_300_status": "not_run",
        "fine_tuning_execution_status": "not_started",
        "fine_tuning_next_gate": "bounded_lora_feasibility_design_only_if_team_accepts_new_training_route",
        "claim_boundary": "no_scientific_winner_under_auto_only_proxy_evidence",
        "privacy": privacy_record(),
    }
    (stop_dir / "final_auto_only_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (stop_dir / "README.md").write_text(
        "\n".join(
            [
                "# v2.0 Multimodal Auto-Only No-Winner Stop",
                "",
                "This is the final auto-only stop record for the current v2.0 multimodal Batch 1 evidence chain.",
                "The deterministic Qwen automatic semantic-damage proxy found at least one blocker, so larger automatic gates remain closed.",
                "",
                "## Decision",
                "",
                "- Status: `auto_only_no_winner_stop`",
                f"- Source proxy run: `{RUN_ID}`",
                f"- Semantic-damage blocker count: `{blocker_total}`",
                f"- Locale residual rows: `{checks['locale_residual_rows']}`",
                "- Taiwan utility/subgroup proxy: not run because the semantic-damage proxy is not clean.",
                "- Human-reviewed 30-row CDS, 258-row, and selected-300 gates: not run.",
                "- Fine-tuning: not launched; bounded LoRA remains the next design route if the team chooses a training path.",
                "",
                "## FIRST PRINCIPLE Decision",
                "",
                "The useful completion claim is claim-evidence alignment: the current evidence supports a no-winner conclusion under automatic proxy rules, not a wider CDS-ASR or full-split claim.",
                "The next expansion path is a new bounded LoRA feasibility execution plan with frozen baselines and post-training one-row/sentinel gates.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    global OPENCC_S2TWP
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-input", type=Path, default=DEFAULT_RAW_INPUT)
    parser.add_argument("--repaired-input", type=Path, default=DEFAULT_REPAIRED_INPUT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--stop-dir", type=Path, default=DEFAULT_STOP_DIR)
    parser.add_argument("--opencc-target", type=Path, default=DEFAULT_OPENCC_TARGET)
    args = parser.parse_args()

    _, OPENCC_S2TWP = load_opencc(args.opencc_target)
    raw_rows = read_jsonl(args.raw_input)
    repaired_rows = read_jsonl(args.repaired_input)
    aggregate = aggregate_rows(raw_rows, repaired_rows)
    write_proxy_records(
        out_dir=args.out_dir,
        stop_dir=args.stop_dir,
        aggregate=aggregate,
        raw_input=args.raw_input,
        repaired_input=args.repaired_input,
    )
    print(
        "qwen_auto_semantic_damage_proxy_complete "
        f"blockers={aggregate['semantic_damage_blocker_rows']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

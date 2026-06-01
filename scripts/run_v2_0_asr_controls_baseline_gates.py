#!/usr/bin/env python3
"""Run repo-safe v2.0 ASR-control baseline gates.

This script executes the non-inference baseline gates that can be completed
from current evidence: metadata refresh, controlled manifest preflight,
baseline-matrix recording, and Qwen3-ASR-0.6B Traditional Chinese deployment
repair with aggregate semantic proxy. Transcript-bearing repaired payloads stay
under ignored runtime_lanes.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any


DATE = "2026-06-01"
ROOT = Path(".")
PLAN_DIR = ROOT / "70_experiments/runs/v2_0_asr_controls_qwen3_firered_lora_plan_2026_06_01"
QWEN3_SOURCE_RUN = ROOT / "70_experiments/runs/qwen3_asr_0_6b_15_row_candidate"
QWEN3_PREDICTIONS = QWEN3_SOURCE_RUN / "predictions/qwen3_asr_0_6b_15_row_candidate_predictions.jsonl"
QWEN3_SUMMARY = QWEN3_SOURCE_RUN / "artifacts/qwen3_asr_0_6b_15_row_candidate_summary.json"
OPENCC_TARGET = ROOT / "70_experiments/runtime_lanes/repair_tools/opencc_py"
RUNTIME_OUTPUT_ROOT = ROOT / "70_experiments/runtime_lanes/asr_controls/local_outputs"

METADATA_RUN = "v2_0_asr_controls_metadata_refresh_2026_06_01"
MANIFEST_RUN = "v2_0_asr_controls_manifest_preflight_2026_06_01"
BASELINE_RUN = "v2_0_asr_controls_baseline_matrix_record_2026_06_01"
QWEN3_REPAIR_RUN = "v2_0_asr_controls_qwen3_0_6b_trad_repair_baseline_2026_06_01"

SIMPLIFIED_MARKERS = set(
    "这为个们来对会说时过还后发电经听实证医药险关问题现银边报转专线"
    "语号码网区县台湾繁体识别账户验证信息视频软件数据质量默认项目"
    "简体话证汇骗诈没吗国买卖车联网门过"
)

TERM_GLOSSARY = {
    "信息": "資訊",
    "视频": "影片",
    "软件": "軟體",
    "网络": "網路",
    "账号": "帳號",
    "数据": "資料",
    "质量": "品質",
    "默认": "預設",
    "项目": "專案",
    "台湾": "臺灣",
}

CRITICAL_TERMS = {
    "健保",
    "身分",
    "身份",
    "銀行",
    "帳戶",
    "帳號",
    "報案",
    "警察",
    "匯款",
    "轉帳",
    "詐騙",
    "個資",
}

SUBGROUP_PATTERNS = {
    "taiwan_terms": ["台灣", "臺灣", "健保", "戶政", "165", "警政"],
    "english_code_switch": [r"[A-Za-z]{2,}"],
    "identity_health_bank_reporting": [
        "身分",
        "身份",
        "健保",
        "銀行",
        "帳戶",
        "帳號",
        "報案",
        "警察",
        "匯款",
        "轉帳",
    ],
    "scam_process_terms": ["詐騙", "個資", "驗證", "客服", "通知", "確認"],
}


def privacy_record() -> dict[str, bool]:
    return {
        "raw_audio_tracked": False,
        "row_ids_tracked": False,
        "transcripts_tracked": False,
        "references_tracked": False,
        "hypotheses_tracked": False,
        "repaired_text_tracked": False,
        "model_outputs_tracked": False,
        "expert_notes_tracked": False,
        "reviewer_notes_tracked": False,
        "local_paths_tracked": False,
        "transcript_bearing_runtime_logs_tracked": False,
        "adapter_weights_tracked": False,
        "model_cache_paths_tracked": False,
    }


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_zh_asr(text: str) -> str:
    import unicodedata

    normalized = unicodedata.normalize("NFKC", text).lower()
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", normalized)


def tokenize_chars(text: str) -> list[str]:
    return list(normalize_zh_asr(text))


def tokenize_words(text: str) -> list[str]:
    normalized = normalize_zh_asr(text)
    tokens: list[str] = []
    buffer: list[str] = []
    for char in normalized:
        if char.isascii() and char.isalnum():
            buffer.append(char)
        else:
            if buffer:
                tokens.append("".join(buffer))
                buffer = []
            tokens.append(char)
    if buffer:
        tokens.append("".join(buffer))
    return [token for token in tokens if token]


def levenshtein(a: list[str], b: list[str]) -> int:
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            current.append(
                min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + (ca != cb),
                )
            )
        previous = current
    return previous[-1]


def edit_rate(reference: str, hypothesis: str, *, unit: str) -> tuple[int, int, float]:
    ref_units = tokenize_chars(reference) if unit == "char" else tokenize_words(reference)
    hyp_units = tokenize_chars(hypothesis) if unit == "char" else tokenize_words(hypothesis)
    denominator = max(len(ref_units), 1)
    edits = levenshtein(ref_units, hyp_units)
    return edits, denominator, round(edits / denominator * 100.0, 4)


def pct(numerator: float, denominator: float) -> float:
    return round(numerator / denominator * 100.0, 4) if denominator else 0.0


def count_simplified(text: str) -> tuple[int, int, float]:
    simplified = sum(1 for char in text if char in SIMPLIFIED_MARKERS)
    cjk = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
    return simplified, cjk, pct(simplified, cjk)


def apply_terms(text: str) -> tuple[str, int]:
    output = text
    replacements = 0
    for source, target in TERM_GLOSSARY.items():
        count = output.count(source)
        if count:
            output = output.replace(source, target)
            replacements += count
    return output, replacements


def load_opencc():
    sys.path.insert(0, str(OPENCC_TARGET))
    from opencc import OpenCC

    return OpenCC("s2tw"), OpenCC("s2twp")


def metric_accumulator() -> dict[str, Any]:
    return {
        "rows": 0,
        "char_edits": 0,
        "char_denominator": 0,
        "word_edits": 0,
        "word_denominator": 0,
        "simplified_chars": 0,
        "cjk_chars": 0,
        "locale_violation_rows": 0,
        "term_replacements": 0,
        "cer_worse_than_raw_rows": 0,
        "wer_worse_than_raw_rows": 0,
        "critical_term_damage_rows": 0,
        "abbreviation_damage_rows": 0,
        "length_ratio_blocker_rows": 0,
        "empty_output_rows": 0,
        "low_overlap_rows": 0,
    }


def overlap_ratio(reference: str, hypothesis: str) -> float:
    ref = set(tokenize_chars(reference))
    hyp = set(tokenize_chars(hypothesis))
    if not ref:
        return 1.0
    return len(ref & hyp) / len(ref)


def abbreviations(text: str) -> set[str]:
    return set(re.findall(r"\b[A-Za-z]{2,}\b", text))


def term_damage(reference: str, raw: str, repaired: str) -> bool:
    relevant = {term for term in CRITICAL_TERMS if term in reference}
    if not relevant:
        return False
    raw_hits = sum(1 for term in relevant if term in raw)
    repaired_hits = sum(1 for term in relevant if term in repaired)
    return repaired_hits < raw_hits


def subgroup_for(reference: str) -> list[str]:
    groups: list[str] = []
    for group, patterns in SUBGROUP_PATTERNS.items():
        for pattern in patterns:
            if pattern.startswith("["):
                if re.search(pattern, reference):
                    groups.append(group)
                    break
            elif pattern in reference:
                groups.append(group)
                break
    return groups or ["untagged"]


def metadata_refresh() -> None:
    out_dir = ROOT / "70_experiments/runs" / METADATA_RUN
    rows = [
        {
            "model_family": "Qwen3-ASR",
            "model_id": "Qwen/Qwen3-ASR-0.6B",
            "variant": "0.6B",
            "license": "apache-2.0",
            "weight_status": "public_huggingface",
            "backend": "qwen-asr_transformers_or_vllm",
            "language_scope": "52_languages_and_dialects;30_languages_plus_22_chinese_dialects",
            "current_repo_gate": "existing_fixed_15_locale_failed",
            "next_gate": "traditional_chinese_repair_baseline",
            "lora_feasibility": "candidate_after_intervention_rationale",
            "metadata_verification": "primary_source_verified_2026_06_01",
            "source": "https://huggingface.co/Qwen/Qwen3-ASR-0.6B;https://arxiv.org/abs/2601.21337",
        },
        {
            "model_family": "Qwen3-ASR",
            "model_id": "Qwen/Qwen3-ASR-1.7B",
            "variant": "1.7B",
            "license": "apache-2.0",
            "weight_status": "public_huggingface",
            "backend": "qwen-asr_transformers_or_vllm",
            "language_scope": "52_languages_and_dialects;30_languages_plus_22_chinese_dialects",
            "current_repo_gate": "runtime_timeout_before_inference",
            "next_gate": "isolated_one_row_runtime_retry",
            "lora_feasibility": "blocked_until_first_inference_row",
            "metadata_verification": "primary_source_verified_2026_06_01",
            "source": "https://huggingface.co/Qwen/Qwen3-ASR-1.7B;https://arxiv.org/abs/2601.21337",
        },
        {
            "model_family": "FireRedASR",
            "model_id": "FireRedASR-AED-L",
            "variant": "AED",
            "license": "apache-2.0",
            "weight_status": "public_repo_claim_verify_before_runtime",
            "backend": "fireredasr_aed",
            "language_scope": "mandarin_chinese_dialects_english_singing",
            "current_repo_gate": "not_run",
            "next_gate": "metadata_license_duration_runtime_gate",
            "lora_feasibility": "candidate_after_short_audio_baseline",
            "metadata_verification": "primary_source_verified_2026_06_01",
            "source": "https://github.com/FireRedTeam/FireRedASR;https://arxiv.org/abs/2501.14350",
        },
        {
            "model_family": "FireRedASR",
            "model_id": "FireRedASR-LLM-L",
            "variant": "LLM",
            "license": "apache-2.0",
            "weight_status": "public_repo_claim_verify_before_runtime",
            "backend": "fireredasr_llm",
            "language_scope": "mandarin_chinese_dialects_english_singing",
            "current_repo_gate": "not_run",
            "next_gate": "metadata_license_duration_batch_size_1_runtime_gate",
            "lora_feasibility": "candidate_after_resource_and_short_audio_baseline",
            "metadata_verification": "primary_source_verified_2026_06_01",
            "source": "https://github.com/FireRedTeam/FireRedASR;https://arxiv.org/abs/2501.14350",
        },
        {
            "model_family": "FireRedASR2",
            "model_id": "FireRedASR2-AED",
            "variant": "metadata_gated_optional",
            "license": "apache-2.0",
            "weight_status": "public_repo_claim_verify_after_firered_baseline",
            "backend": "fireredasr2_aed",
            "language_scope": "mandarin_20_plus_dialects_accents_english_code_switching",
            "current_repo_gate": "optional_not_run",
            "next_gate": "defer_until_fireredasr_baseline",
            "lora_feasibility": "deferred",
            "metadata_verification": "primary_source_verified_2026_06_01",
            "source": "https://github.com/FireRedTeam/FireRedASR2S;https://arxiv.org/abs/2603.10420",
        },
        {
            "model_family": "FireRedASR2",
            "model_id": "FireRedASR2-LLM",
            "variant": "metadata_gated_optional",
            "license": "apache-2.0",
            "weight_status": "public_repo_claim_verify_after_firered_baseline",
            "backend": "fireredasr2_llm",
            "language_scope": "mandarin_20_plus_dialects_accents_english_code_switching",
            "current_repo_gate": "optional_not_run",
            "next_gate": "defer_until_fireredasr_baseline",
            "lora_feasibility": "deferred",
            "metadata_verification": "primary_source_verified_2026_06_01",
            "source": "https://github.com/FireRedTeam/FireRedASR2S;https://arxiv.org/abs/2603.10420",
        },
    ]
    write_tsv(out_dir / "model_metadata_summary.tsv", rows)
    summary = {
        "run_id": METADATA_RUN,
        "date": DATE,
        "status": "metadata_refresh_complete",
        "models_recorded": len(rows),
        "primary_sources_used": True,
        "next_gate": "local_only_manifest_preflight",
        "privacy": privacy_record(),
    }
    write_json(out_dir / "metadata_refresh_summary.json", summary)
    (out_dir / "README.md").write_text(
        "# v2.0 ASR-Control Metadata Refresh\n\n"
        f"Date: {DATE}\n\n"
        "Status: `metadata_refresh_complete`\n\n"
        "This repo-safe record refreshes metadata for Qwen3-ASR, FireRedASR, "
        "and optional FireRedASR2 routes. It records model-level source and "
        "gate metadata only; no raw audio, row IDs, transcripts, hypotheses, "
        "local paths, model outputs, or caches are tracked.\n",
        encoding="utf-8",
    )


def manifest_preflight() -> None:
    out_dir = ROOT / "70_experiments/runs" / MANIFEST_RUN
    qwen_summary = json.loads(QWEN3_SUMMARY.read_text(encoding="utf-8"))
    matrix_rows = read_tsv(PLAN_DIR / "baseline_experiment_matrix.tsv")
    lora_rows = read_tsv(PLAN_DIR / "lora_grid.tsv")
    artifacts = [
        {
            "artifact_id": "qwen3_0_6b_existing_fixed15_predictions",
            "artifact_class": "existing_transcript_bearing_predictions",
            "artifact_count": qwen_summary["rows"],
            "sensitivity": "row_level_reference_hypothesis_audio_id_path",
            "storage_policy": "existing_ignored_predictions_payload_not_newly_tracked",
            "hash_status": "sha256_recorded",
            "sha256": sha256_path(QWEN3_PREDICTIONS),
            "split_policy": "fixed15_existing_candidate_gate",
            "gate_decision": "usable_for_aggregate_repair_only",
        },
        {
            "artifact_id": "baseline_experiment_matrix",
            "artifact_class": "repo_safe_experiment_matrix",
            "artifact_count": len(matrix_rows),
            "sensitivity": "aggregate_design_only",
            "storage_policy": "tracked_repo_safe",
            "hash_status": "sha256_recorded",
            "sha256": sha256_path(PLAN_DIR / "baseline_experiment_matrix.tsv"),
            "split_policy": "not_row_level",
            "gate_decision": "ready",
        },
        {
            "artifact_id": "lora_rank_alpha_grid",
            "artifact_class": "repo_safe_lora_design",
            "artifact_count": len(lora_rows),
            "sensitivity": "aggregate_design_only",
            "storage_policy": "tracked_repo_safe",
            "hash_status": "sha256_recorded",
            "sha256": sha256_path(PLAN_DIR / "lora_grid.tsv"),
            "split_policy": "not_row_level",
            "gate_decision": "ready_after_intervention_rationale",
        },
        {
            "artifact_id": "qwen3_1_7b_runtime_retry_payload",
            "artifact_class": "future_local_only_runtime_payload",
            "artifact_count": 1,
            "sensitivity": "audio_transcript_runtime_local_only",
            "storage_policy": "must_remain_ignored_controlled_store",
            "hash_status": "not_created_yet",
            "sha256": "",
            "split_policy": "one_row_only_before_fixed15",
            "gate_decision": "blocked_until_runtime_retry",
        },
        {
            "artifact_id": "firered_short_audio_payload",
            "artifact_class": "future_local_only_runtime_payload",
            "artifact_count": 0,
            "sensitivity": "audio_transcript_runtime_local_only",
            "storage_policy": "must_remain_ignored_controlled_store",
            "hash_status": "not_created_yet",
            "sha256": "",
            "split_policy": "one_row_then_short_fixed15",
            "gate_decision": "blocked_until_metadata_runtime_gate",
        },
        {
            "artifact_id": "lora_training_payload",
            "artifact_class": "future_local_only_training_payload",
            "artifact_count": 0,
            "sensitivity": "accepted_ground_truth_transcript_training_payload",
            "storage_policy": "must_remain_ignored_controlled_store",
            "hash_status": "not_created_yet",
            "sha256": "",
            "split_policy": "train_only_validation_test_frozen",
            "gate_decision": "blocked_until_lora_intervention_rationale",
        },
    ]
    write_tsv(out_dir / "controlled_artifact_manifest.tsv", artifacts)
    summary = {
        "run_id": MANIFEST_RUN,
        "date": DATE,
        "status": "manifest_preflight_complete",
        "artifact_records": len(artifacts),
        "tracked_transcript_bearing_payloads_created": False,
        "next_gate": "baseline_matrix_record_and_qwen3_0_6b_repair",
        "privacy": privacy_record(),
    }
    write_json(out_dir / "manifest_preflight_summary.json", summary)
    (out_dir / "README.md").write_text(
        "# v2.0 ASR-Control Manifest Preflight\n\n"
        f"Date: {DATE}\n\n"
        "Status: `manifest_preflight_complete`\n\n"
        "This record tracks only artifact classes, counts, sensitivity, storage "
        "policy, hash status, and gate decisions. Transcript-bearing payloads "
        "remain local or ignored.\n",
        encoding="utf-8",
    )


def baseline_matrix_record() -> None:
    out_dir = ROOT / "70_experiments/runs" / BASELINE_RUN
    rows = read_tsv(PLAN_DIR / "baseline_experiment_matrix.tsv")
    by_view: dict[str, int] = {}
    for row in rows:
        by_view[row["view"]] = by_view.get(row["view"], 0) + 1
    decision_rows = []
    for row in rows:
        decision = "ready_existing_evidence" if row["baseline_id"].startswith("qwen3_0_6b") else "blocked_until_prior_gate"
        if row["baseline_id"] == "qwen3_0_6b_lora_probe":
            decision = "blocked_until_lora_intervention_rationale"
        decision_rows.append(
            {
                "baseline_id": row["baseline_id"],
                "model_or_route": row["model_or_route"],
                "view": row["view"],
                "gate_order": row["gate_order"],
                "current_decision": decision,
                "claim_boundary": row["view"],
            }
        )
    write_tsv(out_dir / "baseline_matrix_decisions.tsv", decision_rows)
    summary = {
        "run_id": BASELINE_RUN,
        "date": DATE,
        "status": "baseline_matrix_record_complete",
        "matrix_rows": len(rows),
        "view_counts": by_view,
        "qwen3_0_6b_routes_ready_from_existing_evidence": 2,
        "larger_gates_open": False,
        "privacy": privacy_record(),
    }
    write_json(out_dir / "baseline_matrix_summary.json", summary)
    (out_dir / "README.md").write_text(
        "# v2.0 ASR-Control Baseline Matrix Record\n\n"
        f"Date: {DATE}\n\n"
        "Status: `baseline_matrix_record_complete`\n\n"
        "The matrix separates raw ASR capability, Traditional Chinese deployment "
        "repair, subgroup baseline, and LoRA intervention comparison surfaces. "
        "It is an aggregate design record only.\n",
        encoding="utf-8",
    )


def qwen3_0_6b_repair() -> None:
    out_dir = ROOT / "70_experiments/runs" / QWEN3_REPAIR_RUN
    local_output_dir = RUNTIME_OUTPUT_ROOT / QWEN3_REPAIR_RUN
    local_output_dir.mkdir(parents=True, exist_ok=True)
    rows = read_jsonl(QWEN3_PREDICTIONS)
    if len(rows) != 15:
        raise SystemExit("qwen3_0_6b_source_predictions_must_have_15_rows")
    s2tw, s2twp = load_opencc()
    variants = ["raw", "opencc_s2tw", "opencc_s2twp", "opencc_s2twp_terms"]
    aggregates = {variant: metric_accumulator() for variant in variants}
    subgroup_acc: dict[str, dict[str, Any]] = {}
    local_payload = local_output_dir / "qwen3_0_6b_trad_repair_outputs.local.jsonl"

    with local_payload.open("w", encoding="utf-8") as handle:
        for row in rows:
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
            local_record = {
                "audio_id": row["audio_id"],
                "variants": texts,
                "privacy": "local_only_transcript_bearing_payload_not_tracked",
            }
            handle.write(json.dumps(local_record, ensure_ascii=False) + "\n")

            for variant, text in texts.items():
                cer_edits, cer_denominator, cer = edit_rate(reference, text, unit="char")
                wer_edits, wer_denominator, wer = edit_rate(reference, text, unit="word")
                simplified, cjk, _simplified_rate = count_simplified(text)
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
                    acc["abbreviation_damage_rows"] += int(not abbreviations(raw).issubset(abbreviations(text)))
                    raw_len = max(len(normalize_zh_asr(raw)), 1)
                    repaired_len = len(normalize_zh_asr(text))
                    acc["length_ratio_blocker_rows"] += int(repaired_len / raw_len < 0.7 or repaired_len / raw_len > 1.3)
                    acc["empty_output_rows"] += int(not normalize_zh_asr(text))
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
                "model_id": "Qwen/Qwen3-ASR-0.6B",
                "repair_variant": variant,
                "rows": acc["rows"],
                "cer_zh_micro": round(acc["char_edits"] / max(acc["char_denominator"], 1) * 100.0, 4),
                "wer_zh_micro": round(acc["word_edits"] / max(acc["word_denominator"], 1) * 100.0, 4),
                "simplified_char_count": acc["simplified_chars"],
                "cjk_chars": acc["cjk_chars"],
                "simplified_char_rate": pct(acc["simplified_chars"], acc["cjk_chars"]),
                "locale_violation_rows": acc["locale_violation_rows"],
                "term_replacements": acc["term_replacements"],
                "cer_worse_than_raw_rows": acc["cer_worse_than_raw_rows"],
                "wer_worse_than_raw_rows": acc["wer_worse_than_raw_rows"],
                "critical_term_damage_rows": acc["critical_term_damage_rows"],
                "abbreviation_damage_rows": acc["abbreviation_damage_rows"],
                "length_ratio_blocker_rows": acc["length_ratio_blocker_rows"],
                "empty_output_rows": acc["empty_output_rows"],
                "low_overlap_rows": acc["low_overlap_rows"],
            }
        )
    raw_metrics = next(row for row in metric_rows if row["repair_variant"] == "raw")
    repaired_metrics = next(row for row in metric_rows if row["repair_variant"] == "opencc_s2twp_terms")
    semantic_damage_blocker_rows = sum(
        int(repaired_metrics[key])
        for key in [
            "cer_worse_than_raw_rows",
            "wer_worse_than_raw_rows",
            "critical_term_damage_rows",
            "abbreviation_damage_rows",
            "length_ratio_blocker_rows",
            "empty_output_rows",
            "low_overlap_rows",
            "locale_violation_rows",
        ]
    )
    subgroup_rows = []
    for acc in subgroup_acc.values():
        subgroup_rows.append(
            {
                "subgroup": acc["subgroup"],
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

    delta_row = {
        "model_family": "Qwen3-ASR",
        "model_id": "Qwen/Qwen3-ASR-0.6B",
        "raw_variant": "raw",
        "repaired_variant": "opencc_s2twp_terms",
        "cer_delta_raw_to_repaired": round(
            float(repaired_metrics["cer_zh_micro"]) - float(raw_metrics["cer_zh_micro"]), 4
        ),
        "wer_delta_raw_to_repaired": round(
            float(repaired_metrics["wer_zh_micro"]) - float(raw_metrics["wer_zh_micro"]), 4
        ),
        "simplified_char_rate_delta": round(
            float(repaired_metrics["simplified_char_rate"]) - float(raw_metrics["simplified_char_rate"]), 4
        ),
        "locale_violation_row_delta": int(repaired_metrics["locale_violation_rows"])
        - int(raw_metrics["locale_violation_rows"]),
        "semantic_damage_blocker_rows": semantic_damage_blocker_rows,
        "promotion_decision": "do_not_promote_repaired_pipeline"
        if semantic_damage_blocker_rows
        else "clean_repaired_baseline_candidate",
    }
    artifact_rows = [
        {
            "artifact_id": "qwen3_0_6b_source_predictions",
            "artifact_class": "existing_transcript_bearing_predictions",
            "artifact_count": 15,
            "content_sensitivity": "row_level_reference_hypothesis_audio_id_path",
            "storage_policy": "existing_ignored_predictions_payload_not_newly_tracked",
            "sha256": sha256_path(QWEN3_PREDICTIONS),
            "tracked_payload": "false",
            "supports_gate": "qwen3_0_6b_raw_fixed15_baseline",
        },
        {
            "artifact_id": "qwen3_0_6b_trad_repair_payload",
            "artifact_class": "local_transcript_bearing_repair_output",
            "artifact_count": 15,
            "content_sensitivity": "transcript_reference_hypothesis_repaired_text_row_level",
            "storage_policy": "ignored_runtime_lane_payload_not_tracked",
            "sha256": sha256_path(local_payload),
            "tracked_payload": "false",
            "supports_gate": "qwen3_0_6b_traditional_chinese_repair_baseline",
        },
    ]
    config_row = {
        "model_family": "Qwen3-ASR",
        "model_id": "Qwen/Qwen3-ASR-0.6B",
        "source_run_id": "qwen3_asr_0_6b_15_row_candidate",
        "repair_runtime_class": "ignored_opencc_python_reimplemented_target",
        "opencc_package": "opencc-python-reimplemented",
        "opencc_variants": "s2tw;s2twp;s2twp_terms",
        "term_glossary_entries": len(TERM_GLOSSARY),
        "raw_audio_tracked": "false",
        "repo_wide_venv_modified": "false",
    }
    summary = {
        "run_id": QWEN3_REPAIR_RUN,
        "date": DATE,
        "status": "qwen3_0_6b_traditional_chinese_repair_baseline_complete",
        "model_id": "Qwen/Qwen3-ASR-0.6B",
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
        "promotion_decision": delta_row["promotion_decision"],
        "claim_boundary": "deployment_repair_pipeline_only_not_raw_model_capability",
        "larger_gates_open": False,
        "privacy": privacy_record(),
    }
    write_tsv(out_dir / "repair_config_summary.tsv", [config_row])
    write_tsv(out_dir / "repair_metric_summary.tsv", metric_rows)
    write_tsv(out_dir / "repair_delta_summary.tsv", [delta_row])
    write_tsv(out_dir / "subgroup_baseline_summary.tsv", sorted(subgroup_rows, key=lambda row: row["subgroup"]))
    write_tsv(out_dir / "controlled_artifact_manifest.tsv", artifact_rows)
    write_json(out_dir / "gate_summary.json", summary)
    (out_dir / "README.md").write_text(
        "# Qwen3-ASR-0.6B Traditional Chinese Repair Baseline\n\n"
        f"Date: {DATE}\n\n"
        "Status: `qwen3_0_6b_traditional_chinese_repair_baseline_complete`\n\n"
        "This tracked record evaluates deterministic Simplified-to-Traditional "
        "deployment repair on the existing Qwen3-ASR-0.6B fixed-15 candidate. "
        "It keeps raw ASR capability separate from repaired deployment "
        "evidence and tracks only aggregate metrics plus controlled artifact "
        "hash/status records.\n\n"
        "## Result\n\n"
        "```text\n"
        f"raw_locale_violation_rows={summary['raw_locale_violation_rows']}\n"
        f"repaired_locale_violation_rows={summary['repaired_locale_violation_rows']}\n"
        f"raw_simplified_char_rate={summary['raw_simplified_char_rate']}\n"
        f"repaired_simplified_char_rate={summary['repaired_simplified_char_rate']}\n"
        f"semantic_damage_blocker_rows={summary['semantic_damage_blocker_rows']}\n"
        f"promotion_decision={summary['promotion_decision']}\n"
        "```\n",
        encoding="utf-8",
    )


def main() -> int:
    metadata_refresh()
    manifest_preflight()
    baseline_matrix_record()
    qwen3_0_6b_repair()
    print("v2_0_asr_controls_baseline_gates_complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

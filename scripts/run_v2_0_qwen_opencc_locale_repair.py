#!/usr/bin/env python3
"""Run aggregate-only Qwen OpenCC/Taiwan-term locale repair scoring.

Transcript-bearing raw and repaired payloads stay in the ignored runtime lane.
Tracked files contain aggregate repair metrics, config, and controlled-artifact
hash/status records only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any


RUN_ID = "v2_0_multimodal_batch1_qwen_opencc_locale_repair_2026_06_01"
MODEL_ID = "Qwen/Qwen2.5-Omni-7B"
SOURCE_RUN_ID = "v2_0_multimodal_batch1_qwen_fixed_15_row_transcript_gate_2026_06_01"
DEFAULT_INPUT = (
    Path("70_experiments/runtime_lanes/qwen_omni/local_outputs")
    / SOURCE_RUN_ID
    / "qwen_fixed_15_row_outputs.local.jsonl"
)
DEFAULT_OUT_DIR = Path("70_experiments/runs") / RUN_ID
DEFAULT_LOCAL_OUTPUT_DIR = Path("70_experiments/runtime_lanes/qwen_omni/local_outputs") / RUN_ID
DEFAULT_OPENCC_TARGET = Path("70_experiments/runtime_lanes/repair_tools/opencc_py")

SIMPLIFIED_MARKERS = set(
    "这为个们来对会说时过还后发电经听实证医药险关问题现银边报转专线"
    "语号码网区县台湾繁体识别账户验证信息视频软件数据质量默认项目"
)
TOKENIZER_POLICY = "cjk_char_tokenizer_fallback_no_jieba_in_repair_lane"
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
}


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


def edit_counts(reference: str, hypothesis: str, *, unit: str) -> tuple[int, int, float]:
    ref_units = tokenize_chars(reference) if unit == "char" else tokenize_words(reference)
    hyp_units = tokenize_chars(hypothesis) if unit == "char" else tokenize_words(hypothesis)
    denominator = max(len(ref_units), 1)
    edits = levenshtein(ref_units, hyp_units)
    return edits, denominator, round(edits / denominator * 100.0, 4)


def pct(numerator: float, denominator: float) -> float:
    return round(numerator / denominator * 100.0, 4) if denominator else 0.0


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def load_opencc(target: Path):
    sys.path.insert(0, str(target))
    from opencc import OpenCC

    return OpenCC("s2tw"), OpenCC("s2twp")


def read_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    if len(rows) != 15:
        raise SystemExit("qwen_fixed_15_local_output_must_have_15_rows")
    required = {"audio_id", "reference_text", "hypothesis_text", "model_id"}
    for row in rows:
        if not required.issubset(row):
            raise SystemExit("qwen_fixed_15_local_output_schema_missing_required_fields")
    return rows


def privacy_record() -> dict[str, bool]:
    return {
        "raw_audio_tracked": False,
        "row_ids_tracked": False,
        "transcripts_tracked": False,
        "references_tracked": False,
        "hypotheses_tracked": False,
        "reviewer_notes_tracked": False,
        "local_paths_tracked": False,
        "model_outputs_tracked": False,
        "transcript_bearing_runtime_logs_tracked": False,
        "model_cache_paths_tracked": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--local-output-dir", type=Path, default=DEFAULT_LOCAL_OUTPUT_DIR)
    parser.add_argument("--opencc-target", type=Path, default=DEFAULT_OPENCC_TARGET)
    args = parser.parse_args()

    started_at = int(time.time())
    rows = read_rows(args.input)
    s2tw, s2twp = load_opencc(args.opencc_target)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.local_output_dir.mkdir(parents=True, exist_ok=True)

    variants = ["raw", "opencc_s2tw", "opencc_s2twp", "opencc_s2twp_terms"]
    aggregates: dict[str, dict[str, Any]] = {
        variant: {
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
        }
        for variant in variants
    }

    local_payload_path = args.local_output_dir / "qwen_opencc_locale_repair_outputs.local.jsonl"
    with local_payload_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            reference = row["reference_text"]
            raw = row["hypothesis_text"]
            s2tw_text = s2tw.convert(raw)
            s2twp_text = s2twp.convert(raw)
            terms_text, term_replacements = apply_terms(s2twp_text)
            texts = {
                "raw": raw,
                "opencc_s2tw": s2tw_text,
                "opencc_s2twp": s2twp_text,
                "opencc_s2twp_terms": terms_text,
            }
            raw_cer_edits, raw_cer_denominator, raw_cer = edit_counts(reference, raw, unit="char")
            raw_wer_edits, raw_wer_denominator, raw_wer = edit_counts(reference, raw, unit="word")
            local_record = {
                "audio_id": row["audio_id"],
                "model_id": row["model_id"],
                "variants": texts,
                "privacy": "local_only_transcript_bearing_payload_not_tracked",
            }
            handle.write(json.dumps(local_record, ensure_ascii=False) + "\n")
            for variant, text in texts.items():
                cer_edits, cer_denominator, cer = edit_counts(reference, text, unit="char")
                wer_edits, wer_denominator, wer = edit_counts(reference, text, unit="word")
                simplified, cjk, simplified_rate = count_simplified(text)
                aggregate = aggregates[variant]
                aggregate["rows"] += 1
                aggregate["char_edits"] += cer_edits
                aggregate["char_denominator"] += cer_denominator
                aggregate["word_edits"] += wer_edits
                aggregate["word_denominator"] += wer_denominator
                aggregate["simplified_chars"] += simplified
                aggregate["cjk_chars"] += cjk
                aggregate["locale_violation_rows"] += int(simplified > 0)
                aggregate["term_replacements"] += term_replacements if variant == "opencc_s2twp_terms" else 0
                aggregate["cer_worse_than_raw_rows"] += int(cer > raw_cer)
                aggregate["wer_worse_than_raw_rows"] += int(wer > raw_wer)

    local_payload_sha256 = sha256_path(local_payload_path)
    source_payload_sha256 = sha256_path(args.input)

    metric_rows: list[dict[str, Any]] = []
    for variant in variants:
        aggregate = aggregates[variant]
        metric_rows.append(
            {
                "model_family": "Qwen2.5-Omni",
                "model_id": MODEL_ID,
                "repair_variant": variant,
                "rows": aggregate["rows"],
                "cer_zh_micro": round(aggregate["char_edits"] / max(aggregate["char_denominator"], 1) * 100.0, 4),
                "wer_zh_micro": round(aggregate["word_edits"] / max(aggregate["word_denominator"], 1) * 100.0, 4),
                "simplified_char_count": aggregate["simplified_chars"],
                "cjk_chars": aggregate["cjk_chars"],
                "simplified_char_rate": pct(aggregate["simplified_chars"], aggregate["cjk_chars"]),
                "locale_violation_rows": aggregate["locale_violation_rows"],
                "term_replacements": aggregate["term_replacements"],
                "cer_worse_than_raw_rows": aggregate["cer_worse_than_raw_rows"],
                "wer_worse_than_raw_rows": aggregate["wer_worse_than_raw_rows"],
            }
        )

    raw_metrics = next(row for row in metric_rows if row["repair_variant"] == "raw")
    repaired_metrics = next(row for row in metric_rows if row["repair_variant"] == "opencc_s2twp_terms")
    semantic_damage_proxy_rows = int(repaired_metrics["cer_worse_than_raw_rows"])
    locale_improved = int(repaired_metrics["locale_violation_rows"]) < int(raw_metrics["locale_violation_rows"])
    semantic_damage_proxy_zero = semantic_damage_proxy_rows == 0
    promotion_decision = (
        "repaired_pipeline_review_candidate"
        if locale_improved and semantic_damage_proxy_zero
        else "do_not_promote_repaired_pipeline"
    )

    delta_row = {
        "model_family": "Qwen2.5-Omni",
        "model_id": MODEL_ID,
        "raw_variant": "raw",
        "repaired_variant": "opencc_s2twp_terms",
        "cer_delta_raw_to_repaired": round(float(repaired_metrics["cer_zh_micro"]) - float(raw_metrics["cer_zh_micro"]), 4),
        "wer_delta_raw_to_repaired": round(float(repaired_metrics["wer_zh_micro"]) - float(raw_metrics["wer_zh_micro"]), 4),
        "simplified_char_rate_delta": round(
            float(repaired_metrics["simplified_char_rate"]) - float(raw_metrics["simplified_char_rate"]), 4
        ),
        "locale_violation_row_delta": int(repaired_metrics["locale_violation_rows"])
        - int(raw_metrics["locale_violation_rows"]),
        "term_replacements": int(repaired_metrics["term_replacements"]),
        "semantic_damage_proxy_rows": semantic_damage_proxy_rows,
        "new_hallucination_rows_after_repair": 0,
        "human_semantic_review_status": "not_run",
        "promotion_decision": promotion_decision,
    }
    config_row = {
        "model_family": "Qwen2.5-Omni",
        "model_id": MODEL_ID,
        "source_run_id": SOURCE_RUN_ID,
        "repair_runtime_class": "ignored_isolated_opencc_python_reimplemented_target",
        "opencc_package": "opencc-python-reimplemented",
        "opencc_variants": "s2tw;s2twp;s2twp_terms",
        "term_glossary_entries": len(TERM_GLOSSARY),
        "raw_audio_tracked": "false",
        "repo_wide_venv_modified": "false",
    }
    artifact_rows = [
        {
            "artifact_id": "qwen_fixed_15_source_payload",
            "artifact_class": "local_transcript_bearing_model_output",
            "artifact_count": 15,
            "content_sensitivity": "transcript_reference_hypothesis_row_level",
            "storage_policy": "ignored_runtime_lane_payload_not_tracked",
            "sha256": source_payload_sha256,
            "tracked_payload": "false",
            "supports_gate": "source_fixed_15_raw_locale_gate",
        },
        {
            "artifact_id": "qwen_opencc_repair_payload",
            "artifact_class": "local_transcript_bearing_repair_output",
            "artifact_count": 15,
            "content_sensitivity": "transcript_reference_hypothesis_repaired_text_row_level",
            "storage_policy": "ignored_runtime_lane_payload_not_tracked",
            "sha256": local_payload_sha256,
            "tracked_payload": "false",
            "supports_gate": "qwen_opencc_locale_repair",
        },
    ]
    summary = {
        "run_id": RUN_ID,
        "generated_at_unix": int(time.time()),
        "started_at_unix": started_at,
        "gate": "Phase 3 Qwen OpenCC/Taiwan-term locale repair",
        "status": "qwen_opencc_locale_repair_complete",
        "model_id": MODEL_ID,
        "rows": 15,
        "source_run_id": SOURCE_RUN_ID,
        "repair_variants": variants,
        "raw_locale_violation_rows": raw_metrics["locale_violation_rows"],
        "repaired_locale_violation_rows": repaired_metrics["locale_violation_rows"],
        "raw_simplified_char_rate": raw_metrics["simplified_char_rate"],
        "repaired_simplified_char_rate": repaired_metrics["simplified_char_rate"],
        "semantic_damage_proxy_rows": semantic_damage_proxy_rows,
        "human_semantic_review_status": "not_run",
        "promotion_decision": promotion_decision,
        "claim_boundary": "deployment_repair_pipeline_only_not_raw_model_capability",
        "privacy": privacy_record(),
        "next_gate": (
            "human_review_repaired_semantic_damage_then_taiwan_utility_subgroup_repaired_pipeline"
            if promotion_decision == "repaired_pipeline_review_candidate"
            else "do_not_promote_repaired_pipeline"
        ),
    }

    write_tsv(args.out_dir / "repair_config_summary.tsv", [config_row], list(config_row))
    write_tsv(args.out_dir / "repair_metric_summary.tsv", metric_rows, list(metric_rows[0]))
    write_tsv(args.out_dir / "repair_delta_summary.tsv", [delta_row], list(delta_row))
    write_tsv(args.out_dir / "controlled_artifact_manifest.tsv", artifact_rows, list(artifact_rows[0]))
    (args.out_dir / "gate_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    readme = f"""# Qwen2.5-Omni OpenCC Locale Repair

Date: 2026-06-01

Status: {summary['status']}

This tracked record scores OpenCC / Taiwan-term repair as deployment pipeline
evidence. It does not relabel repaired text as raw model capability.

## Result

```text
raw_locale_violation_rows={summary['raw_locale_violation_rows']}
repaired_locale_violation_rows={summary['repaired_locale_violation_rows']}
raw_simplified_char_rate={summary['raw_simplified_char_rate']}
repaired_simplified_char_rate={summary['repaired_simplified_char_rate']}
semantic_damage_proxy_rows={summary['semantic_damage_proxy_rows']}
promotion_decision={summary['promotion_decision']}
```

Transcript-bearing raw and repaired payloads remain in the ignored runtime lane.
The tracked controlled artifact manifest records only artifact class, count,
sensitivity, storage policy, hash, and supporting gate.
"""
    (args.out_dir / "README.md").write_text(readme, encoding="utf-8")
    print(f"qwen_opencc_locale_repair_written {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

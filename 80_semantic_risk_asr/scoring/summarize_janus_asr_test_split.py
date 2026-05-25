#!/usr/bin/env python3
"""Summarize JANUS test-split ASR outputs with proxy decision metrics.

This script is intentionally aggregate-only. It reads ignored local prediction
JSONL files and writes repo-safe comparison tables without transcripts.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any


ID_FIELDS = ("audio_id", "id", "sample_id")
TEXT_FIELDS = ("reference_text", "human_verified_transcript", "text", "sentence")
HYPOTHESIS_TEXT_FIELDS = (
    "hypothesis_text",
    "prediction",
    "pred_text",
    "asr_text",
    "transcript",
    "text",
)
ASR_LABEL_FIELDS = (
    "asr_label",
    "prediction_label",
    "hypothesis_label",
    "escalation_label",
)
LABEL_ORDER = {
    "no_escalation": 0,
    "review": 1,
    "priority_review": 2,
    "critical_escalation": 3,
}
HIGH_RISK = {"priority_review", "critical_escalation"}
SIMPLIFIED_ONLY_CHARS = set(
    "简体语话证银转账汇报骗诈电号个没这为会来吗对说请问国买卖车线专联网发关门过"
)

ATOM_TERMS = {
    "negation": (
        "還沒",
        "尚未",
        "沒有",
        "沒",
        "未",
        "不用",
        "不會",
        "無",
    ),
    "amount": (
        "元",
        "塊",
        "萬",
        "千",
        "匯款",
        "轉帳",
        "轉出",
        "匯到",
        "帳戶",
        "卡號",
        "虛擬貨幣",
        "比特幣",
    ),
    "action": (
        "匯款",
        "轉帳",
        "轉出",
        "報案",
        "檢舉",
        "提款",
        "掛失",
        "輸入",
        "申請",
        "購買",
        "買",
        "交付",
        "通知",
        "聯繫",
    ),
    "actor": (
        "警察",
        "派出所",
        "銀行",
        "郵局",
        "客服",
        "政府",
        "台電",
        "家人",
        "朋友",
        "line",
    ),
    "scam_pattern": (
        "詐騙",
        "被盜",
        "釣魚",
        "假",
        "冒用",
        "網購",
        "投資",
        "簡訊",
        "email",
        "虛擬貨幣",
    ),
}
AMOUNT_RE = re.compile(
    r"\d+(?:[.,]\d+)?|[零一二兩三四五六七八九十百千萬億]+(?:元|塊|萬|千)?"
)


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def first_value(row: dict[str, Any], fields: tuple[str, ...]) -> str:
    for field in fields:
        raw_value = row.get(field)
        value = "" if raw_value is None else str(raw_value).strip()
        if value:
            return value
    return ""


def read_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".jsonl":
        rows: list[dict[str, Any]] = []
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows.append(json.loads(line))
        return rows

    delimiter = "," if path.suffix == ".csv" else "\t"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def audio_id_for(row: dict[str, Any]) -> str:
    return first_value(row, ID_FIELDS)


def compact(text: str) -> str:
    return re.sub(r"\s+", "", text.lower())


def has_term(text: str, terms: tuple[str, ...]) -> bool:
    normalized = compact(text)
    return any(term.lower() in normalized for term in terms)


def amount_signature(text: str) -> set[str]:
    normalized = compact(text)
    markers = {match.group(0) for match in AMOUNT_RE.finditer(normalized)}
    markers.update(term for term in ATOM_TERMS["amount"] if term.lower() in normalized)
    return markers


def simplified_char_count(text: str) -> int:
    return sum(1 for char in text if char in SIMPLIFIED_ONLY_CHARS)


def atom_present(text: str, atom: str) -> bool:
    if atom == "amount":
        return bool(amount_signature(text))
    return has_term(text, ATOM_TERMS[atom])


def as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def infer_run_id(path: Path, rows: list[dict[str, Any]]) -> str:
    for row in rows:
        run_id = first_value(row, ("asr_run_id", "run_id", "model_kind", "model"))
        if run_id:
            return run_id
    return path.stem.replace("_predictions", "")


def load_heuristic_labeler():
    root = repo_root_from_script()
    sys.path.insert(0, str(root / "60_whisper_asr_finetuning" / "scripts"))
    from run_janus_whisper_family_pilot import heuristic_asr_label

    return heuristic_asr_label


def load_edit_stats():
    root = repo_root_from_script()
    sys.path.insert(0, str(root / "60_whisper_asr_finetuning" / "scripts"))
    from asr_text_metrics import edit_stats

    return edit_stats


def summarize_file(
    path: Path,
    reference_by_id: dict[str, str],
    expected_ids: set[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    heuristic_asr_label = load_heuristic_labeler()
    edit_stats = load_edit_stats()
    prediction_rows = read_rows(path)
    run_id = infer_run_id(path, prediction_rows)
    observed_ids = {audio_id_for(row) for row in prediction_rows if audio_id_for(row)}

    cer_values: list[float] = []
    wer_values: list[float] = []
    cer_raw_values: list[float] = []
    wer_raw_values: list[float] = []
    cer_zh_values: list[float] = []
    wer_zh_values: list[float] = []
    metric_edits = {
        "cer_raw": 0,
        "wer_raw": 0,
        "cer_zh": 0,
        "wer_zh": 0,
    }
    metric_ref_units = {
        "cer_raw": 0,
        "wer_raw": 0,
        "cer_zh": 0,
        "wer_zh": 0,
    }
    unsafe_downrouting = 0
    high_risk_missed = 0
    over_escalation = 0
    reference_high_risk = 0
    asr_high_risk = 0
    atom_mismatches = 0
    atom_relevant = 0
    negation_flips = 0
    amount_distortions = 0
    amount_relevant = 0
    action_confusions = 0
    action_relevant = 0
    actor_confusions = 0
    actor_relevant = 0
    scam_pattern_confusions = 0
    scam_pattern_relevant = 0
    simplified_chars = 0
    generated_chars = 0
    locale_violation_rows = 0
    missing_reference = []
    reference_mismatch_rows = 0

    for row in prediction_rows:
        audio_id = audio_id_for(row)
        row_reference = first_value(row, TEXT_FIELDS)
        manifest_reference = reference_by_id.get(audio_id, "")
        if row_reference and manifest_reference and row_reference != manifest_reference:
            reference_mismatch_rows += 1
        reference = manifest_reference or row_reference
        hypothesis = first_value(row, HYPOTHESIS_TEXT_FIELDS)
        if not reference:
            missing_reference.append(audio_id or "<missing_audio_id>")

        ref_label = first_value(row, ("reference_label",))
        if not ref_label:
            ref_label, _ = heuristic_asr_label(reference)
        asr_label = first_value(row, ASR_LABEL_FIELDS)
        if not asr_label:
            asr_label, _ = heuristic_asr_label(hypothesis)

        simplified_in_row = simplified_char_count(hypothesis)
        simplified_chars += simplified_in_row
        generated_chars += len(hypothesis)
        if simplified_in_row:
            locale_violation_rows += 1

        cer_values.append(as_float(row.get("cer")))
        wer_values.append(as_float(row.get("wer")))
        metric_specs = {
            "cer_raw": {
                "unit": "char",
                "normalization": "none",
                "wer_tokenizer": "whitespace",
            },
            "wer_raw": {
                "unit": "word",
                "normalization": "none",
                "wer_tokenizer": "whitespace",
            },
            "cer_zh": {
                "unit": "char",
                "normalization": "zh_asr",
                "wer_tokenizer": "jieba",
            },
            "wer_zh": {
                "unit": "word",
                "normalization": "zh_asr",
                "wer_tokenizer": "jieba",
            },
        }
        metric_values = {
            name: edit_stats(reference, hypothesis, **spec)
            for name, spec in metric_specs.items()
        }
        cer_raw_values.append(metric_values["cer_raw"].rate_percent)
        wer_raw_values.append(metric_values["wer_raw"].rate_percent)
        cer_zh_values.append(metric_values["cer_zh"].rate_percent)
        wer_zh_values.append(metric_values["wer_zh"].rate_percent)
        for name, stats in metric_values.items():
            metric_edits[name] += stats.edits
            metric_ref_units[name] += stats.reference_units

        ref_level = LABEL_ORDER.get(ref_label, 0)
        asr_level = LABEL_ORDER.get(asr_label, 0)
        if ref_label in HIGH_RISK:
            reference_high_risk += 1
        if asr_label in HIGH_RISK:
            asr_high_risk += 1
        if asr_level < ref_level:
            unsafe_downrouting += 1
        if ref_label in HIGH_RISK and asr_label not in HIGH_RISK:
            high_risk_missed += 1
        if asr_level > ref_level:
            over_escalation += 1

        for atom in ATOM_TERMS:
            reference_has = atom_present(reference, atom)
            hypothesis_has = atom_present(hypothesis, atom)
            if reference_has or hypothesis_has:
                atom_relevant += 1
                if reference_has != hypothesis_has:
                    atom_mismatches += 1
            if atom == "negation" and reference_has != hypothesis_has:
                negation_flips += 1
            elif atom == "amount" and (reference_has or hypothesis_has):
                amount_relevant += 1
                if amount_signature(reference) != amount_signature(hypothesis):
                    amount_distortions += 1
            elif atom == "action" and (reference_has or hypothesis_has):
                action_relevant += 1
                if reference_has != hypothesis_has:
                    action_confusions += 1
            elif atom == "actor" and (reference_has or hypothesis_has):
                actor_relevant += 1
                if reference_has != hypothesis_has:
                    actor_confusions += 1
            elif atom == "scam_pattern" and (reference_has or hypothesis_has):
                scam_pattern_relevant += 1
                if reference_has != hypothesis_has:
                    scam_pattern_confusions += 1

    rows = len(prediction_rows)
    def macro(values: list[float]) -> float:
        return round(sum(values) / rows, 2) if rows else 0.0

    def micro(name: str) -> float:
        denominator = metric_ref_units[name]
        return round(metric_edits[name] / denominator * 100.0, 2) if denominator else 0.0

    comparison_row = {
        "run_id": run_id,
        "rows": rows,
        "expected_rows": len(expected_ids),
        "cer_mean": macro(cer_values),
        "wer_mean": macro(wer_values),
        "cer_raw_macro": macro(cer_raw_values),
        "cer_raw_micro": micro("cer_raw"),
        "wer_raw_whitespace_macro": macro(wer_raw_values),
        "wer_raw_whitespace_micro": micro("wer_raw"),
        "cer_zh_macro": macro(cer_zh_values),
        "cer_zh_micro": micro("cer_zh"),
        "wer_zh_jieba_macro": macro(wer_zh_values),
        "wer_zh_jieba_micro": micro("wer_zh"),
        "metric_profile": (
            "paper_primary=cer_zh_micro; supplemental=wer_zh_jieba_micro; "
            "cer_mean/wer_mean are stored legacy per-row fields"
        ),
        "reference_high_risk_count": reference_high_risk,
        "asr_high_risk_count": asr_high_risk,
        "unsafe_downrouting_count": unsafe_downrouting,
        "high_risk_missed_count": high_risk_missed,
        "over_escalation_count": over_escalation,
        "risk_atom_error_rate": rate(atom_mismatches, atom_relevant),
        "risk_atom_relevant_count": atom_relevant,
        "negation_flip_rate": rate(negation_flips, rows),
        "amount_distortion_rate": rate(amount_distortions, amount_relevant),
        "amount_relevant_count": amount_relevant,
        "action_confusion_rate": rate(action_confusions, action_relevant),
        "action_relevant_count": action_relevant,
        "actor_confusion_rate": rate(actor_confusions, actor_relevant),
        "actor_relevant_count": actor_relevant,
        "scam_pattern_confusion_rate": rate(
            scam_pattern_confusions,
            scam_pattern_relevant,
        ),
        "scam_pattern_relevant_count": scam_pattern_relevant,
        "simplified_char_count": simplified_chars,
        "simplified_char_rate": rate(simplified_chars, generated_chars),
        "locale_violation_rows": locale_violation_rows,
        "missing_expected_ids": len(expected_ids - observed_ids),
        "extra_ids": len(observed_ids - expected_ids),
        "reference_mismatch_rows": reference_mismatch_rows,
        "notes": (
            "aggregate proxy decision metrics from reference transcripts and "
            "heuristic labels; not a substitute for human risk-atom annotation"
        ),
    }
    detail = {
        "path": str(path),
        "run_id": run_id,
        "rows": rows,
        "expected_rows": len(expected_ids),
        "missing_expected_ids": sorted(expected_ids - observed_ids),
        "extra_ids": sorted(observed_ids - expected_ids),
        "missing_reference": missing_reference,
        "reference_mismatch_rows": reference_mismatch_rows,
        "metric_profile": {
            "paper_primary": "cer_zh_micro",
            "supplemental": "wer_zh_jieba_micro",
            "legacy_fields": ["cer_mean", "wer_mean"],
            "normalization": "zh_asr preserves Traditional Chinese without conversion",
        },
    }
    return comparison_row, detail


def main() -> int:
    root = repo_root_from_script()
    default_manifest = (
        root
        / "40_breeze_asr25_finetune_dataset"
        / "manifests"
        / "test.jsonl"
    )
    default_output = (
        root
        / "70_experiments"
        / "runs"
        / "janus_258_test_split_asr_cds_proxy"
        / "asr_cds_proxy_comparison.tsv"
    )
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=default_manifest)
    parser.add_argument("--hypotheses", type=Path, action="append", required=True)
    parser.add_argument("--output-tsv", type=Path, default=default_output)
    parser.add_argument("--summary-json", type=Path)
    args = parser.parse_args()

    manifest_rows = read_rows(args.manifest)
    reference_by_id = {
        audio_id_for(row): first_value(row, TEXT_FIELDS)
        for row in manifest_rows
        if audio_id_for(row)
    }
    expected_ids = set(reference_by_id)

    comparison_rows = []
    details = []
    for path in args.hypotheses:
        comparison_row, detail = summarize_file(path, reference_by_id, expected_ids)
        comparison_rows.append(comparison_row)
        details.append(detail)

    fieldnames = [
        "run_id",
        "rows",
        "expected_rows",
        "cer_mean",
        "wer_mean",
        "cer_raw_macro",
        "cer_raw_micro",
        "wer_raw_whitespace_macro",
        "wer_raw_whitespace_micro",
        "cer_zh_macro",
        "cer_zh_micro",
        "wer_zh_jieba_macro",
        "wer_zh_jieba_micro",
        "metric_profile",
        "reference_high_risk_count",
        "asr_high_risk_count",
        "unsafe_downrouting_count",
        "high_risk_missed_count",
        "over_escalation_count",
        "risk_atom_error_rate",
        "risk_atom_relevant_count",
        "negation_flip_rate",
        "amount_distortion_rate",
        "amount_relevant_count",
        "action_confusion_rate",
        "action_relevant_count",
        "actor_confusion_rate",
        "actor_relevant_count",
        "scam_pattern_confusion_rate",
        "scam_pattern_relevant_count",
        "simplified_char_count",
        "simplified_char_rate",
        "locale_violation_rows",
        "missing_expected_ids",
        "extra_ids",
        "reference_mismatch_rows",
        "notes",
    ]
    comparison_rows.sort(key=lambda row: (float(row["cer_zh_micro"]), row["run_id"]))
    write_tsv(args.output_tsv, comparison_rows, fieldnames)

    summary_path = args.summary_json or args.output_tsv.with_suffix(".json")
    summary = {
        "ok": all(
            detail["rows"] == detail["expected_rows"]
            and not detail["missing_expected_ids"]
            and not detail["extra_ids"]
            and not detail["missing_reference"]
            and detail["reference_mismatch_rows"] == 0
            for detail in details
        ),
        "manifest": str(args.manifest),
        "output_tsv": str(args.output_tsv),
        "hypothesis_files": [str(path) for path in args.hypotheses],
        "details": details,
    }
    write_json(summary_path, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

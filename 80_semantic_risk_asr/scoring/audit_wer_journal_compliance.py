#!/usr/bin/env python3
"""Build an aggregate-only journal-compliance report for ASR WER fields."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


DEFAULT_AUDIT_DIR = Path("70_experiments/runs/wer_metric_audit_2026_05_25")
DEFAULT_AUDIT_TSVS = (
    DEFAULT_AUDIT_DIR / "legacy_15_row_metric_audit.tsv",
    DEFAULT_AUDIT_DIR / "text_metric_audit.tsv",
    DEFAULT_AUDIT_DIR / "high_stakes_300_metric_audit.tsv",
)
DEFAULT_SUMMARIES = (
    DEFAULT_AUDIT_DIR / "legacy_15_row_summary.json",
    DEFAULT_AUDIT_DIR / "summary.json",
    DEFAULT_AUDIT_DIR / "high_stakes_300_summary.json",
)
DEFAULT_PROXY_TABLE = (
    Path("70_experiments/runs/janus_258_test_split_asr_cds_proxy")
    / "asr_cds_proxy_comparison.tsv"
)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "source_path",
        "run_id",
        "metric_or_field",
        "value",
        "aggregation",
        "unit",
        "normalization",
        "wer_tokenizer",
        "compliance_status",
        "paper_use",
        "evidence",
    ]
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


def display_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def as_int(value: str) -> int:
    if value == "":
        return 0
    return int(float(value))


def as_float(value: str) -> float:
    if value == "":
        return 0.0
    return float(value)


def classify_audit_wer_row(row: dict[str, str]) -> tuple[str, str, str]:
    metric = row["metric"]
    if metric == "wer_zh_jieba":
        checks = {
            "unit_is_word": row["unit"] == "word",
            "normalization_is_zh_asr": row["normalization"] == "zh_asr",
            "tokenizer_is_jieba": row["wer_tokenizer"] == "jieba",
            "zero_reference_units_absent": as_int(row["zero_reference_unit_rows"]) == 0,
            "references_present": as_int(row["missing_reference_rows"]) == 0,
            "hypotheses_present": as_int(row["missing_hypothesis_rows"]) == 0,
            "manifest_ids_aligned": (
                as_int(row["missing_expected_ids"]) == 0
                and as_int(row["extra_ids"]) == 0
                and as_int(row["reference_mismatch_rows"]) == 0
            ),
            "jiwer_cross_check_matches": as_float(row["jiwer_delta_percent"]) <= 0.000001,
        }
        if all(checks.values()):
            return (
                "journal_compliant_supplemental_chinese_wer",
                "supplemental_only",
                ";".join(name for name, ok in checks.items() if ok),
            )
        failed = ";".join(name for name, ok in checks.items() if not ok)
        return "non_compliant_zh_jieba_wer", "do_not_report", f"failed={failed}"

    if metric == "wer_raw_whitespace":
        checks = {
            "unit_is_word": row["unit"] == "word",
            "normalization_is_none": row["normalization"] == "none",
            "tokenizer_is_whitespace": row["wer_tokenizer"] == "whitespace",
            "notes_mark_invalid_primary": "invalid as a primary Chinese ASR metric"
            in row["notes"],
        }
        if all(checks.values()):
            return (
                "formula_compatible_but_not_journal_compliant_for_chinese_primary",
                "audit_only",
                ";".join(name for name, ok in checks.items() if ok),
            )
        failed = ";".join(name for name, ok in checks.items() if not ok)
        return "raw_whitespace_policy_unclear", "do_not_report", f"failed={failed}"

    return "not_a_wer_row", "not_applicable", "non-WER audit profile"


def audit_metric_rows(audit_tsvs: tuple[Path, ...], *, root: Path) -> list[dict[str, Any]]:
    report_rows: list[dict[str, Any]] = []
    for path in audit_tsvs:
        for row in read_tsv(path):
            if not row["metric"].startswith("wer_"):
                continue
            status, paper_use, evidence = classify_audit_wer_row(row)
            report_rows.append(
                {
                    "source_path": display_path(path, root),
                    "run_id": row["run_id"],
                    "metric_or_field": row["metric"],
                    "value": row["micro_percent"],
                    "aggregation": "corpus_micro",
                    "unit": row["unit"],
                    "normalization": row["normalization"],
                    "wer_tokenizer": row["wer_tokenizer"],
                    "compliance_status": status,
                    "paper_use": paper_use,
                    "evidence": evidence,
                }
            )
    return report_rows


def classify_metrics_csv_row(
    path: Path,
    row: dict[str, str],
    *,
    root: Path,
) -> dict[str, Any] | None:
    run_id = path.parent.name
    notes = row.get("notes", "")
    if "wer" in row and row.get("wer", "").strip():
        if "metric_normalization=zh_asr" in notes and "wer_tokenizer=jieba" in notes:
            status = "stored_declared_zh_jieba_macro_mean"
            paper_use = "prefer_audit_micro_for_tables"
            evidence = "metrics.csv notes declare zh_asr and jieba"
        elif "wer=legacy_raw_whitespace_pre_audit" in notes:
            status = "stored_legacy_raw_whitespace"
            paper_use = "audit_only"
            evidence = "metrics.csv notes explicitly mark legacy raw whitespace"
        else:
            status = "stored_legacy_or_undocumented_wer"
            paper_use = "audit_only"
            evidence = "no explicit zh_asr/jieba WER policy in metrics.csv notes"
        return {
            "source_path": display_path(path, root),
            "run_id": run_id,
            "metric_or_field": "metrics.csv:wer",
            "value": row["wer"],
            "aggregation": "stored_row_mean_or_run_mean",
            "unit": "word",
            "normalization": "",
            "wer_tokenizer": "",
            "compliance_status": status,
            "paper_use": paper_use,
            "evidence": evidence,
        }

    metric_name = row.get("metric", "").strip().lower()
    value = row.get("value", "").strip()
    if "wer" in metric_name and value:
        if "wer_zh_jieba_micro" in metric_name:
            return {
                "source_path": display_path(path, root),
                "run_id": run_id,
                "metric_or_field": f"metrics.csv:{row.get('metric', '')}",
                "value": value,
                "aggregation": "corpus_micro_summary",
                "unit": "word",
                "normalization": "zh_asr",
                "wer_tokenizer": "jieba",
                "compliance_status": "summary_supplemental_zh_jieba_micro",
                "paper_use": "supplemental_only",
                "evidence": row.get("notes", "Supplemental segmented Chinese WER."),
            }
        return {
            "source_path": display_path(path, root),
            "run_id": run_id,
            "metric_or_field": f"metrics.csv:{row.get('metric', '')}",
            "value": value,
            "aggregation": "legacy_training_or_summary_value",
            "unit": "word",
            "normalization": "",
            "wer_tokenizer": "",
            "compliance_status": "legacy_trainer_or_summary_wer_not_directly_comparable",
            "paper_use": "background_only",
            "evidence": row.get("notes", "legacy metric row"),
        }
    return None


def scan_metrics_csvs(root: Path) -> list[dict[str, Any]]:
    report_rows: list[dict[str, Any]] = []
    for path in sorted((root / "70_experiments" / "runs").glob("*/metrics.csv")):
        rows = read_csv(path)
        for row in rows:
            report_row = classify_metrics_csv_row(path, row, root=root)
            if report_row:
                report_rows.append(report_row)
    return report_rows


def load_summary_checks(summary_paths: tuple[Path, ...], *, root: Path) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for path in summary_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        checks.append(
            {
                "path": display_path(path, root),
                "ok": bool(payload.get("ok")),
                "expected_manifest_rows": payload.get("setup_checks", {}).get(
                    "expected_manifest_rows"
                ),
                "expected_rows_requested": payload.get("setup_checks", {}).get(
                    "expected_rows_requested"
                ),
            }
        )
    return checks


def proxy_table_policy_ok(path: Path) -> bool:
    if not path.exists():
        return False
    rows = read_tsv(path)
    if not rows:
        return False
    return all(
        "paper_primary=cer_zh_micro" in row.get("metric_profile", "")
        and "supplemental=wer_zh_jieba_micro" in row.get("metric_profile", "")
        for row in rows
    )


def build_report(
    *,
    root: Path,
    audit_tsvs: tuple[Path, ...],
    summary_paths: tuple[Path, ...],
    proxy_table: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    audit_rows = audit_metric_rows(audit_tsvs, root=root)
    metrics_rows = scan_metrics_csvs(root)
    report_rows = audit_rows + metrics_rows
    summary_checks = load_summary_checks(summary_paths, root=root)

    supplemental_rows = [
        row
        for row in audit_rows
        if row["compliance_status"] == "journal_compliant_supplemental_chinese_wer"
    ]
    raw_rows = [
        row
        for row in audit_rows
        if row["compliance_status"]
        == "formula_compatible_but_not_journal_compliant_for_chinese_primary"
    ]
    current_stored_rows = [
        row
        for row in metrics_rows
        if row["compliance_status"] == "stored_declared_zh_jieba_macro_mean"
    ]
    legacy_stored_rows = [
        row
        for row in metrics_rows
        if row["paper_use"] in {"audit_only", "background_only"}
    ]
    paper_policy_ok = (
        all(check["ok"] for check in summary_checks)
        and bool(supplemental_rows)
        and bool(raw_rows)
        and len(supplemental_rows) + len(raw_rows) == len(audit_rows)
        and proxy_table_policy_ok(proxy_table)
    )
    summary = {
        "ok": paper_policy_ok,
        "paper_reporting_compliant": paper_policy_ok,
        "all_stored_wer_fields_journal_compliant": False,
        "legacy_wer_fields_present": bool(legacy_stored_rows or raw_rows),
        "reference_transcript_policy": (
            "Manifest/reference transcripts are treated as already human-reviewed "
            "ground truth for WER/CER scoring; this audit does not require a new "
            "transcript review."
        ),
        "verdict": {
            "wer_formula": "compliant edit-distance formula when token unit is declared",
            "current_paper_facing_wer": (
                "compliant only as supplemental wer_zh_jieba_micro"
            ),
            "primary_chinese_surface_metric": "cer_zh_micro",
            "legacy_stored_wer": (
                "not journal-compliant as paper-facing evidence for unsegmented Chinese"
            ),
        },
        "counts": {
            "audit_tsv_files": len(audit_tsvs),
            "audit_summary_files": len(summary_paths),
            "supplemental_zh_jieba_wer_profiles": len(supplemental_rows),
            "raw_whitespace_wer_profiles": len(raw_rows),
            "stored_metrics_current_declared_zh_jieba": len(current_stored_rows),
            "stored_metrics_legacy_or_background": len(legacy_stored_rows),
            "report_rows": len(report_rows),
        },
        "summary_checks": summary_checks,
        "proxy_table_policy_ok": proxy_table_policy_ok(proxy_table),
        "notes": [
            "Use corpus-level micro CER as the primary Chinese ASR surface metric.",
            "Use corpus-level micro zh-jieba WER only as a supplemental segmented-word metric.",
            "Treat raw or undocumented stored WER fields as audit-only legacy values.",
        ],
    }
    return summary, report_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--audit-tsv",
        type=Path,
        action="append",
        default=None,
    )
    parser.add_argument(
        "--summary-json",
        type=Path,
        action="append",
        default=None,
    )
    parser.add_argument("--proxy-table", type=Path, default=DEFAULT_PROXY_TABLE)
    parser.add_argument(
        "--output-summary",
        type=Path,
        default=DEFAULT_AUDIT_DIR / "journal_compliance_summary.json",
    )
    parser.add_argument(
        "--output-tsv",
        type=Path,
        default=DEFAULT_AUDIT_DIR / "journal_compliance_findings.tsv",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    audit_arg_paths = tuple(args.audit_tsv or DEFAULT_AUDIT_TSVS)
    summary_arg_paths = tuple(args.summary_json or DEFAULT_SUMMARIES)
    audit_tsvs = tuple(root / path if not path.is_absolute() else path for path in audit_arg_paths)
    summary_paths = tuple(
        root / path if not path.is_absolute() else path for path in summary_arg_paths
    )
    proxy_table = root / args.proxy_table if not args.proxy_table.is_absolute() else args.proxy_table
    summary, report_rows = build_report(
        root=root,
        audit_tsvs=audit_tsvs,
        summary_paths=summary_paths,
        proxy_table=proxy_table,
    )
    output_summary = (
        root / args.output_summary
        if not args.output_summary.is_absolute()
        else args.output_summary
    )
    output_tsv = root / args.output_tsv if not args.output_tsv.is_absolute() else args.output_tsv
    output_summary.parent.mkdir(parents=True, exist_ok=True)
    output_summary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_tsv(output_tsv, report_rows)
    print(
        json.dumps(
            {
                "ok": summary["ok"],
                "paper_reporting_compliant": summary["paper_reporting_compliant"],
                "all_stored_wer_fields_journal_compliant": summary[
                    "all_stored_wer_fields_journal_compliant"
                ],
                "output_summary": str(output_summary),
                "output_tsv": str(output_tsv),
            },
            ensure_ascii=False,
        )
    )
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

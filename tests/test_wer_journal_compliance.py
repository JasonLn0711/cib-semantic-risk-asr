from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "scoring"))

from audit_wer_journal_compliance import build_report  # noqa: E402


AUDIT_HEADER = (
    "run_id\trows\texpected_rows\tmetric\tunit\tnormalization\twer_tokenizer\t"
    "macro_percent\tmicro_percent\tjiwer_micro_percent\tjiwer_delta_percent\t"
    "zero_reference_unit_rows\tedit_count\treference_unit_count\tstored_cer_mean\t"
    "stored_wer_mean\tmissing_reference_rows\tmissing_hypothesis_rows\t"
    "missing_expected_ids\textra_ids\treference_mismatch_rows\tnotes\n"
)


def write_audit_tsv(path: Path, *, jiwer_delta: str = "0.0") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        AUDIT_HEADER
        + "\t".join(
            [
                "run_a",
                "2",
                "2",
                "wer_raw_whitespace",
                "word",
                "none",
                "whitespace",
                "100.0",
                "100.0",
                "100.0",
                "0.0",
                "0",
                "2",
                "2",
                "1.0",
                "100.0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "Legacy whitespace-token WER; invalid as a primary Chinese ASR metric.",
            ]
        )
        + "\n"
        + "\t".join(
            [
                "run_a",
                "2",
                "2",
                "wer_zh_jieba",
                "word",
                "zh_asr",
                "jieba",
                "12.5",
                "10.0",
                "10.0",
                jiwer_delta,
                "0",
                "1",
                "10",
                "1.0",
                "12.5",
                "0",
                "0",
                "0",
                "0",
                "0",
                "Supplemental Chinese word-level metric using deterministic jieba segmentation.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def write_summary(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "ok": True,
                "setup_checks": {
                    "expected_manifest_rows": 2,
                    "expected_rows_requested": 2,
                },
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def write_proxy_table(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "run_id\tmetric_profile\n"
        "run_a\tpaper_primary=cer_zh_micro; supplemental=wer_zh_jieba_micro\n",
        encoding="utf-8",
    )


def write_metrics_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "step,epoch,split,loss,cer,wer,learning_rate,wall_time_seconds,checkpoint,notes\n"
        "0,0,test,,1.0,100.0,,1.0,model,pilot_inference\n",
        encoding="utf-8",
    )


def test_report_allows_paper_policy_but_flags_legacy_stored_wer(tmp_path: Path) -> None:
    root = tmp_path
    audit_tsv = root / "audit.tsv"
    summary_json = root / "summary.json"
    proxy_table = root / "proxy.tsv"
    write_audit_tsv(audit_tsv)
    write_summary(summary_json)
    write_proxy_table(proxy_table)
    write_metrics_csv(root / "70_experiments" / "runs" / "legacy_run" / "metrics.csv")

    summary, rows = build_report(
        root=root,
        audit_tsvs=(audit_tsv,),
        summary_paths=(summary_json,),
        proxy_table=proxy_table,
    )

    assert summary["ok"] is True
    assert summary["paper_reporting_compliant"] is True
    assert summary["all_stored_wer_fields_journal_compliant"] is False
    assert summary["legacy_wer_fields_present"] is True
    assert summary["verdict"]["primary_chinese_surface_metric"] == "cer_zh_micro"
    assert any(row["paper_use"] == "audit_only" for row in rows)


def test_bad_jiwer_cross_check_blocks_paper_policy(tmp_path: Path) -> None:
    root = tmp_path
    audit_tsv = root / "audit.tsv"
    summary_json = root / "summary.json"
    proxy_table = root / "proxy.tsv"
    write_audit_tsv(audit_tsv, jiwer_delta="0.1")
    write_summary(summary_json)
    write_proxy_table(proxy_table)

    summary, _rows = build_report(
        root=root,
        audit_tsvs=(audit_tsv,),
        summary_paths=(summary_json,),
        proxy_table=proxy_table,
    )

    assert summary["ok"] is False
    assert summary["paper_reporting_compliant"] is False

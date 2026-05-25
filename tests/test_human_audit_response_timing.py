from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "annotation"))

from mark_human_audit_response_timing import mark_response_timing  # noqa: E402


FIELDS = [
    "row_number",
    "selection_stratum",
    "asr_run_id",
    "review_started_at",
    "review_finished_at",
    "review_elapsed_seconds",
    "reviewer_semantic_risk_label",
    "reviewer_notes",
]


def write_response(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def read_response(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def response_rows() -> list[dict[str, str]]:
    return [
        {"row_number": "1", "selection_stratum": "critical", "asr_run_id": "base"},
        {"row_number": "1", "selection_stratum": "critical", "asr_run_id": "lora"},
        {"row_number": "2", "selection_stratum": "critical", "asr_run_id": "base"},
    ]


def test_timing_helper_dry_run_does_not_modify_local_response(tmp_path: Path) -> None:
    response = tmp_path / "artifacts" / "response.tsv"
    write_response(response, response_rows())

    payload = mark_response_timing(
        response_sheet=response,
        row_number=1,
        output_dir=tmp_path,
        summary_json=tmp_path / "summary.json",
        log_tsv=tmp_path / "log.tsv",
        mark_start=False,
        mark_finish=False,
        started_at="2026-05-26T10:00:00+08:00",
        finished_at="2026-05-26T10:02:00+08:00",
        elapsed_seconds=None,
        force=False,
        write=False,
        repo_root=tmp_path,
    )

    assert payload["ok"] is True
    assert payload["status"] == "timing_dry_run_ready"
    assert payload["changed"] is True
    assert payload["review_timing"]["rows_with_timing"] == 1
    assert payload["review_timing"]["rows_missing_timing"] == 1
    assert all(row["review_started_at"] == "" for row in read_response(response))
    tracked = (tmp_path / "summary.json").read_text(encoding="utf-8")
    assert "PRIVATE_" not in tracked
    assert "reference_text" not in tracked
    assert "hypothesis_text" not in tracked
    assert "reviewer_notes" not in tracked


def test_timing_helper_write_updates_all_model_rows_for_selected_row(tmp_path: Path) -> None:
    response = tmp_path / "artifacts" / "response.tsv"
    write_response(response, response_rows())

    payload = mark_response_timing(
        response_sheet=response,
        row_number=1,
        output_dir=tmp_path,
        summary_json=tmp_path / "summary.json",
        log_tsv=tmp_path / "log.tsv",
        mark_start=False,
        mark_finish=False,
        started_at="2026-05-26T10:00:00+08:00",
        finished_at=None,
        elapsed_seconds="75",
        force=False,
        write=True,
        repo_root=tmp_path,
    )

    assert payload["ok"] is True
    assert payload["status"] == "timing_written"
    rows = read_response(response)
    row_1 = [row for row in rows if row["row_number"] == "1"]
    row_2 = [row for row in rows if row["row_number"] == "2"]
    assert {row["review_started_at"] for row in row_1} == {"2026-05-26T10:00:00+08:00"}
    assert {row["review_elapsed_seconds"] for row in row_1} == {"75"}
    assert row_2[0]["review_started_at"] == ""
    assert (tmp_path / "artifacts" / "response.tsv.bak").exists()
    log_text = (tmp_path / "log.tsv").read_text(encoding="utf-8")
    assert "timing_written" in log_text


def test_timing_helper_rejects_finish_before_start(tmp_path: Path) -> None:
    response = tmp_path / "artifacts" / "response.tsv"
    write_response(response, response_rows())

    payload = mark_response_timing(
        response_sheet=response,
        row_number=1,
        output_dir=tmp_path,
        summary_json=tmp_path / "summary.json",
        log_tsv=tmp_path / "log.tsv",
        mark_start=False,
        mark_finish=False,
        started_at="2026-05-26T10:02:00+08:00",
        finished_at="2026-05-26T10:00:00+08:00",
        elapsed_seconds=None,
        force=False,
        write=False,
        repo_root=tmp_path,
    )

    assert payload["ok"] is False
    assert payload["status"] == "timing_update_invalid"
    assert "review_finished_before_started" in payload["error_counts"]
    assert json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))["ok"] is False

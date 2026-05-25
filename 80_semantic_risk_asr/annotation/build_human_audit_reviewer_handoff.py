#!/usr/bin/env python3
"""Build a repo-safe reviewer handoff for the current selected-300 batch."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
ANNOTATION_DIR = SCRIPT_PATH.parent
REPO_ROOT = SCRIPT_PATH.parents[2]
if str(ANNOTATION_DIR) not in sys.path:
    sys.path.insert(0, str(ANNOTATION_DIR))

from prepare_human_audit_review_batch import (  # noqa: E402
    REFERENCE_TRANSCRIPT_POLICY,
    REMAINING_REVIEW_SCOPE,
    assert_tracked_safe,
    repo_relative,
)


DEFAULT_RUN_DIR = (
    REPO_ROOT
    / "70_experiments"
    / "runs"
    / "janus_300_high_stakes_human_audit_selection_2026_05_25"
)
DEFAULT_AUDIT_SHEET = DEFAULT_RUN_DIR / "artifacts" / "human_risk_atom_audit_sheet.tsv"
DEFAULT_BATCH_SUMMARY = DEFAULT_RUN_DIR / "human_audit_next_review_batch_summary.json"
DEFAULT_BATCH_STATUS = DEFAULT_RUN_DIR / "human_audit_current_review_batch_status_summary.json"
DEFAULT_TEMPLATE_SUMMARY = DEFAULT_RUN_DIR / "human_audit_batch_response_template_summary.json"
DEFAULT_APPLY_SUMMARY = DEFAULT_RUN_DIR / "human_audit_batch_response_apply_summary.json"
DEFAULT_APPLY_LOG_SUMMARY = DEFAULT_RUN_DIR / "human_audit_batch_response_apply_log_summary.json"
HANDOFF_SUMMARY_NAME = "human_audit_reviewer_handoff_summary.json"
SOURCE_FIELDS = (
    "batch_summary",
    "batch_status",
    "template_summary",
    "apply_summary",
    "apply_log_summary",
)


def read_json_if_exists(path: Path) -> tuple[dict[str, Any], str]:
    if not path.exists():
        return {}, "missing"
    return json.loads(path.read_text(encoding="utf-8")), "present"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def command(parts: list[str]) -> str:
    return " ".join(parts)


def reviewer_commands(
    *,
    response_sheet: str,
    audit_sheet: str,
    batch_summary: str,
    output_dir: str,
    readiness_output_dir: str,
    expected_rows: int,
    timing_row_number: int | None = None,
) -> dict[str, str]:
    session_start_summary = f"{output_dir}/human_audit_reviewer_session_start_summary.json"
    base = [
        ".venv/bin/python",
        "80_semantic_risk_asr/annotation/apply_human_audit_batch_response.py",
        "--require-complete",
        "--require-timing",
        "--require-session-start-gate",
        "--session-start-summary",
        session_start_summary,
        "--response-sheet",
        response_sheet,
        "--audit-sheet",
        audit_sheet,
        "--batch-summary",
        batch_summary,
        "--output-dir",
        output_dir,
        "--readiness-output-dir",
        readiness_output_dir,
        "--expected-rows",
        str(expected_rows),
    ]
    write = [
        ".venv/bin/python",
        "80_semantic_risk_asr/annotation/apply_human_audit_batch_response.py",
        "--require-complete",
        "--require-timing",
        "--require-session-start-gate",
        "--session-start-summary",
        session_start_summary,
        "--write",
        "--refresh-after-write",
        "--prepare-next-after-write",
        "--response-sheet",
        response_sheet,
        "--audit-sheet",
        audit_sheet,
        "--batch-summary",
        batch_summary,
        "--output-dir",
        output_dir,
        "--readiness-output-dir",
        readiness_output_dir,
        "--expected-rows",
        str(expected_rows),
    ]
    commands = {
        "strict_dry_run": command(base),
        "write_refresh_prepare_next": command(write),
        "batch_status_audit": command(
            [
                ".venv/bin/python",
                "80_semantic_risk_asr/annotation/audit_human_review_batch_status.py",
                "--audit-sheet",
                audit_sheet,
                "--batch-summary",
                batch_summary,
                "--output-dir",
                output_dir,
                "--expected-rows",
                str(expected_rows),
            ]
        ),
    }
    if timing_row_number is not None:
        timing_base = [
            ".venv/bin/python",
            "80_semantic_risk_asr/annotation/mark_human_audit_response_timing.py",
            "--response-sheet",
            response_sheet,
            "--row-number",
            str(timing_row_number),
        ]
        commands["timing_start_write"] = command([*timing_base, "--mark-start", "--write"])
        commands["timing_finish_write"] = command([*timing_base, "--mark-finish", "--write"])
    return commands


def source_paths(
    *,
    batch_summary_path: Path,
    batch_status_path: Path,
    template_summary_path: Path,
    apply_summary_path: Path,
    apply_log_summary_path: Path,
) -> dict[str, Path]:
    return {
        "batch_summary": batch_summary_path,
        "batch_status": batch_status_path,
        "template_summary": template_summary_path,
        "apply_summary": apply_summary_path,
        "apply_log_summary": apply_log_summary_path,
    }


def source_digests(paths: dict[str, Path], *, repo_root: Path) -> dict[str, dict[str, str]]:
    digests: dict[str, dict[str, str]] = {}
    for name in SOURCE_FIELDS:
        path = paths[name]
        item = {
            "path": repo_relative(path, repo_root=repo_root),
            "status": "present" if path.exists() else "missing",
            "sha256": sha256_file(path) if path.exists() else "",
        }
        digests[name] = item
    return digests


def compare_source_digests(
    expected: dict[str, Any],
    current: dict[str, dict[str, str]],
) -> dict[str, list[str]]:
    stale_sources: list[str] = []
    missing_sources: list[str] = []
    for name in SOURCE_FIELDS:
        expected_item = expected.get(name, {}) if isinstance(expected, dict) else {}
        current_item = current[name]
        if current_item["status"] != "present":
            missing_sources.append(name)
            continue
        if not isinstance(expected_item, dict) or expected_item.get("status") != "present":
            stale_sources.append(name)
            continue
        if expected_item.get("sha256") != current_item["sha256"]:
            stale_sources.append(name)
    return {
        "stale_sources": stale_sources,
        "missing_sources": missing_sources,
    }


def check_existing_handoff(
    *,
    handoff_summary_path: Path,
    batch_summary_path: Path,
    batch_status_path: Path,
    template_summary_path: Path,
    apply_summary_path: Path,
    apply_log_summary_path: Path,
    repo_root: Path,
) -> dict[str, Any]:
    started = time.time()
    paths = source_paths(
        batch_summary_path=batch_summary_path,
        batch_status_path=batch_status_path,
        template_summary_path=template_summary_path,
        apply_summary_path=apply_summary_path,
        apply_log_summary_path=apply_log_summary_path,
    )
    current = source_digests(paths, repo_root=repo_root)
    if not handoff_summary_path.exists():
        payload = {
            "ok": False,
            "status": "handoff_missing",
            "handoff_summary": repo_relative(handoff_summary_path, repo_root=repo_root),
            "freshness_status": "missing",
            "source_digests": current,
            "stale_sources": [],
            "missing_sources": [name for name, item in current.items() if item["status"] != "present"],
            "runtime_seconds": round(time.time() - started, 4),
        }
        assert_tracked_safe(payload)
        return payload

    existing = json.loads(handoff_summary_path.read_text(encoding="utf-8"))
    comparison = compare_source_digests(existing.get("source_digests", {}), current)
    stale_sources = comparison["stale_sources"]
    missing_sources = comparison["missing_sources"]
    status = "handoff_fresh" if not stale_sources and not missing_sources else "handoff_stale"
    payload = {
        "ok": status == "handoff_fresh",
        "status": status,
        "handoff_summary": repo_relative(handoff_summary_path, repo_root=repo_root),
        "freshness_status": "fresh" if status == "handoff_fresh" else "stale",
        "source_digests": current,
        "stale_sources": stale_sources,
        "missing_sources": missing_sources,
        "handoff_status": existing.get("status", ""),
        "latest_apply_status": (existing.get("current_gate") or {}).get("latest_apply_status", ""),
        "runtime_seconds": round(time.time() - started, 4),
    }
    assert_tracked_safe(payload)
    return payload


def build_handoff(
    *,
    run_dir: Path,
    audit_sheet: Path,
    batch_summary_path: Path,
    batch_status_path: Path,
    template_summary_path: Path,
    apply_summary_path: Path,
    apply_log_summary_path: Path,
    readiness_output_dir: Path,
    expected_rows: int,
    repo_root: Path,
) -> dict[str, Any]:
    started = time.time()
    sources: dict[str, str] = {}
    paths = source_paths(
        batch_summary_path=batch_summary_path,
        batch_status_path=batch_status_path,
        template_summary_path=template_summary_path,
        apply_summary_path=apply_summary_path,
        apply_log_summary_path=apply_log_summary_path,
    )
    digests = source_digests(paths, repo_root=repo_root)
    batch_summary, sources["batch_summary"] = read_json_if_exists(batch_summary_path)
    batch_status, sources["batch_status"] = read_json_if_exists(batch_status_path)
    template_summary, sources["template_summary"] = read_json_if_exists(template_summary_path)
    apply_summary, sources["apply_summary"] = read_json_if_exists(apply_summary_path)
    apply_log_summary, sources["apply_log_summary"] = read_json_if_exists(apply_log_summary_path)
    missing_inputs = [name for name, status in sources.items() if status != "present"]

    response_sheet = (
        template_summary.get("local_response_template_path")
        or apply_summary.get("response_sheet_path")
        or apply_log_summary.get("latest", {}).get("response_sheet_path", "")
    )
    latest_apply = apply_log_summary.get("latest") if isinstance(apply_log_summary.get("latest"), dict) else {}
    batch_ready = bool(batch_status.get("batch_ready_for_refresh"))
    latest_status = latest_apply.get("status") or apply_summary.get("status", "")
    handoff_status = "reviewer_handoff_missing_inputs"
    if not missing_inputs:
        if batch_ready:
            handoff_status = "batch_ready_for_refresh"
        elif latest_status == "response_complete":
            handoff_status = "response_complete_ready_to_write"
        else:
            handoff_status = "reviewer_input_pending"

    audit_sheet_rel = repo_relative(audit_sheet, repo_root=repo_root)
    batch_summary_rel = repo_relative(batch_summary_path, repo_root=repo_root)
    output_dir_rel = repo_relative(run_dir, repo_root=repo_root)
    readiness_rel = repo_relative(readiness_output_dir, repo_root=repo_root)
    row_numbers = batch_summary.get("row_numbers", [])
    timing_row_number = row_numbers[0] if row_numbers and isinstance(row_numbers[0], int) else None
    commands = reviewer_commands(
        response_sheet=str(response_sheet),
        audit_sheet=audit_sheet_rel,
        batch_summary=batch_summary_rel,
        output_dir=output_dir_rel,
        readiness_output_dir=readiness_rel,
        expected_rows=expected_rows,
        timing_row_number=timing_row_number,
    )
    payload = {
        "ok": not missing_inputs and bool(response_sheet),
        "status": handoff_status,
        "input_boundary": "tracked aggregate summaries plus local path pointers only",
        "output_boundary": "aggregate-only reviewer handoff; no private row keys or transcript text",
        "reference_transcript_policy": REFERENCE_TRANSCRIPT_POLICY,
        "remaining_review_scope": REMAINING_REVIEW_SCOPE,
        "source_status": sources,
        "source_digests": digests,
        "freshness_status": "fresh" if not missing_inputs else "missing_inputs",
        "missing_inputs": missing_inputs,
        "current_packet": {
            "selection_stratum": batch_summary.get("selection_stratum", ""),
            "row_numbers": batch_summary.get("row_numbers", []),
            "rows_in_batch": batch_summary.get("rows_in_batch", ""),
            "model_assessments_in_batch": batch_status.get("model_assessments_in_batch", ""),
            "local_packet_path": batch_summary.get("local_packet_path", ""),
        },
        "current_response": {
            "local_response_template_path": response_sheet,
            "response_rows": template_summary.get("response_rows", ""),
            "template_column_count": template_summary.get("template_column_count", ""),
            "required_timing_fields": [
                "review_started_at",
                "review_finished_at",
                "review_elapsed_seconds",
            ],
            "optional_timing_fields": [
                "review_started_at",
                "review_finished_at",
                "review_elapsed_seconds",
            ],
        },
        "current_gate": {
            "batch_status": batch_status.get("status", ""),
            "batch_ready_for_refresh": batch_ready,
            "latest_apply_status": latest_status,
            "latest_apply_ok": latest_apply.get("ok", apply_summary.get("ok", "")),
            "latest_error_keys": latest_apply.get(
                "error_keys",
                ",".join(sorted((apply_summary.get("error_counts") or {}).keys())),
            ),
            "reviewed_rows_in_batch": batch_status.get("reviewed_rows_in_batch", ""),
            "pending_rows_in_batch": batch_status.get("pending_rows_in_batch", ""),
            "reviewed_model_assessments_in_batch": batch_status.get(
                "reviewed_model_assessments_in_batch",
                "",
            ),
            "pending_model_assessments_in_batch": batch_status.get(
                "pending_model_assessments_in_batch",
                "",
            ),
            "rows_with_timing": latest_apply.get(
                "rows_with_timing",
                (apply_summary.get("review_timing") or {}).get("rows_with_timing", ""),
            ),
            "rows_missing_timing": latest_apply.get(
                "rows_missing_timing",
                (apply_summary.get("review_timing") or {}).get("rows_missing_timing", ""),
            ),
        },
        "apply_log": {
            "status": apply_log_summary.get("status", ""),
            "entries": apply_log_summary.get("apply_log_entries", ""),
            "status_counts": apply_log_summary.get("status_counts", {}),
            "error_key_counts": apply_log_summary.get("error_key_counts", {}),
            "latest_recorded_at": latest_apply.get("recorded_at", ""),
        },
        "reviewer_next_steps": [
            "Open the local packet path only in the local workspace; it is transcript-bearing.",
            "Fill the local response TSV row/model fields plus required per-row review timing.",
            "Use timing_start_write and timing_finish_write if review timing should be written by helper command.",
            "Run strict_dry_run until latest_apply_status is response_complete.",
            "Run write_refresh_prepare_next only after strict_dry_run is response_complete.",
        ],
        "commands": commands,
        "tracked_outputs": {
            "handoff_summary": repo_relative(run_dir / HANDOFF_SUMMARY_NAME, repo_root=repo_root),
            "apply_log_summary": repo_relative(apply_log_summary_path, repo_root=repo_root),
            "batch_status": repo_relative(batch_status_path, repo_root=repo_root),
        },
        "runtime_seconds": round(time.time() - started, 4),
    }
    assert_tracked_safe(payload)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--audit-sheet", type=Path, default=DEFAULT_AUDIT_SHEET)
    parser.add_argument("--batch-summary", type=Path, default=DEFAULT_BATCH_SUMMARY)
    parser.add_argument("--batch-status", type=Path, default=DEFAULT_BATCH_STATUS)
    parser.add_argument("--template-summary", type=Path, default=DEFAULT_TEMPLATE_SUMMARY)
    parser.add_argument("--apply-summary", type=Path, default=DEFAULT_APPLY_SUMMARY)
    parser.add_argument("--apply-log-summary", type=Path, default=DEFAULT_APPLY_LOG_SUMMARY)
    parser.add_argument(
        "--readiness-output-dir",
        type=Path,
        default=REPO_ROOT / "70_experiments" / "runs" / "postdoc_evidence_chain_2026_05_25",
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--expected-rows", type=int, default=30)
    parser.add_argument(
        "--check-existing",
        action="store_true",
        help="Check whether the current handoff summary still matches source-summary digests.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_json = args.output_json or args.run_dir / HANDOFF_SUMMARY_NAME
    if args.check_existing:
        payload = check_existing_handoff(
            handoff_summary_path=output_json,
            batch_summary_path=args.batch_summary,
            batch_status_path=args.batch_status,
            template_summary_path=args.template_summary,
            apply_summary_path=args.apply_summary,
            apply_log_summary_path=args.apply_log_summary,
            repo_root=REPO_ROOT,
        )
        print(json.dumps(payload, ensure_ascii=False))
        return 0 if payload["ok"] else 1

    payload = build_handoff(
        run_dir=args.run_dir,
        audit_sheet=args.audit_sheet,
        batch_summary_path=args.batch_summary,
        batch_status_path=args.batch_status,
        template_summary_path=args.template_summary,
        apply_summary_path=args.apply_summary,
        apply_log_summary_path=args.apply_log_summary,
        readiness_output_dir=args.readiness_output_dir,
        expected_rows=args.expected_rows,
        repo_root=REPO_ROOT,
    )
    write_json(output_json, payload)
    print(
        json.dumps(
            {
                "ok": payload["ok"],
                "status": payload["status"],
                "latest_apply_status": payload["current_gate"]["latest_apply_status"],
                "handoff_summary": str(output_json),
            },
            ensure_ascii=False,
        )
    )
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

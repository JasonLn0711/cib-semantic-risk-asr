#!/usr/bin/env python3
"""Prepare a local transcript-bearing review packet plus tracked batch records."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
ANNOTATION_DIR = SCRIPT_PATH.parent
REPO_ROOT = SCRIPT_PATH.parents[2]
if str(ANNOTATION_DIR) not in sys.path:
    sys.path.insert(0, str(ANNOTATION_DIR))

import validate_human_risk_atom_audit as validation  # noqa: E402


DEFAULT_RUN_DIR = (
    REPO_ROOT
    / "70_experiments"
    / "runs"
    / "janus_300_high_stakes_human_audit_selection_2026_05_25"
)
DEFAULT_AUDIT_SHEET = DEFAULT_RUN_DIR / "artifacts" / "human_risk_atom_audit_sheet.tsv"
DEFAULT_LOCAL_PACKET_DIR = DEFAULT_RUN_DIR / "artifacts" / "review_batches"
SUMMARY_NAME = "human_audit_next_review_batch_summary.json"
ROWS_NAME = "human_audit_next_review_batch_rows.tsv"
LOG_NAME = "human_audit_review_batch_log.tsv"

ROW_REVIEW_FIELDS = validation.ROW_REVIEW_FIELDS
MODEL_REVIEW_FIELDS = validation.MODEL_REVIEW_FIELDS
STRATUM_PRIORITY = {
    "critical_or_high_risk_missed": 0,
    "unsafe_downrouting": 1,
    "high_proxy_risk": 2,
    "model_disagreement": 3,
    "risk_score_fill": 4,
    "clean_control": 5,
}
SENSITIVE_TOKENS = (
    "audio_id",
    "sample_id",
    "reference_text",
    "hypothesis_text",
    "asr_hypotheses_json",
    "reviewer_model_assessments_json",
    "reviewer_notes",
    "reviewer_verified_transcript",
    "PRIVATE_",
)
REFERENCE_TRANSCRIPT_POLICY = (
    "Reference transcripts are already human-reviewed ground truth for WER/CER "
    "scoring; this packet does not ask for duplicate transcript review."
)
REMAINING_REVIEW_SCOPE = (
    "The packet asks reviewers to complete risk atoms, decision-change labels, "
    "expected safe action, confidence, and per-model assessment fields."
)


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), list(reader)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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


def append_tsv(path: Path, row: dict[str, Any], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
        )
        if write_header:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in fieldnames})


def parse_json_field(value: str) -> Any:
    if not value.strip():
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def repo_relative(path: Path, *, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return slug.strip("_") or "review_batch"


def model_assessment_reviewed(item: dict[str, Any]) -> bool:
    return all(str(item.get(field, "")).strip() for field in MODEL_REVIEW_FIELDS)


def iter_model_assessments(row: dict[str, str]) -> list[dict[str, Any]]:
    value = parse_json_field(row.get("reviewer_model_assessments_json", ""))
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def missing_row_fields(row: dict[str, str]) -> list[str]:
    return [field for field in ROW_REVIEW_FIELDS if not (row.get(field) or "").strip()]


def missing_model_field_counts(row: dict[str, str]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for item in iter_model_assessments(row):
        for field in MODEL_REVIEW_FIELDS:
            if not str(item.get(field, "")).strip():
                counts[field] += 1
    return counts


def model_counts(row: dict[str, str]) -> tuple[int, int, int]:
    assessments = iter_model_assessments(row)
    reviewed = sum(1 for item in assessments if model_assessment_reviewed(item))
    return len(assessments), reviewed, len(assessments) - reviewed


def row_needs_review(row: dict[str, str]) -> bool:
    total_models, reviewed_models, _pending_models = model_counts(row)
    return bool(missing_row_fields(row)) or reviewed_models < total_models


def pending_stratum_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        if row_needs_review(row):
            counts[row.get("selection_stratum", "") or "unknown"] += 1
    return dict(counts)


def choose_stratum(rows: list[dict[str, str]], requested: str | None) -> str:
    counts = pending_stratum_counts(rows)
    if requested:
        if counts.get(requested, 0) == 0:
            raise ValueError(f"requested stratum has no pending rows: {requested}")
        return requested
    if not counts:
        raise ValueError("no pending review rows remain")
    return sorted(counts, key=lambda item: (STRATUM_PRIORITY.get(item, 99), item))[0]


def batch_order(stratum: str) -> int:
    return STRATUM_PRIORITY.get(stratum, 98) + 1


def reason_for_stratum(stratum: str) -> str:
    return {
        "critical_or_high_risk_missed": "highest paper-safety risk; resolves missed critical/high-risk cases first",
        "unsafe_downrouting": "directly targets dangerous de-escalation claims",
        "high_proxy_risk": "checks whether proxy SRES/CEIS risk is human-confirmed",
        "model_disagreement": "supports model-comparison claims without relying on row-level labels alone",
        "risk_score_fill": "fills residual high-score evidence coverage",
        "clean_control": "provides negative/control rows for reviewer calibration",
    }.get(stratum, "unrecognized stratum; review after named strata")


def safe_row_summary(row_number: int, row: dict[str, str]) -> dict[str, Any]:
    total_models, reviewed_models, pending_models = model_counts(row)
    missing_models = missing_model_field_counts(row)
    return {
        "row_number": row_number,
        "selection_stratum": row.get("selection_stratum", "") or "unknown",
        "row_review_complete": validation.row_review_complete(row),
        "missing_row_fields": ",".join(missing_row_fields(row)),
        "model_assessments": total_models,
        "reviewed_model_assessments": reviewed_models,
        "pending_model_assessments": pending_models,
        "missing_model_field_counts": ",".join(
            f"{field}={count}" for field, count in sorted(missing_models.items())
        ),
        "model_run_ids": ",".join(
            sorted(str(item.get("asr_run_id", "") or "unknown") for item in iter_model_assessments(row))
        ),
    }


def local_packet_row(row_number: int, row: dict[str, str]) -> dict[str, Any]:
    return {
        "row_number": row_number,
        "selection_stratum": row.get("selection_stratum", ""),
        "selection_reason": row.get("selection_reason", ""),
        "split": row.get("split", ""),
        "reference_label": row.get("reference_label", ""),
        "reference_text": row.get("reference_text", ""),
        "risk_signal": parse_json_field(row.get("risk_signal_json", "")),
        "asr_hypotheses": parse_json_field(row.get("asr_hypotheses_json", "")),
        "current_reviewer_fields": {
            field: row.get(field, "")
            for field in [
                "reviewer_semantic_risk_label",
                "reviewer_risk_atoms",
                "reviewer_critical_atoms",
                "reviewer_asr_confusion_terms",
                "reviewer_would_asr_error_change_decision",
                "reviewer_decision_change_reason",
                "reviewer_expected_safe_action",
                "reviewer_annotation_confidence",
                "reviewer_notes",
            ]
        },
        "current_model_assessments": parse_json_field(
            row.get("reviewer_model_assessments_json", "")
        ),
    }


def update_command_template(row_number: int, assessments: list[dict[str, Any]]) -> str:
    model_lines = []
    for item in assessments:
        run_id = str(item.get("asr_run_id", ""))
        if not run_id:
            continue
        model_lines.append(
            f"  --model-review {run_id}:<yes|no|uncertain>:<critical_atoms|none>:"
            "<expected_safe_action>:<high|medium|low> \\"
        )
    model_block = "\n".join(model_lines)
    if model_block:
        model_block = model_block.rstrip(" \\")
    return "\n".join(
        [
            ".venv/bin/python 80_semantic_risk_asr/annotation/review_human_risk_atom_audit.py \\",
            "  --audit-sheet 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/artifacts/human_risk_atom_audit_sheet.tsv \\",
            f"  --row-number {row_number} \\",
            "  --semantic-risk-label <no_escalation|review|priority_review|critical_escalation> \\",
            "  --risk-atoms <atoms_or_none> \\",
            "  --critical-atoms <atoms_or_none> \\",
            "  --asr-confusion-terms \"<short local note>\" \\",
            "  --decision-change <yes|no|uncertain> \\",
            "  --decision-change-reason \"<routing/safety reason>\" \\",
            "  --expected-safe-action <none|manual_review|priority_review|critical_escalation|conservative_machine_action|abstain> \\",
            "  --confidence <high|medium|low> \\",
            model_block,
        ]
    ).strip()


def render_local_packet(rows: list[tuple[int, dict[str, str]]], stratum: str) -> str:
    parts = [
        "# Local Selected-300 Human Audit Review Packet",
        "",
        "Privacy: this packet is transcript-bearing local output. Do not commit, paste, or export it.",
        f"Selection stratum: `{stratum}`",
        f"Rows in packet: `{len(rows)}`",
        "",
        "Transcript policy: reference transcripts are already accepted as human-reviewed WER/CER ground truth. Use `reviewer_verified_transcript` only for explicit correction exceptions.",
        "",
    ]
    for row_number, row in rows:
        packet = local_packet_row(row_number, row)
        assessments = packet.get("current_model_assessments") or []
        parts.extend(
            [
                f"## Row {row_number}",
                "",
                f"- Selection stratum: `{packet['selection_stratum']}`",
                f"- Selection reason: `{packet['selection_reason']}`",
                f"- Split: `{packet['split']}`",
                f"- Reference label: `{packet['reference_label']}`",
                "",
                "Reference transcript:",
                "",
                "```text",
                str(packet["reference_text"]),
                "```",
                "",
                "Proxy risk signal:",
                "",
                "```json",
                json.dumps(packet["risk_signal"], ensure_ascii=False, indent=2),
                "```",
                "",
                "ASR hypotheses and current model assessments:",
                "",
                "```json",
                json.dumps(
                    {
                        "asr_hypotheses": packet["asr_hypotheses"],
                        "current_model_assessments": assessments,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                "```",
                "",
                "Dry-run update command template:",
                "",
                "```bash",
                update_command_template(row_number, assessments if isinstance(assessments, list) else []),
                "```",
                "",
            ]
        )
    return "\n".join(parts) + "\n"


def assert_tracked_safe(payload: Any) -> None:
    text = json.dumps(payload, ensure_ascii=False) if not isinstance(payload, str) else payload
    for token in SENSITIVE_TOKENS:
        if token in text:
            raise ValueError(f"tracked batch output contains sensitive token: {token}")


def prepare_batch(
    *,
    audit_sheet: Path,
    output_dir: Path,
    local_packet_dir: Path,
    selection_stratum: str | None,
    expected_rows: int | None,
    repo_root: Path,
) -> dict[str, Any]:
    started = time.time()
    fieldnames, rows = read_tsv(audit_sheet)
    validation_payload = validation.validate_rows(
        fieldnames,
        rows,
        require_complete=False,
        expected_rows=expected_rows,
    )
    stratum = choose_stratum(rows, selection_stratum)
    batch = [
        (index + 1, row)
        for index, row in enumerate(rows)
        if (row.get("selection_stratum", "") or "unknown") == stratum and row_needs_review(row)
    ]
    if not batch:
        raise ValueError(f"no pending rows found for stratum: {stratum}")

    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    packet_name = f"{timestamp.replace(':', '').replace('+', '_')}_{slugify(stratum)}.md"
    local_packet_path = local_packet_dir / packet_name
    local_packet_path.parent.mkdir(parents=True, exist_ok=True)
    local_packet_path.write_text(render_local_packet(batch, stratum), encoding="utf-8")

    row_summaries = [safe_row_summary(row_number, row) for row_number, row in batch]
    row_fieldnames = [
        "batch_order",
        "selection_stratum",
        "row_number",
        "row_review_complete",
        "missing_row_fields",
        "model_assessments",
        "reviewed_model_assessments",
        "pending_model_assessments",
        "missing_model_field_counts",
        "model_run_ids",
    ]
    for item in row_summaries:
        item["batch_order"] = batch_order(stratum)

    rows_path = output_dir / ROWS_NAME
    summary_path = output_dir / SUMMARY_NAME
    log_path = output_dir / LOG_NAME
    write_tsv(rows_path, row_summaries, row_fieldnames)

    summary = {
        "ok": validation_payload["ok"],
        "status": "batch_prepared",
        "created_at": timestamp,
        "input_boundary": "local ignored audit sheet; transcript-bearing content is written only to ignored artifacts",
        "output_boundary": "tracked outputs contain row numbers, strata, completion counts, and local packet path only",
        "reference_transcript_policy": REFERENCE_TRANSCRIPT_POLICY,
        "remaining_review_scope": REMAINING_REVIEW_SCOPE,
        "selection_stratum": stratum,
        "batch_order": batch_order(stratum),
        "primary_reason": reason_for_stratum(stratum),
        "rows_in_batch": len(batch),
        "row_numbers": [row_number for row_number, _row in batch],
        "audit_rows": validation_payload["audit_rows"],
        "reviewed_rows": validation_payload["reviewed_rows"],
        "pending_rows": validation_payload["pending_rows"],
        "model_assessments": validation_payload["model_assessments"],
        "reviewed_model_assessments": validation_payload["reviewed_model_assessments"],
        "pending_model_assessments": validation_payload["pending_model_assessments"],
        "local_packet_path": repo_relative(local_packet_path, repo_root=repo_root),
        "tracked_rows_path": repo_relative(rows_path, repo_root=repo_root),
        "tracked_log_path": repo_relative(log_path, repo_root=repo_root),
        "first_principle_decision": (
            "Reviewer attention should first resolve the highest safety-risk "
            "decision evidence, not produce another ASR run or duplicate transcript review."
        ),
        "next_action": (
            "Open the local packet, complete row and model assessment fields via "
            "review_human_risk_atom_audit.py dry-runs, write only after validation, "
            "then run refresh_human_audit_evidence.py --require-complete when all batches finish."
        ),
        "runtime_seconds": round(time.time() - started, 4),
    }
    assert_tracked_safe(summary)
    assert_tracked_safe(row_summaries)
    write_json(summary_path, summary)
    append_tsv(
        log_path,
        {
            "created_at": timestamp,
            "selection_stratum": stratum,
            "batch_order": batch_order(stratum),
            "rows_in_batch": len(batch),
            "row_numbers": ",".join(str(row_number) for row_number, _row in batch),
            "local_packet_path": repo_relative(local_packet_path, repo_root=repo_root),
            "status": "batch_prepared",
        },
        [
            "created_at",
            "selection_stratum",
            "batch_order",
            "rows_in_batch",
            "row_numbers",
            "local_packet_path",
            "status",
        ],
    )
    return {
        **summary,
        "tracked_summary_path": repo_relative(summary_path, repo_root=repo_root),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-sheet", type=Path, default=DEFAULT_AUDIT_SHEET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--local-packet-dir", type=Path, default=DEFAULT_LOCAL_PACKET_DIR)
    parser.add_argument("--selection-stratum")
    parser.add_argument("--expected-rows", type=int, default=30)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = prepare_batch(
        audit_sheet=args.audit_sheet,
        output_dir=args.output_dir,
        local_packet_dir=args.local_packet_dir,
        selection_stratum=args.selection_stratum,
        expected_rows=args.expected_rows,
        repo_root=REPO_ROOT,
    )
    print(
        json.dumps(
            {
                "ok": payload["ok"],
                "status": payload["status"],
                "selection_stratum": payload["selection_stratum"],
                "rows_in_batch": payload["rows_in_batch"],
                "tracked_summary_path": payload["tracked_summary_path"],
                "local_packet_path": payload["local_packet_path"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

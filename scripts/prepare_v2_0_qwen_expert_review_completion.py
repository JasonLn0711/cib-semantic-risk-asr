#!/usr/bin/env python3
"""Prepare repo-safe Qwen expert-review completion aggregates."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import time
import zipfile
from pathlib import Path
from typing import Any

from run_v2_0_qwen_opencc_locale_repair import privacy_record


RUN_ID = "v2_0_multimodal_qwen_expert_review_completion_2026_06_01"
MODEL_ID = "Qwen/Qwen2.5-Omni-7B"
SOURCE_PACKET_RUN_ID = "v2_0_multimodal_qwen_expert_review_packet_2026_06_01"
SOURCE_PROXY_RUN_ID = "v2_0_multimodal_qwen_auto_semantic_damage_proxy_2026_06_01"
DEFAULT_ZIP = Path.home() / "Downloads" / "qwen_expert_review_outputs_2026_06_01.zip"
DEFAULT_OUT_DIR = Path("70_experiments/runs") / RUN_ID
EXPECTED_TSV = "qwen_locale_residual_expert_review_completed_2026_06_01.tsv"
EXPECTED_ROWS = 7
PROHIBITED_TRACKED_FIELDS = {
    "review_item_id",
    "source_order",
    "audio_id",
    "reference_text",
    "raw_hypothesis_text",
    "repaired_hypothesis_text",
    "expert_notes",
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def value_counts(rows: list[dict[str, str]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = (row.get(field) or "").strip() or "blank"
        counts[value] = counts.get(value, 0) + 1
    return counts


def count_rows(counts: dict[str, int], key: str) -> int:
    return int(counts.get(key, 0))


def read_review_zip(path: Path) -> tuple[str, list[dict[str, Any]], list[dict[str, str]]]:
    zip_bytes = path.read_bytes()
    zip_sha = sha256_bytes(zip_bytes)
    file_rows: list[dict[str, Any]] = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        names = archive.namelist()
        if EXPECTED_TSV not in names:
            raise SystemExit(f"missing_expected_tsv:{EXPECTED_TSV}")
        for info in archive.infolist():
            payload = archive.read(info.filename)
            file_rows.append(
                {
                    "file_name": info.filename,
                    "artifact_role": "expert_review_output_zip_member",
                    "byte_size": info.file_size,
                    "sha256": sha256_bytes(payload),
                    "tracked_payload": "false",
                }
            )
        tsv_payload = archive.read(EXPECTED_TSV).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(tsv_payload), delimiter="\t")
    review_rows = list(reader)
    if len(review_rows) != EXPECTED_ROWS:
        raise SystemExit(f"unexpected_review_row_count:{len(review_rows)}")
    missing = {
        "expert_semantic_acceptability",
        "expert_locale_acceptability",
        "expert_critical_term_damage",
        "expert_hallucination_or_omission",
    } - set(reader.fieldnames or [])
    if missing:
        raise SystemExit(f"missing_required_expert_fields:{','.join(sorted(missing))}")
    return zip_sha, file_rows, review_rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=Path, default=DEFAULT_ZIP)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    if not args.zip.exists():
        raise SystemExit(f"missing_zip:{args.zip.name}")

    zip_sha, file_rows, review_rows = read_review_zip(args.zip)
    semantic_counts = value_counts(review_rows, "expert_semantic_acceptability")
    locale_counts = value_counts(review_rows, "expert_locale_acceptability")
    critical_counts = value_counts(review_rows, "expert_critical_term_damage")
    hallucination_counts = value_counts(review_rows, "expert_hallucination_or_omission")

    semantic_accept_rows = count_rows(semantic_counts, "accept")
    semantic_minor_rows = count_rows(semantic_counts, "minor_issue")
    semantic_reject_rows = count_rows(semantic_counts, "reject")
    critical_major_rows = count_rows(critical_counts, "major")
    critical_minor_rows = count_rows(critical_counts, "minor")
    hallucination_or_omission_rows = EXPECTED_ROWS - count_rows(hallucination_counts, "none")
    final_transcript_usable_rows = semantic_accept_rows
    semantic_damage_blocker_rows = sum(
        1
        for row in review_rows
        if row.get("expert_semantic_acceptability") == "reject"
        or row.get("expert_critical_term_damage") == "major"
    )
    promotion_decision = "do_not_promote_repaired_pipeline"

    args.out_dir.mkdir(parents=True, exist_ok=True)
    aggregate_rows = [
        {"metric_name": "review_rows", "metric_value": EXPECTED_ROWS, "metric_scope": "expert_review_completion"},
        {
            "metric_name": "semantic_accept_rows",
            "metric_value": semantic_accept_rows,
            "metric_scope": "expert_review_completion",
        },
        {
            "metric_name": "semantic_minor_issue_rows",
            "metric_value": semantic_minor_rows,
            "metric_scope": "expert_review_completion",
        },
        {
            "metric_name": "semantic_reject_rows",
            "metric_value": semantic_reject_rows,
            "metric_scope": "expert_review_completion",
        },
        {
            "metric_name": "critical_major_rows",
            "metric_value": critical_major_rows,
            "metric_scope": "expert_review_completion",
        },
        {
            "metric_name": "critical_minor_rows",
            "metric_value": critical_minor_rows,
            "metric_scope": "expert_review_completion",
        },
        {
            "metric_name": "hallucination_or_omission_rows",
            "metric_value": hallucination_or_omission_rows,
            "metric_scope": "expert_review_completion",
        },
        {
            "metric_name": "final_transcript_usable_rows",
            "metric_value": final_transcript_usable_rows,
            "metric_scope": "expert_review_completion",
        },
        {
            "metric_name": "semantic_damage_blocker_rows",
            "metric_value": semantic_damage_blocker_rows,
            "metric_scope": "expert_review_completion",
        },
    ]
    write_tsv(args.out_dir / "expert_review_aggregate_counts.tsv", aggregate_rows, list(aggregate_rows[0]))
    write_tsv(
        args.out_dir / "expert_review_value_counts.tsv",
        [
            {"field_name": "expert_semantic_acceptability", "field_value": k, "row_count": v}
            for k, v in sorted(semantic_counts.items())
        ]
        + [
            {"field_name": "expert_locale_acceptability", "field_value": k, "row_count": v}
            for k, v in sorted(locale_counts.items())
        ]
        + [
            {"field_name": "expert_critical_term_damage", "field_value": k, "row_count": v}
            for k, v in sorted(critical_counts.items())
        ]
        + [
            {"field_name": "expert_hallucination_or_omission", "field_value": k, "row_count": v}
            for k, v in sorted(hallucination_counts.items())
        ],
        ["field_name", "field_value", "row_count"],
    )
    write_tsv(args.out_dir / "expert_review_output_file_hashes.tsv", file_rows, list(file_rows[0]))
    manifest_rows = [
        {
            "artifact_class": "qwen_locale_residual_expert_review_completed_zip",
            "artifact_count": 1,
            "review_rows": EXPECTED_ROWS,
            "sensitivity": "transcript_bearing_non_audio_local_downloads_only",
            "storage_policy": "downloads_folder_not_tracked",
            "tracked_payload": "false",
            "sha256": zip_sha,
            "manifest_status": "expert_review_completed_hash_recorded",
            "supporting_gate_decision": promotion_decision,
        }
    ]
    write_tsv(args.out_dir / "controlled_artifact_manifest.tsv", manifest_rows, list(manifest_rows[0]))

    summary = {
        "run_id": RUN_ID,
        "generated_at_unix": int(time.time()),
        "status": "qwen_expert_review_completed_local_only",
        "source_packet_run_id": SOURCE_PACKET_RUN_ID,
        "source_proxy_run_id": SOURCE_PROXY_RUN_ID,
        "model_id": MODEL_ID,
        "review_scope": "qwen_repaired_pipeline_locale_residual_rows",
        "review_row_count": EXPECTED_ROWS,
        "zip_file_name": args.zip.name,
        "zip_sha256": zip_sha,
        "zip_payload_tracked": False,
        "semantic_accept_rows": semantic_accept_rows,
        "semantic_minor_issue_rows": semantic_minor_rows,
        "semantic_reject_rows": semantic_reject_rows,
        "critical_major_rows": critical_major_rows,
        "critical_minor_rows": critical_minor_rows,
        "hallucination_or_omission_rows": hallucination_or_omission_rows,
        "locale_value_counts": locale_counts,
        "final_transcript_usable_rows": final_transcript_usable_rows,
        "semantic_damage_blocker_rows": semantic_damage_blocker_rows,
        "promotion_decision": promotion_decision,
        "claim_boundary": "expert_review_completion_blocks_qwen_repaired_pipeline_final_transcript_claim",
        "larger_gate_policy": "keep_taiwan_utility_30_row_258_selected300_closed_for_qwen_repaired_pipeline",
        "privacy": privacy_record(),
    }
    (args.out_dir / "expert_review_completion_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    readme = f"""# Qwen Expert Review Completion

This record summarizes the completed expert review for Qwen repaired-pipeline
locale-residual rows. The completed TSV and reports remain outside Git because
they contain transcript-bearing fields and identifying fragments.

## Result

```text
review_rows={EXPECTED_ROWS}
semantic_accept_rows={semantic_accept_rows}
semantic_minor_issue_rows={semantic_minor_rows}
semantic_reject_rows={semantic_reject_rows}
critical_major_rows={critical_major_rows}
critical_minor_rows={critical_minor_rows}
hallucination_or_omission_rows={hallucination_or_omission_rows}
final_transcript_usable_rows={final_transcript_usable_rows}
promotion_decision={promotion_decision}
```

## Decision

The repaired Qwen residual subset is useful as repair evidence, but it is not
safe as final transcript evidence. Larger Qwen repaired-pipeline gates remain
closed unless a new non-human claim-evidence design or a new repaired model
first clears the required semantic and locale gates.
"""
    (args.out_dir / "README.md").write_text(readme, encoding="utf-8")
    print(f"qwen_expert_review_completion_written {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

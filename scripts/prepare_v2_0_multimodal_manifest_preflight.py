#!/usr/bin/env python3
"""Create aggregate-only Gate A manifest preflight records.

The real manifest files are local-only and may contain private local paths or
row selectors. This script never copies row-level fields or values into tracked
artifacts; it records only existence, row counts, field counts, and gate status.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


RUN_ID = "v2_0_multimodal_batch1_manifest_preflight_2026_05_31"
DEFAULT_OUT_DIR = Path("70_experiments/runs") / RUN_ID


@dataclass(frozen=True)
class ManifestSpec:
    manifest_id: str
    default_path: str
    gate: str
    minimum_rows: int
    required_before: str
    status_if_missing: str


MANIFESTS = [
    ManifestSpec(
        "one_row_smoke",
        "one_row_smoke_manifest.local.tsv",
        "Gate C one-row transcript-only smoke",
        1,
        "real one-row smoke inference",
        "required_next",
    ),
    ManifestSpec(
        "sentinel_negative_control",
        "sentinel_negative_control_manifest.local.tsv",
        "Gate D sentinel negative controls",
        6,
        "sentinel gate",
        "pending_after_smoke",
    ),
    ManifestSpec(
        "fixed_15_row_multimodal",
        "fixed_15_row_multimodal_manifest.local.tsv",
        "Gate E fixed 15-row transcript gate",
        15,
        "15-row transcript scoring",
        "pending_after_sentinel",
    ),
    ManifestSpec(
        "human_reviewed_30_row_cds",
        "human_reviewed_30_row_cds_manifest.local.tsv",
        "Gate G human-reviewed 30-row CDS gate",
        30,
        "30-row CDS gate",
        "pending_after_15_row",
    ),
    ManifestSpec(
        "promoted_258_row",
        "promoted_258_row_manifest.local.tsv",
        "Gate I promoted 258-row split",
        258,
        "promoted 258-row split",
        "pending_for_scientific_winners",
    ),
    ManifestSpec(
        "selected_300_multimodal",
        "selected_300_multimodal_manifest.local.tsv",
        "Gate J selected-300 high-stakes evidence",
        300,
        "selected-300 high-stakes evidence",
        "pending_for_scientific_winners",
    ),
]


def count_tsv(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "exists": False,
            "row_count": 0,
            "field_count": 0,
            "field_names_tracked": False,
        }
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = reader.fieldnames or []
        rows = sum(1 for _ in reader)
    return {
        "exists": True,
        "row_count": rows,
        "field_count": len(fields),
        "field_names_tracked": False,
    }


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    missing = summary["missing_required_next"]
    if missing:
        next_step = (
            "Create or attach `one_row_smoke_manifest.local.tsv` locally, then "
            "run the real one-row transcript-only smoke adapters. Do not track "
            "the local manifest."
        )
    else:
        next_step = (
            "Use the available local-only manifests for their active gates and "
            "create later fixed-15, 30-row, 258-row, and selected-300 manifests "
            "only when promotion rules require them. Do not track local "
            "manifest values."
        )
    text = f"""# v2.0 Batch 1 Manifest Preflight

Date: 2026-05-31

Status: aggregate manifest preflight recorded; local-only manifest content is
not tracked

本紀錄只保存 manifest count/status，不保存任何逐字稿或私有音訊內容。

## Purpose

This Gate A record checks whether the local-only manifests needed for the v2.0
Batch 1 multimodal experiment exist. It records only aggregate status, row
counts, field counts, and the next required action.

## Privacy Boundary

The local manifest files may contain protected row selectors or local audio
locators. Those files must remain ignored by git. This tracked record does not
store manifest field names, row IDs, audio IDs, transcript text, hypotheses,
reviewer notes, or local file paths.

## Current Result

```text
manifest_specs={summary['manifest_specs']}
manifest_files_present={summary['manifest_files_present']}
missing_required_next={missing}
next_gate={summary['next_gate']}
```

## Next Step

{next_step}
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest-dir", type=Path, default=Path("."))
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for spec in MANIFESTS:
        path = args.manifest_dir / spec.default_path
        counts = count_tsv(path)
        if not counts["exists"]:
            gate_status = spec.status_if_missing
        elif counts["row_count"] >= spec.minimum_rows:
            gate_status = "local_manifest_present_minimum_rows_met"
        else:
            gate_status = "local_manifest_present_row_count_below_minimum"
        rows.append(
            {
                "manifest_id": spec.manifest_id,
                "gate": spec.gate,
                "default_local_path_class": "repo_root_local_only",
                "exists": str(counts["exists"]).lower(),
                "row_count": counts["row_count"],
                "field_count": counts["field_count"],
                "field_names_tracked": str(counts["field_names_tracked"]).lower(),
                "minimum_rows": spec.minimum_rows,
                "required_before": spec.required_before,
                "gate_status": gate_status,
            }
        )

    present = sum(1 for row in rows if row["exists"] == "true")
    one_row = next(row for row in rows if row["manifest_id"] == "one_row_smoke")
    missing_required_next = one_row["exists"] != "true" or int(one_row["row_count"]) < 1
    next_gate = (
        "create_or_attach_one_row_smoke_manifest_local_tsv"
        if missing_required_next
        else "run_real_one_row_transcript_only_smoke_adapters"
    )

    summary = {
        "run_id": RUN_ID,
        "generated_at_unix": int(time.time()),
        "gate": "Gate A local-only manifest preflight",
        "status": "missing_required_next_manifest" if missing_required_next else "ready_for_one_row_smoke",
        "manifest_specs": len(MANIFESTS),
        "manifest_files_present": present,
        "missing_required_next": missing_required_next,
        "tracked_manifest_field_names": False,
        "tracked_row_level_values": False,
        "privacy": {
            "raw_audio_tracked": False,
            "row_ids_tracked": False,
            "transcripts_tracked": False,
            "hypotheses_tracked": False,
            "reviewer_notes_tracked": False,
            "local_paths_tracked": False,
        },
        "next_gate": next_gate,
    }

    write_tsv(
        out_dir / "manifest_preflight_summary.tsv",
        rows,
        [
            "manifest_id",
            "gate",
            "default_local_path_class",
            "exists",
            "row_count",
            "field_count",
            "field_names_tracked",
            "minimum_rows",
            "required_before",
            "gate_status",
        ],
    )
    (out_dir / "manifest_preflight_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_readme(out_dir, summary)
    print(f"wrote {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

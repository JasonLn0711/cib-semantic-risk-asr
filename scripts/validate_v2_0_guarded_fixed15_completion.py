#!/usr/bin/env python3
"""Validate guarded fixed-15 completion and final no-winner audit."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


RUNS = {
    "step": Path("70_experiments/runs/v2_0_multimodal_step_audio_guarded_fixed_15_2026_06_01"),
    "moss4": Path("70_experiments/runs/v2_0_multimodal_moss4_guarded_fixed_15_2026_06_01"),
    "minicpm": Path("70_experiments/runs/v2_0_multimodal_minicpm_guarded_fixed_15_2026_06_01"),
}
STEP_PROXY = Path("70_experiments/runs/v2_0_multimodal_step_audio_guarded_auto_semantic_proxy_2026_06_01")
FINAL = Path("70_experiments/runs/v2_0_multimodal_no_human_final_completion_audit_2026_06_01")

PROHIBITED_HEADERS = {
    "audio_path",
    "local_audio_path",
    "reference_text",
    "hypothesis",
    "hypothesis_text",
    "model_output",
    "repaired_text",
    "reviewer_note",
    "expert_note",
    "local_path",
    "cache_path",
    "adapter_path",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def check_tsv(path: Path) -> None:
    rows = path.read_text(encoding="utf-8").splitlines()
    if not rows:
        fail(f"empty TSV: {path}")
    widths = {len(row.split("\t")) for row in rows if row}
    if len(widths) != 1:
        fail(f"ragged TSV: {path}")
    header = set(rows[0].split("\t"))
    overlap = header.intersection(PROHIBITED_HEADERS)
    if overlap:
        fail(f"sensitive headers in {path}: {sorted(overlap)}")


def main() -> None:
    for name, directory in RUNS.items():
        if not directory.exists():
            fail(f"missing guarded fixed-15 run: {name}")
        summary = json.loads((directory / "gate_summary.json").read_text(encoding="utf-8"))
        if summary["rows"] != 15:
            fail(f"{name} did not record 15 rows")
        if summary["guard_no_speech_rows"] + summary["pass_to_model_rows"] != 15:
            fail(f"{name} guard counts do not sum to 15")
        if summary["privacy"]["raw_audio_tracked"] is not False:
            fail(f"{name} privacy boundary broken")
        for path in directory.glob("*.tsv"):
            check_tsv(path)

    step_summary = json.loads((RUNS["step"] / "gate_summary.json").read_text(encoding="utf-8"))
    if step_summary["promotion_decision"] != "promote_to_semantic_damage_proxy":
        fail("Step must be the only fixed-15 proxy candidate")
    proxy_summary = json.loads((STEP_PROXY / "auto_semantic_proxy_summary.json").read_text(encoding="utf-8"))
    if proxy_summary["decision"] != "guarded_route_no_winner_stop":
        fail("Step proxy must stop the guarded Step route")
    if proxy_summary["semantic_damage_blocker_rows"] <= 0:
        fail("Step proxy blocker rows must be positive")

    for name in ["moss4", "minicpm"]:
        summary = json.loads((RUNS[name] / "gate_summary.json").read_text(encoding="utf-8"))
        if summary["promotion_decision"] != "do_not_promote":
            fail(f"{name} should not promote past fixed-15")

    if not FINAL.exists():
        fail("missing final no-human audit")
    final_summary = json.loads((FINAL / "final_completion_summary.json").read_text(encoding="utf-8"))
    if final_summary["status"] != "final_no_human_no_winner":
        fail("final summary must close as final_no_human_no_winner")
    if final_summary["guarded_route_survivors_after_proxy"] != 0:
        fail("final summary must record zero guarded route survivors after proxy")
    if final_summary["larger_gates_open"] is not False:
        fail("larger gates must remain closed")
    for path in FINAL.glob("*.tsv"):
        check_tsv(path)

    print("OK: guarded fixed-15 completion and final no-winner audit are valid")


if __name__ == "__main__":
    main()

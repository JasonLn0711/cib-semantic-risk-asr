#!/usr/bin/env python3
"""Validate the v2.0 multimodal fine-tuning readiness design."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


RUN_DIR = Path("70_experiments/runs/v2_0_multimodal_finetuning_readiness_design_2026_06_01")
REQUIRED_FILES = {
    "README.md",
    "finetuning_readiness_summary.json",
    "candidate_readiness.tsv",
    "lora_feasibility_gate.tsv",
    "codex_goal_prompt.md",
}


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", nargs="?", type=Path, default=RUN_DIR)
    args = parser.parse_args()
    missing = sorted(name for name in REQUIRED_FILES if not (args.run_dir / name).exists())
    if missing:
        raise SystemExit(f"missing_required_files:{','.join(missing)}")

    summary = json.loads((args.run_dir / "finetuning_readiness_summary.json").read_text(encoding="utf-8"))
    if summary.get("status") != "readiness_design_recorded_do_not_train_yet":
        raise SystemExit("unexpected_status")
    if summary.get("fine_tuning_now") is not False:
        raise SystemExit("fine_tuning_now_must_be_false")
    if any(summary.get("privacy", {}).values()):
        raise SystemExit("privacy_boundary_failed")

    candidates = read_tsv(args.run_dir / "candidate_readiness.tsv")
    if len(candidates) != 6:
        raise SystemExit("candidate_readiness_must_have_6_rows")
    gates = read_tsv(args.run_dir / "lora_feasibility_gate.tsv")
    if len(gates) != 8:
        raise SystemExit("lora_feasibility_gate_must_have_8_rows")
    if [int(row["gate_order"]) for row in gates] != list(range(1, 9)):
        raise SystemExit("gate_order_must_be_1_to_8")

    prompt = (args.run_dir / "codex_goal_prompt.md").read_text(encoding="utf-8")
    for phrase in [
        "Do not fine-tune immediately",
        "Raw audio is never tracked in Git",
        "Step-Audio-2-mini",
        "sentinel reaches 6/6",
    ]:
        if phrase not in prompt:
            raise SystemExit(f"missing_prompt_phrase:{phrase}")
    print(f"multimodal_finetuning_readiness_design_ok {args.run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate the Qwen3-ASR / FireRedASR LoRA planning record."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


RUN_DIR = Path(
    "70_experiments/runs/"
    "v2_0_asr_controls_qwen3_firered_lora_plan_2026_06_01"
)

REQUIRED_FILES = [
    "README.md",
    "baseline_experiment_matrix.tsv",
    "model_gate_plan.tsv",
    "lora_grid.tsv",
    "full_completion_steps.tsv",
    "no_human_evaluation_contract.tsv",
    "qwen3_firered_lora_plan_summary.json",
    "codex_goal_prompt.md",
]

PROHIBITED_PATTERNS = [
    "\taudio_path\t",
    "\tlocal_audio_path\t",
    "\treference_text\t",
    "\thypothesis\t",
    "\tmodel_output\t",
    "\trepaired_text\t",
    "\treviewer_note\t",
    "\texpert_note\t",
    "\tlocal_path\t",
    "\tcache_path\t",
    "\tadapter_path\t",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def main() -> None:
    if not RUN_DIR.exists():
        fail(f"missing run dir: {RUN_DIR}")

    for filename in REQUIRED_FILES:
        path = RUN_DIR / filename
        if not path.exists():
            fail(f"missing required file: {path}")

    combined = "\n".join((RUN_DIR / filename).read_text(encoding="utf-8") for filename in REQUIRED_FILES)
    padded = "\n" + combined.lower().replace("\n", "\t\n\t") + "\n"
    for pattern in PROHIBITED_PATTERNS:
        if pattern in padded:
            fail(f"prohibited pattern found: {pattern}")

    model_rows = read_tsv(RUN_DIR / "model_gate_plan.tsv")
    baseline_rows = read_tsv(RUN_DIR / "baseline_experiment_matrix.tsv")
    lora_rows = read_tsv(RUN_DIR / "lora_grid.tsv")
    steps = read_tsv(RUN_DIR / "full_completion_steps.tsv")
    contract_rows = read_tsv(RUN_DIR / "no_human_evaluation_contract.tsv")

    if len(model_rows) < 6:
        fail("expected at least 6 model gate rows")
    if len(baseline_rows) != 12:
        fail(f"expected 12 baseline matrix rows, found {len(baseline_rows)}")
    if len(lora_rows) != 12:
        fail(f"expected 12 LoRA grid rows, found {len(lora_rows)}")
    if len(steps) != 18:
        fail(f"expected 18 completion phases, found {len(steps)}")
    if len(contract_rows) < 8:
        fail("expected at least 8 no-human contract rows")

    phase_ids = [int(row["phase_id"]) for row in steps]
    if phase_ids != list(range(18)):
        fail(f"phase ids are not contiguous 0..17: {phase_ids}")
    if steps[8]["phase_name"] != "baseline_matrix_record":
        fail("phase 8 must be baseline_matrix_record")
    if steps[10]["phase_name"] != "lora_intervention_rationale_decision":
        fail("phase 10 must be lora_intervention_rationale_decision")

    grid_ids = {row["grid_id"] for row in lora_rows}
    required_grid_ids = {
        "qwen3_0_6b_r4_a8",
        "qwen3_0_6b_r8_a16",
        "qwen3_0_6b_r16_a32",
        "qwen3_1_7b_r4_a8",
        "firered_aed_r4_a8",
        "firered_llm_r4_a8",
    }
    missing = sorted(required_grid_ids - grid_ids)
    if missing:
        fail(f"missing required LoRA grid ids: {missing}")

    summary = json.loads((RUN_DIR / "qwen3_firered_lora_plan_summary.json").read_text(encoding="utf-8"))
    if summary.get("human_review_policy") != "no_additional_human_review":
        fail("human review policy mismatch")
    if summary.get("next_phase_id") != 1:
        fail("next phase must be metadata refresh")
    if summary.get("lora_rank_alpha_grid_count") != len(lora_rows):
        fail("LoRA grid count mismatch")
    if summary.get("baseline_experiment_matrix_count") != len(baseline_rows):
        fail("baseline experiment matrix count mismatch")
    if summary.get("lora_intervention_rationale_required") is not True:
        fail("lora_intervention_rationale_required must be true")
    if summary.get("research_probe_lora_allowed") is not True:
        fail("research_probe_lora_allowed must be true")

    privacy = summary.get("privacy_boundary", {})
    if privacy.get("repo_safe_aggregate_records_tracked") is not True:
        fail("repo_safe_aggregate_records_tracked must be true")
    forbidden_true = [
        key
        for key, value in privacy.items()
        if key != "repo_safe_aggregate_records_tracked" and value is not False
    ]
    if forbidden_true:
        fail(f"privacy boundary has forbidden true values: {forbidden_true}")

    print("OK: Qwen3-ASR / FireRedASR LoRA plan is valid")


if __name__ == "__main__":
    main()

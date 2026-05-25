#!/usr/bin/env python3
"""Run the JANUS 15-row NeMo Curator ASR pilot.

The local NeMo Curator 1.2.0 JsonlReader path batches manifest rows as a
pandas Series for `audio_filepath`, which NeMo ASR does not accept. This runner
keeps the same Curator ASR stage but feeds it explicit `AudioTask` rows so the
stage receives a list of audio-path strings.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import date
from pathlib import Path
from typing import Any


REQUIRED_GOLD_FIELDS = (
    "human_verified_transcript",
    "semantic_risk_label",
    "risk_atoms",
    "asr_confusion_terms",
    "would_asr_error_change_decision",
)

DEFAULT_MODEL = "nvidia/stt_zh_citrinet_1024_gamma_0_25"
DEFAULT_ASR_RUN_ID = "nemo_curator_zh_citrinet_pilot"


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def read_gold_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def validate_gate(
    manifest_rows: list[dict[str, Any]],
    gold_rows: list[dict[str, str]],
    expected_rows: int,
) -> dict[str, Any]:
    manifest_ids = [str(row.get("audio_id", "")).strip() for row in manifest_rows]
    gold_ids = [row.get("audio_id", "").strip() for row in gold_rows]
    missing_gold = {
        field: [
            row.get("audio_id", "")
            for row in gold_rows
            if not (row.get(field) or "").strip()
        ]
        for field in REQUIRED_GOLD_FIELDS
    }
    missing_paths = [
        str(row.get("audio_filepath", ""))
        for row in manifest_rows
        if not Path(str(row.get("audio_filepath", ""))).exists()
    ]
    checks = {
        "manifest_row_count": len(manifest_rows) == expected_rows,
        "gold_row_count": len(gold_rows) == expected_rows,
        "audio_ids_are_unique": len(set(manifest_ids)) == len(manifest_ids),
        "manifest_audio_ids_match_gold": set(manifest_ids) == set(gold_ids),
        "gold_required_fields_complete": not any(missing_gold.values()),
        "audio_paths_exist": not missing_paths,
    }
    return {
        "ok": all(checks.values()),
        "checks": checks,
        "missing_gold_required_fields": missing_gold,
        "missing_audio_paths": missing_paths,
        "manifest_missing_audio_ids": sorted(set(gold_ids) - set(manifest_ids)),
        "manifest_extra_audio_ids": sorted(set(manifest_ids) - set(gold_ids)),
    }


def import_curator_runtime() -> dict[str, Any]:
    try:
        from nemo_curator.stages.audio.inference.asr_nemo import InferenceAsrNemoStage
        from nemo_curator.stages.audio.metrics.get_wer import GetPairwiseWerStage, get_cer
        from nemo_curator.stages.resources import Resources
        from nemo_curator.tasks import AudioTask
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "NeMo Curator runtime is not installed. Install a local ignored env, "
            'for example: uv pip install "nemo-curator[audio_cuda12]".'
        ) from exc
    return {
        "AudioTask": AudioTask,
        "GetPairwiseWerStage": GetPairwiseWerStage,
        "InferenceAsrNemoStage": InferenceAsrNemoStage,
        "Resources": Resources,
        "get_cer": get_cer,
    }


def maybe_quiet_nemo_logs(quiet: bool) -> None:
    if not quiet:
        return
    os.environ.setdefault("NEMO_LOG_LEVEL", "ERROR")
    try:
        from nemo.utils import logging as nemo_logging

        nemo_logging.setLevel("ERROR")
    except Exception:
        pass


def output_text(value: object) -> str:
    if value is None:
        return ""
    if hasattr(value, "text"):
        return str(value.text)
    return str(value)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    root = repo_root_from_script()
    manifests_dir = root / "40_breeze_asr25_finetune_dataset" / "manifests"
    reports_dir = root / "40_breeze_asr25_finetune_dataset" / "reports"
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=manifests_dir / "nemo_pilot_input_manifest.jsonl")
    parser.add_argument("--gold-review", type=Path, default=reports_dir / "gold_subset_review.tsv")
    parser.add_argument("--output", type=Path, default=manifests_dir / "asr_outputs_nemo.jsonl")
    parser.add_argument("--summary", type=Path, default=manifests_dir / "asr_outputs_nemo_summary.json")
    parser.add_argument("--model-name", default=DEFAULT_MODEL)
    parser.add_argument("--asr-run-id", default=DEFAULT_ASR_RUN_ID)
    parser.add_argument("--runtime", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--expected-rows", type=int, default=15)
    parser.add_argument("--skip-gate-check", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    manifest_rows = read_jsonl(args.manifest)
    gold_rows = read_gold_rows(args.gold_review)
    gate = validate_gate(manifest_rows, gold_rows, args.expected_rows)
    if not args.skip_gate_check and not gate["ok"]:
        print(
            json.dumps(
                {
                    "ok": False,
                    "reason": "JANUS pilot gate is not ready for NeMo Curator",
                    "gate": gate,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    maybe_quiet_nemo_logs(args.quiet)
    runtime = import_curator_runtime()
    AudioTask = runtime["AudioTask"]
    GetPairwiseWerStage = runtime["GetPairwiseWerStage"]
    InferenceAsrNemoStage = runtime["InferenceAsrNemoStage"]
    Resources = runtime["Resources"]
    get_cer = runtime["get_cer"]

    tasks = [
        AudioTask(
            task_id=str(row["audio_id"]),
            dataset_name="janus_15_nemo_curator_pilot",
            filepath_key="audio_filepath",
            data=dict(row),
        )
        for row in manifest_rows
    ]
    gpus = 1.0 if args.runtime == "cuda" else 0.0
    stage = InferenceAsrNemoStage(
        model_name=args.model_name,
        filepath_key="audio_filepath",
        pred_text_key="pred_text",
    ).with_(resources=Resources(gpus=gpus, cpus=8.0), batch_size=args.batch_size)
    stage.setup_on_node()
    stage.setup()
    wer_stage = GetPairwiseWerStage(text_key="text", pred_text_key="pred_text", wer_key="wer")

    processed: list[dict[str, Any]] = []
    for start in range(0, len(tasks), args.batch_size):
        batch = tasks[start : start + args.batch_size]
        for task in stage.process_batch(batch):
            task = wer_stage.process(task)
            row = dict(task.data)
            row["pred_text"] = output_text(row.get("pred_text"))
            row["hypothesis_text"] = row["pred_text"]
            row["cer"] = get_cer(row["text"], row["pred_text"])
            row["model"] = args.model_name
            row["asr_run_id"] = args.asr_run_id
            row["runtime"] = args.runtime
            row["run_date"] = date.today().isoformat()
            processed.append(row)
            print(
                json.dumps(
                    {
                        "audio_id": row["audio_id"],
                        "pred_len": len(row["pred_text"]),
                        "wer": row["wer"],
                        "cer": row["cer"],
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )

    field_order = [
        "audio_id",
        "audio_filepath",
        "split",
        "duration",
        "language",
        "speaker_id",
        "source_audio_relative",
        "text",
        "pred_text",
        "hypothesis_text",
        "wer",
        "cer",
        "model",
        "asr_run_id",
        "runtime",
        "run_date",
        "risk_keyword_hits",
    ]
    output_rows = [{key: row.get(key, "") for key in field_order} for row in processed]
    write_jsonl(args.output, output_rows)

    output_ids = {str(row.get("audio_id", "")) for row in output_rows}
    manifest_ids = {str(row.get("audio_id", "")) for row in manifest_rows}
    summary = {
        "ok": len(output_rows) == args.expected_rows and output_ids == manifest_ids,
        "manifest": str(args.manifest),
        "gold_review": str(args.gold_review),
        "output": str(args.output),
        "rows": len(output_rows),
        "model": args.model_name,
        "asr_run_id": args.asr_run_id,
        "runtime": args.runtime,
        "gate": gate,
        "audio_ids": [row["audio_id"] for row in output_rows],
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

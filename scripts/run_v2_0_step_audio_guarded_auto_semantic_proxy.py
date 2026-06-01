#!/usr/bin/env python3
"""Run deterministic semantic-damage proxy for Step guarded fixed-15 outputs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

from run_v2_0_qwen_auto_semantic_damage_proxy import (
    ABBREVIATION_RE,
    CRITICAL_CANONICAL_TERMS,
    abbreviation_counter,
    monitored_term_counter,
    overlap_ratio,
)
from run_v2_0_qwen_omni_fixed_15_row_transcript_gate import (
    SIMPLIFIED_MARKERS,
    edit_counts,
    normalize_zh_asr,
)


RUN_ID = "v2_0_multimodal_step_audio_guarded_auto_semantic_proxy_2026_06_01"
STOP_RUN_ID = "v2_0_multimodal_guarded_route_no_winner_stop_2026_06_01"
MODEL_ID = "stepfun-ai/Step-Audio-2-mini"
SOURCE_RUN_ID = "v2_0_multimodal_step_audio_guarded_fixed_15_2026_06_01"
DEFAULT_INPUT = (
    Path("70_experiments/runtime_lanes/step_audio_2_mini/local_outputs")
    / SOURCE_RUN_ID
    / "step_audio_guarded_fixed_15_outputs.local.jsonl"
)
DEFAULT_OUT_DIR = Path("70_experiments/runs") / RUN_ID
DEFAULT_STOP_DIR = Path("70_experiments/runs") / STOP_RUN_ID
TOKENIZER_POLICY = "cjk_char_tokenizer_fallback_no_jieba_in_auto_proxy_lane"


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_path(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def count_simplified(text: str) -> tuple[int, int, float]:
    simplified = sum(1 for char in text if char in SIMPLIFIED_MARKERS)
    cjk = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
    return simplified, cjk, round(simplified / cjk * 100.0, 4) if cjk else 0.0


def suspicious_length_ratio(reference: str, hypothesis: str) -> bool:
    ref_len = len(normalize_zh_asr(reference))
    hyp_len = len(normalize_zh_asr(hypothesis))
    if ref_len == 0:
        return hyp_len != 0
    ratio = hyp_len / ref_len
    return ratio < 0.6 or ratio > 1.6 or abs(hyp_len - ref_len) > 60


def hallucination_proxy(reference: str, hypothesis: str) -> bool:
    ref_len = len(normalize_zh_asr(reference))
    hyp_len = len(normalize_zh_asr(hypothesis))
    return hyp_len > ref_len * 1.5 + 20 and overlap_ratio(reference, hypothesis) < 0.55


def row_checks(row: dict[str, Any]) -> dict[str, int]:
    reference = row["reference_text"]
    hypothesis = row["hypothesis"]
    _ce, _cd, cer = edit_counts(reference, hypothesis, unit="char")
    _we, _wd, wer = edit_counts(reference, hypothesis, unit="word")
    simplified, _cjk, _rate = count_simplified(hypothesis)
    overlap = overlap_ratio(reference, hypothesis)
    reference_terms = monitored_term_counter(reference)
    hypothesis_terms = monitored_term_counter(hypothesis)
    reference_abbr = abbreviation_counter(reference)
    hypothesis_abbr = abbreviation_counter(hypothesis)
    return {
        "cer_worsening_or_high_error_rows": int(cer > 50.0),
        "wer_worsening_or_high_error_rows": int(wer > 50.0),
        "new_hallucination_proxy_rows": int(hallucination_proxy(reference, hypothesis)),
        "critical_term_or_proper_noun_change_rows": int(reference_terms != hypothesis_terms),
        "abbreviation_change_rows": int(reference_abbr != hypothesis_abbr),
        "suspicious_length_ratio_rows": int(suspicious_length_ratio(reference, hypothesis)),
        "empty_output_change_rows": int(bool(normalize_zh_asr(reference)) and not normalize_zh_asr(hypothesis)),
        "locale_residual_rows": int(simplified > 0),
        "payload_pairing_blocker_rows": int("reference_text" not in row or "hypothesis" not in row),
        "low_overlap_rows": int(overlap < 0.55),
    }


def privacy_record() -> dict[str, bool]:
    return {
        "raw_audio_tracked": False,
        "row_ids_tracked": False,
        "transcripts_tracked": False,
        "references_tracked": False,
        "hypotheses_tracked": False,
        "repaired_text_tracked": False,
        "reviewer_notes_tracked": False,
        "local_paths_tracked": False,
        "transcript_bearing_runtime_logs_tracked": False,
        "adapter_weights_tracked": False,
        "model_cache_paths_tracked": False,
    }


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""# Step-Audio Guarded Automatic Semantic-Damage Proxy

Date: 2026-06-01

Status: {summary['status']}

This deterministic proxy evaluates the local-only Step-Audio guarded fixed-15
payload and writes aggregate blocker counts only. It implements the no-human
route after fixed-15. Transcript-bearing references and hypotheses remain in
the ignored runtime lane.

## Result

```text
rows={summary['rows']}
semantic_damage_blocker_rows={summary['semantic_damage_blocker_rows']}
decision={summary['decision']}
next_gate={summary['next_gate']}
```
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def write_stop_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""# Guarded Route No-Winner Stop

Date: 2026-06-01

Status: {summary['status']}

This partial stop record closes the Step-Audio guarded route after deterministic
semantic-damage proxy blockers. It is not the final all-model closeout because
MOSS-Audio-4B-Instruct and MiniCPM-o 4.5 still remain in the guarded fixed-15
candidate pool.

## Result

```text
blocked_model_id={summary['blocked_model_id']}
semantic_damage_blocker_rows={summary['semantic_damage_blocker_rows']}
final_closeout_ready={summary['final_closeout_ready']}
```
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--stop-dir", type=Path, default=DEFAULT_STOP_DIR)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows = read_jsonl(args.input)
    if len(rows) != 15:
        raise SystemExit("step_guarded_auto_proxy_requires_15_rows")

    check_names = [
        "cer_worsening_or_high_error_rows",
        "wer_worsening_or_high_error_rows",
        "new_hallucination_proxy_rows",
        "critical_term_or_proper_noun_change_rows",
        "abbreviation_change_rows",
        "suspicious_length_ratio_rows",
        "empty_output_change_rows",
        "locale_residual_rows",
        "payload_pairing_blocker_rows",
        "low_overlap_rows",
    ]
    checks = Counter()
    char_edits = char_den = word_edits = word_den = 0
    simplified_chars = cjk_chars = 0
    for row in rows:
        reference = row["reference_text"]
        hypothesis = row["hypothesis"]
        ce, cd, _cer = edit_counts(reference, hypothesis, unit="char")
        we, wd, _wer = edit_counts(reference, hypothesis, unit="word")
        char_edits += ce
        char_den += cd
        word_edits += we
        word_den += wd
        simplified, cjk, _rate = count_simplified(hypothesis)
        simplified_chars += simplified
        cjk_chars += cjk
        checks.update(row_checks(row))

    blocker_rows = sum(checks[name] for name in check_names)
    decision = "guarded_auto_proxy_clean" if blocker_rows == 0 else "guarded_route_no_winner_stop"
    next_gate = "guarded_taiwan_utility_proxy" if blocker_rows == 0 else "do_not_promote_guarded_step"
    proxy_row = {
        "model_family": "Step-Audio 2 mini",
        "model_id": MODEL_ID,
        "source_run_id": SOURCE_RUN_ID,
        "rows": len(rows),
        **{name: checks[name] for name in check_names},
        "semantic_damage_blocker_rows": blocker_rows,
        "decision": decision,
        "claim_boundary": "deterministic_deployment_repair_automatic_proxy",
    }
    metric_row = {
        "model_family": "Step-Audio 2 mini",
        "model_id": MODEL_ID,
        "rows": len(rows),
        "cer_zh_micro": round(char_edits / max(1, char_den) * 100.0, 4),
        "wer_zh_jieba_micro": round(word_edits / max(1, word_den) * 100.0, 4),
        "simplified_char_rate": round(simplified_chars / max(1, cjk_chars) * 100.0, 4),
        "tokenizer_policy": TOKENIZER_POLICY,
        "decision": decision,
    }
    manifest_row = {
        "artifact_class": "local_transcript_bearing_step_guarded_fixed_15_payload",
        "artifact_count": len(rows),
        "content_sensitivity": "contains_references_and_model_outputs",
        "storage_policy": "ignored_local_runtime_lane",
        "sha256": sha256_path(args.input),
        "hash_or_manifest_status": "input_payload_hash_recorded_without_path",
        "gate_status": decision,
    }
    summary = {
        "run_id": RUN_ID,
        "generated_at_unix": int(time.time()),
        "status": "step_audio_guarded_auto_semantic_proxy_complete",
        "model_id": MODEL_ID,
        "source_run_id": SOURCE_RUN_ID,
        "rows": len(rows),
        "semantic_damage_blocker_rows": blocker_rows,
        "decision": decision,
        "next_gate": next_gate,
        "claim_boundary": "deterministic_deployment_repair_automatic_proxy",
        "privacy": privacy_record(),
    }

    write_tsv(args.out_dir / "proxy_blocker_summary.tsv", [proxy_row], list(proxy_row))
    write_tsv(args.out_dir / "proxy_metric_summary.tsv", [metric_row], list(metric_row))
    write_tsv(args.out_dir / "controlled_artifact_manifest.tsv", [manifest_row], list(manifest_row))
    (args.out_dir / "auto_semantic_proxy_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_readme(args.out_dir, summary)

    if blocker_rows:
        args.stop_dir.mkdir(parents=True, exist_ok=True)
        stop_summary = {
            "run_id": STOP_RUN_ID,
            "generated_at_unix": int(time.time()),
            "status": "guarded_route_no_winner_stop_partial",
            "blocked_model_id": MODEL_ID,
            "blocked_source_run_id": RUN_ID,
            "reason": "step_guarded_fixed_15_semantic_proxy_blockers_nonzero",
            "semantic_damage_blocker_rows": blocker_rows,
            "remaining_guarded_candidates": ["MOSS-Audio-4B-Instruct", "MiniCPM-o 4.5"],
            "final_closeout_ready": False,
            "privacy": privacy_record(),
        }
        (args.stop_dir / "partial_stop_summary.json").write_text(
            json.dumps(stop_summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        write_stop_readme(args.stop_dir, stop_summary)

    print(f"step_audio_guarded_auto_semantic_proxy_written {args.out_dir}")
    return 0 if blocker_rows == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())

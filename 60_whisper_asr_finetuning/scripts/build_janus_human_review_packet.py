#!/usr/bin/env python3
"""Build a local JANUS human-review packet with guide, audio, and manifest."""

from __future__ import annotations

import argparse
import csv
import json
import shlex
import shutil
from datetime import date
from pathlib import Path


GOLD_REQUIRED_FIELDS = (
    "human_verified_transcript",
    "semantic_risk_label",
    "risk_atoms",
    "asr_confusion_terms",
    "would_asr_error_change_decision",
)

LONG_SILENCE_REQUIRED_FIELDS = (
    "review_status",
    "reviewer",
    "review_date",
)

GOLD_REVIEW_FIELDS = GOLD_REQUIRED_FIELDS + (
    "reviewer",
    "review_date",
    "review_notes",
)

LONG_SILENCE_REVIEW_FIELDS = LONG_SILENCE_REQUIRED_FIELDS + (
    "review_notes",
)

WORKBOOK_FIELDS = (
    "review_set",
    "index",
    "audio_id",
    "split",
    "packet_audio_path",
    "source_repo_path",
    "candidate_reference_transcript",
    "risk_keyword_hits",
    "human_verified_transcript",
    "semantic_risk_label",
    "risk_atoms",
    "asr_confusion_terms",
    "would_asr_error_change_decision",
    "review_status",
    "reviewer",
    "review_date",
    "review_notes",
)


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_tsv_with_fields(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader), list(reader.fieldnames or [])


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def code_block(text: str) -> str:
    return f"```text\n{(text or '').strip()}\n```"


def playback_command(root: Path, path_value: str) -> str:
    return "ffplay -nodisp -autoexit " + shlex.quote(str(root / path_value))


def missing_fields(row: dict[str, str], fields: tuple[str, ...]) -> list[str]:
    return [field for field in fields if not (row.get(field) or "").strip()]


def packet_audio_path(review_set: str, index: int, audio_id: str, source_path: Path) -> Path:
    return Path("audio") / review_set / f"{index:02d}_{audio_id}{source_path.suffix}"


def copy_audio(
    root: Path,
    packet_dir: Path,
    review_set: str,
    rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    copied: list[dict[str, str]] = []
    for index, row in enumerate(rows, start=1):
        source_rel = Path(row["path"])
        source_abs = root / source_rel
        if not source_abs.exists():
            raise FileNotFoundError(source_abs)
        target_rel = packet_audio_path(review_set, index, row["audio_id"], source_abs)
        target_abs = packet_dir / target_rel
        target_abs.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_abs, target_abs)
        copied.append(
            {
                "review_set": review_set,
                "index": str(index),
                "audio_id": row["audio_id"],
                "split": row.get("split", ""),
                "source_repo_path": source_rel.as_posix(),
                "packet_audio_path": target_rel.as_posix(),
            }
        )
    return copied


def write_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "review_set",
        "index",
        "audio_id",
        "split",
        "source_repo_path",
        "packet_audio_path",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def write_tsv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def build_workbook_rows(
    gold_rows: list[dict[str, str]],
    silence_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    workbook_rows: list[dict[str, str]] = []
    for review_set, rows in (("gold", gold_rows), ("long_silence", silence_rows)):
        for index, row in enumerate(rows, start=1):
            packet_path = packet_audio_path(
                review_set,
                index,
                row["audio_id"],
                Path(row["path"]),
            )
            workbook_rows.append(
                {
                    "review_set": review_set,
                    "index": str(index),
                    "audio_id": row.get("audio_id", ""),
                    "split": row.get("split", ""),
                    "packet_audio_path": packet_path.as_posix(),
                    "source_repo_path": row.get("path", ""),
                    "candidate_reference_transcript": row.get(
                        "candidate_reference_transcript",
                        "",
                    ),
                    "risk_keyword_hits": row.get("risk_keyword_hits", ""),
                    "human_verified_transcript": row.get(
                        "human_verified_transcript",
                        "",
                    ),
                    "semantic_risk_label": row.get("semantic_risk_label", ""),
                    "risk_atoms": row.get("risk_atoms", ""),
                    "asr_confusion_terms": row.get("asr_confusion_terms", ""),
                    "would_asr_error_change_decision": row.get(
                        "would_asr_error_change_decision",
                        "",
                    ),
                    "review_status": row.get("review_status", ""),
                    "reviewer": row.get("reviewer", ""),
                    "review_date": row.get("review_date", ""),
                    "review_notes": row.get("review_notes", ""),
                }
            )
    return workbook_rows


def write_workbook(path: Path, rows: list[dict[str, str]]) -> None:
    write_tsv(path, rows, list(WORKBOOK_FIELDS))


def import_review_rows(
    review_path: Path,
    workbook_rows: list[dict[str, str]],
    review_set: str,
    review_fields: tuple[str, ...],
    dry_run: bool,
) -> dict[str, object]:
    review_rows, fieldnames = read_tsv_with_fields(review_path)
    rows_by_id = {
        row.get("audio_id", ""): row
        for row in review_rows
        if row.get("audio_id")
    }
    workbook_by_id = {
        row.get("audio_id", ""): row
        for row in workbook_rows
        if row.get("review_set") == review_set and row.get("audio_id")
    }
    missing_from_review = sorted(set(workbook_by_id) - set(rows_by_id))
    updated_cells = 0
    updated_rows: set[str] = set()

    for audio_id, workbook_row in workbook_by_id.items():
        target = rows_by_id.get(audio_id)
        if target is None:
            continue
        for field in review_fields:
            value = (workbook_row.get(field) or "").strip()
            if value and target.get(field, "") != value:
                target[field] = value
                updated_cells += 1
                updated_rows.add(audio_id)

    if not dry_run:
        write_tsv(review_path, review_rows, fieldnames)

    return {
        "review_set": review_set,
        "review_path": str(review_path),
        "workbook_rows": len(workbook_by_id),
        "updated_rows": len(updated_rows),
        "updated_cells": updated_cells,
        "missing_from_review": missing_from_review,
        "dry_run": dry_run,
    }


def import_workbook(
    workbook_path: Path,
    gold_review_path: Path,
    long_silence_review_path: Path,
    dry_run: bool,
) -> dict[str, object]:
    workbook_rows = read_tsv(workbook_path)
    result = {
        "workbook": str(workbook_path),
        "gold": import_review_rows(
            gold_review_path,
            workbook_rows,
            "gold",
            GOLD_REVIEW_FIELDS,
            dry_run,
        ),
        "long_silence": import_review_rows(
            long_silence_review_path,
            workbook_rows,
            "long_silence",
            LONG_SILENCE_REVIEW_FIELDS,
            dry_run,
        ),
    }
    return result


def build_gold_section(root: Path, rows: list[dict[str, str]]) -> list[str]:
    lines = ["## Gold Review Checklist", ""]
    for index, row in enumerate(rows, start=1):
        missing = missing_fields(row, GOLD_REQUIRED_FIELDS)
        lines.extend(
            [
                f"### Gold {index}. `{row.get('audio_id', '')}`",
                "",
                f"- Split: `{row.get('split', '')}`",
                f"- Duration seconds: `{row.get('duration_sec', '')}`",
                f"- Alignment score: `{row.get('alignment_score', '')}`",
                f"- Risk keyword hits: `{row.get('risk_keyword_hits', '') or 'none'}`",
                f"- Source audio relative: `{row.get('source_audio_relative', '')}`",
                f"- Local audio path: `{row.get('path', '')}`",
                "- Current required-field status: "
                f"`{', '.join(missing) if missing else 'complete'}`",
                "",
                "Play command:",
                "",
                "```bash",
                playback_command(root, row.get("path", "")),
                "```",
                "",
                "Candidate reference transcript:",
                "",
                code_block(row.get("candidate_reference_transcript", "")),
                "",
                "Fill these values:",
                "",
                "- `human_verified_transcript`: ",
                "- `semantic_risk_label`: ",
                "- `risk_atoms`: ",
                "- `asr_confusion_terms`: ",
                "- `would_asr_error_change_decision`: ",
                "- `reviewer`: ",
                "- `review_date`: ",
                "- `review_notes`: ",
                "",
            ]
        )
    return lines


def build_long_silence_section(root: Path, rows: list[dict[str, str]]) -> list[str]:
    lines = [
        "## How To Review Long-Silence Rows",
        "",
        "For each long-silence row, the task is bounded. Do not turn this into "
        "a full dataset review. Listen only to decide whether the silence is an "
        "acceptable telephone pause/contextual silence or a segmentation or "
        "pilot-quality issue.",
        "",
        "## Long-Silence Checklist",
        "",
    ]
    for index, row in enumerate(rows, start=1):
        missing = missing_fields(row, LONG_SILENCE_REQUIRED_FIELDS)
        lines.extend(
            [
                f"### Long-Silence {index}. `{row.get('audio_id', '')}`",
                "",
                f"- Split: `{row.get('split', '')}`",
                f"- Duration seconds: `{row.get('duration_sec', '')}`",
                f"- Max silence seconds: `{row.get('max_silence_sec', '')}`",
                f"- RMS ratio: `{row.get('rms_ratio', '')}`",
                f"- Peak ratio: `{row.get('peak_ratio', '')}`",
                f"- Risk keyword hits: `{row.get('risk_keyword_hits', '') or 'none'}`",
                f"- Local audio path: `{row.get('path', '')}`",
                "- Current required-field status: "
                f"`{', '.join(missing) if missing else 'complete'}`",
                "",
                "Play command:",
                "",
                "```bash",
                playback_command(root, row.get("path", "")),
                "```",
                "",
                "Candidate reference transcript:",
                "",
                code_block(row.get("candidate_reference_transcript", "")),
                "",
                "Fill these values:",
                "",
                "- `review_status`: ",
                "- `reviewer`: ",
                "- `review_date`: ",
                "- `review_notes`: ",
                "",
            ]
        )
    return lines


def build_guide(
    root: Path,
    gold_rows: list[dict[str, str]],
    silence_rows: list[dict[str, str]],
    generated_date: str,
) -> str:
    gold_missing_count = sum(
        1 for row in gold_rows if missing_fields(row, GOLD_REQUIRED_FIELDS)
    )
    silence_missing_count = sum(
        1 for row in silence_rows if missing_fields(row, LONG_SILENCE_REQUIRED_FIELDS)
    )

    lines = [
        "# JANUS 15-Row Human Review Guide",
        "",
        f"Generated: {generated_date}",
        "",
        "Source repo:",
        "",
        f"```text\n{root}\n```",
        "",
        "This file is a local execution guide for the required human review gate. "
        "It belongs in the local review packet and should not be committed to git "
        "because it includes candidate transcript text, local audio paths, and "
        "manual review context.",
        "",
        "## Current Review Scope",
        "",
        f"- Gold subset rows needing review: {gold_missing_count} / {len(gold_rows)}",
        "- Long-silence rows needing bounded review: "
        f"{silence_missing_count} / {len(silence_rows)}",
        "- Do not reopen all 4,967 JANUS rows at this stage.",
        "- Do not start full-dataset NeMo, Whisper, Breeze, or LoRA runs before "
        "this gate passes.",
        "",
        "## Why These Human Fields Are Required",
        "",
        "Audio health only proves the files are usable: file exists, WAV can be "
        "read, duration is plausible, sample rate/channel are consistent, and "
        "the only current health issue is six long-silence rows. That does not "
        "prove the transcript is correct, nor whether an ASR error changes a "
        "downstream scam-escalation decision.",
        "",
        "The CDS-ASR paper question is not whether ASR has a low WER. The question "
        "is whether plausible ASR alternatives around decision-critical spans "
        "change the downstream decision. The manual gold fields create the small "
        "auditable ground truth needed for SRES, CEIS, and downstream impact checks.",
        "",
        "## Fast Execution Commands",
        "",
        "From the repo root:",
        "",
        "```bash",
        f"cd {root}",
        "python3 60_whisper_asr_finetuning/scripts/build_janus_human_review_packet.py",
        "# Fill review_workbook.tsv in the generated Downloads packet, then import it:",
        "python3 60_whisper_asr_finetuning/scripts/build_janus_human_review_packet.py --import-workbook ~/Downloads/janus_15_human_review_packet_<date>/review_workbook.tsv",
        "python3 60_whisper_asr_finetuning/scripts/review_janus_pilot_gate.py --list-incomplete",
        "python3 60_whisper_asr_finetuning/scripts/review_janus_pilot_gate.py --mode gold --reviewer <your_name> --play",
        "python3 60_whisper_asr_finetuning/scripts/review_janus_pilot_gate.py --mode long-silence --reviewer <your_name> --play",
        "python3 60_whisper_asr_finetuning/scripts/validate_janus_pilot_gate.py",
        "```",
        "",
        "The validator should return `ok: true` before NeMo/Whisper/Breeze pilot "
        "metrics are treated as evidence.",
        "",
        "## Gold Review Fields And Exact Meaning",
        "",
        "| Field | Fill With | Why It Matters |",
        "| --- | --- | --- |",
        "| `human_verified_transcript` | What you hear after listening, corrected "
        "from the candidate transcript. | This becomes the reference text for "
        "WER/CER and risk-atom comparison. |",
        "| `semantic_risk_label` | One of `no_escalation`, `review`, "
        "`priority_review`, `critical_escalation`. | This is the human reference "
        "downstream scam-escalation decision. |",
        "| `risk_atoms` | Pipe-delimited subset of "
        "`negation|amount|action|actor|intent|time|uncertainty|scam_pattern`. | "
        "These are the decision-critical spans that SRES and CEIS score. |",
        "| `asr_confusion_terms` | Compact pairs or notes such as `匯款/未匯款`, "
        "`三萬/三十萬`, or `none_observed`. | These seed plausible ASR "
        "alternatives for counterfactual testing. |",
        "| `would_asr_error_change_decision` | `yes`, `no`, or `unclear`. | This is "
        "the small human benchmark for whether ASR error could flip or alter "
        "routing. |",
        "| `reviewer` | Your name or initials. | Useful audit trail; not required by "
        "the current gate but recommended. |",
        "| `review_date` | YYYY-MM-DD. | Useful audit trail; not required by the "
        "current gold gate but recommended. |",
        "| `review_notes` | Short note only when needed. | Use for uncertainty, noisy "
        "audio, ambiguous scam context, or why a label was chosen. |",
        "",
        "## Semantic Risk Label Rubric",
        "",
        "| Label | Use When |",
        "| --- | --- |",
        "| `no_escalation` | The segment has no meaningful scam-escalation signal by itself. |",
        "| `review` | The segment should be reviewed, but urgency or harm is not clearly high. |",
        "| `priority_review` | The segment contains concrete scam-risk content, suspicious "
        "actor/action/amount, or meaningful potential harm. |",
        "| `critical_escalation` | The segment suggests imminent or severe harm, active "
        "transfer/payment/account compromise, or a missed-intervention scenario. |",
        "",
        "## Risk Atom Rubric",
        "",
        "| Atom | Meaning | Examples Of Decision-Critical Changes |",
        "| --- | --- | --- |",
        "| `negation` | Negation or reversal. | `有匯款` vs `沒有匯款`; `要去` vs `不要去`. |",
        "| `amount` | Money, quantity, account balance, loss amount. | `三萬` vs `三十萬`; `一筆` vs `多筆`. |",
        "| `action` | Payment, transfer, report, cancellation, authentication, withdrawal. | `已轉帳`; `要報案`; `解除分期`. |",
        "| `actor` | Police, bank, customer service, family, scammer, government office. | `警察` vs `客服`; `銀行` vs `LINE`. |",
        "| `intent` | Caller or victim goal/plan. | wants to transfer, cancel, verify, report, ignore. |",
        "| `time` | Deadline, urgency, timing. | `今天`, `馬上`, `已經`, `等一下`. |",
        "| `uncertainty` | Confidence, doubt, hedging. | `好像`, `可能`, `不確定`, `應該`. |",
        "| `scam_pattern` | Fraud scenario type. | fake police, investment, recurring-payment cancellation, fake customer service. |",
        "",
        "## Long-Silence Review Fields And Exact Meaning",
        "",
        "| Field | Fill With | Why It Matters |",
        "| --- | --- | --- |",
        "| `review_status` | One of `valid_call_pause`, `contextual_silence_ok`, "
        "`segmentation_review_needed`, `exclude_from_pilot`. | Confirms whether "
        "the long silence is normal call behavior or a pilot-quality issue. |",
        "| `reviewer` | Your name or initials. | Required by the current long-silence gate. |",
        "| `review_date` | YYYY-MM-DD. | Required by the current long-silence gate. |",
        "| `review_notes` | Short reason. | Use to explain pause type, segmentation concern, or exclusion reason. |",
        "",
        "Long-silence status rubric:",
        "",
        "| Status | Use When |",
        "| --- | --- |",
        "| `valid_call_pause` | Silence sounds like a normal conversational pause or waiting period and the segment remains usable. |",
        "| `contextual_silence_ok` | Silence is expected in the telephone context, such as waiting, listening, hesitation, or background hold. |",
        "| `segmentation_review_needed` | The audio sounds cut incorrectly, contains too much unrelated silence, or may need boundary review. |",
        "| `exclude_from_pilot` | The segment should not be used in the 15-row pilot or downstream comparison. |",
        "",
        "## How To Review Each Gold Row",
        "",
        "For each row:",
        "",
        "1. Play the audio.",
        "2. Listen once for literal transcript correction.",
        "3. Listen again for decision-critical spans: negation, amount, action, "
        "actor, intent, time, uncertainty, scam pattern.",
        "4. Fill `human_verified_transcript` with only what you can verify from audio.",
        "5. Pick one `semantic_risk_label` using the rubric above.",
        "6. Fill `risk_atoms` only for spans that could affect downstream "
        "interpretation. Do not mark every typo.",
        "7. Fill `asr_confusion_terms` with compact confusion pairs. Use "
        "`none_observed` only after listening.",
        "8. Fill `would_asr_error_change_decision` as `yes`, `no`, or `unclear`.",
        "9. Prefer short notes. The goal is a reliable gate, not a long qualitative "
        "transcript essay.",
        "",
    ]
    lines.extend(build_gold_section(root, gold_rows))
    lines.extend(build_long_silence_section(root, silence_rows))
    lines.extend(
        [
            "## Completion Definition",
            "",
            "The human review gate is complete only when:",
            "",
            f"- All {len(gold_rows)} gold rows have non-empty "
            "`human_verified_transcript`, `semantic_risk_label`, `risk_atoms`, "
            "`asr_confusion_terms`, and `would_asr_error_change_decision`.",
            f"- All {len(silence_rows)} long-silence rows have non-empty "
            "`review_status`, `reviewer`, and `review_date`.",
            "- `python3 60_whisper_asr_finetuning/scripts/validate_janus_pilot_gate.py` "
            "returns `ok: true`.",
            "",
            "After this passes, the next correct step is still only the 15-row "
            "NeMo/Whisper/Breeze pilot comparison, not the full 4,967-row dataset.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    root = repo_root_from_script()
    reports_dir = root / "40_breeze_asr25_finetune_dataset" / "reports"
    generated_date = date.today().isoformat()
    default_output = (
        Path.home()
        / "Downloads"
        / f"janus_15_human_review_packet_{generated_date}"
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("--gold-review", type=Path, default=reports_dir / "gold_subset_review.tsv")
    parser.add_argument("--long-silence-review", type=Path, default=reports_dir / "long_silence_review.tsv")
    parser.add_argument("--output-dir", type=Path, default=default_output)
    parser.add_argument("--date", default=generated_date)
    parser.add_argument("--import-workbook", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.import_workbook:
        result = import_workbook(
            args.import_workbook.expanduser(),
            args.gold_review,
            args.long_silence_review,
            dry_run=args.dry_run,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    gold_rows = read_tsv(args.gold_review)
    silence_rows = read_tsv(args.long_silence_review)
    packet_dir = args.output_dir
    packet_dir.mkdir(parents=True, exist_ok=True)

    guide_path = packet_dir / f"janus_15_human_review_guide_{args.date}.md"
    write_text(guide_path, build_guide(root, gold_rows, silence_rows, args.date))

    manifest_rows = []
    manifest_rows.extend(copy_audio(root, packet_dir, "gold", gold_rows))
    manifest_rows.extend(copy_audio(root, packet_dir, "long_silence", silence_rows))
    manifest_path = packet_dir / "audio_manifest.tsv"
    write_manifest(manifest_path, manifest_rows)
    workbook_path = packet_dir / "review_workbook.tsv"
    write_workbook(workbook_path, build_workbook_rows(gold_rows, silence_rows))

    print(f"packet_dir={packet_dir}")
    print(f"guide={guide_path}")
    print(f"audio_manifest={manifest_path}")
    print(f"review_workbook={workbook_path}")
    print(f"gold_audio={len(gold_rows)}")
    print(f"long_silence_audio={len(silence_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

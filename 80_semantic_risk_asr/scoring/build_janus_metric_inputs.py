#!/usr/bin/env python3
"""Build split-aware JANUS metric inputs for SRES, CEIS, and downstream checks.

This generalizes the original 15-row pilot builder without changing the
scoring contracts. It can emit human-reviewed metric inputs when gold review
fields are complete, or explicitly marked proxy inputs when only references and
heuristic labels are available.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any


REQUIRED_HUMAN_FIELDS = (
    "human_verified_transcript",
    "semantic_risk_label",
    "risk_atoms",
    "asr_confusion_terms",
    "would_asr_error_change_decision",
)

ID_FIELDS = ("audio_id", "id", "sample_id")
REFERENCE_TEXT_FIELDS = (
    "human_verified_transcript",
    "reference_text",
    "candidate_reference_transcript",
    "text",
    "sentence",
)
HYPOTHESIS_TEXT_FIELDS = (
    "hypothesis_text",
    "prediction",
    "pred_text",
    "asr_text",
    "transcript",
    "text",
)
ASR_LABEL_FIELDS = (
    "asr_label",
    "prediction_label",
    "hypothesis_label",
    "escalation_label",
)

LABEL_ORDER = {
    "no_escalation": 0,
    "review": 1,
    "priority_review": 2,
    "critical_escalation": 3,
}

NO_OBSERVED_VALUES = {
    "none",
    "none_observed",
    "no_risk_atom",
    "no_risk_atoms",
    "not_applicable",
    "n/a",
    "na",
}

ATOM_TERMS = {
    "negation": (
        "還沒",
        "尚未",
        "沒有",
        "沒",
        "未",
        "不用",
        "不會",
        "無",
    ),
    "amount": (
        "元",
        "塊",
        "萬",
        "千",
        "匯款",
        "轉帳",
        "轉出",
        "匯到",
        "帳戶",
        "卡號",
        "虛擬貨幣",
        "比特幣",
    ),
    "action": (
        "匯款",
        "轉帳",
        "轉出",
        "報案",
        "檢舉",
        "提款",
        "掛失",
        "輸入",
        "申請",
        "購買",
        "買",
        "交付",
        "通知",
        "聯繫",
    ),
    "actor": (
        "警察",
        "派出所",
        "銀行",
        "郵局",
        "客服",
        "政府",
        "台電",
        "家人",
        "朋友",
        "line",
    ),
    "scam_pattern": (
        "詐騙",
        "被盜",
        "釣魚",
        "假",
        "冒用",
        "網購",
        "投資",
        "簡訊",
        "email",
        "虛擬貨幣",
    ),
}


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def read_rows(path: Path) -> list[dict[str, str]]:
    if path.suffix == ".jsonl":
        rows = []
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    item = json.loads(line)
                    rows.append({key: stringify(value) for key, value in item.items()})
        return rows

    delimiter = "," if path.suffix == ".csv" else "\t"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def write_tsv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def first_value(row: dict[str, str], fields: tuple[str, ...]) -> str:
    for field in fields:
        value = (row.get(field) or "").strip()
        if value:
            return value
    return ""


def audio_id_for(row: dict[str, str]) -> str:
    return first_value(row, ID_FIELDS)


def split_tokens(value: str) -> list[str]:
    return [
        token.strip()
        for token in re.split(r"[|,;]", value or "")
        if token.strip() and token.strip().lower() not in NO_OBSERVED_VALUES
    ]


def split_confusions(value: str) -> list[str]:
    return [
        token.strip()
        for token in re.split(r"[|,;]", value or "")
        if token.strip()
    ]


def slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", value.strip())
    return cleaned.strip("_") or "variant"


def compact(text: str) -> str:
    return re.sub(r"\s+", "", text.lower())


def has_term(text: str, terms: tuple[str, ...]) -> bool:
    normalized = compact(text)
    return any(term.lower() in normalized for term in terms)


def infer_proxy_atoms(reference_text: str, hypothesis_text: str) -> list[str]:
    combined = f"{reference_text}\n{hypothesis_text}"
    return [atom for atom, terms in ATOM_TERMS.items() if has_term(combined, terms)]


def import_heuristic_labeler():
    root = repo_root_from_script()
    sys.path.insert(0, str(root / "60_whisper_asr_finetuning" / "scripts"))
    from run_janus_whisper_family_pilot import heuristic_asr_label

    return heuristic_asr_label


def merge_rows(base: dict[str, str], overlay: dict[str, str]) -> dict[str, str]:
    merged = dict(base)
    for key, value in overlay.items():
        if value and not merged.get(key):
            merged[key] = value
    return merged


def load_reference_rows(gold_review: Path | None, manifest: Path | None) -> dict[str, dict[str, str]]:
    rows_by_id: dict[str, dict[str, str]] = {}
    for path in (gold_review, manifest):
        if path is None:
            continue
        for row in read_rows(path):
            audio_id = audio_id_for(row)
            if not audio_id:
                continue
            normalized = dict(row)
            normalized["audio_id"] = audio_id
            if "split" not in normalized or not normalized["split"]:
                normalized["split"] = infer_split_from_audio_id(audio_id)
            if audio_id in rows_by_id:
                rows_by_id[audio_id] = merge_rows(rows_by_id[audio_id], normalized)
            else:
                rows_by_id[audio_id] = normalized
    return rows_by_id


def infer_split_from_audio_id(audio_id: str) -> str:
    match = re.match(r"janus_([^_]+)_", audio_id)
    return match.group(1) if match else ""


def human_fields_missing(row: dict[str, str]) -> list[str]:
    return [field for field in REQUIRED_HUMAN_FIELDS if not (row.get(field) or "").strip()]


def row_review_mode(row: dict[str, str], requested_mode: str) -> str:
    if requested_mode == "human":
        return "human_reviewed"
    if requested_mode == "proxy":
        return "proxy"
    return "human_reviewed" if not human_fields_missing(row) else "proxy"


def decision_distance(reference_label: str, asr_label: str) -> int:
    if reference_label not in LABEL_ORDER or asr_label not in LABEL_ORDER:
        return 0
    return abs(LABEL_ORDER[reference_label] - LABEL_ORDER[asr_label])


def decision_change_flag(row: dict[str, str], reference_label: str, asr_label: str) -> str:
    explicit = (row.get("would_asr_error_change_decision") or "").strip().lower()
    if explicit:
        return explicit
    return "yes" if decision_distance(reference_label, asr_label) else "no"


def severity_for(row: dict[str, str], reference_label: str, asr_label: str) -> int:
    flag = decision_change_flag(row, reference_label, asr_label)
    if flag == "yes":
        return 5
    if flag == "unclear":
        return 3
    if flag == "no":
        return 1
    return 2


def downstream_impact_for(
    row: dict[str, str],
    reference_label: str,
    asr_label: str,
) -> int:
    distance = decision_distance(reference_label, asr_label)
    flag = decision_change_flag(row, reference_label, asr_label)
    if flag == "yes":
        return max(distance, 3)
    if flag == "unclear":
        return max(distance, 1)
    if flag == "no":
        return distance
    return max(distance, 1 if not asr_label else 0)


def infer_run_id(path: Path, row: dict[str, str]) -> str:
    return first_value(row, ("asr_run_id", "run_id", "model_kind", "model")) or path.stem


def sample_id(audio_id: str, asr_run_id: str) -> str:
    return f"{audio_id}__{slug(asr_run_id)}"


def expected_ids_for(rows_by_id: dict[str, dict[str, str]], split: str) -> set[str]:
    if split not in {"train", "validation", "test"}:
        return set(rows_by_id)
    return {
        audio_id
        for audio_id, row in rows_by_id.items()
        if (row.get("split") or infer_split_from_audio_id(audio_id)) == split
    }


def reference_text_for(row: dict[str, str], hypothesis: dict[str, str]) -> str:
    return first_value(row, REFERENCE_TEXT_FIELDS) or first_value(
        hypothesis,
        ("reference_text", "human_verified_transcript", "text", "sentence"),
    )


def reference_label_for(
    row: dict[str, str],
    hypothesis: dict[str, str],
    reference_text: str,
    heuristic_labeler: Any,
) -> tuple[str, str]:
    explicit = first_value(row, ("semantic_risk_label",)) or first_value(
        hypothesis,
        ("reference_label",),
    )
    if explicit:
        return explicit, "gold_or_hypothesis"
    label, _reason = heuristic_labeler(reference_text)
    return label, "heuristic_v0"


def asr_label_for(
    hypothesis: dict[str, str],
    hypothesis_text: str,
    heuristic_labeler: Any,
) -> tuple[str, str]:
    explicit = first_value(hypothesis, ASR_LABEL_FIELDS)
    if explicit:
        return explicit, "hypothesis"
    label, _reason = heuristic_labeler(hypothesis_text)
    return label, "heuristic_v0"


def atoms_for(
    row: dict[str, str],
    reference_text: str,
    hypothesis_text: str,
    review_mode: str,
) -> list[str]:
    atoms = split_tokens(row.get("risk_atoms", ""))
    if atoms:
        return atoms
    if review_mode == "proxy":
        return infer_proxy_atoms(reference_text, hypothesis_text)
    return []


def build_rows(
    rows_by_id: dict[str, dict[str, str]],
    hypothesis_paths: list[Path],
    split: str,
    requested_review_mode: str,
    require_all_gold_ids: bool,
    expected_rows: int | None,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], dict[str, Any]]:
    heuristic_labeler = import_heuristic_labeler()
    expected_ids = expected_ids_for(rows_by_id, split)
    sres_rows: list[dict[str, str]] = []
    ceis_rows: list[dict[str, str]] = []
    downstream_rows: list[dict[str, str]] = []
    unmatched_hypotheses: list[str] = []
    missing_hypothesis_text: list[str] = []
    missing_asr_label: list[str] = []
    missing_reference_text: list[str] = []
    missing_expected_by_file: dict[str, list[str]] = {}
    extra_ids_by_file: dict[str, list[str]] = {}
    observed_ids_by_file: dict[str, list[str]] = {}
    review_mode_counts = {"human_reviewed": 0, "proxy": 0}

    if expected_rows is not None and len(expected_ids) != expected_rows:
        expected_count_error = {
            "expected_rows": expected_rows,
            "actual_reference_rows": len(expected_ids),
        }
    else:
        expected_count_error = {}

    for path in hypothesis_paths:
        observed_ids: set[str] = set()
        for hypothesis in read_rows(path):
            audio_id = audio_id_for(hypothesis)
            asr_run_id = infer_run_id(path, hypothesis)
            if audio_id:
                observed_ids.add(audio_id)
            if audio_id not in rows_by_id:
                unmatched_hypotheses.append(f"{path}:{audio_id or '<missing_audio_id>'}")
                continue
            if expected_ids and audio_id not in expected_ids:
                continue

            gold = rows_by_id[audio_id]
            review_mode = row_review_mode(gold, requested_review_mode)
            review_mode_counts[review_mode] += 1
            segment_id = sample_id(audio_id, asr_run_id)
            reference_text = reference_text_for(gold, hypothesis)
            hypothesis_text = first_value(hypothesis, HYPOTHESIS_TEXT_FIELDS)
            reference_label, reference_label_method = reference_label_for(
                gold,
                hypothesis,
                reference_text,
                heuristic_labeler,
            )
            asr_label, asr_label_method = asr_label_for(
                hypothesis,
                hypothesis_text,
                heuristic_labeler,
            )
            recovered_label = first_value(
                hypothesis,
                ("recovered_label", "post_recovery_label"),
            ) or asr_label
            recovery_action = first_value(hypothesis, ("recovery_action",)) or "none"
            atoms = atoms_for(gold, reference_text, hypothesis_text, review_mode)
            confusions = split_confusions(gold.get("asr_confusion_terms", ""))
            decision_change = decision_change_flag(gold, reference_label, asr_label)

            if not reference_text:
                missing_reference_text.append(segment_id)
            if not hypothesis_text:
                missing_hypothesis_text.append(segment_id)
            if not asr_label:
                missing_asr_label.append(segment_id)

            for atom in atoms:
                sres_rows.append(
                    {
                        "sample_id": segment_id,
                        "split": gold.get("split", "") or infer_split_from_audio_id(audio_id),
                        "asr_run_id": asr_run_id,
                        "reference_text": reference_text,
                        "hypothesis_text": hypothesis_text,
                        "wer": hypothesis.get("wer", ""),
                        "cer": hypothesis.get("cer", ""),
                        "error_type": atom,
                        "severity": str(severity_for(gold, reference_label, asr_label)),
                        "downstream_impact": str(
                            downstream_impact_for(gold, reference_label, asr_label)
                        ),
                        "decision_field": atom,
                        "recovery_action": recovery_action,
                        "annotator_note": (
                            f"review_mode={review_mode}; "
                            f"reference_label_method={reference_label_method}; "
                            f"asr_label_method={asr_label_method}; "
                            f"gold_confusions={gold.get('asr_confusion_terms', '')}; "
                            f"decision_change={decision_change}"
                        ),
                        "review_mode": review_mode,
                    }
                )

            for index, atom in enumerate(atoms, start=1):
                confusion = confusions[index - 1] if index - 1 < len(confusions) else ""
                ceis_rows.append(
                    {
                        "sample_id": segment_id,
                        "variant_id": f"v_{index:02d}_{slug(atom)}",
                        "base_decision": asr_label,
                        "variant_decision": reference_label,
                        "acoustic_plausibility": first_value(
                            hypothesis,
                            ("variant_plausibility", "acoustic_plausibility", "plausibility"),
                        )
                        or "1.0",
                        "risk_atom_type": atom,
                        "risk_atom_weight": "",
                        "decision_distance": "",
                        "base_transcript": hypothesis_text,
                        "variant_transcript": reference_text,
                        "note": (
                            f"review_mode={review_mode}; "
                            f"confusion={confusion or 'unspecified'}; "
                            "default_plausibility_until_ASR_confidence_is_available"
                        ),
                        "review_mode": review_mode,
                    }
                )

            downstream_rows.append(
                {
                    "sample_id": segment_id,
                    "reference_label": reference_label,
                    "asr_label": asr_label,
                    "recovered_label": recovered_label,
                    "recovery_action": recovery_action,
                    "note": (
                        f"audio_id={audio_id}; asr_run_id={asr_run_id}; "
                        f"review_mode={review_mode}; decision_change={decision_change}"
                    ),
                    "review_mode": review_mode,
                }
            )

        missing = sorted(expected_ids - observed_ids)
        extra = sorted(observed_ids - expected_ids)
        if missing:
            missing_expected_by_file[str(path)] = missing
        if extra:
            extra_ids_by_file[str(path)] = extra
        observed_ids_by_file[str(path)] = sorted(observed_ids)

    summary = {
        "split": split,
        "review_mode_requested": requested_review_mode,
        "review_mode_counts": review_mode_counts,
        "reference_rows": len(expected_ids),
        "expected_rows": expected_rows,
        "hypothesis_files": [str(path) for path in hypothesis_paths],
        "sres_rows": len(sres_rows),
        "ceis_rows": len(ceis_rows),
        "downstream_rows": len(downstream_rows),
        "unmatched_hypotheses": unmatched_hypotheses,
        "missing_reference_text": missing_reference_text,
        "missing_hypothesis_text": missing_hypothesis_text,
        "missing_asr_label": missing_asr_label,
        "missing_expected_by_file": missing_expected_by_file,
        "extra_ids_by_file": extra_ids_by_file,
        "observed_counts_by_file": {
            path: len(ids) for path, ids in observed_ids_by_file.items()
        },
        "expected_count_error": expected_count_error,
        "notes": (
            "proxy rows are useful for engineering gates but are not a substitute "
            "for human-reviewed risk-atom evidence"
        ),
    }
    if require_all_gold_ids and missing_expected_by_file:
        summary["require_all_gold_ids_failed"] = True
    else:
        summary["require_all_gold_ids_failed"] = False
    return sres_rows, ceis_rows, downstream_rows, summary


def parse_args() -> argparse.Namespace:
    root = repo_root_from_script()
    default_gold = (
        root
        / "40_breeze_asr25_finetune_dataset"
        / "reports"
        / "gold_subset_review.tsv"
    )
    default_output = (
        root
        / "70_experiments"
        / "runs"
        / "janus_metric_inputs"
        / "artifacts"
        / "metric_inputs"
    )
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", default="pilot_15")
    parser.add_argument("--gold-review", type=Path, default=default_gold)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--hypotheses", type=Path, action="append", required=True)
    parser.add_argument("--output-dir", type=Path, default=default_output)
    parser.add_argument(
        "--review-mode",
        choices=("auto", "human", "proxy"),
        default="auto",
        help="`human` fails if required review fields are missing; `proxy` marks all rows as proxy.",
    )
    parser.add_argument("--expected-rows", type=int)
    parser.add_argument("--require-all-gold-ids", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows_by_id = load_reference_rows(args.gold_review, args.manifest)
    human_missing = {
        audio_id: human_fields_missing(row)
        for audio_id, row in rows_by_id.items()
        if human_fields_missing(row)
    }
    if args.review_mode == "human" and human_missing:
        result = {
            "ok": False,
            "reason": "human review fields are incomplete",
            "missing_required_fields_by_audio_id": human_missing,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    sres_rows, ceis_rows, downstream_rows, summary = build_rows(
        rows_by_id=rows_by_id,
        hypothesis_paths=args.hypotheses,
        split=args.split,
        requested_review_mode=args.review_mode,
        require_all_gold_ids=args.require_all_gold_ids,
        expected_rows=args.expected_rows,
    )

    output_dir = args.output_dir
    write_tsv(
        output_dir / "sres_annotation.tsv",
        sres_rows,
        [
            "sample_id",
            "split",
            "asr_run_id",
            "reference_text",
            "hypothesis_text",
            "wer",
            "cer",
            "error_type",
            "severity",
            "downstream_impact",
            "decision_field",
            "recovery_action",
            "annotator_note",
            "review_mode",
        ],
    )
    write_tsv(
        output_dir / "counterfactual_variants.tsv",
        ceis_rows,
        [
            "sample_id",
            "variant_id",
            "base_decision",
            "variant_decision",
            "acoustic_plausibility",
            "risk_atom_type",
            "risk_atom_weight",
            "decision_distance",
            "base_transcript",
            "variant_transcript",
            "note",
            "review_mode",
        ],
    )
    write_tsv(
        output_dir / "downstream_escalation_decisions.tsv",
        downstream_rows,
        [
            "sample_id",
            "reference_label",
            "asr_label",
            "recovered_label",
            "recovery_action",
            "note",
            "review_mode",
        ],
    )

    summary["ok"] = not (
        summary["unmatched_hypotheses"]
        or summary["missing_reference_text"]
        or summary["missing_hypothesis_text"]
        or summary["missing_asr_label"]
        or summary["expected_count_error"]
        or summary["require_all_gold_ids_failed"]
    )
    summary["output_dir"] = str(output_dir)
    write_json(output_dir / "build_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

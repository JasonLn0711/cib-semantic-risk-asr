#!/usr/bin/env python3
"""Select local high-stakes JANUS candidates for the 300-500 row expansion."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


RISK_WEIGHTS = {
    "匯款": 6,
    "轉帳": 6,
    "轉出": 6,
    "帳戶": 5,
    "銀行": 5,
    "郵局": 4,
    "提款卡": 6,
    "第三方支付": 6,
    "虛擬貨幣": 6,
    "投資": 5,
    "警察": 5,
    "報案": 5,
    "身分證": 4,
    "健保卡": 4,
    "LINE": 4,
    "詐騙": 4,
    "客服": 3,
    "戶政": 3,
    "地政": 3,
    "保險": 2,
}

SCENARIO_TERMS = {
    "money_transfer": ("匯款", "轉帳", "轉出", "轉給"),
    "account_bank": ("帳戶", "銀行", "郵局", "第三方支付"),
    "identity_document": ("身分證", "健保卡", "個資"),
    "police_government": ("警察", "派出所", "報案", "戶政", "地政"),
    "line_social": ("LINE", "帳號被盜", "被盜"),
    "investment_crypto": ("投資", "虛擬貨幣"),
    "card_or_cash": ("提款卡", "提領", "刷卡"),
    "customer_service": ("客服", "預警", "案號"),
}


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


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


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def term_hits(text: str) -> list[str]:
    return [term for term in RISK_WEIGHTS if term in text]


def scenario_hits(text: str) -> list[str]:
    return [
        scenario
        for scenario, terms in SCENARIO_TERMS.items()
        if any(term in text for term in terms)
    ]


def score_row(text: str, duration: float, health_flags: str, alignment_score: float) -> float:
    score = sum(RISK_WEIGHTS[term] for term in term_hits(text))
    scenarios = scenario_hits(text)
    score += len(scenarios) * 2
    if "匯" in text and ("已經" in text or "有" in text or "了" in text):
        score += 4
    if "詐騙" in text and ("報案" in text or "警察" in text):
        score += 3
    if 8.0 <= duration <= 45.0:
        score += 2
    if health_flags and health_flags != "ok":
        score -= 3
    score += max(0.0, min(alignment_score, 1.0))
    return round(score, 4)


def quota_for(split: str, sample_size: int) -> int:
    if split == "train":
        return max(1, int(round(sample_size * 0.80)))
    if split == "validation":
        return max(1, int(round(sample_size * 0.10)))
    if split == "test":
        return max(1, sample_size - quota_for("train", sample_size) - quota_for("validation", sample_size))
    return 0


def main() -> int:
    root = repo_root_from_script()
    default_manifests = root / "40_breeze_asr25_finetune_dataset" / "manifests"
    default_reports = root / "40_breeze_asr25_finetune_dataset" / "reports"
    default_run_dir = root / "70_experiments" / "runs" / "janus_300_500_high_stakes_expansion"

    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=default_manifests / "all.jsonl")
    parser.add_argument("--health", type=Path, default=default_reports / "audio_health_check.csv")
    parser.add_argument("--gold-review", type=Path, default=default_reports / "gold_subset_review.tsv")
    parser.add_argument("--sample-size", type=int, default=300)
    parser.add_argument("--output", type=Path, default=default_run_dir / "artifacts" / "expansion_candidates.tsv")
    parser.add_argument("--summary", type=Path, default=default_run_dir / "selection_summary.tsv")
    args = parser.parse_args()

    manifest_rows = read_jsonl(args.manifest)
    health_by_id = {row["audio_id"]: row for row in read_csv(args.health)}
    gold_ids = {row["audio_id"] for row in read_tsv(args.gold_review) if row.get("audio_id")}

    candidates: list[dict[str, Any]] = []
    for row in manifest_rows:
        audio_id = str(row.get("id", ""))
        if not audio_id or audio_id in gold_ids:
            continue
        text = str(row.get("sentence") or row.get("text") or "")
        health = health_by_id.get(audio_id, {})
        duration = as_float(row.get("duration") or health.get("duration_sec"))
        split = str(row.get("split", ""))
        health_flags = str(health.get("flags", ""))
        risk_terms = term_hits(text)
        scenarios = scenario_hits(text)
        if not risk_terms or not scenarios:
            continue
        candidates.append(
            {
                "audio_id": audio_id,
                "split": split,
                "duration_sec": f"{duration:.3f}",
                "alignment_score": row.get("alignment_score", ""),
                "health_flags": health_flags,
                "risk_term_count": len(risk_terms),
                "risk_terms": "|".join(risk_terms),
                "scenario_tags": "|".join(scenarios),
                "selection_score": score_row(
                    text,
                    duration,
                    health_flags,
                    as_float(row.get("alignment_score")),
                ),
            }
        )

    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for split in ("train", "validation", "test"):
        quota = quota_for(split, args.sample_size)
        split_rows = sorted(
            [row for row in candidates if row["split"] == split],
            key=lambda item: (-as_float(item["selection_score"]), item["audio_id"]),
        )
        for row in split_rows[:quota]:
            selected.append(row)
            seen.add(row["audio_id"])

    if len(selected) < args.sample_size:
        for row in sorted(candidates, key=lambda item: (-as_float(item["selection_score"]), item["audio_id"])):
            if row["audio_id"] in seen:
                continue
            selected.append(row)
            seen.add(row["audio_id"])
            if len(selected) >= args.sample_size:
                break

    selected = selected[: args.sample_size]
    candidate_fields = [
        "audio_id",
        "split",
        "duration_sec",
        "alignment_score",
        "health_flags",
        "risk_term_count",
        "risk_terms",
        "scenario_tags",
        "selection_score",
    ]
    write_tsv(args.output, selected, candidate_fields)

    split_counts = Counter(row["split"] for row in selected)
    health_counts = Counter(row["health_flags"] for row in selected)
    scenario_counts: Counter[str] = Counter()
    risk_term_counts: Counter[str] = Counter()
    durations = [as_float(row["duration_sec"]) for row in selected]
    for row in selected:
        scenario_counts.update(tag for tag in str(row["scenario_tags"]).split("|") if tag)
        risk_term_counts.update(term for term in str(row["risk_terms"]).split("|") if term)

    summary_rows = [
        {"metric": "selected_rows", "value": len(selected), "notes": f"target={args.sample_size}"},
        {"metric": "candidate_pool_rows", "value": len(candidates), "notes": "rows with risk terms and scenario tags"},
        {"metric": "excluded_gold_rows", "value": len(gold_ids), "notes": "held out reviewed pilot rows"},
        {"metric": "duration_min_sec", "value": round(min(durations), 3) if durations else "", "notes": "selected rows"},
        {"metric": "duration_max_sec", "value": round(max(durations), 3) if durations else "", "notes": "selected rows"},
        {"metric": "duration_mean_sec", "value": round(sum(durations) / len(durations), 3) if durations else "", "notes": "selected rows"},
    ]
    for split, count in sorted(split_counts.items()):
        summary_rows.append({"metric": f"split_{split}", "value": count, "notes": "selected rows"})
    for health_flag, count in sorted(health_counts.items()):
        summary_rows.append({"metric": f"health_{health_flag}", "value": count, "notes": "selected rows"})
    for scenario, count in sorted(scenario_counts.items()):
        summary_rows.append({"metric": f"scenario_{scenario}", "value": count, "notes": "non-exclusive scenario tag count"})
    for term, count in sorted(risk_term_counts.items()):
        summary_rows.append({"metric": f"risk_term_{term}", "value": count, "notes": "non-exclusive risk-term count"})

    write_tsv(args.summary, summary_rows, ["metric", "value", "notes"])
    print(
        json.dumps(
            {
                "ok": len(selected) == args.sample_size,
                "selected_rows": len(selected),
                "candidate_pool_rows": len(candidates),
                "output": str(args.output),
                "summary": str(args.summary),
                "split_counts": dict(sorted(split_counts.items())),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if len(selected) == args.sample_size else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Evaluate escalation-label changes before and after recovery."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


HIGH_RISK = {"priority_review", "critical_escalation"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("decisions_tsv", type=Path)
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args()

    with args.decisions_tsv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))

    total = len(rows)
    asr_mismatch = 0
    recovered = 0
    high_risk_missed_by_asr = 0
    high_risk_missed_after_recovery = 0
    recovery_triggered = 0

    for row in rows:
        ref = row.get("reference_label", "")
        asr = row.get("asr_label", "")
        recovered_label = row.get("recovered_label", asr)
        if asr != ref:
            asr_mismatch += 1
        if recovered_label == ref and asr != ref:
            recovered += 1
        if ref in HIGH_RISK and asr not in HIGH_RISK:
            high_risk_missed_by_asr += 1
        if ref in HIGH_RISK and recovered_label not in HIGH_RISK:
            high_risk_missed_after_recovery += 1
        if (row.get("recovery_action") or "none") != "none":
            recovery_triggered += 1

    result = {
        "rows": total,
        "asr_mismatch_rate": round(asr_mismatch / total, 4) if total else 0.0,
        "recovered_error_count": recovered,
        "high_risk_missed_by_asr": high_risk_missed_by_asr,
        "high_risk_missed_after_recovery": high_risk_missed_after_recovery,
        "recovery_trigger_rate": round(recovery_triggered / total, 4) if total else 0.0,
    }
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

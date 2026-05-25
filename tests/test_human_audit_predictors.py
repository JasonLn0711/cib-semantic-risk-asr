from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "annotation"))

from analyze_human_audit_predictors import (  # noqa: E402
    assert_aggregate_safe,
    extract_model_rows,
    model_summary_rows,
    predictor_rows,
    read_tsv,
)


FIELDS = [
    "audio_id",
    "split",
    "selection_stratum",
    "selection_reason",
    "reference_label",
    "reference_text",
    "asr_hypotheses_json",
    "risk_signal_json",
    "reviewer_verified_transcript",
    "reviewer_semantic_risk_label",
    "reviewer_risk_atoms",
    "reviewer_critical_atoms",
    "reviewer_asr_confusion_terms",
    "reviewer_would_asr_error_change_decision",
    "reviewer_decision_change_reason",
    "reviewer_expected_safe_action",
    "reviewer_annotation_confidence",
    "reviewer_model_assessments_json",
    "reviewer_notes",
]


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    lines = ["\t".join(FIELDS)]
    for row in rows:
        lines.append("\t".join(row.get(field, "") for field in FIELDS))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def row_for(audio_id: str, decision: str, wer: float, sres: float) -> dict[str, str]:
    return {
        "audio_id": audio_id,
        "split": "test",
        "selection_stratum": "unsafe_downrouting",
        "selection_reason": "private",
        "reference_label": "priority_review",
        "reference_text": "PRIVATE_REFERENCE",
        "asr_hypotheses_json": json.dumps(
            [
                {
                    "asr_run_id": "run_a",
                    "hypothesis_text": "PRIVATE_HYP",
                    "wer": wer,
                    "cer": wer / 2,
                    "sres_total": sres,
                    "ceis_max": sres / 10,
                }
            ],
            ensure_ascii=False,
        ),
        "risk_signal_json": "{}",
        "reviewer_verified_transcript": "",
        "reviewer_semantic_risk_label": "priority_review",
        "reviewer_risk_atoms": "negation",
        "reviewer_critical_atoms": "negation",
        "reviewer_asr_confusion_terms": "negation",
        "reviewer_would_asr_error_change_decision": decision,
        "reviewer_decision_change_reason": "routing",
        "reviewer_expected_safe_action": "priority_review",
        "reviewer_annotation_confidence": "high",
        "reviewer_model_assessments_json": json.dumps(
            [
                {
                    "asr_run_id": "run_a",
                    "reviewer_would_asr_error_change_decision": decision,
                    "reviewer_critical_atoms": "negation",
                    "reviewer_expected_safe_action": "priority_review",
                    "reviewer_annotation_confidence": "high",
                }
            ],
            ensure_ascii=False,
        ),
        "reviewer_notes": "PRIVATE_NOTE",
    }


def test_human_predictor_analysis_uses_model_level_review(tmp_path: Path) -> None:
    sheet = tmp_path / "audit.tsv"
    write_rows(
        sheet,
        [
            row_for("audio_private_1", "yes", 30.0, 80.0),
            row_for("audio_private_2", "no", 2.0, 0.0),
        ],
    )
    model_rows, counters = extract_model_rows(read_tsv(sheet))
    comparisons = predictor_rows(model_rows)
    model_summary = model_summary_rows(model_rows)
    payload = {"ok": True, "status": "review_complete"}
    assert_aggregate_safe(payload, comparisons + model_summary)

    assert counters["model_assessments"] == 2
    assert counters["reviewed_model_assessments"] == 2
    assert model_summary[0]["human_decision_change_yes_count"] == 1
    sres_row = next(
        row
        for row in comparisons
        if row["scope"] == "overall"
        and row["target"] == "human_decision_change_yes"
        and row["metric"] == "sres_total"
    )
    assert sres_row["auc"] == 1.0
    assert sres_row["best_f1"] == 1.0

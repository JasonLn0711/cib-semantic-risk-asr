import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "80_semantic_risk_asr" / "scoring"))

from analyze_ceis_ablation import main  # noqa: E402


AUDIT_FIELDS = [
    "audio_id",
    "reviewer_semantic_risk_label",
    "reference_text",
    "asr_hypotheses_json",
    "reviewer_model_assessments_json",
    "reviewer_notes",
]


def write_tsv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def audit_row(audio_id: str, decision: str) -> dict[str, str]:
    run_id = "model_a"
    return {
        "audio_id": audio_id,
        "reviewer_semantic_risk_label": "priority_review",
        "reference_text": "PRIVATE_TRANSCRIPT",
        "asr_hypotheses_json": json.dumps(
            [
                {
                    "asr_run_id": run_id,
                    "asr_label": "review",
                }
            ]
        ),
        "reviewer_model_assessments_json": json.dumps(
            [
                {
                    "asr_run_id": run_id,
                    "reviewer_would_asr_error_change_decision": decision,
                    "reviewer_critical_atoms": "amount" if decision == "yes" else "none",
                    "reviewer_expected_safe_action": "priority_review"
                    if decision == "yes"
                    else "none",
                    "reviewer_annotation_confidence": "high",
                }
            ]
        ),
        "reviewer_notes": "PRIVATE_NOTE",
    }


def test_ceis_ablation_outputs_are_aggregate_only(tmp_path, monkeypatch):
    audit = tmp_path / "audit.tsv"
    ceis = tmp_path / "ceis.tsv"
    out = tmp_path / "out"
    write_tsv(
        audit,
        [audit_row("row-1", "yes"), audit_row("row-2", "no")],
        AUDIT_FIELDS,
    )
    write_tsv(
        ceis,
        [
            {
                "sample_id": "row-1__model_a",
                "variant_id": "v1",
                "base_decision": "review",
                "variant_decision": "priority_review",
                "acoustic_plausibility": "0.5",
                "risk_atom_type": "amount",
                "risk_atom_weight_used": "5",
                "decision_distance_used": "1",
                "base_transcript": "PRIVATE_TRANSCRIPT",
                "variant_transcript": "PRIVATE_TRANSCRIPT",
                "ceis_component": "2.5",
            },
            {
                "sample_id": "row-2__model_a",
                "variant_id": "v1",
                "base_decision": "review",
                "variant_decision": "review",
                "acoustic_plausibility": "1",
                "risk_atom_type": "amount",
                "risk_atom_weight_used": "5",
                "decision_distance_used": "0",
                "base_transcript": "PRIVATE_TRANSCRIPT",
                "variant_transcript": "PRIVATE_TRANSCRIPT",
                "ceis_component": "0",
            },
        ],
        [
            "sample_id",
            "variant_id",
            "base_decision",
            "variant_decision",
            "acoustic_plausibility",
            "risk_atom_type",
            "risk_atom_weight_used",
            "decision_distance_used",
            "base_transcript",
            "variant_transcript",
            "ceis_component",
        ],
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "analyze_ceis_ablation.py",
            "--ceis-scored",
            str(ceis),
            "--reviewer-sheet",
            f"r1={audit}",
            "--output-dir",
            str(out),
        ],
    )

    assert main() == 0

    predictor = (out / "ceis_ablation_predictor_summary.tsv").read_text(encoding="utf-8")
    tracked = "\n".join(path.read_text(encoding="utf-8") for path in out.iterdir())
    assert "ceis_full" in predictor
    assert "ceis_without_atom_weights" in predictor
    assert "ceis_without_plausibility" in predictor
    assert "ceis_binary_atom" in predictor
    assert "row-1" not in tracked
    assert "PRIVATE_TRANSCRIPT" not in tracked
    assert "PRIVATE_NOTE" not in tracked
    assert "audio_id" not in tracked

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "80_semantic_risk_asr" / "annotation"))

from compute_human_audit_agreement import main  # noqa: E402


FIELDS = [
    "audio_id",
    "reference_text",
    "reviewer_would_asr_error_change_decision",
    "reviewer_semantic_risk_label",
    "reviewer_expected_safe_action",
    "reviewer_annotation_confidence",
    "reviewer_notes",
]


def write_sheet(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_agreement_outputs_kappa_without_private_content(tmp_path, monkeypatch):
    reviewer_a = tmp_path / "reviewer_a.tsv"
    reviewer_b = tmp_path / "reviewer_b.tsv"
    output_dir = tmp_path / "out"
    base_rows = [
        {
            "audio_id": "row-1",
            "reference_text": "PRIVATE_TRANSCRIPT",
            "reviewer_would_asr_error_change_decision": "yes",
            "reviewer_semantic_risk_label": "priority_review",
            "reviewer_expected_safe_action": "priority_review",
            "reviewer_annotation_confidence": "high",
            "reviewer_notes": "PRIVATE_NOTE",
        },
        {
            "audio_id": "row-2",
            "reference_text": "PRIVATE_TRANSCRIPT",
            "reviewer_would_asr_error_change_decision": "no",
            "reviewer_semantic_risk_label": "review",
            "reviewer_expected_safe_action": "manual_review",
            "reviewer_annotation_confidence": "medium",
            "reviewer_notes": "PRIVATE_NOTE",
        },
        {
            "audio_id": "row-3",
            "reference_text": "PRIVATE_TRANSCRIPT",
            "reviewer_would_asr_error_change_decision": "yes",
            "reviewer_semantic_risk_label": "critical_escalation",
            "reviewer_expected_safe_action": "critical_escalation",
            "reviewer_annotation_confidence": "high",
            "reviewer_notes": "PRIVATE_NOTE",
        },
    ]
    write_sheet(reviewer_a, base_rows)
    reviewer_b_rows = [dict(row) for row in base_rows]
    reviewer_b_rows[1]["reviewer_would_asr_error_change_decision"] = "yes"
    write_sheet(reviewer_b, reviewer_b_rows)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "compute_human_audit_agreement.py",
            "--reviewer-sheet",
            f"r1={reviewer_a}",
            "--reviewer-sheet",
            f"r2={reviewer_b}",
            "--output-dir",
            str(output_dir),
        ],
    )

    assert main() == 0

    agreement = (output_dir / "human_audit_reviewer_agreement.tsv").read_text(encoding="utf-8")
    summary = (output_dir / "human_audit_reviewer_agreement_summary.json").read_text(
        encoding="utf-8"
    )
    assert "reviewer_would_asr_error_change_decision" in agreement
    assert "cohen_kappa" in agreement
    assert "fleiss_kappa" in agreement
    tracked = agreement + summary
    assert "row-1" not in tracked
    assert "PRIVATE_TRANSCRIPT" not in tracked
    assert "PRIVATE_NOTE" not in tracked
    assert "audio_id" not in tracked

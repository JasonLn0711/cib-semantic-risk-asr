from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "annotation"))

from refresh_human_audit_evidence import refresh_human_audit_evidence  # noqa: E402


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


def base_row(*, reviewed: bool, model_reviewed: bool) -> dict[str, str]:
    model_assessment = {
        "asr_run_id": "run_a",
        "reviewer_would_asr_error_change_decision": "yes" if model_reviewed else "",
        "reviewer_critical_atoms": "negation" if model_reviewed else "",
        "reviewer_expected_safe_action": "priority_review" if model_reviewed else "",
        "reviewer_annotation_confidence": "high" if model_reviewed else "",
    }
    row = {
        "audio_id": "private_audio_001",
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
                    "wer": 3.0,
                    "cer": 1.5,
                    "sres_total": 10.0,
                    "ceis_max": 8.0,
                }
            ],
            ensure_ascii=False,
        ),
        "risk_signal_json": "{}",
        "reviewer_verified_transcript": "",
        "reviewer_semantic_risk_label": "",
        "reviewer_risk_atoms": "",
        "reviewer_critical_atoms": "",
        "reviewer_asr_confusion_terms": "",
        "reviewer_would_asr_error_change_decision": "",
        "reviewer_decision_change_reason": "",
        "reviewer_expected_safe_action": "",
        "reviewer_annotation_confidence": "",
        "reviewer_model_assessments_json": json.dumps([model_assessment], ensure_ascii=False),
        "reviewer_notes": "PRIVATE_NOTE",
    }
    if reviewed:
        row.update(
            {
                "reviewer_semantic_risk_label": "priority_review",
                "reviewer_risk_atoms": "negation",
                "reviewer_critical_atoms": "negation",
                "reviewer_asr_confusion_terms": "negation dropped",
                "reviewer_would_asr_error_change_decision": "yes",
                "reviewer_decision_change_reason": "routing changed",
                "reviewer_expected_safe_action": "priority_review",
                "reviewer_annotation_confidence": "high",
            }
        )
    return row


def run_refresh(
    tmp_path: Path,
    *,
    reviewed: bool,
    model_reviewed: bool,
    require_complete: bool = False,
) -> tuple[dict, Path]:
    sheet = tmp_path / "audit.tsv"
    output_dir = tmp_path / "aggregate"
    readiness_dir = tmp_path / "readiness"
    write_rows(sheet, [base_row(reviewed=reviewed, model_reviewed=model_reviewed)])
    payload = refresh_human_audit_evidence(
        audit_sheet=sheet,
        output_dir=output_dir,
        readiness_output_dir=readiness_dir,
        repo_root=tmp_path,
        expected_rows=1,
        require_complete=require_complete,
        skip_readiness=True,
    )
    return payload, output_dir


def load_readiness_fixture_writer():
    path = REPO_ROOT / "tests" / "test_evidence_chain_readiness.py"
    spec = importlib.util.spec_from_file_location("test_evidence_chain_readiness", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.write_minimal_tree


def test_refresh_allows_pending_review_without_strict_mode(tmp_path: Path) -> None:
    payload, output_dir = run_refresh(tmp_path, reviewed=False, model_reviewed=False)

    assert payload["ok"] is True
    assert payload["status"] == "review_pending"
    assert payload["pending_rows"] == 1
    assert payload["pending_model_assessments"] == 1
    assert "--require-timing" in payload["next_action"]
    assert (output_dir / "human_audit_validation_summary.json").exists()
    assert (output_dir / "human_audit_progress_summary.json").exists()
    assert (output_dir / "human_audit_review_batches.tsv").exists()
    assert (output_dir / "human_audit_review_summary.json").exists()
    assert (output_dir / "human_audit_predictor_summary.json").exists()
    assert "PRIVATE_" not in (output_dir / "human_audit_refresh_summary.json").read_text(
        encoding="utf-8"
    )


def test_refresh_require_complete_fails_pending_review(tmp_path: Path) -> None:
    payload, output_dir = run_refresh(
        tmp_path,
        reviewed=False,
        model_reviewed=False,
        require_complete=True,
    )

    assert payload["ok"] is False
    assert payload["status"] == "validation_failed"
    assert payload["validation_error_counts"]["incomplete_row_review"] == 1
    assert payload["validation_error_counts"]["incomplete_model_review"] == 1
    assert (output_dir / "human_audit_validation_summary.json").exists()
    assert (output_dir / "human_audit_progress_summary.json").exists()
    assert not (output_dir / "human_audit_predictor_summary.json").exists()


def test_refresh_complete_review_writes_predictor_aggregate(tmp_path: Path) -> None:
    payload, output_dir = run_refresh(tmp_path, reviewed=True, model_reviewed=True)

    assert payload["ok"] is True
    assert payload["status"] == "review_complete"
    assert payload["reviewed_rows"] == 1
    assert payload["reviewed_model_assessments"] == 1
    predictor_payload = json.loads(
        (output_dir / "human_audit_predictor_summary.json").read_text(encoding="utf-8")
    )
    assert predictor_payload["status"] == "review_complete"
    assert predictor_payload["pending_model_assessments"] == 0


def test_refresh_updates_publishable_completion_audit(tmp_path: Path) -> None:
    load_readiness_fixture_writer()(tmp_path)
    sheet = tmp_path / "audit.tsv"
    output_dir = (
        tmp_path
        / "70_experiments"
        / "runs"
        / "janus_300_high_stakes_human_audit_selection_2026_05_25"
    )
    readiness_dir = (
        tmp_path / "70_experiments" / "runs" / "postdoc_evidence_chain_2026_05_25"
    )
    write_rows(sheet, [base_row(reviewed=False, model_reviewed=False)])

    payload = refresh_human_audit_evidence(
        audit_sheet=sheet,
        output_dir=output_dir,
        readiness_output_dir=readiness_dir,
        repo_root=tmp_path,
        expected_rows=1,
        require_complete=False,
        skip_readiness=False,
    )
    completion_path = readiness_dir / "publishable_evidence_completion_summary.json"
    completion_payload = json.loads(completion_path.read_text(encoding="utf-8"))
    objective_5 = next(
        row
        for row in completion_payload["completion_rows"]
        if row["objective_id"] == "5"
    )

    assert payload["ok"] is True
    assert payload["completion_audit_ok"] is True
    assert payload["publishable_ready"] is False
    assert payload["completion_status_counts"]["review_pending"] == 1
    assert completion_path.exists()
    assert (readiness_dir / "publishable_evidence_completion.tsv").exists()
    assert objective_5["status"] == "review_pending"
    assert "0/1 rows" in objective_5["result"]
    assert "PRIVATE_" not in completion_path.read_text(encoding="utf-8")


def test_refresh_updates_roadmap_completion_audit(tmp_path: Path) -> None:
    load_readiness_fixture_writer()(tmp_path)
    sheet = tmp_path / "audit.tsv"
    output_dir = (
        tmp_path
        / "70_experiments"
        / "runs"
        / "janus_300_high_stakes_human_audit_selection_2026_05_25"
    )
    readiness_dir = (
        tmp_path / "70_experiments" / "runs" / "postdoc_evidence_chain_2026_05_25"
    )
    write_rows(sheet, [base_row(reviewed=False, model_reviewed=False)])

    payload = refresh_human_audit_evidence(
        audit_sheet=sheet,
        output_dir=output_dir,
        readiness_output_dir=readiness_dir,
        repo_root=tmp_path,
        expected_rows=1,
        require_complete=False,
        skip_readiness=False,
    )
    roadmap_path = readiness_dir / "postdoc_roadmap_completion_summary.json"
    roadmap_payload = json.loads(roadmap_path.read_text(encoding="utf-8"))

    assert payload["ok"] is True
    assert payload["roadmap_audit_ok"] is True
    assert payload["roadmap_complete"] is False
    assert payload["roadmap_status_counts"]["blocked"] == 1
    assert roadmap_payload["roadmap_complete"] is False
    assert roadmap_payload["blocking_gate"] == "selected_300_human_review_and_post_review_refresh"
    assert (readiness_dir / "postdoc_roadmap_completion.tsv").exists()
    assert "PRIVATE_" not in roadmap_path.read_text(encoding="utf-8")


def test_refresh_updates_post_review_evidence_checklist(tmp_path: Path) -> None:
    load_readiness_fixture_writer()(tmp_path)
    sheet = tmp_path / "audit.tsv"
    output_dir = (
        tmp_path
        / "70_experiments"
        / "runs"
        / "janus_300_high_stakes_human_audit_selection_2026_05_25"
    )
    readiness_dir = (
        tmp_path / "70_experiments" / "runs" / "postdoc_evidence_chain_2026_05_25"
    )
    write_rows(sheet, [base_row(reviewed=False, model_reviewed=False)])

    payload = refresh_human_audit_evidence(
        audit_sheet=sheet,
        output_dir=output_dir,
        readiness_output_dir=readiness_dir,
        repo_root=tmp_path,
        expected_rows=1,
        require_complete=False,
        skip_readiness=False,
    )
    post_review_path = output_dir / "human_audit_post_review_evidence_summary.json"
    post_review_payload = json.loads(post_review_path.read_text(encoding="utf-8"))

    assert payload["ok"] is True
    assert payload["post_review_evidence_ok"] is False
    assert payload["post_review_evidence_status"] == "post_review_evidence_blocked"
    assert "response_closeout_not_ready" in payload["post_review_blocker_keys"]
    assert "human_refresh_not_complete" in payload["post_review_blocker_keys"]
    assert post_review_payload["ok"] is False
    assert post_review_payload["status"] == "post_review_evidence_blocked"
    assert (output_dir / "human_audit_post_review_evidence_checklist.tsv").exists()
    assert "PRIVATE_" not in post_review_path.read_text(encoding="utf-8")

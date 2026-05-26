from __future__ import annotations

import importlib.util
import csv
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


def load_consistency_fixture_writer():
    path = REPO_ROOT / "tests" / "test_evidence_chain_consistency.py"
    spec = importlib.util.spec_from_file_location("test_evidence_chain_consistency", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.write_consistent_fixture


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")


def write_tsv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_objective_requirements_fixture_tree(root: Path) -> None:
    root.joinpath(".gitignore").write_text(
        "\n".join(
            [
                "*.wav",
                "*.safetensors",
                "50_janus_data_library/",
                "90_legacy_imports/",
                "70_experiments/runs/*/artifacts/",
                "70_experiments/runs/*/predictions/",
                "70_experiments/runs/*/models/",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    registry_ids = [
        "janus_old_train_legacy_import",
        "breeze_asr25_lora_legacy_best",
        "breeze_asr25_partial_encoder_legacy_best",
        "postdoc_evidence_chain_2026_05_25",
        "whisper_small_test_split",
        "whisper_large_v2_test_split",
        "breeze_asr25_base_test_split",
        "breeze_asr25_lora_legacy_best_test_split",
        "breeze_asr25_partial_encoder_legacy_best_test_split",
        "breeze_asr26_test_split",
    ]
    write_tsv(
        root / "70_experiments/registry.tsv",
        [{"run_id": run_id} for run_id in registry_ids],
        ["run_id"],
    )
    for run_id, model_kind in (
        ("breeze_asr25_lora_legacy_best_smoke", "lora"),
        ("breeze_asr25_partial_encoder_legacy_best_smoke", "partial_encoder"),
    ):
        write_json(
            root / f"70_experiments/runs/{run_id}/artifacts/{run_id}_summary.json",
            {
                "ok": True,
                "model_kind": model_kind,
                "runtime": "cuda",
                "torch_dtype": "float16",
                "disable_cudnn": True,
                "rows": 1,
                "wall_time_seconds": 1.25,
            },
        )
    validation_payload = {
        "ok": True,
        "files": [
            {
                "ok": True,
                "checks": {
                    "row_count_matches_expected_ids": True,
                    "audio_ids_match_expected_set": True,
                    "audio_ids_are_unique": True,
                    "audio_id_field_present": True,
                    "hypothesis_text_present": True,
                    "asr_label_present": True,
                    "quality_signal_present": True,
                },
                "counts": {"rows": 15, "expected_ids": 15},
            }
        ],
    }
    for run_id in (
        "breeze_asr25_lora_legacy_best_15_row",
        "breeze_asr25_partial_encoder_legacy_best_15_row",
    ):
        write_json(
            root / f"70_experiments/runs/{run_id}/artifacts/{run_id}_validation.json",
            validation_payload,
        )
    bridge_fields = [
        "run_id",
        "rows",
        "cer_mean",
        "wer_mean",
        "mean_ceis",
        "max_ceis",
        "downstream_mismatch_rate",
        "high_risk_missed_by_asr",
    ]
    bridge_row = {
        "rows": "15",
        "cer_mean": "10",
        "wer_mean": "20",
        "mean_ceis": "1",
        "max_ceis": "5",
        "downstream_mismatch_rate": "0.1",
        "high_risk_missed_by_asr": "1",
    }
    write_tsv(
        root / "70_experiments/runs/janus_15_decision_stability_legacy_best/asr_cds_model_comparison.tsv",
        [
            {"run_id": "breeze_asr25_15_row_baseline", **bridge_row},
            {"run_id": "breeze_asr25_lora_legacy_best_15_row", **bridge_row},
            {"run_id": "breeze_asr25_partial_encoder_legacy_best_15_row", **bridge_row},
        ],
        bridge_fields,
    )
    split_fields = [
        "run_id",
        "rows",
        "expected_rows",
        "cer_zh_micro",
        "wer_zh_jieba_micro",
        "risk_atom_error_rate",
        "negation_flip_rate",
        "amount_distortion_rate",
        "action_confusion_rate",
        "unsafe_downrouting_count",
        "high_risk_missed_count",
    ]
    split_row = {
        "rows": "258",
        "expected_rows": "258",
        "cer_zh_micro": "1",
        "wer_zh_jieba_micro": "1",
        "risk_atom_error_rate": "0.1",
        "negation_flip_rate": "0.1",
        "amount_distortion_rate": "0.1",
        "action_confusion_rate": "0.1",
        "unsafe_downrouting_count": "1",
        "high_risk_missed_count": "1",
    }
    write_tsv(
        root / "70_experiments/runs/janus_258_test_split_asr_cds_proxy/asr_cds_proxy_comparison.tsv",
        [
            {"run_id": run_id, **split_row}
            for run_id in [
                "whisper_small_test_split",
                "whisper_large_v2_test_split",
                "breeze_asr25_base_test_split",
                "breeze_asr25_lora_legacy_best_test_split",
                "breeze_asr25_partial_encoder_legacy_best_test_split",
                "breeze_asr26_test_split",
            ]
        ],
        split_fields,
    )
    write_json(
        root / "70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/summary.json",
        {
            "ok": True,
            "split": "high_stakes_300",
            "review_mode": "proxy",
            "reference_rows": 300,
            "model_samples": 900,
            "ceis": {"unstable_samples": 35},
        },
    )
    write_json(
        root / "70_experiments/runs/janus_300_high_stakes_metric_predictor_proxy_2026_05_25/metric_predictor_summary.json",
        {
            "ok": True,
            "model_sample_count": 900,
            "best_overall_predictors_by_auc": {
                "unsafe_downrouting": {"auc": 0.9, "metric": "ceis_max"}
            },
            "low_wer_summary": [{"rows": 900}],
        },
    )
    policy = {
        "critical_miss_count": 0,
        "critical_miss_rate": 0.0,
        "unsafe_downrouting_count": 0,
        "unsafe_downrouting_rate": 0.0,
        "over_escalation_count": 0,
        "over_escalation_rate": 0.0,
        "machine_abstention_count": 0,
        "machine_abstention_rate": 0.0,
        "recovery_budget_rate": 0.0,
        "high_risk_missed_gain": 0.0,
        "unsafe_downrouting_gain": 0.0,
    }
    write_json(
        root / "70_experiments/runs/janus_300_high_stakes_recovery_proxy_2026_05_25/summary.json",
        {
            "ok": True,
            "policies": {
                "no_recovery": {
                    **policy,
                    "critical_miss_count": 1,
                    "unsafe_downrouting_count": 2,
                    "high_risk_missed_count": 6,
                },
                "confidence_only_trigger": policy,
                "sres_triggered_recovery": {
                    **policy,
                    "high_risk_missed_gain": 1.0,
                    "unsafe_downrouting_gain": 0.5,
                },
                "ceis_triggered_conservative_action": {
                    **policy,
                    "critical_miss_count": 0,
                    "high_risk_missed_count": 0,
                    "high_risk_missed_gain": 1.0,
                    "unsafe_downrouting_gain": 0.5,
                },
                "ceis_ensemble_arbitration": {
                    **policy,
                    "machine_abstention_count": 1,
                    "machine_abstention_rate": 0.1,
                },
            },
        },
    )


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
    load_consistency_fixture_writer()(tmp_path)
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
    load_consistency_fixture_writer()(tmp_path)
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
    load_consistency_fixture_writer()(tmp_path)
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
    assert payload["human_recovery_status"] == "review_pending"
    assert payload["human_recovery_evidence_mode"] == "human_reviewed_pending"
    assert payload["human_recovery_ready"] is False
    assert post_review_payload["ok"] is False
    assert post_review_payload["status"] == "post_review_evidence_blocked"
    assert post_review_payload["human_recovery_status"] == "review_pending"
    assert post_review_payload["human_recovery_evidence_mode"] == "human_reviewed_pending"
    assert (output_dir / "human_audit_post_review_evidence_checklist.tsv").exists()
    assert (
        tmp_path
        / "70_experiments"
        / "runs"
        / "janus_300_high_stakes_recovery_human_reviewed_2026_05_26"
        / "summary.json"
    ).exists()
    assert "PRIVATE_" not in post_review_path.read_text(encoding="utf-8")


def test_refresh_updates_evidence_chain_consistency_audit(tmp_path: Path) -> None:
    load_readiness_fixture_writer()(tmp_path)
    load_consistency_fixture_writer()(tmp_path)
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
    consistency_path = readiness_dir / "evidence_chain_consistency_summary.json"
    consistency_payload = json.loads(consistency_path.read_text(encoding="utf-8"))

    assert payload["ok"] is True
    assert payload["review_work_order_status"] == "review_work_order_ready"
    assert payload["review_work_order_overview"]["total_action_items"] == 126
    assert payload["post_review_sequence_status"] == "post_review_sequence_blocked"
    assert "strict_dry_run" in payload["post_review_sequence_blocker_keys"]
    assert payload["post_review_sequence_executed_step_count"] == 0
    assert payload["consistency_audit_ok"] is True
    assert payload["operation_record_audit_ok"] is True
    assert payload["operation_record_status"] == "operation_records_ready"
    assert payload["operation_record_failed_count"] == 0
    assert payload["consistency_status_counts"] == {"pass": 26}
    assert payload["consistency_failed_checks"] == []
    assert consistency_payload["ok"] is True
    assert (readiness_dir / "evidence_chain_consistency.tsv").exists()
    assert (output_dir / "human_audit_review_work_order.tsv").exists()
    assert (output_dir / "human_audit_post_review_sequence.tsv").exists()
    assert "PRIVATE_" not in consistency_path.read_text(encoding="utf-8")


def test_refresh_updates_original_objective_requirements_audit(tmp_path: Path) -> None:
    load_readiness_fixture_writer()(tmp_path)
    load_consistency_fixture_writer()(tmp_path)
    write_objective_requirements_fixture_tree(tmp_path)
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
    objective_path = readiness_dir / "postdoc_objective_requirements_summary.json"
    objective_payload = json.loads(objective_path.read_text(encoding="utf-8"))

    assert payload["ok"] is True
    assert payload["objective_requirements_audit_ok"] is True
    assert payload["objective_requirements_ready"] is False
    assert payload["objective_requirements_status_counts"] == {
        "satisfied": 8,
        "proxy_satisfied": 5,
        "review_pending": 2,
    }
    assert payload["objective_requirements_proxy_count"] == 5
    assert payload["objective_requirements_blocking_count"] == 2
    assert objective_payload["objective_requirements_ready"] is False
    assert objective_payload["status_counts"]["review_pending"] == 2
    assert (readiness_dir / "postdoc_objective_requirements.tsv").exists()
    assert any(
        item.endswith("postdoc_objective_requirements_summary.json")
        for item in payload["outputs"]
    )
    assert "PRIVATE_" not in objective_path.read_text(encoding="utf-8")

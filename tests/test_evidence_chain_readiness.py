from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "scoring"))

from check_evidence_chain_readiness import (  # noqa: E402
    assert_aggregate_safe,
    build_readiness,
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")


def write_tsv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_minimal_tree(root: Path) -> None:
    write_tsv(
        root / "70_experiments/registry.tsv",
        [
            {"run_id": "janus_old_train_legacy_import"},
            {"run_id": "breeze_asr25_lora_legacy_best"},
            {"run_id": "breeze_asr25_partial_encoder_legacy_best"},
            {"run_id": "postdoc_evidence_chain_2026_05_25"},
        ],
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
                "run_id": run_id,
                "model_kind": model_kind,
                "rows": 1,
                "runtime": "cuda",
                "torch_dtype": "float16",
                "disable_cudnn": True,
            },
        )
    validation_payload = {
        "ok": True,
        "files": [
            {
                "counts": {"rows": 15},
                "checks": {
                    "row_count_matches_expected_ids": True,
                    "audio_ids_match_expected_set": True,
                    "audio_ids_are_unique": True,
                    "audio_id_field_present": True,
                    "hypothesis_text_present": True,
                    "asr_label_present": True,
                    "quality_signal_present": True,
                },
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
    write_tsv(
        root / "70_experiments/runs/janus_15_decision_stability_legacy_best/asr_cds_model_comparison.tsv",
        [
            {"run_id": "breeze_asr25_15_row_baseline"},
            {"run_id": "breeze_asr25_lora_legacy_best_15_row"},
            {"run_id": "breeze_asr25_partial_encoder_legacy_best_15_row"},
        ],
        ["run_id"],
    )
    write_json(
        root / "70_experiments/runs/janus_258_test_split_asr_cds_proxy/summary.json",
        {"ok": True},
    )
    test_split_fields = [
        "run_id",
        "risk_atom_error_rate",
        "negation_flip_rate",
        "amount_distortion_rate",
        "action_confusion_rate",
        "unsafe_downrouting_count",
        "high_risk_missed_count",
    ]
    write_tsv(
        root / "70_experiments/runs/janus_258_test_split_asr_cds_proxy/asr_cds_proxy_comparison.tsv",
        [
            {field: "1" for field in test_split_fields} | {"run_id": run_id}
            for run_id in [
                "whisper_small_test_split",
                "whisper_large_v2_test_split",
                "breeze_asr25_base_test_split",
                "breeze_asr25_lora_legacy_best_test_split",
                "breeze_asr25_partial_encoder_legacy_best_test_split",
                "breeze_asr26_test_split",
            ]
        ],
        test_split_fields,
    )
    for name in ("legacy_15_row_summary", "summary", "high_stakes_300_summary"):
        write_json(
            root / f"70_experiments/runs/wer_metric_audit_2026_05_25/{name}.json",
            {
                "ok": True,
                "summaries": [
                    {
                        "zero_reference_unit_rows": {
                            "cer_raw_char": 0,
                            "wer_raw_whitespace": 0,
                            "cer_zh_normalized": 0,
                            "wer_zh_jieba": 0,
                        }
                    }
                ],
            },
        )
    write_json(
        root / "70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/summary.json",
        {
            "ok": True,
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
                "unsafe_downrouting": {"metric": "ceis_max"}
            },
        },
    )
    write_json(
        root / "70_experiments/runs/janus_300_high_stakes_recovery_proxy_2026_05_25/summary.json",
        {
            "ok": True,
            "policies": {
                "no_recovery": {"critical_miss_count": 1, "high_risk_missed_count": 6},
                "confidence_only_trigger": {},
                "sres_triggered_recovery": {},
                "ceis_triggered_conservative_action": {
                    "critical_miss_count": 0,
                    "high_risk_missed_count": 0,
                },
                "ceis_ensemble_arbitration": {},
            },
        },
    )
    write_json(
        root / "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_validation_summary.json",
        {
            "ok": True,
            "status": "review_pending",
            "reviewed_rows": 0,
            "reviewed_model_assessments": 0,
        },
    )
    write_json(
        root
        / "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_reviewer_action_checklist_summary.json",
        {
            "ok": True,
            "status": "reviewer_action_ready",
            "selection_stratum": "critical_or_high_risk_missed",
            "rows_in_batch": 6,
            "pending_rows_in_batch": 6,
            "model_assessments_in_batch": 18,
            "pending_model_assessments_in_batch": 18,
            "rows_missing_timing": 6,
            "latest_apply_status": "response_pending",
        },
    )


def test_readiness_marks_proxy_and_human_review_pending(tmp_path: Path) -> None:
    write_minimal_tree(tmp_path)

    payload = build_readiness(tmp_path)
    statuses = {row["requirement"]: row["status"] for row in payload["readiness_rows"]}

    assert payload["ok"] is True
    assert payload["paper_ready"] is False
    assert statuses["selected-300 human risk-atom audit completion"] == "review_pending"
    assert statuses["five-condition recovery experiment"] == "proxy_completed"
    assert payload["status_counts"]["review_pending"] == 1
    assert payload["status_counts"]["proxy_completed"] == 4
    assert payload["reviewer_action_gate"]["status"] == "reviewer_action_ready"
    assert payload["reviewer_action_gate"]["pending_rows_in_batch"] == 6
    assert payload["reviewer_action_gate"]["rows_missing_timing"] == 6
    assert "already human-reviewed ground truth" in payload["reference_transcript_policy"]
    assert "risk-atom labels" in payload["remaining_review_scope"]
    assert "per-row review timing" in payload["remaining_review_scope"]
    audit_row = next(
        row
        for row in payload["readiness_rows"]
        if row["requirement"] == "selected-300 human risk-atom audit completion"
    )
    assert "transcript ground truth is not the pending item" in audit_row["result"]
    assert "reviewer_action_ready" in audit_row["result"]
    assert "6/6 timing rows pending" in audit_row["result"]
    assert "--require-timing" in audit_row["next_action"]
    assert "per-row timing fields" in payload["next_decision"]
    assert_aggregate_safe(payload)


def test_aggregate_safety_rejects_private_fields() -> None:
    try:
        assert_aggregate_safe({"bad": "reference_text"})
    except ValueError as exc:
        assert "sensitive token" in str(exc)
    else:
        raise AssertionError("sensitive field did not fail")


def test_readiness_treats_partial_human_review_as_in_progress(tmp_path: Path) -> None:
    write_minimal_tree(tmp_path)
    write_json(
        tmp_path
        / "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_validation_summary.json",
        {
            "ok": True,
            "status": "partial_review",
            "reviewed_rows": 1,
            "reviewed_model_assessments": 3,
        },
    )

    payload = build_readiness(tmp_path)
    audit_row = next(
        row
        for row in payload["readiness_rows"]
        if row["requirement"] == "selected-300 human risk-atom audit completion"
    )

    assert payload["ok"] is True
    assert payload["paper_ready"] is False
    assert audit_row["status"] == "partial_review"
    assert "1/30 selected rows" in audit_row["result"]

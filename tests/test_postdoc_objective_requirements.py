from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "scoring"))

from audit_postdoc_objective_requirements import (  # noqa: E402
    REQUIRED_258_COLUMNS,
    assert_requirement_audit_safe,
    build_objective_requirement_audit_from_payloads,
)


def registry_rows() -> list[dict[str, str]]:
    run_ids = [
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
    return [{"run_id": run_id} for run_id in run_ids]


def gitignore_text() -> str:
    return "\n".join(
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


def smoke(model_kind: str) -> dict:
    return {
        "ok": True,
        "model_kind": model_kind,
        "runtime": "cuda",
        "torch_dtype": "float16",
        "disable_cudnn": True,
        "rows": 1,
        "wall_time_seconds": 1.25,
    }


def validation() -> dict:
    return {
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
                "counts": {
                    "rows": 15,
                    "expected_ids": 15,
                },
            }
        ],
    }


def bridge_rows() -> list[dict[str, str]]:
    fields = {
        "rows": "15",
        "cer_mean": "10",
        "wer_mean": "20",
        "mean_ceis": "1",
        "max_ceis": "5",
        "downstream_mismatch_rate": "0.1",
        "high_risk_missed_by_asr": "1",
    }
    return [
        {"run_id": "breeze_asr25_lora_legacy_best_15_row", **fields},
        {"run_id": "breeze_asr25_partial_encoder_legacy_best_15_row", **fields},
    ]


def split_rows(include_required_columns: bool = True) -> list[dict[str, str]]:
    rows = []
    for run_id in [
        "whisper_small_test_split",
        "whisper_large_v2_test_split",
        "breeze_asr25_base_test_split",
        "breeze_asr25_lora_legacy_best_test_split",
        "breeze_asr25_partial_encoder_legacy_best_test_split",
        "breeze_asr26_test_split",
    ]:
        row = {
            "run_id": run_id,
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
        if not include_required_columns:
            row.pop("action_confusion_rate")
        rows.append(row)
    assert set(rows[0]).issubset(REQUIRED_258_COLUMNS) or not include_required_columns
    return rows


def recovery_summary(recovery_human_ready: bool = False) -> dict:
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
    policies = {
        "no_recovery": {
            **policy,
            "critical_miss_count": 1,
            "unsafe_downrouting_count": 2,
            "high_risk_missed_gain": 0.0,
        },
        "confidence_only_trigger": policy,
        "sres_triggered_recovery": {**policy, "high_risk_missed_gain": 1.0, "unsafe_downrouting_gain": 0.5},
        "ceis_triggered_conservative_action": {
            **policy,
            "critical_miss_count": 0,
            "high_risk_missed_gain": 1.0,
            "unsafe_downrouting_gain": 0.5,
        },
        "ceis_ensemble_arbitration": {**policy, "machine_abstention_count": 1, "machine_abstention_rate": 0.1},
    }
    return {"ok": True, "policies": policies, "recovery_human_ready": recovery_human_ready}


def base_payloads(**overrides: object) -> dict:
    payload = {
        "registry": registry_rows(),
        "gitignore_text": gitignore_text(),
        "lora_smoke": smoke("lora"),
        "partial_smoke": smoke("partial_encoder"),
        "lora_validation": validation(),
        "partial_validation": validation(),
        "bridge_15_rows": bridge_rows(),
        "split_258_rows": split_rows(),
        "high_stakes_summary": {
            "ok": True,
            "split": "high_stakes_300",
            "review_mode": "proxy",
            "reference_rows": 300,
            "model_samples": 900,
        },
        "predictor_summary": {
            "ok": True,
            "model_sample_count": 900,
            "best_overall_predictors_by_auc": {"unsafe_downrouting": {"auc": 0.9}},
            "low_wer_summary": [{"rows": 900}],
        },
        "recovery_summary": recovery_summary(),
        "human_refresh": {
            "ok": True,
            "status": "review_pending",
            "audit_rows": 30,
            "reviewed_rows": 0,
            "model_assessments": 90,
            "reviewed_model_assessments": 0,
            "pending_rows": 30,
            "pending_model_assessments": 90,
        },
        "human_predictor": {
            "ok": True,
            "status": "review_pending",
        },
        "post_review": {
            "recovery_human_ready": False,
        },
    }
    payload.update(overrides)
    return payload


def test_objective_requirement_audit_classifies_current_proxy_state() -> None:
    payload = build_objective_requirement_audit_from_payloads(**base_payloads())
    by_id = {row["requirement_id"]: row for row in payload["requirement_rows"]}

    assert payload["objective_requirements_ready"] is False
    assert by_id["0.1"]["status"] == "satisfied"
    assert by_id["1.1"]["status"] == "satisfied"
    assert by_id["2.2"]["status"] == "satisfied"
    assert by_id["4.1"]["status"] == "proxy_satisfied"
    assert by_id["5.3"]["status"] == "review_pending"
    assert by_id["6.3"]["status"] == "review_pending"
    assert payload["proxy_requirement_count"] == 5
    assert payload["blocking_requirement_count"] == 2
    assert "strict closeout" in payload["next_decision"]
    assert_requirement_audit_safe(payload)


def test_objective_requirement_audit_flags_missing_258_columns() -> None:
    payload = build_objective_requirement_audit_from_payloads(
        **base_payloads(split_258_rows=split_rows(include_required_columns=False))
    )
    by_id = {row["requirement_id"]: row for row in payload["requirement_rows"]}

    assert by_id["4.1"]["status"] == "missing"
    assert "action_confusion_rate" in by_id["4.1"]["result"]


def test_objective_requirement_audit_keeps_recovery_proxy_until_post_review() -> None:
    complete_refresh = {
        "ok": True,
        "status": "review_complete",
        "audit_rows": 30,
        "reviewed_rows": 30,
        "model_assessments": 90,
        "reviewed_model_assessments": 90,
        "pending_rows": 0,
        "pending_model_assessments": 0,
    }
    payload = build_objective_requirement_audit_from_payloads(
        **base_payloads(
            human_refresh=complete_refresh,
            human_predictor={"ok": True, "status": "review_complete"},
            post_review={"recovery_human_ready": False},
        )
    )
    by_id = {row["requirement_id"]: row for row in payload["requirement_rows"]}

    assert by_id["5.3"]["status"] == "satisfied"
    assert by_id["6.3"]["status"] == "review_pending"
    assert payload["objective_requirements_ready"] is False


def test_objective_requirement_audit_safety_rejects_private_tokens() -> None:
    try:
        assert_requirement_audit_safe({"bad": "reference_text"})
    except ValueError as exc:
        assert "sensitive token" in str(exc)
    else:
        raise AssertionError("private token did not fail")

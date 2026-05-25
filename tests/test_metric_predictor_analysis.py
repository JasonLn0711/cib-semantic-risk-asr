from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "scoring"))

from analyze_metric_predictors import (  # noqa: E402
    auc_roc,
    low_wer_rows,
    merged_samples,
    threshold_metrics,
)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def test_auc_roc_counts_ties_as_half() -> None:
    assert auc_roc([0.1, 0.5, 0.5, 0.9], [0, 1, 0, 1]) == 0.875


def test_threshold_metrics_prioritizes_recall_on_tied_f1() -> None:
    result = threshold_metrics([0.1, 0.2, 0.9], [1, 0, 1])

    assert result["best_threshold"] == 0.1
    assert result["recall"] == 1.0
    assert result["true_positive"] == 2


def test_merged_samples_marks_downstream_risk_and_low_wer_danger(tmp_path: Path) -> None:
    sres = tmp_path / "sres_scored.tsv"
    ceis = tmp_path / "ceis_scored.tsv"
    downstream = tmp_path / "downstream.tsv"
    write_text(
        sres,
        """
sample_id	split	asr_run_id	wer	cer	sres
case_001__run_a	test	run_a	5.0	2.0	0.0
case_002__run_a	test	run_a	15.0	9.0	25.0
""",
    )
    write_text(
        ceis,
        """
sample_id	variant_id	base_decision	variant_decision	risk_atom_type	decision_distance_used	ceis_component
case_001__run_a	v1	review	no_escalation	negation	1.0	5.0
case_002__run_a	v1	priority_review	priority_review	amount	0.0	0.0
""",
    )
    write_text(
        downstream,
        """
sample_id	reference_label	asr_label	recovered_label
case_001__run_a	priority_review	review	review
case_002__run_a	review	review	review
""",
    )

    samples = merged_samples(
        sres,
        ceis,
        downstream,
        ceis_threshold=5.0,
        sres_threshold=20.0,
    )

    assert len(samples) == 2
    first = next(sample for sample in samples if sample["sample_id"] == "case_001__run_a")
    assert first["unsafe_downrouting"] == 1
    assert first["high_risk_missed"] == 1
    assert first["danger_event"] == 1

    low_wer = low_wer_rows(
        samples,
        low_wer_threshold=10.0,
        ceis_threshold=5.0,
        sres_threshold=20.0,
    )
    overall = next(row for row in low_wer if row["asr_run_id"] == "ALL")
    assert overall["low_wer_rows"] == 1
    assert overall["low_wer_any_danger_count"] == 1

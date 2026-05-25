from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "annotation"))

from select_human_risk_atom_audit import (  # noqa: E402
    build_audio_candidates,
    load_model_samples,
    select_candidates,
    summary_payload,
    write_local_audit_sheet,
)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def test_selector_prefers_high_risk_and_summary_omits_ids(tmp_path: Path) -> None:
    sres = tmp_path / "sres.tsv"
    ceis = tmp_path / "ceis.tsv"
    downstream = tmp_path / "downstream.tsv"
    write_text(
        sres,
        """
sample_id	split	asr_run_id	reference_text	hypothesis_text	wer	cer	error_type	severity	downstream_impact	sres
audio_a__run_1	test	run_1	REF_A	HYP_A	5.0	2.0	negation	5	3	75.0
audio_b__run_1	test	run_1	REF_B	HYP_B	40.0	20.0	amount	1	0	0.0
audio_c__run_1	test	run_1	REF_C	HYP_C	2.0	1.0	action	0	0	0.0
""",
    )
    write_text(
        ceis,
        """
sample_id	variant_id	base_decision	variant_decision	risk_atom_type	decision_distance_used	ceis_component
audio_a__run_1	v1	review	no_escalation	negation	1.0	5.0
audio_b__run_1	v1	review	review	amount	0.0	0.0
audio_c__run_1	v1	review	review	action	0.0	0.0
""",
    )
    write_text(
        downstream,
        """
sample_id	reference_label	asr_label	recovered_label
audio_a__run_1	priority_review	review	review
audio_b__run_1	review	review	review
audio_c__run_1	review	review	review
""",
    )

    samples = load_model_samples(sres, ceis, downstream)
    candidates = build_audio_candidates(
        samples,
        low_wer_threshold=10.0,
        sres_threshold=20.0,
        ceis_threshold=5.0,
    )
    selected = select_candidates(
        candidates,
        audit_size=2,
        quotas={
            "critical_or_high_risk_missed": 1,
            "unsafe_downrouting": 1,
            "low_wer_danger": 0,
            "high_proxy_risk": 0,
            "model_disagreement": 0,
            "clean_control": 0,
        },
    )

    assert selected[0].audio_id == "audio_a"
    assert selected[0].flags["high_risk_missed"]
    payload = summary_payload(
        args=type(
            "Args",
            (),
            {
                "sres_scored": sres,
                "ceis_scored": ceis,
                "downstream_decisions": downstream,
                "output_dir": tmp_path,
                "low_wer_threshold": 10.0,
                "sres_threshold": 20.0,
                "ceis_threshold": 5.0,
            },
        )(),
        candidates=candidates,
        selected=selected,
        started=0.0,
    )
    summary_text = json.dumps(payload, ensure_ascii=False)

    assert "audio_a" not in summary_text
    assert "REF_A" not in summary_text
    assert payload["selected_audio_count"] == 2

    sheet = tmp_path / "audit.tsv"
    write_local_audit_sheet(sheet, selected)
    sheet_text = sheet.read_text(encoding="utf-8")
    assert "reviewer_model_assessments_json" in sheet_text
    assert "reviewer_would_asr_error_change_decision" in sheet_text

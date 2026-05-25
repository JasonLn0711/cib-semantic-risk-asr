from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "80_semantic_risk_asr" / "scoring"))

from audit_asr_text_metrics import summarize  # noqa: E402


def write_jsonl(path: Path, rows: list[dict[str, str]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_audit_summary_flags_zero_reference_units(tmp_path: Path) -> None:
    hypotheses = tmp_path / "predictions.jsonl"
    write_jsonl(
        hypotheses,
        [
            {
                "audio_id": "case_001",
                "asr_run_id": "run_a",
                "reference_text": "",
                "hypothesis_text": "測試",
            }
        ],
    )

    _, summary = summarize(
        hypotheses,
        reference_by_id={"case_001": ""},
        expected_ids={"case_001"},
    )

    assert summary["missing_expected_ids"] == []
    assert summary["extra_ids"] == []
    assert summary["zero_reference_unit_rows"]["cer_zh_normalized"] == 1
    assert summary["zero_reference_unit_rows"]["wer_zh_jieba"] == 1

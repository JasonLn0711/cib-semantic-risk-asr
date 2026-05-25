from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "60_whisper_asr_finetuning" / "scripts"))

from asr_text_metrics import compute_pair_metrics, edit_stats, units_for_metric  # noqa: E402


def test_zh_asr_preserves_traditional_chinese_without_spaces() -> None:
    reference = "請問您已經匯款到這個帳戶了嗎？"
    hypothesis = "請問您已經匯款到這個帳戶了嗎"

    metrics = compute_pair_metrics(reference, hypothesis)

    assert metrics["cer"] == 0.0
    assert metrics["wer"] == 0.0


def test_raw_whitespace_wer_is_legacy_for_unsegmented_chinese() -> None:
    reference = "我今天已經匯款"
    hypothesis = "我今天還沒匯款"

    raw_wer = edit_stats(
        reference,
        hypothesis,
        unit="word",
        normalization="none",
        wer_tokenizer="whitespace",
    )
    zh_cer = edit_stats(
        reference,
        hypothesis,
        unit="char",
        normalization="zh_asr",
        wer_tokenizer="jieba",
    )

    assert raw_wer.rate_percent == 100.0
    assert 0.0 < zh_cer.rate_percent < raw_wer.rate_percent


def test_jieba_units_can_be_cross_checked_with_jiwer() -> None:
    try:
        import jiwer
    except ImportError:
        return

    references = ["民眾已經匯款三萬元", "請幫我查詢帳戶"]
    hypotheses = ["民眾已經轉帳三萬元", "請幫我查詢帳戶"]
    ref_token_lines = [
        " ".join(units_for_metric(text, unit="word", wer_tokenizer="jieba"))
        for text in references
    ]
    hyp_token_lines = [
        " ".join(units_for_metric(text, unit="word", wer_tokenizer="jieba"))
        for text in hypotheses
    ]
    repo_edits = 0
    repo_ref_units = 0
    for reference, hypothesis in zip(references, hypotheses):
        stats = edit_stats(reference, hypothesis, unit="word", wer_tokenizer="jieba")
        repo_edits += stats.edits
        repo_ref_units += stats.reference_units

    assert round(repo_edits / repo_ref_units, 12) == round(
        jiwer.wer(ref_token_lines, hyp_token_lines),
        12,
    )

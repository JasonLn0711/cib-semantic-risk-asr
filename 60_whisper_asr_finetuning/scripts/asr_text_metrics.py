#!/usr/bin/env python3
"""ASR text metric helpers with explicit normalization and tokenization."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

import editdistance


NORMALIZATION_MODES = ("none", "zh_asr")
WER_TOKENIZERS = ("whitespace", "jieba")


@dataclass(frozen=True)
class EditStats:
    edits: int
    reference_units: int
    rate_percent: float


def normalize_for_metric(text: str, mode: str = "zh_asr") -> str:
    """Normalize text for ASR metrics without traditional/simplified conversion."""

    if mode not in NORMALIZATION_MODES:
        raise ValueError(f"unsupported normalization mode: {mode}")
    if mode == "none":
        return text
    normalized = unicodedata.normalize("NFKC", text).lower()
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", normalized)


def units_for_metric(
    text: str,
    *,
    unit: str,
    normalization: str = "zh_asr",
    wer_tokenizer: str = "jieba",
) -> list[str]:
    normalized = normalize_for_metric(text, normalization)
    if unit == "char":
        return list(normalized)
    if unit != "word":
        raise ValueError(f"unsupported metric unit: {unit}")
    if wer_tokenizer == "whitespace":
        return normalized.split()
    if wer_tokenizer == "jieba":
        import jieba

        return [token for token in jieba.cut(normalized) if token.strip()]
    raise ValueError(f"unsupported WER tokenizer: {wer_tokenizer}")


def edit_stats(
    reference: str,
    prediction: str,
    *,
    unit: str,
    normalization: str = "zh_asr",
    wer_tokenizer: str = "jieba",
) -> EditStats:
    ref_units = units_for_metric(
        reference,
        unit=unit,
        normalization=normalization,
        wer_tokenizer=wer_tokenizer,
    )
    pred_units = units_for_metric(
        prediction,
        unit=unit,
        normalization=normalization,
        wer_tokenizer=wer_tokenizer,
    )
    denominator = max(len(ref_units), 1)
    edits = editdistance.eval(ref_units, pred_units)
    return EditStats(
        edits=edits,
        reference_units=denominator,
        rate_percent=round(edits / denominator * 100.0, 2),
    )


def compute_pair_metrics(
    reference: str,
    prediction: str,
    *,
    normalization: str = "zh_asr",
    wer_tokenizer: str = "jieba",
) -> dict[str, float]:
    """Return paper-facing metrics plus legacy raw metrics for auditability."""

    cer = edit_stats(
        reference,
        prediction,
        unit="char",
        normalization=normalization,
        wer_tokenizer=wer_tokenizer,
    )
    wer = edit_stats(
        reference,
        prediction,
        unit="word",
        normalization=normalization,
        wer_tokenizer=wer_tokenizer,
    )
    cer_raw = edit_stats(
        reference,
        prediction,
        unit="char",
        normalization="none",
        wer_tokenizer="whitespace",
    )
    wer_raw = edit_stats(
        reference,
        prediction,
        unit="word",
        normalization="none",
        wer_tokenizer="whitespace",
    )
    return {
        "cer": cer.rate_percent,
        "wer": wer.rate_percent,
        "cer_raw": cer_raw.rate_percent,
        "wer_raw_whitespace": wer_raw.rate_percent,
    }

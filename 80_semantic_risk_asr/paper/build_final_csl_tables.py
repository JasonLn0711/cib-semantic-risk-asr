#!/usr/bin/env python3
"""Build manuscript tables from final CSL aggregate outputs."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "70_experiments/runs/janus_300_high_stakes_final_csl_2026_06_03"
TABLE_DIR = ROOT / "80_semantic_risk_asr/paper/tables"


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def esc(value: object) -> str:
    text = str(value)
    replacements = {
        "_": r"\_",
        "%": r"\%",
        "&": r"\&",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


def fmt_float(value: str, digits: int = 3) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except ValueError:
        return value


def metric_label(metric: str) -> str:
    return {
        "wer": "WER",
        "cer": "CER",
        "sres_total": "SRES",
        "ceis_max": "CEIS",
        "max_norm_sres_ceis": "max(SRES, CEIS)",
        "rank_fusion_sres_ceis": "Rank fusion",
        "variant_count_only": "Variant count",
        "ceis_top1_capped": "CEIS capped",
    }.get(metric, metric)


def build_predictor() -> None:
    rows = [
        row
        for row in read_tsv(RUN / "final_csl_predictor_performance.tsv")
        if row["target"] == "decision_change_yes"
        and row["metric"] in {"wer", "cer", "sres_total", "ceis_max", "max_norm_sres_ceis"}
    ]
    order = ["wer", "cer", "sres_total", "ceis_max", "max_norm_sres_ceis"]
    rows = sorted(rows, key=lambda row: order.index(row["metric"]))
    lines = [
        r"\begin{table}[!htbp]",
        r"\centering",
        r"\caption{Final 300/900 predictor performance against deterministic dual-reviewer decision-change labels. Unit: model assessments clustered within 300 audio rows; primary endpoint uses the decision-change failover because row-level severe positives are 6.}",
        r"\label{tab:predictor}",
        r"\footnotesize",
        r"\begin{tabularx}{\linewidth}{@{}L{1.10}R{0.75}R{0.75}R{0.75}R{0.75}R{0.75}R{0.75}R{0.65}L{1.25}@{}}",
        r"\toprule",
        r"Predictor & AUC & Threshold & Best F1 & Precision & Recall & FN & Positives & Role \\",
        r"\midrule",
    ]
    roles = {
        "wer": "Surface baseline",
        "cer": "Chinese surface baseline",
        "sres_total": "Semantic-risk baseline",
        "ceis_max": "Decision-stability layer",
        "max_norm_sres_ceis": "Fusion baseline",
    }
    for row in rows:
        lines.append(
            " & ".join(
                [
                    metric_label(row["metric"]),
                    fmt_float(row["auc"]),
                    fmt_float(row["best_threshold"]),
                    fmt_float(row["best_f1"]),
                    fmt_float(row["precision"]),
                    fmt_float(row["recall"]),
                    row["false_negative"],
                    row["positive_count"],
                    roles[row["metric"]],
                ]
            )
            + r" \\"
        )
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabularx}",
            r"\\[0.4em]{\footnotesize\RaggedRight Thresholds are diagnostic operating points selected on the scoped reviewed audit, not deployment thresholds. SRES has the strongest thresholded F1 in this table; CEIS is retained as a scoped decision-stability layer and fusion input rather than a total-superiority claim.\par}",
            r"\end{table}",
        ]
    )
    (TABLE_DIR / "table3_predictor.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def frontier_rows(metrics: set[str], budgets: set[str]) -> list[dict[str, str]]:
    rows = [
        row
        for row in read_tsv(RUN / "final_csl_fixed_budget_frontier_row_level.tsv")
        if row["scope"] == "all"
        and row["score_metric"] in metrics
        and row["budget_target_rate"] in budgets
    ]
    order_metric = {
        "sres_total": 0,
        "ceis_max": 1,
        "max_norm_sres_ceis": 2,
        "variant_count_only": 3,
        "ceis_top1_capped": 4,
    }
    return sorted(rows, key=lambda row: (order_metric[row["score_metric"]], row["budget_target_rate"]))


def build_recovery() -> None:
    rows = frontier_rows({"sres_total", "ceis_max", "max_norm_sres_ceis", "variant_count_only"}, {"0.1000", "0.2000"})
    lines = [
        r"\begin{table}[!htbp]",
        r"\centering",
        r"\caption{Row-level fixed-budget conservative replay on the final selected-300 audit surface.}",
        r"\label{tab:recovery}",
        r"\footnotesize",
        r"\begin{tabularx}{\linewidth}{@{}L{1.10}R{0.65}R{0.70}R{0.70}R{0.70}R{0.70}R{0.70}R{0.80}L{1.10}@{}}",
        r"\toprule",
        r"Metric & Budget & Triggered & Severe rem. & Severe elim. & Unsafe rem. & Critical rem. & Tie worst & Role \\",
        r"\midrule",
    ]
    roles = {
        "sres_total": "Semantic-risk replay",
        "ceis_max": "CEIS replay",
        "max_norm_sres_ceis": "Fusion replay",
        "variant_count_only": "Count stress test",
    }
    for row in rows:
        lines.append(
            " & ".join(
                [
                    metric_label(row["score_metric"]),
                    f"{float(row['budget_target_rate']) * 100:.0f}\\%",
                    row["triggered_rows"],
                    row["row_severe_miss_remaining"],
                    row["row_severe_misses_eliminated"],
                    row["row_unsafe_downrouting_remaining"],
                    row["row_critical_miss_remaining"],
                    row["tie_worst_case_severe_remaining"],
                    roles[row["score_metric"]],
                ]
            )
            + r" \\"
        )
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabularx}",
            r"\\[0.4em]{\footnotesize\RaggedRight The severe-miss baseline is 6 rows, so replay is descriptive high-severity evidence after the pre-declared failover to decision-change prediction. Variant-count-only is included as a stress test for max-over-variants behavior.\par}",
            r"\end{table}",
        ]
    )
    (TABLE_DIR / "table4_recovery.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_frontier() -> None:
    rows = frontier_rows({"sres_total", "ceis_max", "max_norm_sres_ceis", "variant_count_only", "ceis_top1_capped"}, {"0.1000", "0.2000", "0.3000", "0.4000"})
    lines = [
        r"\begin{table}[!htbp]",
        r"\centering",
        r"\caption{Final row-level fixed-budget conservative replay frontier.}",
        r"\label{tab:a1-frontier}",
        r"\footnotesize",
        r"\begin{tabularx}{\linewidth}{@{}L{0.95}R{0.55}R{0.65}R{0.65}R{0.65}R{0.65}R{0.75}R{0.80}R{0.80}@{}}",
        r"\toprule",
        r"Metric & Budget & Triggers & Severe & Eliminated & Unsafe & Critical & Tie best & Tie worst \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(
            " & ".join(
                [
                    metric_label(row["score_metric"]),
                    f"{float(row['budget_target_rate']) * 100:.0f}\\%",
                    row["triggered_rows"],
                    row["row_severe_miss_remaining"],
                    row["row_severe_misses_eliminated"],
                    row["row_unsafe_downrouting_remaining"],
                    row["row_critical_miss_remaining"],
                    row["tie_best_case_severe_remaining"],
                    row["tie_worst_case_severe_remaining"],
                ]
            )
            + r" \\"
        )
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabularx}",
            r"\\[0.4em]{\footnotesize\RaggedRight Retrospective aggregate replay over 300 audio rows. Tied cutoff groups are reported as best/worst-case severe remaining; claims use the worst-case boundary.\par}",
            r"\end{table}",
        ]
    )
    (TABLE_DIR / "table_a1_fixed_budget_frontier.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    build_predictor()
    build_recovery()
    build_frontier()
    print("built final CSL tables")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

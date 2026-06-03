#!/usr/bin/env python3
"""Build final-CSL aggregate-only manuscript figures.

The historical R figure pipeline is retained for old aggregate artifacts, but
the final CSL manuscript needs figures sourced from the 2026-06-03 300/900
regeneration. This script intentionally uses only the Python standard library
and Pillow so it can run in the current local environment.
"""

from __future__ import annotations

import csv
from pathlib import Path
from html import escape

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
PAPER_DIR = ROOT / "80_semantic_risk_asr" / "paper"
FIG_DIR = PAPER_DIR / "figures"
RUN_DIR = ROOT / "70_experiments" / "runs" / "janus_300_high_stakes_final_csl_2026_06_03"

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

INK = (31, 41, 51)
MUTED = (82, 96, 109)
LIGHT = (245, 247, 250)
GRID = (217, 226, 236)
BLUE = (47, 128, 237)
GREEN = (33, 150, 83)
ORANGE = (242, 153, 74)
RED = (214, 69, 69)
PURPLE = (123, 97, 255)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(BOLD if bold else FONT, size)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def canvas(width: int = 1600, height: int = 900) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    return image, draw


def text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    value: str,
    size: int = 30,
    fill: tuple[int, int, int] = INK,
    bold: bool = False,
    anchor: str | None = None,
) -> None:
    draw.text(xy, value, font=font(size, bold), fill=fill, anchor=anchor)


def save_pdf(image: Image.Image, name: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    image.save(FIG_DIR / f"{name}.pdf", "PDF", resolution=180.0)
    image.save(FIG_DIR / f"{name}.png")


def save_text_svg(name: str, title: str, lines: list[str]) -> None:
    """Write a compact SVG companion so the figure package has no stale text."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    height = 140 + 34 * len(lines)
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="{height}" viewBox="0 0 1600 {height}">',
        '<rect width="1600" height="100%" fill="white"/>',
        f'<text x="70" y="70" font-family="DejaVu Sans, Arial, sans-serif" font-size="42" font-weight="700" fill="#1F2933">{escape(title)}</text>',
    ]
    y = 120
    for line in lines:
        svg.append(
            f'<text x="70" y="{y}" font-family="DejaVu Sans, Arial, sans-serif" font-size="25" fill="#52606D">{escape(line)}</text>'
        )
        y += 34
    svg.append("</svg>")
    (FIG_DIR / f"{name}.svg").write_text("\n".join(svg) + "\n", encoding="utf-8")


def scale(value: float, low: float, high: float, start: int, end: int) -> int:
    if high == low:
        return start
    return int(start + (value - low) / (high - low) * (end - start))


def fmt(x: float, digits: int = 3) -> str:
    return f"{x:.{digits}f}"


def metric_label(metric: str) -> str:
    return {
        "wer": "WER",
        "cer": "CER",
        "sres_total": "SRES",
        "ceis_max": "CEIS",
        "sres_ceis_max": "max(SRES, CEIS)",
        "variant_count": "Variant count",
    }.get(metric, metric)


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    value: str,
    width: int,
    size: int = 24,
    fill: tuple[int, int, int] = INK,
    bold: bool = False,
    line_gap: int = 8,
) -> int:
    words = value.split()
    lines: list[str] = []
    current = ""
    fnt = font(size, bold)
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if draw.textbbox((0, 0), candidate, font=fnt)[2] <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += size + line_gap
    return y


def make_f2_evidence_ladder() -> None:
    image, draw = canvas(1600, 620)
    text(draw, (70, 50), "Study evidence ladder and release boundary", 42, bold=True)
    steps = [
        ("ASR split", "audio rows", "258", "model-comparison context"),
        ("Selected provenance", "candidate rows", "300", "enriched audit surface"),
        ("Human-reviewed audit", "audio rows", "300", "dual-reviewer row labels"),
        ("Reviewed assessments", "model-row assessments", "900", "clustered within rows"),
    ]
    box_w, box_h = 320, 230
    y = 165
    for i, (name, unit, n, claim) in enumerate(steps):
        x = 70 + i * 380
        draw.rounded_rectangle((x, y, x + box_w, y + box_h), radius=12, fill="white", outline=INK, width=3)
        text(draw, (x + 28, y + 28), name, 28, bold=True)
        text(draw, (x + 28, y + 78), f"Unit: {unit}", 23, fill=MUTED)
        text(draw, (x + 28, y + 118), f"N = {n}", 36, bold=True, fill=BLUE if i >= 2 else INK)
        draw_wrapped(draw, (x + 28, y + 170), claim, box_w - 56, 22, fill=MUTED)
        if i < len(steps) - 1:
            draw.line((x + box_w + 22, y + box_h // 2, x + box_w + 62, y + box_h // 2), fill=INK, width=4)
            draw.polygon(
                [
                    (x + box_w + 62, y + box_h // 2),
                    (x + box_w + 48, y + box_h // 2 - 10),
                    (x + box_w + 48, y + box_h // 2 + 10),
                ],
                fill=INK,
            )
    note = "Cluster rule: 900 model assessments are clustered within 300 reviewed rows; row-level analysis is primary."
    draw.rounded_rectangle((300, 470, 1300, 540), radius=10, fill=LIGHT, outline=GRID, width=2)
    text(draw, (330, 490), note, 24, fill=INK)
    save_pdf(image, "figure2_evidence_ladder_redrawn")
    save_pdf(image, "f2_evidence_design")
    save_pdf(image, "f6_n_ladder")
    svg_lines = [
        "ASR split: 258 audio rows for model-comparison context.",
        "Selected provenance: 300 candidate rows for the enriched audit surface.",
        "Human-reviewed audit: 300 audio rows with dual-reviewer row labels.",
        "Reviewed assessments: 900 model-row assessments clustered within 300 rows.",
        "Primary analysis uses audio rows; model assessments are clustered secondary evidence.",
    ]
    for name in ["figure2_evidence_ladder_redrawn", "f2_evidence_design", "f2_evidence_boundary", "f6_n_ladder"]:
        save_text_svg(name, "Study evidence ladder and release boundary", svg_lines)


def make_f3_predictor() -> None:
    rows = [
        r
        for r in read_tsv(RUN_DIR / "final_csl_predictor_performance.tsv")
        if r["target"] == "decision_change_yes"
        and r["metric"] in {"wer", "cer", "sres_total", "ceis_max", "sres_ceis_max"}
    ]
    rows.sort(key=lambda r: ["wer", "cer", "sres_total", "ceis_max", "sres_ceis_max"].index(r["metric"]))
    image, draw = canvas(1600, 780)
    text(draw, (70, 48), "Decision-change prediction after full 300/900 regeneration", 40, bold=True)
    text(
        draw,
        (70, 98),
        "Rows are clustered by audio case; sparse severe positives trigger endpoint failover to decision-change AUC.",
        23,
        fill=MUTED,
    )
    left, right = 340, 1450
    top = 190
    for tick in [0.0, 0.25, 0.5, 0.75, 1.0]:
        x = scale(tick, 0, 1, left, right)
        draw.line((x, top - 20, x, top + 390), fill=GRID, width=2)
        text(draw, (x, top + 410), f"{tick:.2f}", 20, fill=MUTED, anchor="ma")
    for i, row in enumerate(rows):
        y = top + i * 82
        label = metric_label(row["metric"])
        auc = float(row["auc"])
        f1 = float(row["best_f1"])
        recall = float(row["recall"])
        fn = int(row["false_negative"])
        color = BLUE if label == "CEIS" else GREEN if label == "SRES" else PURPLE if label.startswith("max") else INK
        text(draw, (70, y - 15), label, 28, bold=True, fill=color)
        draw.line((left, y, right, y), fill=(235, 239, 244), width=2)
        x = scale(auc, 0, 1, left, right)
        draw.ellipse((x - 15, y - 15, x + 15, y + 15), fill=color, outline=INK)
        label_x = x + 24
        label_anchor = None
        if x > right - 255:
            label_x = x - 24
            label_anchor = "ra"
        text(draw, (label_x, y - 25), f"AUC {fmt(auc)}", 20, fill=INK, anchor=label_anchor)
        text(draw, (label_x, y + 1), f"F1 {fmt(f1)}", 20, fill=INK, anchor=label_anchor)
    text(draw, (left, top + 475), "AUC", 26, bold=True)
    text(draw, (70, 700), "Supported scope: CEIS is a decision-stability layer and fusion input; SRES has stronger thresholded F1.", 23, fill=MUTED)
    save_pdf(image, "f3_predictor_auc")
    save_text_svg(
        "f3_predictor_auc",
        "Decision-change prediction after full 300/900 regeneration",
        [
            "WER: AUC 0.811, F1 0.253.",
            "CER: AUC 0.832, F1 0.321.",
            "SRES: AUC 0.720, F1 0.453.",
            "CEIS: AUC 0.718, F1 0.407.",
            "max(SRES, CEIS): AUC 0.720, F1 0.453.",
            "Severe-miss positives are sparse, so the primary endpoint fails over to decision-change AUC.",
        ],
    )


def make_f4_recovery() -> None:
    frontier = read_tsv(RUN_DIR / "final_csl_fixed_budget_frontier_row_level.tsv")
    rows = [r for r in frontier if r["budget_target_rate"] in {"0.1000", "0.2000"} and r["score_metric"] in {"sres_total", "ceis_max", "sres_ceis_max", "variant_count"}]
    image, draw = canvas(1600, 900)
    text(draw, (70, 48), "Row-level conservative replay on selected-300", 42, bold=True)
    text(draw, (70, 98), "Descriptive high-severity replay after primary endpoint failover; trigger budgets are rows, not model assessments.", 24, fill=MUTED)
    left, top = 70, 175
    col_w = 355
    for i, metric in enumerate(["sres_total", "ceis_max", "sres_ceis_max", "variant_count"]):
        x = left + i * 380
        draw.rounded_rectangle((x, top, x + col_w, top + 575), radius=14, fill="white", outline=GRID, width=3)
        text(draw, (x + 22, top + 24), metric_label(metric), 28, bold=True, fill=BLUE if metric == "ceis_max" else GREEN if metric == "sres_total" else PURPLE if metric == "sres_ceis_max" else ORANGE)
        metric_rows = [r for r in rows if r["score_metric"] == metric]
        metric_rows.sort(key=lambda r: float(r["budget_target_rate"]))
        y = top + 82
        for row in metric_rows:
            budget = int(float(row["budget_target_rate"]) * 100)
            severe = int(row["row_severe_miss_remaining"])
            unsafe = int(row["row_unsafe_downrouting_remaining"])
            critical = int(row["row_critical_miss_remaining"])
            tie_worst = int(row["tie_worst_case_severe_remaining"])
            text(draw, (x + 22, y), f"{budget}% budget", 24, bold=True)
            draw.line((x + 22, y + 42, x + col_w - 22, y + 42), fill=GRID, width=2)
            text(draw, (x + 22, y + 64), f"Triggered rows: {row['triggered_rows']}", 22)
            text(draw, (x + 22, y + 102), f"Severe remaining: {severe}", 22, fill=RED if severe else GREEN)
            text(draw, (x + 22, y + 140), f"Unsafe remaining: {unsafe}", 22)
            text(draw, (x + 22, y + 178), f"Critical remaining: {critical}", 22)
            text(draw, (x + 22, y + 216), f"Tie worst-case severe: {tie_worst}", 22, fill=MUTED)
            y += 265
    text(draw, (70, 820), "Baseline: 6 row-level severe misses, 22 unsafe downrouting rows, and 1 critical miss. Variant-count is a stress test for max-over-variants behavior.", 23, fill=MUTED)
    save_pdf(image, "f4_recovery_outcomes")
    save_text_svg(
        "f4_recovery_outcomes",
        "Row-level conservative replay on selected-300",
        [
            "Budgets are selected rows, not model assessments.",
            "SRES, CEIS, and fusion capture the sparse severe rows at 10% and 20% row budgets in descriptive replay.",
            "Variant-count-only is retained as a max-over-variants stress test.",
            "Residual unsafe downrouting is an aggregate taxonomy question, not a solved deployment outcome.",
        ],
    )


def make_f7_frontier() -> None:
    rows = [
        r
        for r in read_tsv(RUN_DIR / "final_csl_fixed_budget_frontier_row_level.tsv")
        if r["score_metric"] in {"sres_total", "ceis_max", "sres_ceis_max", "variant_count"}
    ]
    image, draw = canvas(1600, 860)
    text(draw, (70, 48), "Fixed-budget row-level replay frontier", 42, bold=True)
    text(draw, (70, 98), "Budgets are selected-300 rows; claims use worst-case tie handling at score cutoffs.", 24, fill=MUTED)
    left, right, top, bottom = 150, 1450, 170, 690
    max_y = 6
    for yv in range(0, max_y + 1):
        y = scale(max_y - yv, 0, max_y, top, bottom)
        draw.line((left, y, right, y), fill=GRID, width=2)
        text(draw, (100, y - 12), str(yv), 22, fill=MUTED)
    for budget in [0.1, 0.2, 0.3, 0.4]:
        x = scale(budget, 0.1, 0.4, left, right)
        text(draw, (x, bottom + 35), f"{int(budget * 100)}%", 22, fill=MUTED, anchor="ma")
    colors = {"sres_total": GREEN, "ceis_max": BLUE, "sres_ceis_max": PURPLE, "variant_count": ORANGE}
    offsets = {"sres_total": -12, "ceis_max": 0, "sres_ceis_max": 12, "variant_count": 24}
    for metric in ["sres_total", "ceis_max", "sres_ceis_max", "variant_count"]:
        metric_rows = [r for r in rows if r["score_metric"] == metric]
        metric_rows.sort(key=lambda r: float(r["budget_target_rate"]))
        points: list[tuple[int, int]] = []
        for row in metric_rows:
            x = scale(float(row["budget_target_rate"]), 0.1, 0.4, left, right)
            y = scale(max_y - int(row["row_severe_miss_remaining"]), 0, max_y, top, bottom) + offsets[metric]
            points.append((x, y))
        for a, b in zip(points, points[1:]):
            draw.line((*a, *b), fill=colors[metric], width=5)
        for (x, y), row in zip(points, metric_rows):
            draw.ellipse((x - 12, y - 12, x + 12, y + 12), fill=colors[metric], outline=INK)
            text(draw, (x + 18, y - 12), row["row_severe_miss_remaining"], 20, fill=INK)
    legend_x = 1080
    for i, metric in enumerate(["sres_total", "ceis_max", "sres_ceis_max", "variant_count"]):
        y = 180 + i * 42
        draw.rectangle((legend_x, y, legend_x + 24, y + 24), fill=colors[metric])
        text(draw, (legend_x + 36, y - 3), metric_label(metric), 22)
    text(draw, (left, bottom + 92), "Row-level severe positives = 6; this frontier is descriptive stress testing, not deployment-threshold evidence.", 24, fill=MUTED)
    text(draw, (70, 415), "Severe rows remaining", 26, bold=True)
    text(draw, (left, bottom + 75), "Trigger budget", 26, bold=True)
    save_pdf(image, "f7_budget_risk_frontier")
    save_text_svg(
        "f7_budget_risk_frontier",
        "Fixed-budget row-level replay frontier",
        [
            "10%, 20%, 30%, and 40% budgets map to 30, 60, 90, and 120 selected rows.",
            "SRES, CEIS, and fusion have zero severe rows remaining in the final descriptive replay.",
            "Variant-count-only leaves 5 severe rows at 10% and 2 severe rows at 20%.",
            "Claims use worst-case tie handling at the score boundary.",
        ],
    )


def make_f10_atoms() -> None:
    rows = read_tsv(RUN_DIR / "final_csl_atom_linguistic_evidence.tsv")
    rows.sort(key=lambda r: float(r["decision_change_rate"]), reverse=True)
    image, draw = canvas(1600, 860)
    text(draw, (70, 48), "Risk-atom outcome evidence across final reviewed assessments", 40, bold=True)
    text(draw, (70, 98), "Aggregate atom-level table links decision-bearing spans to decision-change and severe-miss outcomes without releasing transcripts.", 23, fill=MUTED)
    left, right, top = 360, 1420, 180
    max_rate = max(float(r["decision_change_rate"]) for r in rows) or 1
    for tick in [0, 0.01, 0.02, 0.03, 0.04, 0.05]:
        x = scale(tick, 0, 0.05, left, right)
        draw.line((x, top - 25, x, top + 430), fill=GRID, width=2)
        text(draw, (x, top + 455), f"{tick * 100:.0f}%", 20, fill=MUTED, anchor="ma")
    for i, row in enumerate(rows):
        y = top + i * 78
        atom = row["atom_type"].replace("_", " ")
        rate = float(row["decision_change_rate"])
        severe = int(row["severe_miss_count"])
        count = int(row["model_assessment_count"])
        x = scale(rate, 0, max(0.05, max_rate), left, right)
        text(draw, (70, y - 16), atom, 25, bold=True)
        draw.line((left, y, x, y), fill=BLUE, width=8)
        draw.ellipse((x - 14, y - 14, x + 14, y + 14), fill=BLUE, outline=INK)
        text(draw, (x + 24, y - 15), f"{int(row['decision_change_positive_count'])}/{count} change | severe {severe}", 22)
    text(draw, (left, top + 510), "Decision-change rate", 25, bold=True)
    text(draw, (70, 785), "Current aggregate source coverage is proxy-level; source-specific Mandarin shares remain a final validation extension where logs are unavailable.", 22, fill=MUTED)
    save_pdf(image, "f10_human_reviewed_atom_outcomes")
    save_text_svg(
        "f10_human_reviewed_atom_outcomes",
        "Risk-atom outcome evidence across final reviewed assessments",
        [
            "Negation: 405 model assessments, 10 decision-change positives, 4 severe misses.",
            "Amount: 342 model assessments, 11 decision-change positives, 2 severe misses.",
            "Action: 122 model assessments, 5 decision-change positives.",
            "Actor: 31 model assessments, no decision-change positives in the current aggregate table.",
            "This figure is aggregate-only and releases no transcript text or row identifiers.",
        ],
    )


def main() -> None:
    make_f2_evidence_ladder()
    make_f3_predictor()
    make_f4_recovery()
    make_f7_frontier()
    make_f10_atoms()
    print(f"Wrote final-CSL figures to {FIG_DIR}")


if __name__ == "__main__":
    main()

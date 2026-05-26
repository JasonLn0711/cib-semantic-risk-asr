#!/usr/bin/env python3
"""Generate aggregate-only SVG figures for the CDS-ASR manuscript package."""

from __future__ import annotations

import csv
import html
import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAPER_DIR = ROOT / "80_semantic_risk_asr" / "paper"
OUT_DIR = PAPER_DIR / "figures"

ASR_COMPARISON = (
    ROOT
    / "70_experiments"
    / "runs"
    / "janus_258_test_split_asr_cds_proxy"
    / "asr_cds_proxy_comparison.tsv"
)
PREDICTOR_COMPARISON = (
    ROOT
    / "70_experiments"
    / "runs"
    / "janus_300_high_stakes_human_audit_selection_2026_05_25"
    / "human_audit_predictor_comparison.tsv"
)
RECOVERY_COMPARISON = (
    ROOT
    / "70_experiments"
    / "runs"
    / "janus_300_high_stakes_recovery_human_reviewed_2026_05_26"
    / "policy_comparison.tsv"
)
CANDIDATE_SUMMARY = (
    ROOT
    / "70_experiments"
    / "runs"
    / "asr_candidate_current_recheck_2026_05_26"
    / "summary.json"
)
CANDIDATE_TABLE = (
    ROOT
    / "70_experiments"
    / "runs"
    / "asr_candidate_current_recheck_2026_05_26"
    / "candidate_current_recheck_summary.tsv"
)
READINESS_SUMMARY = (
    ROOT
    / "70_experiments"
    / "runs"
    / "postdoc_evidence_chain_2026_05_25"
    / "publishable_evidence_completion_summary.json"
)


COLORS = {
    "ink": "#1f2933",
    "muted": "#52606d",
    "grid": "#d9e2ec",
    "blue": "#2f80ed",
    "green": "#219653",
    "orange": "#f2994a",
    "red": "#d64545",
    "purple": "#7b61ff",
    "teal": "#0f9f9a",
    "gray": "#f5f7fa",
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def svg_wrap(width: int, height: int, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" role="img">\n'
        f"<rect width=\"{width}\" height=\"{height}\" fill=\"white\"/>\n"
        f"<style>\n"
        f"  text {{ font-family: Arial, Helvetica, sans-serif; fill: {COLORS['ink']}; }}\n"
        f"  .title {{ font-size: 22px; font-weight: 700; }}\n"
        f"  .subtitle {{ font-size: 13px; fill: {COLORS['muted']}; }}\n"
        f"  .label {{ font-size: 13px; font-weight: 700; }}\n"
        f"  .small {{ font-size: 11px; fill: {COLORS['muted']}; }}\n"
        f"</style>\n"
        f"{body}\n"
        f"</svg>\n"
    )


def rect(x: int, y: int, w: int, h: int, fill: str, stroke: str = "#bcccdc") -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>'
    )


def text(x: int, y: int, value: str, klass: str = "small", anchor: str = "start") -> str:
    return f'<text x="{x}" y="{y}" class="{klass}" text-anchor="{anchor}">{esc(value)}</text>'


def line(x1: int, y1: int, x2: int, y2: int, color: str = "#9fb3c8") -> str:
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        f'stroke="{color}" stroke-width="2" marker-end="url(#arrow)"/>'
    )


def arrow_defs() -> str:
    return (
        '<defs><marker id="arrow" markerWidth="10" markerHeight="10" '
        'refX="9" refY="3" orient="auto" markerUnits="strokeWidth">'
        '<path d="M0,0 L0,6 L9,3 z" fill="#9fb3c8"/></marker></defs>'
    )


def figure_1_pipeline() -> None:
    boxes = [
        ("Audio", "speech input", COLORS["blue"]),
        ("ASR", "hypothesis + signals", COLORS["teal"]),
        ("Risk atoms", "negation, amount, actor", COLORS["orange"]),
        ("Variants", "plausible alternatives", COLORS["purple"]),
        ("SRES / CEIS", "decision instability", COLORS["green"]),
        ("Recovery", "conservative action", COLORS["red"]),
    ]
    parts = [arrow_defs(), text(34, 42, "F1. CDS-ASR Pipeline", "title")]
    parts.append(text(34, 64, "Aggregate-only method diagram; no transcript or row content.", "subtitle"))
    x, y, w, h, gap = 34, 120, 145, 88, 35
    for i, (head, sub, color) in enumerate(boxes):
        bx = x + i * (w + gap)
        parts.append(rect(bx, y, w, h, "#ffffff", color))
        parts.append(f'<rect x="{bx}" y="{y}" width="{w}" height="10" fill="{color}" rx="5"/>')
        parts.append(text(bx + w // 2, y + 40, head, "label", "middle"))
        parts.append(text(bx + w // 2, y + 62, sub, "small", "middle"))
        if i < len(boxes) - 1:
            parts.append(line(bx + w + 4, y + h // 2, bx + w + gap - 7, y + h // 2))
    parts.append(text(34, 278, "Human review supplies evaluation labels only; recovery policies remain automatic and aggregate-evaluated.", "subtitle"))
    (OUT_DIR / "f1_cds_asr_pipeline.svg").write_text(svg_wrap(1120, 330, "\n".join(parts)), encoding="utf-8")


def figure_2_boundary() -> None:
    summary = read_json(READINESS_SUMMARY)
    parts = [arrow_defs(), text(36, 42, "F2. Evidence Boundary", "title")]
    parts.append(text(36, 64, f"Publishable evidence gate: {summary.get('publishable_ready')} | status counts: {summary.get('status_counts')}", "subtitle"))
    layers = [
        ("258-row test split", "scope-controlled split/model-comparison evidence", "CER/WER + proxy risk metrics", COLORS["blue"]),
        ("selected-300 proxy outputs", "input provenance and row-selection evidence", "not final human-reviewed risk claim", COLORS["orange"]),
        ("selected-300 human-reviewed audit", "paper-grade predictor and recovery evidence", "30 rows / 90 model assessments", COLORS["green"]),
    ]
    x, y, w, h = 70, 110, 300, 118
    for i, (head, role, note, color) in enumerate(layers):
        bx = x + i * 360
        parts.append(rect(bx, y, w, h, "#ffffff", color))
        parts.append(text(bx + 18, y + 34, head, "label"))
        parts.append(text(bx + 18, y + 62, role, "small"))
        parts.append(text(bx + 18, y + 86, note, "small"))
        if i < len(layers) - 1:
            parts.append(line(bx + w + 8, y + 58, bx + 352, y + 58))
    parts.append(rect(70, 270, 1020, 80, COLORS["gray"], "#bcccdc"))
    parts.append(text(92, 302, "Release boundary", "label"))
    parts.append(text(92, 328, "Tracked: aggregate run records, validation summaries, metric tables, figure SVGs, and paper-facing evidence matrices.", "small"))
    parts.append(text(92, 348, "Local-only: raw audio, transcripts, selected IDs, hypotheses, reviewer sheets/notes, runtime logs, model weights.", "small"))
    (OUT_DIR / "f2_evidence_boundary.svg").write_text(svg_wrap(1160, 390, "\n".join(parts)), encoding="utf-8")


def figure_3_predictor_auc() -> None:
    rows = [
        row
        for row in read_tsv(PREDICTOR_COMPARISON)
        if row["scope"] == "overall" and row["target"] == "human_decision_change_yes"
    ]
    labels = {"wer": "WER", "cer": "CER", "sres_total": "SRES", "ceis_max": "CEIS"}
    colors = [COLORS["blue"], COLORS["teal"], COLORS["orange"], COLORS["green"]]
    data = [(labels[row["metric"]], float(row["auc"])) for row in rows]
    parts = [text(36, 42, "F3. Human-Reviewed Predictor AUC", "title")]
    parts.append(text(36, 64, "Target: human_decision_change_yes over 90 reviewed model assessments.", "subtitle"))
    chart_x, chart_y, chart_w, chart_h = 90, 105, 680, 270
    parts.append(f'<line x1="{chart_x}" y1="{chart_y + chart_h}" x2="{chart_x + chart_w}" y2="{chart_y + chart_h}" stroke="{COLORS["ink"]}" stroke-width="1.5"/>')
    parts.append(f'<line x1="{chart_x}" y1="{chart_y}" x2="{chart_x}" y2="{chart_y + chart_h}" stroke="{COLORS["ink"]}" stroke-width="1.5"/>')
    for tick in [0, 0.25, 0.5, 0.75, 1.0]:
        ty = chart_y + chart_h - tick * chart_h
        parts.append(f'<line x1="{chart_x}" y1="{ty:.1f}" x2="{chart_x + chart_w}" y2="{ty:.1f}" stroke="{COLORS["grid"]}" stroke-width="1"/>')
        parts.append(text(chart_x - 12, int(ty + 4), f"{tick:.2f}", "small", "end"))
    bar_w, gap = 92, 62
    for i, (label, value) in enumerate(data):
        bx = chart_x + 70 + i * (bar_w + gap)
        bh = value * chart_h
        by = chart_y + chart_h - bh
        parts.append(f'<rect x="{bx}" y="{by:.1f}" width="{bar_w}" height="{bh:.1f}" fill="{colors[i]}" rx="4"/>')
        parts.append(text(bx + bar_w // 2, int(by - 10), f"{value:.4f}", "small", "middle"))
        parts.append(text(bx + bar_w // 2, chart_y + chart_h + 26, label, "label", "middle"))
    parts.append(text(810, 142, "Interpretation", "label"))
    parts.append(text(810, 170, "CEIS has the highest AUC.", "small"))
    parts.append(text(810, 194, "SRES has the best-threshold F1.", "small"))
    parts.append(text(810, 218, "Claims remain scoped to selected-300", "small"))
    parts.append(text(810, 238, "human-reviewed aggregate evidence.", "small"))
    (OUT_DIR / "f3_predictor_auc.svg").write_text(svg_wrap(1080, 430, "\n".join(parts)), encoding="utf-8")


def figure_4_recovery() -> None:
    rows = read_tsv(RECOVERY_COMPARISON)
    label_map = {
        "no_recovery": "None",
        "confidence_only_trigger": "Conf.",
        "sres_triggered_recovery": "SRES",
        "ceis_triggered_conservative_action": "CEIS",
        "ceis_ensemble_arbitration": "CEIS ens.",
    }
    data = [
        (
            label_map[row["policy"]],
            int(row["high_risk_missed_count"]),
            int(row["critical_miss_count"]),
            int(row["triggered_count"]),
        )
        for row in rows
    ]
    parts = [text(36, 42, "F4. Recovery Outcomes Under Human-Reviewed Labels", "title")]
    parts.append(text(36, 64, "Counts over 90 reviewed model assessments; aggregate-only.", "subtitle"))
    chart_x, chart_y, chart_w, chart_h = 90, 110, 720, 260
    max_count = 7
    parts.append(f'<line x1="{chart_x}" y1="{chart_y + chart_h}" x2="{chart_x + chart_w}" y2="{chart_y + chart_h}" stroke="{COLORS["ink"]}" stroke-width="1.5"/>')
    parts.append(f'<line x1="{chart_x}" y1="{chart_y}" x2="{chart_x}" y2="{chart_y + chart_h}" stroke="{COLORS["ink"]}" stroke-width="1.5"/>')
    for tick in range(0, max_count + 1):
        ty = chart_y + chart_h - tick / max_count * chart_h
        parts.append(f'<line x1="{chart_x}" y1="{ty:.1f}" x2="{chart_x + chart_w}" y2="{ty:.1f}" stroke="{COLORS["grid"]}" stroke-width="1"/>')
        parts.append(text(chart_x - 12, int(ty + 4), str(tick), "small", "end"))
    group_w = 112
    for i, (label, missed, critical, triggered) in enumerate(data):
        gx = chart_x + 38 + i * (group_w + 24)
        for j, (value, color) in enumerate([(missed, COLORS["orange"]), (critical, COLORS["red"])]):
            bh = value / max_count * chart_h
            by = chart_y + chart_h - bh
            bx = gx + j * 38
            parts.append(f'<rect x="{bx}" y="{by:.1f}" width="32" height="{bh:.1f}" fill="{color}" rx="4"/>')
            parts.append(text(bx + 16, int(by - 8), str(value), "small", "middle"))
        parts.append(text(gx + 35, chart_y + chart_h + 24, label, "label", "middle"))
        parts.append(text(gx + 35, chart_y + chart_h + 44, f"trig {triggered}", "small", "middle"))
    parts.append(f'<rect x="860" y="130" width="18" height="18" fill="{COLORS["orange"]}" rx="3"/>')
    parts.append(text(888, 144, "High-risk missed", "small"))
    parts.append(f'<rect x="860" y="164" width="18" height="18" fill="{COLORS["red"]}" rx="3"/>')
    parts.append(text(888, 178, "Critical miss", "small"))
    parts.append(text(860, 222, "SRES and CEIS conservative policies", "small"))
    parts.append(text(860, 244, "both reach 0/0 at budget 0.3889.", "small"))
    (OUT_DIR / "f4_recovery_outcomes.svg").write_text(svg_wrap(1120, 440, "\n".join(parts)), encoding="utf-8")


def figure_5_model_lanes() -> None:
    main_rows = read_tsv(ASR_COMPARISON)
    candidate_rows = read_tsv(CANDIDATE_TABLE)
    candidate_summary = read_json(CANDIDATE_SUMMARY)
    bounded = candidate_summary.get("bounded_probes", [])
    parts = [text(36, 42, "F5. Model Lane State", "title")]
    parts.append(text(36, 64, "Main benchmark, candidate-lane, and runtime-blocked evidence are kept separate.", "subtitle"))
    lanes = [
        ("Main comparable split", f"{len(main_rows)} completed 258-row runs", "Used for split/model-comparison context", COLORS["green"]),
        ("Locale-gated candidates", f"{len(candidate_rows)} fixed 15-row candidates", "No promotion until strict zh-TW gate is clean", COLORS["orange"]),
        ("Runtime-blocked probes", f"{len(bounded)} bounded probes", "Qwen fetch/load timeout and Gemma runtime class block", COLORS["red"]),
    ]
    x, y, w, h = 70, 120, 300, 125
    for i, (head, count, note, color) in enumerate(lanes):
        bx = x + i * 360
        parts.append(rect(bx, y, w, h, "#ffffff", color))
        parts.append(text(bx + 18, y + 36, head, "label"))
        parts.append(text(bx + 18, y + 66, count, "small"))
        parts.append(text(bx + 18, y + 94, note, "small"))
    parts.append(rect(70, 290, 1020, 82, COLORS["gray"], "#bcccdc"))
    parts.append(text(92, 322, "Promotion rule", "label"))
    parts.append(text(92, 348, "Do not move candidates to 258-row or selected-300 until strict Taiwan Traditional Chinese locale evidence is clean", "small"))
    parts.append(text(92, 366, "or an isolated Gemma 4 multimodal/audio runtime exists.", "small"))
    (OUT_DIR / "f5_model_lane_state.svg").write_text(svg_wrap(1160, 410, "\n".join(parts)), encoding="utf-8")


def figure_6_n_ladder() -> None:
    parts = [text(36, 42, "F6. Evidence N-Ladder", "title")]
    parts.append(text(36, 64, "Evaluation units are separated to avoid treating clustered model assessments as independent calls.", "subtitle"))
    layers = [
        ("Test split", "audio rows", "258", "ASR model comparison", COLORS["blue"]),
        ("Selected provenance", "candidate rows / outputs", "300", "selection and provenance", COLORS["orange"]),
        ("Human-reviewed audit", "audio rows", "30", "decision-critical review unit", COLORS["green"]),
        ("Reviewed assessments", "model-row assessments", "90", "predictor and recovery replay", COLORS["purple"]),
    ]
    x, y, w, h, gap = 70, 112, 240, 118, 30
    for i, (head, unit, n_value, role, color) in enumerate(layers):
        bx = x + i * (w + gap)
        parts.append(rect(bx, y, w, h, "#ffffff", color))
        parts.append(text(bx + 16, y + 32, head, "label"))
        parts.append(text(bx + 16, y + 58, f"Unit: {unit}", "small"))
        parts.append(text(bx + 16, y + 82, f"N = {n_value}", "label"))
        parts.append(text(bx + 16, y + 104, role, "small"))
    parts.append(rect(70, 278, 1050, 74, COLORS["gray"], "#bcccdc"))
    parts.append(text(92, 310, "Cluster rule", "label"))
    parts.append(text(92, 336, "The 90 reviewed assessments are clustered within 30 audio rows; uncertainty should use row-clustered bootstrap or leave-one-row-out sensitivity.", "small"))
    (OUT_DIR / "f6_n_ladder.svg").write_text(svg_wrap(1180, 390, "\n".join(parts)), encoding="utf-8")


def figure_7_budget_risk_frontier() -> None:
    rows = read_tsv(RECOVERY_COMPARISON)
    label_map = {
        "no_recovery": "None",
        "confidence_only_trigger": "Conf. unavailable",
        "sres_triggered_recovery": "SRES",
        "ceis_triggered_conservative_action": "CEIS",
        "ceis_ensemble_arbitration": "CEIS ensemble",
    }
    data = []
    for row in rows:
        severe = int(row["high_risk_missed_count"]) + int(row["critical_miss_count"])
        data.append(
            (
                label_map[row["policy"]],
                float(row["recovery_budget_rate"]),
                severe,
                int(row["triggered_count"]),
                int(row["machine_abstention_count"]),
            )
        )

    parts = [text(36, 42, "F7. Budget-Risk Frontier In Aggregate Replay", "title")]
    parts.append(text(36, 64, "X axis: trigger budget. Y axis: high-risk missed + critical miss.", "subtitle"))
    chart_x, chart_y, chart_w, chart_h = 110, 110, 720, 270
    max_x, max_y = 0.6, 7
    parts.append(f'<line x1="{chart_x}" y1="{chart_y + chart_h}" x2="{chart_x + chart_w}" y2="{chart_y + chart_h}" stroke="{COLORS["ink"]}" stroke-width="1.5"/>')
    parts.append(f'<line x1="{chart_x}" y1="{chart_y}" x2="{chart_x}" y2="{chart_y + chart_h}" stroke="{COLORS["ink"]}" stroke-width="1.5"/>')
    for tick in [0.0, 0.2, 0.4, 0.6]:
        tx = chart_x + tick / max_x * chart_w
        parts.append(f'<line x1="{tx:.1f}" y1="{chart_y}" x2="{tx:.1f}" y2="{chart_y + chart_h}" stroke="{COLORS["grid"]}" stroke-width="1"/>')
        parts.append(text(int(tx), chart_y + chart_h + 24, f"{tick:.1f}", "small", "middle"))
    for tick in range(0, max_y + 1):
        ty = chart_y + chart_h - tick / max_y * chart_h
        parts.append(f'<line x1="{chart_x}" y1="{ty:.1f}" x2="{chart_x + chart_w}" y2="{ty:.1f}" stroke="{COLORS["grid"]}" stroke-width="1"/>')
        parts.append(text(chart_x - 12, int(ty + 4), str(tick), "small", "end"))
    colors = [COLORS["red"], COLORS["orange"], COLORS["green"], COLORS["blue"], COLORS["purple"]]
    for i, (label, budget, severe, triggered, abstain) in enumerate(data):
        px = chart_x + budget / max_x * chart_w
        py = chart_y + chart_h - severe / max_y * chart_h
        parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="8" fill="{colors[i]}" stroke="white" stroke-width="2"/>')
        parts.append(text(int(px + 12), int(py - 8), label, "label"))
        parts.append(text(int(px + 12), int(py + 10), f"trig {triggered}, abstain {abstain}", "small"))
    parts.append(text(110, 418, "Recovery budget", "label"))
    parts.append(text(870, 150, "Replay interpretation", "label"))
    parts.append(text(870, 176, "No recovery and confidence-unavailable", "small"))
    parts.append(text(870, 196, "remain at 7 severe misses.", "small"))
    parts.append(text(870, 226, "SRES and CEIS reach 0 severe misses", "small"))
    parts.append(text(870, 246, "at budget 0.3889.", "small"))
    parts.append(text(870, 276, "CEIS ensemble also reaches 0", "small"))
    parts.append(text(870, 296, "with abstention at budget 0.5222.", "small"))
    (OUT_DIR / "f7_budget_risk_frontier.svg").write_text(svg_wrap(1180, 450, "\n".join(parts)), encoding="utf-8")


def write_index() -> None:
    content = """# CDS-ASR Figure Package

Date: 2026-05-26

These manuscript figures are generated from aggregate-only evidence. They do
not include transcript text, audio IDs, selected row IDs, reviewer notes,
model hypotheses, or transcript-bearing runtime logs.

Generate with:

```bash
python 80_semantic_risk_asr/paper/generate_paper_figures.py
```

| Figure | SVG | PDF | Source | Privacy boundary |
| --- | --- | --- | --- | --- |
| F1. CDS-ASR pipeline | `f1_cds_asr_pipeline.svg` | `f1_cds_asr_pipeline.pdf` | method text | no row content |
| F2. Evidence boundary | `f2_evidence_boundary.svg` | `f2_evidence_boundary.pdf` | publishable evidence summary | aggregate status only |
| F3. Predictor AUC | `f3_predictor_auc.svg` | `f3_predictor_auc.pdf` | `human_audit_predictor_comparison.tsv` | aggregate predictor metrics |
| F4. Recovery outcomes | `f4_recovery_outcomes.svg` | `f4_recovery_outcomes.pdf` | `policy_comparison.tsv` | aggregate policy counts |
| F5. Model lane state | `f5_model_lane_state.svg` | `f5_model_lane_state.pdf` | main/candidate aggregate summaries | aggregate lane state |
| F6. Evidence N-ladder | `f6_n_ladder.svg` | `f6_n_ladder.pdf` | method evidence units | aggregate counts only |
| F7. Budget-risk frontier | `f7_budget_risk_frontier.svg` | `f7_budget_risk_frontier.pdf` | `policy_comparison.tsv` | aggregate policy counts |
"""
    (OUT_DIR / "README.md").write_text(content, encoding="utf-8")


def export_pdfs() -> None:
    converter = shutil.which("convert")
    if not converter:
        print("ImageMagick convert not found; skipped PDF export")
        return
    for svg_path in sorted(OUT_DIR.glob("*.svg")):
        pdf_path = svg_path.with_suffix(".pdf")
        subprocess.run([converter, str(svg_path), str(pdf_path)], check=True)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    figure_1_pipeline()
    figure_2_boundary()
    figure_3_predictor_auc()
    figure_4_recovery()
    figure_5_model_lanes()
    figure_6_n_ladder()
    figure_7_budget_risk_frontier()
    export_pdfs()
    write_index()
    print(f"Wrote figures to {OUT_DIR}")


if __name__ == "__main__":
    main()

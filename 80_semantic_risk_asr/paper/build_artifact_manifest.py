#!/usr/bin/env python3
"""Build an aggregate-only artifact manifest for reviewer-facing materials."""

from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "80_semantic_risk_asr" / "paper" / "artifact_manifest.tsv"

ARTIFACTS = [
    (
        "80_semantic_risk_asr/paper/manuscript_draft.md",
        "manuscript draft",
        "paper-facing aggregate documentation",
        "manual manuscript pass",
        "aggregate evidence artifacts",
    ),
    (
        "80_semantic_risk_asr/paper/references.bib",
        "bibliography",
        "paper-facing citation metadata",
        "manual citation pass",
        "official source pages and papers",
    ),
    (
        "80_semantic_risk_asr/paper/submission_readiness_package_zh.md",
        "submission readiness package",
        "paper-facing planning documentation",
        "manual readiness pass",
        "aggregate validation summaries",
    ),
    (
        "80_semantic_risk_asr/paper/hostile_reviewer_hardening_checklist_2026_05_26.md",
        "reviewer hardening checklist",
        "paper-facing planning documentation",
        "manual hostile-reviewer pass",
        "aggregate manuscript and validation evidence",
    ),
    (
        "80_semantic_risk_asr/paper/generate_paper_figures.py",
        "figure generator",
        "aggregate figure-generation code",
        "manual script maintenance",
        "aggregate evidence artifacts",
    ),
    (
        "80_semantic_risk_asr/paper/build_artifact_manifest.py",
        "artifact manifest generator",
        "aggregate manifest-generation code",
        "manual script maintenance",
        "paper-facing aggregate artifacts",
    ),
    (
        "70_experiments/registry.tsv",
        "experiment registry",
        "aggregate run registry",
        "experiment tracking",
        "repo experiment records",
    ),
    (
        "70_experiments/runs/janus_258_test_split_asr_cds_proxy/asr_cds_proxy_comparison.tsv",
        "main ASR comparison",
        "aggregate metric table",
        "ASR proxy comparison pipeline",
        "258-row split aggregate outputs",
    ),
    (
        "70_experiments/runs/wer_metric_audit_2026_05_25/journal_compliance_summary.json",
        "metric policy audit",
        "aggregate validation summary",
        "metric audit script",
        "WER/CER tokenizer and normalization policy",
    ),
    (
        "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_selection_summary.json",
        "selected-300 selection provenance",
        "aggregate selection summary",
        "high-stakes selection pipeline",
        "proxy risk and downstream decision aggregate signals",
    ),
    (
        "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/selection_strata.tsv",
        "selection strata",
        "aggregate selection table",
        "high-stakes selection pipeline",
        "selected-300 aggregate strata",
    ),
    (
        "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/risk_atom_coverage.tsv",
        "risk atom coverage",
        "aggregate coverage table",
        "high-stakes selection pipeline",
        "selected audit aggregate atom coverage",
    ),
    (
        "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/model_signal_coverage.tsv",
        "model signal coverage",
        "aggregate coverage table",
        "high-stakes selection pipeline",
        "selected audit aggregate model signals",
    ),
    (
        "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_refresh_summary.json",
        "human audit refresh status",
        "aggregate review status",
        "human audit refresh pipeline",
        "review status aggregate outputs",
    ),
    (
        "70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_predictor_comparison.tsv",
        "human-reviewed predictor evidence",
        "aggregate predictor metric table",
        "human audit predictor comparison",
        "reviewed model-assessment aggregate labels",
    ),
    (
        "70_experiments/runs/janus_300_high_stakes_recovery_human_reviewed_2026_05_26/policy_comparison.tsv",
        "human-reviewed recovery evidence",
        "aggregate policy replay table",
        "human-reviewed recovery pipeline",
        "reviewed model-assessment aggregate labels",
    ),
    (
        "70_experiments/runs/postdoc_evidence_chain_2026_05_25/publishable_evidence_completion_summary.json",
        "publishable evidence gate",
        "aggregate validation summary",
        "publishable evidence audit",
        "evidence-chain aggregate records",
    ),
    (
        "70_experiments/runs/postdoc_evidence_chain_2026_05_25/evidence_chain_consistency_summary.json",
        "evidence-chain consistency gate",
        "aggregate validation summary",
        "evidence-chain consistency audit",
        "evidence-chain aggregate records",
    ),
]

FIGURES = [
    "f1_cds_asr_pipeline.svg",
    "f2_evidence_boundary.svg",
    "f3_predictor_auc.svg",
    "f4_recovery_outcomes.svg",
    "f5_model_lane_state.svg",
    "f6_n_ladder.svg",
    "f7_budget_risk_frontier.svg",
    "README.md",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unavailable"


def package_versions() -> str:
    names = ["jiwer", "opencc", "jieba", "transformers", "torch", "numpy"]
    values = []
    for name in names:
        try:
            values.append(f"{name}={importlib.metadata.version(name)}")
        except importlib.metadata.PackageNotFoundError:
            values.append(f"{name}=unavailable")
    return ";".join(values)


def main() -> None:
    rows = list(ARTIFACTS)
    for figure in FIGURES:
        rows.append(
            (
                f"80_semantic_risk_asr/paper/figures/{figure}",
                "generated manuscript figure" if figure.endswith(".svg") else "figure package index",
                "aggregate figure artifact",
                "80_semantic_risk_asr/paper/generate_paper_figures.py",
                "aggregate method, predictor, recovery, and lane summaries",
            )
        )

    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    commit = git_commit()
    py_version = platform.python_version()
    versions = package_versions()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, delimiter="\t", lineterminator="\n")
        writer.writerow(
            [
                "artifact_path",
                "role",
                "privacy_class",
                "generated_by",
                "source_inputs",
                "sha256",
                "source_git_commit",
                "timestamp_utc",
                "python_version",
                "package_versions",
            ]
        )
        for rel_path, role, privacy_class, generated_by, source_inputs in rows:
            path = ROOT / rel_path
            writer.writerow(
                [
                    rel_path,
                    role,
                    privacy_class,
                    generated_by,
                    source_inputs,
                    sha256(path) if path.exists() else "missing",
                    commit,
                    timestamp,
                    py_version,
                    versions,
                ]
            )
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()

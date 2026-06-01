#!/usr/bin/env python3
"""Compatibility wrapper for the R-based CDS-ASR figure generator."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
R_SCRIPT = ROOT / "80_semantic_risk_asr" / "paper" / "generate_paper_figures.R"
LOCAL_R = ROOT / ".r-env" / "bin" / "Rscript"


def main() -> int:
    rscript = shutil.which("Rscript") or (str(LOCAL_R) if LOCAL_R.exists() else None)
    if not rscript:
        sys.stderr.write(
            "Rscript is required. Use the repo-local environment command:\n"
            "  micromamba run -p ./.r-env Rscript "
            "80_semantic_risk_asr/paper/generate_paper_figures.R\n"
        )
        return 1
    return subprocess.run([rscript, str(R_SCRIPT)], cwd=ROOT).returncode


if __name__ == "__main__":
    raise SystemExit(main())

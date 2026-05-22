#!/usr/bin/env python3
"""Install repository-local git hooks for automated versioning."""

from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".githooks" / "pre-commit"


def run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, cwd=ROOT, text=True).strip()


def main() -> int:
    if not HOOK.exists():
        raise SystemExit(f"missing hook: {HOOK}")

    mode = HOOK.stat().st_mode
    HOOK.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    run(["git", "config", "core.hooksPath", ".githooks"])
    hook_path = run(["git", "config", "--get", "core.hooksPath"])
    print(f"Installed version hooks: core.hooksPath={hook_path}")
    print(f"Pre-commit hook executable: {os.access(HOOK, os.X_OK)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

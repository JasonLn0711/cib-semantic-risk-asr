#!/usr/bin/env python3
"""Automatically bump repo version for staged git changes."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
VERSION_RE = re.compile(r"^v(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)$")

VERSION_FILE = ROOT / "VERSION"
MANIFEST_FILE = ROOT / "version_manifest.json"
CHANGELOG_FILE = ROOT / "CHANGELOG.md"
HISTORY_FILE = ROOT / "version_history.jsonl"

GENERATED_VERSION_FILES = {
    "VERSION",
    "version_manifest.json",
    "CHANGELOG.md",
    "version_history.jsonl",
}

EXCLUDED_PREFIXES = (
    ".git/",
    "00_source_archives/",
    "10_extracted_parts/",
    "20_inventory/",
    "40_breeze_asr25_finetune_dataset/hf_audiofolder/",
    "40_breeze_asr25_finetune_dataset/manifests/",
    "40_breeze_asr25_finetune_dataset/reports/",
    "50_janus_data_library/catalog/",
    "50_janus_data_library/connections/",
)


def run_git(args: list[str], *, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def parse_version(text: str) -> tuple[int, int, int]:
    match = VERSION_RE.match(text.strip())
    if not match:
        raise ValueError(f"invalid version format: {text!r}")
    return (
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
    )


def format_version(parts: tuple[int, int, int]) -> str:
    return f"v{parts[0]}.{parts[1]}.{parts[2]}"


def bump_version(current: str, bump: str) -> str:
    major, minor, patch = parse_version(current)
    if bump == "major":
        return format_version((major + 1, 0, 0))
    if bump == "minor":
        return format_version((major, minor + 1, 0))
    if bump == "patch":
        return format_version((major, minor, patch + 1))
    raise ValueError(f"unsupported bump type: {bump}")


def current_version() -> str:
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    if MANIFEST_FILE.exists():
        manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
        return str(manifest["version"])
    raise FileNotFoundError("missing VERSION and version_manifest.json")


def staged_paths() -> list[str]:
    output = run_git(["diff", "--cached", "--name-only", "--diff-filter=ACMRD"])
    return [line for line in output.splitlines() if line.strip()]


def is_generated_version_file(path: str) -> bool:
    return path in GENERATED_VERSION_FILES


def is_excluded(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in EXCLUDED_PREFIXES)


def version_trigger_paths(paths: Iterable[str]) -> list[str]:
    triggers = []
    for path in paths:
        if is_generated_version_file(path) or is_excluded(path):
            continue
        triggers.append(path)
    return triggers


def git_value(args: list[str], fallback: str = "") -> str:
    try:
        value = run_git(args)
    except subprocess.CalledProcessError:
        return fallback
    return value or fallback


def markdown_entry(record: dict[str, object]) -> str:
    files = record.get("changed_files", [])
    if not isinstance(files, list):
        files = []
    file_lines = "\n".join(f"  - `{path}`" for path in files) or "  - none"
    return (
        f"## {record['version']} - {record['updated_at']}\n\n"
        f"- Bump: `{record['bump']}`\n"
        f"- Trigger: `{record['trigger']}`\n"
        f"- Base commit: `{record['base_commit']}`\n"
        f"- Branch: `{record['branch']}`\n"
        f"- Summary: {record['summary']}\n"
        f"- Changed files:\n{file_lines}\n\n"
    )


def update_changelog(record: dict[str, object]) -> None:
    header = (
        "# Version Log\n\n"
        "This file is maintained by `scripts/auto_version.py`.\n\n"
        "Every automatic bump is also recorded as a machine-readable JSON line in\n"
        "`version_history.jsonl`.\n\n"
    )
    existing = CHANGELOG_FILE.read_text(encoding="utf-8") if CHANGELOG_FILE.exists() else ""
    if existing.startswith(header):
        body = existing[len(header) :]
    elif existing.startswith("# Version Log"):
        parts = existing.split("\n\n", 3)
        body = parts[3] if len(parts) == 4 else ""
    else:
        body = existing
    CHANGELOG_FILE.write_text(header + markdown_entry(record) + body, encoding="utf-8")


def write_manifest(record: dict[str, object]) -> None:
    major, minor, patch = parse_version(str(record["version"]))
    manifest = {
        "version": record["version"],
        "versioning_scheme": "SemVer",
        "semver": {
            "major": major,
            "minor": minor,
            "patch": patch,
        },
        "updated_at": record["updated_at"],
        "bump": record["bump"],
        "trigger": record["trigger"],
        "branch": record["branch"],
        "base_commit": record["base_commit"],
        "rules": "VERSIONING.md",
        "changelog": "CHANGELOG.md",
        "history": "version_history.jsonl",
        "summary": record["summary"],
        "changed_files": record["changed_files"],
    }
    MANIFEST_FILE.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def append_history(record: dict[str, object]) -> None:
    with HISTORY_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def stage_version_files() -> None:
    run_git(["add", "VERSION", "version_manifest.json", "CHANGELOG.md", "version_history.jsonl"])


def build_record(new_version: str, bump: str, trigger: str, changed_files: list[str]) -> dict[str, object]:
    summary = os.environ.get("VERSION_SUMMARY", "").strip()
    if not summary:
        summary = "Auto version bump for staged repo changes."
    return {
        "version": new_version,
        "updated_at": now_iso(),
        "bump": bump,
        "trigger": trigger,
        "branch": git_value(["branch", "--show-current"], "unknown"),
        "base_commit": git_value(["rev-parse", "--short", "HEAD"], "unknown"),
        "summary": summary,
        "changed_files": changed_files,
    }


def check_files() -> int:
    version = current_version()
    parse_version(version)
    manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    if manifest.get("version") != version:
        raise SystemExit(
            f"manifest version {manifest.get('version')!r} does not match VERSION {version!r}"
        )
    if not CHANGELOG_FILE.exists():
        raise SystemExit("missing CHANGELOG.md")
    if not HISTORY_FILE.exists():
        raise SystemExit("missing version_history.jsonl")
    print(f"Version files OK: {version}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", action="store_true", help="stage generated version files")
    parser.add_argument("--dry-run", action="store_true", help="show what would bump")
    parser.add_argument("--check", action="store_true", help="validate version files and exit")
    parser.add_argument(
        "--bump",
        choices=["major", "minor", "patch"],
        default=os.environ.get("VERSION_BUMP", "patch"),
    )
    args = parser.parse_args()

    if args.check:
        return check_files()

    paths = staged_paths()
    triggers = version_trigger_paths(paths)
    if not triggers:
        print("auto_version: no versioned staged changes; skip")
        return 0

    bump = args.bump
    if bump not in {"major", "minor", "patch"}:
        raise SystemExit(f"VERSION_BUMP must be major, minor, or patch; got {bump!r}")

    old_version = current_version()
    new_version = bump_version(old_version, bump)
    record = build_record(new_version, bump, "pre-commit" if args.stage else "manual", triggers)

    if args.dry_run:
        print(
            json.dumps(
                {
                    "old_version": old_version,
                    "new_version": new_version,
                    "bump": bump,
                    "changed_files": triggers,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    VERSION_FILE.write_text(new_version + "\n", encoding="utf-8")
    write_manifest(record)
    update_changelog(record)
    append_history(record)

    if args.stage:
        stage_version_files()

    print(f"auto_version: {old_version} -> {new_version} ({bump})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

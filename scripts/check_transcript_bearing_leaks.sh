#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

python - <<'PY'
import csv
import json
import subprocess
from pathlib import Path

SENSITIVE_KEYS = {
    "audio_id",
    "sample_id",
    "reference_text",
    "hypothesis_text",
    "asr_hypotheses_json",
    "reviewer_model_assessments_json",
    "reviewer_notes",
    "reviewer_verified_transcript",
}
SCOPE_PREFIXES = (
    "70_experiments/",
    "80_semantic_risk_asr/paper/",
    "docs/",
)
ALLOWLIST = {
    "docs/artifact_privacy_classes.tsv",
    # Legacy non-submission analysis templates/records retain identifier columns.
    # They are not part of the selected-300 reviewer-visible package.
    "70_experiments/templates/error_analysis.tsv",
    "70_experiments/runs/janus_15_decision_stability_pilot/case_candidates.tsv",
    "70_experiments/runs/whisper_large_v2_lora_baseline/error_analysis.tsv",
    "70_experiments/runs/whisper_small_smoke_test/error_analysis.tsv",
}

tracked = subprocess.check_output(
    ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
    text=True,
).splitlines()
violations: list[str] = []

def walk_json(value, path: str, key_path: str = "") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            full_key = f"{key_path}.{key}" if key_path else str(key)
            if key in SENSITIVE_KEYS:
                violations.append(f"{path}: json key {full_key}")
            walk_json(child, path, full_key)
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            walk_json(child, path, f"{key_path}[{idx}]")

for rel in tracked:
    if rel in ALLOWLIST:
        continue
    if not rel.startswith(SCOPE_PREFIXES):
        continue
    path = Path(rel)
    if not path.exists():
        continue
    if path.suffix == ".tsv":
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.reader(handle, delimiter="\t")
            header = next(reader, [])
        for field in header:
            if field in SENSITIVE_KEYS:
                violations.append(f"{rel}: tsv field {field}")
    elif path.suffix == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            violations.append(f"{rel}: invalid json")
            continue
        walk_json(payload, rel)

if violations:
    print("Transcript-bearing leak scan failed:")
    for item in violations:
        print(f"  {item}")
    raise SystemExit(1)

print("Transcript-bearing leak scan passed for tracked aggregate TSV/JSON headers and keys.")
print("Policy docs may still mention sensitive field names as prohibited release items.")
PY

echo
echo "Informational marker scan in paper-facing paths:"
marker_output="$(
  git grep -nE "(reference transcript|hypothesis_text|audio_id|selected_row|reviewer_notes)" \
    -- 70_experiments docs 80_semantic_risk_asr/paper || true
)"
if [[ -z "$marker_output" ]]; then
  echo "No marker mentions found."
else
  marker_count="$(printf '%s\n' "$marker_output" | wc -l | tr -d ' ')"
  echo "Marker mentions found: $marker_count"
  echo "First 80 marker mentions follow; inspect context for policy-only wording vs content leakage."
  printf '%s\n' "$marker_output" | sed -n '1,80p'
fi

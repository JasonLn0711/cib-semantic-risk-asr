#!/usr/bin/env python3
"""Create the v2.0 Batch 1 multimodal candidate metadata snapshot.

The script records public model-card metadata only. It does not download model
weights, audio rows, transcripts, hypotheses, or runtime logs.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HF_API = "https://huggingface.co/api/models/"
USER_AGENT = "cib-semantic-risk-asr-v2-gate0/1.0"
WEIGHT_SUFFIXES = (
    ".safetensors",
    ".bin",
    ".pt",
    ".pth",
    ".ckpt",
    ".onnx",
    ".gguf",
)


@dataclass(frozen=True)
class Candidate:
    family: str
    model_id: str
    candidate_lane: str
    first_gate: str
    parameter_count_or_effective_size: str
    parameter_source: str
    modalities: str
    speech_input_supported: str
    transcript_like_output_supported: str
    recommended_runtime: str
    runtime_source: str
    promotion_decision: str
    notes: str
    license_override: str = ""
    license_source_override: str = ""


CANDIDATES = [
    Candidate(
        family="Kimi-Audio",
        model_id="moonshotai/Kimi-Audio-7B-Instruct",
        candidate_lane="batch1_primary_zh_tw_audio_llm",
        first_gate="metadata_size_boundary_then_runtime_smoke",
        parameter_count_or_effective_size=(
            "Kimi-Audio-7B label; HF widget currently reports 10B params"
        ),
        parameter_source="HF model card lines 230-238 and model name/card introduction",
        modalities="audio,text,speech_generation",
        speech_input_supported="yes",
        transcript_like_output_supported="yes",
        recommended_runtime="official KimiAudio package / Docker; text output only",
        runtime_source="HF card KimiAudio usage and GitHub repository",
        promotion_decision="metadata_pending_size_boundary",
        notes=(
            "Primary scientific candidate, but Gate 0 records a size-boundary "
            "validation layer because the public HF widget says 10B params while "
            "the model family is named 7B."
        ),
    ),
    Candidate(
        family="Qwen2.5-Omni",
        model_id="Qwen/Qwen2.5-Omni-7B",
        candidate_lane="batch1_primary_zh_tw_audio_llm",
        first_gate="runtime_smoke",
        parameter_count_or_effective_size="7B",
        parameter_source="HF model id, model card, and Qwen2.5-Omni technical report",
        modalities="text,image,audio,video,speech_generation",
        speech_input_supported="yes",
        transcript_like_output_supported="yes",
        recommended_runtime="Transformers Qwen2_5Omni; text output only; disable speech output",
        runtime_source="HF model card Transformers usage",
        promotion_decision="runtime_ready_after_artifact_check",
        notes="Stable general-purpose omni baseline; runtime smoke must force transcript-only output.",
        license_override="apache-2.0",
        license_source_override="HF public model page; HF API cardData currently returns other",
    ),
    Candidate(
        family="Step-Audio 2 mini",
        model_id="stepfun-ai/Step-Audio-2-mini",
        candidate_lane="batch1_primary_zh_tw_audio_llm",
        first_gate="runtime_smoke",
        parameter_count_or_effective_size="8B",
        parameter_source="HF model card Model size widget",
        modalities="audio,text,speech_conversation",
        speech_input_supported="yes",
        transcript_like_output_supported="yes",
        recommended_runtime="Transformers custom_code / official examples; no TTS output",
        runtime_source="HF model card and Step-Audio 2 technical report",
        promotion_decision="runtime_ready_after_artifact_check",
        notes="Strict transcript-only smoke before any speech conversation, tool, or paralinguistic task.",
    ),
    Candidate(
        family="MOSS-Audio",
        model_id="OpenMOSS-Team/MOSS-Audio-4B-Instruct",
        candidate_lane="batch1_primary_zh_tw_audio_llm",
        first_gate="runtime_smoke_4b_first",
        parameter_count_or_effective_size="~4.6B total size; 4B label",
        parameter_source="OpenMOSS GitHub model table",
        modalities="audio,text,speech,sound,music",
        speech_input_supported="yes",
        transcript_like_output_supported="yes",
        recommended_runtime="official MOSS-Audio clean Python 3.12 environment",
        runtime_source="OpenMOSS GitHub quickstart",
        promotion_decision="runtime_ready_after_artifact_check",
        notes="First MOSS-Audio runtime target; Instruct variant is the transcript/QA candidate.",
    ),
    Candidate(
        family="MOSS-Audio",
        model_id="OpenMOSS-Team/MOSS-Audio-8B-Instruct",
        candidate_lane="batch1_primary_zh_tw_audio_llm",
        first_gate="runtime_smoke_after_4b",
        parameter_count_or_effective_size="~8.6B total size; 8B label",
        parameter_source="OpenMOSS GitHub model table",
        modalities="audio,text,speech,sound,music",
        speech_input_supported="yes",
        transcript_like_output_supported="yes",
        recommended_runtime="official MOSS-Audio clean Python 3.12 environment",
        runtime_source="OpenMOSS GitHub quickstart",
        promotion_decision="runtime_ready_after_4b_smoke",
        notes="Second MOSS-Audio transcript target after 4B confirms environment and prompt contract.",
    ),
    Candidate(
        family="MOSS-Audio",
        model_id="OpenMOSS-Team/MOSS-Audio-4B-Thinking",
        candidate_lane="batch1_reasoning_variant_after_instruct",
        first_gate="reasoning_variant_after_instruct_gate",
        parameter_count_or_effective_size="~4.6B total size; 4B label",
        parameter_source="OpenMOSS GitHub model table",
        modalities="audio,text,speech,sound,music",
        speech_input_supported="yes",
        transcript_like_output_supported="yes",
        recommended_runtime="official MOSS-Audio clean Python 3.12 environment",
        runtime_source="OpenMOSS GitHub quickstart",
        promotion_decision="defer_until_instruct_transcript_gate",
        notes="Thinking variant is recorded in Batch 1 family metadata but not first transcript target.",
    ),
    Candidate(
        family="MOSS-Audio",
        model_id="OpenMOSS-Team/MOSS-Audio-8B-Thinking",
        candidate_lane="batch1_reasoning_variant_after_instruct",
        first_gate="reasoning_variant_after_instruct_gate",
        parameter_count_or_effective_size="~8.6B total size; 8B label",
        parameter_source="OpenMOSS GitHub model table",
        modalities="audio,text,speech,sound,music",
        speech_input_supported="yes",
        transcript_like_output_supported="yes",
        recommended_runtime="official MOSS-Audio clean Python 3.12 environment",
        runtime_source="OpenMOSS GitHub quickstart",
        promotion_decision="defer_until_instruct_transcript_gate",
        notes="Thinking variant is recorded in Batch 1 family metadata but not first transcript target.",
    ),
    Candidate(
        family="MiniCPM-o",
        model_id="openbmb/MiniCPM-o-4_5",
        candidate_lane="batch1_primary_zh_tw_audio_llm",
        first_gate="artifact_license_runtime_gate_then_runtime_smoke",
        parameter_count_or_effective_size="9B",
        parameter_source="HF model card introduction and Model size widget",
        modalities="text,image,audio,video,speech_generation,full_duplex",
        speech_input_supported="yes",
        transcript_like_output_supported="yes",
        recommended_runtime="Transformers custom_code; text-only audio understanding mode",
        runtime_source="HF model card / OpenBMB project runtime sections",
        promotion_decision="runtime_ready_after_artifact_check",
        notes="Batch 1 MiniCPM target; must remain transcript-only before interaction tests.",
    ),
    Candidate(
        family="MiniCPM-o",
        model_id="openbmb/MiniCPM-o-2_6",
        candidate_lane="fallback_only",
        first_gate="fallback_metadata_then_optional_smoke",
        parameter_count_or_effective_size="8B label in MiniCPM-o 2.6 family",
        parameter_source="HF model family/card label; fallback only",
        modalities="text,image,audio,video,speech_generation",
        speech_input_supported="yes",
        transcript_like_output_supported="yes",
        recommended_runtime="Transformers custom_code fallback",
        runtime_source="HF model card",
        promotion_decision="fallback_only_not_batch1_main",
        notes="Use only if MiniCPM-o 4.5 is not reproducible or strict 2025-only scope is required.",
    ),
    Candidate(
        family="MiniCPM-o",
        model_id="openbmb/MiniCPM-o-2_6-int4",
        candidate_lane="fallback_runtime_variant_only",
        first_gate="fallback_runtime_variant_metadata",
        parameter_count_or_effective_size="int4 quantized fallback of MiniCPM-o 2.6",
        parameter_source="HF model id/card; runtime fallback only",
        modalities="text,image,audio,video,speech_generation",
        speech_input_supported="yes",
        transcript_like_output_supported="yes",
        recommended_runtime="Transformers custom_code int4 fallback",
        runtime_source="HF model card",
        promotion_decision="fallback_only_not_scientific_model",
        notes="Runtime fallback only; not a separate scientific model family.",
    ),
]


FIELDNAMES = [
    "model_family",
    "model_id",
    "release_date_or_hf_created_at",
    "last_modified",
    "pipeline_tag",
    "public_or_gated",
    "license",
    "parameter_count_or_effective_size",
    "weight_storage_gib",
    "modalities",
    "speech_input_supported",
    "transcript_like_output_supported",
    "recommended_runtime",
    "trust_remote_code_required",
    "candidate_lane",
    "first_gate",
    "promotion_decision",
    "source_url",
    "model_revision_sha",
    "parameter_source",
    "license_source",
    "runtime_source",
    "notes",
]


def fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def hf_model_info(model_id: str) -> dict[str, Any]:
    return fetch_json(HF_API + model_id + "?blobs=true")


def weight_storage_gib(model_info: dict[str, Any]) -> str:
    total = 0
    for sibling in model_info.get("siblings", []):
        name = sibling.get("rfilename", "")
        if not name.endswith(WEIGHT_SUFFIXES):
            continue
        size = sibling.get("lfs", {}).get("size", sibling.get("size", 0)) or 0
        total += int(size)
    return f"{total / (1024 ** 3):.2f}"


def trust_remote_code_required(model_info: dict[str, Any]) -> str:
    tags = set(model_info.get("tags") or [])
    library = model_info.get("library_name") or ""
    if "custom_code" in tags or "custom_code" in library:
        return "yes"
    return "likely_no"


def license_value(model_info: dict[str, Any]) -> tuple[str, str]:
    card = model_info.get("cardData") or {}
    license_name = card.get("license")
    if not license_name:
        for tag in model_info.get("tags") or []:
            if tag.startswith("license:"):
                license_name = tag.split(":", 1)[1]
                break
    return str(license_name or "metadata_missing"), "hf_api_cardData_or_license_tag"


def public_status(model_info: dict[str, Any]) -> str:
    if model_info.get("private"):
        return "private"
    gated = model_info.get("gated")
    if gated:
        return f"gated:{gated}"
    return "public"


def row_for(candidate: Candidate, model_info: dict[str, Any]) -> dict[str, str]:
    license_name, license_source = license_value(model_info)
    if candidate.license_override:
        license_name = candidate.license_override
        license_source = candidate.license_source_override or license_source
    return {
        "model_family": candidate.family,
        "model_id": candidate.model_id,
        "release_date_or_hf_created_at": str(model_info.get("createdAt") or ""),
        "last_modified": str(model_info.get("lastModified") or ""),
        "pipeline_tag": str(model_info.get("pipeline_tag") or ""),
        "public_or_gated": public_status(model_info),
        "license": license_name,
        "parameter_count_or_effective_size": candidate.parameter_count_or_effective_size,
        "weight_storage_gib": weight_storage_gib(model_info),
        "modalities": candidate.modalities,
        "speech_input_supported": candidate.speech_input_supported,
        "transcript_like_output_supported": candidate.transcript_like_output_supported,
        "recommended_runtime": candidate.recommended_runtime,
        "trust_remote_code_required": trust_remote_code_required(model_info),
        "candidate_lane": candidate.candidate_lane,
        "first_gate": candidate.first_gate,
        "promotion_decision": candidate.promotion_decision,
        "source_url": f"https://huggingface.co/{candidate.model_id}",
        "model_revision_sha": str(model_info.get("sha") or ""),
        "parameter_source": candidate.parameter_source,
        "license_source": license_source,
        "runtime_source": candidate.runtime_source,
        "notes": candidate.notes,
    }


def write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=FIELDNAMES,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def summary(rows: list[dict[str, str]], errors: list[dict[str, str]]) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    lane_counts: dict[str, int] = {}
    family_status: dict[str, list[str]] = {}
    for row in rows:
        status_counts[row["promotion_decision"]] = status_counts.get(row["promotion_decision"], 0) + 1
        lane_counts[row["candidate_lane"]] = lane_counts.get(row["candidate_lane"], 0) + 1
        family_status.setdefault(row["model_family"], []).append(
            f"{row['model_id']}={row['promotion_decision']}"
        )
    return {
        "run_id": "v2_0_multimodal_batch1_candidate_discovery_2026_05_31",
        "generated_at_unix": int(time.time()),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate": "Gate 0 candidate discovery and license/runtime snapshot",
        "batch1_families": [
            "Kimi-Audio",
            "Qwen2.5-Omni",
            "Step-Audio 2 mini",
            "MOSS-Audio",
            "MiniCPM-o",
        ],
        "batch1_primary_models": [
            "moonshotai/Kimi-Audio-7B-Instruct",
            "Qwen/Qwen2.5-Omni-7B",
            "stepfun-ai/Step-Audio-2-mini",
            "OpenMOSS-Team/MOSS-Audio-4B-Instruct",
            "OpenMOSS-Team/MOSS-Audio-8B-Instruct",
            "openbmb/MiniCPM-o-4_5",
        ],
        "fallback_only_models": [
            "openbmb/MiniCPM-o-2_6",
            "openbmb/MiniCPM-o-2_6-int4",
        ],
        "rows": len(rows),
        "errors": errors,
        "promotion_decision_counts": status_counts,
        "candidate_lane_counts": lane_counts,
        "family_status": family_status,
        "privacy": {
            "raw_audio_tracked": False,
            "row_ids_tracked": False,
            "transcripts_tracked": False,
            "hypotheses_tracked": False,
            "reviewer_notes_tracked": False,
            "model_weights_downloaded": False,
        },
        "next_gate": (
            "isolated runtime smoke only for metadata-clean Batch 1 models; "
            "Kimi requires explicit size-boundary decision before runtime promotion"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("70_experiments/runs/v2_0_multimodal_batch1_candidate_discovery_2026_05_31"),
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []
    for candidate in CANDIDATES:
        try:
            info = hf_model_info(candidate.model_id)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            errors.append(
                {
                    "model_id": candidate.model_id,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
            continue
        rows.append(row_for(candidate, info))

    write_tsv(args.output_dir / "candidate_snapshot.tsv", rows)
    (args.output_dir / "candidate_snapshot_summary.json").write_text(
        json.dumps(summary(rows, errors), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

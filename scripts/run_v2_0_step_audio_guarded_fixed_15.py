#!/usr/bin/env python3
"""Run Step-Audio guarded fixed-15 transcript and zh-TW locale gate.

Transcript-bearing row outputs stay in the ignored local runtime lane. Tracked
artifacts contain only aggregate metrics, guard counts, hashes/status, and gate
decisions.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

import torch

import run_v2_0_qwen_omni_fixed_15_row_transcript_gate as metrics
import run_v2_0_step_audio_one_row_smoke as step_base
import run_v2_0_step_audio_transcript_contract_repair as step_repair
from run_v2_0_acoustic_guard_gates import acoustic_features, guard_decision


RUN_ID = "v2_0_multimodal_step_audio_guarded_fixed_15_2026_06_01"
MODEL_ID = "stepfun-ai/Step-Audio-2-mini"
SNAPSHOT_SHA = "e36fdd5d71e0ea22f09dd94bbab9bfc544ca1e36"
DEFAULT_MANIFEST = Path("fixed_15_row_multimodal_manifest.local.tsv")
DEFAULT_OUT_DIR = Path("70_experiments/runs") / RUN_ID
DEFAULT_LOCAL_OUTPUT_DIR = Path("70_experiments/runtime_lanes/step_audio_2_mini/local_outputs") / RUN_ID
PROMPT_ID = "step_audio_2_mini_guarded_fixed15_strict_transcript_v1"
PROMPT = step_repair.REPAIR_PROMPT
TOKENIZER_POLICY = metrics.TOKENIZER_POLICY


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = list(reader)
    required = {"audio_path", "reference_text", "duration_seconds"}
    if not required.issubset(set(reader.fieldnames or [])):
        raise ValueError("fixed_15_manifest_schema_missing_required_fields")
    if len(rows) != 15:
        raise ValueError("fixed_15_manifest_row_count_must_be_15")
    for row in rows:
        if not Path(row["audio_path"]).expanduser().exists():
            raise FileNotFoundError("fixed_15_audio_missing")
        if not row.get("reference_text", "").strip():
            raise ValueError("fixed_15_reference_missing")
    return rows


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_path(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def classify_text(text: str) -> dict[str, Any]:
    base = step_base.classify_text(text)
    simplified = sum(1 for char in text if char in metrics.SIMPLIFIED_MARKERS)
    cjk = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
    return {**base, "simplified_char_count": simplified, "cjk_chars": cjk}


def model_remote_module(model: Any) -> Any:
    primary = sys.modules[model.__class__.__module__]
    if hasattr(primary, "log_mel_spectrogram"):
        return primary
    remote_model = getattr(getattr(model, "base_model", None), "model", model)
    return sys.modules[remote_model.__class__.__module__]


def model_input_device(model: Any) -> torch.device:
    for candidate in (model, getattr(getattr(model, "base_model", None), "model", None)):
        device = getattr(candidate, "device", None)
        if device is not None:
            return torch.device(device)
    for parameter in model.parameters():
        if parameter.device.type != "meta":
            return parameter.device
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def generate_transcript(
    *,
    model: Any,
    tokenizer: Any,
    remote_module: Any,
    input_device: torch.device,
    audio_path: Path,
    max_new_tokens: int,
) -> str:
    audio, _sample_rate, _seconds = step_base.load_waveform(audio_path)
    mel = remote_module.log_mel_spectrogram(audio)
    feature_len = mel.shape[-1]
    token_count = remote_module.compute_token_num(feature_len)
    audio_tokens = "<audio_start>" + ("<audio_patch>" * token_count) + "<audio_end>"
    messages = [
        {"role": "system", "content": "You are an ASR engine. Output transcript text only."},
        {"role": "user", "content": audio_tokens + "\n" + PROMPT},
    ]
    text = tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
    inputs = tokenizer(text, return_tensors="pt")
    wavs = mel.unsqueeze(0)
    wav_lens = torch.tensor([feature_len], dtype=torch.long)
    with torch.inference_mode():
        output_ids = model.generate(
            input_ids=inputs.input_ids.to(input_device),
            attention_mask=inputs.attention_mask.to(input_device),
            wavs=wavs.to(input_device),
            wav_lens=wav_lens.to(input_device),
            max_new_tokens=max_new_tokens,
            do_sample=False,
            repetition_penalty=1.12,
            no_repeat_ngram_size=4,
        )
    new_tokens = output_ids[0][inputs.input_ids.shape[-1] :]
    return tokenizer.decode(new_tokens, skip_special_tokens=True)


def privacy_record() -> dict[str, bool]:
    return {
        "raw_audio_tracked": False,
        "row_ids_tracked": False,
        "transcripts_tracked": False,
        "references_tracked": False,
        "hypotheses_tracked": False,
        "repaired_text_tracked": False,
        "reviewer_notes_tracked": False,
        "local_paths_tracked": False,
        "transcript_bearing_runtime_logs_tracked": False,
        "adapter_weights_tracked": False,
        "model_cache_paths_tracked": False,
    }


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""# Step-Audio Guarded Fixed-15 Transcript Gate

Date: 2026-06-01

Status: {summary['status']}

This record runs Step-Audio-2-mini behind the deterministic acoustic guard for
the fixed-15 transcript and zh-TW locale gate. It is deployment-repair evidence,
not raw model capability. Transcript-bearing row outputs remain in the ignored
local runtime lane.

## Result

```text
model_id={summary['model_id']}
rows={summary['rows']}
guard_no_speech_rows={summary['guard_no_speech_rows']}
pass_to_model_rows={summary['pass_to_model_rows']}
valid_output_rate={summary['valid_output_rate']}
cer_zh_micro={summary['cer_zh_micro']}
wer_zh_jieba_micro={summary['wer_zh_jieba_micro']}
simplified_char_rate={summary['simplified_char_rate']}
locale_violation_rows={summary['locale_violation_rows']}
promotion_decision={summary['promotion_decision']}
```
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def write_failure(out_dir: Path, started_at: int, failure_mode: str, rows: int = 0) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    metric_row = {
        "model_family": "Step-Audio 2 mini",
        "model_id": MODEL_ID,
        "claim_boundary": "deterministic_deployment_repair_not_raw_model_capability",
        "gate": "guarded_fixed_15_row_transcript_gate",
        "rows": rows,
        "expected_rows": 15,
        "valid_output_rate": 0.0,
        "cer_zh_micro": "",
        "wer_zh_jieba_micro": "",
        "runtime_seconds_per_row": "",
        "tokenizer_policy": TOKENIZER_POLICY,
        "failure_mode_class": failure_mode,
        "promotion_decision": "do_not_promote",
    }
    behavior_row = {
        "model_family": "Step-Audio 2 mini",
        "model_id": MODEL_ID,
        "output_rows": 0,
        "valid_text_outputs": 0,
        "raw_transcript_like_outputs": 0,
        "summary_or_answer_rows": 0,
        "translation_rows": 0,
        "tts_only_rows": 0,
        "invented_timestamp_rows": 0,
        "invented_speaker_label_rows": 0,
        "repetition_rows": 0,
        "empty_output_rows": rows,
        "failure_rows": rows,
    }
    locale_row = {
        "model_family": "Step-Audio 2 mini",
        "model_id": MODEL_ID,
        "output_chars": 0,
        "cjk_chars": 0,
        "simplified_char_count": 0,
        "simplified_char_rate": 0.0,
        "locale_violation_rows": 0,
        "raw_scoring_after_opencc_repair": "false",
    }
    guard_row = {
        "model_family": "Step-Audio 2 mini",
        "model_id": MODEL_ID,
        "rows": rows,
        "guard_no_speech_rows": 0,
        "pass_to_model_rows": 0,
        "guard_failure_rows": rows,
        "fixed_safe_output_rows": 0,
        "claim_boundary": "deterministic_deployment_repair_not_raw_model_capability",
    }
    summary = {
        "run_id": RUN_ID,
        "generated_at_unix": int(time.time()),
        "started_at_unix": started_at,
        "status": "step_audio_guarded_fixed_15_failed",
        "model_id": MODEL_ID,
        "rows": rows,
        "failure_mode": failure_mode,
        "guard_no_speech_rows": 0,
        "pass_to_model_rows": 0,
        "valid_output_rate": 0.0,
        "cer_zh_micro": "",
        "wer_zh_jieba_micro": "",
        "simplified_char_rate": 0.0,
        "locale_violation_rows": 0,
        "promotion_decision": "do_not_promote",
        "privacy": privacy_record(),
    }
    write_tsv(out_dir / "transcript_metric_summary.tsv", [metric_row], list(metric_row))
    write_tsv(out_dir / "behavior_taxonomy_summary.tsv", [behavior_row], list(behavior_row))
    write_tsv(out_dir / "locale_summary.tsv", [locale_row], list(locale_row))
    write_tsv(out_dir / "guard_application_summary.tsv", [guard_row], list(guard_row))
    (out_dir / "gate_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_readme(out_dir, summary)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--local-output-dir", type=Path, default=DEFAULT_LOCAL_OUTPUT_DIR)
    parser.add_argument(
        "--snapshot-dir",
        type=Path,
        default=Path(
            "70_experiments/runtime_lanes/step_audio_2_mini/hf_cache/hub/"
            "models--stepfun-ai--Step-Audio-2-mini/snapshots"
        )
        / SNAPSHOT_SHA,
    )
    parser.add_argument("--max-new-tokens", type=int, default=96)
    args = parser.parse_args()

    started_at = int(time.time())
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.local_output_dir.mkdir(parents=True, exist_ok=True)

    try:
        rows = read_manifest(args.manifest)
        from transformers import AutoModelForCausalLM, AutoTokenizer

        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        tokenizer = AutoTokenizer.from_pretrained(
            args.snapshot_dir,
            trust_remote_code=True,
            local_files_only=True,
            fix_mistral_regex=True,
        )
        model = AutoModelForCausalLM.from_pretrained(
            args.snapshot_dir,
            trust_remote_code=True,
            local_files_only=True,
            torch_dtype="auto",
            device_map="auto",
        )
        model.eval()
        remote_module = model_remote_module(model)
        input_device = model_input_device(model)

        local_rows = []
        output_count = 0
        raw_like_count = 0
        summary_count = 0
        translation_count = 0
        tts_count = 0
        timestamp_count = 0
        speaker_count = 0
        repetition_count = 0
        empty_count = 0
        failure_count = 0
        guard_no_speech_count = 0
        pass_to_model_count = 0
        fixed_safe_output_count = 0
        char_edits = 0
        char_denominator = 0
        word_edits = 0
        word_denominator = 0
        output_chars = 0
        cjk_chars = 0
        simplified_chars = 0
        locale_violation_rows = 0

        for index, row in enumerate(rows, start=1):
            audio_path = Path(row["audio_path"]).expanduser()
            reference = row["reference_text"]
            try:
                features = acoustic_features(audio_path)
                decision, reason = guard_decision(features)
                if decision == "guard_no_speech":
                    hypothesis = "無法辨識"
                    guard_no_speech_count += 1
                    fixed_safe_output_count += 1
                else:
                    pass_to_model_count += 1
                    hypothesis = generate_transcript(
                        model=model,
                        tokenizer=tokenizer,
                        remote_module=remote_module,
                        input_device=input_device,
                        audio_path=audio_path,
                        max_new_tokens=args.max_new_tokens,
                    )
                classification = classify_text(hypothesis)
                ce, cd, _cer = metrics.edit_counts(reference, hypothesis, unit="char")
                we, wd, _wer = metrics.edit_counts(reference, hypothesis, unit="word")
                char_edits += ce
                char_denominator += cd
                word_edits += we
                word_denominator += wd
                output_count += classification["has_text_output"]
                raw_like_count += classification["raw_transcript_like_outputs"]
                summary_count += classification["summary_or_answer_outputs"]
                translation_count += classification["translation_outputs"]
                tts_count += classification["tts_only_outputs"]
                timestamp_count += classification["invented_timestamp_outputs"]
                speaker_count += classification["invented_speaker_label_outputs"]
                repetition_count += classification["repetition_output"]
                empty_count += 1 if not hypothesis.strip() else 0
                output_chars += classification["output_chars"]
                cjk_chars += classification["cjk_chars"]
                simplified_chars += classification["simplified_char_count"]
                if classification["simplified_char_count"] > 0:
                    locale_violation_rows += 1
                local_rows.append(
                    {
                        "row_index": index,
                        "guard_decision": decision,
                        "guard_reason": reason,
                        "hypothesis": hypothesis,
                        "reference_text": reference,
                        "privacy": "local_only_ignored_runtime_lane",
                    }
                )
            except Exception as exc:
                failure_count += 1
                local_rows.append(
                    {
                        "row_index": index,
                        "guard_decision": "row_failed",
                        "guard_reason": f"{type(exc).__name__}",
                        "hypothesis": "",
                        "reference_text": reference,
                        "privacy": "local_only_ignored_runtime_lane",
                    }
                )

        local_path = args.local_output_dir / "step_audio_guarded_fixed_15_outputs.local.jsonl"
        with local_path.open("w", encoding="utf-8") as handle:
            for item in local_rows:
                handle.write(json.dumps(item, ensure_ascii=False) + "\n")

        elapsed = max(0.001, time.time() - started_at)
        cer = round(char_edits / max(1, char_denominator) * 100.0, 4)
        wer = round(word_edits / max(1, word_denominator) * 100.0, 4)
        simplified_rate = round(simplified_chars / max(1, cjk_chars) * 100.0, 4)
        valid_rate = round(output_count / len(rows) * 100.0, 4)
        promote = (
            failure_count == 0
            and valid_rate >= 95.0
            and raw_like_count == len(rows)
            and locale_violation_rows == 0
            and simplified_rate == 0.0
        )
        promotion_decision = "promote_to_semantic_damage_proxy" if promote else "do_not_promote"
        failure_mode = "none" if promote else "fixed_15_or_locale_gate_not_clean"

        metric_row = {
            "model_family": "Step-Audio 2 mini",
            "model_id": MODEL_ID,
            "claim_boundary": "deterministic_deployment_repair_not_raw_model_capability",
            "gate": "guarded_fixed_15_row_transcript_gate",
            "rows": len(rows),
            "expected_rows": 15,
            "valid_output_rate": valid_rate,
            "cer_zh_micro": cer,
            "wer_zh_jieba_micro": wer,
            "runtime_seconds_per_row": round(elapsed / len(rows), 4),
            "tokenizer_policy": TOKENIZER_POLICY,
            "failure_mode_class": failure_mode,
            "promotion_decision": promotion_decision,
        }
        behavior_row = {
            "model_family": "Step-Audio 2 mini",
            "model_id": MODEL_ID,
            "output_rows": len(rows),
            "valid_text_outputs": output_count,
            "raw_transcript_like_outputs": raw_like_count,
            "summary_or_answer_rows": summary_count,
            "translation_rows": translation_count,
            "tts_only_rows": tts_count,
            "invented_timestamp_rows": timestamp_count,
            "invented_speaker_label_rows": speaker_count,
            "repetition_rows": repetition_count,
            "empty_output_rows": empty_count,
            "failure_rows": failure_count,
        }
        locale_row = {
            "model_family": "Step-Audio 2 mini",
            "model_id": MODEL_ID,
            "output_chars": output_chars,
            "cjk_chars": cjk_chars,
            "simplified_char_count": simplified_chars,
            "simplified_char_rate": simplified_rate,
            "locale_violation_rows": locale_violation_rows,
            "raw_scoring_after_opencc_repair": "false",
        }
        guard_row = {
            "model_family": "Step-Audio 2 mini",
            "model_id": MODEL_ID,
            "rows": len(rows),
            "guard_no_speech_rows": guard_no_speech_count,
            "pass_to_model_rows": pass_to_model_count,
            "guard_failure_rows": failure_count,
            "fixed_safe_output_rows": fixed_safe_output_count,
            "claim_boundary": "deterministic_deployment_repair_not_raw_model_capability",
        }
        summary = {
            "run_id": RUN_ID,
            "generated_at_unix": int(time.time()),
            "started_at_unix": started_at,
            "status": "step_audio_guarded_fixed_15_complete",
            "model_id": MODEL_ID,
            "model_revision_sha": SNAPSHOT_SHA,
            "prompt_id": PROMPT_ID,
            "rows": len(rows),
            "guard_no_speech_rows": guard_no_speech_count,
            "pass_to_model_rows": pass_to_model_count,
            "valid_output_rate": valid_rate,
            "cer_zh_micro": cer,
            "wer_zh_jieba_micro": wer,
            "simplified_char_rate": simplified_rate,
            "locale_violation_rows": locale_violation_rows,
            "runtime_seconds_per_row": round(elapsed / len(rows), 4),
            "failure_mode": failure_mode,
            "promotion_decision": promotion_decision,
            "claim_boundary": "deterministic_deployment_repair_not_raw_model_capability",
            "privacy": privacy_record(),
        }
        env_row = {
            "model_family": "Step-Audio 2 mini",
            "model_id": MODEL_ID,
            "runtime_lane": "ignored_step_audio_2_mini_runtime_lane",
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "model_inference_run": True,
            "local_output_tracked": False,
            "transcript_bearing_logs_tracked": False,
            "tokenizer_policy": TOKENIZER_POLICY,
        }
        manifest_row = {
            "artifact_class": "local_transcript_bearing_guarded_fixed_15_outputs",
            "artifact_count": len(local_rows),
            "content_sensitivity": "contains_references_and_model_outputs",
            "storage_policy": "ignored_local_runtime_lane",
            "sha256": sha256_path(local_path),
            "hash_or_manifest_status": "local_output_jsonl_hash_recorded_without_path",
            "gate_status": promotion_decision,
        }

        write_tsv(args.out_dir / "runtime_environment_summary.tsv", [env_row], list(env_row))
        write_tsv(args.out_dir / "transcript_metric_summary.tsv", [metric_row], list(metric_row))
        write_tsv(args.out_dir / "behavior_taxonomy_summary.tsv", [behavior_row], list(behavior_row))
        write_tsv(args.out_dir / "locale_summary.tsv", [locale_row], list(locale_row))
        write_tsv(args.out_dir / "guard_application_summary.tsv", [guard_row], list(guard_row))
        write_tsv(args.out_dir / "controlled_artifact_manifest.tsv", [manifest_row], list(manifest_row))
        (args.out_dir / "gate_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        write_readme(args.out_dir, summary)
        print(f"step_audio_guarded_fixed_15_written {args.out_dir}")
        return 0 if promote else 2
    except Exception as exc:
        write_failure(args.out_dir, started_at, f"inference_error:{type(exc).__name__}")
        print(f"step_audio_guarded_fixed_15_written {args.out_dir}")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

# Candidate Runtime Install

Date: 2026-05-25

## Purpose

Install the optional local runtime packages required for FunASR SenseVoice and
Qwen3-ASR smoke tests without tracking the virtual environment in git.

## Command

```bash
uv pip install --python .venv/bin/python funasr modelscope qwen-asr
```

The command output and `/usr/bin/time -v` record are local-only under
`logs/uv_install_funasr_qwen_2026_05_25.log`.

## Result

| Field | Value |
| --- | --- |
| Status | completed |
| Outer wall time | 11.61s |
| Installed | `funasr 1.3.3`, `modelscope 1.37.1`, `qwen-asr 0.0.6` |
| Updated | `transformers 4.55.2 -> 4.57.6`, `tokenizers 0.21.4 -> 0.22.2`, `accelerate 1.13.0 -> 1.12.0` |
| Git policy | `.venv/` and install logs remain ignored |

## Risk Note

This modifies the disposable local `.venv/` only. Rebuild from
`requirements-whisper.txt` for the pre-Qwen Whisper-only environment, or install
`requirements-asr-candidates.txt` when rerunning SenseVoice/Qwen gates.

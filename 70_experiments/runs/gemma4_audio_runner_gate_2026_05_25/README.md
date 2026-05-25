# Gemma 4 Audio Runner Gate

Date: 2026-05-25

## Purpose

Check whether local inference is ready for `unsloth/gemma-4-E2B` and
`unsloth/gemma-4-E4B` as prompted multimodal-ASR candidates.

## Probe

```bash
.venv/bin/python - <<'PY'
from transformers import AutoModelForMultimodalLM
PY
```

The detailed class/config probe is local-only under
`logs/transformers_class_probe_2026_05_25.log`.

## Result

| Field | Value |
| --- | --- |
| Status | blocked before inference |
| Installed Transformers | 4.57.6 |
| Required local class | `AutoModelForMultimodalLM` |
| Class available | false |
| Import error | `ImportError: cannot import name 'AutoModelForMultimodalLM'` |
| Gemma config model type | `gemma4` |
| Gemma config architecture | `Gemma4ForConditionalGeneration` |
| Gemma config declared Transformers | `5.5.0.dev0` |
| Audio support in config | present for E2B and E4B |
| Audio processor | `Gemma4Processor`, 750 audio tokens, 40 ms/token |

## Decision

Do not mix Gemma 4 output into pure ASR baseline tables. Retry Gemma only in a
separate multimodal lane after creating an isolated runtime that exposes
`AutoModelForMultimodalLM` or an official Gemma 4 audio runner. The strict
prompt remains:

```text
請逐字轉錄以下台灣電話客服語音，輸出繁體中文（台灣用語），不得輸出簡體中文；只輸出轉錄內容，不要翻譯，不要摘要。
```

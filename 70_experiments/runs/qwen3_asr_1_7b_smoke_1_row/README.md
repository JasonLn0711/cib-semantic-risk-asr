# Run Record: qwen3_asr_1_7b_smoke_1_row

Date: 2026-05-25

## Purpose

Attempt a bounded Qwen3-ASR 1.7B smoke only after the 0.6B backend became
runnable with cuDNN disabled.

## Command

```bash
.venv/bin/python - <<'PY'
import torch
from qwen_asr import Qwen3ASRModel
torch.backends.cudnn.enabled = False
Qwen3ASRModel.from_pretrained(
    "Qwen/Qwen3-ASR-1.7B",
    dtype=torch.bfloat16,
    device_map="cuda:0",
    max_inference_batch_size=1,
    max_new_tokens=256,
)
PY
```

The local log is ignored under `logs/probe_disable_cudnn_2026_05_25.log`.

## Result

| Field | Value |
| --- | --- |
| Status | stopped before inference |
| Observed state | stalled at model file fetch/load with no GPU activity |
| Rows | 0 |
| Metrics | none |
| Decision input | 0.6B smoke was runnable but failed strict locale gate |

## Decision

Do not spend more runtime on 1.7B until the 0.6B Qwen lane passes the strict
Taiwan Traditional Chinese locale gate. The 1.7B model should be retried only
in an isolated run with explicit download timeout, cache monitoring, and the
same cuDNN-disabled setting.

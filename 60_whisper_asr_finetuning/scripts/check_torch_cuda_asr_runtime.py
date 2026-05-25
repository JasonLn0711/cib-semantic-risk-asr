#!/usr/bin/env python3
"""Check whether the local PyTorch CUDA runtime can run ASR-style convolutions."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


def run_conv_probe(disable_cudnn: bool) -> dict[str, Any]:
    import torch

    torch.backends.cudnn.enabled = not disable_cudnn
    try:
        x = torch.randn(1, 80, 3000, device="cuda")
        conv = torch.nn.Conv1d(80, 384, 3, padding=1).cuda()
        y = conv(x)
        torch.cuda.synchronize()
        return {
            "ok": True,
            "disable_cudnn": disable_cudnn,
            "cudnn_enabled": torch.backends.cudnn.enabled,
            "shape": list(y.shape),
        }
    except Exception as exc:  # noqa: BLE001 - diagnostic script should report exact failure.
        return {
            "ok": False,
            "disable_cudnn": disable_cudnn,
            "cudnn_enabled": torch.backends.cudnn.enabled,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args()

    import torch

    result = {
        "torch": torch.__version__,
        "torch_cuda": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
        "device_count": torch.cuda.device_count(),
        "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "",
        "cudnn_available": torch.backends.cudnn.is_available(),
        "cudnn_version": torch.backends.cudnn.version(),
        "ld_library_path": os.environ.get("LD_LIBRARY_PATH", ""),
        "conv1d_with_cudnn": None,
        "conv1d_without_cudnn": None,
    }
    if torch.cuda.is_available():
        result["conv1d_with_cudnn"] = run_conv_probe(disable_cudnn=False)
        result["conv1d_without_cudnn"] = run_conv_probe(disable_cudnn=True)

    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)

    return 0 if result.get("conv1d_without_cudnn", {}).get("ok", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Load the local JANUS Breeze-ASR-25 fine-tune dataset with Hugging Face Datasets."""
from pathlib import Path
from datasets import Audio, load_dataset

DATA_DIR = Path(__file__).resolve().parents[1] / "hf_audiofolder"

if __name__ == "__main__":
    ds = load_dataset("audiofolder", data_dir=str(DATA_DIR))
    ds = ds.cast_column("audio", Audio(sampling_rate=16000))
    print(ds)
    for split in ds:
        print(split, ds[split].num_rows, ds[split].features)

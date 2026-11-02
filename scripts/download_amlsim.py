#!/usr/bin/env python3
"""
download_amlsim.py — Download and unpack IBM AMLSim sample datasets.

Downloads:
1. Smoke test dataset: sample/outputs/ (tx.csv, accounts.csv, alerts.csv)
2. 20K dataset with cycles: sample/20K_cycle200.tgz (20,000 accounts with 200 cycle patterns)

Saves into data/datasets/amlsim/
"""

import json
import os
import tarfile
import urllib.request
from pathlib import Path

BASE_URL = "https://raw.githubusercontent.com/IBM/AMLSim/master"
DATASETS_DIR = Path("data/datasets/amlsim")

SMOKE_FILES = [
    "sample/outputs/tx.csv",
    "sample/outputs/accounts.csv",
    "sample/outputs/alerts.csv",
    "sample/outputs/cash_tx.csv"
]

ARCHIVE_FILE = "sample/20K_cycle200.tgz"


def download_file(url: str, dest_path: Path):
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if dest_path.exists():
        print(f"  [cached] {dest_path}")
        return
    print(f"  Downloading: {url} -> {dest_path}")
    urllib.request.urlretrieve(url, dest_path)


def main():
    print("=" * 70)
    print("  Acquiring IBM AMLSim Datasets")
    print("=" * 70)

    # 1. Download smoke test dataset
    smoke_dir = DATASETS_DIR / "smoke"
    print("\n[1/3] Downloading Smoke Test Dataset...")
    for rel_path in SMOKE_FILES:
        filename = os.path.basename(rel_path)
        url = f"{BASE_URL}/{rel_path}"
        download_file(url, smoke_dir / filename)

    # 2. Download and unpack 20K_cycle200.tgz
    cycle_dir = DATASETS_DIR / "20K_cycle"
    archive_path = DATASETS_DIR / "20K_cycle200.tgz"
    print("\n[2/3] Downloading 20K Cycle Dataset Archive (1.28 MB)...")
    url = f"{BASE_URL}/{ARCHIVE_FILE}"
    download_file(url, archive_path)

    print(f"  Extracting {archive_path.name} to {cycle_dir}...")
    cycle_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "r:gz") as tar:
        tar.extractall(path=cycle_dir)
    print("  Extraction complete.")

    # 3. Create dataset manifest (YAML written directly)
    manifest_path = DATASETS_DIR / "manifest.yaml"
    manifest_content = """dataset_name: IBM AMLSim Sample Datasets
source_repository: https://github.com/IBM/AMLSim
license: Apache 2.0 (code/sample data)
datasets:
  smoke:
    description: Minimal sample outputs for smoke testing
    path: data/datasets/amlsim/smoke
    files:
      - tx.csv
      - accounts.csv
      - alerts.csv
      - cash_tx.csv
  20K_cycle:
    description: 20K accounts simulation with 200 injected cycle patterns
    path: data/datasets/amlsim/20K_cycle
    archive: 20K_cycle200.tgz
"""
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(manifest_content)
    print(f"\n[3/3] Manifest written to {manifest_path}")

    print("\n" + "=" * 70)
    print("  Acquisition Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()

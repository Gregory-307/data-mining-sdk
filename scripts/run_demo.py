#!/usr/bin/env python
"""Execute docs/demo.ipynb and report success/failure.

Usage:
    python scripts/run_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path
import argparse

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

parser = argparse.ArgumentParser(description="Execute a Jupyter notebook and verify success")
parser.add_argument("--nb", dest="nb", default=None, help="Path to .ipynb file")
args = parser.parse_args()

# Auto-detect notebook when not provided
if args.nb:
    NB_PATH = Path(args.nb)
else:
    v2_nb = Path("docs/demo_v2.ipynb")
    NB_PATH = v2_nb if v2_nb.exists() else Path("docs/demo.ipynb")

if not NB_PATH.exists():
    sys.exit("Notebook not found – run convert_demo.py first")

with NB_PATH.open(encoding="utf-8") as f:
    nb = nbformat.read(f, as_version=4)

kernel_name = nb.metadata.get("kernelspec", {}).get("name", "python3")
# Some environments register only "python" kernel
if kernel_name not in {"python3", "python"}:
    kernel_name = "python"

# Execute with 120-second total timeout, 40-s per cell (CI quick run).
proc = ExecutePreprocessor(timeout=40, kernel_name=kernel_name, allow_errors=False)

try:
    proc.preprocess(nb, {"metadata": {"path": str(Path.cwd())}})
except Exception as exc:  # noqa: BLE001
    print("❌ Notebook execution failed:", exc)
    sys.exit(1)

print("✅ Notebook executed successfully") 
#!/usr/bin/env python
"""Execute docs/demo.ipynb and report success/failure.

Usage:
    python scripts/run_demo.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

NB_PATH = Path("docs/demo.ipynb")
if not NB_PATH.exists():
    sys.exit("Notebook not found – run convert_demo.py first")

with NB_PATH.open() as f:
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
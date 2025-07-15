#!/usr/bin/env python
"""Convert docs/demo_notebook_draft.py → docs/demo.ipynb.

Usage:
    python scripts/convert_demo.py
"""
from __future__ import annotations

import nbformat as nbf
from pathlib import Path
import sys

DRAFT_PATH = Path("docs/demo_notebook_draft.py")
OUT_PATH = Path("docs/demo.ipynb")

if not DRAFT_PATH.exists():
    sys.exit(f"Draft file not found: {DRAFT_PATH}")

nb = nbf.v4.new_notebook()
current_lines: list[str] = []
current_type: str | None = None  # "markdown" | "code"

with DRAFT_PATH.open(encoding="utf-8") as fh:
    for line in fh:
        if line.startswith("# %%"):
            # Flush previous cell
            if current_type:
                cell = (
                    nbf.v4.new_markdown_cell("".join(current_lines))
                    if current_type == "markdown"
                    else nbf.v4.new_code_cell("".join(current_lines))
                )
                nb.cells.append(cell)
            # Reset for new cell
            current_lines = []
            current_type = "markdown" if "[markdown]" in line else "code"
            continue
        current_lines.append(line)

# Add last cell
if current_type and current_lines:
    cell = (
        nbf.v4.new_markdown_cell("".join(current_lines))
        if current_type == "markdown"
        else nbf.v4.new_code_cell("".join(current_lines))
    )
    nb.cells.append(cell)

nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3"}

OUT_PATH.write_text(nbf.writes(nb), encoding="utf-8")

# Friendly path print – works on Windows too
try:
    rel = OUT_PATH.resolve().relative_to(Path.cwd())
except ValueError:
    rel = OUT_PATH.resolve()

print(f"Notebook written to {rel}") 
#!/usr/bin/env python
"""Convert docs/demo_notebook_draft.py → docs/demo.ipynb.

Usage:
    python scripts/convert_demo.py
"""
from __future__ import annotations

import nbformat as nbf
from pathlib import Path
import sys
import argparse

parser = argparse.ArgumentParser(description="Convert draft .py to .ipynb")
parser.add_argument("--draft", dest="draft", default=None, help="Path to draft .py file")
parser.add_argument("--out", dest="out", default=None, help="Output .ipynb path")
args = parser.parse_args()

# Auto-detect draft file when not provided
if args.draft:
    DRAFT_PATH = Path(args.draft)
else:
    # Prefer V2 when present, fallback to original
    v2_path = Path("docs/demo_notebook_v2_draft.py")
    DRAFT_PATH = v2_path if v2_path.exists() else Path("docs/demo_notebook_draft.py")

if not DRAFT_PATH.exists():
    sys.exit(f"Draft file not found: {DRAFT_PATH}")

# Derive OUT_PATH when not provided
if args.out:
    OUT_PATH = Path(args.out)
else:
    name_map = {
        "demo_notebook_v2_draft.py": "demo_v2.ipynb",
        "demo_notebook_draft.py": "demo.ipynb",
    }
    OUT_PATH = Path("docs") / name_map.get(DRAFT_PATH.name, "demo.ipynb")

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
# Notebook Revamp – Implementation Plan (PLAN-04)

This plan translates the outline (notebook_outline_v2.md) into concrete engineering steps, deliverables, and review gates.  It will serve as our checklist during development.

---
## 1. File Map
| Path | Purpose |
|------|---------|
| `docs/demo_notebook_v2_draft.py` | Draft source with `# %%` cells. |
| `docs/demo_v2.ipynb` | Generated notebook (output of convert script). |
| `scripts/convert_demo.py` | Updated to support `*_v2_*` filenames. |
| `scripts/run_demo.py` | Reused; param updated to `demo_v2.ipynb`. |
| `tests/notebook_v2_offline.py` | New pytest suite executing notebook under `OFFLINE_MODE=1`. |

---
## 2. Development Steps
1. **Draft Notebook (Step-5)**  
   • Copy outline headers into draft file; stub code with `pass` or minimal lines.  
   • Integrate env guards (`if os.getenv("RUN_GOOGLE"):` etc.).
2. **Update Converter (Step-6)**  
   • Add CLI flag `--v2` or auto-detect `_v2_` filename pattern.  
   • Ensure kernelspec preserved as `python3`.
3. **Generate & Execute Notebook (Step-7)**  
   • Run conversion ➜ run_demo.py until green online.  
   • Force `OFFLINE_MODE=1` ➜ run again.
4. **Twitter Flow (Step-8)**  
   • Implement helper `scrapers.twitter_web` or inline logic.  
   • Use Playwright, skip if creds absent.
5. **Polish & Trim (Step-9)**  
   • Add output trimming, consolidate imports.
6. **Docs Update (Step-11)**  
   • README replaces v1 links; badges optional.
7. **CI Update (Step-12)**  
   • GitHub Action: call `python scripts/run_demo.py --nb docs/demo_v2.ipynb`.
8. **Cleanup (Step-13)**  
   • Remove old notebook; keep draft file for future edits.
9. **Commit & Push (Step-14)**  
   • Squash or sequential commits as per repo convention.

---
## 3. Review Gates
1. **Unit Tests** – All existing tests + new notebook offline test pass.
2. **Notebook Run** – Online & offline executions succeed within 3-min budget.
3. **Lint** – `ruff` passes.
4. **Manual QA** – Visual inspection of notebook in Jupyter/Colab; markdown readability.

---
## 4. Rollback Strategy
If Playwright/Twitter flow proves unstable in CI, mark section as skipped by default and log warning instead of failing.

---
_Authored for PLAN-04 – ready for review._ 
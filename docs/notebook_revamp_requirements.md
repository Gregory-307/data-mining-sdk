# Web-Search SDK – Notebook Revamp (V2)

This document consolidates **every explicit requirement and constraint** gathered from the latest brief so we have a single source of truth before touching code.

---
## 1. General Goals
1. Deliver a **fully revamped Jupyter notebook** (`docs/demo_v2.ipynb`) that acts as a _true demo_ and living documentation for the SDK.
2. Notebook must be **self-contained** – a new user should be able to clone the repo, execute the notebook, and understand _what_ each cell does and _why_.
3. Keep code minimal and illustrative; avoid unnecessary boiler-plate – one clear function call → visible, human-readable output.

---
## 2. Content & Structure
1. **Rich Markdown first-class citizen**
   • Each code cell is preceded by a concise markdown explanation (purpose, expected output).  
   • Use numbered lists / sub-headings so developers can follow step-by-step.
2. **Setup Section**
   • Handles repo install, optional Playwright browser install, and any secrets or log-ins.  
   • _Bold_ markdown warnings for steps that require user interaction (e.g. Twitter OAuth).  
   • Tag heavy/optional cells with "_You may safely skip this in CI or offline mode_".
3. **Demo Sections** – one scraper/helper per section:
   1. DuckDuckGo top-words
   2. Wikipedia top-words
   3. RelatedWords synonyms
   4. Google News RSS keywords
   5. Google SERP fallback (optional, labelled)
   6. Paywall article fetch (Bloomberg/CNBC)
   7. Output helpers (`to_json`, `to_csv`)
   8. Text helpers (`tokenise`, `remove_stopwords`, `most_common`)
   9. Rate-limit decorator example
   10. **Twitter login & sample scrape** (new) – show login flow via ScraperContext + Selenium/Playwright if credentials provided.
4. **Call & Response Visibility**  
   For every demo cell, print a trimmed preview of the response so users see immediate results.
5. Clear "Ignore/Skip" markers for cells that are long-running or environment-specific.

---
## 3. Technical Constraints
1. **Single-branch workflow** – all changes land on `main`, no feature branches.
2. Avoid terminal commands of the form `python - <<"PY"` or heredoc/script-embedded Python.  
3. Prefer running scripts (`scripts/convert_demo.py`, `scripts/run_demo.py`) or plain shell commands (`pip install ...`).  
4. CI must execute `scripts/run_demo.py` against the new notebook **without hanging**.
5. Notebook must remain runnable when `OFFLINE_MODE=1` (fixture fallback) _and_ when online.
6. All new helpers or flows must be covered by unit tests where feasible.

---
## 4. Optional Features (Nice-to-Have)
1. Unicorn/FastAPI mini server demonstration – only if time permits; must include automated test.
2. CI badge & coverage badge in README.

---
## 5. Deliverables
1. `docs/demo_notebook_v2_draft.py` – draft file with `# %%` markers.
2. `docs/demo_v2.ipynb` – generated notebook.
3. Any new utility/helper modules required for the Twitter flow.
4. Updated `README.md` referencing the new notebook.
5. CI job or GitHub Action update running `scripts/run_demo.py` on the new notebook.

---
## 6. Acceptance Criteria
- Notebook executes **cleanly** via `python scripts/run_demo.py` in < 3 min (CI default timeout).
- Every section has markdown context and a visible, trimmed output.
- No interactive prompts in CI; Twitter credentials pulled from env vars if provided else cell is skipped.
- Lint (`ruff`) & unit tests pass.
- All tasks in the project todo list are marked **completed**.

---
_Compiled during PLAN-01 – will be re-evaluated before development begins._ 
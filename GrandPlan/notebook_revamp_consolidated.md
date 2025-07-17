# Web-Search SDK – Notebook Revamp Planning (Consolidated)

*This document consolidates all notebook revamp planning from docs/archive/planning/* into a single reference.*

---

## 1. Current State Audit (from notebook_audit_current.md)

### Structural Issues
| Section | Problem | Notes |
|---------|---------|-------|
| Heading hierarchy | Mixed `##` titles with numeric prefixes jump from 2 → 4 → 5 (missing 1). | Need consistent numbering. |
| Setup cells | Multiple install calls not clearly labelled as skippable; marker comments absent. | Add bold warnings in markdown. |
| Google SERP fallback | Heavy cell _always_ runs Playwright; should be optional due to CAPTCHA risk. | Wrap in env-flag check `RUN_GOOGLE`. |
| Paywall fetch | Uses Bloomberg URL ellipsis (`…`) causing runtime error when executed. | Replace with real or fixture URL. |
| Text Helper cell | Uses correct `tokenise` functions but lacks explanation of expected output. | Add sample preview. |

### Missing Markdown / Explanations
- ~40% of code cells have no preceding markdown.
- No high-level intro explaining SDK purpose or notebook goals.
- Twitter/OAuth flow absent entirely (requirement).
- No section summarising expected outputs or how to integrate results into downstream apps.

### Redundant / Confusing Code
- Smoke-test cell prints full token list—very noisy; trim output.
- Repeated import of `asyncio`, `sys` across several cells.
- `_first_five_tokens` helper could be simplified with slicing.

### Runtime Risks
- Hard-coded Playwright install each run (slow).
- Missing try/except around web scrapers → notebook aborts on network blips.
- No `OFFLINE_MODE` fallback markers for new cells (post-v0.3 sections).

### CI Concerns
- Notebook passes tests now, but selenium tests xfail – acceptable yet should document.
- Execution time ~90s; fine, but Twitter flow may add overhead.

---

## 2. V2 Outline (from notebook_outline_v2.md)

### Structure: One Markdown Header → One Code Cell

#### 0. Title & Overview
- Markdown: Project banner, purpose of SDK, notebook goals, link to README.
- No code.

#### 1. Environment & Installation (Skippable)
- Markdown: Explain editable install (`pip install -e .[browser]`). Warn readers they can skip if running inside repo dev env.
- Code: Shell magic to install package & Playwright _only if_ `!pip show web-search-sdk` is empty. Use `os.getenv("SKIP_INSTALL")` guard.

#### 2. Quick Smoke Test
- Markdown: Verify installation & version.
- Code: Print `web_search_sdk.__version__` and run `smoke_test.py`.

#### 3. ScraperContext Cheatsheet
- Markdown: Explain context params with table.
- Code: Instantiate 3 contexts (HTTP, Selenium, Playwright).

#### 4. Core Scrapers (Primary flow)
- **4.1 DuckDuckGo Top Words**: Markdown: Why DDG first, expected output. Code: `await duckduckgo_top_words(...)` ➜ print top 15.
- **4.2 Wikipedia Top Words**: Similar structure.
- **4.3 RelatedWords Synonyms**: Similar structure.
- **4.4 Google News RSS Keywords**: Similar structure.

#### 5. Optional Google SERP Fallback
- Markdown: Heavy, may CAPTCHA; skip unless `RUN_GOOGLE=1` env var.
- Code: Guarded by env var.

#### 6. Paywall Article Retrieval
- Markdown: Demonstrates browser usage; show trimmed article body.
- Code: Fetch Bloomberg fixture if offline.

#### 7. Twitter Login & Sample Scrape (NEW)
- Markdown: Explain requirement for env vars `TW_EMAIL`, `TW_PASS`. Bold warning.
- Code: If vars missing ➜ print "Skipped". Else use Playwright to log in and fetch user timeline HTML snippet.

#### 8. Output Utilities
- Markdown & code for `to_json`, `to_csv`.

#### 9. Text Helpers Showcase
- Markdown & code for `tokenise`, `remove_stopwords`, `most_common`.

#### 10. Rate-Limit Decorator Example
- Markdown & short code.

#### 11. Parallel Scraping Example
- Markdown & `gather_scrapers` demo.

#### 12. Closing Notes & Next Steps
- Markdown summary, links to API docs, how to contribute.

### Implementation Notes
1. All optional heavy cells are wrapped in env guards.
2. Each code cell prints **trimmed** outputs to keep notebook compact.
3. Use fixtures (`tests/fixtures/...`) when `OFFLINE_MODE=1`.
4. Total execution target < 3 minutes in CI.

---

## 3. Implementation Plan (from notebook_revamp_plan.md)

### File Map
| Path | Purpose |
|------|---------|
| `docs/demo_notebook_v2_draft.py` | Draft source with `# %%` cells. |
| `docs/demo_v2.ipynb` | Generated notebook (output of convert script). |
| `scripts/convert_demo.py` | Updated to support `*_v2_*` filenames. |
| `scripts/run_demo.py` | Reused; param updated to `demo_v2.ipynb`. |
| `tests/notebook_v2_offline.py` | New pytest suite executing notebook under `OFFLINE_MODE=1`. |

### Development Steps
1. **Draft Notebook (Step-5)**: Copy outline headers into draft file; stub code with `pass` or minimal lines. Integrate env guards (`if os.getenv("RUN_GOOGLE"):` etc.).
2. **Update Converter (Step-6)**: Add CLI flag `--v2` or auto-detect `_v2_` filename pattern. Ensure kernelspec preserved as `python3`.
3. **Generate & Execute Notebook (Step-7)**: Run conversion ➜ run_demo.py until green online. Force `OFFLINE_MODE=1` ➜ run again.
4. **Twitter Flow (Step-8)**: Implement helper `scrapers.twitter_web` or inline logic. Use Playwright, skip if creds absent.
5. **Polish & Trim (Step-9)**: Add output trimming, consolidate imports.
6. **Docs Update (Step-11)**: README replaces v1 links; badges optional.
7. **CI Update (Step-12)**: GitHub Action: call `python scripts/run_demo.py --nb docs/demo_v2.ipynb`.
8. **Cleanup (Step-13)**: Remove old notebook; keep draft file for future edits.
9. **Commit & Push (Step-14)**: Squash or sequential commits as per repo convention.

### Review Gates
1. **Unit Tests** – All existing tests + new notebook offline test pass.
2. **Notebook Run** – Online & offline executions succeed within 3-min budget.
3. **Lint** – `ruff` passes.
4. **Manual QA** – Visual inspection of notebook in Jupyter/Colab; markdown readability.

### Rollback Strategy
If Playwright/Twitter flow proves unstable in CI, mark section as skipped by default and log warning instead of failing.

---

## 4. Requirements (from notebook_revamp_requirements.md)

### General Goals
1. Deliver a **fully revamped Jupyter notebook** (`docs/demo_v2.ipynb`) that acts as a _true demo_ and living documentation for the SDK.
2. Notebook must be **self-contained** – a new user should be able to clone the repo, execute the notebook, and understand _what_ each cell does and _why_.
3. Keep code minimal and illustrative; avoid unnecessary boiler-plate – one clear function call → visible, human-readable output.

### Content & Structure
1. **Rich Markdown first-class citizen**: Each code cell is preceded by a concise markdown explanation (purpose, expected output). Use numbered lists / sub-headings so developers can follow step-by-step.
2. **Setup Section**: Handles repo install, optional Playwright browser install, and any secrets or log-ins. _Bold_ markdown warnings for steps that require user interaction (e.g. Twitter OAuth). Tag heavy/optional cells with "_You may safely skip this in CI or offline mode_".
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
4. **Call & Response Visibility**: For every demo cell, print a trimmed preview of the response so users see immediate results.
5. Clear "Ignore/Skip" markers for cells that are long-running or environment-specific.

### Technical Constraints
1. **Single-branch workflow** – all changes land on `main`, no feature branches.
2. Avoid terminal commands of the form `python - <<"PY"` or heredoc/script-embedded Python.
3. Prefer running scripts (`scripts/convert_demo.py`, `scripts/run_demo.py`) or plain shell commands (`pip install ...`).
4. CI must execute `scripts/run_demo.py` against the new notebook **without hanging**.
5. Notebook must remain runnable when `OFFLINE_MODE=1` (fixture fallback) _and_ when online.
6. All new helpers or flows must be covered by unit tests where feasible.

### Optional Features (Nice-to-Have)
1. Unicorn/FastAPI mini server demonstration – only if time permits; must include automated test.
2. CI badge & coverage badge in README.

### Deliverables
1. `docs/demo_notebook_v2_draft.py` – draft file with `# %%` markers.
2. `docs/demo_v2.ipynb` – generated notebook.
3. Any new utility/helper modules required for the Twitter flow.
4. Updated `README.md` referencing the new notebook.
5. CI job or GitHub Action update running `scripts/run_demo.py` on the new notebook.

### Acceptance Criteria
- Notebook executes **cleanly** via `python scripts/run_demo.py` in < 3 min (CI default timeout).
- Every section has markdown context and a visible, trimmed output.
- No interactive prompts in CI; Twitter credentials pulled from env vars if provided else cell is skipped.
- Lint (`ruff`) & unit tests pass.
- All tasks in the project todo list are marked **completed**.

---

## 5. Repo Plans Context (from repo_plans.md)

### web-search-sdk Status
**Purpose**: Async search (Google, news) with full-article parsing; feeds sentiment pipeline.

| Area | Status | Next Step |
|------|--------|-----------|
| CLI export (`export_articles`) | Prototype works for Google; news scraping WIP | Extend to NewsAPI & output gzip NDJSON to S3 |
| Proxy rotation | Basic list hard-coded | Move to dynamic pool & health-check |
| Response schema | JSON Pydantic model v0.1 | Align with `sentiment-pipeline` schema once defined |

---

*Consolidated from docs/archive/planning/* on 2025-01-27* 
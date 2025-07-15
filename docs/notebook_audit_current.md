# Audit – Current Demo Notebook (docs/demo_notebook_draft.py)

_Last updated: {{DATE}}
_

## 1. Structural Issues

| Section | Problem | Notes |
|---------|---------|-------|
| Heading hierarchy | Mixed `##` titles with numeric prefixes jump from 2 → 4 → 5 (missing 1). | Need consistent numbering. |
| Setup cells | Multiple install calls not clearly labelled as skippable; marker comments absent. | Add bold warnings in markdown. |
| Google SERP fallback | Heavy cell _always_ runs Playwright; should be optional due to CAPTCHA risk. | Wrap in env-flag check `RUN_GOOGLE`. |
| Paywall fetch | Uses Bloomberg URL ellipsis (`…`) causing runtime error when executed. | Replace with real or fixture URL. |
| Text Helper cell | Uses correct `tokenise` functions but lacks explanation of expected output. | Add sample preview. |

## 2. Missing Markdown / Explanations

- ~40% of code cells have no preceding markdown.
- No high-level intro explaining SDK purpose or notebook goals.
- Twitter/OAuth flow absent entirely (requirement).
- No section summarising expected outputs or how to integrate results into downstream apps.

## 3. Redundant / Confusing Code

- Smoke-test cell prints full token list—very noisy; trim output.
- Repeated import of `asyncio`, `sys` across several cells.
- `_first_five_tokens` helper could be simplified with slicing.

## 4. Runtime Risks

- Hard-coded Playwright install each run (slow).
- Missing try/except around web scrapers → notebook aborts on network blips.
- No `OFFLINE_MODE` fallback markers for new cells (post-v0.3 sections).

## 5. CI Concerns

- Notebook passes tests now, but selenium tests xfail – acceptable yet should document.
- Execution time ~90s; fine, but Twitter flow may add overhead.

## 6. Action Items Extracted

1. Add high-level overview markdown (Why, What, How).
2. Introduce skip flags (`OFFLINE_MODE`, `RUN_GOOGLE`, `RUN_TWITTER`).
3. Replace placeholder URLs with real sample or fixture links.
4. Consolidate duplicate imports.
5. Trim noisy outputs with `print(...[:300])` etc.
6. Integrate Twitter login demo cell (env-vars for creds).
7. Label heavy install cells and mark skippable in local env.
8. Ensure all cells have markdown header & explanation. 
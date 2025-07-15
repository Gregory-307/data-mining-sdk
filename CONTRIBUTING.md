# Contributing to Web-Search SDK

First off, thank you for taking the time to contribute!  The project thrives on
community feedback, bug reports and new scrapers.

> **TL;DR**  Fork → branch → PR.  Make sure tests pass and write new ones when
> you add functionality.

---

## Development Environment

1. Clone your fork and create a virtual environment:

   ```bash
   git clone https://github.com/<you>/web-search-sdk
   cd web-search-sdk
   python -m venv .venv && source .venv/bin/activate
   ```

2. Install the package in **editable** mode with test & browser extras:

   ```bash
   pip install -e .[test,browser]
   ```

3. (Optional) Install Playwright browsers once:

   ```bash
   playwright install --with-deps
   ```

4. Verify everything is green:

   ```bash
   pytest -q
   scripts/run_demo.py  # OFFLINE_MODE honoured
   ```

---

## Branching & Commit Style

* File a short issue or discussion first if you’re planning a large change.
* Create a **topic branch** from `main` – e.g. `feat/new-scraper`.
* Keep commits focussed; squash when appropriate.
* Conventional commit prefixes (`feat:`, `fix:`, `docs:`…) are welcomed but not enforced.

---

## Coding Guidelines

| Area            | Tool / Standard | Command |
|-----------------|-----------------|---------|
| Formatting      | **black**       | `black .` |
| Linting         | **ruff**        | `ruff check .` |
| Type-checking   | **mypy** (*TBD*)| `mypy web_search_sdk` |
| Tests           | **pytest**      | `pytest -q` |
| Coverage        | **pytest-cov**  | `pytest --cov=web_search_sdk -q` |

A pre-commit config is provided; enable it via:

```bash
pip install pre-commit
pre-commit install
```

---

## Writing Tests

* Place unit tests in `web_search_sdk/tests/` or integration tests in `tests/`.
* Aim for deterministic tests; use `OFFLINE_MODE=1` and fixtures for network.
* When adding a new scraper, cover at least:
  1. Happy path with live fetch (can be `xfail` on CI if truly flaky).
  2. Pure HTML parsing unit test with a stored fixture.

---

## CI Pipeline

Every PR triggers GitHub Actions:

1. Install deps & Playwright on Ubuntu.
2. Run tests with coverage (`coverage.xml` is uploaded as an artifact).
3. Execute the demo notebook in `OFFLINE_MODE`.

Your PR must come back green before merge.

---

## Documentation

* Update `README.md` and the notebook where relevant.
* Public functions should have doc-strings; keep them concise.

---

## License & CLA

By submitting a pull request, you agree that your contribution will be licensed
under the MIT License and that you have the right to do so. 
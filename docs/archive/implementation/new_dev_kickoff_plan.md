# New-Dev Kickoff Plan  
*Version 0.1 – 2025-07-14*

> Scope: stand-up skeleton repos and data plumbing **only**. Do **not** implement sentiment models or trading logic until the research appendix lands.

---

## 0  Context & Ground Rules
1. Clone existing SDKs:
   - `web-search-sdk` (this repo)
   - `twitter-sdk`
2. Every substantive action → commit a dated dev log under `logs/YYYY-MM-DD_dev-log.md` with sections **Done / Blocked / Next / Questions**.
3. Use conventional commits:
   - `feat:` code
   - `docs:` documentation or log updates
   - `ci:` automation
   - `refactor:` non-breaking restructuring
   - `log:` standalone status updates/questions

---

## 1  Repository Boot-Strap
Create three new public-but-private-to-org GitHub repos (ask admin):
| Repo | Purpose |
|------|---------|
| `sentiment-pipeline` | Ingestion, cleaning, feature engineering, **model placeholder** |
| `ml-backtester` | Historical replay harness, metric calc, **strategy placeholder** |
| `hedge-engine` | Score → hedge sizing logic, REST façade, **logic placeholder** |

Initial commit in each repo (`feat: repo skeleton`):
- `pyproject.toml` (Python 3.11, pytest, black)
- `README.md` (1-paragraph purpose + setup)
- `logs/.gitkeep` (empty placeholder)
- `.github/workflows/ci.yaml` running lint + tests

---

## 2  Data Plumbing (depends on existing SDKs)
**Goal:** wire raw data into a consistent folder layout that all new repos can read.

### 2.1 Twitter Feed Export (`twitter-sdk`)
- Extend CLI: `python -m twitter_sdk.export --day YYYY-MM-DD --out s3://crypto-data/tweets/`  
- Output: gzip-compressed NDJSON files.

### 2.2 Web Article Export (`web-search-sdk`)
- Extend CLI: `python -m web_search_sdk.export_articles --query-file queries.txt --out s3://crypto-data/web/`

### 2.3 Transfer Helper
Create `scripts/transfer_data.py` (single repo of your choice) that copies one day’s data locally for rapid iteration.

Commit tag: `feat: data plumbing MVP`

---

## 3  Sentiment Pipeline *Skeleton* (`sentiment-pipeline`)
**Do NOT implement a model yet.**  Provide:
- Package layout (`sentiment_pipeline/__init__.py`).
- `bot_filter.py` stub with class `BotFilter` (TODO: Botometer integration).
- `schema.py` with Pydantic models for cleaned tweet & sentiment result.
- Unit tests that import modules & assert placeholder methods raise `NotImplementedError`.

Commit tag: `feat: sentiment skeleton`

---

## 4  Backtester *Skeleton* (`ml-backtester`)
Provide:
- `data_loader.py` that reads Parquet tweets, price candles, order-book snapshots (schema TBD).
- `engine.py` with class `BacktestEngine` (no strategy yet).
- CLI stub: `python -m ml_backtester.run --config configs/baseline.yaml` (prints "NOT IMPLEMENTED – waiting for research")
- Basic pytest harness confirming the CLI exits 0.

Commit tag: `feat: backtester skeleton`

---

## 5  Hedge Engine *Skeleton* (`hedge-engine`)
Provide:
- FastAPI/Flask app exposing `POST /hedge` that returns fixed JSON `{ "hedge_pct": null, "msg": "Score model not ready" }`.
- Dockerfile that builds & runs the stub.

Commit tag: `feat: hedge engine skeleton`

---

## 6  CI & Automation
- Enable GitHub Actions in each repo to run `black --check`, `pytest`, and `mypy` on PRs.
- Optionally cache Python deps for faster runs.

Commit tag: `ci: baseline workflow`

---

## Deferred Work (post-research)
The upcoming **Research Appendix** will decide:
1. Which sentiment model family (e.g., transformer, structured embedding, etc.).
2. Feature set for the backtester (lag windows, liquidity deltas, etc.).
3. Hedge sizing curve and risk parameters.

Hold off on any of these until we commit `research/Research-Appendix.md`.

---

## Milestone Completion Criteria
| Phase | Files/Artifacts that must exist |
|-------|---------------------------------|
| 1     | Three new repos with skeleton structure & CI passing |
| 2     | Data export CLIs produce gzip NDJSON; `scripts/transfer_data.py` copies locally |
| 3     | `sentiment_pipeline` imports without error; tests green |
| 4     | `ml-backtester` CLI runs & exits 0; tests green |
| 5     | `hedge-engine` container builds & `curl /hedge` returns stub JSON |
| 6     | All repos: GitHub Actions show ✓ on PRs |

When each milestone passes, push a log entry titled `log: milestone X completed – details`.

---

## Questions & Clarifications
Add questions in your daily log under **Open Questions:**; they will be answered via the next commit.

Good luck & welcome aboard! 🎉 
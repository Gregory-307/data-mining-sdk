# New-Dev Onboarding Packs – Other Repositories  
*Version 0.1 – 2025-07-14*

> This companion to `docs/new_dev_kickoff_plan.md` gives **repo-specific** guidance so a freshly onboarded engineer can become productive in <1 day and hit the first milestone within a week.  Each section lists *context*, *day-1 setup*, *week-1 deliverables*, and *key code areas/links*.

---
## Index  
1. twitter-sdk  
2. sentiment-pipeline  
3. ml-backtester  
4. hedge-engine  
5. trends-sdk *(future)*

---
## 1  twitter-sdk

### 1.1 Context & Goals
High-throughput Twitter ingestion with **BotFilter** integration and export CLI producing gzip NDJSON files that downstream repos can read.

### 1.2 Day-1 Checklist
- [ ] `git clone` the repo; create & activate Python 3.11 venv.  
- [ ] `pip install -e ".[dev]"` – brings in Tweepy, pytest, ruff.  
- [ ] Run `pytest -q` – should pass (skeleton tests only).  
- [ ] Scan `src/` structure: `core`, `services/`, `apps/moderation_ui`, Prometheus metrics.  
- [ ] Read `docs/TwitterScraper.md` (architecture) **end-to-end**.

### 1.3 Week-1 Milestones
| Milestone | Description | Acceptance  |
|-----------|-------------|-------------|
| **CLI Exporter** | `python -m twitter_sdk.export --day 2025-07-13 --out s3://crypto-data/tweets/` writes *gzip NDJSON* | 1 day’s data visible in S3 path  |
| **Filtered Stream** | Switch from sample stream to filtered stream with crypto keyword rules | Tweets for BTC/ETH appear in `export/` folder |
| **BotFilter Hook** | Add placeholder call `BotFilter.is_bot(user)` from sentiment-pipeline stub | CLI log shows `bot_flag` field |
| **CI Green** | GitHub Actions runs lint + tests on PRs | ✓ badge |

### 1.4 Key Code Areas
| Path | Purpose |
|------|---------|
| `src/services/scraper` | Tweepy client & ingest loop |
| `src/services/writer` | Future posting; ignore for now |
| `src/core` | Settings loader, logging, secrets |
| `docs/TwitterScraper.md` | Full stack diagram |

---
## 2  sentiment-pipeline

### 2.1 Context & Goals
Cleaning, feature engineering, and sentiment scoring **(model placeholder)**.  Implements **BotFilter**, data schema, and tiered LLM router skeleton.

### 2.2 Day-1 Checklist
- [ ] Clone repo skeleton (may need to create from kickoff plan).  
- [ ] `pip install -e ".[dev]"` (Transformers optional for now).  
- [ ] Run `pytest -q` – should collect placeholder tests.  
- [ ] Read `docs/research_integration_notes.md` sections on BotFilter & time-decay.

### 2.3 Week-1 Milestones
| Milestone | Description | Acceptance |
|-----------|-------------|------------|
| **Schema v0.1** | `schema.py` Pydantic models align with data fields from twitter-sdk exporter (incl. liquidity, whale metrics placeholders) | Passing unit test: model parses sample JSON |
| **BotFilter MVP** | `BotFilter` class wraps Botometer REST call; falls back to heuristic if API key missing | `pytest tests/test_bot_filter.py -q` green |
| **LLM Router Stub** | `models/router.py` chooses between `llama_local` and `gpt4_gateway` by confidence & cost | Unit test shows correct routing logic |
| **CI & Coverage ≥80 %** | GitHub Actions runs lint, tests, coverage gate | ✓ badge |

### 2.4 Key Code Areas
| Path | Purpose |
|------|---------|
| `sentiment_pipeline/schema.py` | Unified data model |
| `sentiment_pipeline/bot_filter.py` | Bot detection logic |
| `sentiment_pipeline/models/` | Tiered LLM wrappers and router |
| `tests/` | Expectation contracts |

---
## 3  ml-backtester

### 3.1 Context & Goals
Historical replay, metric calculation, and evaluation harness (*strategy placeholder*).  Reads Parquet/CSV exported by other repos.

### 3.2 Day-1 Checklist
- [ ] Clone repo, install dev deps, run tests.  
- [ ] Familiarise with `data_loader.py`, `engine.py` stubs.  
- [ ] Ensure local data folder with one day of sample exports (use `scripts/transfer_data.py`).

### 3.3 Week-1 Milestones
| Milestone | Description | Acceptance |
|-----------|-------------|------------|
| **DataLoader v0.1** | Reads Parquet tweets & price candles into Polars/Pandas | CLI prints row counts |
| **Engine Loop Skeleton** | `BacktestEngine.run()` iterates time-steps & logs stub metrics | Runs on 1-day sample without error |
| **Liquidity Metrics Script** | Separate module computes `spread_Δ`, `depth1pct`, `realised_vol` from order-book snapshots | Unit test verifies numeric output |
| **Config-Driven CLI** | `python -m ml_backtester.run --config configs/baseline.yaml` picks symbols & date | CLI prints config echo |

### 3.4 Key Code Areas
| Path | Purpose |
|------|---------|
| `ml_backtester/data_loader.py` | I/O helpers |
| `ml_backtester/engine.py` | Core backtest loop |
| `configs/` | YAML configs per experiment |

---
## 4  hedge-engine

### 4.1 Context & Goals
Map Swing Score + liquidity deltas → hedge size via REST API; containerised micro-service.

### 4.2 Day-1 Checklist
- [ ] Clone repo, build Docker image `docker build .`.  
- [ ] Run `uvicorn app.main:app --reload` locally; `curl /hedge` returns stub JSON.  
- [ ] Skim `MasterPlan.md` hedge sizing section.

### 4.3 Week-1 Milestones
| Milestone | Description | Acceptance |
|-----------|-------------|------------|
| **Env-Config** | `.env` ‑> Pydantic `Settings`; configures risk params & Redis cache | Local run shows loaded settings |
| **Score Lookup** | Endpoint reads latest Swing Score from Redis/S3 mock & returns placeholder hedge pct | Unit test uses Fakeredis |
| **Swagger Docs** | Automatic FastAPI docs describe `/hedge` request/response | `/docs` renders |
| **Docker CI** | GitHub Actions builds & pushes image to org registry on tags | ✓ badge |

### 4.4 Key Code Areas
| Path | Purpose |
|------|---------|
| `hedge_engine/app/main.py` | FastAPI app factory |
| `hedge_engine/core/settings.py` | Config loader |
| `Dockerfile` | Container spec |

---
## 5  trends-sdk *(future placeholder)*
Pending extraction of Google Trends logic from web-search-sdk.  Not active in kickoff; ignore until Phase 2.

---
### FAQ / Common Pitfalls
- **Missing AWS creds** – use `localstack` profile in dev, see each repo `.env.example`.
- **Botometer rate-limits** – cache results in Redis or run offline test fixtures.
- **Large Parquet files** – use `scripts/sample_parquet.py` to down-sample for unit tests.

---
*Edit this file as tasks evolve; keep version/date in header updated.* 
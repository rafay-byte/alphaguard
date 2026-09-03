<![CDATA[<div align="center">

# 🛡️ AlphaGuard AI

### Autonomous · Explainable · Risk-First AI Options Trading Platform

**Built for the [Alpaca AI Trading Agents Hackathon](https://alpaca.markets)**

> **AI PROPOSES · RISK PROTECTS · ALPACA EXECUTES · EVERY DECISION IS EXPLAINABLE**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![Alpaca Trading API](https://img.shields.io/badge/Alpaca-Trading%20API-yellow.svg)](https://alpaca.markets)
[![Alpaca MCP Server](https://img.shields.io/badge/Alpaca-MCP%20Server-blueviolet.svg)](https://github.com/alpacahq/alpaca-mcp-server)
[![Options Trading](https://img.shields.io/badge/Options-Trading-orange.svg)](#options-trading)
[![Tests](https://img.shields.io/badge/tests-15%2F15%20passing-brightgreen.svg)](#running-tests)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

</div>

---

AlphaGuard AI is an **8-agent AI Investment Committee** that researches market opportunities, debates its own trade thesis (bull vs. bear), enforces **deterministic, LLM-independent risk controls**, executes approved **options trades** through **Alpaca paper trading**, monitors open positions autonomously, and learns from outcomes through automated AI post-mortems.

This is not "an AI that predicts stock prices." The LLM **never** has unrestricted trading authority — every single proposal must pass a Python risk engine before it can reach Alpaca.

### 🏆 Hackathon Compliance

| Requirement | Implementation | Status |
|---|---|---|
| **Alpaca Trading API** | `alpaca-py` SDK — orders, positions, account, market data | ✅ |
| **Alpaca MCP Server** | Official `alpaca-mcp-server` via `uvx` over stdio — Market Analyst pulls live account context | ✅ |
| **Options Trading** | Full options flow — `OptionHistoricalDataClient`, `get_option_chain`, contract selection, OCC symbol execution | ✅ |
| **Dedicated Paper Account** | Fresh paper trading account created for this submission | ✅ |

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AlphaGuard AI Pipeline                       │
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                          │
│  │  Market   │  │  Quant   │  │   News   │   Research Layer         │
│  │ Analyst   │  │ Analyst  │  │  Intel   │   (data → indicators)    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                          │
│       │              │             │                                │
│       ▼              ▼             ▼                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐                      │
│  │   Bull   │  │   Bear   │  │ Alternative  │   Debate Layer        │
│  │  Agent   │  │  Agent   │  │    Agent     │   (challenge thesis)  │
│  └────┬─────┘  └────┬─────┘  └──────┬───────┘                      │
│       │              │               │                              │
│       ▼              ▼               ▼                              │
│  ┌─────────────────────────────────────┐                            │
│  │         Strategy Agent              │   Synthesis Layer          │
│  │   (entry / stop / target / size)    │   (concrete proposal)      │
│  └──────────────┬──────────────────────┘                            │
│                 │                                                   │
│                 ▼                                                   │
│  ┌─────────────────────────────────────┐                            │
│  │         Decision Agent              │   Committee Chair          │
│  │   (final BUY / HOLD / NO TRADE)    │   (aggregate + vote)       │
│  └──────────────┬──────────────────────┘                            │
│                 │                                                   │
│  ═══════════════╪═══════════ FIREWALL ══════════════════════════    │
│                 │                                                   │
│                 ▼                                                   │
│  ┌─────────────────────────────────────┐                            │
│  │     Deterministic Risk Engine       │   Python-only gate         │
│  │  (10 checks, no LLM, no bypass)    │   (approves OR rejects)    │
│  └──────────────┬──────────────────────┘                            │
│                 │                                                   │
│            APPROVED?                                                │
│           /        \                                                │
│          ▼          ▼                                               │
│    ┌──────────┐  ┌────────┐                                        │
│    │  Alpaca  │  │REJECTED│                                        │
│    │  Paper   │  │(logged)│                                        │
│    │  Order   │  └────────┘                                        │
│    └────┬─────┘                                                    │
│         │                                                          │
│         ▼                                                          │
│    ┌──────────────────────┐                                        │
│    │  Position Monitor    │  APScheduler background job             │
│    │  (stop/target/exit)  │  → re-price → risk check → exit        │
│    └────┬─────────────────┘                                        │
│         │                                                          │
│         ▼                                                          │
│    ┌──────────────────────┐                                        │
│    │   AI Post-Mortem     │  Prediction vs. actual outcome          │
│    │   + Journal Entry    │  What worked · What failed · Next time  │
│    └──────────────────────┘                                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Quick Start (< 2 minutes)

```bash
# Clone / unzip
cd alphaguard-ai

# Set up Python environment
python -m venv venv
# Linux / macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure (leave keys blank to stay in DEMO MODE)
cp .env.example .env

# Run
python run.py
```

Open **http://localhost:5000**, register an account, and click **Scan Market**.

> **No API keys are required.** The app boots into fully-functional Demo Mode with deterministic simulated data, real quant math, and real risk engine logic — all clearly labeled in the UI.

---

## ✅ What's Real & Tested

Every feature listed below was exercised end-to-end against the running application.
**15/15 pytest passing + full live server smoke test, zero errors.**

| # | Feature | Verified |
|---|---------|----------|
| 1 | 8-agent AI Investment Committee with real-time Socket.IO progress | ✅ |
| 2 | Deterministic risk engine — approves good trades, rejects bad ones with exact reasons | ✅ |
| 3 | Deterministic quant engine (SMA/EMA/RSI/MACD/Bollinger/ATR/volatility) — real math | ✅ |
| 4 | Alpaca paper-trading service with automatic demo-mode fallback | ✅ |
| 5 | **Alpaca MCP Server** — Market Analyst agent pulls live account context via official `alpaca-mcp-server` | ✅ |
| 6 | **Options trading** — real option chains, contract selection, OCC symbol execution | ✅ |
| 7 | AI provider abstraction (OpenAI/Anthropic/Gemini) with demo fallback | ✅ |
| 8 | Full trade lifecycle: scan → analyze → decide → risk check → execute → monitor → close | ✅ |
| 9 | AI Post-Mortem after every closed trade | ✅ |
| 10 | Apple-inspired "Liquid Glass" UI with animated agent flow | ✅ |
| 11 | Chart.js equity curves and execution timelines | ✅ |
| 12 | Authentication with hashed passwords (Flask-Login) | ✅ |
| 13 | APScheduler background position monitor (stop-loss / take-profit) | ✅ |
| 14 | Strategy Lab historical backtester (SMA crossover) | ✅ |
| 15 | Full audit trail / AI Journal | ✅ |
| 16 | Real-time UI updates via WebSocket (no manual refresh) | ✅ |
| 17 | Comprehensive test suite (risk engine, indicators, position sizing, auth, demo mode) | ✅ |

---

## 🏗️ Architecture

### The Three Layers

1. **AI Layer** — 8 specialized agents form an Investment Committee. Each agent receives deterministic data from the quant engine and produces a structured JSON assessment. AI-generated opinions **never** directly move money.

2. **Risk Layer** — A pure-Python `RiskEngine` class that is **100% independent of any LLM**. Ten deterministic checks (stop-loss validity, risk/reward ratio, confidence threshold, position sizing, buying power, max open positions, duplicate exposure, daily loss limit, portfolio drawdown, capital requirement) must all pass before any order reaches Alpaca. The AI cannot bypass this gate.

3. **Execution Layer** — The Alpaca paper-trading client submits market orders (including options with OCC symbols), tracks positions, and monitors stop-loss/take-profit levels via an APScheduler background job. Automatically degrades to clearly-labeled demo mode if Alpaca credentials are missing or a call fails.

### Alpaca Integration

| Product | How It's Used | File |
|---------|---------------|------|
| **Alpaca Trading API** (`alpaca-py`) | Submit orders, get account/positions/orders, close positions | `broker/client.py` |
| **Alpaca Options Data API** | `OptionHistoricalDataClient` — fetch option chains, strikes, expirations, latest premiums | `broker/client.py` |
| **Alpaca MCP Server** (official) | Market Analyst agent connects to `alpaca-mcp-server` over stdio via MCP protocol to pull live account context (equity, buying power, positions) into its analysis | `services/mcp_client.py`, `agents/market_agent.py` |

### Options Trading Flow

```
Strategy Agent
  → alpaca_service.get_option_chain(ticker)     # Fetch available contracts
  → Select ATM call/put based on market regime
  → alpaca_service.get_latest_option_price()    # Price the contract
  → Build proposal with OCC symbol (e.g. AAPL260918C00230000)
  → Risk Engine validates option-specific fields
  → Trade Executor submits order with OCC symbol via Alpaca API
```

### The 8 Agents

| Agent | Role | Uses AI? |
|-------|------|----------|
| **Market Analyst** | Trend/regime classification + live account context via **Alpaca MCP Server** | ✅ (with deterministic fallback) |
| **Quant Analyst** | Indicator computation + composite scoring | ❌ Pure math |
| **News Intel** | Sentiment analysis + risk event detection | ✅ (demo mode by default) |
| **Bull Agent** | Constructs the strongest case FOR the trade | ✅ (with deterministic fallback) |
| **Bear Agent** | Attacks the trade thesis with counterarguments | ✅ (with deterministic fallback) |
| **Alternative Agent** | Ranks all watchlist tickers — "is this really the best opportunity?" | ❌ Pure math |
| **Strategy Agent** | Selects optimal options contract + entry/stop/target/size | ✅ (with deterministic fallback) |
| **Decision Agent** | Committee chair — final BUY/HOLD/NO TRADE vote | ❌ Deterministic rules |

### Risk Engine Checks (10 Gates)

```
1. Stop-loss / entry price sanity
2. Risk/reward ratio ≥ configurable minimum (default 1.5:1)
3. AI confidence ≥ configurable minimum (default 65%)
4. Position sizing (equity × risk% → shares, capped by position limit)
5. Maximum position % of portfolio (default 10%)
6. Buying power availability
7. Maximum open positions (default 10)
8. Duplicate exposure prevention
9. Daily loss limit (default 2%)
10. Portfolio drawdown limit (default 10%)
```

All thresholds are configurable via environment variables. Every rejection includes the exact reason(s), shown in the UI and logged to the journal.

---

## 📁 Project Structure

```
alphaguard-ai/
│
├── app.py                          # Flask application factory
├── run.py                          # Entrypoint (python run.py)
├── config.py                       # Environment-driven configuration
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template
├── .gitignore
│
├── agents/                         # AI Investment Committee
│   ├── committee.py                #   Orchestrator (runs full pipeline per ticker)
│   ├── market_agent.py             #   Trend/regime analysis
│   ├── quant_agent.py              #   Quant indicator scoring
│   ├── news_agent.py               #   News intelligence
│   ├── bull_agent.py               #   Bull case builder
│   ├── bear_agent.py               #   Bear case challenger
│   ├── alternative_agent.py        #   Cross-ticker opportunity ranking
│   ├── strategy_agent.py           #   Entry/stop/target/size proposal
│   ├── decision_agent.py           #   Committee chair (final vote)
│   └── postmortem_agent.py         #   Post-trade AI analysis
│
├── broker/                         # Alpaca paper-trading service
│   └── client.py                   #   Full client with demo fallback + CLI integration
│
├── trading/                        # Core trading infrastructure
│   ├── indicator_engine.py         #   SMA/EMA/RSI/MACD/BB/ATR/vol (pure math)
│   ├── risk_engine.py              #   Deterministic 10-check risk gate
│   ├── strategy_engine.py          #   Trade proposal builder (ATR-based)
│   ├── position_sizer.py           #   Deterministic position sizing
│   ├── trade_executor.py           #   Approved trade → Alpaca order + audit
│   ├── position_monitor.py         #   Live stop/target monitoring
│   ├── postmortem.py               #   Prediction vs. outcome analysis
│   └── scheduler.py                #   APScheduler background monitoring job
│
├── services/                       # External service abstractions
│   ├── ai_service.py               #   OpenAI/Anthropic/Gemini + demo fallback
│   ├── market_service.py           #   Alpaca bars → indicators → scores
│   ├── mcp_client.py               #   Alpaca MCP Server client (JSON-RPC over stdio)
│   ├── news_service.py             #   News API (demo mode by default)
│   └── notification_service.py     #   Real-time notification dispatch
│
├── .agents/
│   └── mcp_config.json             #   Official Alpaca MCP Server config (uvx)
│
├── models/                         # SQLAlchemy data models
│   ├── __init__.py                 #   db instance + model imports
│   ├── user.py                     #   User (auth, hashed passwords)
│   ├── trade.py                    #   Trade (full lifecycle)
│   ├── position.py                 #   Position (open/closed, P&L)
│   ├── agent_decision.py           #   Agent decision audit records
│   ├── risk_check.py               #   Risk engine audit records
│   ├── audit_log.py                #   AI Journal entries
│   ├── market_snapshot.py          #   Market data snapshots
│   └── strategy.py                 #   Strategy definitions
│
├── routes/                         # Flask blueprints
│   ├── auth.py                     #   Login / Register / Logout
│   ├── dashboard.py                #   Main dashboard
│   ├── trading.py                  #   Trading pages
│   ├── agents.py                   #   Decision Room / Opportunities / Journal
│   ├── portfolio.py                #   Portfolio page
│   ├── risk.py                     #   Risk Center / Settings
│   ├── strategies.py               #   Strategy Lab
│   └── api.py                      #   JSON API (all frontend AJAX calls)
│
├── templates/                      # Jinja2 templates (Liquid Glass UI)
│   ├── base.html                   #   App shell (sidebar, topbar, badges)
│   ├── dashboard.html              #   Main dashboard
│   ├── decision_room.html          #   Agent pipeline visualizer
│   ├── opportunities.html          #   Market scan results
│   ├── portfolio.html              #   Positions + equity curve
│   ├── risk_center.html            #   Risk metrics dashboard
│   ├── strategy_lab.html           #   Backtest simulator
│   ├── journal.html                #   AI Journal (audit trail)
│   ├── trade_detail.html           #   Single trade + post-mortem
│   ├── login.html / register.html  #   Authentication
│   ├── settings.html               #   Configuration page
│   └── 404.html / 500.html         #   Error pages
│
├── static/
│   ├── css/
│   │   ├── main.css                #   Core design system
│   │   ├── liquid-glass.css        #   Glassmorphism effects
│   │   └── animations.css          #   Micro-animations
│   └── js/
│       ├── app.js                  #   Socket.IO init + globals
│       ├── dashboard.js            #   Dashboard interactivity
│       ├── decision-room.js        #   Agent pipeline animation
│       ├── agents.js               #   Agent status management
│       ├── charts.js               #   Chart.js configuration
│       ├── notifications.js        #   Toast notification system
│       └── trading.js              #   Trade execution UI
│
└── tests/                          # pytest suite (15 tests)
    ├── conftest.py                 #   App fixture (in-memory SQLite)
    ├── test_risk_engine.py         #   Risk engine approve/reject paths
    ├── test_indicators.py          #   SMA/EMA/RSI/composite scoring
    ├── test_position_sizer.py      #   Position sizing edge cases
    ├── test_demo_mode.py           #   App boots in demo mode
    └── test_auth_and_routes.py     #   Register/login/redirect
```

---

## 🔧 Configuration

### Environment Variables (`.env`)

```bash
# ==== Alpaca Paper Trading ====
ALPACA_API_KEY=                     # Leave blank for demo mode
ALPACA_SECRET_KEY=                  # Leave blank for demo mode
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# ==== Alpaca MCP Server ====
# Enables the Market Analyst agent to pull live account context
# from Alpaca's official MCP server (github.com/alpacahq/alpaca-mcp-server)
USE_ALPACA_MCP=true                 # Set to true to enable MCP integration

# ==== AI Provider ====
# Supported: openai, anthropic, gemini
AI_PROVIDER=openai
AI_API_KEY=                         # Leave blank for demo mode

# ==== App ====
SECRET_KEY=change-me-super-secret
DATABASE_URL=sqlite:///alphaguard.db
APP_ENV=development
DEMO_MODE=true

# ==== Risk Engine Tuning (optional) ====
MAX_POSITION_PERCENT=10             # Max % of equity per position
MAX_TRADE_RISK_PERCENT=1            # Max % of equity risked per trade
MAX_DAILY_LOSS_PERCENT=2            # Max daily loss before trading halted
MAX_PORTFOLIO_DRAWDOWN_PERCENT=10   # Max drawdown before trading halted
MAX_OPEN_POSITIONS=10               # Max concurrent positions
MIN_RISK_REWARD=1.5                 # Min reward:risk ratio
MIN_CONFIDENCE=65                   # Min AI confidence score (0-100)
MONITOR_INTERVAL_SECONDS=60         # Position monitor polling interval
```

### Demo Mode

Demo Mode activates **automatically** whenever `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, or `AI_API_KEY` is blank. In this mode:

- **Market data** uses a deterministic-per-ticker random walk (seeded, so it's internally consistent)
- **Quant indicators** are computed with **real math** on the simulated bars
- **AI agents** return structured deterministic fallback responses (clearly labeled `DEMO_MODE`)
- **Orders** are simulated locally (clearly labeled `DEMO`)
- The **risk engine** runs identical logic regardless of mode
- All demo content is **clearly labeled in the UI** with badges and markers

### Connecting Real Alpaca Paper Trading

1. Create a free account at [alpaca.markets](https://alpaca.markets)
2. Switch to **Paper Trading** in your Alpaca dashboard
3. Generate API keys from the paper account
4. Add them to `.env` and restart the app
5. The UI badges will switch from "ALPACA DEMO" → "ALPACA CONNECTED"

### Connecting an AI Provider

Set `AI_PROVIDER` to `openai`, `anthropic`, or `gemini` and provide your API key in `AI_API_KEY`. The agents will use real LLM completions instead of deterministic fallbacks.

---

## 🧪 Running Tests

```bash
pip install pytest
pytest tests/ -v
```

Expected output:

```
tests/test_auth_and_routes.py::test_register_login_dashboard     PASSED
tests/test_auth_and_routes.py::test_login_required_redirects     PASSED
tests/test_demo_mode.py::test_app_boots_in_demo_mode             PASSED
tests/test_demo_mode.py::test_alpaca_service_demo_account        PASSED
tests/test_indicators.py::test_sma_basic                         PASSED
tests/test_indicators.py::test_ema_moves_toward_recent_price     PASSED
tests/test_indicators.py::test_rsi_bounds                        PASSED
tests/test_indicators.py::test_compute_all_indicators_and_score  PASSED
tests/test_position_sizer.py::test_position_sizing_basic         PASSED
tests/test_position_sizer.py::test_position_sizing_zero_when_no_stop_distance PASSED
tests/test_risk_engine.py::test_approves_good_trade              PASSED
tests/test_risk_engine.py::test_rejects_low_confidence           PASSED
tests/test_risk_engine.py::test_rejects_bad_risk_reward          PASSED
tests/test_risk_engine.py::test_rejects_duplicate_exposure       PASSED
tests/test_risk_engine.py::test_rejects_max_positions            PASSED

15 passed
```

---

## 🎬 Hackathon Demo Script

1. **Dashboard** — Note the status badges: `DEMO MODE` · `ALPACA DEMO` · `AI ENGINE DEMO` · `PAPER TRADING`
2. **Scan Market** — Click it. Watch the watchlist get ranked by the deterministic quant engine
3. **Decision Room** — Select a ticker, click **Run Investment Committee**
   - Watch each agent animate: `WAITING → ANALYZING → COMPLETE` in real time over WebSocket
4. **Committee Result** — Review the final decision, confidence meter, and individual agent scores
5. **Risk Verdict** — See `RISK APPROVED ✅` or `RISK REJECTED ❌` with exact reason(s)
6. **Execute** — If approved, click **Execute Paper Trade**. Watch the execution timeline animate through to `POSITION ACTIVE`
7. **Portfolio** — See the live position and equity curve (Chart.js)
8. **Close Position** — Close it manually (or let the background monitor catch a stop/target)
9. **Post-Mortem** — Open the trade detail page. See the AI Post-Mortem: prediction vs. outcome, what worked, what failed, future recommendation
10. **AI Journal** — Full chronological audit trail of every system event
11. **Strategy Lab** — Run a labeled SMA-crossover backtest simulation with equity curve

---

## 🎨 Design

The UI follows an **Apple-inspired "Liquid Glass"** design language:

- Translucent glass panels with backdrop blur
- Soft pastel gradients and animated background blobs
- Premium micro-interactions (hover effects, transitions, pulse indicators)
- Chart.js-rendered equity curves and performance visualizations
- Real-time Socket.IO updates (no manual page refresh)
- `prefers-reduced-motion` support for accessibility
- Fully responsive layout

---

## ⚠️ Known Limitations (Honest)

These are documented here because transparency matters more than marketing:

1. **News Intelligence** runs in deterministic demo mode by default. No live news API is wired in — the `services/news_service.py` interface is ready for one (e.g., Benzinga, NewsAPI.org, or Alpaca News).

2. **AI provider HTTP call paths** (OpenAI, Anthropic, Gemini) are implemented in `services/ai_service.py` but were **only validated against the demo-mode fallback path**. No external AI API key was available in the build/test environment. The HTTP call code is complete and follows each provider's documented API — it just wasn't live-tested against a real key.

3. **Sector-level concentration limits** are noted as an extension point in the risk engine but not implemented (would require a market-data provider with sector classifications).

4. **Demo-mode market data** is a seeded random walk that produces consistent-per-ticker prices but evolves slightly between calls in the same session (to feel "live"). Exact numbers will differ between runs. This does **not** affect the real quant math, risk engine, or trading logic.

5. **WebSocket transport** falls back to long-polling in threading mode on Windows. The Socket.IO WebSocket upgrade attempt produces a benign `ConnectionError` in server logs — this is a known Flask-SocketIO/threading-mode behavior, not an application bug.

---

## 🛣️ Future Improvements

- [ ] Live news API integration (Alpaca News, Benzinga, or NewsAPI.org)
- [ ] Sector/industry concentration limits in the risk engine
- [ ] Multi-user portfolio-level drawdown tracking across sessions
- [ ] WebSocket-driven live price ticking on Portfolio and Risk Center
- [ ] Persisted per-user risk configuration (Settings page currently reads global defaults)
- [ ] Options flow analysis agent
- [ ] Multi-timeframe indicator analysis (currently daily bars only)
- [ ] Production deployment guide (Gunicorn + Redis for Socket.IO)

---

## 🔒 Safety Disclaimer

This platform is for **educational and experimental purposes only** and does not provide financial advice. It trades exclusively through **Alpaca paper trading** by default; live trading is **never** enabled automatically. Past performance shown in Strategy Lab backtests does not guarantee future results. Always do your own research.

---

## 📄 Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Flask 3.0, Flask-SocketIO, Flask-Login, Flask-SQLAlchemy |
| Database | SQLite (default, swappable via `DATABASE_URL`) |
| AI | OpenAI / Anthropic / Gemini via REST (with full demo fallback) |
| Broker | Alpaca paper trading via `alpaca-py` + Alpaca CLI (optional) |
| MCP | Alpaca's official `alpaca-mcp-server` via `uvx` (JSON-RPC over stdio) |
| Options | `OptionHistoricalDataClient` — chains, strikes, premiums, OCC symbols |
| Scheduler | APScheduler (background position monitoring) |
| Frontend | Jinja2 templates, vanilla CSS (Liquid Glass), vanilla JS |
| Charts | Chart.js 4.x |
| Real-time | Socket.IO (Flask-SocketIO + client) |
| Testing | pytest |

---

<div align="center">

**Built with 🛡️ by AlphaGuard AI**

*AI proposes. Risk protects. Alpaca executes. Every decision is explainable.*

</div>
]]>

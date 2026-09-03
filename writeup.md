# AlphaGuard AI - Hackathon 1-Page Write-Up

## Overview
AlphaGuard AI is an autonomous, explainable options trading platform built for the Alpaca AI Trading Agents Hackathon. It solves a critical problem in AI-driven finance: **trust**. Rather than giving an LLM unrestricted access to a brokerage account, AlphaGuard separates *ideation* from *execution* using an 8-agent Investment Committee and a strict, deterministic Risk Engine.

## AI Logic: The 8-Agent Committee
Our AI architecture mirrors a quantitative hedge fund. Instead of a single LLM prompt, 8 specialized agents debate every trade:
1. **Market Analyst:** Classifies the current market regime (trending, ranging, volatile).
2. **Quant Analyst:** Computes deterministic technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands, ATR).
3. **News Intelligence:** Analyzes real-time sentiment and flags macroeconomic risk events.
4. **Bull Agent:** Constructs the strongest possible thesis *for* the trade.
5. **Bear Agent:** Actively attacks the bull thesis to find weaknesses.
6. **Alternative Agent:** Scans the broader watchlist to ask "is this the best use of capital?"
7. **Strategy Agent:** Synthesizes the debate into a concrete Options Trade Proposal (e.g., BUY CALL at strike X).
8. **Decision Agent:** Acts as the committee chair, casting the final BUY/HOLD/NO TRADE vote based on a weighted composite score.

This multi-agent debate produces a detailed "AI Post-Mortem" and Journal entry for every decision, ensuring 100% explainability.

## Risk Gates: The Deterministic Firewall
If the AI Committee votes "BUY", the proposal hits the **Risk Engine**. This is a pure-Python module that is **100% independent of any LLM**. The AI cannot bypass it. The proposal must pass 10 strict checks:
1. **Options Validity:** Checks that the proposed option expiration is valid.
2. **Reward/Risk Ratio:** Enforces a minimum asymmetric payout profile (e.g., > 1.5:1).
3. **Confidence Threshold:** The AI's composite score must exceed 65%.
4. **Position Sizing:** Dynamically calculates contract quantities based on a maximum equity risk cap (e.g., 1% of portfolio per trade).
5. **Position Cap:** Enforces a maximum allocation (e.g., 10% of equity) per position.
6. **Buying Power:** Verifies sufficient capital.
7. **Max Open Positions:** Prevents over-trading (cap at 10 concurrent trades).
8. **Duplicate Exposure:** Blocks multiple overlapping trades on the same underlying ticker.
9. **Daily Loss Limit:** Halts trading if the portfolio drops >2% in a single day (circuit breaker).
10. **Drawdown Limit:** Halts trading if the portfolio falls >10% from its peak.

If any check fails, the trade is rejected and logged. Only if all 10 pass does the trade proceed.

## Alpaca Infrastructure
We leverage Alpaca's full product suite — API, CLI, and MCP server — for data, execution, and agent tooling:
- **Alpaca Trading API:** Used via `alpaca-py` to submit options orders, monitor open positions, and execute stop-loss / take-profit exits.
- **Alpaca Options Data API:** Provides the option chains, strikes, expirations, and latest premium quotes used by the Strategy Agent to select the optimal contract.
- **Alpaca CLI Integration:** Trade execution can be routed through Alpaca's official CLI binary (`alpaca order submit --symbol <OCC_SYMBOL> --side buy --qty <N> --type market`) via subprocess, making every order auditable in the terminal. Controlled by `USE_ALPACA_CLI=true`. The SDK path remains as fallback.
- **Alpaca MCP Server (Official):** The Market Analyst agent connects to Alpaca's official `alpaca-mcp-server` (github.com/alpacahq/alpaca-mcp-server) over stdio using the Model Context Protocol. It pulls live account context (equity, buying power, open positions) directly into the agent's analysis prompt, giving the AI portfolio awareness before recommending trades. Controlled by `USE_ALPACA_MCP=true`.
- **Background Position Monitor:** An `APScheduler` job runs constantly, fetching live quotes via Alpaca to manage active options positions and trigger exits autonomously.

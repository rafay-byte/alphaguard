"""
AlphaGuard AI - Investment Committee Orchestrator
====================================================
Runs the full pipeline for one ticker:
MARKET -> QUANT -> NEWS -> BULL/BEAR -> ALTERNATIVE -> STRATEGY -> DECISION

Emits websocket progress events at each stage so the Decision Room UI can
animate agents from WAITING -> ANALYZING -> COMPLETE in real time.
"""
from services.market_service import get_market_snapshot
from services.news_service import news_service
from services.ai_service import ai_service as default_ai_service
from agents.market_agent import run_market_agent
from agents.quant_agent import run_quant_agent
from agents.news_agent import run_news_agent
from agents.bull_agent import run_bull_agent
from agents.bear_agent import run_bear_agent
from agents.alternative_agent import run_alternative_agent
from agents.strategy_agent import run_strategy_agent
from agents.decision_agent import run_decision_agent

AGENT_SEQUENCE = ["market", "quant", "news", "bull", "bear", "alternative", "strategy", "risk"]


def _emit(socketio, event, payload):
    if socketio:
        socketio.emit(event, payload)


def scan_universe(tickers, alpaca_service):
    """Quick quant-only scan across the whole watchlist, used for the
    Opportunities screen and for the Alternative Agent's comparison."""
    results = {}
    for ticker in tickers:
        snap = get_market_snapshot(ticker, alpaca_service)
        results[ticker] = snap
    return results


def run_committee(ticker, alpaca_service, ai_service=None, socketio=None, watchlist=None):
    ai_service = ai_service or default_ai_service
    watchlist = watchlist or [ticker]
    if ticker not in watchlist:
        watchlist = watchlist + [ticker]

    _emit(socketio, "agent_started", {"agent": "market", "ticker": ticker})
    snapshot = get_market_snapshot(ticker, alpaca_service)
    indicators, scores = snapshot["indicators"], snapshot["scores"]

    market = run_market_agent(ticker, indicators, scores, ai_service)
    _emit(socketio, "agent_completed", {"agent": "market", "ticker": ticker, "result": market})

    _emit(socketio, "agent_started", {"agent": "quant", "ticker": ticker})
    quant = run_quant_agent(ticker, indicators, scores)
    _emit(socketio, "agent_completed", {"agent": "quant", "ticker": ticker, "result": quant})

    _emit(socketio, "agent_started", {"agent": "news", "ticker": ticker})
    news = run_news_agent(ticker, news_service)
    _emit(socketio, "agent_completed", {"agent": "news", "ticker": ticker, "result": news})

    _emit(socketio, "agent_started", {"agent": "bull", "ticker": ticker})
    bull = run_bull_agent(ticker, market, quant, news, ai_service)
    _emit(socketio, "agent_completed", {"agent": "bull", "ticker": ticker, "result": bull})

    _emit(socketio, "agent_started", {"agent": "bear", "ticker": ticker})
    bear = run_bear_agent(ticker, market, quant, news, ai_service)
    _emit(socketio, "agent_completed", {"agent": "bear", "ticker": ticker, "result": bear})

    _emit(socketio, "agent_started", {"agent": "alternative", "ticker": ticker})
    universe_scores = {}
    for t in watchlist:
        if t == ticker:
            universe_scores[t] = scores["overall_score"]
        else:
            other_snap = get_market_snapshot(t, alpaca_service)
            universe_scores[t] = other_snap["scores"]["overall_score"]
    alternative = run_alternative_agent(universe_scores)
    _emit(socketio, "agent_completed", {"agent": "alternative", "ticker": ticker, "result": alternative})

    _emit(socketio, "agent_started", {"agent": "strategy", "ticker": ticker})
    strategy = run_strategy_agent(ticker, indicators, scores, bull, bear, news, ai_service)
    _emit(socketio, "agent_completed", {"agent": "strategy", "ticker": ticker, "result": strategy})

    decision = run_decision_agent(ticker, market, quant, news, bull, bear, alternative, strategy)

    return {
        "ticker": ticker,
        "snapshot": snapshot,
        "market": market,
        "quant": quant,
        "news": news,
        "bull": bull,
        "bear": bear,
        "alternative": alternative,
        "strategy": strategy,
        "decision": decision,
    }

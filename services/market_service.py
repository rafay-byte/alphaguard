"""
AlphaGuard AI - Market Service
Thin orchestration layer combining Alpaca bars + the indicator engine.
"""
from trading.indicator_engine import compute_all_indicators, quant_score


def get_market_snapshot(ticker, alpaca_service):
    bars = alpaca_service.get_historical_bars(ticker, days=90)
    indicators = compute_all_indicators(bars)
    scores = quant_score(indicators)
    return {"ticker": ticker, "bars": bars, "indicators": indicators, "scores": scores}

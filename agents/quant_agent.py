"""Quant Agent - wraps the deterministic indicator engine (no LLM math)."""


def run_quant_agent(ticker, indicators, scores):
    reasoning = (
        f"RSI {indicators.get('rsi')}, MACD {indicators.get('macd')}, "
        f"momentum {indicators.get('momentum')}%, volume change {indicators.get('volume_change')}%. "
        f"Composite quant score: {scores['overall_score']}."
    )
    return {
        "ticker": ticker,
        "indicators": indicators,
        "scores": scores,
        "reasoning": reasoning,
        "score": scores["overall_score"],
        "_source": "DETERMINISTIC",
    }

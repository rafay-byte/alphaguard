"""Market Analyst Agent - trend / regime analysis."""


def run_market_agent(ticker, indicators, scores, ai_service):
    price = indicators.get("price")
    sma20, sma50 = indicators.get("sma20"), indicators.get("sma50")

    if price and sma20 and sma50 and price > sma20 > sma50:
        regime = "TRENDING_UP"
        trend = "BULLISH"
    elif price and sma20 and sma50 and price < sma20 < sma50:
        regime = "TRENDING_DOWN"
        trend = "BEARISH"
    else:
        regime = "RANGING"
        trend = "NEUTRAL"

    def fallback():
        reasoning = (
            f"{ticker} is trading at {price}, "
            f"{'above' if sma20 and price > sma20 else 'near/below'} its 20-day average. "
            f"Market regime classified as {regime.replace('_', ' ').title()}."
        )
        return {
            "ticker": ticker, "trend": trend, "confidence": round(scores['overall_score'] / 100, 2),
            "market_regime": regime, "reasoning": reasoning, "score": scores["trend_score"],
        }

    system = "You are a professional market analyst. Respond ONLY with JSON matching the schema."
    user = (
        f"Ticker: {ticker}\nPrice: {price}\nSMA20: {sma20}\nSMA50: {sma50}\n"
        f"Quant scores: {scores}\n"
        'Schema: {"ticker": str, "trend": "BULLISH|BEARISH|NEUTRAL", "confidence": float(0-1), '
        '"market_regime": str, "reasoning": str, "score": float(0-100)}'
    )
    return ai_service.complete_json(system, user, fallback)

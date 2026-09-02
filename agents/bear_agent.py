"""Bear Agent - attacks the proposed trade."""


def run_bear_agent(ticker, market, quant, news, ai_service):
    def fallback():
        risks = []
        rsi_v = quant["indicators"].get("rsi")
        if rsi_v and rsi_v > 70:
            risks.append(f"RSI at {rsi_v} signals overbought conditions - reversal risk is elevated.")
        if quant["indicators"].get("volatility", 0) and quant["indicators"].get("volatility", 0) > 40:
            risks.append(f"Annualized volatility of {quant['indicators'].get('volatility')}% raises position risk.")
        if news.get("negative_factors"):
            risks.extend(news["negative_factors"][:2])
        if quant["scores"]["trend_score"] < 45:
            risks.append("Trend structure is weak or breaking down.")
        if not risks:
            risks.append("No major red flags detected, but any thesis carries execution and macro risk.")
        bear_score = round(100 - quant["scores"]["overall_score"] * 0.5 - news.get("sentiment_score", 50) * 0.3, 1)
        bear_score = max(5, min(95, bear_score))
        return {"ticker": ticker, "bear_score": bear_score, "risks": risks,
                "confidence": round(bear_score / 100, 2)}

    system = "You are the Bear Agent on an AI investment committee. Challenge the trade thesis. Respond ONLY with JSON."
    user = (
        f"Ticker: {ticker}\nMarket: {market}\nQuant indicators: {quant['indicators']}\nNews: {news}\n"
        'Schema: {"ticker": str, "bear_score": float(0-100), "risks": [str,...], "confidence": float(0-1)}'
    )
    return ai_service.complete_json(system, user, fallback)

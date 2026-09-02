"""Bull Agent - constructs the strongest case FOR the trade."""


def run_bull_agent(ticker, market, quant, news, ai_service):
    def fallback():
        args = []
        if quant["scores"]["trend_score"] > 60:
            args.append("Price structure remains above key moving averages, confirming trend strength.")
        if quant["scores"]["momentum_score"] > 55:
            args.append("Momentum indicators show continued positive acceleration.")
        if quant["scores"]["volume_score"] > 55:
            args.append("Volume is confirming the price move rather than diverging from it.")
        if news.get("sentiment_score", 0) > 55:
            args.append("News sentiment is net positive, supporting the bullish thesis.")
        if not args:
            args.append("Limited bullish confirmation currently, but downside appears contained near support.")
        bull_score = round((quant["scores"]["overall_score"] * 0.6 + news.get("sentiment_score", 50) * 0.4), 1)
        return {"ticker": ticker, "bull_score": bull_score, "arguments": args,
                "confidence": round(bull_score / 100, 2)}

    system = "You are the Bull Agent on an AI investment committee. Argue FOR the trade. Respond ONLY with JSON."
    user = (
        f"Ticker: {ticker}\nMarket: {market}\nQuant scores: {quant['scores']}\nNews: {news}\n"
        'Schema: {"ticker": str, "bull_score": float(0-100), "arguments": [str,...], "confidence": float(0-1)}'
    )
    return ai_service.complete_json(system, user, fallback)

"""Decision Agent - the AI Investment Committee chair. Combines every
agent's output into a final recommendation. Cannot bypass the risk engine -
that check happens separately, afterward, in Python."""


def run_decision_agent(ticker, market, quant, news, bull, bear, alternative, strategy):
    scores = {
        "TECHNICAL": market.get("score", quant["scores"]["trend_score"]),
        "QUANT": quant["scores"]["overall_score"],
        "NEWS": news.get("sentiment_score", 50),
        "BULL": bull.get("bull_score", 50),
        "BEAR": bear.get("bear_score", 50),
    }

    final_decision = strategy.get("action", "BUY") if strategy else "BUY"
    confidence = strategy.get("confidence", 65.0) if strategy else 65.0

    reasoning = (
        f"Technical {scores['TECHNICAL']}, Quant {scores['QUANT']}, News {scores['NEWS']}, "
        f"Bull {scores['BULL']} vs Bear {scores['BEAR']}. "
        f"Committee consensus: {final_decision} on {ticker} with {confidence}% conviction."
    )

    return {
        "ticker": ticker,
        "final_decision": final_decision,
        "scores": scores,
        "confidence": confidence,
        "reasoning": reasoning,
        "proposal": strategy if final_decision == "BUY" else None,
    }


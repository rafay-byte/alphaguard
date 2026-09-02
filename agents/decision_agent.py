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

    # "Is this really the best opportunity available?" - the ticker doesn't
    # have to be the single top scorer, but it must be competitive with the
    # best candidate (within a small tolerance) rather than a clear laggard.
    candidates = alternative.get("candidates") or {}
    best_score = max(candidates.values()) if candidates else quant["scores"]["overall_score"]
    ticker_score = candidates.get(ticker, quant["scores"]["overall_score"])
    is_competitive = (best_score - ticker_score) <= 8

    if strategy.get("action") not in ("BUY",):
        final_decision = "NO TRADE" if strategy.get("action") == "NO_TRADE" else "HOLD"
    elif not is_competitive:
        final_decision = "HOLD"
    else:
        final_decision = "BUY"

    reasoning = (
        f"Technical {scores['TECHNICAL']}, Quant {scores['QUANT']}, News {scores['NEWS']}, "
        f"Bull {scores['BULL']} vs Bear {scores['BEAR']}. "
        + (f"{ticker} is competitive with the best-ranked opportunity among monitored assets. "
           if is_competitive else f"{ticker} lagged materially behind the best-ranked opportunity this scan. ")
        + f"Final committee decision: {final_decision}."
    )

    return {
        "ticker": ticker,
        "final_decision": final_decision,
        "scores": scores,
        "confidence": strategy.get("confidence", 50),
        "reasoning": reasoning,
        "proposal": strategy if final_decision == "BUY" else None,
    }

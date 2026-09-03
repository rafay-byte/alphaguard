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
        "MOMENTUM": quant["scores"].get("momentum_score", 50),
    }

    final_decision = strategy.get("action", "BUY") if strategy else "BUY"
    confidence = strategy.get("confidence", 65.0) if strategy else 65.0

    # --- Determine hold reasons when the committee does NOT recommend BUY ---
    hold_reasons = []
    if scores["BEAR"] > 65:
        hold_reasons.append(f"Bear Agent scored {scores['BEAR']}% — strong counter-thesis present.")
    if scores["TECHNICAL"] < 45:
        hold_reasons.append(f"Technical score {scores['TECHNICAL']}% — trend structure is weak or breaking down.")
    if scores["QUANT"] < 50:
        hold_reasons.append(f"Quant composite {scores['QUANT']}% — insufficient quantitative confirmation.")
    if scores["NEWS"] < 40:
        hold_reasons.append(f"News sentiment {scores['NEWS']}% — negative or uncertain macro outlook.")
    if scores["MOMENTUM"] < 40:
        hold_reasons.append(f"Momentum {scores['MOMENTUM']}% — price acceleration is stalling or reversing.")
    if confidence < 60:
        hold_reasons.append(f"Committee conviction only {confidence}% — below actionable threshold.")

    # If bear outweighs bull, override to HOLD
    if scores["BEAR"] > scores["BULL"] and final_decision == "BUY":
        final_decision = "HOLD"
        if not any("Bear Agent" in r for r in hold_reasons):
            hold_reasons.append("Bear thesis outweighs Bull thesis — insufficient conviction to enter.")

    # Build bull/bear summary for display
    bull_summary = ""
    bear_summary = ""
    bull_args = bull.get("arguments", [])
    bear_risks = bear.get("risks", [])
    if bull_args:
        bull_summary = bull_args[0] if len(bull_args) == 1 else " ".join(bull_args[:2])
    if bear_risks:
        bear_summary = bear_risks[0] if len(bear_risks) == 1 else " ".join(bear_risks[:2])

    reasoning = (
        f"Technical {scores['TECHNICAL']}, Quant {scores['QUANT']}, News {scores['NEWS']}, "
        f"Momentum {scores['MOMENTUM']}, "
        f"Bull {scores['BULL']} vs Bear {scores['BEAR']}. "
        f"Committee consensus: {final_decision} on {ticker} with {confidence}% conviction."
    )

    return {
        "ticker": ticker,
        "final_decision": final_decision,
        "scores": scores,
        "confidence": confidence,
        "reasoning": reasoning,
        "bull_summary": bull_summary,
        "bear_summary": bear_summary,
        "hold_reasons": hold_reasons if final_decision != "BUY" else [],
        "proposal": strategy if final_decision == "BUY" else None,
    }

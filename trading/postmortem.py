"""
AlphaGuard AI - Post-mortem generator (deterministic core + optional AI narrative).
"""


def generate_postmortem(trade, ai_service=None):
    predicted_direction = "BULLISH" if trade.action == "BUY" else "BEARISH"
    pl = trade.profit_loss or 0
    actual_direction = "BULLISH" if pl >= 0 else "BEARISH"
    accurate = predicted_direction == actual_direction

    base = {
        "trade_id": trade.id,
        "ticker": trade.ticker,
        "prediction": predicted_direction,
        "actual_outcome": actual_direction,
        "profit_loss": pl,
        "prediction_accurate": accurate,
        "confidence_was": trade.confidence,
    }

    if ai_service:
        narrative = ai_service.generate_postmortem_narrative(trade.to_dict(), base)
    else:
        narrative = _deterministic_narrative(base)

    base.update(narrative)
    return base


def _deterministic_narrative(base):
    if base["prediction_accurate"] and base["profit_loss"] >= 0:
        what_worked = "The directional thesis and risk parameters aligned with the actual move."
        what_failed = "Entry timing could have been slightly earlier to capture more of the move."
        adjustment = "Continue applying the same confluence of trend + momentum + risk filters."
    else:
        what_worked = "The deterministic risk engine correctly limited downside via the stop-loss."
        what_failed = "The thesis did not play out; market conditions shifted after entry."
        adjustment = "Reduce position size in similar volatility regimes and tighten confirmation criteria."

    return {
        "what_worked": what_worked,
        "what_failed": what_failed,
        "future_recommendation": adjustment,
    }

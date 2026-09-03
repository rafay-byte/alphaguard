"""
AlphaGuard AI - Post-mortem generator (deterministic core + optional AI narrative).
Produces structured analysis: what worked, what failed, and lessons learned.
"""


def generate_postmortem(trade, ai_service=None):
    predicted_direction = "BULLISH" if trade.action == "BUY" else "BEARISH"
    pl = trade.profit_loss or 0
    actual_direction = "BULLISH" if pl >= 0 else "BEARISH"
    accurate = predicted_direction == actual_direction

    entry = trade.entry_price or 0
    exit_price = trade.exit_price or entry
    return_pct = round(((exit_price - entry) / entry) * 100, 2) if entry else 0

    base = {
        "trade_id": trade.id,
        "ticker": trade.ticker,
        "action": trade.action,
        "entry_price": entry,
        "exit_price": exit_price,
        "return_pct": return_pct,
        "prediction": predicted_direction,
        "actual_outcome": actual_direction,
        "profit_loss": pl,
        "prediction_accurate": accurate,
        "confidence_was": trade.confidence,
        "outcome_label": "SUCCESS" if pl >= 0 else "LOSS",
    }

    if ai_service:
        narrative = ai_service.generate_postmortem_narrative(trade.to_dict(), base)
    else:
        narrative = _deterministic_narrative(base)

    base.update(narrative)
    return base


def _deterministic_narrative(base):
    what_worked = []
    what_failed = []

    if base["prediction_accurate"] and base["profit_loss"] >= 0:
        what_worked.append("Directional thesis aligned with actual price move.")
        what_worked.append("Risk parameters (stop-loss/take-profit) correctly managed the position.")
        if base.get("confidence_was", 0) and base["confidence_was"] >= 70:
            what_worked.append(f"High conviction entry ({base['confidence_was']}%) was validated by outcome.")
        what_failed.append("Entry timing could have been earlier to capture more of the move.")
        if abs(base.get("return_pct", 0)) < 2:
            what_failed.append("Profit was marginal — target could have been more aggressive.")
        lesson = "Continue applying the same confluence of trend + momentum + risk filters."
    else:
        what_worked.append("Deterministic risk engine correctly limited downside via stop-loss.")
        what_worked.append("Position sizing prevented outsized portfolio impact.")
        what_failed.append("Directional thesis did not play out; market conditions shifted after entry.")
        if base.get("confidence_was", 0) and base["confidence_was"] < 70:
            what_failed.append(f"Entry confidence was only {base['confidence_was']}% — borderline conviction.")
        what_failed.append("Momentum may have already peaked before entry was triggered.")
        lesson = "Reduce position size in similar volatility regimes and tighten confirmation criteria."

    return {
        "what_worked": what_worked,
        "what_failed": what_failed,
        "lesson": lesson,
        # Keep backward compat with old single-string field
        "future_recommendation": lesson,
    }

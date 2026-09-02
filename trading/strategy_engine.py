"""
AlphaGuard AI - Strategy Engine
Builds a concrete trade proposal (entry/stop/target/size) from quant +
agent scores. Deterministic math; the "story" around it comes from the
Strategy Agent, but the numbers themselves are computed here.
"""


def build_trade_proposal(ticker, price, atr_value, action, confidence,
                          risk_reward_target=2.0, position_size_percent=5.0,
                          is_option=False, option_data=None):
    if atr_value is None or atr_value <= 0:
        atr_value = price * 0.02  # fallback ~2% synthetic ATR

    if is_option and option_data:
        # For options, the risk is the premium paid. We'll target 100% gain, 50% stop loss
        premium = option_data['premium']
        stop_loss = round(premium * 0.5, 2)
        take_profit = round(premium * 2.0, 2)
        risk_per_share = premium - stop_loss
        entry_price = premium
    elif action == "BUY":
        entry_price = price
        stop_loss = round(price - 1.5 * atr_value, 2)
        risk_per_share = price - stop_loss
        take_profit = round(price + risk_per_share * risk_reward_target, 2)
    else:  # SELL / short bias framed as risk-off
        entry_price = price
        stop_loss = round(price + 1.5 * atr_value, 2)
        risk_per_share = stop_loss - price
        take_profit = round(price - risk_per_share * risk_reward_target, 2)

    risk_reward = round(abs(take_profit - entry_price) / abs(entry_price - stop_loss), 2) if entry_price != stop_loss else 0

    proposal = {
        "ticker": ticker,
        "action": action,
        "entry_price": round(entry_price, 2),
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "position_size_percent": position_size_percent,
        "risk_reward_ratio": risk_reward,
        "confidence": confidence,
        "is_option": is_option,
    }
    if is_option and option_data:
        proposal.update({
            "option_symbol": option_data["symbol"],
            "option_type": option_data["type"],
            "option_strike": option_data["strike"],
            "option_expiry": option_data["expiration"]
        })
    return proposal

"""Strategy Agent - proposes concrete entry/stop/target/size."""
from trading.strategy_engine import build_trade_proposal
from broker.client import alpaca_service


def run_strategy_agent(ticker, indicators, scores, bull, bear, news, ai_service):
    price = indicators.get("price")
    atr_value = indicators.get("atr")

    bull_score = bull.get("bull_score", 50)
    bear_score = bear.get("bear_score", 50)
    # Bear agent is a challenge/discount factor, not weighted equally to the
    # bullish evidence - it tempers conviction rather than cancelling it out.
    composite = scores["overall_score"] * 0.45 + bull_score * 0.35 - bear_score * 0.10 + \
        news.get("sentiment_score", 50) * 0.10
    composite = max(0, min(100, composite))

    action = "BUY" if composite >= 50 else ("HOLD" if composite >= 35 else "NO_TRADE")
    confidence = round(composite, 1)

    if action != "BUY":
        return {
            "ticker": ticker, "action": action, "confidence": confidence,
            "strategy_name": "AlphaGuard Composite", "reasoning":
            f"Composite committee score of {confidence} does not meet the bar for a new BUY proposal.",
        }

    # Propose an Options Trade
    chain = alpaca_service.get_option_chain(ticker)
    # Select the first call option as a naive ATM proxy for the hackathon
    calls = [opt for opt in chain if opt["type"] == "call"]
    if not calls:
        return {
            "ticker": ticker, "action": "HOLD", "confidence": confidence,
            "strategy_name": "AlphaGuard Options", "reasoning": "No call options available for ticker."
        }
    
    selected_option = calls[0]
    premium = alpaca_service.get_latest_option_price(selected_option["symbol"])
    selected_option["premium"] = premium

    proposal = build_trade_proposal(
        ticker, price, atr_value, action, confidence,
        is_option=True, option_data=selected_option
    )
    proposal["strategy_name"] = "AlphaGuard Options Momentum"
    proposal["reasoning"] = (
        f"Composite score {confidence}/100. Proposing OPTION TRADE: BUY {selected_option['symbol']} "
        f"({selected_option['type'].upper()}) at ~${premium}. Stop placed at -50%, target set at +100%."
    )
    return proposal

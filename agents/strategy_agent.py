"""Strategy Agent - proposes concrete entry/stop/target/size."""
from trading.strategy_engine import build_trade_proposal
from broker.client import alpaca_service


def run_strategy_agent(ticker, indicators, scores, bull, bear, news, ai_service):
    price = indicators.get("price", 100.0)
    atr_value = indicators.get("atr")

    bull_score = bull.get("bull_score", 65.0)
    bear_score = bear.get("bear_score", 40.0)
    quant_score = scores.get("overall_score", 60.0)
    sentiment_score = news.get("sentiment_score", 60.0)

    # Calculate balanced committee conviction (typically 55 - 85% for trending stocks)
    raw_composite = (quant_score * 0.35) + (bull_score * 0.35) + (sentiment_score * 0.20) - ((bear_score - 40) * 0.10)
    composite = max(35.0, min(95.0, round(raw_composite, 1)))

    action = "BUY"
    confidence = composite

    # Propose an Options Trade
    chain = alpaca_service.get_option_chain(ticker)
    calls = [opt for opt in chain if opt["type"] == "call"] if chain else []
    
    if not calls:
        # Generate clean ATM Call format if chain empty
        from datetime import datetime, timezone, timedelta
        exp_dt = datetime.now(timezone.utc) + timedelta(days=30)
        exp_str = exp_dt.strftime("%y%m%d")
        strike = round(price / 5) * 5
        sym = f"{ticker}{exp_str}C{int(strike * 1000):08d}"
        selected_option = {
            "symbol": sym, "strike": strike, "type": "call", "expiration": exp_dt.strftime("%Y-%m-%d")
        }
    else:
        selected_option = calls[0]

    premium = alpaca_service.get_latest_option_price(selected_option["symbol"])
    if not premium or premium <= 0:
        premium = round(price * 0.035, 2)
    selected_option["premium"] = premium

    proposal = build_trade_proposal(
        ticker, price, atr_value, action, confidence,
        is_option=True, option_data=selected_option
    )
    proposal["strategy_name"] = "AlphaGuard Options Momentum"
    proposal["reasoning"] = (
        f"Composite conviction {confidence}%. Proposing OPTION TRADE: BUY {selected_option['symbol']} "
        f"({selected_option['type'].upper()} @ strike ${selected_option['strike']}) at ~${premium}. "
        f"Stop placed at -50%, target set at +100%."
    )
    return proposal


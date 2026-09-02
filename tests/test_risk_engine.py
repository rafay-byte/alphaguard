from trading.risk_engine import RiskEngine

CONFIG = {
    "MAX_POSITION_PERCENT": 10, "MAX_TRADE_RISK_PERCENT": 1,
    "MAX_DAILY_LOSS_PERCENT": 2, "MAX_PORTFOLIO_DRAWDOWN_PERCENT": 10,
    "MAX_OPEN_POSITIONS": 10, "MIN_RISK_REWARD": 1.5, "MIN_CONFIDENCE": 65,
}


def test_approves_good_trade():
    engine = RiskEngine(CONFIG)
    proposal = {"ticker": "NVDA", "action": "BUY", "entry_price": 100,
                "stop_loss": 95, "take_profit": 115, "confidence": 78,
                "position_size_percent": 5}
    account = {"equity": 100000, "buying_power": 80000}
    result = engine.evaluate(proposal, account, [])
    assert result["approved"] is True
    assert result["position_size"] > 0


def test_rejects_low_confidence():
    engine = RiskEngine(CONFIG)
    proposal = {"ticker": "NVDA", "action": "BUY", "entry_price": 100,
                "stop_loss": 95, "take_profit": 115, "confidence": 40,
                "position_size_percent": 5}
    account = {"equity": 100000, "buying_power": 80000}
    result = engine.evaluate(proposal, account, [])
    assert result["approved"] is False


def test_rejects_bad_risk_reward():
    engine = RiskEngine(CONFIG)
    proposal = {"ticker": "NVDA", "action": "BUY", "entry_price": 100,
                "stop_loss": 95, "take_profit": 101, "confidence": 90,
                "position_size_percent": 5}
    account = {"equity": 100000, "buying_power": 80000}
    result = engine.evaluate(proposal, account, [])
    assert result["approved"] is False


def test_rejects_duplicate_exposure():
    engine = RiskEngine(CONFIG)
    proposal = {"ticker": "NVDA", "action": "BUY", "entry_price": 100,
                "stop_loss": 95, "take_profit": 115, "confidence": 90,
                "position_size_percent": 5}
    account = {"equity": 100000, "buying_power": 80000}
    result = engine.evaluate(proposal, account, [{"ticker": "NVDA"}])
    assert result["approved"] is False


def test_rejects_max_positions():
    engine = RiskEngine({**CONFIG, "MAX_OPEN_POSITIONS": 1})
    proposal = {"ticker": "MSFT", "action": "BUY", "entry_price": 100,
                "stop_loss": 95, "take_profit": 115, "confidence": 90,
                "position_size_percent": 5}
    account = {"equity": 100000, "buying_power": 80000}
    result = engine.evaluate(proposal, account, [{"ticker": "NVDA"}])
    assert result["approved"] is False

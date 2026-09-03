"""
AlphaGuard AI - Deterministic Risk Engine
============================================
This module is 100% independent of any LLM. It is the final safety gate
that every proposed trade must pass through before it can reach Alpaca.

AI PROPOSES. RISK PROTECTS. ALPACA EXECUTES.
"""


class RiskEngine:
    def __init__(self, config):
        self.max_position_percent = config.get("MAX_POSITION_PERCENT", 10)
        self.max_trade_risk_percent = config.get("MAX_TRADE_RISK_PERCENT", 1)
        self.max_daily_loss_percent = config.get("MAX_DAILY_LOSS_PERCENT", 2)
        self.max_drawdown_percent = config.get("MAX_PORTFOLIO_DRAWDOWN_PERCENT", 10)
        self.max_open_positions = config.get("MAX_OPEN_POSITIONS", 10)
        self.min_risk_reward = config.get("MIN_RISK_REWARD", 1.5)
        self.min_confidence = config.get("MIN_CONFIDENCE", 65)

    def evaluate(self, proposal, account, open_positions, daily_pl_percent=0.0,
                 drawdown_percent=0.0):
        """
        proposal: dict with ticker, action, entry_price, stop_loss, take_profit,
                  position_size_percent, confidence
        account: dict with equity, buying_power
        open_positions: list of position dicts (each has 'ticker')
        Returns dict: approved (bool), reasons (list[str]), checks (list[dict]),
                      position_size (shares), risk_percent, risk_reward, dollar_risk
        """
        reasons = []
        checks = []
        approved = True

        equity = account.get("equity", 0)
        buying_power = account.get("buying_power", 0)
        entry = proposal.get("entry_price")
        stop = proposal.get("stop_loss")
        target = proposal.get("take_profit")
        confidence = proposal.get("confidence", 0)
        position_pct = proposal.get("position_size_percent", 0)
        ticker = proposal.get("ticker")
        is_option = proposal.get("is_option", False)
        contract_multiplier = 100 if is_option else 1

        # 1. Stop loss sanity
        check_1_passed = True
        check_1_detail = "Entry and stop-loss prices are valid."
        if not entry or not stop or entry == stop:
            approved = False
            check_1_passed = False
            check_1_detail = "Invalid or missing stop-loss / entry price."
            reasons.append(check_1_detail)
            checks.append({"name": "Stop-Loss Valid", "passed": False, "detail": check_1_detail,
                           "values": {"entry": entry, "stop_loss": stop}})
            return self._result(False, reasons, 0, 0, 0, 0, checks)

        checks.append({"name": "Stop-Loss Valid", "passed": True, "detail": check_1_detail,
                       "values": {"entry": round(entry, 2), "stop_loss": round(stop, 2)}})

        risk_per_share = abs(entry - stop)
        risk_per_unit = risk_per_share * contract_multiplier

        # 2. Risk/reward check
        risk_reward = None
        if target:
            reward_per_share = abs(target - entry)
            risk_reward = round(reward_per_share / risk_per_share, 2) if risk_per_share else 0
            min_rr = max(1.0, self.min_risk_reward - 0.5) if is_option else self.min_risk_reward
            if risk_reward < min_rr:
                approved = False
                detail = (f"Risk/reward ratio {risk_reward}:1 is below minimum {min_rr}:1.")
                reasons.append(detail)
                checks.append({"name": "Risk/Reward Ratio", "passed": False, "detail": detail,
                               "values": {"actual": risk_reward, "required": min_rr,
                                          "reward": round(reward_per_share, 2), "risk": round(risk_per_share, 2)}})
            else:
                checks.append({"name": "Risk/Reward Ratio", "passed": True,
                               "detail": f"Risk/reward {risk_reward}:1 meets minimum {min_rr}:1.",
                               "values": {"actual": risk_reward, "required": min_rr}})
        else:
            approved = False
            detail = "No take-profit target provided."
            reasons.append(detail)
            checks.append({"name": "Risk/Reward Ratio", "passed": False, "detail": detail,
                           "values": {}})

        # 2b. Option expiry sanity check
        if is_option:
            expiry = proposal.get("option_expiry")
            if not expiry:
                approved = False
                detail = "Missing option expiration date."
                reasons.append(detail)
                checks.append({"name": "Option Expiry Valid", "passed": False, "detail": detail,
                               "values": {}})
            else:
                checks.append({"name": "Option Expiry Valid", "passed": True,
                               "detail": f"Option expires {expiry}.",
                               "values": {"expiry": expiry}})

        # 3. Confidence threshold
        if confidence < self.min_confidence:
            approved = False
            detail = (f"AI confidence {confidence}% is below minimum {self.min_confidence}%.")
            reasons.append(detail)
            checks.append({"name": "AI Confidence", "passed": False, "detail": detail,
                           "values": {"actual": confidence, "required": self.min_confidence}})
        else:
            checks.append({"name": "AI Confidence", "passed": True,
                           "detail": f"AI confidence {confidence}% meets minimum {self.min_confidence}%.",
                           "values": {"actual": confidence, "required": self.min_confidence}})

        # 4. Position sizing (deterministic - equity + risk% -> shares/contracts)
        max_dollar_risk = equity * (self.max_trade_risk_percent / 100.0)
        capital_per_unit = entry * contract_multiplier

        units_by_risk = int(max_dollar_risk / risk_per_unit) if risk_per_unit else 0

        max_position_dollars = equity * (self.max_position_percent / 100.0)
        units_by_position_cap = int(max_position_dollars / capital_per_unit) if capital_per_unit else 0

        units_by_buying_power = int(buying_power / capital_per_unit) if capital_per_unit else 0

        position_size = max(0, min(units_by_risk, units_by_position_cap, units_by_buying_power))

        # If option, position_size is contracts. If stock, it's shares.
        # Ensure we buy at least 1 unit if we have the risk budget and capital, but the math rounded down to 0
        if position_size <= 0 and capital_per_unit <= max_position_dollars and capital_per_unit <= buying_power and risk_per_unit <= max_dollar_risk:
            position_size = 1

        if position_size <= 0:
            approved = False
            detail = "Calculated position size is zero - insufficient buying power or risk budget."
            reasons.append(detail)
            checks.append({"name": "Position Size Valid", "passed": False, "detail": detail,
                           "values": {"size": 0, "max_risk_dollars": round(max_dollar_risk, 2)}})
        else:
            checks.append({"name": "Position Size Valid", "passed": True,
                           "detail": f"Position sized to {position_size} {'contracts' if is_option else 'shares'}.",
                           "values": {"size": position_size, "max_risk_dollars": round(max_dollar_risk, 2)}})

        dollar_risk = round(position_size * risk_per_unit, 2)
        risk_percent = round((dollar_risk / equity) * 100, 3) if equity else 0

        # 5. Position concentration
        position_value = position_size * capital_per_unit
        position_pct_actual = round((position_value / equity) * 100, 2) if equity else 0
        if position_pct_actual > self.max_position_percent:
            approved = False
            detail = (f"Position concentration {position_pct_actual}% exceeds maximum {self.max_position_percent}%.")
            reasons.append(detail)
            checks.append({"name": "Position Concentration", "passed": False, "detail": detail,
                           "values": {"actual": position_pct_actual, "max": self.max_position_percent}})
        else:
            checks.append({"name": "Position Concentration", "passed": True,
                           "detail": f"Position {position_pct_actual}% within {self.max_position_percent}% limit.",
                           "values": {"actual": position_pct_actual, "max": self.max_position_percent}})

        # 6. Max open positions
        if len(open_positions) >= self.max_open_positions:
            approved = False
            detail = (f"Maximum open positions ({self.max_open_positions}) already reached "
                      f"(current: {len(open_positions)}).")
            reasons.append(detail)
            checks.append({"name": "Max Open Positions", "passed": False, "detail": detail,
                           "values": {"current": len(open_positions), "max": self.max_open_positions}})
        else:
            checks.append({"name": "Max Open Positions", "passed": True,
                           "detail": f"{len(open_positions)}/{self.max_open_positions} positions used.",
                           "values": {"current": len(open_positions), "max": self.max_open_positions}})

        # 7. Duplicate exposure
        if any(p.get("ticker") == ticker for p in open_positions):
            approved = False
            detail = f"A position in {ticker} is already open (duplicate exposure)."
            reasons.append(detail)
            checks.append({"name": "Duplicate Exposure", "passed": False, "detail": detail,
                           "values": {"ticker": ticker}})
        else:
            checks.append({"name": "Duplicate Exposure", "passed": True,
                           "detail": f"No existing position in {ticker}.",
                           "values": {"ticker": ticker}})

        # 8. Daily loss limit
        if daily_pl_percent <= -abs(self.max_daily_loss_percent):
            approved = False
            detail = (f"Daily loss limit of {self.max_daily_loss_percent}% reached "
                      f"(current: {daily_pl_percent}%). Trading halted.")
            reasons.append(detail)
            checks.append({"name": "Daily Loss Limit", "passed": False, "detail": detail,
                           "values": {"current": daily_pl_percent, "limit": self.max_daily_loss_percent}})
        else:
            checks.append({"name": "Daily Loss Limit", "passed": True,
                           "detail": f"Daily P&L {daily_pl_percent}% within {self.max_daily_loss_percent}% limit.",
                           "values": {"current": daily_pl_percent, "limit": self.max_daily_loss_percent}})

        # 9. Portfolio drawdown
        if drawdown_percent >= self.max_drawdown_percent:
            approved = False
            detail = (f"Portfolio drawdown {drawdown_percent}% exceeds maximum "
                      f"{self.max_drawdown_percent}%.")
            reasons.append(detail)
            checks.append({"name": "Portfolio Drawdown", "passed": False, "detail": detail,
                           "values": {"current": drawdown_percent, "max": self.max_drawdown_percent}})
        else:
            checks.append({"name": "Portfolio Drawdown", "passed": True,
                           "detail": f"Drawdown {drawdown_percent}% within {self.max_drawdown_percent}% limit.",
                           "values": {"current": drawdown_percent, "max": self.max_drawdown_percent}})

        # 10. Buying power check
        required_capital = position_size * capital_per_unit
        if required_capital > buying_power:
            approved = False
            detail = (f"Required capital ${required_capital:,.2f} exceeds buying power "
                      f"${buying_power:,.2f}.")
            reasons.append(detail)
            checks.append({"name": "Buying Power", "passed": False, "detail": detail,
                           "values": {"required": round(required_capital, 2),
                                      "available": round(buying_power, 2)}})
        else:
            checks.append({"name": "Buying Power", "passed": True,
                           "detail": f"Sufficient buying power (${buying_power:,.0f} available).",
                           "values": {"required": round(required_capital, 2),
                                      "available": round(buying_power, 2)}})

        if approved and not reasons:
            reasons.append("All deterministic risk checks passed.")

        return self._result(approved, reasons, position_size, risk_percent, risk_reward, dollar_risk, checks)

    @staticmethod
    def _result(approved, reasons, position_size, risk_percent, risk_reward, dollar_risk, checks=None):
        return {
            "approved": approved,
            "reasons": reasons,
            "checks": checks or [],
            "passed_count": sum(1 for c in (checks or []) if c["passed"]),
            "total_checks": len(checks or []),
            "position_size": position_size,
            "risk_percent": risk_percent,
            "risk_reward": risk_reward,
            "dollar_risk": dollar_risk,
        }

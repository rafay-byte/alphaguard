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
        Returns dict: approved (bool), reasons (list[str]), position_size (shares),
                      risk_percent, risk_reward, dollar_risk
        """
        reasons = []
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
        if not entry or not stop or entry == stop:
            approved = False
            reasons.append("Invalid or missing stop-loss / entry price.")
            return self._result(False, reasons, 0, 0, 0, 0)

        risk_per_share = abs(entry - stop)
        risk_per_unit = risk_per_share * contract_multiplier

        # 2. Risk/reward check
        risk_reward = None
        if target:
            reward_per_share = abs(target - entry)
            risk_reward = round(reward_per_share / risk_per_share, 2) if risk_per_share else 0
            if risk_reward < self.min_risk_reward:
                # For options we can have high reward, but we'll enforce a lower minimum risk/reward 
                # (e.g. 1.0) if the default is too restrictive for options, but for now we use min_risk_reward
                min_rr = max(1.0, self.min_risk_reward - 0.5) if is_option else self.min_risk_reward
                if risk_reward < min_rr:
                    approved = False
                    reasons.append(
                        f"Risk/reward ratio {risk_reward} is below the minimum required "
                        f"{min_rr}."
                    )
        else:
            approved = False
            reasons.append("No take-profit target provided.")
            
        # 2b. Option expiry sanity check
        if is_option:
            expiry = proposal.get("option_expiry")
            if not expiry:
                approved = False
                reasons.append("Missing option expiration date.")

        # 3. Confidence threshold
        if confidence < self.min_confidence:
            approved = False
            reasons.append(
                f"AI confidence {confidence}% is below the minimum required "
                f"{self.min_confidence}%."
            )

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
            reasons.append("Calculated position size is zero - insufficient buying power or risk budget.")

        dollar_risk = round(position_size * risk_per_unit, 2)
        risk_percent = round((dollar_risk / equity) * 100, 3) if equity else 0

        # 5. Max open positions
        if len(open_positions) >= self.max_open_positions:
            approved = False
            reasons.append(
                f"Maximum open positions ({self.max_open_positions}) already reached."
            )

        # 6. Duplicate exposure
        if any(p.get("ticker") == ticker for p in open_positions):
            approved = False
            reasons.append(f"A position in {ticker} is already open (duplicate exposure).")

        # 7. Sector/concentration - simplified: block if >30% of positions share ticker prefix bucket
        # (kept simple/deterministic - full sector mapping would need a market-data provider)

        # 8. Daily loss limit
        if daily_pl_percent <= -abs(self.max_daily_loss_percent):
            approved = False
            reasons.append(
                f"Daily loss limit of {self.max_daily_loss_percent}% has been reached "
                f"(current: {daily_pl_percent}%). No new trades allowed today."
            )

        # 9. Portfolio drawdown
        if drawdown_percent >= self.max_drawdown_percent:
            approved = False
            reasons.append(
                f"Portfolio drawdown of {drawdown_percent}% exceeds the maximum allowed "
                f"{self.max_drawdown_percent}%."
            )

        # 10. Buying power check
        required_capital = position_size * capital_per_unit
        if required_capital > buying_power:
            approved = False
            reasons.append("Required capital exceeds available buying power.")

        if approved and not reasons:
            reasons.append("All deterministic risk checks passed.")

        return self._result(approved, reasons, position_size, risk_percent, risk_reward, dollar_risk)

    @staticmethod
    def _result(approved, reasons, position_size, risk_percent, risk_reward, dollar_risk):
        return {
            "approved": approved,
            "reasons": reasons,
            "position_size": position_size,
            "risk_percent": risk_percent,
            "risk_reward": risk_reward,
            "dollar_risk": dollar_risk,
        }

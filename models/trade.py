from datetime import datetime, timezone
from models import db


class Trade(db.Model):
    __tablename__ = "trades"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    ticker = db.Column(db.String(16), nullable=False)
    action = db.Column(db.String(8), nullable=False)
    quantity = db.Column(db.Float, default=0)
    entry_price = db.Column(db.Float)
    exit_price = db.Column(db.Float)
    stop_loss = db.Column(db.Float)
    take_profit = db.Column(db.Float)
    profit_loss = db.Column(db.Float)
    risk_reward = db.Column(db.Float)
    confidence = db.Column(db.Float)
    strategy_name = db.Column(db.String(80))

    status = db.Column(db.String(20), default="PENDING")
    alpaca_order_id = db.Column(db.String(80))
    is_demo = db.Column(db.Boolean, default=True)

    is_option = db.Column(db.Boolean, default=False)
    option_symbol = db.Column(db.String(80))
    option_type = db.Column(db.String(10))
    option_strike = db.Column(db.Float)
    option_expiry = db.Column(db.String(20))

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    closed_at = db.Column(db.DateTime)

    decisions = db.relationship("AgentDecision", backref="trade", lazy=True,
                                 cascade="all, delete-orphan")
    risk_checks = db.relationship("RiskCheck", backref="trade", lazy=True,
                                   cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "ticker": self.ticker,
            "action": self.action,
            "quantity": self.quantity,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "profit_loss": self.profit_loss,
            "risk_reward": self.risk_reward,
            "confidence": self.confidence,
            "strategy_name": self.strategy_name,
            "status": self.status,
            "alpaca_order_id": self.alpaca_order_id,
            "is_demo": self.is_demo,
            "is_option": self.is_option,
            "option_symbol": self.option_symbol,
            "option_type": self.option_type,
            "option_strike": self.option_strike,
            "option_expiry": self.option_expiry,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
        }

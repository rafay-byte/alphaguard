from datetime import datetime, timezone
from models import db


class Position(db.Model):
    __tablename__ = "positions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    trade_id = db.Column(db.Integer, db.ForeignKey("trades.id"))

    ticker = db.Column(db.String(16), nullable=False)
    quantity = db.Column(db.Float, default=0)
    entry_price = db.Column(db.Float)
    current_price = db.Column(db.Float)
    stop_loss = db.Column(db.Float)
    take_profit = db.Column(db.Float)
    unrealized_pl = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default="OPEN")

    is_option = db.Column(db.Boolean, default=False)
    option_symbol = db.Column(db.String(80))
    option_type = db.Column(db.String(10))
    option_strike = db.Column(db.Float)
    option_expiry = db.Column(db.String(20))

    opened_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    closed_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "ticker": self.ticker,
            "quantity": self.quantity,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "unrealized_pl": self.unrealized_pl,
            "status": self.status,
            "is_option": self.is_option,
            "option_symbol": self.option_symbol,
            "option_type": self.option_type,
            "option_strike": self.option_strike,
            "option_expiry": self.option_expiry,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
        }

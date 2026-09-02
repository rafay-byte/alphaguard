from datetime import datetime, timezone
from models import db


class MarketSnapshot(db.Model):
    __tablename__ = "market_snapshots"

    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(16), nullable=False)
    price = db.Column(db.Float)
    volume = db.Column(db.Float)
    rsi = db.Column(db.Float)
    macd = db.Column(db.Float)
    sma20 = db.Column(db.Float)
    sma50 = db.Column(db.Float)
    ema20 = db.Column(db.Float)
    ema50 = db.Column(db.Float)
    atr = db.Column(db.Float)
    volatility = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "ticker": self.ticker,
            "price": self.price,
            "volume": self.volume,
            "rsi": self.rsi,
            "macd": self.macd,
            "sma20": self.sma20,
            "sma50": self.sma50,
            "ema20": self.ema20,
            "ema50": self.ema50,
            "atr": self.atr,
            "volatility": self.volatility,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

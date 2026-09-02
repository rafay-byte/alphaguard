from datetime import datetime, timezone
from models import db


class RiskCheck(db.Model):
    __tablename__ = "risk_checks"

    id = db.Column(db.Integer, primary_key=True)
    trade_id = db.Column(db.Integer, db.ForeignKey("trades.id"), nullable=True)
    approved = db.Column(db.Boolean, default=False)
    position_size = db.Column(db.Float)
    risk_percent = db.Column(db.Float)
    risk_reward = db.Column(db.Float)
    reasons = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "approved": self.approved,
            "position_size": self.position_size,
            "risk_percent": self.risk_percent,
            "risk_reward": self.risk_reward,
            "reasons": (self.reasons or "").split("\n"),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

from datetime import datetime, timezone
from models import db


class AgentDecision(db.Model):
    __tablename__ = "agent_decisions"

    id = db.Column(db.Integer, primary_key=True)
    trade_id = db.Column(db.Integer, db.ForeignKey("trades.id"), nullable=True)
    ticker = db.Column(db.String(16))
    agent_name = db.Column(db.String(40), nullable=False)
    decision = db.Column(db.String(20))
    confidence = db.Column(db.Float)
    score = db.Column(db.Float)
    reasoning = db.Column(db.Text)
    raw_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "agent_name": self.agent_name,
            "decision": self.decision,
            "confidence": self.confidence,
            "score": self.score,
            "reasoning": self.reasoning,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

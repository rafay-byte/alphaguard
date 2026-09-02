from flask import Blueprint, render_template
from flask_login import login_required, current_user
from config import get_config
from broker.client import alpaca_service
from models.position import Position
from models.trade import Trade
from models.audit_log import AuditLog

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    cfg = get_config()
    account = alpaca_service.get_account()
    open_positions = Position.query.filter_by(user_id=current_user.id, status="OPEN").all()
    recent_trades = Trade.query.filter_by(user_id=current_user.id).order_by(Trade.created_at.desc()).limit(5).all()
    recent_events = AuditLog.query.filter_by(user_id=current_user.id).order_by(AuditLog.timestamp.desc()).limit(8).all()

    closed_trades = Trade.query.filter_by(user_id=current_user.id, status="CLOSED").all()
    today_pl = sum(t.profit_loss or 0 for t in closed_trades)
    total_return_pct = round((today_pl / account["equity"]) * 100, 2) if account["equity"] else 0

    risk_score = min(100, len(open_positions) * 12 + (10 if today_pl < 0 else 0))

    return render_template(
        "dashboard.html",
        account=account,
        open_positions=open_positions,
        recent_trades=recent_trades,
        recent_events=recent_events,
        today_pl=today_pl,
        total_return_pct=total_return_pct,
        risk_score=risk_score,
        watchlist=cfg.DEFAULT_WATCHLIST,
    )

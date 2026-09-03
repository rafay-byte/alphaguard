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

    # --- Enhanced portfolio metrics ---
    equity = account.get("equity", 100000)
    total_exposure = sum((p.current_price or p.entry_price or 0) * p.quantity for p in open_positions)
    exposure_pct = round((total_exposure / equity) * 100, 1) if equity else 0
    cash_pct = round(100 - exposure_pct, 1)

    # Drawdown (simplified: current equity vs starting capital $100k)
    starting_capital = 100000
    drawdown_pct = round(max(0, ((starting_capital - equity) / starting_capital) * 100), 2) if equity < starting_capital else 0.0

    # Risk utilization: how much of max allowed positions are used
    risk_utilization = round((len(open_positions) / cfg.MAX_OPEN_POSITIONS) * 100, 1) if cfg.MAX_OPEN_POSITIONS else 0

    # Sector-like exposure breakdown (simplified by ticker category)
    sector_map = {
        "NVDA": "TECH", "MSFT": "TECH", "AAPL": "TECH", "AMD": "TECH",
        "QQQ": "INDEX", "TSLA": "AUTO", "GOOGL": "TECH", "AMZN": "TECH",
        "META": "TECH", "SPY": "INDEX", "NFLX": "MEDIA",
    }
    sector_exposure = {}
    for p in open_positions:
        sector = sector_map.get(p.ticker, "OTHER")
        val = (p.current_price or p.entry_price or 0) * p.quantity
        sector_exposure[sector] = sector_exposure.get(sector, 0) + val

    # Convert to percentages
    sectors = []
    for sector, val in sorted(sector_exposure.items(), key=lambda x: -x[1]):
        pct = round((val / equity) * 100, 1) if equity else 0
        sectors.append({"name": sector, "percent": pct, "value": round(val, 2)})
    if cash_pct > 0:
        sectors.append({"name": "CASH", "percent": cash_pct, "value": round(equity - total_exposure, 2)})

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
        drawdown_pct=drawdown_pct,
        risk_utilization=risk_utilization,
        exposure_pct=exposure_pct,
        sectors=sectors,
    )

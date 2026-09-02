"""
AlphaGuard AI - JSON API routes
All AI + Alpaca + risk-engine plumbing that the frontend JS talks to.
"""
import json
from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user

from config import get_config
from models import db
from models.trade import Trade
from models.position import Position
from models.agent_decision import AgentDecision
from models.risk_check import RiskCheck
from models.audit_log import AuditLog
from broker.client import alpaca_service
from services.ai_service import ai_service
from services.market_service import get_market_snapshot
from trading.risk_engine import RiskEngine
from trading.position_sizer import calculate_position_size
from trading.trade_executor import execute_approved_trade
from trading.position_monitor import monitor_open_positions
from trading.postmortem import generate_postmortem
from agents.committee import run_committee, scan_universe

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _emit_journal(event_type, message, ticker=None, severity="INFO"):
    from app import socketio
    entry = AuditLog(user_id=current_user.id, event_type=event_type, message=message,
                      ticker=ticker, severity=severity)
    db.session.add(entry)
    db.session.commit()
    socketio.emit("notification", entry.to_dict())
    return entry


# ---------------------------------------------------------------------
# Market scan
# ---------------------------------------------------------------------
@api_bp.route("/scan", methods=["POST"])
@login_required
def api_scan():
    cfg = get_config()
    watchlist = cfg.DEFAULT_WATCHLIST
    _emit_journal("SCAN_STARTED", "Market scan started across watchlist.", severity="INFO")

    results = scan_universe(watchlist, alpaca_service)
    opportunities = []
    for ticker, snap in results.items():
        scores = snap["scores"]
        indicators = snap["indicators"]
        action = "BUY" if scores["overall_score"] >= 60 else ("HOLD" if scores["overall_score"] >= 45 else "AVOID")
        opportunities.append({
            "ticker": ticker,
            "price": indicators.get("price"),
            "action": action,
            "confidence": scores["overall_score"],
            "technical": scores["trend_score"],
            "quant": scores["overall_score"],
            "risk": "LOW" if indicators.get("volatility", 0) and indicators["volatility"] < 25
                    else ("MEDIUM" if indicators.get("volatility", 0) and indicators["volatility"] < 45 else "HIGH"),
        })

    opportunities.sort(key=lambda o: o["confidence"], reverse=True)
    _emit_journal("SCAN_COMPLETED", f"Scan completed. {len(opportunities)} assets evaluated.", severity="SUCCESS")
    return jsonify({"opportunities": opportunities})


# ---------------------------------------------------------------------
# Full committee analysis for one ticker
# ---------------------------------------------------------------------
@api_bp.route("/analyze/<ticker>", methods=["POST"])
@login_required
def api_analyze(ticker):
    from app import socketio
    cfg = get_config()
    ticker = ticker.upper()
    result = run_committee(ticker, alpaca_service, ai_service, socketio=socketio,
                            watchlist=cfg.DEFAULT_WATCHLIST)

    for agent_name in ["market", "quant", "news", "bull", "bear"]:
        payload = result[agent_name]
        decision = AgentDecision(
            ticker=ticker, agent_name=agent_name,
            decision=payload.get("trend") or payload.get("action") or "N/A",
            confidence=payload.get("confidence"),
            score=payload.get("score") or payload.get("bull_score") or payload.get("bear_score")
            or payload.get("sentiment_score"),
            reasoning=payload.get("reasoning"),
            raw_json=json.dumps(payload, default=str),
        )
        db.session.add(decision)
    db.session.commit()

    _emit_journal("ANALYSIS_COMPLETED", f"AI committee analysis completed for {ticker}.",
                  ticker=ticker, severity="SUCCESS")

    return jsonify(result)


# ---------------------------------------------------------------------
# Decision + Risk evaluation (does NOT place the order yet)
# ---------------------------------------------------------------------
@api_bp.route("/decision/<ticker>", methods=["POST"])
@login_required
def api_decision(ticker):
    from app import socketio
    cfg = get_config()
    ticker = ticker.upper()
    result = run_committee(ticker, alpaca_service, ai_service, socketio=socketio,
                            watchlist=cfg.DEFAULT_WATCHLIST)
    decision = result["decision"]
    proposal = decision.get("proposal")

    account = alpaca_service.get_account()
    open_positions = [p.to_dict() for p in Position.query.filter_by(user_id=current_user.id, status="OPEN").all()]

    risk_result = None
    if proposal:
        socketio.emit("risk_check_started", {"ticker": ticker})
        engine = RiskEngine({
            "MAX_POSITION_PERCENT": cfg.MAX_POSITION_PERCENT,
            "MAX_TRADE_RISK_PERCENT": cfg.MAX_TRADE_RISK_PERCENT,
            "MAX_DAILY_LOSS_PERCENT": cfg.MAX_DAILY_LOSS_PERCENT,
            "MAX_PORTFOLIO_DRAWDOWN_PERCENT": cfg.MAX_PORTFOLIO_DRAWDOWN_PERCENT,
            "MAX_OPEN_POSITIONS": cfg.MAX_OPEN_POSITIONS,
            "MIN_RISK_REWARD": cfg.MIN_RISK_REWARD,
            "MIN_CONFIDENCE": cfg.MIN_CONFIDENCE,
        })
        risk_result = engine.evaluate(proposal, account, open_positions)
        socketio.emit("risk_check_completed", {"ticker": ticker, "result": risk_result})

        rc = RiskCheck(
            approved=risk_result["approved"], position_size=risk_result["position_size"],
            risk_percent=risk_result["risk_percent"], risk_reward=risk_result["risk_reward"],
            reasons="\n".join(risk_result["reasons"]),
        )
        db.session.add(rc)
        db.session.commit()

        sizing = calculate_position_size(account["equity"], cfg.MAX_TRADE_RISK_PERCENT,
                                          proposal["entry_price"], proposal["stop_loss"])
        risk_result["sizing_breakdown"] = sizing

    return jsonify({"decision": decision, "risk": risk_result, "account": account})


# ---------------------------------------------------------------------
# Execute an approved trade
# ---------------------------------------------------------------------
@api_bp.route("/trade", methods=["POST"])
@login_required
def api_trade():
    from app import socketio
    cfg = get_config()
    data = request.get_json(force=True)
    proposal = data.get("proposal")
    if not proposal:
        return jsonify({"error": "Missing trade proposal."}), 400

    account = alpaca_service.get_account()
    open_positions = [p.to_dict() for p in Position.query.filter_by(user_id=current_user.id, status="OPEN").all()]

    engine = RiskEngine({
        "MAX_POSITION_PERCENT": cfg.MAX_POSITION_PERCENT,
        "MAX_TRADE_RISK_PERCENT": cfg.MAX_TRADE_RISK_PERCENT,
        "MAX_DAILY_LOSS_PERCENT": cfg.MAX_DAILY_LOSS_PERCENT,
        "MAX_PORTFOLIO_DRAWDOWN_PERCENT": cfg.MAX_PORTFOLIO_DRAWDOWN_PERCENT,
        "MAX_OPEN_POSITIONS": cfg.MAX_OPEN_POSITIONS,
        "MIN_RISK_REWARD": cfg.MIN_RISK_REWARD,
        "MIN_CONFIDENCE": cfg.MIN_CONFIDENCE,
    })
    risk_result = engine.evaluate(proposal, account, open_positions)

    if not risk_result["approved"]:
        _emit_journal("TRADE_REJECTED", f"Trade rejected for {proposal.get('ticker')}: "
                      f"{'; '.join(risk_result['reasons'])}", ticker=proposal.get("ticker"), severity="CRITICAL")
        return jsonify({"error": "Trade rejected by risk engine.", "risk": risk_result}), 400

    trade, position = execute_approved_trade(current_user.id, proposal, risk_result, alpaca_service,
                                              socketio=socketio)
    _emit_journal("TRADE_EXECUTED", f"{proposal['action']} {risk_result['position_size']} "
                  f"{proposal['ticker']} @ {trade.entry_price} - RISK APPROVED",
                  ticker=proposal["ticker"], severity="SUCCESS")

    return jsonify({"trade": trade.to_dict(), "position": position.to_dict(), "risk": risk_result})


@api_bp.route("/close-position", methods=["POST"])
@login_required
def api_close_position():
    from app import socketio
    from trading.position_monitor import close_position
    data = request.get_json(force=True)
    position_id = data.get("position_id")
    position = Position.query.get_or_404(position_id)
    if position.user_id != current_user.id:
        return jsonify({"error": "Forbidden"}), 403

    price = alpaca_service.get_latest_price(position.ticker)
    trade = close_position(position, price, "MANUAL_CLOSE", alpaca_service, socketio=socketio)

    if trade:
        postmortem = generate_postmortem(trade, ai_service=ai_service)
        socketio.emit("postmortem_completed", postmortem)

    return jsonify({"status": "closed", "exit_price": price})


# ---------------------------------------------------------------------
# Account / positions / orders / portfolio history
# ---------------------------------------------------------------------
@api_bp.route("/account")
@login_required
def api_account():
    return jsonify(alpaca_service.get_account())


@api_bp.route("/positions")
@login_required
def api_positions():
    monitor_open_positions(current_user.id, alpaca_service)
    positions = Position.query.filter_by(user_id=current_user.id, status="OPEN").all()
    return jsonify({"positions": [p.to_dict() for p in positions]})


@api_bp.route("/orders")
@login_required
def api_orders():
    trades = Trade.query.filter_by(user_id=current_user.id).order_by(Trade.created_at.desc()).limit(50).all()
    return jsonify({"orders": [t.to_dict() for t in trades]})


@api_bp.route("/portfolio-history")
@login_required
def api_portfolio_history():
    return jsonify(alpaca_service.get_portfolio_history())


# ---------------------------------------------------------------------
# Risk center data
# ---------------------------------------------------------------------
@api_bp.route("/risk")
@login_required
def api_risk():
    cfg = get_config()
    account = alpaca_service.get_account()
    open_positions = Position.query.filter_by(user_id=current_user.id, status="OPEN").all()
    closed_trades = Trade.query.filter_by(user_id=current_user.id, status="CLOSED").all()

    total_exposure = sum((p.current_price or p.entry_price or 0) * p.quantity for p in open_positions)
    exposure_pct = round((total_exposure / account["equity"]) * 100, 2) if account["equity"] else 0
    daily_pl = sum(t.profit_loss or 0 for t in closed_trades)
    daily_pl_pct = round((daily_pl / account["equity"]) * 100, 2) if account["equity"] else 0

    def status_for(value, warn, critical):
        if value >= critical:
            return "CRITICAL"
        if value >= warn:
            return "WARNING"
        return "SAFE"

    return jsonify({
        "exposure_percent": exposure_pct,
        "exposure_status": status_for(exposure_pct, cfg.MAX_POSITION_PERCENT * 5, cfg.MAX_POSITION_PERCENT * 8),
        "daily_loss_percent": daily_pl_pct,
        "daily_loss_status": status_for(abs(min(0, daily_pl_pct)), cfg.MAX_DAILY_LOSS_PERCENT * 0.6,
                                         cfg.MAX_DAILY_LOSS_PERCENT),
        "open_positions": len(open_positions),
        "max_open_positions": cfg.MAX_OPEN_POSITIONS,
        "max_position_percent": cfg.MAX_POSITION_PERCENT,
        "max_trade_risk_percent": cfg.MAX_TRADE_RISK_PERCENT,
        "max_daily_loss_percent": cfg.MAX_DAILY_LOSS_PERCENT,
        "max_drawdown_percent": cfg.MAX_PORTFOLIO_DRAWDOWN_PERCENT,
        "min_risk_reward": cfg.MIN_RISK_REWARD,
        "min_confidence": cfg.MIN_CONFIDENCE,
    })


@api_bp.route("/agents/status")
@login_required
def api_agents_status():
    names = ["market", "quant", "news", "bull", "bear", "alternative", "strategy", "risk"]
    return jsonify({"agents": [{"name": n, "status": "IDLE"} for n in names]})


@api_bp.route("/journal")
@login_required
def api_journal():
    events = AuditLog.query.filter_by(user_id=current_user.id).order_by(AuditLog.timestamp.desc()).limit(100).all()
    return jsonify({"events": [e.to_dict() for e in events]})


@api_bp.route("/trade/<int:trade_id>")
@login_required
def api_trade_detail(trade_id):
    trade = Trade.query.get_or_404(trade_id)
    if trade.user_id != current_user.id:
        return jsonify({"error": "Forbidden"}), 403

    postmortem = None
    if trade.status == "CLOSED":
        postmortem = generate_postmortem(trade, ai_service=ai_service)

    return jsonify({
        "trade": trade.to_dict(),
        "decisions": [d.to_dict() for d in trade.decisions],
        "risk_checks": [r.to_dict() for r in trade.risk_checks],
        "postmortem": postmortem,
    })


# ---------------------------------------------------------------------
# Strategy Lab - simple historical backtest on demo/real bars
# ---------------------------------------------------------------------
@api_bp.route("/backtest", methods=["POST"])
@login_required
def api_backtest():
    data = request.get_json(force=True)
    ticker = (data.get("ticker") or "NVDA").upper()
    starting_capital = float(data.get("starting_capital", 10000))
    days = int(data.get("days", 90))

    bars = alpaca_service.get_historical_bars(ticker, days=days)
    from trading.indicator_engine import sma

    closes = [b["c"] for b in bars]
    capital = starting_capital
    position = 0
    entry_price = 0
    trades = []
    equity_curve = []

    for i in range(50, len(closes)):
        window = closes[: i + 1]
        fast = sma(window, 10)
        slow = sma(window, 30)
        price = closes[i]

        if fast and slow:
            if fast > slow and position == 0:
                position = capital / price
                entry_price = price
                capital = 0
                trades.append({"type": "BUY", "price": round(price, 2), "index": i})
            elif fast < slow and position > 0:
                capital = position * price
                pl = round((price - entry_price) * position, 2)
                trades.append({"type": "SELL", "price": round(price, 2), "index": i, "pl": pl})
                position = 0

        equity_curve.append(round(capital + position * price, 2))

    final_price = closes[-1]
    final_capital = capital + position * final_price
    wins = [t for t in trades if t.get("pl", 0) > 0]
    sells = [t for t in trades if t["type"] == "SELL"]
    win_rate = round((len(wins) / len(sells)) * 100, 1) if sells else 0

    peak = starting_capital
    max_dd = 0
    for eq in equity_curve:
        peak = max(peak, eq)
        dd = (peak - eq) / peak * 100 if peak else 0
        max_dd = max(max_dd, dd)

    total_return = round(((final_capital - starting_capital) / starting_capital) * 100, 2)

    return jsonify({
        "ticker": ticker,
        "is_simulation": True,
        "disclaimer": "Historical backtest simulation. Past performance does not guarantee future results.",
        "initial_capital": starting_capital,
        "final_capital": round(final_capital, 2),
        "total_return_percent": total_return,
        "win_rate_percent": win_rate,
        "number_of_trades": len(sells),
        "max_drawdown_percent": round(max_dd, 2),
        "equity_curve": equity_curve,
        "trades": trades,
    })

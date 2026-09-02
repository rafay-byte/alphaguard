"""
AlphaGuard AI - Position Monitor
Periodically re-prices open positions, checks stop-loss / take-profit,
and flags positions for AI re-evaluation. Any resulting EXIT order still
goes through the same executor/risk path - never bypassed.
"""
from datetime import datetime, timezone
from models import db
from models.position import Position
from models.trade import Trade
from models.audit_log import AuditLog


def monitor_open_positions(user_id, alpaca_service, socketio=None):
    positions = Position.query.filter_by(user_id=user_id, status="OPEN").all()
    updates = []

    for pos in positions:
        is_option = getattr(pos, 'is_option', False)
        
        if is_option and pos.option_symbol:
            price = alpaca_service.get_latest_option_price(pos.option_symbol)
            multiplier = 100
        else:
            price = alpaca_service.get_latest_price(pos.ticker)
            multiplier = 1

        pos.current_price = price
        pos.unrealized_pl = round((price - pos.entry_price) * pos.quantity * multiplier, 2)

        exit_reason = None
        if pos.stop_loss and price <= pos.stop_loss:
            exit_reason = "STOP_LOSS_HIT"
        elif pos.take_profit and price >= pos.take_profit:
            exit_reason = "TAKE_PROFIT_HIT"

        if exit_reason:
            close_position(pos, price, exit_reason, alpaca_service, socketio)
        else:
            db.session.commit()
            updates.append(pos.to_dict())
            if socketio:
                socketio.emit("position_updated", pos.to_dict())

    return updates


def close_position(pos, exit_price, reason, alpaca_service, socketio=None):
    close_symbol = pos.option_symbol if getattr(pos, 'is_option', False) and pos.option_symbol else pos.ticker
    alpaca_service.close_position(close_symbol)

    pos.status = "CLOSED"
    pos.closed_at = datetime.now(timezone.utc)
    pos.current_price = exit_price

    trade = Trade.query.get(pos.trade_id) if pos.trade_id else None
    if trade:
        trade.exit_price = exit_price
        trade.status = "CLOSED"
        trade.closed_at = datetime.now(timezone.utc)
        direction = 1 if trade.action == "BUY" else -1
        multiplier = 100 if getattr(trade, 'is_option', False) else 1
        trade.profit_loss = round((exit_price - trade.entry_price) * trade.quantity * multiplier * direction, 2)

    log = AuditLog(
        user_id=pos.user_id, event_type="POSITION_CLOSED",
        message=f"{pos.ticker} closed @ {exit_price} ({reason})",
        ticker=pos.ticker, severity="WARNING" if reason == "STOP_LOSS_HIT" else "SUCCESS",
    )
    db.session.add(log)
    db.session.commit()

    if socketio:
        socketio.emit("trade_completed", {"ticker": pos.ticker, "reason": reason,
                                           "exit_price": exit_price,
                                           "trade_id": trade.id if trade else None})
    return trade

"""
AlphaGuard AI - Trade Executor
Bridges an APPROVED risk decision to the Alpaca paper order and persists
the full audit trail. Only ever called after RiskEngine.evaluate() returns
approved=True.
"""
from datetime import datetime, timezone
from models import db
from models.trade import Trade
from models.position import Position
from models.audit_log import AuditLog


def execute_approved_trade(user_id, proposal, risk_result, alpaca_service, socketio=None):
    ticker = proposal["ticker"]
    action = proposal["action"]
    qty = risk_result["position_size"]

    is_option = proposal.get("is_option", False)
    trade = Trade(
        user_id=user_id,
        ticker=ticker,
        action=action,
        quantity=qty,
        entry_price=proposal["entry_price"],
        stop_loss=proposal["stop_loss"],
        take_profit=proposal["take_profit"],
        risk_reward=risk_result.get("risk_reward"),
        confidence=proposal.get("confidence"),
        strategy_name=proposal.get("strategy_name", "AlphaGuard Composite"),
        status="APPROVED",
        is_demo=not alpaca_service.configured,
        is_option=is_option,
        option_symbol=proposal.get("option_symbol"),
        option_type=proposal.get("option_type"),
        option_strike=proposal.get("option_strike"),
        option_expiry=proposal.get("option_expiry"),
    )
    db.session.add(trade)
    db.session.commit()

    if socketio:
        socketio.emit("order_submitted", {"ticker": ticker, "trade_id": trade.id, "qty": qty})

    # If it's an option, submit the option symbol instead of the underlying ticker
    order_symbol = trade.option_symbol if trade.is_option else ticker
    order = alpaca_service.submit_market_order(order_symbol, qty, side="buy" if action == "BUY" else "sell")

    trade.alpaca_order_id = order.get("id")
    trade.status = "OPEN" if order.get("status") in ("FILLED", "filled") else "PENDING"
    if order.get("filled_avg_price"):
        trade.entry_price = order["filled_avg_price"]
    db.session.commit()

    position = Position(
        user_id=user_id, trade_id=trade.id, ticker=ticker, quantity=qty,
        entry_price=trade.entry_price, current_price=trade.entry_price,
        stop_loss=trade.stop_loss, take_profit=trade.take_profit, status="OPEN",
        is_option=trade.is_option,
        option_symbol=trade.option_symbol,
        option_type=trade.option_type,
        option_strike=trade.option_strike,
        option_expiry=trade.option_expiry,
    )
    db.session.add(position)

    log = AuditLog(
        user_id=user_id, event_type="ORDER_FILLED",
        message=f"{action} {qty} {ticker} @ {trade.entry_price} "
                f"({'DEMO' if trade.is_demo else 'ALPACA PAPER'})",
        ticker=ticker, severity="SUCCESS",
    )
    db.session.add(log)
    db.session.commit()

    if socketio:
        socketio.emit("order_filled", {"ticker": ticker, "trade_id": trade.id,
                                        "price": trade.entry_price, "demo": trade.is_demo})
        socketio.emit("position_updated", position.to_dict())

    return trade, position

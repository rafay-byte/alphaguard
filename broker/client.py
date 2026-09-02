"""
AlphaGuard AI - Alpaca Service Layer
=====================================
Wraps the Alpaca paper-trading API behind a single, safe interface.

- Always defaults to PAPER trading.
- If credentials are missing or a call fails (auth, network, rate limit,
  market closed, invalid symbol, insufficient buying power) the service
  degrades gracefully into deterministic DEMO MODE data instead of crashing.
- No API keys are ever exposed to the frontend - all calls happen server-side.
"""
import random
import math
import time
from datetime import datetime, timedelta, timezone

from flask import current_app


class AlpacaError(Exception):
    pass


class AlpacaService:
    def __init__(self, app=None):
        self.trading_client = None
        self.data_client = None
        self.configured = False
        self._demo_seed_cache = {}
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        api_key = app.config.get("ALPACA_API_KEY")
        secret_key = app.config.get("ALPACA_SECRET_KEY")
        self.configured = bool(api_key and secret_key)

        if self.configured:
            try:
                from alpaca.trading.client import TradingClient
                from alpaca.data.historical import StockHistoricalDataClient
                from alpaca.data.historical.option import OptionHistoricalDataClient
                self.trading_client = TradingClient(api_key, secret_key, paper=True)
                self.data_client = StockHistoricalDataClient(api_key, secret_key)
                self.option_data_client = OptionHistoricalDataClient(api_key, secret_key)
            except Exception as e:
                app.logger.warning(f"Alpaca client init failed, falling back to demo mode: {e}")
                self.configured = False

    # ------------------------------------------------------------------
    # Deterministic demo data generator (seeded per-ticker so numbers
    # stay internally consistent across a session, but still move).
    # ------------------------------------------------------------------
    def _seed_for(self, ticker):
        if ticker not in self._demo_seed_cache:
            base_prices = {
                "NVDA": 128.40, "MSFT": 441.20, "AAPL": 227.80,
                "QQQ": 486.10, "TSLA": 258.90, "AMD": 152.30,
            }
            base = base_prices.get(ticker, 100 + (sum(ord(c) for c in ticker) % 200))
            self._demo_seed_cache[ticker] = {
                "base": base,
                "rand": random.Random(sum(ord(c) for c in ticker) * 7919),
            }
        return self._demo_seed_cache[ticker]

    def get_demo_bars(self, ticker, days=90):
        seed = self._seed_for(ticker)
        rnd = seed["rand"]
        price = seed["base"] * 0.9
        bars = []
        now = datetime.now(timezone.utc)
        for i in range(days):
            drift = math.sin(i / 9.0) * 0.6
            change_pct = rnd.gauss(0.05 + drift * 0.05, 1.4) / 100.0
            price = max(1.0, price * (1 + change_pct))
            high = price * (1 + abs(rnd.gauss(0, 0.006)))
            low = price * (1 - abs(rnd.gauss(0, 0.006)))
            open_p = price * (1 + rnd.gauss(0, 0.003))
            volume = int(abs(rnd.gauss(5_000_000, 1_500_000)))
            bars.append({
                "t": (now - timedelta(days=(days - i))).isoformat(),
                "o": round(open_p, 2),
                "h": round(high, 2),
                "l": round(low, 2),
                "c": round(price, 2),
                "v": volume,
            })
        return bars

    # ------------------------------------------------------------------
    # Account
    # ------------------------------------------------------------------
    def get_account(self):
        if self.configured:
            try:
                acc = self.trading_client.get_account()
                return {
                    "equity": float(acc.equity),
                    "cash": float(acc.cash),
                    "buying_power": float(acc.buying_power),
                    "portfolio_value": float(acc.portfolio_value),
                    "daytrade_count": acc.daytrade_count,
                    "status": acc.status.value if hasattr(acc.status, "value") else str(acc.status),
                    "demo": False,
                }
            except Exception as e:
                current_app.logger.warning(f"Alpaca get_account failed, using demo: {e}")

        return {
            "equity": 100000.00,
            "cash": 42500.00,
            "buying_power": 85000.00,
            "portfolio_value": 100000.00,
            "daytrade_count": 0,
            "status": "ACTIVE",
            "demo": True,
        }

    # ------------------------------------------------------------------
    # Market Data
    # ------------------------------------------------------------------
    def get_latest_price(self, ticker):
        if self.configured:
            try:
                from alpaca.data.requests import StockLatestTradeRequest
                req = StockLatestTradeRequest(symbol_or_symbols=ticker)
                trade = self.data_client.get_stock_latest_trade(req)
                return float(trade[ticker].price)
            except Exception as e:
                current_app.logger.warning(f"Alpaca get_latest_price failed for {ticker}: {e}")

        bars = self.get_demo_bars(ticker, days=2)
        return bars[-1]["c"]

    def get_historical_bars(self, ticker, days=90):
        if self.configured:
            try:
                from alpaca.data.requests import StockBarsRequest
                from alpaca.data.timeframe import TimeFrame
                req = StockBarsRequest(
                    symbol_or_symbols=ticker,
                    timeframe=TimeFrame.Day,
                    start=datetime.now(timezone.utc) - timedelta(days=days),
                )
                barset = self.data_client.get_stock_bars(req)
                out = []
                for b in barset[ticker]:
                    out.append({
                        "t": b.timestamp.isoformat(), "o": float(b.open), "h": float(b.high),
                        "l": float(b.low), "c": float(b.close), "v": float(b.volume),
                    })
                if out:
                    return out
            except Exception as e:
                current_app.logger.warning(f"Alpaca get_historical_bars failed for {ticker}: {e}")

        return self.get_demo_bars(ticker, days=days)

    # ------------------------------------------------------------------
    # Options Data
    # ------------------------------------------------------------------
    def get_option_chain(self, ticker):
        """Returns a simplified option chain (simulated in demo mode)."""
        if self.configured:
            try:
                from alpaca.data.requests import OptionChainRequest
                req = OptionChainRequest(underlying_symbol=ticker)
                chain = self.option_data_client.get_option_chain(req)
                out = []
                for symbol, data in chain.items():
                    # Parse symbol: e.g. TSLA240816C00355000
                    # Ticker can be 1-5 chars. Date is 6 chars. Type is 1 char. Strike is 8 chars.
                    # We can parse from the back: last 8 = strike, 9th from back = type, 15th to 10th from back = date
                    strike_str = symbol[-8:]
                    type_char = symbol[-9:-8]
                    date_str = symbol[-15:-9]
                    
                    strike_val = int(strike_str) / 1000.0
                    opt_type = "call" if type_char == "C" else "put"
                    expiry_fmt = f"20{date_str[:2]}-{date_str[2:4]}-{date_str[4:6]}"
                    
                    out.append({
                        "symbol": symbol,
                        "strike": strike_val,
                        "type": opt_type,
                        "expiration": expiry_fmt,
                    })
                if out:
                    return out
            except Exception as e:
                current_app.logger.warning(f"Alpaca get_option_chain failed for {ticker}: {e}")

        # Demo Mode: Generate synthetic ATM options
        base_price = self.get_latest_price(ticker)
        expiry_dt = datetime.now(timezone.utc) + timedelta(days=30)
        expiry = expiry_dt.strftime("%Y-%m-%d")
        date_str = expiry_dt.strftime("%y%m%d")
        strike = round(base_price / 5) * 5
        strike_str = f"{int(strike * 1000):08d}"
        
        return [
            {"symbol": f"{ticker}{date_str}C{strike_str}", "strike": strike, "type": "call", "expiration": expiry},
            {"symbol": f"{ticker}{date_str}P{strike_str}", "strike": strike, "type": "put", "expiration": expiry},
        ]

    def get_latest_option_price(self, option_symbol):
        if self.configured:
            try:
                from alpaca.data.requests import OptionLatestTradeRequest
                req = OptionLatestTradeRequest(symbol_or_symbols=option_symbol)
                trade = self.option_data_client.get_option_latest_trade(req)
                return float(trade[option_symbol].price)
            except Exception as e:
                current_app.logger.warning(f"Alpaca get_latest_option_price failed for {option_symbol}: {e}")
                
        # Demo mode: synthetic option premium (around 3% of underlying)
        ticker = option_symbol[:4].replace("2", "") # rough parsing
        if len(ticker) < 2: ticker = "NVDA"
        underlying = self.get_latest_price(ticker)
        return round(underlying * 0.03, 2)

    # ------------------------------------------------------------------
    # Positions / Orders
    # ------------------------------------------------------------------
    def get_positions(self):
        if self.configured:
            try:
                positions = self.trading_client.get_all_positions()
                return [{
                    "ticker": p.symbol, "quantity": float(p.qty),
                    "entry_price": float(p.avg_entry_price),
                    "current_price": float(p.current_price),
                    "unrealized_pl": float(p.unrealized_pl),
                    "demo": False,
                } for p in positions]
            except Exception as e:
                current_app.logger.warning(f"Alpaca get_positions failed: {e}")
        return []

    def get_orders(self, limit=50):
        if self.configured:
            try:
                from alpaca.trading.requests import GetOrdersRequest
                orders = self.trading_client.get_orders(GetOrdersRequest(limit=limit))
                return [{
                    "id": str(o.id), "symbol": o.symbol, "side": o.side.value,
                    "status": o.status.value, "qty": float(o.qty or 0),
                    "filled_avg_price": float(o.filled_avg_price) if o.filled_avg_price else None,
                } for o in orders]
            except Exception as e:
                current_app.logger.warning(f"Alpaca get_orders failed: {e}")
        return []

    def get_portfolio_history(self):
        if self.configured:
            try:
                hist = self.trading_client.get_portfolio_history()
                return {"equity": [float(x) for x in hist.equity], "timestamp": hist.timestamp}
            except Exception as e:
                current_app.logger.warning(f"Alpaca get_portfolio_history failed: {e}")

        rnd = random.Random(42)
        equity = [100000.0]
        for _ in range(29):
            equity.append(round(equity[-1] * (1 + rnd.gauss(0.001, 0.008)), 2))
        return {"equity": equity, "timestamp": None, "demo": True}

    def submit_market_order(self, ticker, qty, side="buy"):
        """side: 'buy' or 'sell'. Returns order dict. Falls back to a simulated
        FILLED paper order in demo mode - clearly marked as demo, never presented
        as a real Alpaca fill."""
        if self.configured:
            try:
                from alpaca.trading.requests import MarketOrderRequest
                from alpaca.trading.enums import OrderSide, TimeInForce
                order_side = OrderSide.BUY if side == "buy" else OrderSide.SELL
                req = MarketOrderRequest(
                    symbol=ticker, qty=qty, side=order_side, time_in_force=TimeInForce.DAY,
                )
                order = self.trading_client.submit_order(req)
                return {
                    "id": str(order.id), "symbol": order.symbol, "side": side,
                    "qty": float(qty), "status": order.status.value, "demo": False,
                }
            except Exception as e:
                current_app.logger.warning(f"Alpaca submit_market_order failed: {e}")
                raise AlpacaError(str(e))

        price = self.get_latest_price(ticker)
        return {
            "id": f"DEMO-{int(time.time() * 1000)}", "symbol": ticker, "side": side,
            "qty": float(qty), "status": "FILLED", "filled_avg_price": price, "demo": True,
        }

    def close_position(self, ticker):
        if self.configured:
            try:
                self.trading_client.close_position(ticker)
                return {"status": "CLOSED", "demo": False}
            except Exception as e:
                current_app.logger.warning(f"Alpaca close_position failed: {e}")
        return {"status": "CLOSED", "demo": True}

    def cancel_order(self, order_id):
        if self.configured:
            try:
                self.trading_client.cancel_order_by_id(order_id)
                return {"status": "CANCELED", "demo": False}
            except Exception as e:
                current_app.logger.warning(f"Alpaca cancel_order failed: {e}")
        return {"status": "CANCELED", "demo": True}

    def get_order_status(self, order_id):
        if self.configured:
            try:
                order = self.trading_client.get_order_by_id(order_id)
                return {"id": str(order.id), "status": order.status.value, "demo": False}
            except Exception as e:
                current_app.logger.warning(f"Alpaca get_order_status failed: {e}")
        return {"id": order_id, "status": "FILLED", "demo": True}


alpaca_service = AlpacaService()

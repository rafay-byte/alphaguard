"""
AlphaGuard AI - Deterministic Quant Indicator Engine
======================================================
All numbers here are computed with real math from OHLCV bars.
The LLM is never asked to invent an indicator value.
"""
import statistics


def sma(closes, period):
    if len(closes) < period:
        return None
    return sum(closes[-period:]) / period


def ema_series(closes, period):
    if len(closes) < period:
        return []
    k = 2 / (period + 1)
    ema_vals = [sum(closes[:period]) / period]
    for price in closes[period:]:
        ema_vals.append(price * k + ema_vals[-1] * (1 - k))
    return ema_vals


def ema(closes, period):
    series = ema_series(closes, period)
    return series[-1] if series else None


def rsi(closes, period=14):
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def macd(closes, fast=12, slow=26, signal=9):
    if len(closes) < slow + signal:
        return None, None, None
    ema_fast = ema_series(closes, fast)
    ema_slow = ema_series(closes, slow)
    offset = len(ema_fast) - len(ema_slow)
    macd_line = [ema_fast[i + offset] - ema_slow[i] for i in range(len(ema_slow))]
    if len(macd_line) < signal:
        return round(macd_line[-1], 4), None, None
    signal_series = ema_series(macd_line, signal)
    signal_line = signal_series[-1]
    macd_val = macd_line[-1]
    histogram = macd_val - signal_line
    return round(macd_val, 4), round(signal_line, 4), round(histogram, 4)


def bollinger_bands(closes, period=20, num_std=2):
    if len(closes) < period:
        return None, None, None
    window = closes[-period:]
    mid = sum(window) / period
    std = statistics.pstdev(window)
    upper = mid + num_std * std
    lower = mid - num_std * std
    return round(upper, 2), round(mid, 2), round(lower, 2)


def atr(bars, period=14):
    if len(bars) < period + 1:
        return None
    trs = []
    for i in range(1, len(bars)):
        high, low, prev_close = bars[i]["h"], bars[i]["l"], bars[i - 1]["c"]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)
    if len(trs) < period:
        return round(sum(trs) / len(trs), 4)
    return round(sum(trs[-period:]) / period, 4)


def volatility(closes, period=20):
    if len(closes) < period:
        return None
    window = closes[-period:]
    returns = [(window[i] - window[i - 1]) / window[i - 1] for i in range(1, len(window))]
    if not returns:
        return 0.0
    return round(statistics.pstdev(returns) * (252 ** 0.5) * 100, 2)  # annualized %


def volume_change(bars, period=20):
    if len(bars) < period + 1:
        return None
    recent_avg = sum(b["v"] for b in bars[-period:]) / period
    prior_avg = sum(b["v"] for b in bars[-(period * 2):-period]) / period if len(bars) >= period * 2 else recent_avg
    if prior_avg == 0:
        return 0.0
    return round(((recent_avg - prior_avg) / prior_avg) * 100, 2)


def momentum(closes, period=10):
    if len(closes) < period + 1:
        return None
    return round(((closes[-1] - closes[-1 - period]) / closes[-1 - period]) * 100, 2)


def compute_all_indicators(bars):
    """bars: list of dicts with o/h/l/c/v, oldest -> newest."""
    closes = [b["c"] for b in bars]
    macd_val, macd_signal, macd_hist = macd(closes)
    bb_upper, bb_mid, bb_lower = bollinger_bands(closes)

    return {
        "price": closes[-1] if closes else None,
        "sma20": sma(closes, 20),
        "sma50": sma(closes, 50),
        "ema20": ema(closes, 20),
        "ema50": ema(closes, 50),
        "rsi": rsi(closes),
        "macd": macd_val,
        "macd_signal": macd_signal,
        "macd_histogram": macd_hist,
        "bb_upper": bb_upper,
        "bb_mid": bb_mid,
        "bb_lower": bb_lower,
        "atr": atr(bars),
        "volatility": volatility(closes),
        "volume_change": volume_change(bars),
        "momentum": momentum(closes),
    }


def quant_score(indicators):
    """Deterministic 0-100 composite quant score."""
    score = 50.0
    price = indicators.get("price")
    sma20, sma50 = indicators.get("sma20"), indicators.get("sma50")
    ema20, ema50 = indicators.get("ema20"), indicators.get("ema50")
    rsi_v = indicators.get("rsi")
    macd_v, macd_sig = indicators.get("macd"), indicators.get("macd_signal")
    momentum_v = indicators.get("momentum")
    vol_change = indicators.get("volume_change")

    trend_score = 50.0
    if price and sma20 and sma50:
        if price > sma20 > sma50:
            trend_score = 85
        elif price > sma20:
            trend_score = 70
        elif price < sma20 < sma50:
            trend_score = 20
        elif price < sma20:
            trend_score = 35
    if ema20 and ema50:
        trend_score += 5 if ema20 > ema50 else -5
    trend_score = max(0, min(100, trend_score))

    momentum_score = 50.0
    if momentum_v is not None:
        momentum_score = max(0, min(100, 50 + momentum_v * 3))

    volume_score = 50.0
    if vol_change is not None:
        volume_score = max(0, min(100, 50 + vol_change * 1.2))

    rsi_score = 50.0
    if rsi_v is not None:
        if rsi_v > 70:
            rsi_score = 60  # overbought - still bullish but riskier
        elif rsi_v < 30:
            rsi_score = 40  # oversold - potential reversal
        else:
            rsi_score = 50 + (rsi_v - 50) * 0.6

    macd_score = 50.0
    if macd_v is not None and macd_sig is not None:
        macd_score = 70 if macd_v > macd_sig else 30

    overall = (
        trend_score * 0.35 +
        momentum_score * 0.20 +
        volume_score * 0.15 +
        rsi_score * 0.15 +
        macd_score * 0.15
    )

    return {
        "trend_score": round(trend_score, 1),
        "momentum_score": round(momentum_score, 1),
        "volume_score": round(volume_score, 1),
        "rsi_score": round(rsi_score, 1),
        "macd_score": round(macd_score, 1),
        "overall_score": round(max(0, min(100, overall)), 1),
    }

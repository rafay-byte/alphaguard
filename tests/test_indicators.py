from trading.indicator_engine import sma, ema, rsi, compute_all_indicators, quant_score


def make_bars(n=60, start=100.0, step=0.5):
    bars = []
    price = start
    for i in range(n):
        price += step if i % 2 == 0 else -step * 0.4
        bars.append({"o": price, "h": price * 1.01, "l": price * 0.99, "c": price, "v": 1_000_000 + i * 1000})
    return bars


def test_sma_basic():
    closes = [1, 2, 3, 4, 5]
    assert sma(closes, 5) == 3.0
    assert sma(closes, 10) is None


def test_ema_moves_toward_recent_price():
    closes = [10] * 30 + [20]
    val = ema(closes, 20)
    assert val is not None
    assert 10 < val < 20


def test_rsi_bounds():
    closes = [100 + i for i in range(30)]  # strictly increasing
    val = rsi(closes)
    assert val == 100.0


def test_compute_all_indicators_and_score():
    bars = make_bars()
    indicators = compute_all_indicators(bars)
    assert indicators["price"] is not None
    scores = quant_score(indicators)
    assert 0 <= scores["overall_score"] <= 100

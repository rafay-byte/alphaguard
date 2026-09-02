from trading.position_sizer import calculate_position_size


def test_position_sizing_basic():
    result = calculate_position_size(equity=100000, risk_percent=1, entry_price=100, stop_price=95)
    assert result["max_risk_dollars"] == 1000
    assert result["risk_per_share"] == 5
    assert result["max_shares"] == 200


def test_position_sizing_zero_when_no_stop_distance():
    result = calculate_position_size(equity=100000, risk_percent=1, entry_price=100, stop_price=100)
    assert result["max_shares"] == 0

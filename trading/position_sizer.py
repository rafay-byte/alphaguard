"""
AlphaGuard AI - Deterministic Position Sizing
Never lets the AI arbitrarily pick a position size.
"""


def calculate_position_size(equity, risk_percent, entry_price, stop_price):
    """Returns dict with the full sizing calculation, shown to the user for transparency."""
    if entry_price is None or stop_price is None or entry_price == stop_price:
        return {
            "equity": equity, "risk_percent": risk_percent, "max_risk_dollars": 0,
            "entry_price": entry_price, "stop_price": stop_price,
            "risk_per_share": 0, "max_shares": 0,
        }

    max_risk_dollars = round(equity * (risk_percent / 100.0), 2)
    risk_per_share = round(abs(entry_price - stop_price), 4)
    max_shares = int(max_risk_dollars / risk_per_share) if risk_per_share else 0

    return {
        "equity": equity,
        "risk_percent": risk_percent,
        "max_risk_dollars": max_risk_dollars,
        "entry_price": entry_price,
        "stop_price": stop_price,
        "risk_per_share": risk_per_share,
        "max_shares": max_shares,
    }

"""Market Analyst Agent - trend / regime analysis.

When USE_ALPACA_MCP is enabled, this agent also pulls live account context
(equity, buying power, open positions) from Alpaca's official MCP server
via the Model Context Protocol. This enriches the analysis with portfolio
awareness — the agent knows how much capital is available and what
positions are already open before recommending new trades.
"""
import logging

logger = logging.getLogger(__name__)


def _get_mcp_context():
    """Attempt to pull account context from Alpaca's official MCP server.
    Returns a dict with account info, or empty dict if MCP is unavailable."""
    try:
        from config import Config
        if not Config.USE_ALPACA_MCP:
            return {}

        from services.mcp_client import mcp_get_account, mcp_get_positions

        context = {}

        account = mcp_get_account()
        if account:
            context["mcp_account"] = {
                "equity": account.get("equity"),
                "cash": account.get("cash"),
                "buying_power": account.get("buying_power"),
                "portfolio_value": account.get("portfolio_value"),
            }
            logger.info(f"[MCP] Account context loaded: equity={account.get('equity')}")

        positions = mcp_get_positions()
        if positions:
            if isinstance(positions, list):
                context["mcp_position_count"] = len(positions)
                context["mcp_position_symbols"] = [
                    p.get("symbol", "?") for p in positions[:10]
                ]
            elif isinstance(positions, dict):
                context["mcp_positions"] = positions
            logger.info(f"[MCP] Positions context loaded")

        return context

    except Exception as e:
        logger.debug(f"[MCP] Could not load account context: {e}")
        return {}


def run_market_agent(ticker, indicators, scores, ai_service):
    price = indicators.get("price")
    sma20, sma50 = indicators.get("sma20"), indicators.get("sma50")

    if price and sma20 and sma50 and price > sma20 > sma50:
        regime = "TRENDING_UP"
        trend = "BULLISH"
    elif price and sma20 and sma50 and price < sma20 < sma50:
        regime = "TRENDING_DOWN"
        trend = "BEARISH"
    else:
        regime = "RANGING"
        trend = "NEUTRAL"

    # Pull live account context from Alpaca's MCP server (if enabled)
    mcp_context = _get_mcp_context()

    def fallback():
        reasoning = (
            f"{ticker} is trading at {price}, "
            f"{'above' if sma20 and price > sma20 else 'near/below'} its 20-day average. "
            f"Market regime classified as {regime.replace('_', ' ').title()}."
        )
        if mcp_context.get("mcp_account"):
            acct = mcp_context["mcp_account"]
            reasoning += (
                f" [MCP Context] Portfolio equity: ${acct.get('equity', 'N/A')}, "
                f"buying power: ${acct.get('buying_power', 'N/A')}."
            )
        return {
            "ticker": ticker, "trend": trend, "confidence": round(scores['overall_score'] / 100, 2),
            "market_regime": regime, "reasoning": reasoning, "score": scores["trend_score"],
        }

    system = "You are a professional market analyst. Respond ONLY with JSON matching the schema."

    # Build the user prompt — include MCP account context if available
    user_parts = [
        f"Ticker: {ticker}\nPrice: {price}\nSMA20: {sma20}\nSMA50: {sma50}\n"
        f"Quant scores: {scores}\n"
    ]
    if mcp_context.get("mcp_account"):
        acct = mcp_context["mcp_account"]
        user_parts.append(
            f"[Live Account Context via Alpaca MCP Server]\n"
            f"Portfolio Equity: ${acct.get('equity', 'N/A')}\n"
            f"Buying Power: ${acct.get('buying_power', 'N/A')}\n"
            f"Open Positions: {mcp_context.get('mcp_position_count', 'N/A')}\n"
            f"Current Holdings: {mcp_context.get('mcp_position_symbols', [])}\n"
        )
    user_parts.append(
        'Schema: {"ticker": str, "trend": "BULLISH|BEARISH|NEUTRAL", "confidence": float(0-1), '
        '"market_regime": str, "reasoning": str, "score": float(0-100)}'
    )
    user = "\n".join(user_parts)

    return ai_service.complete_json(system, user, fallback)


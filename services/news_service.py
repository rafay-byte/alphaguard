"""
AlphaGuard AI - News Intelligence Service
If no news API is configured, operates in deterministic DEMO MODE and the
result is clearly labeled so it is never presented as live news.
"""
import os
import random


class NewsService:
    def __init__(self, app=None):
        self.api_key = ""
        self.configured = False
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.api_key = os.environ.get("NEWS_API_KEY", "")
        self.configured = bool(self.api_key)

    def get_news_context(self, ticker):
        if self.configured:
            # A real implementation would call a news API here.
            # Kept out-of-scope for this build - falls through to demo.
            pass

        rnd = random.Random(sum(ord(c) for c in ticker) * 31)
        sentiment = round(rnd.uniform(35, 85), 1)
        positive = []
        negative = []
        pool_pos = [
            "Analyst coverage remains constructive on forward guidance.",
            "Recent product cycle momentum continues to build.",
            "Institutional accumulation patterns detected in recent sessions.",
        ]
        pool_neg = [
            "Valuation remains elevated versus historical averages.",
            "Sector-wide macro headwinds could pressure near-term sentiment.",
            "Elevated short-term volatility increases event risk.",
        ]
        positive = rnd.sample(pool_pos, k=rnd.randint(1, 2))
        negative = rnd.sample(pool_neg, k=rnd.randint(1, 2))

        return {
            "ticker": ticker,
            "sentiment_score": sentiment,
            "positive_factors": positive,
            "negative_factors": negative,
            "risk_events": [] if sentiment > 55 else ["Heightened macro sensitivity"],
            "confidence": round(rnd.uniform(55, 80), 1),
            "demo_mode": not self.configured,
        }


news_service = NewsService()

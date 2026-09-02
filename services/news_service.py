"""
AlphaGuard AI - News Intelligence Service
Connects directly to Alpaca's Live News Feed (Benzinga / Reuters / Dow Jones).
If Alpaca keys are missing or offline, falls back gracefully to a deterministic model.
"""
import os
import random
from datetime import datetime


class NewsService:
    def __init__(self, app=None):
        self.news_client = None
        self.configured = False
        if app:
            self.init_app(app)

    def init_app(self, app):
        api_key = app.config.get("ALPACA_API_KEY", os.environ.get("ALPACA_API_KEY", ""))
        secret_key = app.config.get("ALPACA_SECRET_KEY", os.environ.get("ALPACA_SECRET_KEY", ""))
        if api_key and secret_key:
            try:
                from alpaca.data.historical.news import NewsClient
                self.news_client = NewsClient(api_key=api_key, secret_key=secret_key)
                self.configured = True
            except Exception as e:
                self.configured = False

    def get_news_context(self, ticker):
        if not self.news_client:
            api_key = os.environ.get("ALPACA_API_KEY", "")
            secret_key = os.environ.get("ALPACA_SECRET_KEY", "")
            if api_key and secret_key:
                try:
                    from alpaca.data.historical.news import NewsClient
                    self.news_client = NewsClient(api_key=api_key, secret_key=secret_key)
                    self.configured = True
                except Exception:
                    pass

        if self.news_client:
            try:
                from alpaca.data.requests import NewsRequest
                req = NewsRequest(symbols=ticker, limit=6)
                response = self.news_client.get_news(req)
                articles = getattr(response, "news", []) if hasattr(response, "news") else response.get("news", [])
                
                if articles:
                    positive_keywords = ["growth", "record", "upgrade", "beat", "rally", "scale", "launch", "bull", "surge", "gain", "profit", "expansion"]
                    negative_keywords = ["risk", "downgrade", "fall", "warn", "drop", "headwind", "cut", "decline", "slowdown", "short", "loss", "probe", "lawsuit"]
                    
                    positive_factors = []
                    negative_factors = []
                    pos_count = 0
                    neg_count = 0

                    for art in articles:
                        headline = art.headline or ""
                        summary = art.summary or ""
                        full_text = f"{headline} {summary}".lower()

                        p_hits = sum(1 for kw in positive_keywords if kw in full_text)
                        n_hits = sum(1 for kw in negative_keywords if kw in full_text)
                        pos_count += p_hits
                        neg_count += n_hits

                        if p_hits > n_hits and len(positive_factors) < 3:
                            positive_factors.append(headline)
                        elif n_hits > 0 and len(negative_factors) < 3:
                            negative_factors.append(headline)

                    total = pos_count + neg_count
                    if total > 0:
                        sentiment_score = round(50 + (pos_count - neg_count) / total * 35, 1)
                    else:
                        sentiment_score = 55.0
                    sentiment_score = max(20.0, min(90.0, sentiment_score))

                    if not positive_factors and articles:
                        positive_factors = [articles[0].headline]
                    if not negative_factors and len(articles) > 1:
                        negative_factors = [articles[1].headline]

                    return {
                        "ticker": ticker,
                        "sentiment_score": sentiment_score,
                        "positive_factors": positive_factors,
                        "negative_factors": negative_factors,
                        "risk_events": ["Live event headline flagged"] if sentiment_score < 45 else [],
                        "confidence": 75.0,
                        "demo_mode": False,
                        "headlines_count": len(articles),
                    }
            except Exception:
                pass

        # Deterministic Fallback if offline
        rnd = random.Random(sum(ord(c) for c in ticker) * 31)
        sentiment = round(rnd.uniform(35, 85), 1)
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
        return {
            "ticker": ticker,
            "sentiment_score": sentiment,
            "positive_factors": rnd.sample(pool_pos, k=rnd.randint(1, 2)),
            "negative_factors": rnd.sample(pool_neg, k=rnd.randint(1, 2)),
            "risk_events": [] if sentiment > 55 else ["Heightened macro sensitivity"],
            "confidence": round(rnd.uniform(55, 80), 1),
            "demo_mode": True,
        }


news_service = NewsService()


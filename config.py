"""
AlphaGuard AI - Configuration
Central place for all environment-driven configuration.
Never hard-codes secrets. Falls back to safe demo defaults.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _bool(val, default=False):
    if val is None:
        return default
    return str(val).strip().lower() in ("1", "true", "yes", "on")


class Config:
    # --- Core Flask ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-key-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///alphaguard.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    APP_ENV = os.environ.get("APP_ENV", "development")

    # --- Alpaca ---
    ALPACA_API_KEY = os.environ.get("ALPACA_API_KEY", "").strip()
    ALPACA_SECRET_KEY = os.environ.get("ALPACA_SECRET_KEY", "").strip()
    ALPACA_BASE_URL = os.environ.get("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    ALPACA_CONFIGURED = bool(ALPACA_API_KEY and ALPACA_SECRET_KEY)

    # --- AI Provider ---
    AI_PROVIDER = os.environ.get("AI_PROVIDER", "openai").strip().lower()
    AI_API_KEY = os.environ.get("AI_API_KEY", "").strip()
    AI_CONFIGURED = bool(AI_API_KEY)

    # --- Demo Mode ---
    # Can be toggled via .env DEMO_MODE=false
    DEMO_MODE = _bool(os.environ.get("DEMO_MODE", "true"))

    # --- Trading Mode Safety ---
    # Hard safety switch. Live trading requires this to be explicitly "live"
    # AND a non-paper ALPACA_BASE_URL. Defaults to paper always.
    TRADING_MODE = "paper"

    # --- Risk Engine Defaults (deterministic, independent of any LLM) ---
    MAX_POSITION_PERCENT = float(os.environ.get("MAX_POSITION_PERCENT", 10))
    MAX_TRADE_RISK_PERCENT = float(os.environ.get("MAX_TRADE_RISK_PERCENT", 1))
    MAX_DAILY_LOSS_PERCENT = float(os.environ.get("MAX_DAILY_LOSS_PERCENT", 2))
    MAX_PORTFOLIO_DRAWDOWN_PERCENT = float(os.environ.get("MAX_PORTFOLIO_DRAWDOWN_PERCENT", 10))
    MAX_OPEN_POSITIONS = int(os.environ.get("MAX_OPEN_POSITIONS", 10))
    MIN_RISK_REWARD = float(os.environ.get("MIN_RISK_REWARD", 1.5))
    MIN_CONFIDENCE = float(os.environ.get("MIN_CONFIDENCE", 65))

    # --- Monitored universe for demo/scan ---
    DEFAULT_WATCHLIST = ["NVDA", "MSFT", "AAPL", "QQQ", "TSLA", "AMD"]

    # --- Scheduler ---
    MONITOR_INTERVAL_SECONDS = int(os.environ.get("MONITOR_INTERVAL_SECONDS", 60))


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


def get_config():
    env = os.environ.get("APP_ENV", "development")
    return ProductionConfig if env == "production" else DevelopmentConfig

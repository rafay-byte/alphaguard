"""
AlphaGuard AI - Application Factory
"""
import os
from flask import Flask, render_template
from flask_login import LoginManager
from flask_socketio import SocketIO

from config import get_config
from models import db, User
from broker.client import alpaca_service
from services.ai_service import ai_service
from services.news_service import news_service

login_manager = LoginManager()
socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(get_config())

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    socketio.init_app(app)

    alpaca_service.init_app(app)
    ai_service.init_app(app)
    news_service.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.trading import trading_bp
    from routes.agents import agents_bp
    from routes.portfolio import portfolio_bp
    from routes.risk import risk_bp
    from routes.strategies import strategies_bp
    from routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(trading_bp)
    app.register_blueprint(agents_bp)
    app.register_blueprint(portfolio_bp)
    app.register_blueprint(risk_bp)
    app.register_blueprint(strategies_bp)
    app.register_blueprint(api_bp)

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception(e)
        return render_template("500.html"), 500

    with app.app_context():
        db.create_all()

    if not app.config.get("TESTING"):
        try:
            from trading.scheduler import start_scheduler
            start_scheduler(app, socketio, alpaca_service,
                             interval_seconds=app.config.get("MONITOR_INTERVAL_SECONDS", 60))
        except Exception as e:
            app.logger.warning(f"Background scheduler failed to start: {e}")

    @app.context_processor
    def inject_globals():
        return {
            "demo_mode": app.config.get("DEMO_MODE"),
            "alpaca_configured": alpaca_service.configured,
            "ai_configured": ai_service.configured,
            "trading_mode": app.config.get("TRADING_MODE", "paper").upper(),
        }

    return app

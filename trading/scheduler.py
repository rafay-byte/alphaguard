"""
AlphaGuard AI - Autonomous Position Monitoring Scheduler
Uses APScheduler to periodically re-price open positions for every user,
check stop-loss/take-profit, and push updates over websockets.
Any resulting exit still goes through the same position_monitor/executor
code path used everywhere else - never bypassed.
"""
from apscheduler.schedulers.background import BackgroundScheduler

_scheduler = None


def start_scheduler(app, socketio, alpaca_service, interval_seconds=60):
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    def job():
        with app.app_context():
            from models.user import User
            from trading.position_monitor import monitor_open_positions
            try:
                for user in User.query.all():
                    monitor_open_positions(user.id, alpaca_service, socketio=socketio)
            except Exception as e:
                app.logger.warning(f"Scheduler monitoring pass failed: {e}")

    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(job, "interval", seconds=interval_seconds, id="position_monitor")
    _scheduler.start()
    return _scheduler

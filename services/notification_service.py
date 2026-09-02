"""
AlphaGuard AI - Notification / Audit Service
Writes to the AuditLog table and (optionally) pushes a websocket toast.
"""
from models import db
from models.audit_log import AuditLog


def log_event(user_id, event_type, message, ticker=None, severity="INFO", socketio=None):
    entry = AuditLog(user_id=user_id, event_type=event_type, message=message,
                      ticker=ticker, severity=severity)
    db.session.add(entry)
    db.session.commit()

    if socketio:
        socketio.emit("notification", entry.to_dict())
    return entry

"""
utils.py
--------
Small shared helper functions used across routes/auth.
"""

from app.extensions import db
from app.models import ActivityLog


def log_activity(user_id: int, action: str, details: str = "") -> None:
    """Records a user action for the Activity Log / audit trail."""
    entry = ActivityLog(user_id=user_id, action=action, details=details)
    db.session.add(entry)
    db.session.commit()


def parse_tags(raw: str):
    """Turns a comma-separated string into a clean list of tag names."""
    if not raw:
        return []
    return [t.strip() for t in raw.split(",") if t.strip()]

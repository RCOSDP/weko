from flask import current_app
from werkzeug.local import LocalProxy

from weko_logging.models import UserActivityLog

_logger = LocalProxy(lambda: current_app.extensions["weko-logging-activity"])

class UserActivityLogger:
    """User activity logger."""

    def __init__(self, app):
        """Initialize user logger."""
        self.app = app

    @classmethod
    def error(cls, operation=None, parent_id=None, target_key=None, remarks=None):
        """Log error."""
        _logger.error("update author db", extra={
            "parent_id": parent_id,
            "operation": operation,
            "target_key": target_key
        })

    @classmethod
    def info(cls, operation=None, parent_id=None, target_key=None, remarks=None):
        """Log info."""
        _logger.info("update author db", extra={
            "parent_id": parent_id,
            "operation": operation,
            "target_key": target_key
        })

    @classmethod
    def get_next_parent_id(session):
        """Get next parent id."""
        return UserActivityLog.get_sequence(session)
from datetime import datetime
import logging
from flask import request, current_app
from flask_security import current_user

from invenio_accounts.models import User
from invenio_db import db
from weko_logging.models import UserActivityLog

class UserActivityLogHandler(logging.Handler):
    """Logging handler for audit logs."""

    def __init__(self, app):
        super(UserActivityLogHandler, self).__init__()
        self.app = app

    def emit(self, record):
        """Emit a log record."""
        # if not has operation, skip create record
        if not hasattr(record, "operation"):
            return

        # create record if error level is error or info
        if record.levelname not in ["ERROR", "INFO"]:
            return

        operation = record.operation
        # get operation_type_id, operation_id, target from config "WEKO_LOGGING_OPERATION_MASTER"
        operation_type_id, operation_id, target = self._get_target_from_operation_id(operation)

        # get log group uuid
        parent_id = None
        if hasattr(record, "parend_id"):
            parent_id = record.parent_id or None

        # get user_id from current_user
        user_id = None
        eppn = None
        if current_user.is_authenticated and hasattr(current_user, "id"):
            user_id = current_user.id
            user = User.query.filter_by(id=user_id).first()
            # get eppn from user
            if user is not None:
                shib_users = list(user.shib_weko_user)
                if shib_users is not None and len(shib_users) == 1:
                    shib_user = shib_users[0]
                    eppn = shib_user.shib_eppn

        # get source, ip_address and client_id from request
        ip_address = request.remote_addr
        if request.headers.getlist("X-Forwarded-For"):
            ip_address = request.headers.getlist("X-Forwarded-For")[0]
        source = request.path

        # get client id from request oauth
        client_id = None
        if hasattr(request, "oauth") and request.oauth:
            client_id = request.oauth.client.client_id

        # get other values from record
        target_key = None
        if target is not None:
            target_key = record.target_key if hasattr(record, "target_key") else None
        remarks = record.remarks if hasattr(record, "remarks") else None

        # get repositoy path from request
        # TODO: get repository_path from request
        repository_path = "/"
        if hasattr(request, "repository_path"):
            repository_path = request.repository_path

        timestamp_seconds = record.created
        created_dt = datetime.fromtimestamp(timestamp_seconds)

        user_activity_log = UserActivityLog(
            user_id=user_id,
            log={},
            repository_path=repository_path,
            remarks=remarks,
        )
        log = {
            "id": None,
            "log_level": record.levelname,
            "date": created_dt.strftime("%Y/%m/%d %H:%M:%S.%f"),
            "user_id": user_id,
            "eppn": eppn,
            "ip_address": ip_address,
            "client_id": client_id,
            "repository_path": repository_path,
            "source": source,
            "parent_id": parent_id,
            "operation_type_id": operation_type_id,
            "operation_id": operation_id,
            "target": target,
            "target_key": target_key,
        }

        try:
            with db.session.begin_nested():
                db.session.add(user_activity_log)
                db.session.flush()
                log["id"] = user_activity_log.id
                user_activity_log.log = log
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to create user activity log: {e}")
            current_app.logger.error(e.__traceback__)
            raise

    def _get_target_from_operation_id(self, operation):
        # get target from config "WEKO_LOGGING_OPERATION_MASTER"
        operation_master = self.app.config.get("WEKO_LOGGING_OPERATION_MASTER", {})
        for operation_category in operation_master.values():
            if operation not in operation_category.get("operation", {}).keys():
                continue

            operation_info = operation_category["operation"][operation]
            operation_type_id = operation_category.get("id")
            operation_id = operation_info.get("id")
            target = operation_info.get("target")
            return (operation_type_id, operation_id, target)
        return (None, None, None)


from datetime import datetime
import logging
from flask import request, current_app
from flask_security import current_user

from invenio_accounts.models import User
from invenio_db import db
from weko_logging.models import UserActivityLog

class AuditLogHandler(logging.Handler):
    """Logging handler for audit logs."""
    
    def init_app(self, app):
        """
        Flask application initialization.

        :param app: The flask application.
        """
        self.init_config(app)
        if app.config["WEKO_LOGGING_FS_LOGFILE"] is None:
            return
        self.install_handler(app)
        app.extensions["weko-logging-fs"] = self

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
        operation_type_id, operation_id, target = self._get_target_from_operation(operation)
        
        # get user_id from current_user
        user_id = None
        eppn = None
        if current_user.is_authenticated and hasattr(current_user, "id"):
            user_id = current_user.id
            user = User.query.filter_by(id=user_id).first()
            # get eppn from user
            if user is not None:
                shib_user = user.shib_weko_user
                if shib_user is not None:
                    eppn = shib_user.shib_eppn

        # get source, ip_address and client_id from request
        ip_address = request.remote_addr
        if request.headers.getlist("X-Forwarded-For"):
            ip_address = request.headers.getlist("X-Forwarded-For")[0]
        
        source = request.headers.get("User-Agent")
        client_id = request.headers.get("Client-ID")

        # get other values from record
        target_key = None
        if target is not None:
            target_key = record.target_key if hasattr(record, "target_key") else None
        remarks = record.remarks if hasattr(record, "remarks") else None

        log = {
            "id": record.id,
            "log_level": record.levelname,
            "date": datetime.now().strftime("%Y/%m/%d %H:%M:%S.%f"),
            "user_id": user_id,
            "eppn": eppn,
            "ip_address": ip_address,
            "client_id": client_id,
            "repository_path": record.repository_path,
            "source": source,
            "parent_id": record.parent_id,
            "operation_type_id": operation_type_id,
            "operation_id": operation_id,
            "target": target,
            "target_key": target_key,
        }
        db.session.add(
            UserActivityLog(
                user_id=record.user_id,
                repository_path=record.repository_path,
                log=log,
                remarks=remarks,
            )
        )
        db.session.commit()

    def _get_target_from_operation_id(self, operation):
        # get target from config "WEKO_LOGGING_OPERATION_MASTER"
        operation_master = current_app.config.get("WEKO_LOGGING_OPERATION_MASTER", {})
        for operation_category in operation_master.values():
            if operation not in operation_category.get("operation", {}).keys():
                continue

            operation_info = operation_category["operation"][operation]
            operation_type_id = operation_category.get("id")
            operation_id = operation_info.get("id")
            target = operation_info.get("target")
            return (operation_type_id, operation_id, target)
        return (None, None, None)


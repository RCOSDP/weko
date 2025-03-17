from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from flask import current_app

from invenio_db import db
from weko_logging.models import UserActivityLog

class UserActivityLogUtils:
    """Utility for user activity (audit) log."""

    @staticmethod  
    def delete_log():
        """Delete logs."""
        # get config from current_app
        config = current_app.config.get("WEKO_LOGGING_USER_ACTIVITY_SETTING")
        if config is None:
            raise Exception("WEKO_LOGGING_USER_ACTIVITY_SETTING is not set.")

        when = config.get("delete").get("when")
        interval = config.get("delete").get("interval")
        if when is None or interval is None:
            raise Exception("WEKO_LOGGING_USER_ACTIVITY_SETTING.delete.when or interval is not set.")
        
        # set date according to when and interval
        deletion_date_to = None
        if when == "days":
            deletion_date_to = datetime.now() - timedelta(days=interval)
        elif when == "weeks":
            deletion_date_to = datetime.now() - timedelta(weeks=interval)
        elif when == "months":
            deletion_date_to = datetime.now() - relativedelta(months=interval)
        elif when == "years":
            deletion_date_to = datetime.now() - relativedelta(years=interval)
        else:
            raise Exception("WEKO_LOGGING_USER_ACTIVITY_SETTING.delete.when is invalid.")
        
        UserActivityLog.query.filter(UserActivityLog.date < deletion_date_to).delete()
        db.session.commit()

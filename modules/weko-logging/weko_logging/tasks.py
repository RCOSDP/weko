

"""Tasks for the WEKO logging module."""

from celery import shared_task
from flask import current_app

from .utils import UserActivityLogUtils

@shared_task(ignore_results=True)
def delete_log():
    """Delete logs."""
    with current_app.app_context():
        UserActivityLogUtils.delete_log()
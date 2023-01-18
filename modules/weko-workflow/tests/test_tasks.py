# .tox/c1/bin/pytest --cov=weko_workflow tests/test_tasks.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp

from weko_workflow.tasks import cancel_expired_usage_report_activities
from sqlalchemy.exc import OperationalError
import pytest

# def cancel_expired_usage_report_activities():
def test_cancel_expired_usage_report_activities(app,db_guestactivity):
    with app.test_request_context():
        with pytest.raises(OperationalError):
            cancel_expired_usage_report_activities()
    

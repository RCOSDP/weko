# .tox/c1/bin/pytest --cov=weko_workflow tests/test_tasks.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp

from weko_workflow.tasks import cancel_expired_usage_report_activities
from weko_workflow.models import Activity, ActivityStatusPolicy
import pytest

# def cancel_expired_usage_report_activities():
def test_cancel_expired_usage_report_activities(app,db_guestactivity):
    res1 = Activity.query.filter(Activity.activity_id=="1").one()
    res2 = Activity.query.filter(Activity.activity_id=="2").one()
    assert res1.activity_status == ActivityStatusPolicy.ACTIVITY_BEGIN
    assert res2.activity_status == ActivityStatusPolicy.ACTIVITY_BEGIN
    with app.test_request_context():
        cancel_expired_usage_report_activities()
    res1 = Activity.query.filter(Activity.activity_id=="1").one()
    res2 = Activity.query.filter(Activity.activity_id=="2").one()
    assert res1.activity_status == ActivityStatusPolicy.ACTIVITY_BEGIN
    assert res2.activity_status == ActivityStatusPolicy.ACTIVITY_CANCEL
    

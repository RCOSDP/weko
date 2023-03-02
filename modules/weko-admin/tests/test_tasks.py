
import os
from datetime import datetime, timedelta
from flask import current_app

from weko_admin.models import AdminSettings
from weko_admin.tasks import (
    send_all_reports,
    check_send_all_reports,
    send_feedback_mail,
    _due_to_run,
    check_send_site_access_report,
    clean_temp_info
)

# .tox/c1/bin/pytest --cov=weko_admin tests/test_tasks.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp

# def send_all_reports(report_type=None, year=None, month=None):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_tasks.py::test_send_all_reports -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_send_all_reports(app, users, statistic_email_addrs,mocker):
    current_app.config.update(
        WEKO_ADMIN_REPORT_EMAIL_TEMPLATE='weko_admin/email_templates/report.html'
    )
    class MockZip():
        def getvalue(self):
            return "test_value"
    now = datetime.now()
    subject = "{} Log report.".format(now.strftime("%Y-%m"))
    target_email=[email.email_address for email in statistic_email_addrs]
    mocker.patch("weko_admin.tasks.package_reports", return_value=MockZip())
    mocker.patch("weko_admin.tasks.render_template",return_value="test_html")

    # report_type is None
    mock_mail = mocker.patch("weko_admin.tasks.send_mail")
    send_all_reports()
    args, kwargs = mock_mail.call_args
    assert args == (subject, target_email)
    assert kwargs["html"] == "test_html"
    
    # report_type is not None
    mock_mail = mocker.patch("weko_admin.tasks.send_mail")
    send_all_reports("fiile_download")
    args, kwargs = mock_mail.call_args
    assert args == (subject, target_email)
    assert kwargs["html"] == "test_html"
    
    # raise Exception
    mock_mail = mocker.patch("weko_admin.tasks.send_mail", side_effect=Exception("test_error"))
    send_all_reports("file_download")
    args, kwargs = mock_mail.call_args
    assert args == (subject, target_email)
    assert kwargs["html"] == "test_html"
    
# def check_send_all_reports():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_tasks.py::test_check_send_all_reports -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_check_send_all_reports(app, admin_settings, mocker):
    mock_send = mocker.patch("weko_admin.tasks.send_all_reports.delay")
    check_send_all_reports()
    mock_send.assert_not_called()
    
    AdminSettings.update("report_email_schedule_settings", {"details":"","enabled":True,"frequency":"daily"})
    mock_send = mocker.patch("weko_admin.tasks.send_all_reports.delay")
    check_send_all_reports()
    mock_send.assert_called()
    

# def send_feedback_mail():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_tasks.py::test_send_feedback_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_send_feedback_mail(app, mocker):
    mock_send = mocker.patch("weko_admin.tasks.StatisticMail.send_mail_to_all")
    send_feedback_mail()
    mock_send.assert_called()
    

# def _due_to_run(schedule):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_tasks.py::test_due_to_run -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_due_to_run():
    schedule = {"details":"","enabled":False,"frequency":"daily"}
    result = _due_to_run(schedule)
    assert result == False
    
    schedule = {"details":"","enabled":True,"frequency":"daily"}
    result = _due_to_run(schedule)
    assert result == True

# def check_send_site_access_report():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_tasks.py::test_check_send_site_access_report -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_check_send_site_access_report(client, admin_settings, mocker):

    # site_license_mail_setting.auto_send_flag is False
    check_send_site_access_report()
    
    # site_license_mail_setting.auto_send_flag is True
    AdminSettings.update("site_license_mail_settings", {"auto_send_flag": True})
    mock_send = mocker.patch("weko_admin.tasks.manual_send_site_license_mail")
    check_send_site_access_report()
    mock_send.assert_called()
    
# def clean_temp_info():
# .tox/c1/bin/pytest --cov=weko_admin tests/test_tasks.py::test_clean_temp_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_clean_temp_info(instance_path, mocker):
    #/tmp
    dir_not_expire = os.path.join(instance_path,"not_expire")
    dir_expire_after_now = os.path.join(instance_path,"expire_after_now")
    dir_expire_before_now = os.path.join(instance_path,"expire_before_now")
    os.makedirs(dir_not_expire, exist_ok=True)
    os.makedirs(dir_expire_after_now, exist_ok=True)
    os.makedirs(dir_expire_before_now, exist_ok=True)
    data = {"test_key":{
        "/not_exist_path": {},# not exist path
        dir_not_expire: {},
        dir_expire_after_now: {"expire":(datetime.now()+timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")},
        dir_expire_before_now: {"expire":(datetime.now()+timedelta(days=-10)).strftime("%Y-%m-%d %H:%M:%S")}
    }}
    class MockTempDirInfo():
        def __init__(self):
            self.key = "test_key"
            self.data = data
        def get_all(self):
            result = {}
            for idx, val in self.data.get(self.key).items():
                path = idx
                result[path] = val
            return result
        def delete(self, path):
            self.data[self.key].pop(path)
    mock_temp_dir_info = MockTempDirInfo()
    mocker.patch("weko_admin.tasks.TempDirInfo", return_value=mock_temp_dir_info)
    clean_temp_info()
    result = mock_temp_dir_info.get_all()
    assert list(result.keys()) == [dir_not_expire, dir_expire_after_now]
    assert os.path.exists(dir_expire_before_now) is False
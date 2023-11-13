import pytest
import datetime
from mock import patch, MagicMock


from weko_records_ui.models import InstitutionName, FilePermission, FileOnetimeDownload


institution_name = InstitutionName(
    name="test"
)

file_permission = FilePermission(
    user_id=1,
    record_id=99,
    file_name="test",
    usage_application_activity_id="test",
    usage_report_activity_id="test",
    status=-1
)

file_one_time_download = FileOnetimeDownload(
    file_name="test",
    user_mail="test@test",
    record_id=99,
    download_count=1,
    expiration_date=99,
)


# InstitutionName
def test_InstitutionName_set_institution_name(app):
    # Exception coverage
    institution_name.set_institution_name("test")


# FilePermission
def test_FilePermission_set_institution_name(app, db):
    db.session.add(file_permission)
    db.session.commit()

    file_permission.find(
        user_id=file_permission.id,
        record_id=file_permission.record_id,
        file_name=file_permission.file_name
    )


def test_FilePermission_init_file_permission(app, db):
    db.session.add(file_permission)
    db.session.commit()

    file_permission.init_file_permission(
        user_id=file_permission.id,
        record_id=file_permission.record_id,
        file_name=file_permission.file_name,
        activity_id=file_permission.usage_application_activity_id
    )


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_models.py::test_FilePermission_update_status -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_FilePermission_update_status(app, db):
    db.session.add(file_permission)
    db.session.commit()

    f = db.session.query(FilePermission).first()
    assert f.status == -1
    file_permission.update_status(
        permission=f,
        status=1
    )
    db.session.commit()
    f = db.session.query(FilePermission).first()
    assert f.status == 1


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_models.py::test_FilePermission_update_open_date -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_FilePermission_update_open_date(app, db):
    db.session.add(file_permission)
    db.session.commit()

    f = db.session.query(FilePermission).first()
    file_permission.update_open_date(
        permission=f,
        open_date=datetime.datetime(2022, 12, 31)
    )
    db.session.commit()
    f = db.session.query(FilePermission).first()
    assert f.open_date == datetime.datetime(2022, 12, 31)


def test_FilePermission_find_by_activity(app, db):
    db.session.add(file_permission)
    db.session.commit()

    file_permission.find_by_activity(
        activity_id=file_permission.usage_application_activity_id
    )


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_models.py::test_FilePermission_update_usage_report_activity_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_FilePermission_update_usage_report_activity_id(app, db):
    db.session.add(file_permission)
    db.session.commit()

    f = db.session.query(FilePermission).first()
    assert f.usage_application_activity_id == "test"
    file_permission.update_usage_report_activity_id(
        permission=f,
        activity_id='test2'
    )
    db.session.commit()
    f = db.session.query(FilePermission).first()
    assert f.usage_report_activity_id == "test2"


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_models.py::test_FilePermission_delete_object -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_FilePermission_delete_object(app, db):
    db.session.add(file_permission)
    db.session.commit()

    assert db.session.query(FilePermission).count() == 1
    file_permission.delete_object(
        permission=file_permission
    )
    assert db.session.query(FilePermission).count() == 0


def test_FileOnetimeDownload_update_download(app, db):
    db.session.add(file_one_time_download)
    db.session.add(file_permission)
    db.session.commit()

    data1 = {
        "file_name": file_one_time_download.file_name,
        "user_mail": file_one_time_download.user_mail,
        "record_id": file_one_time_download.record_id,
    }

    file_one_time_download.update_download(
        data=data1
    )

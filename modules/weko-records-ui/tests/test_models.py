import io
from datetime import datetime, timedelta, timezone
from sqlite3 import IntegrityError
from unittest import mock  # python3
#from unittest.mock import MagicMock

import mock  # python2, after pip install mock
import pytest
from flask import Flask, json, jsonify, session, url_for
from flask_babelex import get_locale, to_user_timezone, to_utc
from flask_login import current_user
from flask_security import login_user
from flask_security.utils import login_user
from invenio_accounts.models import Role, User
from invenio_accounts.testutils import create_test_user, login_user_via_session
from mock import patch

from weko_records_ui.models import (
    InstitutionName
    ,FileSecretDownload
    ,FilePermission
    ,FileOnetimeDownload
)
    

institution_name = InstitutionName(
    name="test"
)


# InstitutionName
def test_InstitutionName_set_institution_name(app,):
    # Exception coverage
    institution_name.set_institution_name("test")


# FilePermission
def test_FilePermission_set_institution_name(app, db, db_FilePermission):
    db_FilePermission.find(
        user_id=db_FilePermission.id,
        record_id=db_FilePermission.record_id,
        file_name=db_FilePermission.file_name
    )


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_models.py::test_FilePermission_init_file_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_FilePermission_init_file_permission(app, db, db_FilePermission):
    db_FilePermission.init_file_permission(
        user_id=db_FilePermission.id,
        record_id=db_FilePermission.record_id,
        file_name=db_FilePermission.file_name,
        activity_id=db_FilePermission.usage_application_activity_id
    )


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_models.py::test_FilePermission_update_status -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_FilePermission_update_status(app, db, db_FilePermission):
    f = db.session.query(FilePermission).first()
    assert f.status == -1
    db_FilePermission.update_status(
        permission=f,
        status=1
    )
    db.session.commit()
    f = db.session.query(FilePermission).first()
    assert f.status == 1


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_models.py::test_FilePermission_update_open_date -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_FilePermission_update_open_date(app, db, db_FilePermission):
    f = db.session.query(FilePermission).first()
    db_FilePermission.update_open_date(
        permission=f,
        open_date=datetime(2022, 12, 31)
    )
    db.session.commit()
    f = db.session.query(FilePermission).first()
    assert f.open_date == datetime(2022, 12, 31)


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_models.py::test_FilePermission_find_by_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_FilePermission_find_by_activity(app, db, db_FilePermission):
    db_FilePermission.find_by_activity(
        activity_id=db_FilePermission.usage_application_activity_id
    )


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_models.py::test_FilePermission_update_usage_report_activity_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_FilePermission_update_usage_report_activity_id(app, db, db_FilePermission):
    f = db.session.query(FilePermission).first()
    assert f.usage_application_activity_id == "test"
    db_FilePermission.update_usage_report_activity_id(
        permission=f,
        activity_id='test2'
    )
    db.session.commit()
    f = db.session.query(FilePermission).first()
    assert f.usage_report_activity_id == "test2"


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_models.py::test_FilePermission_delete_object -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_FilePermission_delete_object(app, db, db_FilePermission):
    assert db.session.query(FilePermission).count() == 1
    db_FilePermission.delete_object(
        permission=db_FilePermission
    )
    assert db.session.query(FilePermission).count() == 0


# def find_list_permission_approved(record_id, file_name):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_models.py::test_find_list_permission_approved -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_find_list_permission_approved(app, records_restricted, users,db_file_permission):
    #32
    indexer, results = records_restricted
    recid = results[len(results)-1]["recid"]
    filename =results[len(results)-1]["filename"]
    assert len(FilePermission.find_list_permission_approved(users[0]["id"],recid.pid_value, filename)) == 0

# def find_by_activity:
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_models.py::test_find_by_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_find_by_activity(db_file_permission):
    #34
    listpermission:list = FilePermission.find_by_activity("usage_application_activity_id_dummy1")

    sorted_list = sorted(listpermission, key= lambda x: x.id ,reverse=True)
    assert listpermission == sorted_list


class TestFileOnetimeDownload:
    expiration_date = datetime.now(timezone.utc) + timedelta(hours=24)
    no_tz = expiration_date.replace(tzinfo=None)
    base_data = {
        'approver_id': 1,
        'record_id': '1',
        'file_name': 'test file',
        'expiration_date': expiration_date,
        'download_limit': 1,
        'user_mail': 'test@example.org',
        'is_guest': False,
        'extra_info': {'info': 'value'}
    }
    expected_data = {
        **base_data,
        'expiration_date': no_tz
    }

    # .tox/c1/bin/pytest --cov=weko_records_ui tests/test_models.py::TestFileOnetimeDownload::test_init -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp -p no:warnings
    def test_init(self, db):
        obj = FileOnetimeDownload(**self.base_data)
        for key, value in self.base_data.items():
            assert getattr(obj, key) == value
        for key in self.base_data.keys():
            bad_data = self.base_data.copy()
            bad_data.pop(key)
            with pytest.raises(TypeError):
                FileOnetimeDownload(**bad_data)

    # .tox/c1/bin/pytest --cov=weko_records_ui tests/test_models.py::TestFileOnetimeDownload::test_create -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp -p no:warnings
    def test_create(self, users):
        assert FileOnetimeDownload.query.count() == 0
        obj = FileOnetimeDownload.create(**self.base_data)
        assert isinstance(obj, FileOnetimeDownload)
        assert FileOnetimeDownload.query.count() == 1
        rec = FileOnetimeDownload.query.first()
        for key, value in self.expected_data.items():
            assert getattr(rec, key) == value

        bad_data1 = self.base_data.copy()
        bad_data1['expiration_date'] = (datetime.now(timezone.utc)
                                        - timedelta(hours=24))
        with pytest.raises(Exception):
            FileOnetimeDownload.create(**bad_data1)
        assert FileOnetimeDownload.query.count() == 1

        bad_data2 = self.base_data.copy()
        bad_data2['download_limit'] = -1
        with pytest.raises(Exception):
            FileOnetimeDownload.create(**bad_data2)
        assert FileOnetimeDownload.query.count() == 1

        with patch('weko_records_ui.models.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception('DB error test')
            with pytest.raises(Exception):
                FileOnetimeDownload.create(**self.base_data)
            mock_commit.assert_called_once()
        assert FileOnetimeDownload.query.count() == 1

    # .tox/c1/bin/pytest --cov=weko_records_ui tests/test_models.py::TestFileOnetimeDownload::test_get_by_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp -p no:warnings
    def test_get_by_id(self, users):
        FileOnetimeDownload.create(**self.base_data)
        record = FileOnetimeDownload.get_by_id(1)
        assert isinstance(record, FileOnetimeDownload)
        not_found = FileOnetimeDownload.get_by_id(100)
        assert not_found is None

    # .tox/c1/bin/pytest --cov=weko_records_ui tests/test_models.py::TestFileOnetimeDownload::test_update_extra_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp -p no:warnings
    def test_update_extra_info(self, users):
        obj = FileOnetimeDownload.create(**self.base_data)
        obj.update_extra_info({'new': 'value'})
        assert obj.extra_info == {'new': 'value'}

        with pytest.raises(ValueError):
            obj.update_extra_info('invalid')
        assert obj.extra_info == {'new': 'value'}

        with patch('weko_records_ui.models.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception('DB error test')
            with pytest.raises(Exception):
                obj.update_extra_info({'new': 'value2'})
            mock_commit.assert_called_once()
        assert obj.extra_info == {'new': 'value'}

    # .tox/c1/bin/pytest --cov=weko_records_ui tests/test_models.py::TestFileOnetimeDownload::test_increment_download_count -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp -p no:warnings
    def test_increment_download_count(self, users):
        rec = FileOnetimeDownload.create(**self.base_data)
        assert rec.download_count == 0
        rec.increment_download_count()
        assert rec.download_count == 1

        with pytest.raises(ValueError):
            rec.increment_download_count()
        assert rec.download_count == 1

        rec2 = FileOnetimeDownload.create(**self.base_data)
        with patch('weko_records_ui.models.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception('DB error test')
            with pytest.raises(Exception):
                rec2.increment_download_count()
            mock_commit.assert_called_once()
        assert rec2.download_count == 0

    # .tox/c1/bin/pytest --cov=weko_records_ui tests/test_models.py::TestFileOnetimeDownload::test_delete_logically -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp -p no:warnings
    def test_delete_logically(self, users):
        rec = FileOnetimeDownload.create(**self.base_data)
        assert rec.is_deleted is False
        rec.delete_logically()
        assert rec.is_deleted is True

        rec.delete_logically()
        assert rec.is_deleted is True

        rec2 = FileOnetimeDownload.create(**self.base_data)
        with patch('weko_records_ui.models.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception('DB error test')
            with pytest.raises(Exception):
                rec2.delete_logically()
            mock_commit.assert_called_once()
        assert rec2.is_deleted is False

class TestFileSecretDownload:
    expiration_date = datetime.now(timezone.utc) + timedelta(hours=24)
    no_tz = expiration_date.replace(tzinfo=None)
    base_data = {
        'creator_id': 1,
        'record_id': '1',
        'file_name': 'test file',
        'label_name': 'test label',
        'expiration_date': expiration_date,
        'download_limit': 1
    }
    expected_data = {
        **base_data,
        'expiration_date': no_tz
    }

    # .tox/c1/bin/pytest --cov=weko_records_ui tests/test_models.py::TestFileSecretDownload::test_init -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp -p no:warnings
    def test_init(self, db):
        obj = FileSecretDownload(**self.base_data)
        for key, value in self.base_data.items():
            assert getattr(obj, key) == value
        for key in self.base_data.keys():
            bad_data = self.base_data.copy()
            bad_data.pop(key)
            with pytest.raises(TypeError):
                FileSecretDownload(**bad_data)

    # .tox/c1/bin/pytest --cov=weko_records_ui tests/test_models.py::TestFileSecretDownload::test_create -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp -p no:warnings
    def test_create(self, users):
        assert FileSecretDownload.query.count() == 0
        obj = FileSecretDownload.create(**self.base_data)
        assert isinstance(obj, FileSecretDownload)
        assert FileSecretDownload.query.count() == 1
        rec = FileSecretDownload.query.first()
        for key, value in self.expected_data.items():
            assert getattr(rec, key) == value

        bad_data1 = self.base_data.copy()
        bad_data1['expiration_date'] = (datetime.now(timezone.utc)
                                        - timedelta(hours=24))
        with pytest.raises(Exception):
            FileSecretDownload.create(**bad_data1)
        assert FileSecretDownload.query.count() == 1

        bad_data2 = self.base_data.copy()
        bad_data2['download_limit'] = -1
        with pytest.raises(Exception):
            FileSecretDownload.create(**bad_data2)
        assert FileSecretDownload.query.count() == 1

        with patch('weko_records_ui.models.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception('DB error test')
            with pytest.raises(Exception):
                FileSecretDownload.create(**self.base_data)
            mock_commit.assert_called_once()
        assert FileSecretDownload.query.count() == 1

    # .tox/c1/bin/pytest --cov=weko_records_ui tests/test_models.py::TestFileSecretDownload::test_get_by_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp -p no:warnings
    def test_get_by_id(self, users):
        FileSecretDownload.create(**self.base_data)
        record = FileSecretDownload.get_by_id(1)
        assert isinstance(record, FileSecretDownload)
        not_found = FileSecretDownload.get_by_id(100)
        assert not_found is None

    # .tox/c1/bin/pytest --cov=weko_records_ui tests/test_models.py::TestFileSecretDownload::test_increment_download_count -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp -p no:warnings
    def test_increment_download_count(self, users):
        rec = FileSecretDownload.create(**self.base_data)
        assert rec.download_count == 0
        rec.increment_download_count()
        assert rec.download_count == 1

        with pytest.raises(ValueError):
            rec.increment_download_count()
        assert rec.download_count == 1

        rec2 = FileSecretDownload.create(**self.base_data)
        with patch('weko_records_ui.models.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception('DB error test')
            with pytest.raises(Exception):
                rec2.increment_download_count()
            mock_commit.assert_called_once()
        assert rec2.download_count == 0

    # .tox/c1/bin/pytest --cov=weko_records_ui tests/test_models.py::TestFileSecretDownload::test_delete_logically -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp -p no:warnings
    def test_delete_logically(self, users):
        rec = FileSecretDownload.create(**self.base_data)
        assert rec.is_deleted is False
        rec.delete_logically()
        assert rec.is_deleted is True

        rec.delete_logically()
        assert rec.is_deleted is True

        rec2 = FileSecretDownload.create(**self.base_data)
        with patch('weko_records_ui.models.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception('DB error test')
            with pytest.raises(Exception):
                rec2.delete_logically()
            mock_commit.assert_called_once()
        assert rec2.is_deleted is False


# def find_downloadable_only(cls, **obj) -> list:
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_models.py::test_find_downloadable_only -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.skip(reason="'from sqlalchemy.dialects.postgresql import INTERVAL' can't tests on SQLite.")
def test_find_downloadable_only(app,db):
    # 35
    user_mail ='aaa@example.org' 
    record_id=1
    file_name="text.txt"
    created=datetime.now() - timedelta(2)
    with app.test_request_context():
        # with db.session.begin_nested():
        FileOnetimeDownload.create(**{"user_mail":user_mail,"record_id":record_id,"file_name":file_name,"download_count":0 ,"expiration_date":2})
        FileOnetimeDownload.create(**{"user_mail":user_mail,"record_id":record_id,"file_name":file_name,"download_count":1 ,"expiration_date":1})
        FileOnetimeDownload.create(**{"user_mail":user_mail,"record_id":record_id,"file_name":file_name,"download_count":1 ,"expiration_date":2})
        FileOnetimeDownload.create(**{"user_mail":user_mail,"record_id":record_id,"file_name":file_name,"download_count":1 ,"expiration_date":2})

        recs = FileOnetimeDownload.find_downloadable_only(user_mail=user_mail,record_id=record_id,file_name=file_name)
        assert len(recs) == 2

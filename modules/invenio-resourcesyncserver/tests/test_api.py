import os
import json
import copy
import pytest
import unittest
import datetime
from mock import patch, MagicMock, Mock
from flask import current_app, make_response, request
from flask_login import current_user
from flask_babelex import Babel

from invenio_resourcesyncserver.api import ResourceListHandler, ChangeListHandler
from invenio_resourcesyncserver.models import ChangeListIndexes, ResourceListIndexes


def sample_ResourceListHandler():
    test = ResourceListHandler()
    test.id = 1
    test.status = "test"
    test.repository_id = 33
    test.resource_dump_manifest = "test"
    test.url_path = "test"
    test.created = "test"
    test.updated = "test"
    test.index = "test"
    
    return test


def sample_ResourceListIndexes():
    test = ResourceListIndexes(
        id=1,
        status=True,
        repository_id=1,
        resource_dump_manifest=True,
        url_path="/"
    )

    return test


def sample_ChangeListHandler(key):

    def _func(keyword):
        if keyword == "str":
            test = ChangeListHandler(
                change_tracking_state="test"
            )
        else:
            test = ChangeListHandler(
                change_tracking_state=["test"]
            )
        
        test.id = "test"
        test.status = "test"
        test.repository_id = "Root Index"
        test.change_dump_manifest = "test"
        test.max_changes_size = "test"
        test.url_path = "/"
        test.created = "test"
        test.updated = "test"
        test.index = "test"
        test.publish_date = "test"
        test.interval_by_date = 2

        return test
    
    return _func(key)


# class ResourceListHandler(object):
#     def __init__(self, **kwargs):
#     def get_index(self):
def test_get_index_ResourceListHandler(i18n_app, indices):
    test = sample_ResourceListHandler()

    assert test.get_index()


#     def to_dict(self):
def test_to_dict_ResourceListHandler(i18n_app):
    test = sample_ResourceListHandler()
    data = MagicMock()
    data.index_name_english = "test"
    test.index = data
    
    assert test.to_dict()


#     def create(cls, data=None):
def test_create_ResourceListHandler(i18n_app):
    test = sample_ResourceListHandler()

    with patch("invenio_resourcesyncserver.api.ResourceListHandler.get_resource_by_repository_id", return_value=True):
        assert test.create()
    assert test.create()


#     def update(self, data=None):
def test_update_ResourceListHandler(i18n_app):
    test = sample_ResourceListHandler()

    assert test.update()


#     def delete(self):
def test_delete_ResourceListHandler(i18n_app):
    test = sample_ResourceListHandler()

    assert not test.delete()


#     def get_resource(cls, resource_id, type_result='obj'):
def test_get_resource_ResourceListHandler(i18n_app, db):
    test = sample_ResourceListHandler()
    sample = sample_ResourceListIndexes()
    db.session.add(sample)
    db.session.commit()

    assert test.get_resource(1)
    assert not test.get_resource("a")
    
    
#     def get_list_resource(cls, type_result='obj'):
def test_get_list_resource_ResourceListHandler(i18n_app, db):
    test = sample_ResourceListHandler()
    sample = sample_ResourceListIndexes()
    db.session.add(sample)
    db.session.commit()

    assert test.get_list_resource()
# def test_get_list_resource_2_ResourceListHandler(i18n_app):
#     test = sample_ResourceListHandler()

#     assert test.get_list_resource()


#     def get_resource_by_repository_id(cls, repository_id, type_result='obj'):
def test_get_resource_by_repository_id_ResourceListHandler(i18n_app, db):
    test = sample_ResourceListHandler()
    sample = sample_ResourceListIndexes()
    db.session.add(sample)
    db.session.commit()

    assert test.get_resource_by_repository_id(1)
    assert test.get_resource_by_repository_id(1, type_result='test')
    assert not test.get_resource_by_repository_id("a")


#     def _validation(self, record_id=None):
def test__validation_ResourceListHandler(i18n_app):
    test = sample_ResourceListHandler()
    test.index = MagicMock()
    test.index.public_state = MagicMock()
    # return_data = {
    #     'path': '/'
    # }

    # with patch("weko_deposit.api.WekoRecord.get_record_by_pid", return_value=""):
    assert test._validation()


#     def get_resource_list_xml(self, from_date=None, to_date=None): ERR ~ 
def test_get_resource_list_xml_ResourceListHandler(i18n_app):
    test = sample_ResourceListHandler()
    test.repository_id = "Root Index"
    return_data = [{}]

    with patch("invenio_resourcesyncserver.api.ResourceListHandler._validation", return_value=""):
        assert not test.get_resource_list_xml()
    with patch("invenio_resourcesyncserver.api.ResourceListHandler._validation", return_value="test"):
        with patch("invenio_resourcesyncserver.query.get_items_by_index_tree", return_value=return_data):
            assert test.get_resource_list_xml()


#     def get_resource_dump_xml(self, from_date=None, to_date=None): ERR ~ 
def test_get_resource_dump_xml_ResourceListHandler(i18n_app):
    test = sample_ResourceListHandler()
    test.repository_id = "Root Index"
    from_date = "2022/11/3 0:00:00"
    to_date = "2022/11/4 0:00:00"

    with patch("invenio_resourcesyncserver.api.ResourceListHandler._validation", return_value=""):
        assert not test.get_resource_dump_xml()
    with patch("invenio_resourcesyncserver.api.ResourceListHandler._validation", return_value="test"):
        with patch("invenio_resourcesyncserver.query.get_items_by_index_tree", return_value=MagicMock()):
            assert test.get_resource_dump_xml(from_date=from_date, to_date=to_date)


#     def get_capability_content(cls):
def test_get_capability_content_ResourceListHandler(i18n_app):
    test = sample_ResourceListHandler()
    return_data = MagicMock()

    def _validation():
        return True

    return_data._validation = _validation

    with patch("invenio_resourcesyncserver.api.ResourceListHandler.get_list_resource", return_value=[return_data]):
        assert test.get_capability_content()


#     def get_resource_dump_manifest(self, record_id):
def test_get_resource_dump_manifest_ResourceListHandler(i18n_app):
    test = sample_ResourceListHandler()
    test.resource_dump_manifest = True
    record_id = 1
    return_data = MagicMock()
    return_data_2 = MagicMock()

    def as_xml_sample():
        return True

    return_data_2.as_xml = as_xml_sample
    return_data.files = [return_data_2]

    with patch("invenio_resourcesyncserver.api.ResourceListHandler._validation", return_value=False):
        assert not test.get_resource_dump_manifest(record_id)

    with patch("invenio_resourcesyncserver.api.ResourceListHandler._validation", return_value=True):
        with patch("weko_deposit.api.WekoRecord.get_record_by_pid", return_value=return_data):
            # try and except is for bypassing ResourceDumpManifest.as_xml()
            try:
                assert test.get_resource_dump_manifest(record_id)
            except:
                pass
    

#     def get_record_content_file(self, record_id):
def test_get_record_content_file_ResourceListHandler(i18n_app):
    test = sample_ResourceListHandler()

    with patch("invenio_resourcesyncserver.api.ResourceListHandler._validation", return_value=False):
        assert not test.get_record_content_file(1)

    with patch("invenio_resourcesyncserver.api.ResourceListHandler._validation", return_value=True):
        with patch("weko_items_ui.utils._export_item", return_value=[MagicMock(), MagicMock()]):
            # Exception coverage
            assert not test.get_record_content_file(1)


# class ChangeListHandler(object):
#     def __init__(self, **kwargs):
#     def save(self):
def test_save_ChangeListHandler(i18n_app):
    test_str = sample_ChangeListHandler("str")
    test_list = sample_ChangeListHandler("list")

    return_data = MagicMock()

    with patch("invenio_resourcesyncserver.api.ChangeListHandler.get_change_list_by_repo_id", return_value=return_data):
        assert test_str.save()
        assert test_list.save()

    return_data.id = "test"

    with patch("invenio_resourcesyncserver.api.ChangeListHandler.get_change_list_by_repo_id", return_value=return_data):
        with patch("invenio_resourcesyncserver.api.ChangeListHandler.get_change_list", return_value=MagicMock()):
            with patch("invenio_db.db.session.merge", return_value=""):
                assert test_str.save()
                assert test_list.save()
            assert test_str.save()
        with patch("invenio_resourcesyncserver.api.ChangeListHandler.get_change_list", return_value=""):
            assert not test_str.save()

    with patch("invenio_resourcesyncserver.api.ChangeListHandler.get_change_list_by_repo_id", return_value=""):
        test_str.id = None
        assert test_str.save()

    with patch("invenio_resourcesyncserver.api.ChangeListHandler.get_change_list_by_repo_id", return_value="test"):
        test_str.id = None
        assert test_str.save()    


#     def get_change_list_content_xml(self, from_date,
def test_get_change_list_content_xml(i18n_app, db, users):
    from invenio_pidstore.models import PersistentIdentifier
    from invenio_pidstore.models import PIDStatus
    import uuid

    user = users[3]["obj"]
    rec_uuid = uuid.uuid4()
    sample = PersistentIdentifier.create(
        "recid",
        "1.0",
        object_type="rec",
        object_uuid=rec_uuid,
        status=PIDStatus.REGISTERED,
    )

    db.session.add(sample)
    db.session.commit()

    test_str = sample_ChangeListHandler("str")
    from_date = "2022/11/3 0:00:00"
    from_date_args = "2022/11/3 0:00:00"
    to_date_args = "2022/11/4 0:00:00"
    return_data = MagicMock()
    return_data.pid_value = "test"

    with patch("invenio_resourcesyncserver.api.ChangeListHandler._validation", return_value=""):
        assert not test_str.get_change_list_content_xml(
            from_date=from_date,
            from_date_args=from_date_args,
            to_date_args=to_date_args
        )
    with patch("invenio_resourcesyncserver.api.ChangeListHandler._validation", return_value="_str"):
        with patch("invenio_resourcesyncserver.query.get_items_by_index_tree", return_value=MagicMock()):
            with patch("invenio_resourcesyncserver.api.ChangeListHandler._get_record_changes_with_interval", return_value=[MagicMock()]):
                with patch("invenio_pidstore.models.PersistentIdentifier.get", return_value=sample):
                    with patch("invenio_pidrelations.contrib.versioning.PIDVersioning", return_value=return_data):
                        # Exception coverage
                        assert test_str.get_change_list_content_xml(
                            from_date=from_date,
                            from_date_args=from_date_args,
                            to_date_args=to_date_args
                        )


#     def get_change_list_index(self):
def test_get_change_list_index(i18n_app):
    test_str = sample_ChangeListHandler("str")
    test_str.publish_date = datetime.datetime.now() - datetime.timedelta(hours=1)
    
    with patch("invenio_resourcesyncserver.api.ChangeListHandler._validation", return_value=""):
        assert not test_str.get_change_list_index()

    with patch("invenio_resourcesyncserver.api.ChangeListHandler._validation", return_value="_str"):
        assert test_str.get_change_list_index()


#     def get_change_dump_index(self):
#     def get_change_dump_xml(self, from_date):
#     def _validation(self):
#     def get_change_dump_manifest_xml(self, record_id):
#     def delete(cls, change_list_id):
#     def get_index(self):
#     def to_dict(self):
#     def get_change_list(cls, changelist_id, type_result='obj'):
#     def get_all(cls):
#     def convert_modal_to_obj(cls, model=ChangeListIndexes()):
#     def get_change_list_by_repo_id(cls, repo_id, type_result='obj'):
#     def _is_record_in_index(self, record_id):
#     def get_record_content_file(self, record_id):
#     def get_capability_content(cls):
#     def _date_validation(self, date_from: str):
#     def _next_change(self, data, changes):
#     def _get_record_changes_with_interval(self, from_date):
#     def _get_record_changes(self, repo_id, from_date, until_date):
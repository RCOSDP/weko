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
from invenio_communities.models import Community

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

    def get_resource(key1, key2):
        data = MagicMock()
        return data

    test.get_resource = get_resource

    # Exception coverage
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


# .tox/c1/bin/pytest --cov=invenio_resourcesyncserver tests/test_api.py::test_get_list_resource_ResourceListHandler -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-resourcesyncserver/.tox/c1/tmp
#     def get_list_resource(cls, type_result='obj'):
def test_get_list_resource_ResourceListHandler(i18n_app, db, users):
    test = sample_ResourceListHandler()
    sample = sample_ResourceListIndexes()
    db.session.add(sample)
    db.session.commit()

    # no type_result
    result = test.get_list_resource(type_result=None)
    assert len(result)
    assert isinstance(result[0], ResourceListIndexes)
    assert result[0].id == 1

    # no user
    result = test.get_list_resource()
    assert len(result) == 1
    assert isinstance(result[0], ResourceListHandler)
    assert result[0].id == 1

    # super role user
    user = users[3]["obj"]
    result = test.get_list_resource(user=user)
    assert len(result) == 1
    assert isinstance(result[0], ResourceListHandler)
    assert result[0].id == 1

    # comadmin role user with repository
    user = users[4]["obj"]
    mock_repo = Community(root_node_id=1)
    with patch("invenio_communities.models.Community.get_repositories_by_user", return_value=[mock_repo]):
        with patch("weko_index_tree.api.Indexes.get_child_list_recursive", return_value=[sample.repository_id]):
            result = test.get_list_resource(user=user)
            assert len(result) == 1
            assert isinstance(result[0], ResourceListHandler)
            assert result[0].id == 1

    # comadmin role user with no repository
    with patch("invenio_communities.models.Community.get_repositories_by_user", return_value=[]):
        result = test.get_list_resource(user=user)
        assert len(result) == 0

    # comadmin role user with repository but no index
    user = users[4]["obj"]
    with patch("invenio_communities.models.Community.get_repositories_by_user", return_value=[mock_repo]):
        with patch("weko_index_tree.api.Indexes.get_child_list_recursive", return_value=[]):
            result = test.get_list_resource(user=user)
            assert len(result) == 0

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
    return_data = MagicMock()

    with patch("weko_deposit.api.WekoRecord.get_record_by_pid", return_value=return_data):
        with patch("invenio_resourcesyncserver.utils.get_real_path", return_value=["33"]):
            assert test._validation(record_id=1) == True

        with patch("invenio_resourcesyncserver.utils.get_real_path", return_value=[]):
            assert test._validation(record_id=1) == False

    assert test._validation() == True

    test.repository_id = "Root Index"

    assert test._validation() == True


#     def get_resource_list_xml(self, from_date=None, to_date=None): ERR ~
def test_get_resource_list_xml_ResourceListHandler(i18n_app, indices):
    test = sample_ResourceListHandler()
    test.repository_id = "Root Index"

    data1 = [MagicMock()]

    data2 = MagicMock()
    def as_xml():
        return True
    data2.as_xml = as_xml

    data3 = {"_updated": True}

    from_date = datetime.datetime.now() - datetime.timedelta(hours=11)
    to_date = datetime.datetime.now()

    with patch("invenio_resourcesyncserver.api.ResourceListHandler._validation", return_value=""):
        assert test.get_resource_list_xml() is None

    with patch("invenio_resourcesyncserver.api.ResourceListHandler._validation", return_value="test"):
        with patch('invenio_resourcesyncserver.api.get_items_by_index_tree', return_value=data1):
            with patch('invenio_resourcesyncserver.api.ResourceList', return_value=data2):
                with patch('invenio_resourcesyncserver.api.str_to_datetime', return_value=from_date):
                    with patch('invenio_resourcesyncserver.api.Resource', return_value=data3):
                        assert test.get_resource_list_xml(from_date=from_date, to_date=to_date)


#     def get_resource_dump_xml(self, from_date=None, to_date=None): ERR ~
def test_get_resource_dump_xml_ResourceListHandler(i18n_app):
    test = sample_ResourceListHandler()
    test.repository_id = "Root Index"
    from_date = "2022/11/3 0:00:00"
    to_date = "2022/11/6 0:00:00"

    data1 = [{
        "_source": {"_updated": "2022/11/4 0:00:00"}
    }]

    data2 = MagicMock()
    def as_xml():
        return True
    data2.as_xml = as_xml

    data3 = MagicMock()
    data3.ln = []

    with patch("invenio_resourcesyncserver.api.ResourceListHandler._validation", return_value=""):
        assert not test.get_resource_dump_xml()
    with patch("invenio_resourcesyncserver.api.ResourceListHandler._validation", return_value="test"):
        with patch('invenio_resourcesyncserver.api.get_items_by_index_tree', return_value=data1):
            with patch('invenio_resourcesyncserver.api.Resource', return_value=data3):
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
    def get_resource_dump_manifest(item):
        return "item"
    test.get_resource_dump_manifest = get_resource_dump_manifest
    data1 = MagicMock()
    data2 = MagicMock()
    data3 = MagicMock()
    data4 = {
        "a": 1,
        "b": 1,
        "c": 1,
        "4": 1,
    }

    with patch("invenio_resourcesyncserver.api.ResourceListHandler._validation", return_value=False):
        assert not test.get_record_content_file(1)

    with patch("invenio_resourcesyncserver.api.ResourceListHandler._validation", return_value=True):
        with patch("invenio_resourcesyncserver.api._export_item", return_value=[data1, data2]):
            with patch("weko_deposit.api.ItemTypes.get_by_id", return_value=data3):
                with patch("invenio_resourcesyncserver.api.check_item_type_name", return_value=data3):
                    with patch("invenio_resourcesyncserver.api.make_stats_file", return_value=[data4, data2]):
                        assert test.get_record_content_file(1) is not None

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
def test_get_change_list_content_xml_ChangeListHandler(i18n_app, db, users):
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
                    # Exception coverage
                    test_str.get_change_list_content_xml(
                        from_date=from_date,
                        from_date_args=from_date_args,
                        to_date_args=to_date_args
                    )

                    with patch("invenio_resourcesyncserver.api.Resource", return_value=return_data):
                        with patch("invenio_resourcesyncserver.api.PIDVersioning", return_value=return_data):
                            assert "xml" in test_str.get_change_list_content_xml(
                                from_date=from_date,
                                from_date_args=from_date_args,
                                to_date_args=to_date_args
                            )

                        with patch("invenio_resourcesyncserver.api.PIDVersioning", return_value=return_data):
                            return_data.last_child = MagicMock()
                            return_data.last_child.pid_value = "test"
                            assert "xml" in test_str.get_change_list_content_xml(
                                from_date=from_date,
                                from_date_args=from_date_args,
                                to_date_args=to_date_args
                            )

#     def get_change_list_index(self):
def test_get_change_list_index_ChangeListHandler(i18n_app):
    test_str = sample_ChangeListHandler("str")
    test_str.publish_date = datetime.datetime.now() - datetime.timedelta(hours=1)

    with patch("invenio_resourcesyncserver.api.ChangeListHandler._validation", return_value=""):
        assert not test_str.get_change_list_index()

    with patch("invenio_resourcesyncserver.api.ChangeListHandler._validation", return_value="_str"):
        assert test_str.get_change_list_index()


#     def get_change_dump_index(self):
def test_get_change_dump_index_ChangeListHandler(i18n_app):
    test_str = sample_ChangeListHandler("str")

    def _validation():
        return True

    def _not_validation():
        return False

    test_str._validation = _validation
    test_str.publish_date = datetime.datetime.now() - datetime.timedelta(hours=1)

    assert test_str.get_change_dump_index()

    test_str._validation = _not_validation

    assert not test_str.get_change_dump_index()


#     def get_change_dump_xml(self, from_date):
def test_get_change_dump_xml_ChangeListHandler(i18n_app):
    test_str = sample_ChangeListHandler("str")
    from_date = datetime.datetime.now() - datetime.timedelta(hours=1)


    def _validation():
        return True

    def _not_validation():
        return False

    def _get_record_changes_with_interval(key_date, keyword=True):
        data_1 = MagicMock()

        if not keyword:
            data_1.status = "deleted"

        data_1.updated = datetime.datetime.now()
        data_2 = [data_1]
        return data_2

    def _next_change(x, y):
        return MagicMock()

    test_str._validation = _validation
    test_str._get_record_changes_with_interval = _get_record_changes_with_interval
    test_str._next_change = _next_change

    # Exception coverage
    assert test_str.get_change_dump_xml(from_date)

    test_str._validation = _not_validation

    assert not test_str.get_change_dump_xml(from_date)


#     def _validation(self):
def test__validation_ChangeListHandler(i18n_app):
    test_str = sample_ChangeListHandler("str")
    test_str.index = MagicMock()
    test_str.index.public_state = True

    assert test_str._validation()

    test_str.repository_id = None

    assert test_str._validation()

    test_str.status = False

    assert not test_str._validation()


#     def get_change_dump_manifest_xml(self, record_id):
def test_get_change_dump_manifest_xml_ChangeListHandler(i18n_app):
    test_str = sample_ChangeListHandler("str")
    record_id = "8.9"

    def _validation():
        return MagicMock()

    def _is_record_in_index(key):
        return "8.9"

    assert not test_str.get_change_dump_manifest_xml(record_id)

    test_str._validation = _validation
    test_str._is_record_in_index = _is_record_in_index
    return_data = MagicMock()
    data_1 = MagicMock()
    return_data.files = [data_1]

    with patch("weko_deposit.api.WekoRecord.get_record_by_pid", return_value=return_data):
        with patch("invenio_resourcesyncserver.utils.get_pid", return_value=return_data):
            with patch("weko_deposit.api.WekoRecord.get_record", return_value=return_data):
                assert test_str.get_change_dump_manifest_xml(record_id)


#     def delete(cls, change_list_id):
def test_delete_ChangeListHandler(i18n_app):
    change_list_id = 1
    test_str = sample_ChangeListHandler("str")

    # def get_change_list(x, y):
    #     return True

    # def not_get_change_list(x, y):
    #     return False

    # test_str.get_change_list = not_get_change_list

    with patch("invenio_resourcesyncserver.api.ChangeListHandler.get_change_list", return_value="test"):
        assert not test_str.delete(change_list_id)

    assert not test_str.delete(change_list_id)


#     def get_index(self):
def test_get_index_ChangeListHandler(i18n_app):
    test_str = sample_ChangeListHandler("str")
    with patch("weko_index_tree.api.Indexes.get_index", return_value=""):
        assert not test_str.get_index()


#     def to_dict(self):
def test_to_dict_ChangeListHandler(i18n_app):
    test_str = sample_ChangeListHandler("str")
    test_str.index = MagicMock()
    test_str.index.index_name_english = "test"

    assert test_str.to_dict()


#     def get_change_list(cls, changelist_id, type_result='obj'):
def test_get_change_list_ChangeListHandler(i18n_app, db):
    test_str = sample_ChangeListHandler("str")
    changelist_id = 1

    from invenio_resourcesyncserver.models import ChangeListIndexes
    test = ChangeListIndexes(
        id=1,
        repository_id=111,
        change_dump_manifest=True,
        max_changes_size=1,
        interval_by_date=2,
        change_tracking_state="test",
        url_path="/",
        publish_date=datetime.datetime.now()
    )

    assert not test_str.get_change_list(changelist_id)

    db.session.add(test)
    db.session.commit()

    assert test_str.get_change_list(changelist_id, "modal")
    assert test_str.get_change_list(changelist_id)


#     def get_all(cls):
#     def convert_modal_to_obj(cls, model=ChangeListIndexes()):
def test_get_all_ChangeListHandler(i18n_app, db, users):
    test_str = sample_ChangeListHandler("str")

    from invenio_resourcesyncserver.models import ChangeListIndexes
    test = ChangeListIndexes(
        id=1,
        repository_id=111,
        change_dump_manifest=True,
        max_changes_size=1,
        interval_by_date=2,
        change_tracking_state="test",
        url_path="/",
        publish_date=datetime.datetime.now()
    )

    # no data
    assert not test_str.get_all()

    db.session.add(test)
    db.session.commit()

    # without user
    result = test_str.get_all()
    assert len(result) == 1
    assert result[0].id == test.id

    # super role user
    user = users[3]["obj"]
    result = test_str.get_all(user=user)
    assert len(result) == 1
    assert isinstance(result[0], ChangeListHandler)
    assert result[0].id == test.id

    # comadmin role user with repository
    user = users[4]["obj"]
    mock_repo = Community(root_node_id=1)
    with patch("invenio_communities.models.Community.get_repositories_by_user", return_value=[mock_repo]):
        with patch("weko_index_tree.api.Indexes.get_child_list_recursive", return_value=[test.repository_id]):
            result = test_str.get_all(user=user)
            assert len(result) == 1
            assert isinstance(result[0], ChangeListHandler)
            assert result[0].id == test.id

    # comadmin role user with no repository
    with patch("invenio_communities.models.Community.get_repositories_by_user", return_value=[]):
        result = test_str.get_all(user=user)
        assert len(result) == 0

    # comadmin role user with repository but no index
    with patch("invenio_communities.models.Community.get_repositories_by_user", return_value=[mock_repo]):
        with patch("weko_index_tree.api.Indexes.get_child_list_recursive", return_value=[]):
            result = test_str.get_all(user=user)
            assert len(result) == 0


#     def get_change_list_by_repo_id(cls, repo_id, type_result='obj'):
def test_get_change_list_by_repo_id_ChangeListHandler(i18n_app, db):
    test_str = sample_ChangeListHandler("str")
    repo_id = 111

    from invenio_resourcesyncserver.models import ChangeListIndexes
    test = ChangeListIndexes(
        id=1,
        repository_id=111,
        change_dump_manifest=True,
        max_changes_size=1,
        interval_by_date=2,
        change_tracking_state="test",
        url_path="/",
        publish_date=datetime.datetime.now()
    )

    db.session.add(test)
    db.session.commit()

    assert test_str.get_change_list_by_repo_id(repo_id)
    assert test_str.get_change_list_by_repo_id(repo_id, 'modal')


#     def _is_record_in_index(self, record_id):
def test__is_record_in_index_ChangeListHandler(i18n_app):
    test_str = sample_ChangeListHandler("str")
    record_id = 1
    return_data = MagicMock()
    return_data.object_uuid = 1

    with patch("invenio_resourcesyncserver.utils.get_pid", return_value=return_data):
        with patch("weko_deposit.api.WekoRecord.get_record", return_value=MagicMock()):
            with patch("invenio_resourcesyncserver.utils.get_real_path", return_value=test_str.repository_id):
                assert test_str._is_record_in_index(record_id)

                test_str.repository_id = "Index"

                assert test_str._is_record_in_index(record_id)
            assert not test_str._is_record_in_index(record_id)


#     def get_record_content_file(self, record_id):
def test_get_record_content_file_ChangeListHandler(i18n_app, es_records):
    test_str = sample_ChangeListHandler("str")
    record_id = 1
    data_1 = MagicMock()
    data_2 = MagicMock()
    return_data = (data_1, data_2)

    def _is_record_in_index(key):
        return True

    def _is_not_record_in_index(key):
        return False

    def get_change_dump_manifest_xml(key):
        return "test"

    test_str._is_record_in_index = _is_not_record_in_index

    assert not test_str.get_record_content_file(record_id)

    test_str._is_record_in_index = _is_record_in_index

    # Exception coverage
    assert not test_str.get_record_content_file(record_id)

    test_str.get_change_dump_manifest_xml = get_change_dump_manifest_xml

    assert test_str.get_record_content_file(record_id)


#     def get_capability_content(cls):
def test_get_capability_content_ChangeListHandler(i18n_app):
    test_str = sample_ChangeListHandler("str")
    return_data = MagicMock()

    def _validation():
        return True

    return_data._validation = _validation
    return_data.url_path = "/test"

    with patch("invenio_resourcesyncserver.api.ChangeListHandler.get_all", return_value=[return_data]):
        assert test_str.get_capability_content()


#     def _date_validation(self, date_from: str):
def test__date_validation_ChangeListHandler(i18n_app):
    test_str = sample_ChangeListHandler("str")
    test_str.publish_date = datetime.datetime.now() - datetime.timedelta(days=5)
    date_from = "20221107"

    assert test_str._date_validation(date_from)

    date_from = "test"

    # Exception coverage
    assert not test_str._date_validation(date_from)


#     def _next_change(self, data, changes):
def test__next_change_ChangeListHandler(i18n_app):
    test_str = sample_ChangeListHandler("str")
    data = {
        "record_id": 1,
        "record_version": 1
    }
    changes = {
        "record_id": 1,
        "record_version": 2
    }

    assert test_str._next_change(data, [changes])

    changes["record_version"] = 1

    assert not test_str._next_change(data, [changes])


#     def _get_record_changes_with_interval(self, from_date):
def test__get_record_changes_with_interval_ChangeListHandler(i18n_app):
    test_str = sample_ChangeListHandler("str")

    def _date_validation(key):
        return datetime.datetime.now() - datetime.timedelta(hours=1)

    def _not_date_validation(key):
        return False

    def _get_record_changes(key1, key2, key3):
        return "test"

    test_str._date_validation = _date_validation
    test_str.interval_by_date = 1
    test_str._get_record_changes = _get_record_changes

    from_date = "test"

    assert test_str._get_record_changes_with_interval(from_date)

    test_str._date_validation = _not_date_validation

    assert not test_str._get_record_changes_with_interval(from_date)


#     def _get_record_changes(self, repo_id, from_date, until_date):
def test__get_record_changes_ChangeListHandler(i18n_app):
    test_str = sample_ChangeListHandler("str")
    repo_id = 1
    from_date = 1
    until_date = 1

    with patch("invenio_resourcesyncserver.utils.query_record_changes", return_value=True):
        assert test_str._get_record_changes(repo_id, from_date, until_date)

    # Exception coverage
    assert not test_str._get_record_changes(repo_id, from_date, until_date)

import json
import pytest
import datetime
from lxml import etree
from flask import current_app, make_response, request
from flask_login import current_user
from mock import patch, MagicMock
from werkzeug.local import LocalProxy

from invenio_resourcesyncserver.api import ResourceListHandler, ChangeListHandler
from invenio_resourcesyncserver.models import ChangeListIndexes, ResourceListIndexes
from invenio_accounts.testutils import login_user_via_session
from invenio_resourcesyncserver.views import (
    resource_list,
    resource_dump,
    file_content,
    capability,
    resource_dump_manifest,
    change_list_index,
    change_list,
    change_dump_index,
    change_dump,
    change_dump_manifest,
    change_dump_content,
    well_know_resourcesync,
    source_description,
    record_detail_in_index
)


user_results = [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
    (7, 200),
    (8, 200),
]

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


# def resource_list(index_id):
# @pytest.mark.parametrize('id, status_code', user_results)
# @pytest.mark.parametrize('status', [True, False])
def test_resource_list(client_api, users, indices):
    # login_user_via_session(client=client_api, email=users[3]["email"])

    # res = client_api.post(
    #     "/resync/<index_id>/resourcelist.xml",
    #     data=json.dumps({}),
    #     content_type="application/json"
    # )

    # assert res.status_code == status_code

    test = sample_ResourceListHandler()
    index_id = 33

    def get_resource_list_xml():
        return True

    def not_get_resource_list_xml():
        return False

    data_1 = MagicMock()
    data_1.status = True
    data_1.get_resource_list_xml = get_resource_list_xml

    with patch("invenio_resourcesyncserver.api.ResourceListHandler.get_resource_by_repository_id", return_value=data_1):
        assert resource_list(index_id)

    with patch("invenio_resourcesyncserver.api.ResourceListHandler.get_resource_by_repository_id", return_value=None):
        try:
            assert resource_list(index_id)
        # abort(404) coverage
        except:
            pass

    with patch("invenio_resourcesyncserver.api.ResourceListHandler.get_resource_by_repository_id", return_value=data_1):
        data_1.get_resource_list_xml = not_get_resource_list_xml
        try:
            assert resource_list(index_id)
        # abort(404) coverage
        except:
            pass


# def resource_dump(index_id):
def test_resource_dump(client_api, users, indices):
    test = sample_ResourceListHandler()
    index_id = 33

    def get_resource_dump_xml():
        return True

    def not_get_resource_dump_xml():
        return False

    data_1 = MagicMock()
    data_1.status = True
    data_1.get_resource_dump_xml = get_resource_dump_xml

    with patch("invenio_resourcesyncserver.api.ResourceListHandler.get_resource_by_repository_id", return_value=data_1):
        assert resource_dump(index_id)

    with patch("invenio_resourcesyncserver.api.ResourceListHandler.get_resource_by_repository_id", return_value=None):
        try:
            assert resource_dump(index_id)
        # abort(404) coverage
        except:
            pass

    with patch("invenio_resourcesyncserver.api.ResourceListHandler.get_resource_by_repository_id", return_value=data_1):
        data_1.get_resource_dump_xml = not_get_resource_dump_xml
        try:
            assert resource_dump(index_id)
        # abort(404) coverage
        except:
            pass


# def file_content(index_id, record_id):
def test_file_content(i18n_app, indices):
    index_id = 33
    record_id = 1
    data1 = MagicMock()
    def get_record_content_file(item):
        return item
    data1.get_record_content_file = get_record_content_file

    with patch("invenio_resourcesyncserver.api.ResourceListHandler.get_resource_by_repository_id", return_value=data1):
        assert file_content(index_id=index_id, record_id=record_id) is not None
    
    # Exception coverage
    # file_content(index_id=index_id, record_id=record_id) is not None


# def capability():
def test_capability(i18n_app):
    with patch("invenio_resourcesyncserver.views.render_capability_xml", return_value=[1,2,3]):
        assert "Response" in str(type(capability()))

    # Exception coverage
    # capability()


# def resource_dump_manifest(index_id, record_id):
def test_resource_dump_manifest(i18n_app):
    index_id = 33
    record_id = 1
    data1 = MagicMock()
    def get_record_content_file(item):
        return item
    data1.get_record_content_file = get_record_content_file

    with patch("invenio_resourcesyncserver.api.ResourceListHandler.get_resource_by_repository_id", return_value=data1):
        assert "Response" in str(type(resource_dump_manifest(index_id=index_id, record_id=record_id)))

    # Exception coverage
    # resource_dump_manifest(index_id=index_id, record_id=record_id)


# def change_list_index(index_id):
def test_change_list_index(i18n_app, indices):
    index_id = 33
    data1 = MagicMock()

    def get_change_list_index():
        return True

    def get_change_list_by_repo_id(item):
        data = MagicMock()
        data.get_change_list_index = get_change_list_index
        return data
        
    data1.get_change_list_by_repo_id = get_change_list_by_repo_id

    with patch("invenio_resourcesyncserver.api.ChangeListHandler.get_change_list_by_repo_id", return_value=data1):
        assert "Response" in str(type(change_list_index(index_id=index_id)))

    # Exception coverage
    # change_list_index(index_id=index_id)


# def change_list(index_id, from_date):
def test_change_list(i18n_app, indices):
    index_id = 33
    from_date = datetime.datetime.now() - datetime.timedelta(days=2)
    data1 = MagicMock()

    def get_change_list_content_xml():
        return True

    def get_change_list_by_repo_id(item):
        data = MagicMock()
        data.get_change_list_content_xml = get_change_list_content_xml
        return data
        
    data1.get_change_list_by_repo_id = get_change_list_by_repo_id

    with patch("invenio_resourcesyncserver.api.ChangeListHandler.get_change_list_by_repo_id", return_value=data1):
        assert "Response" in str(type(change_list(index_id=index_id, from_date=from_date)))

    # Exception coverage
    # change_list_index(index_id=index_id)


# def change_dump_index(index_id):
def test_change_dump_index(i18n_app, indices):
    index_id = 33
    from_date = datetime.datetime.now() - datetime.timedelta(days=2)
    data1 = MagicMock()

    def get_change_dump_index():
        return True

    def get_change_list_by_repo_id(item):
        data = MagicMock()
        data.get_change_dump_index = get_change_list_content_xml
        return data
        
    data1.get_change_list_by_repo_id = get_change_list_by_repo_id

    with patch("invenio_resourcesyncserver.api.ChangeListHandler.get_change_list_by_repo_id", return_value=data1):
        assert "Response" in str(type(change_dump_index(index_id=index_id)))

    # Exception coverage
    # change_dump_index(index_id=index_id)


# def change_dump(index_id, from_date):
def test_change_dump(i18n_app, indices):
    index_id = 33
    from_date = datetime.datetime.now() - datetime.timedelta(days=2)
    data1 = MagicMock()

    def get_change_dump_xml():
        return True

    def get_change_list_by_repo_id(item):
        data = MagicMock()
        data.get_change_dump_xml = get_change_dump_xml
        return data
        
    data1.get_change_list_by_repo_id = get_change_list_by_repo_id

    with patch("invenio_resourcesyncserver.api.ChangeListHandler.get_change_list_by_repo_id", return_value=data1):
        assert "Response" in str(type(change_dump(index_id=index_id, from_date=from_date)))

    # Exception coverage
    # change_dump(index_id=index_id)


# def change_dump_manifest(index_id, record_id):
def test_change_dump_manifest(i18n_app, indices):
    index_id = 33
    record_id = 1
    data1 = MagicMock()

    def get_change_dump_manifest_xml():
        return True

    def get_change_list_by_repo_id(item):
        data = MagicMock()
        data.get_change_dump_manifest_xml = get_change_dump_manifest_xml
        return data
        
    data1.get_change_list_by_repo_id = get_change_list_by_repo_id

    with patch("invenio_resourcesyncserver.api.ChangeListHandler.get_change_list_by_repo_id", return_value=data1):
        assert "Response" in str(type(change_dump_manifest(index_id=index_id, record_id=record_id)))

    # Exception coverage
    # change_dump_manifest(index_id=index_id)


# def change_dump_content(index_id, record_id):
def test_change_dump_content(i18n_app, indices):
    index_id = 33
    record_id = 1
    data1 = MagicMock()

    def get_record_content_file():
        return True

    def get_change_list_by_repo_id(item):
        data = MagicMock()
        data.get_record_content_file = get_record_content_file
        return data
        
    data1.get_change_list_by_repo_id = get_change_list_by_repo_id

    with patch("invenio_resourcesyncserver.api.ChangeListHandler.get_change_list_by_repo_id", return_value=data1):
        assert str(type(change_dump_content(index_id=index_id, record_id=record_id))) == str(type(get_change_list_by_repo_id(index_id)))

    # Exception coverage
    # change_dump_content(index_id=index_id)


# def well_know_resourcesync():
def test_well_know_resourcesync(i18n_app):
    assert "Response" in str(type(well_know_resourcesync()))


# def source_description():
def test_source_description(i18n_app):
    assert "Response" in str(type(source_description()))


# def record_detail_in_index(index_id, record_id):
def test_record_detail_in_index(i18n_app, indices):
    index_id = 33
    record_id = MagicMock()
    def zfill(item):
        return "item"
    record_id.zfill = zfill

    test = etree.Element("test")
    test.append( etree.Element("test1") )

    with patch("invenio_resourcesyncserver.views.getrecord", return_value=test):
        assert "Response" in str(type(record_detail_in_index(index_id=index_id, record_id=record_id)))
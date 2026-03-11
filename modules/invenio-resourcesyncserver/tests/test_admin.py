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

from invenio_resourcesyncserver.admin import AdminResourceListView, AdminChangeListView
from invenio_resourcesyncserver.models import ResourceListIndexes, ChangeListIndexes

test_1 = AdminResourceListView()
test_1.admin = MagicMock()
test_1.admin.base_template = MagicMock()

def sample_render(key):
    return True

test_1.render = sample_render

test_2 = AdminChangeListView()
test_2.admin = MagicMock()
test_2.admin.base_template = MagicMock()

def sample_render(key):
    return True

test_2.render = sample_render


# class AdminResourceListView(BaseView):
#     def index(self):
def test_index_AdminResourceListView(i18n_app):
    assert test_1.index()

#     def get_list(self):
def test_get_list_AdminResourceListView(i18n_app):
    mock_data = MagicMock()
    mock_data.to_dict.return_value = {"key": "value"}
    with  patch("invenio_resourcesyncserver.api.ResourceListHandler.get_list_resource", return_value=[mock_data]) as mock_get_list_resource:
        result = test_1.get_list()
        assert result.status_code == 200
        result_json = result.get_json()
        assert len(result_json) == 1
        assert result_json[0] == {"key": "value"}
        mock_get_list_resource.assert_called_once_with(user=current_user)

#     def create(self):
def test_create_AdminResourceListView(i18n_app):
    data = MagicMock()
    data.success = True

    with patch("invenio_resourcesyncserver.api.ResourceListHandler.create", return_value=data):
        assert test_1.create()

    assert test_1.create()

#     def update(self, resource_id):
def test_update_AdminResourceListView(i18n_app, db):
    from invenio_resourcesyncserver.api import ResourceListHandler
    test = ResourceListIndexes(
        id=1,
        repository_id=2,
    )

    db.session.add(test)
    db.session.commit()

    data = MagicMock()
    data.success = True

    with patch("invenio_resourcesyncserver.api.ResourceListHandler.get_resource", return_value=data):
        assert test_1.update(resource_id=1)

    data = None

    with patch("invenio_resourcesyncserver.api.ResourceListHandler.get_resource", return_value=data):
        assert test_1.update(resource_id=0)

#     def delete(self, resource_id):
def test_delete_AdminResourceListView(i18n_app, db):
    test = ResourceListIndexes(
        id=1,
        repository_id=2
    )

    db.session.add(test)
    db.session.commit()

    assert test_1.delete(resource_id=1)


# class AdminChangeListView(BaseView):
#     def index(self):
def test_index_AdminChangeListView(i18n_app):
    assert test_2.index()

#     def get_list(self):
def test_get_list_AdminChangeListView(i18n_app, db):
    data = MagicMock()
    data.to_dict.return_value = {"key": "value"}

    with patch("invenio_resourcesyncserver.api.ChangeListHandler.get_all", return_value=[data]) as mock_get_all:
        result = test_2.get_list()
        assert result.status_code == 200
        result_json = result.get_json()
        assert len(result_json) == 1
        assert result_json[0] == {"key": "value"}
        mock_get_all.assert_called_once_with(user=current_user)

#     def get_change_list(self, repo_id):
def test_get_change_list_AdminChangeListView(i18n_app, db):
    data = MagicMock()

    with patch("invenio_resourcesyncserver.api.ChangeListHandler.get_change_list", return_value=data):
        assert test_2.get_change_list(1)

#     def create(self):
def test_create_AdminChangeListView(i18n_app, db):
    sample = MagicMock()
    def to_dict():
        return {"A": 1}
    sample.to_dict = to_dict

    data = {
        "id": 2,
        "status": "test",
        "repository_id": 2,
        "change_dump_manifest": "test",
        "max_changes_size": 2,
        "change_tracking_state": "test",
        "url_path": "test",
        "created": datetime.datetime.now().strftime("%Y%m%d"),
        "updated": datetime.datetime.now().strftime("%Y%m%d"),
        "index": 2,
        "publish_date": datetime.datetime.now().strftime("%Y%m%d"),
        "interval_by_date": datetime.datetime.now().strftime("%Y%m%d"),
        "success": 1,
        "message": "message"
    }

    with patch("flask.request.get_json", return_value=data):
        data["data"] = sample
        with patch("invenio_resourcesyncserver.api.ChangeListHandler.save", return_value=data):
            assert test_2.create()
            data["success"] = False
            assert test_2.create()

#     def update(self, repo_id):
def test_update_AdminChangeListView(i18n_app, db):
    data = {}
    test = ChangeListIndexes(
        id=1,
        repository_id=2,
        max_changes_size=11,
        interval_by_date=1,
    )

    db.session.add(test)
    db.session.commit()

    with patch("flask.request.get_json", return_value=data):
        assert test_2.update(1)

#     def delete(self, repo_id):
def test_delete_AdminChangeListView(i18n_app, db):
    data = {}
    test = ChangeListIndexes(
        id=1,
        repository_id=2,
        max_changes_size=11,
        interval_by_date=1,
    )

    db.session.add(test)
    db.session.commit()

    with patch("flask.request.get_json", return_value=data):
        assert test_2.delete(1)

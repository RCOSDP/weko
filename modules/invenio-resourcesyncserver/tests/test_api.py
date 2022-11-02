import os
import json
import copy
import pytest
import unittest
from datetime import datetime
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


#     def get_resource_list_xml(self, from_date=None, to_date=None):
#     def get_resource_dump_xml(self, from_date=None, to_date=None):
#     def get_capability_content(cls):
#     def get_resource_dump_manifest(self, record_id):
#     def get_record_content_file(self, record_id):


# class ChangeListHandler(object):
#     def __init__(self, **kwargs):
#     def save(self):
#     def get_change_list_content_xml(self, from_date,
#     def get_change_list_index(self):
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
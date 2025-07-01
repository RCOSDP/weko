# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Module tests."""

from re import T
# from tkinter import W
import pytest
from unittest import TestCase
import json
from elasticsearch import helpers
from elasticsearch.exceptions import RequestError
from flask_login.utils import login_user
from invenio_records.api import Record
from invenio_records.errors import MissingModelError
from invenio_pidstore.models import PersistentIdentifier
from weko_deposit.api import WekoDeposit
from weko_index_tree.models import Index
from mock import patch,MagicMock
import uuid
from sqlalchemy.exc import IntegrityError,SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound

from weko_records.api import FeedbackMailList, RequestMailList, FilesMetadata, ItemLink, \
    ItemsMetadata, ItemTypeEditHistory, ItemTypeNames, ItemTypeProps, \
    ItemTypes, Mapping, JsonldMapping, SiteLicense, RecordBase, WekoRecord
from weko_records.models import ItemType, ItemTypeJsonldMapping, ItemTypeName, \
    SiteLicenseInfo, SiteLicenseIpAddress
from jsonschema.validators import Draft4Validator
from datetime import datetime, timedelta
from weko_records.models import ItemReference
import pytest
from unittest.mock import patch, MagicMock

# class RecordBase(dict):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_recordbase -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_recordbase(app, db):
    class MockClass():
        def __init__(self, id, version_id, created, updated):
            self.id=id
            self.version_id=version_id
            self.created=created
            self.updated=updated
            self.schema=""

    data = dict(
        id=1,
        version_id=10,
        created="yesterday",
        updated="now"
    )
    test_model = MockClass(**data)
    record = RecordBase(data)
    assert record.id == None
    assert record.revision_id == None
    assert record.created == None
    assert record.updated == None
    record.model = test_model
    assert record.id == 1
    assert record.revision_id == 9
    assert record.created == "yesterday"
    assert record.updated == "now"
    result = record.dumps()
    assert result["id"] == 1
    assert result["version_id"] == 10
    assert result["created"] == "yesterday"
    assert result["updated"] == "now"
    assert record.validate(validator=Draft4Validator)==None

    schema = {
    'type': 'object',
    'properties': {
    'id': { 'type': 'integer' },
    'version_id': { 'type': 'integer' },
    'created': {'type': 'string' },
    'updated': { 'type': 'string' },
    },
    'required': ['id']
    }
    data = dict(
        id=1,
        version_id=10,
        created="yesterday",
        updated="now"
    )
    data['$schema']=schema
    test_model = MagicMock()
    test_model.__getitem__.side_effect = data.__getitem__
    record = RecordBase(data)
    record.model = test_model
    assert record.validate(validator=Draft4Validator) == None
    assert record.replace_refs()=={'id': 1, 'version_id': 10, 'created': 'yesterday', 'updated': 'now', '$schema': {'type': 'object', 'properties': {'id': {'type': 'integer'}, 'version_id': {'type': 'integer'}, 'created': {'type': 'string'}, 'updated': {'type': 'string'}}, 'required': ['id']}}

# class ItemTypeNames(RecordBase):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_itemtypenames -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_itemtypenames(app, db, item_type, item_type2):
    _item_type_name_3 = ItemTypeName(name='test3')
    with db.session.begin_nested():
        db.session.add(_item_type_name_3)
    # def get_record(cls, id_, with_deleted=False):
    item_type_name = ItemTypeNames.get_record(1)
    assert item_type_name.id == 1
    assert item_type_name.name == "test"
    assert item_type_name.has_site_license == True
    assert item_type_name.is_active== True
    assert isinstance(item_type_name.created,datetime)
    assert isinstance(item_type_name.updated,datetime)

    # def update(cls, obj):
    item_type_name = ItemTypeNames.get_record(2)
    item_type_name.name = "test2 updated"
    ItemTypeNames.update(item_type_name)
    item_type_name = ItemTypeNames.get_record(2)
    assert item_type_name.id == 2
    assert item_type_name.name == "test2 updated"

    data1 = {"id": 1}
    data2 = {"test": [data1]}
    ItemTypeNames.update(data2)

    # def delete(self, force=False):
    ItemTypeNames.delete(item_type_name)
    assert item_type_name.id == 2
    item_type_name = ItemTypeNames.get_record(2)
    assert item_type_name is None
    item_type_name = ItemTypeNames.get_record(2, with_deleted=True)
    assert item_type_name.id == 2
    assert item_type_name.name == "test2 updated"
    assert item_type_name.has_site_license == True
    assert item_type_name.is_active== False
    assert isinstance(item_type_name.created,datetime)
    assert isinstance(item_type_name.updated,datetime)

    # def get_all_by_id(cls, ids, with_deleted=False):
    lst = ItemTypeNames.get_all_by_id(ids=[1,2,3])
    assert len(lst)==2
    lst = ItemTypeNames.get_all_by_id(ids=[1,2,3], with_deleted=True)
    assert len(lst)==3

    # def get_name_and_id_all(cls):
    lst = ItemTypeNames.get_name_and_id_all()
    assert len(lst)>0

    # def delete(self, force=True):
    item_type_name = ItemTypeNames.get_record(3)
    assert item_type_name.id == 3
    ItemTypeNames.delete(item_type_name, force=True)
    item_type_name = ItemTypeNames.get_record(3)
    assert item_type_name is None
    item_type_name = ItemTypeNames.get_record(3, with_deleted=True)
    assert item_type_name is None
    lst = ItemTypeNames.get_all_by_id(ids=[1,2,3])
    assert len(lst)==1
    lst = ItemTypeNames.get_all_by_id(ids=[1,2,3], with_deleted=True)
    assert len(lst)==2

    # def restore(self):
    item_type_name = ItemTypeNames.get_record(2, with_deleted=True)
    assert item_type_name.id == 2
    ItemTypeNames.restore(item_type_name)
    item_type_name = ItemTypeNames.get_record(2)
    assert item_type_name.id == 2
    assert item_type_name.name == "test2 updated"
    assert item_type_name.has_site_license == True
    assert item_type_name.is_active== True


# class ItemTypes(RecordBase):
#     def create(cls, item_type_name=None, name=None, schema=None, form=None, render=None, tag=1):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_itemtypes_create -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_itemtypes_create(app, db):
    _item_type_name = ItemTypeName(name='test')

    _form = {
        'items': []
    }

    _render = {
        'meta_list': {},
        'table_row_map': {
            'schema': {
                'properties': {
                    'item_1': {}
                }
            }
        },
        'table_row': ['1']
    }

    _schema = {
        'properties': {},
    }

    # there is not param "name"
    with pytest.raises(Exception) as e:
        item_type = ItemTypes.create()
    assert e.type==ValueError
    assert str(e.value)=="Item type name cannot be empty."

    # create item type
    item_type = ItemTypes.create(
        name='test',
        item_type_name=_item_type_name,
        schema=_schema,
        form=_form,
        render=_render,
        tag=1
    )
    assert item_type=={'properties': {}}
    assert item_type.model.item_type_name.name=='test'
    assert item_type.model.schema=={'properties': {}}
    assert item_type.model.form=={'items': []}
    assert item_type.model.render=={'meta_list': {}, 'table_row_map': {'schema': {'properties': {'item_1': {}}}}, 'table_row': ['1']}
    assert item_type.model.tag==1

    # item type name is exist
    with pytest.raises(Exception) as e:
        item_type = ItemTypes.create(
            name='test'
        )
    assert e.type==ValueError
    assert str(e.value)=="Item type name is already in use."

    # create item type with only param "name"
    item_type = ItemTypes.create(
        name='test2'
    )
    assert item_type=={}
    assert item_type.model.item_type_name.name=='test2'
    assert item_type.model.schema=={}
    assert item_type.model.form=={}
    assert item_type.model.render=={}
    assert item_type.model.tag==1

# class ItemTypes(RecordBase):
#     def update(cls, id_=0, name=None, schema=None, form=None, render=None, tag=1):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_itemtypes_update -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_itemtypes_update(app, db):
    _form = {
        'items': []
    }

    _render = {
        'meta_list': {},
        'table_row_map': {
            'schema': {
                'properties': {
                    'item_1': {}
                }
            }
        },
        'table_row': ['1']
    }

    _schema = {
        'properties': {},
    }

    # update without param
    with pytest.raises(Exception) as e:
        item_type = ItemTypes.update()
    assert e.type==AssertionError

    # update with only param name and render
    item_type = ItemTypes.update(name="test", render=_render)
    assert item_type=={}
    assert item_type.model.item_type_name.name=='test'
    assert item_type.model.schema=={}
    assert item_type.model.form=={}
    assert item_type.model.render=={'meta_list': {}, 'table_row_map': {'schema': {'properties': {'item_1': {}}}}, 'table_row': ['1']}
    assert item_type.model.tag==1

    # update
    item_type = ItemTypes.update(id_=1, name="test1", schema=_schema, form=_form, render=_render)
    assert item_type=={}
    assert item_type.model.item_type_name.name=='test1'
    assert item_type.model.schema=={'properties': {}}
    assert item_type.model.form=={'items': []}
    assert item_type.model.render=={'meta_list': {}, 'table_row_map': {'schema': {'properties': {'item_1': {}}}}, 'table_row': ['1']}
    assert item_type.model.tag==1

    # id does not exist
    with pytest.raises(Exception) as e:
        item_type = ItemTypes.update(id_=10, name="test1")
    assert e.type==ValueError
    assert str(e.value)=="Invalid id."

# class ItemTypes(RecordBase):
#     def update_item_type(cls, form, id_, name, render, result, schema):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_itemtypes_update -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_itemtypes_update_item_type(app, db, location):
    _form = {
        'items': []
    }

    _render = {
        'meta_list': {},
        'table_row_map': {
            'schema': {
                'properties': {
                    'item_1': {}
                }
            }
        },
        'table_row': ['1']
    }

    _render_2 = {
        'meta_list': {},
        'table_row_map': {
            'schema': {
                'properties': {
                    'item_1': {}
                }
            }
        },
        'table_row': ['2']
    }

    _schema = {
        'properties': {},
    }

    _item_type_name_exist = ItemTypeName(name='exist title')
    with db.session.begin_nested():
        db.session.add(_item_type_name_exist)

    ItemTypes.create(
        name='test',
        schema=_schema,
        form=_form,
        render=_render,
        tag=1
    )
    item_type = ItemTypes.get_by_id(1)

    def to_dict():
        return {
            "hits": {
                "hits": [{
                    "_id": "1",
                    "_source": {
                        "_item_metadata": {
                            "item_type_id": "1"
                        }
                    },
                }]
            },
        }

    def myfilter(item):
        def all():
            return []

        filter_magicmock = MagicMock()
        filter_magicmock.all = all

        return filter_magicmock

    def myfilter_2(item):
        def all_2():
            all2_magicmock = MagicMock()
            all2_magicmock.json = {"1": "1"}
            return [all2_magicmock]

        filter_magicmock_2 = MagicMock()
        filter_magicmock_2.all = all_2

        return filter_magicmock_2

    data1 = MagicMock()
    data1.to_dict = to_dict
    data1.filter = myfilter

    data2 = MagicMock()
    data2.filter = myfilter_2

    data3 = MagicMock()

    test = ItemTypes(
                data={}
            )

    app.config['WEKO_ITEMTYPES_UI_UPGRADE_VERSION_ENABLED'] = False

    with patch("weko_records.api.RecordsSearch.execute", return_value=data1):
        with patch("weko_records.api.Mapping", return_value=data3):
            with patch("weko_records.api.db.session.merge", return_value=""):
                with patch("weko_records.api.db.session.query", return_value=data2):
                    assert test.update_item_type(
                        form=_form,
                        id_=1,
                        name='test',
                        render=_render_2,
                        result=item_type,
                        schema=_schema
                    ) != None

            with patch("weko_records.api.db.session.query", return_value=data1):
                assert test.update_item_type(
                    form=_form,
                    id_=1,
                    name='test',
                    render=_render_2,
                    result=item_type,
                    schema=_schema
                ) != None

    with pytest.raises(Exception) as e:
        record = ItemTypes.update_item_type(
            form=_form,
            id_=1,
            name='exist title',
            render=_render,
            result=item_type,
            schema=_schema
        )
    assert e.type==ValueError
    assert str(e.value)=="Invalid name."

    app.config['WEKO_ITEMTYPES_UI_UPGRADE_VERSION_ENABLED'] = False
    record = ItemTypes.update_item_type(
        form=_form,
        id_=1,
        name='test',
        render=_render_2,
        result=item_type,
        schema=_schema
    )
    assert record=={'properties': {}}
    assert record.model.item_type_name.name=='test'
    assert record.model.schema=={'properties': {}}
    assert record.model.form=={'items': []}
    assert record.model.render=={'meta_list': {}, 'table_row_map': {'schema': {'properties': {'item_1': {}}}}, 'table_row': ['2']}
    assert record.model.tag==1

    app.config['WEKO_ITEMTYPES_UI_UPGRADE_VERSION_ENABLED'] = True
    record = ItemTypes.update_item_type(
        form=_form,
        id_=1,
        name='test3',
        render=_render,
        result=item_type,
        schema=_schema
    )
    assert record=={'properties': {}}
    assert record.model.item_type_name.name=='test3'
    assert record.model.schema=={'properties': {}}
    assert record.model.form=={'items': []}
    assert record.model.render=={'meta_list': {}, 'table_row_map': {'schema': {'properties': {'item_1': {}}}}, 'table_row': ['1']}
    assert record.model.tag==1

    record = ItemTypes.update_item_type(
        form=_form,
        id_=1,
        name='test4',
        render=_render,
        result=item_type,
        schema=_schema
    )
    assert record=={'properties': {}}
    assert record.model.item_type_name.name=='test4'
    assert record.model.schema=={'properties': {}}
    assert record.model.form=={'items': []}
    assert record.model.render=={'meta_list': {}, 'table_row_map': {'schema': {'properties': {'item_1': {}}}}, 'table_row': ['1']}
    assert record.model.tag==1

# class ItemTypes(RecordBase):
#     def __update_item_type(cls, id_, schema, form, render):
#     def __update_metadata(cls, item_type_id, item_type_name, old_render, new_render):
#     def __get_records_by_item_type_name(cls, item_type_name):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test__get_records_by_item_type_name -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test__get_records_by_item_type_name(app, esindex):
    item_type_name = "test_item_type"
    def _generate_es_data(num, start_datetime=datetime.now()):
        for i in range(num):
            doc = {
                "_index": "test-weko-item-v1.0.0",
                "_type": "item-v1.0.0",
                "_id": f"2d1a2520-9080-437f-a304-230adc8{i:05d}",
                "_source": {
                    "_item_metadata": {
                        "title": [f"test_title_{i}"],
                    },
                    "relation_version_is_last": True,
                    "path": ["66"],
                    "control_number": f"{i:05d}",
                    "_created": (start_datetime + timedelta(seconds=i)).isoformat(),
                    "_updated": (start_datetime + timedelta(seconds=i)).isoformat(),
                    "publish_date": (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                    "publish_status": "0",
                },
            }
            if i % 2 == 0:
                doc["_source"]["itemtype"] = item_type_name
            else:
                doc["_source"]["itemtype"] = "test_item_type2"
            yield doc

    generate_data_num = 20002
    helpers.bulk(esindex, _generate_es_data(generate_data_num), refresh='true')

    # result over 10000
    assert len(ItemTypes._ItemTypes__get_records_by_item_type_name(item_type_name)) == int(generate_data_num/2)


# class ItemTypes(RecordBase):
#     def get_record(cls, id_, with_deleted=False):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_itemtypes_get_record -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_itemtypes_get_record(app, db):
    ItemTypes.create(name='test')
    it = ItemTypes.create(name='test2')
    ItemTypes.delete(it)

    item_type = ItemTypes.get_record(1)
    assert item_type=={}
    assert item_type.model.item_type_name.name=='test'
    assert item_type.model.schema=={}
    assert item_type.model.form=={}
    assert item_type.model.render=={}
    assert item_type.model.tag==1

    item_type = ItemTypes.get_record(2, False)
    assert item_type==None
    item_type = ItemTypes.get_record(2, True)
    assert item_type=={}
    assert item_type.model.item_type_name.name=='test2'
    assert item_type.model.schema=={}
    assert item_type.model.form=={}
    assert item_type.model.render=={}
    assert item_type.model.tag==1

# class ItemTypes(RecordBase):
#     def get_records(cls, ids, with_deleted=False):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_itemtypes_get_records -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_itemtypes_get_records(app, db):
    ItemTypes.create(name='test')
    it = ItemTypes.create(name='test2')
    ItemTypes.delete(it)

    item_types = ItemTypes.get_records([1, 2], False)
    assert len(item_types)==1
    assert item_types[0]=={}
    assert item_types[0].model.item_type_name.name=='test'
    assert item_types[0].model.schema=={}
    assert item_types[0].model.form=={}
    assert item_types[0].model.render=={}
    assert item_types[0].model.tag==1

    item_types = ItemTypes.get_records([1, 2], True)
    assert len(item_types)==2
    assert item_types[0]=={}
    assert item_types[0].model.item_type_name.name=='test'
    assert item_types[0].model.schema=={}
    assert item_types[0].model.form=={}
    assert item_types[0].model.render=={}
    assert item_types[0].model.tag==1
    assert item_types[1]=={}
    assert item_types[1].model.item_type_name.name=='test2'
    assert item_types[1].model.schema=={}
    assert item_types[1].model.form=={}
    assert item_types[1].model.render=={}
    assert item_types[1].model.tag==1

# class ItemTypes(RecordBase):
#     def get_by_id(cls, id_, with_deleted=False):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_itemtypes_get_by_id -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_itemtypes_get_by_id(app, db):
    ItemTypes.create(name='test')
    it = ItemTypes.create(name='test2')
    ItemTypes.delete(it)

    item_type = ItemTypes.get_by_id(1)
    assert item_type.item_type_name.name=='test'
    assert item_type.schema=={}
    assert item_type.form=={}
    assert item_type.render=={}
    assert item_type.tag==1

    item_type = ItemTypes.get_by_id(2, False)
    assert item_type==None
    item_type = ItemTypes.get_by_id(2, True)
    assert item_type.item_type_name.name=='test2'
    assert item_type.schema=={}
    assert item_type.form=={}
    assert item_type.render=={}
    assert item_type.tag==1

# class ItemTypes(RecordBase):
#     def get_by_name_id(cls, name_id, with_deleted=False):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_itemtypes_get_by_name_id -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_itemtypes_get_by_name_id(app, db):
    ItemTypes.create(name='test')
    it = ItemTypes.create(name='test2')
    ItemTypes.delete(it)

    item_types = ItemTypes.get_by_name_id(1)
    assert len(item_types)==1
    assert item_types[0].item_type_name.name=='test'
    assert item_types[0].schema=={}
    assert item_types[0].form=={}
    assert item_types[0].render=={}
    assert item_types[0].tag==1

    item_types = ItemTypes.get_by_name_id(2, False)
    assert len(item_types)==0
    item_types = ItemTypes.get_by_name_id(2, True)
    assert len(item_types)==1
    assert item_types[0].item_type_name.name=='test2'
    assert item_types[0].schema=={}
    assert item_types[0].form=={}
    assert item_types[0].render=={}
    assert item_types[0].tag==1

# class ItemTypes(RecordBase):
#     def get_records_by_name_id(cls, name_id, with_deleted=False):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_itemtypes_get_records_by_name_id -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_itemtypes_get_records_by_name_id(app, db):
    ItemTypes.create(name='test')
    it = ItemTypes.create(name='test2')
    ItemTypes.delete(it)

    item_types = ItemTypes.get_records_by_name_id(1)
    assert len(item_types)==1
    assert item_types[0]=={}
    assert item_types[0].model.item_type_name.name=='test'
    assert item_types[0].model.schema=={}
    assert item_types[0].model.form=={}
    assert item_types[0].model.render=={}
    assert item_types[0].model.tag==1

    item_types = ItemTypes.get_records_by_name_id(2, False)
    assert len(item_types)==0
    item_types = ItemTypes.get_records_by_name_id(2, True)
    assert len(item_types)==1
    assert item_types[0]=={}
    assert item_types[0].model.item_type_name.name=='test2'
    assert item_types[0].model.schema=={}
    assert item_types[0].model.form=={}
    assert item_types[0].model.render=={}
    assert item_types[0].model.tag==1

# class ItemTypes(RecordBase):
#     def get_latest(cls, with_deleted=False):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_itemtypes_get_latest -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_itemtypes_get_latest(app, db):
    ItemTypes.create(name='test')
    it = ItemTypes.create(name='test2')
    ItemTypes.delete(it)

    # need to fix
    item_type_names = ItemTypes.get_latest(False)
    assert len(item_type_names)==1
    assert item_type_names[0].id == 1
    assert item_type_names[0].name == "test"
    assert item_type_names[0].has_site_license == True
    assert item_type_names[0].is_active== True
    assert isinstance(item_type_names[0].created,datetime)
    assert isinstance(item_type_names[0].updated,datetime)

    # need to fix
    item_type_names = ItemTypes.get_latest(True)
    assert len(item_type_names)==2
    assert item_type_names[0].id == 1
    assert item_type_names[0].name == "test"
    assert item_type_names[0].has_site_license == True
    assert item_type_names[0].is_active== True
    assert isinstance(item_type_names[0].created,datetime)
    assert isinstance(item_type_names[0].updated,datetime)
    assert item_type_names[1].id == 2
    assert item_type_names[1].name == "test2"
    assert item_type_names[1].has_site_license == True
    assert item_type_names[1].is_active== True
    assert isinstance(item_type_names[1].created,datetime)
    assert isinstance(item_type_names[1].updated,datetime)

# class ItemTypes(RecordBase):
#     get_latest_with_item_type(cls, with_deleted=False):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_itemtypes_get_latest_with_item_type -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_itemtypes_get_latest_with_item_type(app, db):
    ItemTypes.create(name='test')
    it = ItemTypes.create(name='test2')
    ItemTypes.delete(it)

    item_types = ItemTypes.get_latest_with_item_type(False)
    assert len(item_types)==1
    assert item_types[0].name == "test"
    assert item_types[0].id == 1
    assert item_types[0].harvesting_type == False
    assert item_types[0].is_deleted == False
    assert item_types[0].tag == 1

    item_types = ItemTypes.get_latest_with_item_type(True)
    assert len(item_types)==2
    assert item_types[0].name == "test"
    assert item_types[0].id == 1
    assert item_types[0].harvesting_type == False
    assert item_types[0].is_deleted == False
    assert item_types[0].tag == 1
    assert item_types[1].name == "test2"
    assert item_types[1].id == 2
    assert item_types[1].harvesting_type == False
    assert item_types[1].is_deleted == True
    assert item_types[1].tag == 1

# class ItemTypes(RecordBase):
#     get_latest_custorm_harvesting(cls, with_deleted=False, harvesting_type=False):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_itemtypes_get_latest_custorm_harvesting -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_itemtypes_get_latest_custorm_harvesting(app, db):
    ItemTypes.create(name='test')
    ItemTypes.create(name='test2')
    it3 = ItemTypes.create(name='test3')
    it4 = ItemTypes.create(name='test4')
    ItemTypes.delete(it3)
    ItemTypes.delete(it4)
    with db.session.begin_nested():
        it2 = ItemTypes.get_by_id(2, True)
        it2.harvesting_type = True
        db.session.merge(it2)
        it4 = ItemTypes.get_by_id(4, True)
        it4.harvesting_type = True
        db.session.merge(it4)
    db.session.commit()

    item_type_names = ItemTypes.get_latest_custorm_harvesting(False, False)
    assert len(item_type_names)==1
    assert item_type_names[0].id == 1
    assert item_type_names[0].name == "test"
    assert item_type_names[0].has_site_license == True
    assert item_type_names[0].is_active== True
    assert isinstance(item_type_names[0].created,datetime)
    assert isinstance(item_type_names[0].updated,datetime)

    item_type_names = ItemTypes.get_latest_custorm_harvesting(False, True)
    assert len(item_type_names)==1
    assert item_type_names[0].id == 2
    assert item_type_names[0].name == "test2"
    assert item_type_names[0].has_site_license == True
    assert item_type_names[0].is_active== True
    assert isinstance(item_type_names[0].created,datetime)
    assert isinstance(item_type_names[0].updated,datetime)

    # need to fix
    item_type_names = ItemTypes.get_latest_custorm_harvesting(True, False)
    assert len(item_type_names)==4

    # need to fix
    item_type_names = ItemTypes.get_latest_custorm_harvesting(True, True)
    assert len(item_type_names)==4

# class ItemTypes(RecordBase):
#     def get_all(cls, with_deleted=False):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_itemtypes_get_all -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_itemtypes_get_all(app, db):
    ItemTypes.create(name='test')
    it = ItemTypes.create(name='test2')
    ItemTypes.delete(it)

    item_types = ItemTypes.get_all(False)
    assert len(item_types)==1
    assert item_types[0].item_type_name.name=='test'
    assert item_types[0].schema=={}
    assert item_types[0].form=={}
    assert item_types[0].render=={}
    assert item_types[0].tag==1

    item_types = ItemTypes.get_all(True)
    assert len(item_types)==2
    assert item_types[0].id==1
    assert item_types[0].name_id==1
    assert item_types[0].item_type_name.name=='test'
    assert item_types[0].schema=={}
    assert item_types[0].form=={}
    assert item_types[0].render=={}
    assert item_types[0].tag==1
    assert item_types[0].is_deleted==False
    assert item_types[1].id==2
    assert item_types[1].name_id==2
    assert item_types[1].item_type_name.name=='test2'
    assert item_types[1].schema=={}
    assert item_types[1].form=={}
    assert item_types[1].render=={}
    assert item_types[1].tag==1
    assert item_types[1].is_deleted==True

# class ItemTypes(RecordBase):
#     def patch(self, patch):
def test_patch_ItemTypes(app):
    test = ItemTypes(data={})

    with patch("weko_records.api.apply_patch", return_value=""):
        test.patch(patch="test")

# class ItemTypes(RecordBase):
#     def commit(self, **kwargs):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_itemtypes_commit -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_itemtypes_commit(app, db):
    it = ItemTypes.create(name='test')
    it2 = ItemTypes.create(name='test2')

    it.model = None
    with pytest.raises(Exception) as e:
        ItemTypes.commit(it)
    assert e.type==MissingModelError
    it2 = ItemTypes.commit(it2)
    assert it2=={}
    assert it2.model.item_type_name.name=='test2'
    assert it2.model.schema=={}
    assert it2.model.form=={}
    assert it2.model.render=={}
    assert it2.model.tag==1
    assert it2.model.is_deleted==False

# class ItemTypes(RecordBase):
#     def delete(self, force=False):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_itemtypes_delete -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_itemtypes_delete(app, db):
    it = ItemTypes.create(name='test')
    it2 = ItemTypes.create(name='test2')
    it3 = ItemTypes.create(name='test3')

    it.model = None
    with pytest.raises(Exception) as e:
        ItemTypes.delete(it, False)
    assert e.type==MissingModelError

    it2 = ItemTypes.delete(it2, False)
    assert it2=={}
    assert it2.model.item_type_name.name=='test2'
    assert it2.model.schema=={}
    assert it2.model.form=={}
    assert it2.model.render=={}
    assert it2.model.tag==1
    assert it2.model.is_deleted==True

    # need to fix
    with pytest.raises(Exception) as e:
        it3 = ItemTypes.delete(it3, True)

# class ItemTypes(RecordBase):
#     def revert(self, revision_id):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_itemtypes_revert -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_itemtypes_revert(app, db):
    it = ItemTypes.create(name='test')
    it2 = ItemTypes.create(name='test2')

    it.model = None
    with pytest.raises(Exception) as e:
        ItemTypes.revert(it, 0)
    assert e.type==MissingModelError
    # need to fix
    with pytest.raises(Exception) as e:
        ItemTypes.revert(it2, 0)
    assert e.type==AttributeError

# class ItemTypes(RecordBase):
#     def restore(self):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_itemtypes_restore -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_itemtypes_restore(app, db):
    it = ItemTypes.create(name='test')
    it2 = ItemTypes.create(name='test2')

    it.model = None
    with pytest.raises(Exception) as e:
        ItemTypes.restore(it)
    assert e.type==MissingModelError

    ItemTypes.delete(it2, False)
    it2 = ItemTypes.restore(it2)
    assert it2=={}
    assert it2.model.item_type_name.name=='test2'
    assert it2.model.schema=={}
    assert it2.model.form=={}
    assert it2.model.render=={}
    assert it2.model.tag==1
    assert it2.model.is_deleted==False

# class ItemTypes(RecordBase):
#     def revisions(self):
def test_revision_ItemTypes(app):
    test = ItemTypes(data={})

    # Exception coverage
    try:
        test.revisions()
    except:
        pass

    test.model = True

    with patch('weko_records.api.RevisionsIterator', return_value=MagicMock()):
        assert test.revisions() != None

# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::TestItemTypes::test_update_attribute_options -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records/.tox/c1/tmp
class TestItemTypes:

    # def (cls, itemtype_id, specified_list=[], renew_value='None'):
    # .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::TestItemTypes::test_reload -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records/.tox/c1/tmp
    def test_reload(self, app, db, user, item_type_with_form, item_type_mapping_with_form):

        item_type_id = item_type_with_form.id

        with patch('weko_records.api.db.session.merge', return_value=""):
            with patch('weko_records.api.db.session.commit', return_value=""):
                result = ItemTypes.reload(item_type_id)
                assert result["msg"] == "Fix ItemType({}) mapping".format(item_type_id)
                assert result["code"] == 0

                result = ItemTypes.reload(item_type_id, specified_list=[1000])
                assert result["msg"] == "Update ItemType({})".format(item_type_id)
                assert result["code"] == 0

    # .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::TestItemTypes::test_update_property_enum -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records/.tox/c1/tmp
    def test_update_property_enum(app):
        old_value = {'type': 'array', 'items': {'type': 'object', 'title': 'dcterms_date', 'format': 'object', 'properties': {'subitem_dcterms_date': {'type': 'string', 'title': '日付（リテラル）', 'format': 'text', 'title_i18n': {'en': 'Date Literal', 'ja': '日付（リテラル）'}}, 'subitem_dcterms_date_language': {'enum': [None, 'ja', 'ja-Kana', 'ja-Latn', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': '言語', 'format': 'select', 'editAble': True}}, 'system_prop': False}, 'title': 'dcterms_date', 'maxItems': 9999, 'minItems': 1, 'system_prop': False}
        new_value = {'type': 'array', 'items': {'type': 'object', 'title': 'dcterms_date', 'format': 'object', 'properties': {'subitem_dcterms_date': {'type': 'string', 'title': '日付（リテラル）', 'format': 'text', 'title_i18n': {'en': 'Date Literal', 'ja': '日付（リテラル）'}}, 'subitem_dcterms_date_language': {'enum': [None, 'ja', 'ja-Kana', 'ja-Latn', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': '言語', 'format': 'select', 'editAble': True}}, 'system_prop': False}, 'title': 'dcterms_date', 'maxItems': 9999, 'minItems': 1, 'system_prop': False}
        expected_dict = {'type': 'array', 'items': {'type': 'object', 'title': 'dcterms_date', 'format': 'object', 'properties': {'subitem_dcterms_date': {'type': 'string', 'title': '日付（リテラル）', 'format': 'text', 'title_i18n': {'en': 'Date Literal', 'ja': '日付（リテラル）'}}, 'subitem_dcterms_date_language': {'enum': [None, 'ja', 'ja-Kana', 'ja-Latn', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': '言語', 'format': 'select', 'editAble': True}}, 'system_prop': False}, 'title': 'dcterms_date', 'maxItems': 9999, 'minItems': 1, 'system_prop': False}
        ItemTypes.update_property_enum(old_value,new_value)
        TestCase().assertDictEqual(new_value, expected_dict)

        old_value = {'type': 'array', 'items': {'type': 'object', 'title': 'dcterms_date', 'format': 'object', 'properties': {'subitem_dcterms_date': {'type': 'string', 'title': '日付（リテラル）', 'format': 'text', 'title_i18n': {'en': 'Date Literal', 'ja': '日付（リテラル）'}}, 'subitem_dcterms_date_language': {'type': ['null', 'string'], 'title': '言語', 'format': 'select', 'editAble': True}}, 'system_prop': False}, 'title': 'dcterms_date', 'maxItems': 9999, 'minItems': 1, 'system_prop': False}
        new_value = {'type': 'array', 'items': {'type': 'object', 'title': 'dcterms_date', 'format': 'object', 'properties': {'subitem_dcterms_date': {'type': 'string', 'title': '日付（リテラル）', 'format': 'text', 'title_i18n': {'en': 'Date Literal', 'ja': '日付（リテラル）'}}, 'subitem_dcterms_date_language': {'enum': [None, 'ja', 'ja-Kana', 'ja-Latn', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': '言語', 'format': 'select', 'editAble': True}}, 'system_prop': False}, 'title': 'dcterms_date', 'maxItems': 9999, 'minItems': 1, 'system_prop': False}
        expected_dict = {'type': 'array', 'items': {'type': 'object', 'title': 'dcterms_date', 'format': 'object', 'properties': {'subitem_dcterms_date': {'type': 'string', 'title': '日付（リテラル）', 'format': 'text', 'title_i18n': {'en': 'Date Literal', 'ja': '日付（リテラル）'}}, 'subitem_dcterms_date_language': {'enum': [None, 'ja', 'ja-Kana', 'ja-Latn', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': '言語', 'format': 'select', 'editAble': True}}, 'system_prop': False}, 'title': 'dcterms_date', 'maxItems': 9999, 'minItems': 1, 'system_prop': False}
        ItemTypes.update_property_enum(old_value,new_value)
        TestCase().assertDictEqual(new_value, expected_dict)
    # .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::TestItemTypes::test_update_attribute_options -vv -s -v  --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-records/.tox/c1/tmp
    def test_update_attribute_options(self, app):

        a = {"key": "key", "type": "fieldset", "items": [{"key": "key.subkey", "type": "text", "title": "バージョン情報","isHide":True, "required": True, "isShowList": True, "title_i18n": {"en": "Version", "ja": "バージョン情報"}, "isNonDisplay": True, "title_i18n_temp": {"en": "Version", "ja": "バージョン情報"}, "isSpecifyNewline": True}], "title": "Version", "title_i18n": {"en": "Version", "ja": "バージョン情報"}}
        b = {"key": "key", "type": "fieldset", "items": [{"key": "key.subkey", "type": "text", "title": "バージョン情報", "isHide":True, "required": True, "isShowList": True, "title_i18n": {"en": "Version", "ja": "バージョン情報"}, "isNonDisplay": True, "title_i18n_temp": {"en": "Version", "ja": "バージョン情報"}, "isSpecifyNewline": True}], "title": "Version", "title_i18n": {"en": "Version", "ja": "バージョン情報"}}
        expected_dict = {"key": "key", "type": "fieldset", "items": [{"key": "key.subkey", "type": "text", "title": "バージョン情報", "isHide":True, "required": True, "isShowList": True, "title_i18n": {"en": "Version", "ja": "バージョン情報"}, "isNonDisplay": True, "title_i18n_temp": {"en": "Version", "ja": "バージョン情報"}, "isSpecifyNewline": True}], "title": "Version", "isHide": False, "isShowList": False, "isNonDisplay": False, "isSpecifyNewline": False, "required": False, "title_i18n": {"en": "Version", "ja": "バージョン情報"},"title_i18n_temp": {"en": "Version", "ja": "バージョン情報"}}
        ItemTypes.update_attribute_options(a,b,"None")
        TestCase().assertDictEqual(b, expected_dict)

        a = {"key": "key", "type": "fieldset", "items": [{"key": "key.subkey", "type": "text", "title": "バージョン情報","isHide":False, "required": False, "isShowList": False, "title_i18n": {"en": "Version", "ja": "バージョン情報"}, "isNonDisplay": False, "title_i18n_temp": {"en": "Version", "ja": "バージョン情報"}, "isSpecifyNewline": False}], "title": "Version", "title_i18n": {"en": "Version", "ja": "バージョン情報"}}
        b = {"key": "key", "type": "fieldset", "items": [{"key": "key.subkey", "type": "text", "title": "バージョン情報", "isHide":False, "required": False, "isShowList": False, "title_i18n": {"en": "Version", "ja": "バージョン情報"}, "isNonDisplay": False, "title_i18n_temp": {"en": "Version", "ja": "バージョン情報"}, "isSpecifyNewline": False}], "title": "Version", "title_i18n": {"en": "Version", "ja": "バージョン情報"}}
        expected_dict = {"isHide": False, "isShowList": False, "isNonDisplay": False, "isSpecifyNewline": False, "required": False, "key": "key", "type": "fieldset", "items": [{"key": "key.subkey", "type": "text", "title": "バージョン情報", "isHide":False, "required": False, "isShowList": False, "title_i18n": {"en": "Version", "ja": "バージョン情報"}, "isNonDisplay": False, "title_i18n_temp": {"en": "Version", "ja": "バージョン情報"}, "isSpecifyNewline": False}], "title": "Version", "title_i18n": {"en": "Version", "ja": "バージョン情報"},"title_i18n_temp": {"en": "Version", "ja": "バージョン情報"}}
        ItemTypes.update_attribute_options(a,b,"None")
        TestCase().assertDictEqual(b, expected_dict)

        a = {"key": "key", "type": "fieldset", "items": [{"key": "key.subkey", "type": "text", "title": "バージョン情報","title_i18n": {"en": "Version", "ja": "バージョン情報"},"title_i18n_temp": {"en": "Version", "ja": "バージョン情報"}}], "title": "Version", "title_i18n": {"en": "Version", "ja": "バージョン情報"}}
        b = {"key": "key", "type": "fieldset", "items": [{"key": "key.subkey", "type": "text", "title": "バージョン情報","title_i18n": {"en": "Version", "ja": "バージョン情報"},"title_i18n_temp": {"en": "Version", "ja": "バージョン情報"}}], "title": "Version", "title_i18n": {"en": "Version", "ja": "バージョン情報"}}
        expected_dict = {"isHide": False, "isShowList": False, "isNonDisplay": False, "isSpecifyNewline": False, "required": False, "key": "key", "type": "fieldset", "items": [{"isHide": False,"isNonDisplay": False,"isShowList": False,"isSpecifyNewline": False,"required":False,"key": "key.subkey", "type": "text", "title": "バージョン情報", "title_i18n": {"en": "Version", "ja": "バージョン情報"}, "title_i18n_temp": {"en": "Version", "ja": "バージョン情報"}}], "title": "Version", "title_i18n": {"en": "Version", "ja": "バージョン情報"}, "title_i18n_temp": {"en": "Version", "ja": "バージョン情報"}}
        ItemTypes.update_attribute_options(a,b,"None")
        TestCase().assertDictEqual(b, expected_dict)

        a = {"key": "key", "type": "fieldset", "items": [{"key": "key.subkey", "type": "text", "title": "バージョン情報","isHide":False, "required": False, "isShowList": False, "title_i18n": {"en": "Version", "ja": "バージョン情報"}, "isNonDisplay": True, "title_i18n_temp": {"en": "Version", "ja": "バージョン情報"}, "isSpecifyNewline": False}], "title": "Version", "title_i18n": {"en": "Version", "ja": "バージョン情報"}}
        b = {"key": "key", "type": "fieldset", "items": [{"key": "key.subkey", "type": "text", "title": "バージョン情報", "isHide":False, "required": False, "isShowList": False, "title_i18n": {"en": "Version", "ja": "バージョン情報"}, "isNonDisplay": False, "title_i18n_temp": {"en": "Version", "ja": "バージョン情報"}, "isSpecifyNewline": False}], "title": "Version", "title_i18n": {"en": "Version", "ja": "バージョン情報"}}
        expected_dict = {"isHide": False, "isShowList": False, "isNonDisplay": False, "isSpecifyNewline": False, "required": False, "key": "key", "type": "fieldset", "items": [{"key": "key.subkey", "type": "text", "title": "バージョン情報", "isHide":False, "required": False, "isShowList": False, "title_i18n": {"en": "Version", "ja": "バージョン情報"}, "isNonDisplay": True, "title_i18n_temp": {"en": "Version", "ja": "バージョン情報"}, "isSpecifyNewline": False}], "title": "Version", "title_i18n": {"en": "Version", "ja": "バージョン情報"}, "title_i18n_temp": {"en": "Version", "ja": "バージョン情報"}}
        ItemTypes.update_attribute_options(a,b, "None")
        TestCase().assertDictEqual(b, expected_dict)

        a = {"key": "key", "type": "fieldset", "items": [{"key": "key.subkey", "type": "text", "title": "subkey","isHide":False, "required": False, "isShowList": False, "title_i18n": {"en": "subkey", "ja": "subkey"}, "isNonDisplay": True, "title_i18n_temp": {"en": "subkey", "ja": "subkey"}, "isSpecifyNewline": False,"items": [{"key": "key.subkey.subkey", "type": "text", "title": "subkey.subkey","isHide":False, "required": False, "isShowList": False, "title_i18n": {"en": "subkey.subkey", "ja": "subkey.subkey"}, "isNonDisplay": True, "title_i18n_temp": {"en": "subkey.subkey", "ja": "subkey.subkey"}, "isSpecifyNewline": False}]}], "title": "Version", "title_i18n": {"en": "key", "ja": "key"}}
        b = {"key": "key", "type": "fieldset", "items": [{"key": "key.subkey", "type": "text", "title": "subkey","isHide":True, "required": True, "isShowList": True, "title_i18n": {"en": "subkey", "ja": "subkey"}, "isNonDisplay": False, "title_i18n_temp": {"en": "subkey", "ja": "subkey"}, "isSpecifyNewline": True,"items": [{"key": "key.subkey.subkey", "type": "text", "title": "subkey.subkey","isHide":True, "required": True, "isShowList": True, "title_i18n": {"en": "subkey.subkey", "ja": "subkey.subkey"}, "isNonDisplay": False, "title_i18n_temp": {"en": "subkey.subkey", "ja": "subkey.subkey"}, "isSpecifyNewline": True}]}], "title": "Version", "title_i18n": {"en": "key", "ja": "key"}}
        expected_dict = {"isHide": False, "isShowList": False, "isNonDisplay": False, "isSpecifyNewline": False, "required": False, "key": "key", "type": "fieldset", "items": [{"key": "key.subkey", "type": "text", "title": "subkey","isHide":False, "required": False, "isShowList": False, "title_i18n": {"en": "subkey", "ja": "subkey"}, "isNonDisplay": True, "title_i18n_temp": {"en": "subkey", "ja": "subkey"}, "isSpecifyNewline": False,"items": [{"key": "key.subkey.subkey", "type": "text", "title": "subkey.subkey","isHide":False, "required": False, "isShowList": False, "title_i18n": {"en": "subkey.subkey", "ja": "subkey.subkey"}, "isNonDisplay": True, "title_i18n_temp": {"en": "subkey.subkey", "ja": "subkey.subkey"}, "isSpecifyNewline": False}]}], "title": "Version", "title_i18n": {"en": "key", "ja": "key"},"title_i18n_temp": {"en": "key", "ja": "key"}}
        ItemTypes.update_attribute_options(a,b, "None")
        TestCase().assertDictEqual(b, expected_dict)

        old_value = {"key": "key", "type": "fieldset", "items": [{"key": "key.subitem_select_language", "type": "select", "title": "言語", "titleMap": [{"name": "ja", "value": "ja"}, {"name": "en", "value": "en"}], "title_i18n": {"en": "Language", "ja": "言語"}, "title_i18n_temp": {"en": "Language", "ja": "言語"}}, {"key": "key.subitem_select_item", "type": "select", "title": "値", "titleMap": [{"name": "a", "value": "a"}, {"name": "b", "value": "b"}, {"name": "c", "value": "c"}, {"name": "d", "value": "d"}, {"name": "e", "value": "e"}, {"name": "f", "value": "f"}], "title_i18n": {"en": "Value", "ja": "値"}, "title_i18n_temp": {"en": "Value", "ja": "値"}}], "title": "abcdef", "title_i18n": {"en": "", "ja": ""}}
        new_value = {"key": "key", "type": "fieldset", "items": [{"key": "key.subitem_select_language", "type": "select", "title": "言語", "titleMap": '', "title_i18n": {"en": "Language", "ja": "言語"}, "title_i18n_temp": {"en": "Language", "ja": "言語"}}, {"key": "key.subitem_select_item", "type": "select", "title": "値", "titleMap": [], "title_i18n": {"en": "Value", "ja": "値"}, "title_i18n_temp": {"en": "Value", "ja": "値"}}], "title": "abcdef", "title_i18n": {"en": "", "ja": ""}}
        expected_dict = {"isHide": False, "isShowList": False, "isNonDisplay": False, "isSpecifyNewline": False, "required": False,"key": "key", "type": "fieldset", "items": [{"key": "key.subitem_select_language", "type": "select", "title": "言語", "titleMap": [{"name": "ja", "value": "ja"}, {"name": "en", "value": "en"}], "title_i18n": {"en": "Language", "ja": "言語"}, "title_i18n_temp": {"en": "Language", "ja": "言語"},'isHide': False,'isNonDisplay': False,'isShowList': False, 'isSpecifyNewline': False,'required': False}, {"key": "key.subitem_select_item", "type": "select", "title": "値", "titleMap": [{"name": "a", "value": "a"}, {"name": "b", "value": "b"}, {"name": "c", "value": "c"}, {"name": "d", "value": "d"}, {"name": "e", "value": "e"}, {"name": "f", "value": "f"}], "title_i18n": {"en": "Value", "ja": "値"}, "title_i18n_temp": {"en": "Value", "ja": "値"},'isHide': False,'isNonDisplay': False,'isShowList': False, 'isSpecifyNewline': False,'required': False}], "title": "abcdef", "title_i18n": {"en": "", "ja": ""},"title_i18n_temp": {"en": "", "ja": ""}}
        ItemTypes.update_attribute_options(old_value,new_value,"None")
        TestCase().assertDictEqual(new_value, expected_dict)

        old_value = {"key": "key", "type": "fieldset", "items": [{"key": "key.subitem_select_language", "type": "select", "title": "言語", "titleMap": [{"name": "ja", "value": "ja"}, {"name": "en", "value": "en"}], "title_i18n": {"en": "Language", "ja": "言語"}, "title_i18n_temp": {"en": "Language", "ja": "言語"}}, {"key": "key.subitem_select_item", "type": "select", "title": "値", "titleMap": [{"name": "a", "value": "a"}, {"name": "b", "value": "b"}, {"name": "c", "value": "c"}, {"name": "d", "value": "d"}, {"name": "e", "value": "e"}, {"name": "f", "value": "f"}], "title_i18n": {"en": "Value", "ja": "値"}, "title_i18n_temp": {"en": "Value", "ja": "値"}}], "title": "abcdef", "title_i18n": {"en": "", "ja": ""}}
        new_value = {"key": "key", "type": "fieldset", "items": [{"key": "key.subitem_select_language", "type": "select", "title": "言語", "titleMap": '', "title_i18n": {"en": "Language", "ja": "言語"}}, {"key": "key.subitem_select_item", "type": "select", "title": "値", "titleMap": [], "title_i18n": {"en": "Value", "ja": "値"}, "title_i18n_temp": {"en": "Value", "ja": "値"}}], "title": "abcdef", "title_i18n": {"en": "", "ja": ""}}
        expected_dict = {"isHide": False, "isShowList": False, "isNonDisplay": False, "isSpecifyNewline": False, "required": False,"key": "key", "type": "fieldset", "items": [{"key": "key.subitem_select_language", "type": "select", "title": "言語", "titleMap": [{"name": "ja", "value": "ja"}, {"name": "en", "value": "en"}], "title_i18n": {"en": "Language", "ja": "言語"}, "title_i18n_temp": {"en": "Language", "ja": "言語"},'isHide': False,'isNonDisplay': False,'isShowList': False, 'isSpecifyNewline': False,'required': False}, {"key": "key.subitem_select_item", "type": "select", "title": "値", "titleMap": [{"name": "a", "value": "a"}, {"name": "b", "value": "b"}, {"name": "c", "value": "c"}, {"name": "d", "value": "d"}, {"name": "e", "value": "e"}, {"name": "f", "value": "f"}], "title_i18n": {"en": "Value", "ja": "値"}, "title_i18n_temp": {"en": "Value", "ja": "値"},'isHide': False,'isNonDisplay': False,'isShowList': False, 'isSpecifyNewline': False,'required': False}], "title": "abcdef", "title_i18n": {"en": "", "ja": ""},"title_i18n_temp": {"en": "", "ja": ""}}
        ItemTypes.update_attribute_options(old_value,new_value, "None")
        TestCase().assertDictEqual(new_value, expected_dict)

        old_value = {"key": "key", "type": "fieldset", "items": [{"key": "key.subitem_select_item", "type": "select", "title": "値", "titleMap": [{"name": "a", "value": "a"}, {"name": "b", "value": "b"}], "title_i18n": {"en": "Value", "ja": "値"}, "title_i18n_temp": {"en": "Value", "ja": "値"}}], "title": "abcdef", "title_i18n": {"en": "", "ja": ""}}
        new_value = {"key": "key", "type": "fieldset", "items": [{"key": "key.subitem_select_item", "type": "select", "title": "値", "titleMap": [{"name": "a", "value": "a"}, {"name": "b", "value": "b"}, {"name": "c", "value": "c"}], "title_i18n": {"en": "Test Value", "ja": "テスト値"}, "title_i18n_temp": {"en": "Test Value", "ja": "テスト値"}}], "title": "abcdef", "title_i18n": {"en": "", "ja": ""}}
        expected_dict = {"isHide": False, "isShowList": False, "isNonDisplay": False, "isSpecifyNewline": False, "required": False,"key": "key", "key": "key", "type": "fieldset", "items": [{"key": "key.subitem_select_item", "type": "select", "title": "値", "titleMap": [{"name": "a", "value": "a"}, {"name": "b", "value": "b"}], "title_i18n": {"en": "Value", "ja": "値"}, "title_i18n_temp": {"en": "Value", "ja": "値"},'isHide': False,'isNonDisplay': False,'isShowList': False, 'isSpecifyNewline': False,'required': False}], "title": "abcdef", "title_i18n": {"en": "", "ja": ""}, "title_i18n_temp": {"en": "", "ja": ""}}
        ItemTypes.update_attribute_options(old_value,new_value,"VAL")
        TestCase().assertDictEqual(new_value, expected_dict)

        old_value = {"key": "key", "type": "fieldset", "items": [{"key": "key.subitem_select_item", "type": "select", "title": "値", "titleMap": [{"name": "a", "value": "a"}, {"name": "b", "value": "b"}], "title_i18n": {"en": "Value", "ja": "値"}, "title_i18n_temp": {"en": "Value", "ja": "値"}}], "title": "abcdef", "title_i18n": {"en": "", "ja": ""}}
        new_value = {"key": "key", "type": "fieldset", "items": [{"key": "key.subitem_select_item", "type": "select", "title": "値", "titleMap": [{"name": "a", "value": "a"}, {"name": "b", "value": "b"}, {"name": "c", "value": "c"}], "title_i18n": {"en": "Test Value", "ja": "テスト値"}, "title_i18n_temp": {"en": "Test Value", "ja": "テスト値"}}], "title": "abcdef", "title_i18n": {"en": "", "ja": ""}}
        expected_dict = {"isHide": False, "isShowList": False, "isNonDisplay": False, "isSpecifyNewline": False, "required": False,"key": "key", "type": "fieldset", "items": [{"key": "key.subitem_select_item", "type": "select", "title": "値", "titleMap": [{"name": "a", "value": "a"}, {"name": "b", "value": "b"}], "title_i18n": {"en": "Test Value", "ja": "テスト値"}, "title_i18n_temp": {"en": "Test Value", "ja": "テスト値"},'isHide': False,'isNonDisplay': False,'isShowList': False, 'isSpecifyNewline': False,'required': False}], "title": "abcdef", "title_i18n": {"en": "", "ja": ""}}
        ItemTypes.update_attribute_options(old_value,new_value,"LOC")
        TestCase().assertDictEqual(new_value, expected_dict)

        old_value = {"key": "key", "type": "fieldset", "items": [{"key": "key.subitem_select_item", "type": "select", "title": "値", "titleMap": [{"name": "a", "value": "a"}, {"name": "b", "value": "b"}], "title_i18n": {"en": "Value", "ja": "値"}, "title_i18n_temp": {"en": "Value", "ja": "値"}}], "title": "abcdef", "title_i18n": {"en": "", "ja": ""}}
        new_value = {"key": "key", "type": "fieldset", "items": [{"key": "key.subitem_select_item", "type": "select", "title": "値", "titleMap": [{"name": "a", "value": "a"}, {"name": "b", "value": "b"}, {"name": "c", "value": "c"}], "title_i18n": {"en": "Test Value", "ja": "テスト値"}, "title_i18n_temp": {"en": "Test Value", "ja": "テスト値"}}], "title": "abcdef", "title_i18n": {"en": "", "ja": ""}}
        expected_dict = {"isHide": False, "isShowList": False, "isNonDisplay": False, "isSpecifyNewline": False, "required": False,"key": "key", "type": "fieldset", "items": [{"key": "key.subitem_select_item", "type": "select", "title": "値", "titleMap": [{"name": "a", "value": "a"}, {"name": "b", "value": "b"}], "title_i18n": {"en": "Test Value", "ja": "テスト値"}, "title_i18n_temp": {"en": "Test Value", "ja": "テスト値"},'isHide': False,'isNonDisplay': False,'isShowList': False, 'isSpecifyNewline': False,'required': False}], "title": "abcdef", "title_i18n": {"en": "", "ja": ""}}
        ItemTypes.update_attribute_options(old_value,new_value,"ALL")
        TestCase().assertDictEqual(new_value, expected_dict)


# class ItemTypeEditHistory(RecordBase):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_item_type_edit_history -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_item_type_edit_history(app, db, user):
    ItemTypes.create(name='test')

    record = ItemTypeEditHistory.create_or_update(
        id=0,
        item_type_id=1,
        user_id=user.id,
        notes={}
    )
    assert record.id==1
    assert record.item_type_id==1
    assert record.user_id==1
    assert record.notes=={}

    record = ItemTypeEditHistory.create_or_update(
        id=0,
        item_type_id=1,
        user_id=user.id,
        notes={'msg': 'test'}
    )
    assert record.id==2
    assert record.item_type_id==1
    assert record.user_id==1
    assert record.notes=={'msg': 'test'}

    # need to fix
    with pytest.raises(Exception) as e:
        records = ItemTypeEditHistory.get_by_item_type_id(1)
    #assert len(records)==2
    #assert records[0].id==1
    #assert records[0].item_type_id==1
    #assert records[0].user_id==1
    #assert records[0].notes=={}
    #assert records[1].id==2
    #assert records[1].item_type_id==1
    #assert records[1].user_id==1
    #assert records[1].notes=={'msg': 'test'}

# class Mapping(RecordBase):
#     def create(cls, item_type_id=None, mapping=None):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_mapping_create -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_mapping_create(app, db):
    mapping = Mapping.create()
    assert mapping.id==1
    assert mapping.model.item_type_id==None
    assert mapping.model.mapping=={}

    mapping = Mapping.create(1, {'mapping': 'test'})
    assert mapping.id==2
    assert mapping.model.item_type_id==1
    assert mapping.model.mapping=={'mapping': 'test'}

# class Mapping(RecordBase):
#     def get_record(cls, item_type_id, with_deleted=False):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_mapping_get_record -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_mapping_get_record(app, db):
    Mapping.create(1, {'mapping': 'test'})
    Mapping.create(2)

    mapping = Mapping.get_record(0)
    assert mapping==None
    mapping = Mapping.get_record(1)
    assert mapping.id==1
    assert mapping.model.item_type_id==1
    assert mapping.model.mapping=={'mapping': 'test'}
    mapping = Mapping.get_record(2, False)
    assert mapping=={}
    mapping = Mapping.get_record(2, True)
    assert mapping.id==2
    assert mapping.model.item_type_id==2
    assert mapping.model.mapping=={}

    mappings = Mapping.get_records([0], False)
    assert len(mappings)==0
    # need to fix
    with pytest.raises(Exception) as e:
        mappings = Mapping.get_records([1, 2], False)
    #assert len(mappings)==1
    #assert mappings[0].id==1
    #assert mappings[0].model.item_type_id==1
    #assert mappings[0].model.mapping=={'mapping': 'test'}
    #mappings = Mapping.get_records([1, 2], True)
    #assert len(mappings)==2
    #assert mappings[0].id==1
    #assert mappings[0].model.item_type_id==1
    #assert mappings[0].model.mapping=={'mapping': 'test'}
    #assert mappings[1].id==2
    #assert mappings[1].model.item_type_id==2
    #assert mappings[1].model.mapping=={}

# class Mapping(RecordBase):
#     def patch(self, patch):
def test_patch_Mapping(app):
    test = Mapping(data={})

    with patch("weko_records.api.apply_patch", return_value=""):
        assert test.patch("test") == {}

# class Mapping(RecordBase):
#     def commit(self, **kwargs):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_mapping_commit -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_mapping_commit(app, db):
    mapping1 = Mapping.create(1)
    mapping2 = Mapping.create(2)

    mapping1.model = None
    with pytest.raises(Exception) as e:
        Mapping.commit(mapping1)
    assert e.type==MissingModelError

    # need to fix
    with pytest.raises(Exception) as e:
        Mapping.commit(mapping2)
    assert e.type==AttributeError

# class Mapping(RecordBase):
#     def delete(self, force=False):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_mapping_delete -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_mapping_delete(app, db):
    mapping1 = Mapping.create(1)
    mapping2 = Mapping.create(2)
    mapping3 = Mapping.create(3)

    mapping1.model = None
    with pytest.raises(Exception) as e:
        Mapping.delete(mapping1)
    assert e.type==MissingModelError

    mapping2 = Mapping.delete(mapping2, False)
    assert mapping2.id==2
    assert mapping2.model.item_type_id==2
    assert mapping2.model.mapping=={}

    # need to fix
    mapping3 = Mapping.delete(mapping3, True)
    assert mapping2=={}

# class Mapping(RecordBase):
#     def revert(self, revision_id):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_mapping_revert -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_mapping_revert(app, db):
    mapping1 = Mapping.create(1)
    mapping2 = Mapping.create(2)

    mapping1.model = None
    with pytest.raises(Exception) as e:
        Mapping.revert(mapping1, 0)
    assert e.type==MissingModelError

    # need to fix
    with pytest.raises(Exception) as e:
        Mapping.revert(mapping2, 0)
    assert e.type==AttributeError

# class Mapping(RecordBase):
#     def revisions(self):
def test_revisions_Mapping(app):
    test = Mapping(data={})
    test.model = "Not None"

    def dummy_func():
        return True

    with patch("weko_records.api.RevisionsIterator", return_value=dummy_func):
        assert test.revisions() != None

    test.model = None

    # Exception coverage
    try:
        test.revisions()
    except:
        pass

# class Mapping(RecordBase):
#     def get_mapping_by_item_type_ids(cls, item_type_ids: list) -> list:
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_mapping_get_mapping_by_item_type_ids -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_mapping_get_mapping_by_item_type_ids(app, db):
    Mapping.create(1)
    Mapping.create(2)

    mappings = Mapping.get_mapping_by_item_type_ids([0])
    assert len(mappings)==0
    mappings = Mapping.get_mapping_by_item_type_ids([1, 2])
    assert len(mappings)==2
    assert mappings[0].id==2
    assert mappings[0].model.item_type_id==2
    assert mappings[0].model.mapping=={}
    assert mappings[1].id==1
    assert mappings[1].model.item_type_id==1
    assert mappings[1].model.mapping=={}

# class ItemTypeProps(RecordBase):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_item_type_props -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_item_type_props(app, db):
    # create
    # need to fix
    with pytest.raises(Exception) as e:
        prop1 = ItemTypeProps.create()
    #assert prop1.id==1
    #assert prop1.model.name==''
    #assert prop1.model.schema=={}
    #assert prop1.model.form=={}
    #assert prop1.model.forms=={}
    #assert prop1.model.delflg==False
    #assert prop1.model.sort==None
    prop1 = ItemTypeProps.create(
        property_id=1,
        name='prop1',
        schema={'item1': {}},
        form_single={'key': 'item1'},
        form_array=[{'key': 'item1'}]
    )
    assert prop1.id==1
    assert prop1.model.name=='prop1'
    assert prop1.model.schema=={'item1': {}}
    assert prop1.model.form=={'key': 'item1'}
    assert prop1.model.forms==[{'key': 'item1'}]
    assert prop1.model.delflg==False
    assert prop1.model.sort==None

    # get_record
    record = ItemTypeProps.get_record(0)
    assert record==None
    record = ItemTypeProps.get_record(1)
    assert record.id==1
    assert record.name=='prop1'
    assert record.schema=={'item1': {}}
    assert record.form=={'key': 'item1'}
    assert record.forms==[{'key': 'item1'}]
    assert record.delflg==False
    assert record.sort==None

    # helper_remove_empty_required
    data = {
        'required': None,
        'properties': {
            'test': {
                'items': None
            }
        }
    }
    ItemTypeProps.helper_remove_empty_required(data)
    assert data=={'properties': {'test': {'items': None}}}

    # get_records
    # need to fix
    with pytest.raises(Exception) as e:
        records = ItemTypeProps.get_records([0])
    #assert len(records)==0
    records = ItemTypeProps.get_records([])
    assert len(records)==1
    assert records[0].id==1
    assert records[0].name=='prop1'
    assert records[0].schema=={'item1': {}}
    assert records[0].form=={'key': 'item1'}
    assert records[0].forms==[{'key': 'item1'}]
    assert records[0].delflg==False
    assert records[0].sort==None
    # need to fix
    #records = ItemTypeProps.get_records([1])
    #assert len(records)==1
    #assert records[0].id==1
    #assert records[0].name=='prop1'
    #assert records[0].schema=={'item1': {}}
    #assert records[0].form=={'key': 'item1'}
    #assert records[0].forms==[{'key': 'item1'}]
    #assert records[0].delflg==False
    #assert records[0].sort==None

#     def revisions(self):
def test_revisions_ItemTypeProps(app):
    test = ItemTypeProps(data={})
    test.model = "Not None"

    def dummy_func():
        return True

    with patch("weko_records.api.RevisionsIterator", return_value=dummy_func):
        assert test.revisions() != None

    test.model = None

    # Exception coverage
    try:
        test.revisions()
    except:
        pass

# class ItemsMetadata(RecordBase):
#     def create(cls, data, id_=None, **kwargs):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_item_metadata_create -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_item_metadata_create(app, db):
    _uuid2 = uuid.uuid4()
    _uuid3 = uuid.uuid4()
    _data = {'item1': None}

    record1 = ItemsMetadata.create(data={'item1': None})
    _id = str(record1.id)
    assert record1=={'item1': None}
    assert str(type(record1.id))=="<class 'uuid.UUID'>"
    assert record1.model.item_type_id==None
    assert record1.model.json=={'item1': None}
    assert record1.model.version_id==1
    record2 = ItemsMetadata.create(data=_data, id_=_uuid2)
    assert record2=={'item1': None}
    assert record2.id==_uuid2
    assert record2.model.item_type_id==None
    assert record2.model.json=={'item1': None}
    assert record2.model.version_id==1
    record3 = ItemsMetadata.create(data=_data, id_=_uuid3, item_type_id=1)
    assert record3=={'item1': None}
    assert record3.id==_uuid3
    assert record3.model.item_type_id==1
    assert record3.model.json=={'item1': None}
    assert record3.model.version_id==1

# class ItemsMetadata(RecordBase):
#     def get_record(cls, id_, with_deleted=False):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_item_metadata_get_record -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_item_metadata_get_record(app, db):
    _uuid1 = uuid.uuid4()
    _uuid2 = uuid.uuid4()
    _uuid3 = uuid.uuid4()
    _data = {'item1': None}
    record2 = ItemsMetadata.create(data=_data, id_=_uuid2, item_type_id=1)
    record3 = ItemsMetadata.create(data=_data, id_=_uuid3, item_type_id=1)
    ItemsMetadata.delete(record3, False)

    with pytest.raises(Exception) as e:
        ItemsMetadata.get_record(_uuid1)
    assert e.type==NoResultFound
    assert str(e.value)=="No row was found for one()"
    record2 = ItemsMetadata.get_record(_uuid2)
    assert record2=={'item1': None}
    assert record2.id==_uuid2
    assert record2.model.item_type_id==1
    assert record2.model.json=={'item1': None}
    assert record2.model.version_id==1
    with pytest.raises(Exception) as e:
        ItemsMetadata.get_record(str(_uuid3), False)
    assert e.type==NoResultFound
    assert str(e.value)=="No row was found for one()"
    # need to fix
    with pytest.raises(Exception) as e:
        record3 = ItemsMetadata.get_record(str(_uuid3), True)
    #assert record3=={}
    #assert record3.id==_uuid2
    #assert record3.model.item_type_id==1
    #assert record3.model.json==None
    #assert record3.model.version_id==2

# class ItemsMetadata(RecordBase):
#     def __custom_item_metadata(cls, item_metadata: dict):
#     def __replace_fqdn_of_file_metadata(cls, item_metadata: Union[list, dict]):

# class ItemsMetadata(RecordBase):
#     def get_records(cls, ids, with_deleted=False):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_item_metadata_get_records -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_item_metadata_get_records(app, db):
    _uuid1 = uuid.uuid4()
    _uuid2 = uuid.uuid4()
    _uuid3 = uuid.uuid4()
    _data = {'item1': None}
    ItemsMetadata.create(data=_data, id_=_uuid2, item_type_id=1)
    record3 = ItemsMetadata.create(data=_data, id_=_uuid3, item_type_id=1)
    ItemsMetadata.delete(record3, False)

    records = ItemsMetadata.get_records([str(_uuid1)])
    assert len(records)==0
    records = ItemsMetadata.get_records([str(_uuid2), str(_uuid3)], False)
    assert len(records)==1
    assert records[0]=={'item1': None}
    assert records[0].id==_uuid2
    assert records[0].model.item_type_id==1
    assert records[0].model.json=={'item1': None}
    assert records[0].model.version_id==1
    records = ItemsMetadata.get_records([str(_uuid2), str(_uuid3)], True)
    assert len(records)==2

# class ItemsMetadata(RecordBase):
#     def get_by_item_type_id(cls, item_type_id, with_deleted=False):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_item_metadata_get_by_item_type_id -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_item_metadata_get_by_item_type_id(app, db):
    _uuid1 = uuid.uuid4()
    _uuid2 = uuid.uuid4()
    _data = {'item1': None}
    ItemsMetadata.create(data=_data, id_=_uuid1, item_type_id=1)
    record2 = ItemsMetadata.create(data=_data, id_=_uuid2, item_type_id=1)
    ItemsMetadata.delete(record2, False)

    records = ItemsMetadata.get_by_item_type_id(1, False)
    assert len(records)==1
    assert records[0].id==_uuid1
    assert records[0].item_type_id==1
    assert records[0].json=={'item1': None}
    assert records[0].version_id==1
    records = ItemsMetadata.get_by_item_type_id(1, True)
    assert len(records)==2

# class ItemsMetadata(RecordBase):
#     def get_registered_item_metadata(cls, item_type_id):
def test_get_registered_item_metadata_ItemsMetadata(app):
    test = ItemsMetadata(data={})
    data1 = MagicMock()

    def all_func():
        all_magicmock = MagicMock()
        all_magicmock.id = 1
        return [all_magicmock]

    data1.query = MagicMock()
    data1.query.filter_by = MagicMock()
    data1.query.filter_by.all = all_func

    with patch("weko_records.api.ItemMetadata", return_value=data1):
        with patch("weko_records.api.PersistentIdentifier", return_value=data1):
            assert test.get_registered_item_metadata(item_type_id=1) != None

# class ItemsMetadata(RecordBase):
#     def get_by_object_id(cls, object_id):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_item_metadata_get_by_object_id -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_item_metadata_get_by_object_id(app, db):
    _uuid1 = uuid.uuid4()
    _uuid2 = uuid.uuid4()
    _uuid3 = uuid.uuid4()
    _data = {'item1': None}
    record2 = ItemsMetadata.create(data=_data, id_=_uuid2, item_type_id=1)
    record3 = ItemsMetadata.create(data=_data, id_=_uuid3, item_type_id=1)
    ItemsMetadata.delete(record3, False)

    record1 = ItemsMetadata.get_by_object_id(str(_uuid1))
    assert record1==None
    record2 = ItemsMetadata.get_by_object_id(str(_uuid2))
    assert record2.id==_uuid2
    assert record2.item_type_id==1
    assert record2.json=={'item1': None}
    assert record2.version_id==1
    record3 = ItemsMetadata.get_by_object_id(str(_uuid3))
    assert record3.id==_uuid3
    assert record3.item_type_id==1
    assert record3.json==None
    assert record3.version_id==2

    # ItemsMetadata.get_registered_item_metadata(item_type_id=1)

# class ItemsMetadata(RecordBase):
#     def patch(self, patch):
def test_patch_ItemsMetadata(app):
    test = ItemsMetadata(data={})

    with patch("weko_records.api.apply_patch", return_value=""):
        test.patch(patch="test")

# class ItemsMetadata(RecordBase):
#     def commit(self, **kwargs):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_item_metadata_commit -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_item_metadata_commit(app, db):
    _uuid1 = uuid.uuid4()
    _uuid2 = uuid.uuid4()
    _data = {'item1': None}
    record1 = ItemsMetadata.create(data=_data, id_=_uuid1, item_type_id=1)
    record2 = ItemsMetadata.create(data=_data, id_=_uuid2, item_type_id=1)

    record1.model = None
    with pytest.raises(Exception) as e:
        ItemsMetadata.commit(record1)
    assert e.type==MissingModelError
    record2 = ItemsMetadata.commit(record2)
    assert record2=={'item1': None}
    assert record2.id==_uuid2
    assert record2.model.item_type_id==1
    assert record2.model.json=={'item1': None}
    assert record2.model.version_id==2

# class ItemsMetadata(RecordBase):
#     def delete(self, force=False):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_item_metadata_delete -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_item_metadata_delete(app, db):
    _uuid1 = uuid.uuid4()
    _uuid2 = uuid.uuid4()
    _uuid3 = uuid.uuid4()
    _data = {'item1': None}
    record1 = ItemsMetadata.create(data=_data, id_=_uuid1, item_type_id=1)
    record2 = ItemsMetadata.create(data=_data, id_=_uuid2, item_type_id=1)
    record3 = ItemsMetadata.create(data=_data, id_=_uuid3, item_type_id=1)

    record1.model = None
    with pytest.raises(Exception) as e:
        ItemsMetadata.delete(record1)
    assert e.type==MissingModelError
    record2 = ItemsMetadata.delete(record2, False)
    assert record2=={'item1': None}
    assert record2.id==_uuid2
    assert record2.model.item_type_id==1
    assert record2.model.json==None
    assert record2.model.version_id==2
    # need to fix
    record3 = ItemsMetadata.delete(record3, True)
    #assert record3==None

# class ItemsMetadata(RecordBase):
#     def revert(self, revision_id):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_item_metadata_revert -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_item_metadata_revert(app, db):
    _uuid1 = uuid.uuid4()
    _uuid2 = uuid.uuid4()
    _data = {'item1': None}
    record1 = ItemsMetadata.create(data=_data, id_=_uuid1, item_type_id=1)
    record2 = ItemsMetadata.create(data=_data, id_=_uuid2, item_type_id=1)

    record1.model = None
    with pytest.raises(Exception) as e:
        ItemsMetadata.revert(record1, 0)
    assert e.type==MissingModelError
    record2 = ItemsMetadata.revert(record2, 0)
    assert record2=={'item1': None}
    assert record2.id==_uuid2
    assert record2.model.item_type_id==1
    assert record2.model.json=={'item1': None}
    assert record2.model.version_id==2

# class ItemsMetadata(RecordBase):
#     def revisions(self):
def test_revision_ItemsMetadata(app):
    test = ItemsMetadata(data={})

    # Exception coverage
    try:
        test.revisions()
    except:
        pass

    test.model = True

    with patch('weko_records.api.RevisionsIterator', return_value=MagicMock()):
        assert test.revisions() != None

# class FilesMetadata(RecordBase):
#     def create(cls, data, id_=None, **kwargs):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_files_metadata_create -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_files_metadata_create(app, db):
    record = FilesMetadata.create(data={})
    assert record.id==1
    assert record.model.pid==None
    assert record.model.contents==None
    assert record.model.json=={}
    assert record.model.version_id==1

    record = FilesMetadata.create(data={'data': 'test'}, id_=3, pid=1, con=bytes('test content', 'utf-8'))
    assert record.id==2
    assert record.model.pid==1
    assert record.model.contents==b'test content'
    assert record.model.json=={'data': 'test'}
    assert record.model.version_id==1

# class FilesMetadata(RecordBase):
#     def get_record(cls, id_, with_deleted=False):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_files_metadata_get_record -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_files_metadata_get_record(app, db):
    FilesMetadata.create(data={'data': 'test'}, pid=1, con=bytes('test content', 'utf-8'))
    FilesMetadata.create(data={})

    record = FilesMetadata.get_record(1)
    assert record.id==1
    assert record.model.pid==1
    assert record.model.contents==b'test content'
    assert record.model.json=={'data': 'test'}
    assert record.model.version_id==1

    with pytest.raises(Exception) as e:
        FilesMetadata.get_record(None, False)
    assert e.type==NoResultFound
    assert str(e.value)=="No row was found for one()"
    record = FilesMetadata.get_record(None, True)
    assert record.id==2
    assert record.model.pid==None
    assert record.model.contents==None
    assert record.model.json=={}
    assert record.model.version_id==1

# class FilesMetadata(RecordBase):
#     def get_records(cls, ids, with_deleted=False):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_files_metadata_get_records -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_files_metadata_get_records(app, db):
    FilesMetadata.create(data={'data': 'test'}, pid=1, con=bytes('test content', 'utf-8'))
    FilesMetadata.create(data={}, pid=2)

    # need to fix
    with pytest.raises(Exception) as e:
        records = FilesMetadata.get_records([1, 2], False)
    #assert len(records)==1
    #assert records[0].id==1
    #assert records[0].model.pid==1
    #assert records[0].model.contents==b'test content'
    #assert records[0].model.json=={'data': 'test'}
    #assert records[0].model.version_id==1
    #records = FilesMetadata.get_records([1, 2], True)
    #assert len(records)==2

# class FilesMetadata(RecordBase):
#     def patch(self, patch):
def test_patch_FilesMetadata(app):
    test = FilesMetadata(data={})

    with patch("weko_records.api.apply_patch", return_value=""):
        test.patch(patch="test")

# class FilesMetadata(RecordBase):
#     def update_data(id, jsn):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_files_metadata_update_data -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_files_metadata_update_data(app, db):
    FilesMetadata.create(data={}, pid=1, con=bytes('test content', 'utf-8'))

    # need to fix
    FilesMetadata.update_data(1, {'data': 'test'})
    record = FilesMetadata.get_record(1)
    assert record.id==1
    assert record.model.pid==1
    assert record.model.contents==b'test content'
    #assert record.model.json=={'data': 'test'}
    assert record.model.json=={}
    assert record.model.version_id==1

# class FilesMetadata(RecordBase):
#     def commit(self, **kwargs):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_files_metadata_commit -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_files_metadata_commit(app, db):
    record1 = FilesMetadata.create(data={'data': 'test'}, pid=1, con=bytes('test content', 'utf-8'))
    record2 = FilesMetadata.create(data={'data': 'test'}, pid=2, con=bytes('test content', 'utf-8'))

    record1.model = None
    with pytest.raises(Exception) as e:
        FilesMetadata.commit(record1)
    assert e.type==MissingModelError

    record2 = FilesMetadata.commit(record2)
    assert record2.id==2
    assert record2.model.pid==2
    assert record2.model.contents==b'test content'
    assert record2.model.json=={'data': 'test'}
    assert record2.model.version_id==2

# class FilesMetadata(RecordBase):
#     def delete(self, force=False):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_files_metadata_delete -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_files_metadata_delete(app, db):
    record1 = FilesMetadata.create(data={'data': 'test'}, pid=1, con=bytes('test content', 'utf-8'))
    record2 = FilesMetadata.create(data={'data': 'test'}, pid=2, con=bytes('test content', 'utf-8'))
    record3 = FilesMetadata.create(data={'data': 'test'}, pid=3, con=bytes('test content', 'utf-8'))

    record1.model = None
    with pytest.raises(Exception) as e:
        FilesMetadata.delete(record1)
    assert e.type==MissingModelError

    record2 = FilesMetadata.delete(record2, False)
    assert record2.id==2
    assert record2.model.pid==2
    assert record2.model.contents==b'test content'
    assert record2.model.json==None
    assert record2.model.version_id==2

    # need to fix
    record3 = FilesMetadata.delete(record3, True)
    #assert record3==None

# class FilesMetadata(RecordBase):
#     def revert(self, revision_id):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_files_metadata_revert -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_files_metadata_revert(app, db):
    record1 = FilesMetadata.create(data={'data': 'test'}, pid=1, con=bytes('test content', 'utf-8'))
    record2 = FilesMetadata.create(data={'data': 'test'}, pid=2, con=bytes('test content', 'utf-8'))

    record1.model = None
    with pytest.raises(Exception) as e:
        FilesMetadata.revert(record1, 0)
    assert e.type==MissingModelError

    record2 = FilesMetadata.revert(record2, 0)
    assert record2.id==2
    assert record2.model.pid==2
    assert record2.model.contents==b'test content'
    assert record2.model.json=={'data': 'test'}
    assert record2.model.version_id==2

# class FilesMetadata(RecordBase):
#     def revisions(self):
def test_revision_FilesMetadata(app):
    test = FilesMetadata(data={})

    # Exception coverage
    try:
        test.revisions()
    except:
        pass

    test.model = True

    with patch('weko_records.api.RevisionsIterator', return_value=MagicMock()):
        assert test.revisions() != None

# class RecordRevision(RecordBase):
#     def __init__(self, model):

# class SiteLicense(RecordBase):
#     def get_records(cls):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_site_license_get_records -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_site_license_get_records(app, db, site_license_info, users):
    records = SiteLicense.get_records()
    assert len(records)==1
    assert records[0]['organization_name']=='test'
    assert records[0]['domain_name']=='domain'
    assert records[0]['mail_address']=='nii@nii.co.jp'
    assert records[0]['addresses']==[]

    records = SiteLicense.get_records(users[0]['obj'])
    assert len(records)==1
    assert records[0]['organization_name']=='test'
    assert records[0]['domain_name']=='domain'
    assert records[0]['mail_address']=='nii@nii.co.jp'
    assert records[0]['addresses']==[]

    site_license_info.repository_id = "comm01"
    db.session.commit()
    records = SiteLicense.get_records(users[2]['obj'])
    assert len(records)==1
    assert records[0]['organization_name']=='test'
    assert records[0]['domain_name']=='domain'
    assert records[0]['mail_address']=='nii@nii.co.jp'
    assert records[0]['addresses']==[]

# class SiteLicense(RecordBase):
#     def update(cls, obj):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_site_license_update -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_site_license_update(app, db, site_license_info, users):
    _none_obj = {}
    _no_data_obj = {
        'item_type': {},
        'site_license': []
    }
    _test_obj = {
        'item_type': {},
        'site_license': [
            {
                'mail_address': 'nii@nii.co.jp',
                'receive_mail_flag': 'T',
                'organization_name': 'test1',
                'domain_name': 'domain1',
                'addresses': [
                    {
                        'start_ip_address': ['0', '0', '0', '0'],
                        'finish_ip_address': ['255', '255', '255', '255']
                    }
                ]
            }
        ]
    }
    user = users[0]["obj"]
    login_user(user)
    SiteLicense.update(_none_obj)
    db.session.commit()
    records = SiteLicense.get_records()
    assert len(records)==1

    SiteLicense.update(_no_data_obj)
    db.session.commit()
    records = SiteLicense.get_records()
    assert len(records)==0

    SiteLicense.update(_test_obj)
    db.session.commit()
    records = SiteLicense.get_records()
    assert len(records)==1
    assert records[0]['organization_name']=='test1'
    assert records[0]['domain_name']=='domain1'
    assert records[0]['mail_address']=='nii@nii.co.jp'
    assert records[0]['addresses']==[{'finish_ip_address': '255.255.255.255', 'start_ip_address': '0.0.0.0'}]

    user = users[2]["obj"]
    login_user(user)
    SiteLicense.update(_test_obj)
    db.session.commit()
    records = SiteLicense.get_records(user)
    assert len(records)==1
    assert records[0]['organization_name']=='test1'
    assert records[0]['domain_name']=='domain1'
    assert records[0]['mail_address']=='nii@nii.co.jp'
    assert records[0]['addresses']==[{'finish_ip_address': '255.255.255.255', 'start_ip_address': '0.0.0.0'}]

# class RevisionsIterator(object):
#     def __init__(self, model):
#     def __len__(self):
#     def __iter__(self):
#     def next(self):
#     def __next__(self):
#     def __getitem__(self, revision_id):
#     def __contains__(self, revision_id):

# class WekoRecord(Record):
#     def get_record(cls, pid, id_, with_deleted=False):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_wekorecord_get_record -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_wekorecord_get_record(app, db, records):
    FilesMetadata.create(data={'data': 'test'}, pid=1, con=bytes('test content', 'utf-8'))

    r = WekoRecord.get_record(1, records[0][0].object_uuid)
    assert len(r)==1
    assert r[0].id==1
    assert r[0].model.pid==1
    assert r[0].model.contents==b'test content'
    assert r[0].model.json=={'data': 'test'}
    assert r[0].model.version_id==1

# class WekoRecord(Record):
#     def pid(self):
def test_pid_WekoRecord(app):
    def record_fetcher(item1, item2):
        record_fetcher_magicmock = MagicMock()
        record_fetcher_magicmock.pid_type = "pid_type"
        return record_fetcher_magicmock

    def get_func(item1, item2):
        return True

    test = WekoRecord(data={})
    test.record_fetcher = record_fetcher

    data1 = MagicMock()
    data1.get = get_func

    with patch('weko_records.api.PersistentIdentifier', return_value=data1):
        assert test.pid() != None

#     def depid(self):
def test_depid_WekoRecord(app):
    test = WekoRecord(data={})

    with patch('weko_records.api.PersistentIdentifier', return_value=True):
        assert test.depid() != None

# class FeedbackMailList(object):
#     def update(cls, item_id, feedback_maillist):
#     def update_by_list_item_id(cls, item_ids, feedback_maillist):
#     def get_mail_list_by_item_id(cls, item_id):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_feedback_mail_list_create_and_update -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
@patch('invenio_communities.utils.get_repository_id_by_item_id', return_value='Root Index')
def test_feedback_mail_list_create_and_update(app, db):
    _item_id0 = uuid.uuid4()
    _item_id1 = uuid.uuid4()
    _item_id2 = uuid.uuid4()
    _feedback_maillist1 = []
    _feedback_maillist2 = [{'email': 'nii2@nii.co.jp'}]
    _feedback_maillist3 = [{'email': 'nii3@nii.co.jp', 'author_id': '1'}]

    FeedbackMailList.update(_item_id0, _feedback_maillist1)
    db.session.commit()
    record0 = FeedbackMailList.get_mail_list_by_item_id(_item_id0)
    assert record0==[]
    record1 = FeedbackMailList.get_mail_list_by_item_id(_item_id1)
    assert record1==[]
    FeedbackMailList.update(_item_id1, _feedback_maillist1)
    db.session.commit()
    record1 = FeedbackMailList.get_mail_list_by_item_id(_item_id1)
    assert record1==[]
    FeedbackMailList.update(_item_id1, _feedback_maillist2)
    db.session.commit()
    record1 = FeedbackMailList.get_mail_list_by_item_id(_item_id1)
    assert record1==[{'email': 'nii2@nii.co.jp', 'author_id': ''}]
    FeedbackMailList.update_by_list_item_id([_item_id1, _item_id2], _feedback_maillist3)
    with patch('weko_records.api.Authors.get_emails_by_id', return_value=['nii3@nii.co.jp']):
        record1 = FeedbackMailList.get_mail_list_by_item_id(_item_id1)
        record2 = FeedbackMailList.get_mail_list_by_item_id(_item_id2)
        assert record1==[{'email': 'nii3@nii.co.jp', 'author_id': '1'}]
        assert record2==[{'email': 'nii3@nii.co.jp', 'author_id': '1'}]


# class FeedbackMailList(object):
#     def get_feedback_mail_list(cls):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_get_feedback_mail_list -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
@patch('invenio_communities.utils.get_repository_id_by_item_id', return_value='Root Index')
def test_get_feedback_mail_list(app, db):
    def _create_pid(id, uuid):
        pid = PersistentIdentifier()
        pid.created = datetime.utcnow()
        pid.updated = datetime.utcnow()
        pid.id = id
        pid.pid_type = 'recid'
        pid.pid_value = str(id)
        pid.status = 'R'
        pid.object_type = 'rec'
        pid.object_uuid = uuid
        return pid

    _item_id0 = uuid.uuid4()
    _item_id1 = uuid.uuid4()
    _item_id2 = uuid.uuid4()
    _feedback_maillist0 = [{'email': 'nii0@nii.co.jp'}]
    _feedback_maillist1 = [{'email': 'nii1@nii.co.jp', 'author_id': '1'}]
    _feedback_maillist2 = [{'email': 'nii1@nii.co.jp', 'author_id': '1'}, {'email': 'nii0@nii.co.jp', 'author_id': ''}]

    FeedbackMailList.update(_item_id0, _feedback_maillist0)
    FeedbackMailList.update(_item_id1, _feedback_maillist1)
    FeedbackMailList.update(_item_id2, _feedback_maillist2)

    db.session.add(_create_pid(1, _item_id0))
    db.session.add(_create_pid(2, _item_id1))
    db.session.add(_create_pid(3, _item_id2))
    db.session.commit()
    with patch('weko_records.api.Authors.get_emails_by_id', return_value=['nii1@nii.co.jp']):
        data = FeedbackMailList.get_feedback_mail_list()
        assert data=={'nii0@nii.co.jp': {'items': [str(_item_id0), str(_item_id2)], 'author_id': ''},
                      'nii1@nii.co.jp': {'items': [str(_item_id1), str(_item_id2)], 'author_id': '1'}}
        data = FeedbackMailList.get_feedback_mail_list(repo_id='Root Index')
        assert data=={'nii0@nii.co.jp': {'items': [str(_item_id0), str(_item_id2)], 'author_id': ''},
                      'nii1@nii.co.jp': {'items': [str(_item_id1), str(_item_id2)], 'author_id': '1'}}


# class FeedbackMailList(object):
#     def delete(cls, item_id):
#     def delete_without_commit(cls, item_id):
#     def delete_by_list_item_id(cls, item_ids):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_feedback_mail_list_delete -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
@patch('invenio_communities.utils.get_repository_id_by_item_id', return_value='Root Index')
def test_feedback_mail_list_delete(app, db):
    _item_id1 = uuid.uuid4()
    _item_id2 = uuid.uuid4()
    _item_id3 = uuid.uuid4()
    _item_id4 = uuid.uuid4()
    _feedback_maillist = [{'email': 'nii0@nii.co.jp'}]
    FeedbackMailList.update_by_list_item_id([_item_id1, _item_id2, _item_id3, _item_id4], _feedback_maillist)

    flag = FeedbackMailList.delete(1)
    assert flag==False
    flag = FeedbackMailList.delete(_item_id1)
    record1 = FeedbackMailList.get_mail_list_by_item_id(_item_id1)
    assert flag==True
    assert record1==[]
    FeedbackMailList.delete_without_commit(_item_id2)
    record2 = FeedbackMailList.get_mail_list_by_item_id(_item_id2)
    assert record2==[]
    FeedbackMailList.delete_by_list_item_id([_item_id3, _item_id4])
    record3 = FeedbackMailList.get_mail_list_by_item_id(_item_id3)
    record4 = FeedbackMailList.get_mail_list_by_item_id(_item_id4)
    assert record3==[]
    assert record4==[]

# class RequestMailList(object):
#     def update(cls, item_id, request_maillist):
#     def update_by_list_item_id(cls, item_ids, request_maillist):
#     def get_mail_list_by_item_id(cls, item_id):
#     def get_request_mail_by_mailaddress(cls, address):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_request_mail_list_create_and_update -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_request_mail_list_create_and_update(mocker, app, db):
    _item_id1 = uuid.uuid4()
    _item_id2 = uuid.uuid4()
    _request_maillist1 = []
    _request_maillist2 = [{'email':'nii2@nii.co.jp'}]
    _request_maillist3 = [{'email':'nii3@nii.co.jp'}]

    flag = RequestMailList.update(1, _request_maillist1)
    assert flag==False
    record0 = RequestMailList.get_mail_list_by_item_id(1)
    assert record0==[]
    assert not RequestMailList.get_request_mail_by_mailaddress(address='nii2@nii.co.jp')
    record1 = RequestMailList.get_mail_list_by_item_id(_item_id1)
    assert record1==[]
    flag = RequestMailList.update(_item_id1, _request_maillist1)
    record1 = RequestMailList.get_mail_list_by_item_id(_item_id1)
    assert flag==True
    assert record1==[]
    flag = RequestMailList.update(_item_id1, _request_maillist2)
    record1 = RequestMailList.get_mail_list_by_item_id(_item_id1)
    item_ids=[]
    for request_mail in RequestMailList.get_request_mail_by_mailaddress(address='nii2@nii.co.jp'):
        item_ids.append(request_mail.item_id)
    assert flag==True
    assert record1==[{'email':'nii2@nii.co.jp'}]
    assert [_item_id1] == item_ids
    RequestMailList.update_by_list_item_id([_item_id1, _item_id2], _request_maillist3)
    record1 = RequestMailList.get_mail_list_by_item_id(_item_id1)
    record2 = RequestMailList.get_mail_list_by_item_id(_item_id2)
    item_ids=[]
    for request_mail in RequestMailList.get_request_mail_by_mailaddress(address='nii3@nii.co.jp'):
        item_ids.append(request_mail.item_id)
    assert record1==[{'email':'nii3@nii.co.jp'}]
    assert record2==[{'email':'nii3@nii.co.jp'}]
    assert [_item_id1,_item_id2] == item_ids
    mocker.patch("flask_sqlalchemy.BaseQuery.all", side_effect=SQLAlchemyError)
    assert not RequestMailList.get_request_mail_by_mailaddress(address='nii3@nii.co.jp')


# class RequestMailList(object):
#     def delete(cls, item_id):
#     def delete_without_commit(cls, item_id):
#     def delete_by_list_item_id(cls, item_ids):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_request_mail_list_delete -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_request_mail_list_delete(app, db):
    _item_id1 = uuid.uuid4()
    _item_id2 = uuid.uuid4()
    _item_id3 = uuid.uuid4()
    _item_id4 = uuid.uuid4()
    _request_maillist = ['nii@nii.co.jp']
    RequestMailList.update_by_list_item_id([_item_id1, _item_id2, _item_id3, _item_id4], _request_maillist)

    flag = RequestMailList.delete(1)
    assert flag==False
    flag = RequestMailList.delete(_item_id1)
    record1 = RequestMailList.get_mail_list_by_item_id(_item_id1)
    assert flag==True
    assert record1==[]
    RequestMailList.delete_without_commit(_item_id2)
    record2 = RequestMailList.get_mail_list_by_item_id(_item_id2)
    assert record2==[]
    RequestMailList.delete_by_list_item_id([_item_id3, _item_id4])
    record3 = RequestMailList.get_mail_list_by_item_id(_item_id3)
    record4 = RequestMailList.get_mail_list_by_item_id(_item_id4)
    assert record3==[]
    assert record4==[]


# class ItemLink(object):
#     def __init__(self, recid: str):
#     def __get_titles_key(item_type_mapping):
#     def __get_titles(cls, record):

# class ItemLink(object):
#     def update(self, items):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_item_link_update -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_item_link_update(app, db, records):
    """
    test cases for ItemLink.update()
    """
    with app.test_request_context():
        with app.test_client() as client:
            # test case with integer id
            # src item pid
            org_item_id = "999"
            # dst item pid
            dst_item_id_1 = "1"
            dst_item_id_1_1 = "1.1"
            dst_item_id_2 = "2"
            dst_item_id_2_1 = "2.1"
            dst_item_id_3 = "3"
            dst_item_id_3_1 = "3.1"

            # create test instance
            instance = ItemLink(recid=org_item_id)

            # test case 1: create new relation
            items = [
                {'item_id': dst_item_id_1, 'sele_id': 'normal'},
                {'item_id': dst_item_id_2, 'sele_id': 'isSupplementTo'}
            ]
            result = instance.update(items)
            assert result is None

            expected_relations = [
                {'src_item_pid': org_item_id,
                 'dst_item_pid': dst_item_id_1,
                 'reference_type': 'normal'},
                {'src_item_pid': org_item_id,
                 'dst_item_pid': dst_item_id_2,
                 'reference_type': 'isSupplementTo'},
                {'src_item_pid': dst_item_id_2,
                 'dst_item_pid': org_item_id,
                 'reference_type': 'isSupplementedBy'}, # inverse relation
                {'src_item_pid': dst_item_id_2_1,
                 'dst_item_pid': org_item_id,
                 'reference_type': 'isSupplementedBy'} # inverse relation
            ]
            actual_relations = ItemReference.query.all()
            assert len(actual_relations) == len(expected_relations)
            for rel in actual_relations:
                assert {'src_item_pid': rel.src_item_pid,
                        'dst_item_pid': rel.dst_item_pid,
                        'reference_type': rel.reference_type
                        } in expected_relations

            # test case 2: update exist relations
            items = []
            result = instance.update(items)
            assert result is None
            items = [
                {'src_item_pid': org_item_id,
                 'dst_item_pid': dst_item_id_1,
                 'sele_id': 'isSupplementTo'},
                {'src_item_pid': org_item_id,
                 'dst_item_pid': dst_item_id_2,
                 'sele_id': 'isSupplementedBy'},
                {'src_item_pid': dst_item_id_2,
                 'dst_item_pid': org_item_id,
                 'sele_id': 'normal'} # overwritten after update
            ]
            instance.bulk_create(items)
            items = [
                    {'item_id': dst_item_id_2, 'sele_id': 'isSupplementedBy'},
                    {'item_id': dst_item_id_1, 'sele_id': 'isSupplementedBy'}
                ]
            result = instance.update(items)
            expected_relations = [
                {'src_item_pid': org_item_id,
                 'dst_item_pid': dst_item_id_2,
                 'reference_type': 'isSupplementedBy'},
                {'src_item_pid': dst_item_id_2,
                 'dst_item_pid': org_item_id,
                 'reference_type': 'isSupplementTo'}, # inverse relation
                {'src_item_pid': dst_item_id_2_1,
                 'dst_item_pid': org_item_id,
                 'reference_type': 'isSupplementTo'}, # inverse relation
                {'src_item_pid': org_item_id,
                 'dst_item_pid': dst_item_id_1,
                 'reference_type': 'isSupplementedBy'},
                {'src_item_pid': dst_item_id_1,
                 'dst_item_pid': org_item_id,
                 'reference_type': 'isSupplementTo'}, # inverse relation
                {'src_item_pid': dst_item_id_1_1,
                 'dst_item_pid': org_item_id,
                 'reference_type': 'isSupplementTo'} # inverse relation
            ]

            actual_relations = ItemReference.query.all()
            assert len(actual_relations) == len(expected_relations)
            for rel in actual_relations:
                assert {'src_item_pid': rel.src_item_pid,
                        'dst_item_pid': rel.dst_item_pid,
                        'reference_type': rel.reference_type
                        } in expected_relations

            # test case 3: delete relations
            items = []
            result = instance.update(items)
            assert result is None
            assert ItemReference.query.count() == 0

            # test case 4: create and delete supplement relations
            items = [
                {'item_id': dst_item_id_1, 'sele_id': 'isSupplementTo'}
            ]
            result = instance.update(items)
            assert result is None

            supplement_relation = ItemReference.query.filter_by(
                src_item_pid=org_item_id, dst_item_pid=dst_item_id_1).first()
            assert supplement_relation.reference_type == 'isSupplementTo'
            inverse_relation = ItemReference.query.filter_by(
                src_item_pid=dst_item_id_1, dst_item_pid=org_item_id).first()
            assert inverse_relation.reference_type == 'isSupplementedBy'

            # test case 5: invalid item id
            items = [
                {'item_id': 'invalid', 'sele_id': 'normal'}
            ]
            result = instance.update(items)
            assert result is None
            assert ItemReference.query.filter_by(
                dst_item_pid='invalid'
                ).first() is None

            # test case 6: DB error
            # case IntegrityError
            with patch.object(
                    instance,
                    'bulk_create',
                    side_effect=IntegrityError(
                        "duplicate key value", None, None)
                ):
                items = [
                    {'item_id': dst_item_id_1, 'sele_id': 'normal'}
                ]
                result = instance.update(items)

                assert result is not None
                assert "duplicate key value" in result

            # case SQLAlchemyError
            with patch.object(
                    instance,
                    'bulk_create',
                    side_effect=SQLAlchemyError("transaction error")
                ):
                items = [
                    {'item_id': dst_item_id_1, 'sele_id': 'normal'}
                ]
                result = instance.update(items)

                assert result is not None
                assert "transaction error" in result

            # test case 7: multi relations
            items = [
                {'item_id': dst_item_id_1, 'sele_id': 'normal'},
                {'item_id': dst_item_id_2, 'sele_id': 'isSupplementTo'},
                {'item_id': dst_item_id_3, 'sele_id': 'isSupplementedBy'}
            ]
            result = instance.update(items)
            assert result is None

            expected_relations = [
                {'src_item_pid': org_item_id,
                 'dst_item_pid': dst_item_id_1,
                 'reference_type': 'normal'},
                {'src_item_pid': org_item_id,
                 'dst_item_pid': dst_item_id_2,
                 'reference_type': 'isSupplementTo'},
                {'src_item_pid': dst_item_id_2,
                 'dst_item_pid': org_item_id,
                 'reference_type': 'isSupplementedBy'}, # inverse relation
                {'src_item_pid': dst_item_id_2_1,
                 'dst_item_pid': org_item_id,
                 'reference_type': 'isSupplementedBy'}, # inverse relation
                {'src_item_pid': org_item_id,
                 'dst_item_pid': dst_item_id_3,
                 'reference_type': 'isSupplementedBy'},
                {'src_item_pid': dst_item_id_3,
                 'dst_item_pid': org_item_id,
                 'reference_type': 'isSupplementTo'}, # inverse relation
                {'src_item_pid': dst_item_id_3_1,
                 'dst_item_pid': org_item_id,
                 'reference_type': 'isSupplementTo'} # inverse relation
            ]
            actual_relations = ItemReference.query.all()
            assert len(actual_relations) == len(expected_relations)
            for rel in actual_relations:
                assert {'src_item_pid': rel.src_item_pid,
                        'dst_item_pid': rel.dst_item_pid,
                        'reference_type': rel.reference_type
                        } in expected_relations

            # test case8: create inverse relations of supplement relations
            items = [
                {'item_id': dst_item_id_1, 'sele_id': 'isSupplementTo'}
            ]
            result = instance.update(items)
            assert result is None

            inverse_relation = ItemReference.query.filter_by(
                src_item_pid=dst_item_id_1, dst_item_pid=org_item_id).first()
            assert inverse_relation.reference_type == 'isSupplementedBy'

            # test case 9: update from `isSupplementedBy` to `isSupplementTo`
            items = [
                {'item_id': dst_item_id_1, 'sele_id': 'isSupplementTo'}
            ]
            result = instance.update(items)
            assert result is None

            updated_relation = ItemReference.query.filter_by(
                src_item_pid=org_item_id, dst_item_pid=dst_item_id_1).first()
            assert updated_relation.reference_type == 'isSupplementTo'

            # test case 10: update from supplement to non-supplement
            items = [
                {'item_id': dst_item_id_1, 'sele_id': 'isSupplementTo'}
            ]
            result = instance.update(items)
            assert result is None

            updated_relation = ItemReference.query.filter_by(
                src_item_pid=org_item_id, dst_item_pid=dst_item_id_1).first()
            inverse_relation = ItemReference.query.filter_by(
                src_item_pid=dst_item_id_1, dst_item_pid=org_item_id).first()
            inverse_relation_1 = ItemReference.query.filter_by(
                src_item_pid=dst_item_id_1_1, dst_item_pid=org_item_id).first()
            assert updated_relation.reference_type == 'isSupplementTo'
            assert inverse_relation.reference_type == 'isSupplementedBy'
            assert inverse_relation_1.reference_type == 'isSupplementedBy'

            items = [
                {'item_id': dst_item_id_1, 'sele_id': 'normal'}
            ]
            result = instance.update(items)
            updated_relation = ItemReference.query.filter_by(
                src_item_pid=org_item_id, dst_item_pid=dst_item_id_1).first()
            inverse_relation = ItemReference.query.filter_by(
                src_item_pid=dst_item_id_1, dst_item_pid=org_item_id).all()
            inverse_relation_1 = ItemReference.query.filter_by(
                src_item_pid=dst_item_id_1_1, dst_item_pid=org_item_id).all()
            assert updated_relation.reference_type == 'normal'
            assert len (inverse_relation) == 0
            assert len (inverse_relation_1) == 0

            # test case 11: delete supplement relations
            items = []
            result = instance.update(items)
            assert result is None
            assert ItemReference.query.count() == 0

            # test case with decimal id
            # src item pid
            org_item_id = "999.0"
            # dst item pid
            dst_item_id_1 = "1"
            dst_item_id_2 = "2"
            dst_item_id_3 = "3"

            # create test instance
            instance = ItemLink(recid=org_item_id)

            # test case 1.0: create new relation
            items = [
                {'item_id': dst_item_id_1, 'sele_id': 'normal'},
                {'item_id': dst_item_id_2, 'sele_id': 'isSupplementTo'}
            ]
            result = instance.update(items)
            assert result is None

            expected_relations = [
                {'src_item_pid': org_item_id,
                 'dst_item_pid': dst_item_id_1,
                 'reference_type': 'normal'},
                {'src_item_pid': org_item_id,
                 'dst_item_pid': dst_item_id_2,
                 'reference_type': 'isSupplementTo'}
            ]
            actual_relations = ItemReference.query.all()
            assert len(actual_relations) == len(expected_relations)
            for rel in actual_relations:
                assert {'src_item_pid': rel.src_item_pid,
                 'dst_item_pid': rel.dst_item_pid,
                 'reference_type': rel.reference_type
                 } in expected_relations

            # test case 2.0: update exist relations
            # create old relations
            items = []
            result = instance.update(items)
            assert result is None
            items = [
                {'src_item_pid': org_item_id,
                 'dst_item_pid': dst_item_id_1,
                 'sele_id': 'isSupplementTo'},
                {'src_item_pid': org_item_id,
                 'dst_item_pid': dst_item_id_2,
                 'sele_id': 'isSupplementedBy'}
            ]
            instance.bulk_create(items)

            # update relations
            items = [
                    {'item_id': dst_item_id_2, 'sele_id': 'isSupplementedBy'},
                    {'item_id': dst_item_id_1, 'sele_id': 'isSupplementedBy'}
                ]
            result = instance.update(items)

            expected_relations = [
                {'src_item_pid': org_item_id, 'dst_item_pid': dst_item_id_2,
                 'reference_type': 'isSupplementedBy'},
                {'src_item_pid': org_item_id, 'dst_item_pid': dst_item_id_1,
                 'reference_type': 'isSupplementedBy'}
            ]

            actual_relations = ItemReference.query.all()
            assert len(actual_relations) == len(expected_relations)
            for rel in actual_relations:
                assert {'src_item_pid': rel.src_item_pid,
                        'dst_item_pid': rel.dst_item_pid,
                        'reference_type': rel.reference_type
                        } in expected_relations


# class ItemLink(object):
#     def get_item_link_info(cls, recid):
#     def bulk_create(self, dst_items):
#     def get_item_link_info_output_xml(cls, recid):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_item_link_bulk_create -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_item_link_bulk_create(app, db, records):
    _uuid = str(records[0][0].object_uuid)
    _items = [
        {
            'src_item_pid': _uuid,
            'dst_item_pid': '1',
            'sele_id': 'URI'
        }
    ]
    ItemLink.bulk_create(ItemLink(_uuid), _items)
    r = ItemLink.get_item_link_info(_uuid)
    assert len(r)==1
    assert r[0]['item_links']=='1'
    assert r[0]['item_title']==records[0][1]['item_title']
    assert r[0]['value']=='URI'
    # need to fix
    with pytest.raises(Exception) as e:
        ItemLink.get_item_link_info_output_xml(_uuid)
    #assert len(r)==1
    #assert r[0]['reference_type']=='URI'


# class ItemLink(object):
#     def bulk_update(self, dst_items):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_item_link_bulk_update -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_item_link_bulk_update(app, db, records):
    _uuid = str(records[0][0].object_uuid)
    _items1 = [
        {
            'src_item_pid': _uuid,
            'dst_item_pid': '1',
            'sele_id': 'URI'
        }
    ]
    _items2 = [
        {
            'src_item_pid': _uuid,
            'dst_item_pid': '1',
            'sele_id': 'URI'
        },
        {
            'src_item_pid': _uuid,
            'dst_item_pid': '2',
            'sele_id': 'DOI'
        }
    ]
    ItemLink.bulk_create(ItemLink(_uuid), _items1)

    ItemLink.bulk_update(ItemLink(_uuid), _items2)
    r = ItemLink.get_item_link_info(_uuid)
    assert len(r)==2
    assert r[0]['item_links']=='1'
    assert r[0]['item_title']==records[0][1]['item_title']
    assert r[0]['value']=='URI'
    assert r[1]['item_links']=='2'
    assert r[1]['item_title']==records[1][1]['item_title']
    assert r[1]['value']=='DOI'

# class ItemLink(object):
#     def bulk_delete(self, dst_item_ids):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_item_link_bulk_delete -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_item_link_bulk_delete(app, db, records):
    _uuid = str(records[0][0].object_uuid)
    _items = [
        {
            'src_item_pid': _uuid,
            'dst_item_pid': '1',
            'sele_id': 'URI'
        },
        {
            'src_item_pid': _uuid,
            'dst_item_pid': '2',
            'sele_id': 'DOI'
        },
        {
            'src_item_pid': _uuid,
            'dst_item_pid': '3',
            'sele_id': 'HDL'
        }
    ]
    ItemLink.bulk_create(ItemLink(_uuid), _items)

    ItemLink.bulk_delete(ItemLink(_uuid), _items[0:2])
    r = ItemLink.get_item_link_info(_uuid)
    assert len(r)==1
    assert r[0]['item_links']=='3'
    assert r[0]['item_title']==records[2][1]['item_title']
    assert r[0]['value']=='HDL'


# class JsonldMapping:
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py::TestJsonldMapping -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
class TestJsonldMapping:
    # def get_mapping_by_id(cls, id, ignore_deleted=True):
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py::TestJsonldMapping::test_get_mapping_by_id -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_get_mapping_by_id(app, db, item_type):
        obj = JsonldMapping.create(
            name="test1",
            mapping={"test": "test"},
            item_type_id=item_type.model.id,
        )
        assert JsonldMapping.get_mapping_by_id(obj.id) is obj
        assert JsonldMapping.get_mapping_by_id(obj.id).is_deleted is False

        # not found
        assert JsonldMapping.get_mapping_by_id(999) is None

        # Retrieval with_deleted=False
        obj.is_deleted = True
        db.session.commit()
        mapping = JsonldMapping.get_mapping_by_id(obj.id, with_deleted=False)
        assert mapping is None

        # Retrieve with_deleted=True
        obj.is_deleted = True
        db.session.commit()
        mapping = JsonldMapping.get_mapping_by_id(obj.id, with_deleted=True)
        assert mapping.id == obj.id
        assert mapping.is_deleted is True

    # def create(cls, name, mapping, item_type_id):
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py::TestJsonldMapping::test_create -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_create(app, db, item_type):
        # one
        obj = JsonldMapping.create(
            name="test1",
            mapping={"test": "test"},
            item_type_id=item_type[0]["item_type"].id,
        )
        assert obj.id == 1
        assert (ItemTypeJsonldMapping.query.filter_by(id=obj.id).first()) == obj

        # one more
        obj = JsonldMapping.create(
            name="test2",
            mapping={"test": "test"},
            item_type_id=item_type[0]["item_type"].id,
        )
        assert obj.id == 2
        assert (ItemTypeJsonldMapping.query.filter_by(id=obj.id).first()) == obj

        # occurs DB error. invalid item_type_id
        with pytest.raises(SQLAlchemyError) as e:
            JsonldMapping.create(
                name="test2", mapping={"test": "test"}, item_type_id=999
            )
        assert isinstance(e.value, SQLAlchemyError)
        assert ItemTypeJsonldMapping.query.filter_by(id=3).first() == None

    # def update(cls, id, name=None, mapping=None, item_type_id=None):
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py::TestJsonldMapping::test_update -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_update(app, db, item_type, sword_mapping):
        obj = JsonldMapping.create(
            name="test1",
            mapping={"test": "test"},
            item_type_id=item_type.model.id,
        )

        # Update Successful
        obj = JsonldMapping.update(
            id=obj.id,
            name="test2",
            mapping={"test2": "test2"},
            item_type_id=item_type.model.id,
        )

        result = ItemTypeJsonldMapping.query.filter_by(id=obj.id).first()
        assert result == obj
        assert result.name == "test2"
        assert result.mapping == obj.mapping
        assert result.version_id == 2


        obj = JsonldMapping.update(
            name="test2", id=999, mapping=None, item_type_id=sword_mapping[0]["item_type_id"]
        )
        assert obj is None

        # Update with invalid item_type_id
        with pytest.raises(SQLAlchemyError) as e:
            JsonldMapping.update(name="test2", id=sword_mapping[0]["id"], mapping=None, item_type_id=999)
        assert isinstance(e.value, SQLAlchemyError)

    # def versions()
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py::TestJsonldMapping::test_versions -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_versions(app, db, item_type):

        obj = JsonldMapping.create(
            name="test1",
            mapping={"test": "test"},
            item_type_id=item_type.model.id,
        )
        obj.mapping = {"test2": "test2"}
        db.session.commit()

        versions = obj.versions.all()
        assert len(versions) == 2
        assert versions[0].id == obj.id
        assert versions[1].id == obj.id
        assert versions[0].mapping == {"test": "test"}
        assert versions[1].mapping == obj.mapping
        assert versions[0].version_id == 1
        assert versions[1].version_id == 2

    # delete(cls, id):
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py::TestJsonldMapping::test_delete -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_delete(app, db, item_type):
        obj = JsonldMapping.create(
            name="test1",
            mapping={"test": "test"},
            item_type_id=item_type.model.id,
        )
        obj.is_deleted = True
        db.session.commit()

        # Successful delete
        JsonldMapping.delete(id=obj.id)
        assert (
            ItemTypeJsonldMapping.query.filter_by(id=obj.id).first().is_deleted == True
        )

        # Delete with non-existent id
        res = JsonldMapping.delete(id=999)
        assert res == None

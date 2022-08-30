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
from tkinter import W
import pytest
from elasticsearch.exceptions import RequestError
from invenio_records.api import Record
from invenio_records.errors import MissingModelError
from weko_deposit.api import WekoDeposit
from weko_index_tree.models import Index
from mock import patch,MagicMock
import uuid
from sqlalchemy.exc import SQLAlchemyError

from weko_records.api import FeedbackMailList, FilesMetadata, ItemLink, \
    ItemsMetadata, ItemTypeEditHistory, ItemTypeNames, ItemTypeProps, \
    ItemTypes, Mapping, SiteLicense, RecordBase
from weko_records.models import ItemType, ItemTypeName, \
    SiteLicenseInfo, SiteLicenseIpAddress
from jsonschema.validators import Draft4Validator
from datetime import datetime

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
def test_itemtypes_update_item_type(app, db, location, mocker):
    _form = {
        'items': []
    }

    _render = {
        'meta_list': {},
        'table_row_map': {
            'mapping': {
                'pubdate': {}
            },
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
            'mapping': {
                'pubdate': {}
            },
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


# def ItemTypes.__update_item_type
# def ItemTypes.__update_metadata
# def ItemTypes.__get_records_by_item_type_name

# class ItemTypes(RecordBase):
#     def get_record(cls, id_, with_deleted=False):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_get_record -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_record(app, db):
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
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_get_records -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_records(app, db):
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
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_get_by_id -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_by_id(app, db):
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
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_get_by_id -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_by_name_id(app, db):
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
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_get_records_by_name_id -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_records_by_name_id(app, db):
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
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_get_latest -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_latest(app, db):
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
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_get_latest_with_item_type -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_latest_with_item_type(app, db):
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
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_get_latest_custorm_harvesting -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_latest_custorm_harvesting(app, db):
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
    assert item_type_names[0].id == 1
    assert item_type_names[0].name == "test"
    assert item_type_names[0].has_site_license == True
    assert item_type_names[0].is_active== True
    assert isinstance(item_type_names[0].created,datetime)
    assert isinstance(item_type_names[0].updated,datetime)

    # need to fix
    item_type_names = ItemTypes.get_latest_custorm_harvesting(True, True)
    assert len(item_type_names)==4
    assert item_type_names[0].id == 4
    assert item_type_names[0].name == "test4"
    assert item_type_names[0].has_site_license == True
    assert item_type_names[0].is_active== True
    assert isinstance(item_type_names[0].created,datetime)
    assert isinstance(item_type_names[0].updated,datetime)

# class ItemTypes(RecordBase):
#     def get_all(cls, with_deleted=False):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_get_all -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_all(app, db):
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

# def ItemTypes.patch
# def ItemTypes.commit

# class ItemTypes(RecordBase):
#     def delete(self, force=False):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_delete -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_delete(app, db):
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

    # ItemTypes.delete(it3, True)
    # to do something

# def ItemTypes.revert

# class ItemTypes(RecordBase):
#     def restore(self):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_restore -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_restore(app, db):
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

# def ItemTypes.revisions

# class ItemTypeEditHistory(RecordBase):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_item_type_edit_history -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_item_type_edit_history(app, db, user):
    item_type = ItemTypes.create(name='test')

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

    # record = ItemTypeEditHistory.get_by_item_type_id(item_type.id)
    # to do something

# class Mapping(RecordBase):
#     def create(cls, item_type_id=None, mapping=None):
# .tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_mapping_create -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_mapping_create(app, db, item_type):
    mapping = Mapping.create(
        item_type_id=item_type.id,
        mapping={})

    record = Mapping.get_record(item_type.id)

    with pytest.raises(AttributeError):
        records = Mapping.get_records([item_type.id])

    mapping.patch({})

    mapping.revisions

    mappings = Mapping.get_mapping_by_item_type_ids([item_type.id])


def test_mapping_delete(app, db, item_type):
    mapping = Mapping.create(
        item_type_id=item_type.id,
        mapping={}
    )

    mapping.delete()


def test_item_type_props(app, db, item_type):
    prop = ItemTypeProps.create(
        property_id=1,
        name='test',
        schema={},
        form_single={},
        form_array={}
    )

    new_prop = ItemTypeProps.create(
        property_id=1,
        name='test',
        schema={},
        form_single={},
        form_array={}
    )

    record = ItemTypeProps.get_record(new_prop.id)

    ItemTypeProps.helper_remove_empty_required({
        'required': None,
        'properties': {
            'test': {
                'items': None
            }
        }
    })

    with pytest.raises(TypeError):
        records = ItemTypeProps.get_records([new_prop.id])

    prop.revisions


def test_itemsmetadata(app, db, item_type):
    record = ItemsMetadata.create(data={
            'version_id': {},
            'url': {
                'url': '',
            }
        }, _id=0, item_type_id=item_type.id)

    item_metadata = ItemsMetadata.get_record(record.id)

    ItemsMetadata.get_records([record.id])

    ItemsMetadata.get_by_item_type_id(item_type.id)

    ItemsMetadata.get_registered_item_metadata(item_type.id)

    ItemsMetadata.get_by_object_id(item_metadata.id)

    record.revisions
    record.commit()
    record.delete()


def test_files_metadata(app, db):
    record = FilesMetadata.create(data={}, pid=1, con=b'abc')

    FilesMetadata.get_record(record.model.pid)

    FilesMetadata.get_records(record.model.pid)

    record.commit()

    record.delete()


def test_site_license(app, db):
    site_license_address = SiteLicenseIpAddress(
        organization_no=1,
        start_ip_address='1.1.1.1',
        finish_ip_address='0.0.0.0',
    )
    site_license = SiteLicenseInfo(
        organization_name='text',
        addresses=[site_license_address]
    )

    records = SiteLicense.get_records()

    item_type_name = ItemTypeName(name='test')

    SiteLicense.update({
        'item_type': item_type_name.name,
        'site_license': [
            {
                'receive_mail_flag': 'T',
                'organization_name': 'T',
                'mail_address': 'T',
                'domain_name': 'T',
                'addresses': [{
                    'start_ip_address': '1',
                    'finish_ip_address': '0'
                }]
            }
        ]
    })


def test_feedback_mail_list(app, db, location):
    app.config['WEKO_BUCKET_QUOTA_SIZE'] = 50 * 1024 * 1024 * 1024
    app.config['WEKO_MAX_FILE_SIZE'] = 50 * 1024 * 1024 * 1024
    app.config['FILES_REST_DEFAULT_STORAGE_CLASS'] = 'S'
    app.config['FILES_REST_STORAGE_CLASS_LIST'] = {
        'S': 'Standard',
        'A': 'Archive',
    }
    app.config['DEPOSIT_DEFAULT_JSONSCHEMA'] = 'deposits/'
    'deposit-v1.0.0.json'

    deposit = WekoDeposit.create({})
    db.session.commit()

    FeedbackMailList.update_by_list_item_id([deposit.id], [])

    FeedbackMailList.get_mail_list_by_item_id([deposit.id])

    FeedbackMailList.delete_by_list_item_id([deposit.id])


def test_item_link(app, db, location):
    app.config['WEKO_BUCKET_QUOTA_SIZE'] = 50 * 1024 * 1024 * 1024
    app.config['WEKO_MAX_FILE_SIZE'] = 50 * 1024 * 1024 * 1024
    app.config['FILES_REST_DEFAULT_STORAGE_CLASS'] = 'S'
    app.config['FILES_REST_STORAGE_CLASS_LIST'] = {
        'S': 'Standard',
        'A': 'Archive',
    }
    app.config['DEPOSIT_DEFAULT_JSONSCHEMA'] = 'deposits/'
    'deposit-v1.0.0.json'

    deposit = WekoDeposit.create({})
    db.session.commit()

    item_link = ItemLink(deposit.pid.pid_value)

    ItemLink.get_item_link_info(deposit.get('id'))

    item_link.bulk_create([{
        'item_id': 2,
        'sele_id': 0
    }])

    item_link.update([
        {
            'item_id': 2,
            'sele_id': 1
        }
    ])

    item_link.update([
        {
            'item_id': 3,
            'sele_id': 0
        }
    ])

    ItemLink.get_item_link_info_output_xml(deposit.get('id'))




# class ItemTypes(RecordBase):
#     def create(cls, item_type_name=None, name=None, schema=None, form=None,
#             An instance of the class :class:`jsonschema.FormatChecker`, which
#             A :class:`jsonschema.IValidator` class that will be used to
#     def update(cls, id_=0, name=None, schema=None, form=None, render=None,
#     def update_item_type(cls, form, id_, name, render, result, schema):
#     def __update_item_type(cls, id_, schema, form, render):
#     def __update_metadata(
#         def __diff(list1, list2):
#         def __del_data(_json, diff_keys):
#         def __get_delete_mapping_key(item_type_mapping, _delete_list):
#         def __update_es_data(_es_data, _delete_list):
#         def __update_db(db_records, _delete_list):
#         def __update_record_metadata(_record_ids, _delete_list):
#         def __update_item_metadata(_record_ids, _delete_list):
#     def __get_records_by_item_type_name(cls, item_type_name):
#     def get_record(cls, id_, with_deleted=False):
#     def get_records(cls, ids, with_deleted=False):
#     def get_by_id(cls, id_, with_deleted=False):
#     def get_by_name_id(cls, name_id, with_deleted=False):
#     def get_records_by_name_id(cls, name_id, with_deleted=False):
#     def get_latest(cls, with_deleted=False):
#     def get_latest_with_item_type(cls, with_deleted=False):
#     def get_latest_custorm_harvesting(cls, with_deleted=False,
#     def get_all(cls, with_deleted=False):
#     def patch(self, patch):
#     def commit(self, **kwargs):
#             An instance of the class :class:`jsonschema.FormatChecker`, which
#             A :class:`jsonschema.IValidator` class that will be used to
#     def delete(self, force=False):
#     def revert(self, revision_id):
#     def restore(self):
#     def revisions(self):
# class ItemTypeEditHistory(object):
#     def create_or_update(cls, id=0, item_type_id=None, user_id=None,
#     def get_by_item_type_id(cls, item_type_id):
# class Mapping(RecordBase):
#     def create(cls, item_type_id=None, mapping=None):
#             An instance of the class :class:`jsonschema.FormatChecker`, which
#             # A :class:`jsonschema.IValidator` class that will be used to
#     def get_record(cls, item_type_id, with_deleted=False):
#     def get_records(cls, ids, with_deleted=False):
#     def patch(self, patch):
#     def commit(self, **kwargs):
#             An instance of the class :class:`jsonschema.FormatChecker`, which
#             A :class:`jsonschema.IValidator` class that will be used to
#     def delete(self, force=False):
#     def revert(self, revision_id):
#     def revisions(self):
#     def get_mapping_by_item_type_ids(cls, item_type_ids: list) -> list:
# class ItemTypeProps(RecordBase):
#     def create(cls, property_id=None, name=None, schema=None, form_single=None,
#     def get_record(cls, property_id):
#     def helper_remove_empty_required(cls, data):
#     def get_records(cls, ids):
#     def revisions(self):
# class ItemsMetadata(RecordBase):
#     def create(cls, data, id_=None, **kwargs):
#             An instance of the class :class:`jsonschema.FormatChecker`, which
#             A :class:`jsonschema.IValidator` class that will be used to
#     def get_record(cls, id_, with_deleted=False):
#     def __custom_item_metadata(cls, item_metadata: dict):
#     def __replace_fqdn_of_file_metadata(cls, item_metadata: Union[list, dict]):
#     def get_records(cls, ids, with_deleted=False):
#     def get_by_item_type_id(cls, item_type_id, with_deleted=False):
#     def get_registered_item_metadata(cls, item_type_id):
#     def get_by_object_id(cls, object_id):
#     def patch(self, patch):
#     def commit(self, **kwargs):
#             An instance of the class :class:`jsonschema.FormatChecker`, which
#             A :class:`jsonschema.IValidator` class that will be used to
#     def delete(self, force=False):
#     def revert(self, revision_id):
#     def revisions(self):
# class FilesMetadata(RecordBase):
#     def create(cls, data, id_=None, **kwargs):
#             An instance of the class :class:`jsonschema.FormatChecker`, which
#             A :class:`jsonschema.IValidator` class that will be used to
#     def get_record(cls, id_, with_deleted=False):
#     def get_records(cls, ids, with_deleted=False):
#     def patch(self, patch):
#     def update_data(id, jsn):
#     def commit(self, **kwargs):
#             An instance of the class :class:`jsonschema.FormatChecker`, which
#             A :class:`jsonschema.IValidator` class that will be used to
#     def delete(self, force=False):
#     def revert(self, revision_id):
#     def revisions(self):
# class RecordRevision(RecordBase):
#     def __init__(self, model):
# class SiteLicense(RecordBase):
#     def get_records(cls):
#     def update(cls, obj):
#         def get_addr(lst, id_):
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
#     def pid(self):
#     def depid(self):
# class FeedbackMailList(object):
#     def update(cls, item_id, feedback_maillist):
#     def update_by_list_item_id(cls, item_ids, feedback_maillist):
#     def get_mail_list_by_item_id(cls, item_id):
#     def delete(cls, item_id):
#     def delete_without_commit(cls, item_id):
#     def delete_by_list_item_id(cls, item_ids):
# class ItemLink(object):
#     def __init__(self, recid: str):
#     def get_item_link_info(cls, recid):
#     def __get_titles_key(item_type_mapping):
#     def __get_titles(cls, record):
#     def get_item_link_info_output_xml(cls, recid):
#         def get_url(pid_value):
#     def update(self, items):
#     def bulk_create(self, dst_items):
#     def bulk_update(self, dst_items):
#     def bulk_delete(self, dst_item_ids):

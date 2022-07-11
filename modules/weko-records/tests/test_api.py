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
import pytest
from elasticsearch.exceptions import RequestError
from invenio_records.api import Record
from weko_deposit.api import WekoDeposit
from weko_index_tree.models import Index
from mock import patch
import uuid
from sqlalchemy.exc import SQLAlchemyError

from weko_records.api import FeedbackMailList, FilesMetadata, ItemLink, \
    ItemsMetadata, ItemTypeEditHistory, ItemTypeNames, ItemTypeProps, \
    ItemTypes, Mapping, SiteLicense, RecordBase
from weko_records.models import ItemTypeName, SiteLicenseInfo, \
    SiteLicenseIpAddress


def test_recordbase(app, db):
    class MockClass():
        def __init__(self, id, version_id, created, updated):
            self.id=id
            self.version_id=version_id
            self.created=created
            self.updated=updated
    data = dict(
        id=1,
        version_id=10,
        created="yesterday",
        updated="now"
    )
    test_model = MockClass(**data)
    record = RecordBase(data)
    record.model = test_model
    result = record.dumps()
    assert result["id"] == 1
    assert result["version_id"] == 10
    assert result["created"] == "yesterday"
    assert result["updated"] == "now"

def test_itemtypenames(app, db):
    item_type_name = ItemTypeNames.update({'a': [{'id': 1}]})


def test_itemtypes(app, db):
    _item_type_name = ItemTypeName(name='test')

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

    item_type = ItemTypes.create(
        name='test',
        item_type_name=_item_type_name,
        schema=_schema,
        render=_render,
        tag=1
    )

    record = ItemTypes.update(
        id_=item_type.id,
        name='test',
        schema=_schema,
        form={},
        render=_render
    )

    record = ItemTypes.update(
        id_=item_type.id,
        name='test',
        schema=_schema,
        form={},
        render=_render
    )

    ItemTypes.get_record(record.id)
    ItemTypes.get_records([record.id])
    ItemTypes.get_by_id(record.id)

    ItemTypes.get_records_by_name_id(_item_type_name.id)
    ItemTypes.get_latest()
    ItemTypes.get_latest_with_item_type()
    ItemTypes.get_latest_custorm_harvesting()
    ItemTypes.get_all()

    record.commit()
    if len(record.revisions) > 1:
        record.revert(len(record.revisions) - 1)

def test_itemtypes_update(app, db, location, mocker):
    # create new record
    mock_create = mocker.patch("weko_records.api.ItemTypes.create")
    ItemTypes.update(id_=-1, name="test")
    mock_create.assert_called_once()
    
    # the record to be updated does not exist
    with pytest.raises(ValueError):
        ItemTypes.update(id_=1,name="test")

def test_itemtypes_update_item_type(app, db, location, mocker):
    _item_type_name = ItemTypeName(name='test')
    _item_type_name_exist = ItemTypeName(name='exist title')
    with db.session.begin_nested():
        db.session.add(_item_type_name_exist)
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

    item_type = ItemTypes.create(
        name='test',
        item_type_name=_item_type_name,
        schema=_schema,
        render=_render,
        tag=1
    )
    # Change the name
    record = ItemTypes.update(
        id_=item_type.id,
        name='test2',
        schema=_schema,
        form={},
        render=_render
    )

    # Alliance exists
    with pytest.raises(ValueError):
        record = ItemTypes.update(
            id_=item_type.id,
            name='exist title',
            schema=_schema,
            form={},
            render=_render
        )

    app.config['WEKO_ITEMTYPES_UI_UPGRADE_VERSION_ENABLED'] = False
    record = ItemTypes.update(
        id_=item_type.id,
        name='test2',
        schema=_schema,
        form={},
        render=_render
    )

    # check_to_upgrade_version is True
    with patch("weko_records.utils.check_to_upgrade_version", return_value=True):
        with patch("weko_records.api.ItemTypes.create"):
            record = ItemTypes.update(
                id_=item_type.id,
                name="new item",
                schema=_schema,
                form={},
                render=_render_2
            )

    # with pytest.raises(RequestError):
    record = ItemTypes.update(
        id_=item_type.id,
        name='test',
        schema=_schema,
        form={},
        render=_render_2
    )


@pytest.fixture()
def update_metadata_data(app, db):
    _render1 = {
        'meta_list': {},
        'table_row_map': {
            'schema': {
                'properties': {
                    'item_1': {}
                }
            }
        },
        'table_row': ['pub_date','system_file','2','3']
    }
    _render2 = {
        'meta_list': {},
        'table_row_map': {
            'schema': {
                'properties': {
                    'item_1': {}
                }
            }
        },
        'table_row':['2', '3', '4']
    }
    _schema={
        'properties':{},
    }
    _mapping={
        "pubdate":{
        },
        "system_file":{
            "jpcoar_mapping": {
                "URL":{},
                "date":{},
                "extent":{}
                
            }
        }
    }
    _item_type_name = ItemTypeName(name='test')
    _item_type_name2 = ItemTypeName(name="test2")
    item_type = ItemTypes.create(
        name="test",
        item_type_name=_item_type_name,
        schema=_schema,
        render=_render1,
        tag=1
    )
    item_type2 = ItemTypes.create(
        name="test2",
        item_type_name=_item_type_name2,
        schema=_schema,
        render=_render1,
        tag=1
    )
    _item_type_mapping= Mapping.create(
        item_type_id=item_type.id,
        mapping=_mapping)
    app.config['WEKO_ITEMTYPES_UI_UPGRADE_VERSION_ENABLED']=False
    return {
        "item_type_name":[_item_type_name,_item_type_name2],
        "item_type":[item_type, item_type2],
        "schema":_schema,
        "render":[_render1, _render2]
        }


@pytest.mark.parametrize("dummy_data",[
    {"hits":{"hits":
                [{"_id":"",
                    "_source":{
                        "_item_metadata":{
                            "item_type_id":"","system_file":{}
                        },
                        "URL":{},
                        "date":{}
                    }
                },
                {"_id":"not_item_type",
                    "_source":{
                        "item_metadata":{
                            "item_type_id":"xxxxx"
                        }
                    }
                }]}
    },
    {"hits":{"hits":
                [{"_id":"",
                    "_source":{
                        "_item_metadata":{
                            "item_type_id":"",
                            },
                        }
                },
                {"_id":"not_item_type",
                    "_source":{
                        "item_metadata":{
                            "item_type_id":"xxxxx"
                        }
                    }
                }]}
    }
])
def test_itemtypes_update_metadata(app, db, mock_execute, records, update_metadata_data, mocker, dummy_data):

    item_type=update_metadata_data["item_type"][0]
    _schema=update_metadata_data["schema"]
    _render2=update_metadata_data["render"][1]
    
    dummy_data["hits"]["hits"][0]["_id"]=records[0][0].object_uuid
    dummy_data["hits"]["hits"][0]["_source"]["_item_metadata"]["item_type_id"] = str(item_type.id)

    app.config['WEKO_ITEMTYPES_UI_UPGRADE_VERSION_ENABLED']=False
    mocker.patch("weko_records.api.RecordsSearch.execute", return_value=mock_execute(dummy_data))
    record = ItemTypes.update(
        id_=item_type.id,
        name="test",
        schema=_schema,
        form={},
        render=_render2
    )


def test_itemtypes_update_metadata_diff_itemtype(app, db, mock_execute, update_metadata_data, mocker):
    item_type2 = update_metadata_data["item_type"][1]
    item_type=update_metadata_data["item_type"][0]
    _schema=update_metadata_data["schema"]
    _render2=update_metadata_data["render"][1]
    dummy_data = {
        "hits":{
            "hits":[
                {
                    "_id":"test data",
                    "_item_metadata":{
                        "item_type_id":str(item_type2.id)
                    }
                }
            ]
        }
    }

    mocker.patch("weko_records.api.RecordsSearch.execute", return_value=mock_execute(dummy_data))
    record = ItemTypes.update(
        id_=item_type.id,
        name="test",
        schema=_schema,
        form={},
        render=_render2
    )


def test_itemtypes_update_metadata_sqlerror(app, db, records, mock_execute, update_metadata_data, mocker):
    item_type=update_metadata_data["item_type"][0]
    _schema=update_metadata_data["schema"]
    _render2=update_metadata_data["render"][1]
    dummy_data = {
        "hits":{
            "hits":
                [
                    {
                        "_id":records[0][0].object_uuid,
                        "_source":{
                            "_item_metadata":{
                                "item_type_id":str(item_type.id),
                                "system_file":{}
                            },
                            "URL":{},
                            "date":{}
                            
                        }
                    },
                    {
                        "_id":"not_item_type",
                        "_source":{
                            "item_metadata":{
                                "item_type_id":"xxxxx"
                            }
                        }
                    }
                ]
        }
    }
    mocker.patch("weko_records.api.RecordsSearch.execute", return_value=mock_execute(dummy_data))
    with patch("weko_records.api.db.session.commit", side_effect=SQLAlchemyError):
        with pytest.raises(SQLAlchemyError):
            record = ItemTypes.update(
                id_=item_type.id,
                name="test",
                schema=_schema,
                form={},
                render=_render2
            )


def test_itemtypes_update_metadata_record0(app, db, mock_execute, update_metadata_data, mocker):
    item_type=update_metadata_data["item_type"][0]
    _schema=update_metadata_data["schema"]
    _render2=update_metadata_data["render"][1]
    dummy_data = {
        "hits":{
            "hits":
                [
                    {
                        "_id":uuid.uuid4(),
                        "_source":{
                            "_item_metadata":{
                                "item_type_id":str(item_type.id),
                                "system_file":{}
                            },
                            "URL":{},
                            "date":{}
                            
                        }
                    }
                ]
        }
    }
    mocker.patch("weko_records.api.RecordsSearch.execute", return_value=mock_execute(dummy_data))
    record = ItemTypes.update(
        id_=item_type.id,
        name="test",
        schema=_schema,
        form={},
        render=_render2
    )


def test_itemtypes_update_metadata_item0(app, db, records, mock_execute, update_metadata_data, mocker):
    item_type=update_metadata_data["item_type"][0]
    item_type=update_metadata_data["item_type"][0]
    _schema=update_metadata_data["schema"]
    _render2=update_metadata_data["render"][1]

    dummy_data = {
        "hits":{
            "hits":
                [
                    {
                        "_id":records[0][0].object_uuid,
                        "_source":{
                            "_item_metadata":{
                                "item_type_id":str(item_type.id),
                                "system_file":{}
                            },
                            "URL":{},
                            "date":{}
                            
                        }
                    }
                ]
        }
    }
    app.config['WEKO_ITEMTYPES_UI_UPGRADE_VERSION_ENABLED']=False
    mocker.patch("weko_records.api.RecordsSearch.execute", return_value=mock_execute(dummy_data))
    record = ItemTypes.update(
        id_=item_type.id,
        name="test",
        schema=_schema,
        form={},
        render=_render2
    )


def test_itemtypes_delete(app, db):
    _item_type_name = ItemTypeName(name='test')

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

    item_type = ItemTypes.create(
        name='test',
        item_type_name=_item_type_name,
        schema=_schema,
        render=_render,
        tag=1
    )

    item_type.delete()
    item_type.restore()


def test_item_type_history(app, db, user):
    _item_type_name = ItemTypeName(name='test')

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

    item_type = ItemTypes.create(
        name='test',
        item_type_name=_item_type_name,
        schema={},
        render=_render,
        tag=1
    )

    record = ItemTypeEditHistory.create_or_update(
        id=0,
        item_type_id=item_type.id,
        user_id=user.id)

    record = ItemTypeEditHistory.get_by_item_type_id(item_type.id)


def test_mapping(app, db, item_type):
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

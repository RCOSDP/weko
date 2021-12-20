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

import pytest
from elasticsearch.exceptions import NotFoundError
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.errors import MissingModelError
from invenio_records_rest.errors import PIDResolveRESTError
from six import BytesIO
from sqlalchemy.orm.exc import NoResultFound
from weko_admin.models import AdminSettings
from weko_records.api import ItemTypes

from weko_deposit.api import WekoDeposit, WekoFileObject, WekoIndexer, \
    WekoRecord, _FormatSysBibliographicInformation, _FormatSysCreator


def test_missing_location(app, record):
    """Test missing location."""
    with pytest.raises(AttributeError):
        WekoRecord.create({}).file
    # for file in record.files:
        # file_info = file.info()


def test_record_create(app, db, location):
    """Test record creation with only bucket."""
    record = WekoRecord.create({'title': 'test'})
    db.session.commit()
    # assert record['_bucket'] == record.bucket_id
    assert '_files' not in record
    # assert len(record.pid)


def test_weko_record(app, db, location):
    """Test record files property."""
    with pytest.raises(MissingModelError):
        WekoRecord({}).files

    AdminSettings.update(
        'items_display_settings',
        {'items_search_author': 'name', 'items_display_email': True},
        1
    )

    # item_type = ItemTypes.create(item_type_name='test', name='test')

    # deposit = WekoDeposit.create({'item_type_id': item_type.id})
    deposit = WekoDeposit.create({})
    db.session.commit()

    record = WekoRecord.get_record_by_pid(deposit.pid.pid_value)

    record.pid

    record.pid_recid

    # record.hide_file

    record.navi

    # record.item_type_info
    with pytest.raises(AttributeError):
        record.items_show_list

    with pytest.raises(AttributeError):
        record.display_file_info

    record._get_creator([{}], True)

    record._get_creator({}, False)


def test_files_property(app, db, location):
    """Test record files property."""
    with pytest.raises(MissingModelError):
        WekoRecord({}).files

    deposit = WekoDeposit.create({})
    db.session.commit()

    record = WekoRecord.get_record_by_pid(deposit.pid.pid_value)

    assert 0 == len(record.files)
    assert 'invalid' not in record.files
    # make sure that _files key is not added after accessing record.files
    assert '_files' not in record

    with pytest.raises(KeyError):
        record.files['invalid']

    bucket = record.files.bucket
    assert bucket


def test_format_sys_creator(app, db):

    creator = {
        'creatorNames': [{
            'creatorName': 'test',
            'creatorNameLang': 'en'
        }]
    }

    format_creator = _FormatSysCreator(creator)


def test_format_sys_bibliographic_information_multiple(app, db):
    metadata = [
        {
            "bibliographic_titles":
            [
                {
                    "bibliographic_title": "test",
                    "bibliographic_titleLang": "en"
                }
            ],
            "bibliographicPageEnd": "",
            "bibliographicIssueNumber": "",
            "bibliographicPageStart": "",
            "bibliographicVolumeNumber": "",
            "bibliographicNumberOfPages": "",
            "bibliographicIssueDates": ""
        }
    ]

    sys_bibliographic = _FormatSysBibliographicInformation(metadata, [])

    sys_bibliographic.is_bibliographic()

    sys_bibliographic.get_bibliographic_list(True)

    sys_bibliographic.get_bibliographic_list(False)


def test_weko_deposit(app, db, location):
    deposit = WekoDeposit.create({})
    db.session.commit()

    with pytest.raises(PIDResolveRESTError):
        deposit.update({'actions': 'publish', 'index': '0', }, {})

    with pytest.raises(NoResultFound):
        deposit.item_metadata

    deposit.is_published()

    deposit['_deposit'] = {
        'pid': {
            'revision_id': 1,
            'type': 'pid',
            'value': '1'
        }
    }


def test_weko_indexer(app, db, location):
    deposit = WekoDeposit.create({})
    db.session.commit()

    indexer = WekoIndexer()

    with pytest.raises(NotFoundError):
        indexer.update_publish_status(deposit)

    indexer.get_es_index()

    indexer.upload_metadata(
        jrc={},
        item_id=deposit.id,
        revision_id=0,
        skip_files=True
    )

    with pytest.raises(NotFoundError):
        indexer.update_relation_version_is_last({
            'id': 1,
            'is_last': True
        })

    indexer.update_path(deposit, update_revision=False)

    indexer.delete_file_index([deposit.id], 0)

    indexer.get_pid_by_es_scroll('')


def test_weko_indexer(app, db, location):
    deposit = WekoDeposit.create({})
    db.session.commit()

    indexer = WekoIndexer()

    with pytest.raises(NotFoundError):
        indexer.update_publish_status(deposit)

    indexer.get_es_index()

    indexer.upload_metadata(
        jrc={},
        item_id=deposit.id,
        revision_id=0,
        skip_files=True
    )

    indexer.get_pid_by_es_scroll('')


def test_weko_file_object(app, db, location, testfile):
    record = WekoFileObject(
        obj=testfile,
        data={
            'size': 1,
            'format': 'application/msword',
        }
    )


def test_weko_deposit_new(app, db, location):
    recid = '1'
    deposit = WekoDeposit.create({}, recid=int(recid))
    db.session.commit()

    pid = PersistentIdentifier.query.filter_by(
        pid_type='recid',
        pid_value=recid
    ).first()

    record = WekoDeposit.get_record(pid.object_uuid)
    deposit = WekoDeposit(record, record.model)

    with pytest.raises(NotFoundError):
        deposit.publish()

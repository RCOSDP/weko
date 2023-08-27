# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Test the API."""

from __future__ import absolute_import, print_function

from copy import deepcopy

import uuid
import pytest
from mock import patch
from invenio_db import db
from invenio_pidstore.errors import PIDInvalidAction
from invenio_records.errors import MissingModelError
from jsonschema.exceptions import RefResolutionError
from six import BytesIO
from sqlalchemy.orm.exc import NoResultFound

from invenio_deposit.api import Deposit
from invenio_deposit.errors import MergeConflict

from flask_login.utils import login_user, logout_user

def test_schemas(app, fake_schemas):
    """Test schema URL transformations."""
    deposit = Deposit.create({})
    assert 'http://localhost/schemas/deposits/deposit-v1.0.0.json' == \
        deposit['$schema']

    assert 'http://localhost/schemas/deposit-v1.0.0.json' == \
        deposit.record_schema

    assert 'http://localhost/schemas/deposits/test-v1.0.0.json' == \
        deposit.build_deposit_schema({
            '$schema': 'http://localhost/schemas/test-v1.0.0.json',
        })

    with pytest.raises(RefResolutionError):
        Deposit.create({
            '$schema': 'http://localhost/schemas/deposits/invalid.json',
        })


def test_simple_flow(app, fake_schemas, location):
    """Test simple flow of deposit states through its lifetime."""
    deposit = Deposit.create({})
    assert deposit['_deposit']['id']
    assert 'draft' == deposit.status
    assert 0 == deposit.revision_id

    deposit.publish()
    assert 'published' == deposit.status
    assert 1 == deposit.revision_id

    with pytest.raises(PIDInvalidAction):
        deposit.delete()
    with pytest.raises(PIDInvalidAction):
        deposit.clear()
    with pytest.raises(PIDInvalidAction):
        deposit.update(title='Revision 2')
    assert 'published' == deposit.status

    # deposit = deposit.edit()
    # assert 'draft' == deposit.status
    # assert 2 == deposit.revision_id
    # assert 0 == deposit['_deposit']['pid']['revision_id']

    # with pytest.raises(PIDInvalidAction):
    #     deposit.edit()
    # assert 'draft' == deposit.status

    # deposit['title'] = 'Revision 1'
    # deposit.publish()
    # assert 'published' == deposit.status
    # assert 3 == deposit.revision_id
    # assert 0 == deposit['_deposit']['pid']['revision_id']

    # deposit = deposit.edit()
    # assert 'draft' == deposit.status
    # assert 4 == deposit.revision_id
    # assert 1 == deposit['_deposit']['pid']['revision_id']

    # deposit['title'] = 'Revision 2'
    # deposit.commit()
    # assert 5 == deposit.revision_id

    # (_, record) = deposit.fetch_published()
    # record_schema_before = record['$schema']
    # record_json = deepcopy(record.model.json)

    # deposit = deposit.discard()
    # assert 'published' == deposit.status
    # assert 'Revision 1' == deposit['title']
    # assert 6 == deposit.revision_id

    # (_, record) = deposit.fetch_published()
    # record_schema_after = record['$schema']
    # assert record_schema_before == record_schema_after
    # assert record_json == record.model.json


def test_delete(app, fake_schemas, location):
    """Test simple delete."""
    deposit = Deposit.create({})
    pid = deposit.pid
    assert deposit['_deposit']['id']
    assert 'draft' == deposit.status
    assert 0 == deposit.revision_id

    deposit.delete()

    with pytest.raises(NoResultFound):
        Deposit.get_record(deposit.id)

    with pytest.raises(PIDInvalidAction):
        deposit.publish(pid=pid)


def test_files_property(app, fake_schemas, location):
    """Test deposit files property."""
    with pytest.raises(MissingModelError):
        Deposit({}).files

    deposit = Deposit.create({})

    assert 0 == len(deposit.files)
    assert 'invalid' not in deposit.files

    with pytest.raises(KeyError):
        deposit.files['invalid']

    bucket = deposit.files.bucket
    assert bucket

    # Create first file:
    deposit.files['hello.txt'] = BytesIO(b'Hello world!')

    file_0 = deposit.files['hello.txt']
    assert 'hello.txt' == file_0['key']
    assert 1 == len(deposit.files)

    # Update first file with new content:
    deposit.files['hello.txt'] = BytesIO(b'Hola mundo!')
    file_1 = deposit.files['hello.txt']
    assert 'hello.txt' == file_1['key']
    assert 1 == len(deposit.files)

    assert file_0['version_id'] != file_1['version_id']

    # Create second file and check number of items in files.
    deposit.files['second.txt'] = BytesIO(b'Second file.')
    assert deposit.files['second.txt']
    assert 2 == len(deposit.files)
    assert 'hello.txt' in deposit.files
    assert 'second.txt' in deposit.files

    # Check order of files.
    order_0 = [f['key'] for f in deposit.files]
    assert ['hello.txt', 'second.txt'] == order_0

    deposit.files.sort_by(*reversed(order_0))
    order_1 = [f['key'] for f in deposit.files]
    assert ['second.txt', 'hello.txt'] == order_1

    # Try to rename second file to 'hello.txt'.
    with pytest.raises(Exception):
        deposit.files.rename('second.txt', 'hello.txt')

    # Remove the 'hello.txt' file.
    del deposit.files['hello.txt']
    assert 'hello.txt' not in deposit.files
    # Make sure that 'second.txt' is still there.
    assert 'second.txt' in deposit.files

    with pytest.raises(KeyError):
        del deposit.files['hello.txt']

    # Now you can rename 'second.txt' to 'hello.txt'.
    deposit.files.rename('second.txt', 'hello.txt')
    assert 'second.txt' not in deposit.files
    assert 'hello.txt' in deposit.files


def test_publish_revision_changed_mergeable(app, location, fake_schemas):
    """Try to Publish and someone change the deposit in the while."""
    # create a deposit
    deposit = Deposit.create({"metadata": {"title": "title-1"}})
    deposit.commit()
    db.session.commit()
    # publish
    deposit.publish()
    db.session.commit()
    # # edit
    # deposit = deposit.edit()
    # db.session.commit()
    # # simulate a externally modification
    # rid, record = deposit.fetch_published()
    # rev_id = record.revision_id
    # # try to change metadata
    # record.update({
    #     'metadata': {"title": "title-1", 'poster': 'myposter'},
    # })
    # record.commit()
    # db.session.commit()
    # assert rev_id != record.revision_id
    # # edit again and check the merging
    # deposit.update({"metadata": {"title": "title-1",
    # "description": "mydesc"}})
    # deposit.commit()
    # deposit.publish()
    # db.session.commit()
    # # check if is properly merged
    # did, deposit = deposit.fetch_published()
    # assert deposit['metadata']['title'] == 'title-1'
    # assert deposit['metadata']['poster'] == 'myposter'
    # assert deposit['metadata']['description'] == 'mydesc'
    # assert deposit['$schema'] ==
    # 'http://localhost/schemas/deposit-v1.0.0.json'


def test_publish_revision_changed_not_mergeable(app, location, fake_schemas):
    """Try to Publish and someone change the deposit in the while."""
    # create a deposit
    deposit = Deposit.create({"metadata": {
        "title": "title-1",
    }})
    deposit.commit()
    db.session.commit()
    # publish
    deposit.publish()
    db.session.commit()
    # # edit
    # deposit = deposit.edit()
    # db.session.commit()
    # # simulate a externally modification
    # rid, record = deposit.fetch_published()
    # rev_id = record.revision_id
    # record.update({'metadata': {
    #     "title": "title-2.1",
    # }})
    # record.commit()
    # db.session.commit()
    # assert rev_id != record.revision_id
    # # edit again and check the merging
    # deposit.update({"metadata": {
    #     "title": "title-2.2",
    # }})
    # deposit.commit()
    # with pytest.raises(MergeConflict):
    #     deposit.publish()


# .tox/c1/bin/pytest --cov=invenio_deposit tests/test_api.py::test_deposit_create -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-deposit/.tox/c1/tmp
def test_deposit_create(app, location, fake_schemas):
    datastore = app.extensions['security'].datastore
    user1 = datastore.create_user(email='info@inveniosoftware.org', password='tester', active=True)

    with app.test_request_context():
        logout_user()
        data_no_login = {
            "metadata": {
                        "title": "test-title",
                        },
            "_deposit": {
                "id": "1"
            }
        }
        deposit = Deposit.create(data_no_login)
        assert deposit['_deposit']['owner'] == 1
        assert deposit['_deposit']['owners'] == [1]
        assert deposit['_deposit']['weko_shared_ids'] == []

        with patch("flask_login.utils._get_user", return_value=user1):
            data = {
                "metadata": {
                            "title": "test-title",
                            },
                "owner": 1,
                "weko_shared_ids":[2]
            }
            deposit = Deposit.create(data)
            assert deposit['_deposit']['created_by'] == user1.id
            assert deposit['_deposit']['owner'] == 1
            assert deposit['_deposit']['owners'] == [1]
            assert deposit['_deposit']['weko_shared_ids'] == [2]

            data_1 = {
                "metadata": {
                            "title": "test-title",
                            },
                "owner": 1
            }
            deposit_1 = Deposit.create(data_1)
            assert deposit_1['weko_shared_ids'] == []
            assert deposit_1['_deposit']['weko_shared_ids'] == []
            """
            data_2 = {
                "metadata": {
                            "title": "test-title",
                            },
                "owner": 1
            }
            id = uuid.uuid4()
            recid = 3
            deposit_1 = Deposit.create(data_2, id_=id, recid=recid)
            assert deposit_1['weko_shared_ids'] == []
            assert deposit_1['_deposit']['weko_shared_ids'] == []
            """

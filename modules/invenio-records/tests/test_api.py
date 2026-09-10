# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test Invenio Records API."""

from __future__ import absolute_import, print_function

import copy
import uuid
from datetime import datetime, timedelta

import pytest
from jsonresolver import JSONResolver
from jsonresolver.contrib.jsonref import json_loader_factory
from jsonschema import FormatChecker
from jsonschema.exceptions import ValidationError
from sqlalchemy.orm.exc import NoResultFound

from invenio_records import Record
from invenio_records.errors import MissingModelError
from invenio_records.models import RecordMetadata
from invenio_records.validators import PartialDraft4Validator


def strip_ms(dt):
    """Strip microseconds."""
    return dt - timedelta(microseconds=dt.microsecond)


def test_get_records(app, db):
    """Test bulk record fetching."""
    # Create test records
    test_records = [
        Record.create({'title': 'test1'}),
        Record.create({'title': 'to_be_deleted'}),
        Record.create({'title': 'test3'}),
    ]
    db.session.commit()
    test_ids = [record.id for record in test_records]

    # Fetch test records
    assert len(Record.get_records(test_ids)) == 3

    test_records[1].delete()

    # should not show deleted
    db.session.commit()
    assert len(Record.get_records(test_ids)) == 2

    # should show deleted
    assert len(Record.get_records(test_ids, with_deleted=True)) == 3


def test_revision_id_created_updated_properties(app, db):
    """Test properties."""
    record = Record.create({'title': 'test'})
    assert record.revision_id == 0
    dt_c = record.created
    assert dt_c
    dt_u = record.updated
    assert dt_u
    record['title'] = 'test 2'
    record.commit()
    db.session.commit()
    assert record.revision_id == 1
    assert strip_ms(record.created) == strip_ms(dt_c)
    assert strip_ms(record.updated) >= strip_ms(dt_u)

    assert dt_u.tzinfo is None
    utcnow = datetime.utcnow()
    assert dt_u > utcnow - timedelta(seconds=10)
    assert dt_u < utcnow + timedelta(seconds=10)


def test_delete(app, db):
    """Test delete a record."""
    # Create a record, revise it and delete it.
    record = Record.create({'title': 'test 1'})
    db.session.commit()
    record['title'] = 'test 2'
    record.commit()
    db.session.commit()
    record.delete()
    db.session.commit()

    # Deleted records a not retrievable by default
    pytest.raises(NoResultFound, Record.get_record, record.id)

    # # Deleted records can be retrieved if you explicit request it
    # record = Record.get_record(record.id, with_deleted=True)

    # # Deleted records are empty
    # assert record == {}
    # assert record.model.json is None

    # # Deleted records *cannot* be modified
    # record['title'] = 'deleted'
    # assert pytest.raises(MissingModelError, record.commit)

    # # Deleted records *can* be reverted
    # record = record.revert(-2)
    # assert record['title'] == 'test 2'
    # db.session.commit()

    # # The "undeleted" record can now be retrieve again
    # record = Record.get_record(record.id)
    # assert record['title'] == 'test 2'

    # # Force deleted record cannot be retrieved again
    # record.delete(force=True)
    # db.session.commit()
    # pytest.raises(
    #     NoResultFound, Record.get_record, record.id,
    #     with_deleted=True)


def test_revisions(app, db):
    """Test revisions."""
    # Create a record and make modifications to it.
    record = Record.create({'title': 'test 1'})
    rec_uuid = record.id
    db.session.commit()
    record['title'] = 'test 2'
    record.commit()
    db.session.commit()
    record['title'] = 'test 3'
    record.commit()
    db.session.commit()

    # Get the record
    record = Record.get_record(rec_uuid)
    assert record['title'] == 'test 3'
    assert record.revision_id == 2

    # Retrieve specific revisions
    rev1 = record.revisions[0]
    assert rev1['title'] == 'test 1'
    assert rev1.revision_id == 0

    rev2 = record.revisions[1]
    assert rev2['title'] == 'test 2'
    assert rev2.revision_id == 1

    # Latest revision is identical to record.
    rev_latest = record.revisions[-1]
    assert dict(rev_latest) == dict(record)

    # Revert to a specific revision
    record = record.revert(rev1.revision_id)
    assert record['title'] == 'test 1'
    assert record.created == rev1.created
    assert record.updated != rev1.updated
    assert record.revision_id == 3
    db.session.commit()

    # Get the record again and check it
    record = Record.get_record(rec_uuid)
    assert record['title'] == 'test 1'
    assert record.revision_id == 3

    # Make a change and ensure revision id is changed as well.
    record['title'] = 'modification'
    record.commit()
    db.session.commit()
    assert record.revision_id == 4

    # Iterate over revisions
    assert len(record.revisions) == 5
    revs = list(record.revisions)
    assert revs[0]['title'] == 'test 1'
    assert revs[1]['title'] == 'test 2'
    assert revs[2]['title'] == 'test 3'
    assert revs[3]['title'] == 'test 1'
    assert revs[4]['title'] == 'modification'

    assert 2 in record.revisions
    assert 5 not in record.revisions


def test_record_update_mutable(app, db):
    """Test updating mutables in a record."""
    recid = uuid.UUID('262d2748-ba41-456f-a844-4d043a419a6f')

    # Create a new record with two mutables, a list and a dict
    rec = Record.create(
        {
            'title': 'Title',
            'list': ['foo', ],
            'dict': {'moo': 'boo'},
        },
        id_=recid)
    # Make sure mutables are there before and after commit
    assert rec == {
        'title': 'Title',
        'list': ['foo', ],
        'dict': {'moo': 'boo'}
    }
    db.session.commit()
    db.session.expunge_all()
    rec = Record.get_record(recid)
    assert rec == {
        'title': 'Title',
        'list': ['foo', ],
        'dict': {'moo': 'boo'}
    }

    # Set the mutables under key
    rec['list'] = ['bar', ]
    rec['dict'] = {'eggs': 'bacon'}
    rec.commit()
    # Make sure it commits to DB
    assert rec == {
        'title': 'Title',
        'list': ['bar', ],
        'dict': {'eggs': 'bacon'}
    }
    db.session.commit()
    db.session.expunge_all()
    rec = Record.get_record(recid)
    assert rec == {
        'title': 'Title',
        'list': ['bar', ],
        'dict': {'eggs': 'bacon'}
    }

    # Update the mutables under key
    rec['list'].append('spam')
    rec['dict']['ham'] = 'chicken'
    rec.commit()
    # Make sure it commits to DB
    assert rec == {
        'title': 'Title',
        'list': ['bar', 'spam'],
        'dict': {'eggs': 'bacon', 'ham': 'chicken'}
    }
    db.session.commit()
    db.session.expunge_all()
    rec = Record.get_record(recid)
    assert rec == {
        'title': 'Title',
        'list': ['bar', 'spam'],
        'dict': {'eggs': 'bacon', 'ham': 'chicken'}
    }


def test_missing_model(app, db):
    """Test revisions."""
    record = Record({})
    assert record.id is None
    assert record.revision_id is None
    assert record.created is None
    assert record.updated is None

    try:
        record.revisions
        assert False
    except MissingModelError:
        assert True

    pytest.raises(MissingModelError, record.commit)
    pytest.raises(MissingModelError, record.delete)
    pytest.raises(MissingModelError, record.revert, -1)


def test_record_replace_refs(app, db):
    """Test the replacement of JSON references using JSONResolver."""
    record = Record.create({
        'one': {'$ref': 'http://nest.ed/A'},
        'three': {'$ref': 'http://nest.ed/ABC'}
    })
    with pytest.raises(ImportError):
        app.extensions['invenio-records'].loader_cls = json_loader_factory(
            JSONResolver(plugins=['demo.json_resolver']))
        out_json = record.replace_refs()
    # expected_json = {
    #     'one': {
    #         'letter': 'A',
    #         'next': '.',
    #     },
    #     'three': {
    #         'letter': 'A',
    #         'next': {
    #             'letter': 'B',
    #             'next': {
    #                 'letter': 'C',
    #                 'next': '.',
    #             },
    #         },
    #     },
    # }
    # assert out_json == expected_json


def test_replace_refs_deepcopy(app):
    """Test problem with replace_refs and deepcopy."""
    with app.app_context():
        assert copy.deepcopy(Record({'recid': 1}).replace_refs()) \
            == {'recid': 1}


def test_record_dump(app, db):
    """Test record dump method."""
    with app.app_context():
        record = Record.create({'foo': {'bar': 'Bazz', }, })
        record_dump = record.dumps()
        record_dump['foo']['bar'] = 'Spam'
        assert record_dump['foo']['bar'] != record['foo']['bar']


def test_validate_with_format(app, db):
    """Test that validation can accept custom format rules."""
    with app.app_context():
        checker = FormatChecker()
        checker.checks('foo')(lambda el: el.startswith('foo'))
        data = {
            'bar': 'foo',
            '$schema': {
                'properties': {
                    'bar': {'format': 'foo'}
                }
            }
        }

        # test record creation with valid data
        assert data == Record.create(data)
        record = Record.create(data, format_checker=checker)
        # test direct call to validate with valid data
        assert record.validate(format_checker=checker) is None
        # test commit with valid data
        record.commit(format_checker=checker)

        record['bar'] = 'bar'
        # test direct call to validate with invalid data
        with pytest.raises(ValidationError) as excinfo:
            record.validate(format_checker=checker)
        assert "'bar' is not a 'foo'" in str(excinfo.value)
        # test commit with invalid data
        with pytest.raises(ValidationError) as excinfo:
            record.commit(format_checker=checker)
        assert "'bar' is not a 'foo'" in str(excinfo.value)

        data['bar'] = 'bar'
        # test record creation with invalid data
        with pytest.raises(ValidationError) as excinfo:
            record = Record.create(data, format_checker=checker)
        assert "'bar' is not a 'foo'" in str(excinfo.value)


def test_validate_partial(app, db):
    """Test partial validation."""
    schema = {
        'properties': {
            'a': {'type': 'string'},
            'b': {'type': 'string'},
        },
        'required': ['b']
    }
    data = {
        'a': 'hello',
        '$schema': schema
    }
    with app.app_context():
        # Test validation on create()

        # normal validation should fail because 'b' is required
        with pytest.raises(ValidationError) as exc_info:
            Record.create(data)
        assert "'b' is a required property" == exc_info.value.message
        # validate with a less restrictive validator
        record = Record.create(data, validator=PartialDraft4Validator)
        # set wrong data types should fails in any case
        data_incorrect = copy.deepcopy(data)
        data_incorrect['a'] = 1
        with pytest.raises(ValidationError) as exc_info:
            Record.create(data_incorrect, validator=PartialDraft4Validator)
        assert "1 is not of type 'string'" == exc_info.value.message

        # Test validation on commit()

        # validation not passing with normal validator
        with pytest.raises(ValidationError) as exc_info:
            record.commit()
        assert "'b' is a required property" == exc_info.value.message
        # validation passing with less restrictive validator
        assert data == record.commit(validator=PartialDraft4Validator)
        # set wrong data types should fails in any case
        record['a'] = 1
        with pytest.raises(ValidationError) as exc_info:
            record.commit(validator=PartialDraft4Validator)

@pytest.mark.parametrize(
    "fix_accessrights, access_path, updated, meta_patch, expected",
    [
        # Empty data
        (True, None, None, {}, None),

        # Only updated is set
        (True, None, datetime(2026, 3, 1, 0, 0, 0), None, datetime(2026, 3, 1, 0, 0, 0)),

        # item_type_id is None
        (True, None, datetime(2026, 3, 1, 0, 0, 0), {"item_type_id": None}, datetime(2026, 3, 1, 0, 0, 0)),

        # Only item_type_id is set
        (True, None, datetime(2026, 3, 1, 0, 0, 0), {"item_type_id": 1}, datetime(2026, 3, 1, 0, 0, 0)),

        # Empty file attribute
        (True, None, datetime(2026, 3, 1, 0, 0, 0), {
            "item_type_id": 1,
            "item_1736146823660": {
                "attribute_name": "アクセス権",
                "attribute_value_mlt": []
            }
        }, datetime(2026, 3, 1, 0, 0, 0)),

        # Empty file attribute (updated=None)
        (True, None, None, {"item_type_id": 1, "item_foo": {"attribute_type": "file", "attribute_value_mlt": []}}, None),

        # open_date is in the future
        (True, "item_1736146823660.attribute_value_mlt.subitem_access_right", datetime(2027, 1, 1, 0, 0, 0), {
            "item_type_id": 1,
            "item_1736146823660": {
                "attribute_name": "アクセス権",
                "attribute_value_mlt": [
                    {
                        "subitem_access_right": "embargoed access",
                        "subitem_access_right_uri": "http://purl.org/coar/access_right/c_f1cf"
                    }
                ]
            },
            "item_1736148125517": {
                "attribute_type": "file",
                "attribute_value_mlt": [
                    {"date": [{"dateType": "Available", "dateValue": "2026-12-31"}], "accessrole": "open_date"}
                ]
            }
        }, datetime(2027, 1, 1, 0, 0, 0)),

        # open_date is in the past
        (True, "item_1736146823660.attribute_value_mlt.subitem_access_right", datetime(2026, 3, 1, 0, 0, 0), {
            "item_type_id": 1,
            "item_1736146823660": {
                "attribute_name": "アクセス権",
                "attribute_value_mlt": [
                    {
                        "subitem_access_right": "embargoed access",
                        "subitem_access_right_uri": "http://purl.org/coar/access_right/c_f1cf"
                    }
                ]
            },
            "item_1736148125517": {
                "attribute_type": "file",
                "attribute_value_mlt": [
                    {"date": [{"dateType": "Available", "dateValue": "2026-01-01"}], "accessrole": "open_date"}
                ]
            }
        }, datetime(2026, 3, 1, 0, 0, 0)),

        # open_access file
        (True, "item_1736146823660.attribute_value_mlt.subitem_access_right", datetime(2026, 3, 1, 0, 0, 0), {
            "item_type_id": 1,
            "item_1736146823660": {
                "attribute_name": "アクセス権",
                "attribute_value_mlt": [
                    {
                        "subitem_access_right": "embargoed access",
                        "subitem_access_right_uri": "http://purl.org/coar/access_right/c_f1cf"
                    }
                ]
            },
            "item_1736148125517": {
                "attribute_type": "file",
                "attribute_value_mlt": [
                    {"date": [{"dateType": "Available", "dateValue": "2026-04-01"}], "accessrole": "open_access"}
                ]
            }
        }, datetime(2026, 4, 1, 0, 0, 0)),

        # date exists but no accessrole
        (True, "item_1736146823660.attribute_value_mlt.subitem_access_right", datetime(2026, 3, 1, 0, 0, 0), {
            "item_type_id": 1,
            "item_1736146823660": {
                "attribute_name": "アクセス権",
                "attribute_value_mlt": [
                    {
                        "subitem_access_right": "embargoed access",
                        "subitem_access_right_uri": "http://purl.org/coar/access_right/c_f1cf"
                    }
                ]
            },
            "item_1736148125517": {
                "attribute_type": "file",
                "attribute_value_mlt": [
                    {"date": [{"dateType": "Available", "dateValue": "2027-01-01"}]}
                ]
            }
        }, datetime(2026, 3, 1, 0, 0, 0)),

        # accessrole exists but no date
        (True, "item_1736146823660.attribute_value_mlt.subitem_access_right", datetime(2026, 3, 1, 0, 0, 0), {
            "item_type_id": 1,
            "item_1736146823660": {
                "attribute_name": "アクセス権",
                "attribute_value_mlt": [
                    {
                        "subitem_access_right": "embargoed access",
                        "subitem_access_right_uri": "http://purl.org/coar/access_right/c_f1cf"
                    }
                ]
            },
            "item_1736148125517": {
                "attribute_type": "file",
                "attribute_value_mlt": [
                    {"accessrole": "open_date"}
                ]
            }
        }, datetime(2026, 3, 1, 0, 0, 0)),

        # Multiple open_dates (with access rights info)
        (True, "item_1736146823660.attribute_value_mlt.subitem_access_right", datetime(2026, 3, 1, 0, 0, 0), {
            "item_type_id": 1,
            "item_1736146823660": {
                "attribute_name": "アクセス権",
                "attribute_value_mlt": [
                    {
                        "subitem_access_right": "embargoed access",
                        "subitem_access_right_uri": "http://purl.org/coar/access_right/c_f1cf"
                    }
                ]
            },
            "item_1736148125517": {
                "attribute_type": "file",
                "attribute_value_mlt": [
                    {"date": [{"dateType": "Available", "dateValue": "2026-03-31"}], "accessrole": "open_date"},
                    {"date": [{"dateType": "Available", "dateValue": "2026-03-30"}], "accessrole": "open_date"}
                ]
            }
        }, datetime(2026, 3, 31, 0, 0, 0)),

        # Multiple open_dates (with access rights info), original_updated > max(open_dates)
        (True, "item_1736146823660.attribute_value_mlt.subitem_access_right", datetime(2026, 4, 2, 0, 0, 0), {
            "item_type_id": 1,
            "item_1736146823660": {
                "attribute_name": "アクセス権",
                "attribute_value_mlt": [
                    {
                        "subitem_access_right": "embargoed access",
                        "subitem_access_right_uri": "http://purl.org/coar/access_right/c_f1cf"
                    }
                ]
            },
            "item_1736148125517": {
                "attribute_type": "file",
                "attribute_value_mlt": [
                    {"date": [{"dateType": "Available", "dateValue": "2026-03-31"}], "accessrole": "open_date"},
                    {"date": [{"dateType": "Available", "dateValue": "2026-03-30"}], "accessrole": "open_date"}
                ]
            }
        }, datetime(2026, 4, 2, 0, 0, 0)),
        # WEKO_SEARCH_FIX_ACCESSRIGHTS is False
        (False, "item_1736146823660.attribute_value_mlt.subitem_access_right", datetime(2026, 3, 1, 0, 0, 0), {
            "item_type_id": 1,
            "item_1736146823660": {
                "attribute_name": "アクセス権",
                "attribute_value_mlt": [
                    {
                        "subitem_access_right": "embargoed access",
                        "subitem_access_right_uri": "http://purl.org/coar/access_right/c_f1cf"
                    }
                ]
            },
            "item_1736148125517": {
                "attribute_type": "file",
                "attribute_value_mlt": [
                    {"date": [{"dateType": "Available", "dateValue": "2026-03-31"}], "accessrole": "open_date"},
                    {"date": [{"dateType": "Available", "dateValue": "2026-03-30"}], "accessrole": "open_date"}
                ]
            }
        }, datetime(2026, 3, 1, 0, 0, 0)),

        # _get_nested_value list branch (does not contain subitem_access_right)
        (True, "item_foo.subitem_access_right", datetime(2026, 3, 1, 0, 0, 0), {
            "item_type_id": 1,
            "item_foo": [
                {"not_target": 1}
            ]
        }, datetime(2026, 3, 1, 0, 0, 0)),

        #Case where attribute_mlt is not in the path
        (True, "item_foo.subitem_access_right",datetime(2026, 3, 1, 0, 0, 0), {
                "item_type_id": 1,
                "item_foo": {
                    "attribute_type": "アクセス権",
                    "attribute_value_mlt": [
                        {"not_target": 1},
                        {"subitem_access_right": "embargoed access"}
                    ]
                }
            },
            datetime(2026, 3, 1, 0, 0, 0)
        ),

        # Case where the path key does not exist
        (True,"item_foo.subitem_access_right", datetime(2026, 3, 1, 0, 0, 0), {
                "item_type_id": 1,
                "item_foo": {
                    "attribute_type": "file",
                    "attribute_value_mlt": [
                        {"not_target": 1}
                    ]
                }
            },
            datetime(2026, 3, 1, 0, 0, 0)
        ),

        # Case where value is neither list nor dict
        (True, "item_foo.subitem_access_right" ,datetime(2026, 3, 1, 0, 0, 0),{
                "item_type_id": 1,
                "item_foo": {
                    "attribute_type": "アクセス権",
                    "attribute_value_mlt": "invalid"
                }
            },
            datetime(2026, 3, 1, 0, 0, 0)
        ),

        # Case where updated is None but opendate exists
        (True, "item_1736146823660.attribute_value_mlt.subitem_access_right" ,None, {
                "item_type_id": 1,
                "item_1736146823660": {
                    "attribute_name": "アクセス権",
                    "attribute_value_mlt": [
                        {
                            "subitem_access_right": "embargoed access",
                            "subitem_access_right_uri": "http://purl.org/coar/access_right/c_f1cf"
                        }
                    ]
                },
                "item_1736148125517": {
                    "attribute_type": "file",
                    "attribute_value_mlt": [
                        {"date": [{"dateType": "Available", "dateValue": "2026-03-31"}], "accessrole": "open_date"}
                    ]
                }
            },
            datetime(2026, 3, 31, 0, 0, 0)
        ),
    ]
)
# .tox/c1/bin/pytest --cov=invenio_records tests/test_api.py::test_record_updated -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-records/.tox/c1/tmp
def test_record_updated(app, monkeypatch, access_path, fix_accessrights, updated, meta_patch, expected):
    base_meta = {
        "item_type_id": 1
    }
    meta = copy.deepcopy(base_meta)
    if meta_patch is not None:
        meta.update(copy.deepcopy(meta_patch))
    else:
        meta = None

    class DummyQuery:
        def filter_by(self, id):
            return self
        def scalar(self):
            return meta

    class DummySession:
        def __init__(self):
            self.session = self
        def query(self, *args, **kwargs):
            return DummyQuery()

    monkeypatch.setattr("weko_records.serializers.utils.get_mapping", lambda i, t: {"accessRights.@value": access_path})
    with app.app_context():
        from flask import current_app
        current_app.config["WEKO_SEARCH_FIX_ACCESSRIGHTS"] = fix_accessrights
        record = Record({})
        class DummyModel:
            def __init__(self, updated, json, id=1):
                self.updated = updated
                self.json = json
                self.id = id
        record.model = DummyModel(updated=updated, json=meta, id=1)
        monkeypatch.setattr("invenio_records.api.db", DummySession())
        result = record.updated
        assert result == expected

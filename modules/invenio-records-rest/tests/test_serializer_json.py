# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio serializer tests."""

import json

from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record
from invenio_rest.serializer import BaseSchema as Schema
from marshmallow import fields

from invenio_records_rest.schemas.fields import PersistentIdentifier as PIDField
from invenio_records_rest.serializers.json import JSONSerializer


def test_serialize(app, db):
    """Test JSON serialize."""
    app.config['WEKO_RECORDS_UI_EMAIL_ITEM_KEYS'] = ['creatorMails', 'contributorMails', 'mails']

    class TestSchema(Schema):
        title = fields.Str(attribute="metadata.mytitle")
        id = PIDField(attribute="pid.pid_value")

    data = json.loads(
        JSONSerializer(TestSchema).serialize(
            PersistentIdentifier(pid_type="recid", pid_value="2"),
            Record({"mytitle": "test"}),
        )
    )
    assert data["title"] == "test"
    assert data["id"] == "2"

def test_serialize2(app, db, item_type):
    """Test JSON serialize."""
    app.config["WEKO_RECORDS_UI_EMAIL_ITEM_KEYS"] = ["creatorMails", "contributorMails", "mails"]

    class TestSchema(Schema):
        title = fields.Str(attribute="metadata.mytitle")
        id = PIDField(attribute="pid.pid_value")
        metadata = fields.Raw()

    data = json.loads(JSONSerializer(TestSchema).serialize(
        PersistentIdentifier(pid_type="recid", pid_value="3"),
        Record(
        {
            "item_type_id": "15",
            "mytitle": "test",
            "_deposit": {
                "owners": [1],
                "owners_ext": {
                    "username": "test username",
                    "displayname": "test displayname",
                    "email": "test@test.com"
                }
            },
            "publish_date": "2021-08-06",
            "publish_status": "0"
        })
    ))
    assert data == {
        "id": "3",
        "metadata": {
            "item_type_id": "15",
            "_deposit": {
                "owners": [1]
            },
            "mytitle": "test",
            "publish_date": "2021-08-06",
            "publish_status": "0"
        },
        "title": "test"
    }


def test_serialize_search(app, db):
    """Test JSON serialize."""
    app.config['WEKO_RECORDS_UI_EMAIL_ITEM_KEYS'] = ['creatorMails', 'contributorMails', 'mails']

    class TestSchema(Schema):
        title = fields.Str(attribute="metadata.mytitle")
        id = PIDField(attribute="pid.pid_value")

    def fetcher(obj_uuid, data):
        assert obj_uuid in ["a", "b"]
        return PersistentIdentifier(pid_type="recid", pid_value=data["pid"])

    total = dict(value=2)
    data = json.loads(
        JSONSerializer(TestSchema).serialize_search(
            fetcher,
            dict(
                hits=dict(
                    hits=[
                        {
                            "_source": dict(mytitle="test1", pid="1"),
                            "_id": "a",
                            "_version": 1,
                        },
                        {
                            "_source": dict(mytitle="test2", pid="2"),
                            "_id": "b",
                            "_version": 1,
                        },
                    ],
                    total=total,
                ),
                aggregations={},
            ),
        )
    )

    assert data["aggregations"] == {}
    assert "links" in data
    assert data["hits"] == dict(
        hits=[
            dict(title="test1", id="1"),
            dict(title="test2", id="2"),
        ],
        total=2,
    )


def test_serialize_search2(app, db, item_type):
    """Test JSON serialize."""
    app.config["WEKO_RECORDS_UI_EMAIL_ITEM_KEYS"] = ["creatorMails", "contributorMails", "mails"]

    class TestSchema(Schema):
        title = fields.Str(attribute="metadata.mytitle")
        id = PIDField(attribute="pid.pid_value")
        metadata = fields.Raw()

    def fetcher(obj_uuid, data):
        assert obj_uuid in ["a", "b"]
        return PersistentIdentifier(pid_type="recid", pid_value=data["pid"])

    total = dict(value=2)
    data = json.loads(JSONSerializer(TestSchema).serialize_search(
        fetcher,
        dict(
            hits=dict(
                hits=[
                    {
                        "_source": {
                            "_item_metadata": {
                                "_deposit": {
                                    "owners": [1],
                                    "owners_ext": {
                                        "username": "test username",
                                        "displayname": "test displayname",
                                        "email": "test@test.com"
                                    }
                                },
                                "publish_date": "2021-08-06",
                                "item_type_id": "15"
                            },
                            "feedback_mail_list": [
                                "test@test.com"
                            ],
                            "pid": "1"
                        },
                        "_id": "a",
                        "_version": 1
                    },
                ],
                total=total,
            ),
            aggregations={},
        )
    ))

    assert data["aggregations"] == {}
    assert "links" in data
    assert data["hits"] == {
        "hits": [
            {
                "id": "1",
                "metadata": {
                    "_item_metadata": {
                        "_deposit": {
                            "owners": [1]
                        },
                        "publish_date": "2021-08-06",
                        "item_type_id": "15"
                    },
                    "feedback_mail_list": [], "pid": "1"
                }
            }
        ],
        "total": total
    }


def test_serialize_pretty(app, db):
    """Test pretty JSON."""
    app.config['WEKO_RECORDS_UI_EMAIL_ITEM_KEYS'] = ['creatorMails', 'contributorMails', 'mails']

    class TestSchema(Schema):
        title = fields.Str(attribute="metadata.title")

    pid = (PersistentIdentifier(pid_type="recid", pid_value="2"),)
    rec = Record({"title": "test"})

    with app.test_request_context():
        assert JSONSerializer(TestSchema).serialize(pid, rec) == '{"title":"test"}'

    with app.test_request_context("/?prettyprint=1"):
        assert (
            JSONSerializer(TestSchema).serialize(pid, rec) == '{\n  "title": "test"\n}'
        )
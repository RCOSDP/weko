# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2020 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test Invenio Records."""


import uuid

import pytest
from invenio_db import InvenioDB
from invenio_db import db as db_
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy_utils.functions import create_database, database_exists

from invenio_records import Record
from invenio_records.models import RecordMetadataBase


@pytest.fixture(scope="module")
def CustomMetadata(database):
    """."""
    db = database

    class CustomMetadata(db.Model, RecordMetadataBase):
        __tablename__ = "custom_metadata"

    CustomMetadata.__table__.create(db.engine)
    return CustomMetadata


def test_class_model(testapp, database, CustomMetadata):
    """Test custom class model."""
    db = database

    class CustomRecord(Record):
        model_cls = CustomMetadata

    assert "custom_metadata" in db.metadata.tables.keys()

    recid = uuid.UUID("262d2748-ba41-456f-a844-4d043a419a6f")

    # Create a new record with two mutables, a list and a dict
    rec = CustomRecord.create(
        {
            "title": "Title",
            "list": [
                "foo",
            ],
            "dict": {"moo": "boo"},
        },
        id_=recid,
    )

    db.session.commit()
    db.session.expunge_all()
    # record should be in the table
    rec = CustomRecord.get_record(recid)
    assert rec == {
        "title": "Title",
        "list": [
            "foo",
        ],
        "dict": {"moo": "boo"},
    }
    # the record should not be in the default table
    pytest.raises(NoResultFound, Record.get_record, recid)

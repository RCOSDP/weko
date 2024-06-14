# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

import uuid
from unittest.mock import MagicMock, patch

import pytz
from flask import Flask
from invenio_db import db
from invenio_records import Record
from invenio_search.engine import check_os_version

from invenio_indexer import InvenioIndexer
from invenio_indexer.api import RecordIndexer
from invenio_indexer.signals import before_record_index

_global_magic_hook = MagicMock()
"""Iternal importable magic hook instance."""


def test_version():
    """Test version import."""
    from invenio_indexer import __version__

    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask("testapp")
    ext = InvenioIndexer(app)
    assert "invenio-indexer" in app.extensions

    app = Flask("testapp")
    ext = InvenioIndexer()
    assert "invenio-indexer" not in app.extensions
    ext.init_app(app)
    assert "invenio-indexer" in app.extensions


def test_hook_initialization(base_app):
    """Test hook initialization."""
    app = base_app
    magic_hook = MagicMock()
    app.config["INDEXER_BEFORE_INDEX_HOOKS"] = [
        magic_hook,
        "test_invenio_indexer:_global_magic_hook",
    ]
    ext = InvenioIndexer(app)

    with app.app_context():
        recid = uuid.uuid4()
        record = Record.create({"title": "Test"}, id_=recid)
        db.session.commit()

        client_mock = MagicMock()
        RecordIndexer(search_client=client_mock, version_type="force").index(record)
        args = (app,)
        kwargs = dict(
            index=app.config["INDEXER_DEFAULT_INDEX"],
            arguments={},
            record=record,
            json={
                "title": "Test",
                "_created": pytz.utc.localize(record.created).isoformat(),
                "_updated": pytz.utc.localize(record.updated).isoformat(),
            },
        )
        magic_hook.assert_called_with(*args, **kwargs)
        _global_magic_hook.assert_called_with(*args, **kwargs)
        client_mock.index.assert_called_with(
            id=str(recid),
            version=0,
            version_type="force",
            index=app.config["INDEXER_DEFAULT_INDEX"],
            body={
                "title": "Test",
                "_created": pytz.utc.localize(record.created).isoformat(),
                "_updated": pytz.utc.localize(record.updated).isoformat(),
            },
        )


def test_index_prefixing(base_app):
    """Test index prefixing."""
    app = base_app
    app.config["INDEXER_REPLACE_REFS"] = False
    app.config["SEARCH_INDEX_PREFIX"] = "test-"
    ext = InvenioIndexer(app)

    default_index = app.config["INDEXER_DEFAULT_INDEX"]

    with app.app_context():
        with patch("invenio_records.api._records_state.validate"):
            record = Record.create({"title": "Test"})
            record2 = Record.create(
                {
                    "$schema": "/records/authorities/authority-v1.0.0.json",
                    "title": "Test with schema",
                }
            )
            record3 = Record.create({"title": "Test"})
            record3.delete()
        db.session.commit()

        with patch(
            "invenio_indexer.signals.before_record_index.send"
        ) as before_record_index_send:
            client_mock = MagicMock()
            RecordIndexer(search_client=client_mock).index(record)
            client_mock.index.assert_called_with(
                id=str(record.id),
                version=0,
                version_type="external_gte",
                index="test-" + default_index,
                body={
                    "title": "Test",
                    "_created": pytz.utc.localize(record.created).isoformat(),
                    "_updated": pytz.utc.localize(record.updated).isoformat(),
                },
            )
            before_record_index_send.assert_called_with(
                app,
                json={
                    "title": "Test",
                    "_created": pytz.utc.localize(record.created).isoformat(),
                    "_updated": pytz.utc.localize(record.updated).isoformat(),
                },
                record=record,
                index=default_index,  # non-prefixed index passed to receiver
                arguments={},
            )

            RecordIndexer(search_client=client_mock).index(record2)
            client_mock.index.assert_called_with(
                id=str(record2.id),
                version=0,
                version_type="external_gte",
                index="test-records-authorities-authority-v1.0.0",
                body={
                    "$schema": "/records/authorities/authority-v1.0.0.json",
                    "title": "Test with schema",
                    "_created": pytz.utc.localize(record2.created).isoformat(),
                    "_updated": pytz.utc.localize(record2.updated).isoformat(),
                },
            )
            before_record_index_send.assert_called_with(
                app,
                json={
                    "$schema": "/records/authorities/authority-v1.0.0.json",
                    "title": "Test with schema",
                    "_created": pytz.utc.localize(record2.created).isoformat(),
                    "_updated": pytz.utc.localize(record2.updated).isoformat(),
                },
                record=record2,
                index="records-authorities-authority-v1.0.0",  # no prefix
                arguments={},
            )
            RecordIndexer(search_client=client_mock).delete(record3)
            client_mock.delete.assert_called_with(
                id=str(record3.id),
                index="test-" + default_index,
                version=record3.revision_id,
                version_type="external_gte",
            )

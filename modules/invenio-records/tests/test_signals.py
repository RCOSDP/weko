# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test Invenio Records API."""

from functools import partial

import pytest

from invenio_records.api import Record
from invenio_records.signals import (
    after_record_delete,
    after_record_insert,
    after_record_revert,
    after_record_update,
    before_record_delete,
    before_record_insert,
    before_record_revert,
    before_record_update,
)


@pytest.fixture()
def signals():
    """Fixtures to connect signals."""
    called = {}

    def _listener(signal_name, sender, *args, **kwargs):
        if signal_name not in called:
            called[signal_name] = 0
        called[signal_name] += 1

    after_record_delete_listener = partial(_listener, "after_record_delete")
    after_record_insert_listener = partial(_listener, "after_record_insert")
    after_record_revert_listener = partial(_listener, "after_record_revert")
    after_record_update_listener = partial(_listener, "after_record_update")
    before_record_delete_listener = partial(_listener, "before_record_delete")
    before_record_insert_listener = partial(_listener, "before_record_insert")
    before_record_revert_listener = partial(_listener, "before_record_revert")
    before_record_update_listener = partial(_listener, "before_record_update")
    before_record_insert_listener = partial(_listener, "before_record_insert")

    after_record_delete.connect(after_record_delete_listener)
    after_record_insert.connect(after_record_insert_listener)
    after_record_revert.connect(after_record_revert_listener)
    after_record_update.connect(after_record_update_listener)
    before_record_delete.connect(before_record_delete_listener)
    before_record_insert.connect(before_record_insert_listener)
    before_record_revert.connect(before_record_revert_listener)
    before_record_update.connect(before_record_update_listener)
    before_record_insert.connect(before_record_insert_listener)

    yield called

    after_record_delete.disconnect(after_record_delete_listener)
    after_record_insert.disconnect(after_record_insert_listener)
    after_record_revert.disconnect(after_record_revert_listener)
    after_record_update.disconnect(after_record_update_listener)
    before_record_delete.disconnect(before_record_delete_listener)
    before_record_insert.disconnect(before_record_insert_listener)
    before_record_revert.disconnect(before_record_revert_listener)
    before_record_update.disconnect(before_record_update_listener)
    before_record_insert.disconnect(before_record_insert_listener)


def test_signals(testapp, database, signals):
    """Test signals being sent."""
    db = database
    record = Record.create({"title": "Test"})
    db.session.commit()
    assert "before_record_insert" in signals
    assert "after_record_insert" in signals
    assert len(signals.keys()) == 2

    record["title"] = "Test2"
    record.commit()
    db.session.commit()
    assert "before_record_update" in signals
    assert "after_record_update" in signals
    assert len(signals.keys()) == 4

    record.revert(0)
    db.session.commit()
    assert "before_record_revert" in signals
    assert "after_record_revert" in signals
    assert len(signals.keys()) == 6

    record.delete()
    db.session.commit()
    assert "before_record_delete" in signals
    assert "after_record_delete" in signals
    assert len(signals.keys()) == 8


def test_signals_disabled(testapp, database, signals):
    """Test signals being sent."""
    db = database

    class MyRecord(Record):
        # Disable signals
        send_signals = False

    # Same operations as above (but none of them should send signals)
    record = MyRecord.create({"title": "Test"})
    db.session.commit()
    record["title"] = "Test2"
    record.commit()
    db.session.commit()
    record.revert(0)
    db.session.commit()
    record.delete()
    db.session.commit()

    # Assert that no signals was sent.
    assert len(signals.keys()) == 0

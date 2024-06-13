# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
# Copyright (C) 2022 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Percolator test cases."""

import pytest
from helpers import create_record, run_after_insert_oai_set
from invenio_db import db
from invenio_search import current_search

from invenio_oaiserver.models import OAISet
from invenio_oaiserver.query import OAINoRecordsMatchError, get_records
from invenio_oaiserver.receivers import after_update_oai_set


@pytest.fixture()
def test0(app, without_oaiset_signals, schema):
    _ = create_record(app, {"title_statement": {"title": "Test0"}, "$schema": schema})
    current_search.flush_and_refresh("records")


def create_oaiset(name, title_pattern):
    oaiset = OAISet(
        spec=name,
        search_pattern=f"title_statement.title:{title_pattern}",
        system_created=False,
    )
    db.session.add(oaiset)
    db.session.commit()
    run_after_insert_oai_set()

    return oaiset


def test_set_with_no_records(without_oaiset_signals, schema):
    _ = create_oaiset("test", "Test0")
    with pytest.raises(OAINoRecordsMatchError):
        get_records(set="test")


def test_empty_set(without_oaiset_signals, test0):
    _ = create_oaiset("test", "Test1")
    with pytest.raises(OAINoRecordsMatchError):
        get_records(set="test")


def test_set_with_records(app, without_oaiset_signals, test0, schema):
    # create extra record
    _ = create_record(app, {"title_statement": {"title": "Test1"}, "$schema": schema})
    current_search.flush_and_refresh("records")

    # create and query set
    _ = create_oaiset("test", "Test0")
    rec_in_set = get_records(set="test")
    assert rec_in_set.total == 1
    rec = next(rec_in_set.items)
    assert rec["json"]["_source"]["title_statement"]["title"] == "Test0"


def test_search_pattern_change(without_oaiset_signals, test0):
    """Test search pattern change."""
    # create set
    oaiset = create_oaiset("test", "Test0")
    # check record is in set
    rec_in_set = get_records(set="test")
    assert rec_in_set.total == 1
    rec = next(rec_in_set.items)
    assert rec["json"]["_source"]["title_statement"]["title"] == "Test0"

    # change search pattern
    oaiset.search_pattern = "title_statement.title:Test1"
    db.session.merge(oaiset)
    db.session.commit()
    after_update_oai_set(None, None, oaiset)
    # check records is not in set
    with pytest.raises(OAINoRecordsMatchError):
        get_records(set="test")

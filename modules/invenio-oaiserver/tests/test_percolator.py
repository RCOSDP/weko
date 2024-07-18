# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
# Copyright (C) 2022 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Percolator test cases."""

import uuid
import os
import pytest
from mock import patch
from flask import Flask
from sqlalchemy_utils.functions import create_database, database_exists
from invenio_cache import InvenioCache, current_cache
from invenio_db import db as db_
from invenio_db import InvenioDB
from invenio_records.api import Record
from invenio_records.models import RecordMetadata
from invenio_search import current_search, current_search_client


from invenio_oaiserver import current_oaiserver, InvenioOAIServer
from invenio_oaiserver.models import OAISet
from invenio_oaiserver.query import OAINoRecordsMatchError, get_records
from invenio_oaiserver.receivers import after_update_oai_set

from invenio_oaiserver.percolator import (
    _create_percolator_mapping,
    _percolate_query,
    _get_percolator_doc_type,
    _new_percolator,
    _delete_percolator,
    _build_cache,
    get_record_sets
)

from .helpers import create_record, run_after_insert_oai_set

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_percolator.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp

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
    db__.session.add(oaiset)
    db_.session.commit()
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
    db_.session.merge(oaiset)
    db_.session.commit()
    after_update_oai_set(None, None, oaiset)
    # check records is not in set
    with pytest.raises(OAINoRecordsMatchError):
        get_records(set="test")

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_percolator.py::test_create_percolator_mapping -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_create_percolator_mapping(es_app):
    index = "test-weko-item-v1.0.0"
    # es_version = 6
    _create_percolator_mapping(index,"percolators")
    
    with patch("invenio_oaiserver.percolator.ES_VERSION",[2]):
        _create_percolator_mapping(index,"percolators")

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_percolator.py::test_percolate_query -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_percolate_query(es_app):
    current_search_client.indices.put_mapping(
        index="test-weko-item-v1.0.0", doc_type="item-v1.0.0",
        body={
            'properties': {'query': {'type': 'percolator'}}
        }, ignore=[400, 404])
    current_search_client.index(
        index="test-weko-item-v1.0.0", doc_type="item-v1.0.0",
        id="oaiset-1",body={
            "query":{'query_string': {'query': 'test_pettern'}}
        }
    )
    result = _percolate_query("test-weko-item-v1.0.0","item-v1.0.0","item-v1.0.0",{})
    assert result == []
    with patch("invenio_oaiserver.percolator.ES_VERSION",[7]):
        result = _percolate_query("test-weko-item-v1.0.0","item_v1.0.0","item_v1.0.0",{})
        assert result == None
    
    def mock_percolate(index=None,doc_type=None,allow_no_indices=True,ignore_unavailable=True,body={}):
        return {"matches":[]}
    with patch("invenio_oaiserver.percolator.ES_VERSION",[2]):
        setattr(current_search_client,"percolate",mock_percolate)
        result = _percolate_query("test-weko-item-v1.0.0","item-v1.0.0","item-v1.0.0",{})
        assert result == []

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_percolator.py::test_get_percolator_doc_type -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_get_percolator_doc_type(es_app):
    index = "test-weko-item-v1.0.0"
    
    # es_version = 2
    with patch("invenio_oaiserver.percolator.ES_VERSION",[2]):
        result = _get_percolator_doc_type(index)
        assert result == ".percolator"
    
    # es_version = 5
    with patch("invenio_oaiserver.percolator.ES_VERSION",[5]):
        result = _get_percolator_doc_type(index)
        assert result == "percolators"

    # es_version = 6
    result = _get_percolator_doc_type(index)
    assert result == "item-v1.0.0"
    
    # other
    with patch("invenio_oaiserver.percolator.ES_VERSION",[7]):
        result = _get_percolator_doc_type(index)
        assert result == None


# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_percolator.py::test_new_percolator -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_new_percolator(es_app,db,without_oaiset_signals,mocker):
    mocker.patch("invenio_oaiserver.percolator.INDEXER_DEFAULT_INDEX","test-weko-item-v1.0.0")
    oai = OAISet(id=1,
        spec='test',
        name='test_name',
        description='some test description',
        search_pattern="test_pettern")

    db.session.add(oai)
    db.session.commit()
    _new_percolator(None,None)
    _new_percolator(spec=oai.spec,search_pattern=oai.search_pattern)

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_percolator.py::test_delete_percolator -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_delete_percolator(es_app,mocker):
    mocker.patch("invenio_oaiserver.percolator.INDEXER_DEFAULT_INDEX","test-weko-item-v1.0.0")

    # spec is None
    _delete_percolator(None,None)
    
    _delete_percolator("test","test")

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_percolator.py::test_build_cache -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_build_cache(instance_path):
    app = Flask("test_app",instance_path=instance_path)
    app.config.update(
        CACHE_REDIS_URL='redis://redis:6379/0',
        CACHE_REDIS_DB='0',
        CACHE_REDIS_HOST="redis",
        OAISERVER_CACHE_KEY="DynamicOAISets::",
        OAISERVER_REGISTER_RECORD_SIGNALS=True,
        OAISERVER_REGISTER_SET_SIGNALS=True,
        SQLALCHEMY_DATABASE_URI=os.environ.get('SQLALCHEMY_DATABASE_URI',
                                               'sqlite:///test.db')
        )
    InvenioDB(app)
    InvenioCache(app)
    with app.app_context():
        current_cache.delete("DynamicOAISets::")
        InvenioOAIServer(app,cache=current_cache)
        current_oaiserver.unregister_signals_oaiset()
        if not database_exists(str(db_.engine.url)):
            create_database(str(db_.engine.url))
        db_.create_all()
        
        oai = OAISet(id=1,
            spec='test',
            name='test_name',
            description='some test description',
            search_pattern=None)
    
        db_.session.add(oai)
        db_.session.commit()
        
        result = _build_cache()
        assert result == ["test"]
        
        result = _build_cache()
        assert result == ["test"]
        
        current_oaiserver.register_signals_oaiset()
        db_.session.remove()
        db_.drop_all()
        
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_percolator.py::test_get_record_sets -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_get_record_sets(es_app,db,mocker):
    from weko_deposit.api import WekoDeposit
    mocker.patch("invenio_oaiserver.percolator._build_cache",return_value=["1","2"])
    data = {"_oai":{"sets":["1"]}}
    rec_uuid = uuid.uuid4()
    rec = RecordMetadata(id=rec_uuid,json=data)
    record = WekoDeposit(rec.json, rec)
    
    response = [
        {"_id":"oaiset-test"},
        {"_id":"notoaiset-test"}
    ]
    with patch("invenio_oaiserver.percolator._percolate_query",return_value=response):
        result = get_record_sets(record)

        result = [r for r in result]
        assert result == ["1","test"]

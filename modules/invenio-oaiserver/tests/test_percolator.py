# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
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
from invenio_oaiserver.errors import OAISetSpecUpdateError
from invenio_oaiserver.models import OAISet
from invenio_oaiserver.receivers import after_delete_oai_set, \
    after_insert_oai_set, after_update_oai_set
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

@pytest.mark.skip(reason="")
def test_search_pattern_change(app, without_oaiset_signals, schema, db):
    """Test search pattern change."""
    record0 = create_record(app, {
        '_oai': {'sets': ['a']}, 'title_statement': {'title': 'Test0'},
        '$schema': schema
    })
    rec_uuid = record0.id
    oaiset = OAISet(spec="a", search_pattern="title_statement.title:Test0")
    db.session.add(oaiset)
    db.session.commit()
    run_after_insert_oai_set()
    current_search.flush_and_refresh('records')
    record = Record.get_record(rec_uuid)
    assert record['_oai']['sets'] == ['a']

    # change search pattern: record0 will not inside it anymore
    oaiset = OAISet.query.first()
    oaiset.search_pattern = 'title_statement.title:Test1'
    db.session.merge(oaiset)
    db.session.commit()
    after_update_oai_set(None, None, oaiset)
    current_search.flush_and_refresh('records')
    record = Record.get_record(rec_uuid)
    record.commit()
    assert record['_oai']['sets'] == []


# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_percolator.py::test_populate_oaisets -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
@pytest.mark.skip(reason="")
def test_populate_oaisets(es_app, without_oaiset_signals, schema, db):
    """Populate OAISets."""
    def create_oaiset(**kwargs):
        oaiset = OAISet(**kwargs)
        db.session.add(oaiset)
        db.session.commit()
        return oaiset

    a = create_oaiset(spec='a')
    create_oaiset(spec='b')
    create_oaiset(
        spec="e", search_pattern="title_statement.title:Test2 OR "
        "title_statement.title:Test3")
    create_oaiset(spec="c", search_pattern="title_statement.title:Test0")
    create_oaiset(spec="d", search_pattern="title_statement.title:Test1")
    f = create_oaiset(spec="f", search_pattern="title_statement.title:Test2")
    create_oaiset(spec="g")
    create_oaiset(spec="h")
    i = create_oaiset(spec="i", search_pattern="title_statement.title:Test3")
    j = create_oaiset(spec="j with space",
                      search_pattern="title_statement.title:Test4")
    # Note below: brackets around AND search query are required
    create_oaiset(spec="math",
                  search_pattern="(title_statement.title:foo AND genre:math)")
    create_oaiset(spec="nonmath",
                  search_pattern="(title_statement.title:foo AND -genre:math)")

    run_after_insert_oai_set()

    a_id = OAISet.query.filter_by(spec=a.spec).one().id
    i_id = OAISet.query.filter_by(spec=i.spec).one().id

    # start tests

    record0 = create_record(es_app, {
        '_oai': {'sets': ['a']}, 'title_statement': {'title': 'Test0'},
        '$schema': schema
    })

    assert 'a' in record0['_oai']['sets'], 'Keep manually managed set "a".'
    #assert 'c' in record0['_oai']['sets']
    #assert len(record0['_oai']['sets']) == 2

    record_not_found = create_record(
        es_app, {'title': 'TestNotFound', '$schema': schema}
    )

    # Don't create empty sets list just because of commit
    assert 'sets' not in record_not_found['_oai']

    record1 = create_record(es_app, {'title_statement': {'title': 'Test1'},
                            '$schema': schema})

    assert 'd' in record1['_oai']['sets']
    assert len(record1['_oai']['sets']) == 1

    record2 = create_record(es_app, {'title_statement': {'title': 'Test2'},
                            '$schema': schema})
    record2_id = record2.id

    assert 'e' in record2['_oai']['sets']
    assert 'f' in record2['_oai']['sets']
    assert len(record2['_oai']['sets']) == 2

    record3 = create_record(es_app, {'title_statement': {'title': 'Test3'},
                            '$schema': schema})
    record3_id = record3.id

    assert 'e' in record3['_oai']['sets']
    assert 'i' in record3['_oai']['sets']
    assert len(record3['_oai']['sets']) == 2

    record4 = create_record(es_app, {'title_statement': {'title': 'Test4'},
                            '$schema': schema})
    record4_id = record4.id

    assert 'j with space' in record4['_oai']['sets']
    assert len(record4['_oai']['sets']) == 1

    # If record does not have '_oai', don't add any sets,
    # nor even the default '_oai' key
    record5 = create_record(es_app, {'title_statement': {'title': 'Test1'},
                            '$schema': schema},
                            mint_oaiid=False)
    assert '_oai' not in record5

    # Test 'AND' keyword for records
    record6 = create_record(es_app, {
        'title_statement': {'title': 'foo'},
        'genre': 'math', '$schema': schema
    })
    assert record6['_oai']['sets'] == ['math', ]

    record7 = create_record(es_app, {
        'title_statement': {'title': 'foo'},
        'genre': 'physics', '$schema': schema
    })
    assert record7['_oai']['sets'] == ['nonmath', ]

    record8 = create_record(es_app, {
        'title_statement': {'title': 'bar'},
        'genre': 'math', '$schema': schema
    })
    assert 'sets' not in record8['_oai']  # title is not 'foo'

    current_search.flush_and_refresh('records')

    # test delete
    current_oaiserver.unregister_signals_oaiset()
    with patch('invenio_oaiserver.receivers.after_delete_oai_set') as f:
        current_oaiserver.register_signals_oaiset()

        with db.session.begin_nested():
            db.session.delete(j)
        db.session.commit()
        assert f.called
        after_delete_oai_set(None, None, j)
        record4_model = RecordMetadata.query.filter_by(
            id=record4_id).first().json

        assert 'j with space' not in record4_model['_oai']['sets']
        assert len(record4_model['_oai']['sets']) == 0

        current_oaiserver.unregister_signals_oaiset()

    # test update search_pattern
    with patch('invenio_oaiserver.receivers.after_update_oai_set') as f:
        current_oaiserver.register_signals_oaiset()
        with db.session.begin_nested():
            i.search_pattern = None
            assert current_oaiserver.sets is None, 'Cache should be empty.'
            db.session.merge(i)
        db.session.commit()
        assert f.called
        i = OAISet.query.get(i_id)
        after_update_oai_set(None, None, i)
        record3_model = RecordMetadata.query.filter_by(
            id=record3_id).first().json

        assert 'i' in record3_model['_oai']['sets'], \
            'Set "i" is manually managed.'
        assert 'e' in record3_model['_oai']['sets']
        assert len(record3_model['_oai']['sets']) == 2

        current_oaiserver.unregister_signals_oaiset()

    # test update search_pattern
    with patch('invenio_oaiserver.receivers.after_update_oai_set') as f:
        current_oaiserver.register_signals_oaiset()

        with db.session.begin_nested():
            i.search_pattern = 'title_statement.title:Test3'
            db.session.merge(i)
        db.session.commit()
        assert f.called
        i = OAISet.query.get(i_id)
        after_update_oai_set(None, None, i)
        record3_model = RecordMetadata.query.filter_by(
            id=record3_id).first().json

        assert 'e' in record3_model['_oai']['sets']
        assert 'i' in record3_model['_oai']['sets']
        assert len(record3_model['_oai']['sets']) == 2

        current_oaiserver.unregister_signals_oaiset()

    # test update the spec
    with pytest.raises(OAISetSpecUpdateError) as exc_info:
        a = OAISet.query.get(a_id)
        a.spec = 'new-a'
    assert exc_info.type is OAISetSpecUpdateError

    # test create new set
    with patch('invenio_oaiserver.receivers.after_insert_oai_set') as f:
        current_oaiserver.register_signals_oaiset()

        with db.session.begin_nested():
            k = OAISet(spec="k", search_pattern="title_statement.title:Test2")
            db.session.add(k)
        db.session.commit()
        assert f.called
        after_insert_oai_set(None, None, k)
        record2_model = RecordMetadata.query.filter_by(
            id=record2_id).first().json

        assert 'e' in record2_model['_oai']['sets']
        assert 'f' in record2_model['_oai']['sets']
        assert 'k' in record2_model['_oai']['sets']
        assert len(record2_model['_oai']['sets']) == 3

        current_oaiserver.register_signals_oaiset()


def test_oaiset_add_remove_record(app, db):
    """Test the API method for manual record adding."""
    with app.app_context():
        oaiset1 = OAISet(spec='abc')
        rec1 = Record.create({'title_statement': {'title': 'Test1'}})
        rec1.commit()
        # Adding a record to an OAIset should change the record's updated date
        dt1 = rec1.updated
        assert not oaiset1.has_record(rec1)
        oaiset1.add_record(rec1)
        assert 'abc' in rec1['_oai']['sets']
        assert oaiset1.has_record(rec1)
        rec1.commit()
        dt2 = rec1.updated
        assert dt2 > dt1

        oaiset1.remove_record(rec1)
        rec1.commit()
        dt3 = rec1.updated
        assert 'abc' not in rec1['_oai']['sets']
        assert not oaiset1.has_record(rec1)
        assert dt3 > dt2


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
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                         'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),

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

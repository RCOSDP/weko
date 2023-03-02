import pytest
from datetime import datetime

from weko_schema_ui.utils import (
    dumps_oai_etree,
    dumps_etree,
    dumps,
    export_tree,
    json_merge_all,
    json_merge,
    dict_zip
)
from weko_schema_ui.utils import MISSING

# def dumps_oai_etree(pid, records, **kwargs):
# .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_utils.py::test_dumps_oai_etree -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
def test_dumps_oai_etree(app, db, records):
    assert dumps_oai_etree(records[1][0]['recid'], {'_source': records[1][0]['record']}, schema_type='jpcoar_v1')

# def dumps_etree(records, schema_type):
# .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_utils.py::test_dumps_etree -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
def test_dumps_etree(app, db, records):
    assert dumps_etree(records[1][0]['record_data'], None) == None
    assert dumps_etree({'metadata': {'_item_metadata': records[1][0]['record_data']}}, 'jpcoar_v1')

    assert dumps_etree(records[1][1]['record_data'], None) == None
    assert dumps_etree({'metadata': {'_item_metadata': records[1][1]['record_data']}}, 'jpcoar_v1')

    assert dumps_etree(records[1][2]['record_data'], None) == None
    assert dumps_etree({'metadata': {'_item_metadata': records[1][2]['record_data']}}, 'jpcoar_v1')

# def dumps(records, schema_type=None, **kwargs):
# .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_utils.py::test_dumps -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
def test_dumps(app, db, records):
    assert dumps({'metadata': records[1][0]['record'],
                  'updated': datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z')})
    records[1][0]['record']['@export_schema_type'] = 'jpcoar'
    assert dumps({'metadata': records[1][1]['record'],
                  'updated': datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z')})

# def export_tree(record, **kwargs):

# def json_merge_all(json_lst):
# .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_utils.py::test_json_merge_all -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
def test_json_merge_all():
    with pytest.raises(Exception) as e:
        json_merge_all({})
    assert e.type==ValueError
    assert str(e.value)=="json_lst was empty"
    assert json_merge_all({'test1': '1'}) == 'test1'

# def json_merge(a, b):
# .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_utils.py::test_json_merge -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
def test_json_merge():
    a = MISSING
    b = {'test1': '1'}
    assert json_merge(a, b) == {'test1': '1'}
    assert json_merge(b, a) == {'test1': '1'}

    a = {'test2': '2'}
    assert json_merge(a, b) == {'test1': '1', 'test2': '2'}
    assert json_merge([a], [b]) == [{'test2': '2'}, {'test1': '1'}]

# def dict_zip(*dicts, **kwargs):

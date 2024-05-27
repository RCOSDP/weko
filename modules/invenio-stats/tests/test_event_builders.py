import pytest
import tempfile
from datetime import datetime
from mock import patch
from six import BytesIO

from werkzeug.datastructures import ImmutableMultiDict

from invenio_files_rest.models import Bucket, Location, ObjectVersion
from invenio_stats.contrib.event_builders import (
    celery_task_event_builder,
    file_download_event_builder,
    file_preview_event_builder,
    build_celery_task_unique_id,
    build_file_unique_id,
    build_record_unique_id,
    copy_record_index_list,
    copy_user_group_list,
    copy_search_keyword,
    copy_search_type,
    record_view_event_builder,
    top_view_event_builder,
    build_top_unique_id,
    build_item_create_unique_id,
    resolve_address,
    search_event_builder,
    build_search_unique_id,
    build_search_detail_condition,
    item_create_event_builder
)

CONTRIBUTOR = 0

# def celery_task_event_builder(event, sender_app, exec_data=None, user_data=None, **kwargs):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_event_builders.py::test_celery_task_event_builder -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_celery_task_event_builder(app):
    _exec_data = {
        'task_id': 'T000000000001',
        'task_name': 'Test task',
        'task_state': 'E',
        'start_time': datetime(2022, 1, 1),
        'end_time': datetime(2022, 1, 31),
        'total_records': 10,
        'repository_name': 'root',
        'execution_time': 100
    }
    _user_data = {
        'ip_address': '127.0.0.1',
        'user_agent': 'Chrome',
        'user_id': 1,
        'session_id': 'S0000000001'
    }

    with pytest.raises(Exception) as e:
        celery_task_event_builder({}, app)
    assert e.type==TypeError
    res = celery_task_event_builder({}, app, _exec_data, _user_data)
    assert res=={
        'timestamp': res['timestamp'],
        'task_id': 'T000000000001',
        'task_name': 'Test task',
        'task_state': 'E',
        'start_time': datetime(2022, 1, 1),
        'end_time': datetime(2022, 1, 31),
        'total_records': 10,
        'repository_name': 'root',
        'execution_time': 100,
        'ip_address': '127.0.0.1',
        'user_agent': 'Chrome',
        'user_id': 1,
        'session_id': 'S0000000001'
    }


# def file_download_event_builder(event, sender_app, obj=None, **kwargs):
# def file_preview_event_builder(event, sender_app, obj=None, **kwargs):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_event_builders.py::test_file_download_event_builder -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_file_download_event_builder(app, request_headers, db):
    tmppath = tempfile.mkdtemp()
    _location = Location(
        name='testloc',
        uri=tmppath,
        default=True
    )
    db.session.add(_location)
    db.session.commit()
    _bucket = Bucket.create()
    _obj = ObjectVersion.create(
            _bucket, 'LICENSE', stream=BytesIO(b'content data'),
            size=len(b'content data')
        )
    _obj.userrole = 'guest'
    _obj.site_license_name = ''
    _obj.site_license_flag = False
    _obj.index_list = []
    _obj.userid = 0
    _obj.item_id = 1
    _obj.item_title = 'test title'
    _obj.is_billing_item = False
    _obj.billing_file_price = 0
    _obj.user_group_list = []
    _obj.is_open_access = True
    with app.test_request_context(headers=request_headers['user']):
        # file_download_event_builder
        res = file_download_event_builder({}, app, _obj)
        assert res=={'accessrole': '', 'billing_file_price': 0, 'bucket_id': str(_bucket.id), 'cur_user_id': 0, 'file_id': str(_obj.file_id), 'file_key': 'LICENSE', 'index_list': [], 'ip_address': None, 'is_billing_item': False, 'is_open_access': True, 'item_id': 1, 'item_title': 'test title', 'referrer': None, 'remote_addr': None, 'root_file_id': str(_obj.root_file_id), 'session_id': None, 'site_license_flag': False, 'site_license_name': '', 'size': 12, 'timestamp': res['timestamp'], 'user_agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)Chrome/45.0.2454.101 Safari/537.36', 'user_group_list': [], 'user_id': None, 'userrole': 'guest'}
        # file_preview_event_builder
        res = file_preview_event_builder({}, app, _obj)
        assert res=={'accessrole': '', 'billing_file_price': 0, 'bucket_id': str(_bucket.id), 'cur_user_id': 0, 'file_id': str(_obj.file_id), 'file_key': 'LICENSE', 'index_list': [], 'ip_address': None, 'is_billing_item': False, 'item_id': 1, 'item_title': 'test title', 'referrer': None, 'remote_addr': None, 'root_file_id': str(_obj.root_file_id), 'session_id': None, 'site_license_flag': False, 'site_license_name': '', 'size': 12, 'timestamp': res['timestamp'], 'user_agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)Chrome/45.0.2454.101 Safari/537.36', 'user_group_list': [], 'user_id': None, 'userrole': 'guest'}
        # is_valid_access is False
        with patch("invenio_stats.contrib.event_builders.is_valid_access", return_value=False):
            res = file_download_event_builder({}, app, _obj)
            assert res==None


# def build_celery_task_unique_id(doc):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_event_builders.py::test_build_celery_task_unique_id -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_build_celery_task_unique_id(app):
    _doc = {
        'task_id': 'T000000000001',
        'task_name': 'Test task',
        'repository_name': 'root'
    }
    with pytest.raises(Exception) as e:
        build_celery_task_unique_id({})
    assert e.type==KeyError
    res = build_celery_task_unique_id(_doc)
    assert res=={'repository_name': 'root', 'task_id': 'T000000000001', 'task_name': 'Test task', 'unique_id': '149c715f-859c-36d9-a0be-2a0b3117e30c'}


# def build_file_unique_id(doc):
# def build_record_unique_id(doc):


# def copy_record_index_list(doc, aggregation_data=None):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_event_builders.py::test_copy_record_index_list -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_copy_record_index_list(app):
    _doc = {
        'record_index_list': [
            {'index_name': 'Index A'},
            {'index_name': 'Index B'},
            {'index_english_name': 'Index C'}
        ]
    }
    res = copy_record_index_list(_doc)
    assert res=='Index A, Index B, '


# def copy_user_group_list(doc, aggregation_data=None):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_event_builders.py::test_copy_user_group_list -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_copy_user_group_list(app):
    _doc = {
        'user_group_list': [
            {'group_name': 'Group A'},
            {'group_name': 'Group B'}
        ]
    }
    res = copy_user_group_list(_doc)
    assert res=='Group A, Group B'


# def copy_search_keyword(doc, aggregation_data=None):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_event_builders.py::test_copy_search_keyword -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_copy_search_keyword(app):
    _doc1 = {
        'search_detail': {}
    }
    res = copy_search_keyword(_doc1)
    assert res==''
    _doc2 = {
        'search_detail': {
            'search_key': 'Test Key'
        }
    }
    res = copy_search_keyword(_doc2)
    assert res=='Test Key'


# def copy_search_type(doc, aggregation_data=None):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_event_builders.py::test_copy_search_type -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_copy_search_type(app):
    _doc1 = {
        'search_detail': {}
    }
    res = copy_search_type(_doc1)
    assert res==-1
    _doc2 = {
        'search_detail': {
            'search_type': 1
        }
    }
    res = copy_search_type(_doc2)
    assert res==1

# def record_view_event_builder(event, sender_app, pid=None, record=None, info=None, **kwargs):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_event_builders.py::test_record_view_event_builder -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_record_view_event_builder(app, request_headers, records):
    _info = {
        'site_license_flag': False,
        'site_license_name': ''
    }
    with app.test_request_context(headers=request_headers['user']):
        _records = records[0][1]
        _records.navi = [
            (None, 1, None, 'Index A', 'Index A (en)'),
            (None, 2, None, 'Index B', 'Index B (en)')
        ]
        res = record_view_event_builder({}, app, records[0][0], records[0][1], _info)
        assert res=={'cur_user_id': 'guest', 'ip_address': None, 'pid_type': 'recid', 'pid_value': '1', 'record_id': str(records[0][0].object_uuid), 'record_index_list': [{'index_id': '1', 'index_name': 'Index A', 'index_name_en': 'Index A (en)'}, {'index_id': '2', 'index_name': 'Index B', 'index_name_en': 'Index B (en)'}], 'record_name': 'Back to the Future', 'referrer': None, 'remote_addr': None, 'session_id': None, 'site_license_flag': False, 'site_license_name': '', 'timestamp': res['timestamp'], 'user_agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)Chrome/45.0.2454.101 Safari/537.36', 'user_id': None}


# def top_view_event_builder(event, sender_app, info=None, **kwargs):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_event_builders.py::test_top_view_event_builder -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_top_view_event_builder(app, request_headers):
    _info = {
        'site_license_flag': False,
        'site_license_name': ''
    }
    with app.test_request_context(headers=request_headers['user']):
        res = top_view_event_builder({}, app, _info)
        assert res=={'ip_address': None, 'referrer': None, 'remote_addr': None, 'session_id': None, 'site_license_flag': False, 'site_license_name': '', 'timestamp': res['timestamp'], 'user_agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)Chrome/45.0.2454.101 Safari/537.36', 'user_id': None}

# def build_top_unique_id(doc):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_event_builders.py::test_build_top_unique_id -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_build_top_unique_id(app):
    _doc = {
        'site_license_name': '',
        'remote_addr': '127.0.0.1',
        'unique_session_id': 'S0000001',
        'visitor_id': 0
    }
    res = build_top_unique_id(_doc)
    assert res=={'hostname': 't', 'remote_addr': '127.0.0.1', 'site_license_name': '', 'unique_id': 'b79b359a-e8d7-3eab-9a15-5139732705c8', 'unique_session_id': 'S0000001', 'visitor_id': 0}


# def build_item_create_unique_id(doc):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_event_builders.py::test_build_item_create_unique_id -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_build_item_create_unique_id(app):
    _doc = {
        'pid_value': '1',
        'remote_addr': '127.0.0.1'
    }
    res = build_item_create_unique_id(_doc)
    assert res=={'hostname': 't', 'pid_value': '1', 'remote_addr': '127.0.0.1', 'unique_id': 'item_create_1'}


# def resolve_address(addr):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_event_builders.py::test_resolve_address -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_resolve_address(app):
    res = resolve_address('0.0.0.0')
    assert res=='t'
    res = resolve_address(None)
    assert res==None


# def search_event_builder(event, sender_app, search_args=None, info=None, **kwargs):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_event_builders.py::test_search_event_builder -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_search_event_builder(app, request_headers):
    _info = {
        'site_license_flag': False,
        'site_license_name': ''
    }
    _search_args = ImmutableMultiDict([('search_key', 'Test Key'), ('search_type', '1')])
    with app.test_request_context(headers=request_headers['user']):
        res = search_event_builder({}, app, _search_args, _info)
        assert res=={'ip_address': None, 'referrer': None, 'search_detail': {'search_key': ['Test Key'], 'search_type': ['1']}, 'session_id': None, 'site_license_flag': False, 'site_license_name': '', 'timestamp': res['timestamp'], 'user_agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)Chrome/45.0.2454.101 Safari/537.36', 'user_id': None}


# def build_search_unique_id(doc):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_event_builders.py::test_build_search_unique_id -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_build_search_unique_id(app):
    _doc = {
        'search_detail': {
            'search_key': 'Test Key',
            'search_type': 1
        },
        'site_license_name': '',
        'unique_session_id': 'S0000001'
    }
    res = build_search_unique_id(_doc)
    assert res=={'search_detail': {'search_key': 'Test Key', 'search_type': 1}, 'site_license_name': '', 'unique_id': 'b471384d-925e-3a15-9f49-23cf697d3ccb', 'unique_session_id': 'S0000001'}


# def build_search_detail_condition(doc):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_event_builders.py::test_build_search_detail_condition -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_build_search_detail_condition(app):
    _doc1 = {
        'search_detail': {
            'search_key': ['Test Key1', 'Test Key2'],
            'search_type': '1'
        }
    }
    res = build_search_detail_condition(_doc1)
    assert res=={'search_detail': {'search_key': 'Test Key1 Test Key2', 'search_type': '1'}}
    _doc2 = {
        'search_detail': {
            'q': 'Query1'
        }
    }
    res = build_search_detail_condition(_doc2)
    assert res=={'search_detail': {'search_key': 'Query1'}}


# def item_create_event_builder(event, sender_app, user_id=None, item_id=None, item_title=None, **kwargs):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_event_builders.py::test_item_create_event_builder -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_item_create_event_builder(app, request_headers, records):
    with app.test_request_context(headers=request_headers['user']):
        res = item_create_event_builder({}, app, 1, records[0][0], 'Test title')
        assert res=={'cur_user_id': 1, 'ip_address': None, 'pid_type': 'recid', 'pid_value': '1', 'record_name': 'Test title', 'referrer': None, 'remote_addr': None, 'session_id': None, 'timestamp': res['timestamp'], 'user_agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)Chrome/45.0.2454.101 Safari/537.36', 'user_id': None}

import pytest
import json
from mock import patch, MagicMock
from flask import Blueprint

from invenio_deposit.utils import check_oauth2_scope_write, \
    check_oauth2_scope_write_elasticsearch
from invenio_records_rest.utils import check_elasticsearch
from sqlalchemy.exc import SQLAlchemyError
from weko_records_ui.errors import VersionNotFoundRESTError, InternalServerError \
  ,RecordsNotFoundRESTError ,PermissionError
from weko_records_ui.rest import (
    create_error_handlers,
    create_blueprint,
    WekoRecordsCitesResource,
    WekoRecordsResource
)


blueprint = Blueprint(
    'invenio_records_rest',
    __name__,
    url_prefix='',
)

_PID = 'pid(depid,record_class="invenio_deposit.api:Deposit")'

endpoints = {
    'depid': {
        'pid_type': 'depid',
        'pid_minter': 'deposit',
        'pid_fetcher': 'deposit',
        'record_class': 'invenio_deposit.api:Deposit',
        'files_serializers': {
            'application/json': ('invenio_deposit.serializers'
                                 ':json_v1_files_response'),
        },
        'record_serializers': {
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_response'),
        },
        'search_class': 'invenio_deposit.search:DepositSearch',
        'search_serializers': {
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        'list_route': '/deposits/',
        'indexer_class': None,
        'item_route': '/deposits/<{0}:pid_value>'.format(_PID),
        'file_list_route': '/deposits/<{0}:pid_value>/files'.format(_PID),
        'file_item_route':
            '/deposits/<{0}:pid_value>/files/<path:key>'.format(_PID),
        'default_media_type': 'application/json',
        'links_factory_imp': 'invenio_deposit.links:deposit_links_factory',
        'create_permission_factory_imp': check_oauth2_scope_write,
        'read_permission_factory_imp': check_elasticsearch,
        'update_permission_factory_imp':
            check_oauth2_scope_write_elasticsearch,
        'delete_permission_factory_imp':
            check_oauth2_scope_write_elasticsearch,
        'max_result_window': 10000,
        'cites_route': 1,
        'item_route': '/<string:version>/records/<int:pid_value>/detail',
    },
}


# def create_error_handlers(blueprint):
def test_create_error_handlers(app):
    assert create_error_handlers(blueprint) == None

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_rest.py::test_create_blueprint -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
# def create_blueprint(endpoints):
def test_create_blueprint(app):
    assert create_blueprint(endpoints) != None


# WekoRecordsCitesResource
def test_WekoRecordsCitesResource(app, records):
    data1 = MagicMock()
    data2 = {"1": 1}
    values = {}
    indexer, results = records
    record = results[0]['record']
    pid_value = record.pid.pid_value

    test = WekoRecordsCitesResource(data1, data2)
    with app.test_request_context():
        with patch("flask.request", return_value=values):
            with patch("weko_records_ui.rest.citeproc_v1.serialize", return_value=data2):
                assert WekoRecordsCitesResource.get(pid_value, pid_value)

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_rest.py::test_WekoRecordsResource -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_WekoRecordsResource(app, records):

    app.register_blueprint(create_blueprint(app.config['WEKO_RECORDS_UI_CITES_REST_ENDPOINTS']))
    with app.test_client() as client:
        res = client.get('/v1.0/records/1/detail',content_type='application/json')
        assert res.status_code == 200
        try:
            json.loads(res.get_data())
            assert True
        except:
            assert False

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_rest.py::test_WekoRecordsResource_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_WekoRecordsResource_error(app, records):

    def dammy_permission():
        return False
    
    url = '/v1.0/records/1/detail'
    
    app.register_blueprint(create_blueprint(app.config['WEKO_RECORDS_UI_CITES_REST_ENDPOINTS']))
    with app.test_client() as client:
        res = client.get('/v1.0/records/1/detail',content_type='application/json')
        headers = {}
        headers['If-None-Match'] = res.headers['Etag'].strip('"')
        res = client.get('/v1.0/records/1/detail',content_type='application/json', headers=headers)
        assert res.status_code == 304
        
        res = client.get('/ver1/records/1/detail',content_type='application/json')
        assert res.status_code == 400
        
        with patch('weko_index_tree.utils.get_user_roles', 
                   MagicMock(side_effect=PermissionError())):
            res = client.get('/v1.0/records/1/detail',content_type='application/json')
            assert res.status_code == 403
        
        res = client.get('/v1.0/records/100/detail',content_type='application/json')
        assert res.status_code == 404
        
        with patch('weko_deposit.api.WekoRecord.get_record', MagicMock(side_effect=SQLAlchemyError())):
            res = client.get('/v1.0/records/1/detail',content_type='application/json')
            assert res.status_code == 500

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_rest.py::test_WekoRecordsStats -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_WekoRecordsStats(app, records):

    app.register_blueprint(create_blueprint(app.config['WEKO_RECORDS_UI_CITES_REST_ENDPOINTS']))
    with app.test_client() as client:
        res = client.get('/v1.0/records/1/stats',content_type='application/json')
        assert res.status_code == 200
        try:
            json.loads(res.get_data())
            assert True
        except:
            assert False

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_rest.py::test_WekoRecordsStats_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_WekoRecordsStats_error(app, records):
    
    url = '/v1.0/records/1/stats'
    
    app.register_blueprint(create_blueprint(app.config['WEKO_RECORDS_UI_CITES_REST_ENDPOINTS']))
    with app.test_client() as client:
        res = client.get(url,content_type='application/json')
        headers = {}
        headers['If-None-Match'] = res.headers['Etag'].strip('"')
        res = client.get(url,content_type='application/json', headers=headers)
        assert res.status_code == 304
        
        res = client.get('/ver1/records/1/detail',content_type='application/json')
        assert res.status_code == 400
        
        with patch('weko_index_tree.utils.get_user_roles', 
                   MagicMock(side_effect=PermissionError())):
            res = client.get(url,content_type='application/json')
            assert res.status_code == 403
        
        err_query_date = '?date=2023-15'
        res = client.get(url,content_type='application/json')
        assert res.status_code == 404
        
        res = client.get('/v1.0/records/100/stats',content_type='application/json')
        assert res.status_code == 404
        
        with patch('weko_deposit.api.WekoRecord.get_record', MagicMock(side_effect=SQLAlchemyError())):
            res = client.get(url,content_type='application/json')
            assert res.status_code == 500

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_rest.py::test_WekoFilesStats -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_WekoFilesStats(app, records):

    app.register_blueprint(create_blueprint(app.config['WEKO_RECORDS_UI_CITES_REST_ENDPOINTS']))
    with app.test_client() as client:
        res = client.get('/v1.0/records/1/files/helloworld.pdf/stats',content_type='application/json')
        assert res.status_code == 200
        try:
            json.loads(res.get_data())
            assert True
        except:
            assert False

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_rest.py::test_WekoFilesStats_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_WekoFilesStats_error(app, records):
      
    url = '/v1.0/records/1/files/helloworld.pdf/stats'
    
    app.register_blueprint(create_blueprint(app.config['WEKO_RECORDS_UI_CITES_REST_ENDPOINTS']))
    with app.test_client() as client:
        res = client.get(url,content_type='application/json')
        headers = {}
        headers['If-None-Match'] = res.headers['Etag'].strip('"')
        res = client.get(url,content_type='application/json', headers=headers)
        assert res.status_code == 304
        
        res = client.get('/ver1/records/1/detail',content_type='application/json')
        assert res.status_code == 400
        
        with patch('weko_index_tree.utils.get_user_roles', 
                   MagicMock(side_effect=PermissionError())):
            res = client.get(url,content_type='application/json')
            assert res.status_code == 403
        
        res = client.get('/v1.0/records/100/detail',content_type='application/json')
        assert res.status_code == 404
        
        with patch('weko_deposit.api.WekoRecord.get_record', MagicMock(side_effect=SQLAlchemyError())):
            res = client.get(url,content_type='application/json')
            assert res.status_code == 500

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_rest.py::test_WekoFilesGet -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_WekoFilesGet(app, records):

    app.register_blueprint(create_blueprint(app.config['WEKO_RECORDS_UI_CITES_REST_ENDPOINTS']))
    with app.test_client() as client:
        res = client.get('/v1.0/records/1/files/helloworld.pdf?mode=preview',content_type='application/json')
        assert res.status_code == 200

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_rest.py::test_WekoFilesGet_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_WekoFilesGet_error(app, records):
      
    url = '/v1.0/records/1/files/helloworld.pdf?mode=preview'
    
    app.register_blueprint(create_blueprint(app.config['WEKO_RECORDS_UI_CITES_REST_ENDPOINTS']))
    with app.test_client() as client:
        res = client.get(url,content_type='application/json')
        headers = {}
        headers['If-None-Match'] = res.headers['Etag'].strip('"')
        res = client.get(url,content_type='application/json', headers=headers)
        assert res.status_code == 304
        
        res = client.get('/ver1.0/records/1/files/helloworld.pdf?mode=preview',content_type='application/json')
        assert res.status_code == 400

        res = client.get('/v1.0/records/1/files/helloworld.pdf',content_type='application/json')
        assert res.status_code == 400
        
        with patch('weko_index_tree.utils.get_user_roles', 
                   MagicMock(side_effect=PermissionError())):
            res = client.get(url,content_type='application/json')
            assert res.status_code == 403
        
        res = client.get('/v1.0/records/100/files/helloworld.pdf?mode=preview',content_type='application/json')
        assert res.status_code == 404
        
        res = client.get('/v1.0/records/1/files/nofile.pdf?mode=preview',content_type='application/json')
        assert res.status_code == 404
        
        with patch('weko_deposit.api.WekoRecord.get_record', MagicMock(side_effect=SQLAlchemyError())):
            res = client.get(url,content_type='application/json')
            assert res.status_code == 500
import json
from mock import patch, MagicMock
from flask import Blueprint, Response
import pytest

from invenio_deposit.utils import check_oauth2_scope_write, \
    check_oauth2_scope_write_elasticsearch
from invenio_records_rest.utils import check_elasticsearch
from sqlalchemy.exc import SQLAlchemyError
#from weko_records_ui.errors import AvailableFilesNotFoundRESTError, FilesNotFoundRESTError, InvalidRequestError
from weko_records_ui.rest import (
    create_error_handlers,
    create_blueprint,
    WekoRecordsCitesResource,
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
        'file_list_all_route': '/deposits/<{0}:pid_value>/files/all'.format(_PID),
        'file_list_selected_route': '/deposits/<{0}:pid_value>/files/selected'.format(_PID),
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
def test_WekoRecordsResource(app, records_rest, db_rocrate_mapping):
    app.register_blueprint(create_blueprint(app.config['WEKO_RECORDS_UI_CITES_REST_ENDPOINTS']))
    with app.test_client() as client:
        res = client.get('/v1/records/1')
        assert res.status_code == 200
        data = json.loads(res.get_data())
        assert data['rocrate']['@graph'][0]['name'][0] == 'test data'


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_rest.py::test_WekoRecordsResource_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_WekoRecordsResource_error(app, records_rest, db_rocrate_mapping):
    app.register_blueprint(create_blueprint(app.config['WEKO_RECORDS_UI_CITES_REST_ENDPOINTS']))
    with app.test_client() as client:
        url = '/v1/records/1'
        res = client.get(url)
        etag = res.headers['Etag']
        last_modified = res.headers['Last-Modified']

        # Check Etag
        headers = {}
        headers['If-None-Match'] = etag
        res = client.get(url, headers=headers)
        assert res.status_code == 304

        # Check Last-Modified
        headers = {}
        headers['If-Modified-Since'] = last_modified
        res = client.get(url, headers=headers)
        assert res.status_code == 304

        # Invalid version
        url = '/v0/records/1'
        res = client.get(url)
        assert res.status_code == 400

        # Record not found
        url = '/v1/records/100'
        res = client.get(url)
        assert res.status_code == 404

        # Access denied
        with patch('weko_records_ui.permissions.check_publish_status', MagicMock(return_value=False)):
            url = '/v1/records/1'
            res = client.get(url)
            assert res.status_code == 403

        # Failed to execute SQL
        with patch('weko_deposit.api.WekoRecord.get_record', MagicMock(side_effect=SQLAlchemyError())):
            url = '/v1/records/1'
            res = client.get(url)
            assert res.status_code == 500


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_rest.py::test_WekoRecordsStats -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_WekoRecordsStats(app, records_rest, db_rocrate_mapping):
    app.register_blueprint(create_blueprint(app.config['WEKO_RECORDS_UI_CITES_REST_ENDPOINTS']))
    with app.test_client() as client:
        res = client.get('/v1/records/1/stats')
        assert res.status_code == 200

        res = client.get('/v1/records/1/stats?date=2023-09')
        assert res.status_code == 200


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_rest.py::test_WekoRecordsStats_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_WekoRecordsStats_error(app, records_rest, db_rocrate_mapping):
    app.register_blueprint(create_blueprint(app.config['WEKO_RECORDS_UI_CITES_REST_ENDPOINTS']))
    with app.test_client() as client:
        url = '/v1/records/1/stats'
        res = client.get(url)
        etag = res.headers['Etag']

        # Check Etag
        headers = {}
        headers['If-None-Match'] = etag
        res = client.get(url, headers=headers)
        assert res.status_code == 304

        # Invalid version
        url = '/v0/records/1/stats'
        res = client.get(url)
        assert res.status_code == 400

        # Record not found
        url = '/v1/records/100/stats'
        res = client.get(url)
        assert res.status_code == 404

        # Invalid date
        url = '/v1/records/1/stats?date=dummydate'
        res = client.get(url)
        assert res.status_code == 400

        # Access denied
        with patch('weko_records_ui.permissions.check_publish_status', MagicMock(return_value=False)):
            url = '/v1/records/1/stats'
            res = client.get(url)
            assert res.status_code == 403

        # Failed to execute SQL
        with patch('weko_deposit.api.WekoRecord.get_record', MagicMock(side_effect=SQLAlchemyError())):
            url = '/v1/records/1/stats'
            res = client.get(url)
            assert res.status_code == 500


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_rest.py::test_WekoFilesStats -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_WekoFilesStats(app, records):
    app.register_blueprint(create_blueprint(app.config['WEKO_RECORDS_UI_CITES_REST_ENDPOINTS']))
    with app.test_client() as client:
        res = client.get('/v1/records/1/files/helloworld.pdf/stats')
        assert res.status_code == 200

        res = client.get('/v1/records/1/files/helloworld.pdf/stats?date=2023-09')
        assert res.status_code == 200


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_rest.py::test_WekoFilesStats_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_WekoFilesStats_error(app, records):
    app.register_blueprint(create_blueprint(app.config['WEKO_RECORDS_UI_CITES_REST_ENDPOINTS']))
    with app.test_client() as client:
        url = '/v1/records/1/files/helloworld.pdf/stats'
        res = client.get(url)
        etag = res.headers['Etag']

        # Check Etag
        headers = {}
        headers['If-None-Match'] = etag
        res = client.get(url, headers=headers)
        assert res.status_code == 304

        # Invalid version
        url = '/v0/records/1/files/helloworld.pdf/stats'
        res = client.get(url)
        assert res.status_code == 400

        # Record not found
        url = '/v1/records/100/files/helloworld.pdf/stats'
        res = client.get(url)
        assert res.status_code == 404

        # File not found
        url = '/v1/records/1/files/nofile.pdf/stats'
        res = client.get(url)
        assert res.status_code == 404

        # Invalid date
        url = '/v0/records/1/files/helloworld.pdf/stats?date=dummydate'
        res = client.get(url)
        assert res.status_code == 400

        # Access denied
        with patch('weko_records_ui.permissions.check_publish_status', MagicMock(return_value=False)):
            url = '/v1/records/1/files/helloworld.pdf/stats'
            res = client.get(url)
            assert res.status_code == 403
        with patch('weko_records_ui.permissions.check_file_download_permission', MagicMock(return_value=False)):
            url = '/v1/records/1/files/helloworld.pdf/stats'
            res = client.get(url)
            assert res.status_code == 403

        # Failed to execute SQL
        with patch('weko_deposit.api.WekoRecord.get_record', MagicMock(side_effect=SQLAlchemyError())):
            url = '/v1/records/1/files/helloworld.pdf/stats'
            res = client.get(url)
            assert res.status_code == 500


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_rest.py::test_WekoFilesGet -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_WekoFilesGet(app, records):
    app.register_blueprint(create_blueprint(app.config['WEKO_RECORDS_UI_CITES_REST_ENDPOINTS']))
    with app.test_client() as client:
        res = client.get('/v1/records/1/files/helloworld.pdf')
        assert res.status_code == 200

        res = client.get('/v1/records/1/files/helloworld.pdf?mode=preview')
        assert res.status_code == 200


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_rest.py::test_WekoFilesGet_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_WekoFilesGet_error(app, records):
    app.register_blueprint(create_blueprint(app.config['WEKO_RECORDS_UI_CITES_REST_ENDPOINTS']))
    with app.test_client() as client:
        url = '/v1/records/1/files/helloworld.pdf'
        res = client.get(url)
        etag = res.headers['Etag']
        last_modified = res.headers['Last-Modified']

        # Check Etag
        headers = {}
        headers['If-None-Match'] = etag
        res = client.get(url, headers=headers)
        assert res.status_code == 304

        # Check Last-Modified
        headers = {}
        headers['If-Modified-Since'] = last_modified
        res = client.get(url, headers=headers)
        assert res.status_code == 304

        # Invalid version
        url = '/v0/records/1/files/helloworld.pdf'
        res = client.get(url)
        assert res.status_code == 400

        # Record not found
        url = '/v1/records/100/files/helloworld.pdf'
        res = client.get(url)
        assert res.status_code == 404

        # File not found
        url = '/v1/records/1/files/nofile.pdf'
        res = client.get(url)
        assert res.status_code == 404

        # Access denied
        with patch('weko_records_ui.permissions.check_publish_status', MagicMock(return_value=False)):
            url = '/v1/records/1/files/helloworld.pdf'
            res = client.get(url)
            assert res.status_code == 403
        with patch('weko_records_ui.permissions.check_file_download_permission', MagicMock(return_value=False)):
            url = '/v1/records/1/files/helloworld.pdf'
            res = client.get(url)
            assert res.status_code == 403

        # Failed to execute SQL
        with patch('weko_deposit.api.WekoRecord.get_record', MagicMock(side_effect=SQLAlchemyError())):
            url = '/v1/records/1/files/helloworld.pdf'
            res = client.get(url)
            assert res.status_code == 500


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_rest.py::test_WekoFileListGetAll -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_WekoFileListGetAll(app, mocker, records):
    app.register_blueprint(create_blueprint(app.config['WEKO_RECORDS_UI_CITES_REST_ENDPOINTS']))
    with app.test_client() as client:
        with patch('weko_records_ui.fd.file_list_ui', return_value=Response(status=200)):
            # 1 GET request
            res = client.get('/v1/records/1/files/all')
            assert res.status_code == 200

    test_mock = mocker.patch('weko_records_ui.fd.file_list_ui', return_value=Response(status=200))
    # 2 Exist thumbnail
    url = '/v1/records/7/files/all'
    res = client.get(url)
    assert len(test_mock.call_args[0][1]) == 1


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_rest.py::test_WekoFileListGetAll_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_WekoFileListGetAll_error(app, records):
    app.register_blueprint(create_blueprint(app.config['WEKO_RECORDS_UI_CITES_REST_ENDPOINTS']))
    with app.test_client() as client:
        with patch('weko_records_ui.permissions.check_publish_status', MagicMock(return_value=False)):
            # 3 Access denied
            url = '/v1/records/1/files/all'
            res = client.get(url)
            assert res.status_code == 403

        with patch('weko_records_ui.permissions.page_permission_factory', MagicMock(return_value=False)):
            # 3 Access denied
            url = '/v1/records/1/files/all'
            res = client.get(url)
            assert res.status_code == 403

        with patch('weko_records_ui.fd.file_list_ui', MagicMock(side_effect=AvailableFilesNotFoundRESTError())):
            # 4 File not availlable
            url = '/v1/records/5/files/all'
            res = client.get(url)
            assert res.status_code == 403

        with patch('weko_records_ui.fd.file_list_ui', return_value=Response(status=200)):
            # 5 File not exist
            url = '/v1/records/6/files/all'
            res = client.get(url)
            assert res.status_code == 404

            # 6 Invalid record
            url = '/v1/records/100/files/all'
            res = client.get(url)
            assert res.status_code == 404

            # 7 Invalid version
            url = '/v0/records/1/files/all'
            res = client.get(url)
            assert res.status_code == 400

            # 8 Check Etag, Last-Modified
            url = '/v1/records/1/files/all'
            res = client.get(url)
            etag = res.headers['Etag']
            last_modified = res.headers['Last-Modified']

            headers = {}
            headers['If-None-Match'] = etag
            res = client.get(url, headers=headers)
            assert res.status_code == 304

            headers = {}
            headers['If-Modified-Since'] = last_modified
            res = client.get(url, headers=headers)
            assert res.status_code == 304


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_rest.py::test_WekoFileListGetSelected -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_WekoFileListGetSelected(app, mocker, records):
    app.register_blueprint(create_blueprint(app.config['WEKO_RECORDS_UI_CITES_REST_ENDPOINTS']))
    with app.test_client() as client:
        with patch('weko_records_ui.fd.file_list_ui', return_value=Response(status=200)):
            # 1 POST request
            json={"filenames":["helloworld.pdf"]}
            res = client.post('/v1/records/1/files/selected', json=json)
            assert res.status_code == 200


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_rest.py::test_WekoFileListGetSelected_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_WekoFileListGetSelected_error(app, records):
    app.register_blueprint(create_blueprint(app.config['WEKO_RECORDS_UI_CITES_REST_ENDPOINTS']))
    json={"filenames":["helloworld.pdf"]}
    with app.test_client() as client:
        with patch('weko_records_ui.permissions.check_publish_status', MagicMock(return_value=False)):
            # 2 Access denied
            url = '/v1/records/1/files/selected'
            res = client.post(url, json=json)
            assert res.status_code == 403

        with patch('weko_records_ui.permissions.page_permission_factory', MagicMock(return_value=False)):
            # 2 Access denied
            url = '/v1/records/1/files/selected'
            res = client.post(url, json=json)
            assert res.status_code == 403

        with patch('weko_records_ui.fd.file_list_ui', MagicMock(side_effect=AvailableFilesNotFoundRESTError())):
            # 3 File not availlable
            url = '/v1/records/5/files/selected'
            res = client.post(url, json=json)
            assert res.status_code == 403

        with patch('weko_records_ui.fd.file_list_ui', return_value=Response(status=200)):
            # 4 File not exist
            url = '/v1/records/6/files/selected'
            res = client.post(url, json=json)
            assert res.status_code == 404

            # 5 Invalid record
            url = '/v1/records/100/files/selected'
            res = client.post(url, json=json)
            assert res.status_code == 404

            # 6 Invalid version
            url = '/v0/records/1/files/selected'
            res = client.post(url, json=json)
            assert res.status_code == 400

            # 7 Invalid filenames
            json={"filenames":["invalid.file"]}
            url = '/v1/records/1/files/selected'
            res = client.post(url, json=json)
            assert res.status_code == 404

            # 8 Unspecified filenames
            json={"filenames":[]}
            res = client.post(url, json=json)
            assert res.status_code == 400

            # 9 Unspecified request body
            res = client.post(url, json=None)
            assert res.status_code == 400

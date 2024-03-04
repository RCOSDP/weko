# .tox/c1/bin/pytest --cov=weko_authors tests/test_rest.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp

import json
from mock import patch
from flask import Blueprint, Response

from invenio_deposit.utils import check_oauth2_scope_write, \
    check_oauth2_scope_write_elasticsearch
from invenio_records_rest.utils import check_elasticsearch
from weko_authors.rest import (
    create_blueprint,
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
            'application/json': ('invenio_deposit.serializers:json_v1_files_response'),
        },
        'search_class': 'invenio_deposit.search:DepositSearch',
        'search_serializers': {
            'application/json': ('invenio_records_rest.serializers:json_v1_search'),
        },
        'list_route': '/deposits/',
        'indexer_class': None,
        'item_route': '/deposits/<{0}:pid_value>'.format(_PID),
        'route': '/deposits/<{0}:pid_value>/authors/count'.format(_PID),
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
    },
}


# def create_blueprint(endpoints):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_rest.py::test_create_blueprint -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_create_blueprint(app):
    assert create_blueprint(endpoints) != None


# def Authors(ContentNegotiatedMethodView):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_rest.py::test_Authors -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_Authors(app, mocker):
    app.register_blueprint(create_blueprint(app.config['WEKO_AUTHORS_REST_ENDPOINTS']))
    with \
        app.test_client() as client, \
        patch('weko_authors.utils.count_authors', return_value=Response(status=200)), \
        patch('json.dumps', return_value={}):

        # 1 GET reqest
        res = client.get('/v1/authors/count')
        assert res.status_code == 200

        # 2 Invalid version
        res = client.get('/v0/authors/count')
        assert res.status_code == 400

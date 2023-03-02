import pytest
from mock import patch, MagicMock
from flask import Blueprint

from invenio_deposit.utils import check_oauth2_scope_write, \
    check_oauth2_scope_write_elasticsearch
from invenio_records_rest.utils import check_elasticsearch

from weko_records_ui.rest import (
    create_error_handlers,
    create_blueprint,
    WekoRecordsCitesResource
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
        'cites_route': 1
    },
}


# def create_error_handlers(blueprint):
def test_create_error_handlers(app):
    assert create_error_handlers(blueprint) == None


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

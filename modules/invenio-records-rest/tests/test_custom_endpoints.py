# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test using Invenio Records REST view classes directly.

By default Invenio Records REST will create endpoints using the configuration.
However some Invenio applications need a full control over the REST API and
create the endpoints directly using the view classes (ex: RecordResource).
These tests check if it is possible to do it.
"""

import pytest
from flask import Blueprint, url_for
from helpers import get_json
from invenio_search import RecordsSearch

from invenio_records_rest import utils
from invenio_records_rest.query import default_search_factory
from invenio_records_rest.schemas import RecordSchemaJSONV1
from invenio_records_rest.serializers.json import JSONSerializer
from invenio_records_rest.serializers.response import record_responsify, \
    search_responsify
from invenio_records_rest.utils import allow_all
from invenio_records_rest.views import RecordResource, RecordsListResource


@pytest.yield_fixture()
def test_custom_endpoints_app(app):
    """Create an application enabling the creation of a custom endpoint."""
    # Hack necessary to have links generated properly
    @app.before_first_request
    def extend_default_endpoint_prefixes():
        """Extend redirects between PID types."""
        endpoint_prefixes = utils.build_default_endpoint_prefixes(
            {'recid': {'pid_type': 'recid'}})
        current_records_rest = app.extensions[
            'invenio-records-rest']
        current_records_rest.default_endpoint_prefixes.update(
            endpoint_prefixes
        )
    return app


@pytest.mark.parametrize('app', [dict(
    # Disable all endpoints from config. The test will create the endpoint.
    records_rest_endpoints=dict(),
)], indirect=['app'])
def test_get_record(test_custom_endpoints_app, test_records):
    """Test the creation of a custom endpoint using RecordResource."""
    test_records = test_records
    """Test creation of a RecordResource view."""
    blueprint = Blueprint(
        'test_invenio_records_rest',
        __name__,
    )

    json_v1 = JSONSerializer(RecordSchemaJSONV1)

    blueprint.add_url_rule(
        '/records/<pid(recid):pid_value>',
        view_func=RecordResource.as_view(
            'recid_item',
            serializers={
                'application/json': record_responsify(
                    json_v1, 'application/json'
                )
            },
            default_media_type='application/json',
            read_permission_factory=allow_all,
            update_permission_factory=allow_all,
            delete_permission_factory=allow_all,
        )
    )

    test_custom_endpoints_app.register_blueprint(blueprint)

    with test_custom_endpoints_app.app_context():
        pid, record = test_records[0]
        url = url_for('test_invenio_records_rest.recid_item',
                      pid_value=pid.pid_value, user=1)
        with test_custom_endpoints_app.test_client() as client:
            res = client.get(url)
            assert res.status_code == 200

            # Check metadata
            data = get_json(res)
            assert record == data['metadata']


@pytest.mark.parametrize('test_custom_endpoints_app', [dict(
    # Disable all endpoints from config. The test will create the endpoint.
    records_rest_endpoints=dict(),
)], indirect=['test_custom_endpoints_app'])
def test_get_records_list(test_custom_endpoints_app, indexed_records):
    """Test the creation of a custom endpoint using RecordsListResource."""
    blueprint = Blueprint(
        'test_invenio_records_rest',
        __name__,
    )
    json_v1 = JSONSerializer(RecordSchemaJSONV1)

    blueprint.add_url_rule(
        '/records/',
        view_func=RecordsListResource.as_view(
            'recid_list',
            minter_name='recid',
            pid_fetcher='recid',
            pid_type='recid',
            search_serializers={
                'application/json': search_responsify(
                    json_v1, 'application/json'
                )
            },
            search_class=RecordsSearch,
            read_permission_factory=allow_all,
            create_permission_factory=allow_all,
            search_factory=default_search_factory,
            default_media_type='application/json',
        )
    )
    test_custom_endpoints_app.register_blueprint(blueprint)

    with test_custom_endpoints_app.test_request_context():
        search_url = url_for('test_invenio_records_rest.recid_list')
    with test_custom_endpoints_app.test_client() as client:
        # Get a query with only one record
        res = client.get(search_url, query_string={'q': 'year:2015'})
        record = next(iter(
            [rec for rec in indexed_records if rec[1]['year'] == 2015]
        ))
        assert res.status_code == 200
        data = get_json(res)
        assert len(data['hits']['hits']) == 1
        # We need to check only for select record keys, since the ES
        # result contains manually-injected 'suggest' properties
        for k in ['title', 'year', 'stars', 'control_number']:
            assert record[1][k] == data['hits']['hits'][0]['metadata'][k]

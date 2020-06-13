# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Link factory tests."""

from __future__ import absolute_import, print_function

import copy

import pytest
from helpers import create_record, get_json, record_url

from invenio_records_rest.config import RECORDS_REST_ENDPOINTS
from invenio_records_rest.links import default_links_factory_with_additional
from invenio_records_rest.views import create_blueprint


def test_default_links_factory_with_additional(app, db):
    """Test links factory with additional links."""
    pid, record = create_record({'title': 'test'})
    with app.test_request_context('/records/1'):
        link_factory = default_links_factory_with_additional(
            dict(test_link='{scheme}://{host}/{pid.pid_value}'))
        links = link_factory(pid)
        assert links['test_link'] == 'http://localhost:5000/1'


# Create a configuration with an old link factory. Used in the next test.
config = copy.deepcopy(RECORDS_REST_ENDPOINTS)
config['recid']['links_factory_imp'] = \
    lambda pid: {'test_link': 'http://old_links_factory.com'}


@pytest.mark.parametrize('app', [dict(
    # Provide the configuration with the old links_factory
    records_rest_endpoints=config,
)], indirect=['app'])
def test_old_signature_backward_compatibility(app, test_records):
    """Check that the old Links_factory signature is still supported.

    This old signature was links_factory(pid), without "record" and "**kwargs"
    parameters.
    """
    # blueprint = create_blueprint(config)
    with app.test_client() as client:
        pid, record = test_records[0]

        res = client.get(record_url(pid))
        assert res.status_code == 200

        # Check metadata
        data = get_json(res)
        assert data['links']['test_link'] == 'http://old_links_factory.com'

# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

# .tox/c1/bin/pytest --cov=invenio_records_rest tests/test_permissions.py -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/invenio-records-rest/.tox/c1/tmp

"""Permissions tests."""

from __future__ import absolute_import, print_function

import json

from tests.helpers import record_url


def test_default_permissions(app, default_permissions, indexed_10records, 
                             record_data10, search_url,aggs_and_facet):
    """Test default create permissions."""
    pid, record = indexed_10records[0]
    rec_url = record_url(pid)
    data = json.dumps(record_data10[0])
    h = {'Content-Type': 'application/json'}
    hp = {'Content-Type': 'application/json-patch+json'}

    with default_permissions.test_client() as client:
        args = dict(data=data, headers=h)
        pargs = dict(data=data, headers=hp)
        qs = {'user': '1'}
        uargs = dict(data=data, headers=h, query_string=qs)
        upargs = dict(data=data, headers=hp, query_string=qs)

        assert client.get(search_url).status_code == 200
        assert client.get(rec_url).status_code == 200

        assert 401 == client.post(search_url, **args).status_code
        assert 405 == client.put(search_url, **args).status_code
        assert 405 == client.patch(search_url).status_code
        assert 405 == client.delete(search_url).status_code

        assert 405 == client.post(rec_url, **args).status_code
        assert 401 == client.put(rec_url, **args).status_code
        assert 401 == client.patch(rec_url, **pargs).status_code
        assert 401 == client.delete(rec_url).status_code

        assert 401 == client.post(search_url, **uargs).status_code
        assert 401 == client.put(rec_url, **uargs).status_code
        assert 401 == client.patch(rec_url, **upargs).status_code
        assert 401 == client.delete(rec_url, query_string=qs).status_code

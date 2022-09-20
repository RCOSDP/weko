# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test view functions."""
import json
import uuid

from invenio_accounts.testutils import login_user_via_session
from flask import url_for
from invenio_stats.views import (
    WekoQuery,
    StatsQueryResource,
    QueryRecordViewCount,
    QueryFileStatsCount,
    QueryItemRegReport,
    QueryRecordViewReport,
    QueryRecordViewPerIndexReport,
    QueryFileReports,
    QueryCommonReports,
    QueryCeleryTaskReport,
    QuerySearchReport
)

CONTRIBUTOR = 0
REPO_ADMIN = 1
SYSTEM_ADMIN = 2
COM_ADMIN = 3

# class WekoQuery(ContentNegotiatedMethodView):

# class StatsQueryResource(WekoQuery):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_stats_query_resource -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_stats_query_resource(client, db, query_entrypoints,
                              role_users, custom_permission_factory,
                              sample_histogram_query_data):
    """Test post request to stats API."""
    headers = [('Content-Type', 'application/json'),
                ('Accept', 'application/json')]
    sample_histogram_query_data['mystat']['stat'] = 'test-query'
    login_user_via_session(client=client, email=role_users[SYSTEM_ADMIN]["email"])
    # need to fix
    resp = client.post(
        url_for('invenio_stats.stat_query'),
        headers=headers,
        data=json.dumps(sample_histogram_query_data))
    assert resp.status_code==400


# class QueryRecordViewCount(WekoQuery):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_query_record_view_count -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_query_record_view_count(client, db, records):
    _uuid = str(records[0][0].object_uuid)
    resp = client.get(
        url_for('invenio_stats.get_record_view_count', record_id=_uuid))
    assert resp.status_code==200

# class QueryFileStatsCount(WekoQuery):
# class QueryItemRegReport(WekoQuery):
# class QueryRecordViewReport(WekoQuery):
# class QueryRecordViewPerIndexReport(WekoQuery):
# class QueryFileReports(WekoQuery):
# class QueryCommonReports(WekoQuery):
# class QueryCeleryTaskReport(WekoQuery):
# class QuerySearchReport(ContentNegotiatedMethodView):

# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# INVENIO-ResourceSyncServer is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module of invenio-resourcesyncserver."""

# TODO: This is an example file. Remove it if your package does not use any
# extra configuration variables.

INVENIO_RESOURCESYNCSERVER_DEFAULT_VALUE = 'foobar'
"""Default value for the application."""

INVENIO_RESOURCESYNCSERVER_BASE_TEMPLATE = \
    'invenio_resourcesyncserver/base.html'
"""Default base template for the demo page."""

INVENIO_RESOURCESYNCSERVER_ADMIN_TEMPLATE = \
    'invenio_resourcesyncserver/resource.html'
"""Admin template for the demo page."""

INVENIO_RESOURCESYNC_CHANGE_LIST_ADMIN = \
    'invenio_resourcesyncserver/change_list.html'
"""Admin template for the demo page."""

INVENIO_DATETIME_ISOFORMAT = r"%Y-%m-%d"
"""ISO 8601 format for Datetime."""

INVENIO_DELAY_PUBLISHEDDATE = False
"""Delay published to first change date."""

DATA_FAKE = [
    {
        'record_id': 1,
        'version_id': 1,
        'state': 'created',
        'created': '2020-01-10T06:10:54.444843Z',
        'updated': '2020-01-14T06:10:54.444843Z'
    },
    {
        'record_id': 2,
        'version_id': 1,
        'state': 'created',
        'created': '2020-01-11T06:10:54.444843Z',
        'updated': '2020-01-14T06:10:54.444843Z'
    },
    {
        'record_id': 2,
        'version_id': 2,
        'state': 'updated',
        'created': '2020-01-12T06:10:54.444843Z',
        'updated': '2020-01-14T06:10:54.444843Z'
    },
    {
        'record_id': 2,
        'version_id': 3,
        'state': 'updated',
        'created': '2020-01-13T06:10:54.444843Z',
        'updated': '2020-01-14T06:10:54.444843Z'
    },
    {
        'record_id': 3,
        'version_id': 1,
        'state': 'created',
        'created': '2020-01-14T06:10:54.444843Z',
        'updated': '2020-01-15T06:10:54.444843Z'
    },
    {
        'record_id': 4,
        'version_id': 1,
        'state': 'created',
        'created': '2020-01-15T06:10:54.444843Z',
        'updated': '2020-01-16T06:10:54.444843Z'
    },
    {
        'record_id': 4,
        'version_id': 2,
        'state': 'updated',
        'created': '2020-01-17T06:10:54.444843Z',
        'updated': '2020-01-18T06:10:54.444843Z'
    }
]

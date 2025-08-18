# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# INVENIO-ResourceSyncClient is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module of invenio-resourcesyncclient."""

# TODO: This is an example file. Remove it if your package does not use any
# extra configuration variables.
from datetime import timedelta

INVENIO_RESOURCESYNCCLIENT_DEFAULT_VALUE = 'foobar'
"""Default value for the application."""

INVENIO_RESOURCESYNCCLIENT_BASE_TEMPLATE = \
    'invenio_resourcesyncclient/base.html'
"""Default base template for the demo page."""

INVENIO_RESOURCESYNCCLIENT_ADMIN_TEMPLATE = \
    'invenio_resourcesyncclient/resync_client.html'
"""Default base template for the demo page."""

INVENIO_RESYNC_INDEXES_STATUS = {
    'automatic': 'Automatic',
    'manual': 'Manual'
}
"""Value of resync_indexes_status."""

INVENIO_RESYNC_INDEXES_MODE = {
    'baseline': 'Baseline',
    'incremental': 'Incremental',
    'audit': 'Audit'
}
"""Value of resync_indexes_mode."""

INVENIO_RESYNC_INDEXES_SAVING_FORMAT = {
    'jpcoar': 'JPCOAR-XML',
    'biosample': 'BIOSAMPLE-JSON-LD',
    'bioproject': 'BIOPROJECT-JSON-LD',
    # 'json': 'JSON',
}
"""Value of resync_indexes_mode."""

INVENIO_RESYNC_LOGS_STATUS = {
    'successful': "Successful",
    'running': 'Running',
    'failed': 'Failed'
}

INVENIO_RESYNC_SAVE_PATH = '/tmp/resync/'

INVENIO_RESYNC_MODE = True
"""  If True, fetch files collected by resync.   """

INVENIO_RESYNC_ENABLE_ITEM_VERSIONING = False
""" If True, the version of the item will be updated upon import.  """

INVENIO_RESOURCESYNCCLIENT_DEFAULT_TIME = '00:00:00'
""" Start time of changelist in Resync sync process.  """

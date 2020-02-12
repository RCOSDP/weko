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
    'Incremental': 'Incremental',
    'audit': 'Audit'
}
"""Value of resync_indexes_mode."""

INVENIO_RESYNC_INDEXES_SAVING_FORMAT = {
    'jpcoar': 'JPCOAR-XML',
    'json': 'JSON',
}
"""Value of resync_indexes_mode."""


INVENIO_RESYNC_WEKO_DEFAULT_DIR = 'records'
"""Value of WEKO default dir for records."""

INVENIO_RESYNC_LOGS_STATUS = {
    'successful': "Successful",
    'running': 'Running',
    'failed': 'Failed'
}

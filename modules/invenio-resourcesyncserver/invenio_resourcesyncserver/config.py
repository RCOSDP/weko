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

INVENIO_CAPABILITY_URL = "{}resync/capability.xml"
"""Temp for capability url."""

INVENIO_SOURCE_DESC_URL = "{}resync/source.xml"
"""Temp for source description url."""

WEKO_RECORD_FIRST_VERSION = '1'
"""Record version of unver record."""

WEKO_RECORD_ORIGIN_VERSION = '0'
"""Record version of original record."""

WEKO_ROOT_INDEX = 0
"""Root index id."""

VALIDATE_MESSAGE = 'Selected repository has been registered already. ' \
    'Please select another repository.'
"""Validate message."""

# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018, 2019 CERN.
# Copyright (C) 2019 Esteban J. G. Gabancho
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""IIIF API for Invenio."""

IIIF_API_PREFIX = '/iiif/'
"""URL prefix to IIIF API."""

IIIF_API_SERVER = 'https://127.0.0.1:5000/'
"""IIIF Presentation API server"""

IIIF_UI_URL = '/api{}'.format(IIIF_API_PREFIX)
"""URL to IIIF API endpoint (allow hostname)."""

IIIF_PREVIEWER_PARAMS = {
    'size': '750,'
}
"""Parameters for IIIF image previewer extension."""

IIIF_PREVIEW_TEMPLATE = 'invenio_iiif/preview.html'
"""Template for IIIF image preview."""

IIIF_MANIFEST_ENDPOINTS = {
    "recid": {
        "pid_type": "recid",
        "route": "/records/<pid_value>",
    },

}
"""Default manifest endpoint."""

IIIF_API_DECORATOR_HANDLER = 'invenio_iiif.handlers:protect_api'
"""Image opener handler decorator."""

IIIF_IMAGE_OPENER_HANDLER = 'invenio_iiif.handlers:image_opener'
"""Image opener handler function."""

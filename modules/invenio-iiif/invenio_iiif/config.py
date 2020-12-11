# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""IIIF API for Invenio."""

IIIF_API_PREFIX = '/iiif/'
"""URL prefix to IIIF API."""

IIIF_UI_URL = '/api{}'.format(IIIF_API_PREFIX)
"""URL to IIIF API endpoint (allow hostname)."""

IIIF_PREVIEWER_PARAMS = {
    'size': '750,'
}
"""Parameters for IIIF image previewer extension."""

IIIF_PREVIEW_TEMPLATE = 'invenio_iiif/preview.html'
"""Template for IIIF image preview."""

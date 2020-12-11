# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""IIIF API for Invenio."""

from __future__ import absolute_import, print_function

from flask_iiif import IIIF
from flask_restful import Api

from . import config
from .handlers import image_opener, protect_api


class InvenioIIIF(object):
    """Invenio-IIIF extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        self.iiif_ext = IIIF(app=app)
        self.iiif_ext.api_decorator_handler(protect_api)
        self.iiif_ext.uuid_to_image_opener_handler(image_opener)
        app.extensions['invenio-iiif'] = self

    def init_config(self, app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith('IIIF_'):
                app.config.setdefault(k, getattr(config, k))


class InvenioIIIFAPI(InvenioIIIF):
    """Invenio-IIIF extension."""

    def init_app(self, app):
        """Flask application initialization."""
        super(InvenioIIIFAPI, self).init_app(app)
        api = Api(app=app)
        self.iiif_ext.init_restful(api, prefix=app.config['IIIF_API_PREFIX'])

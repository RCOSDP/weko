# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""IIIF API for Invenio."""

from flask_iiif import IIIF
from flask_restful import Api
from invenio_base.utils import obj_or_import_string

from . import config


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
        # register decorator if configured
        decorator_handler = app.config["IIIF_API_DECORATOR_HANDLER"]
        if decorator_handler:
            decorator_handler_func = obj_or_import_string(decorator_handler)
            self.iiif_ext.api_decorator_handler(decorator_handler_func)
        # register image opener handler
        image_opener = obj_or_import_string(
            app.config["IIIF_IMAGE_OPENER_HANDLER"])
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

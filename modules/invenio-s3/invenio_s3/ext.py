# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Esteban J. G. Gabancho.
#
# Invenio-S3 is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""S3 file storage support for Invenio."""

from __future__ import absolute_import, print_function

import boto3
from flask import current_app
from invenio_files_rest.models import Location
from werkzeug.utils import cached_property

from . import config


class InvenioS3(object):
    """Invenio-S3 extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    @cached_property
    def init_s3f3_info(self):
        """Gather all the information needed to start the S3FSFileSystem."""
        info = dict(
            key=current_app.config.get('S3_ACCCESS_KEY_ID', ''),
            secret=current_app.config.get('S3_SECRECT_ACCESS_KEY', ''),
            client_kwargs={},
        )
        s3_endpoint_url = current_app.config.get('S3_ENDPOINT_URL', None)
        if s3_endpoint_url:
            info['client_kwargs']['endpoint_url'] = s3_endpoint_url
        default_location = Location.query.filter_by(default=True).first()
        if default_location.type == 's3':
            if default_location.access_key != '':
                info['key'] = default_location.access_key
            if default_location.secret_key != '':
                info['secret'] = default_location.secret_key
            if default_location.s3_endpoint_url != '':
                info['client_kwargs']['endpoint_url'] = default_location.s3_endpoint_url
                
        return info

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions['invenio-s3'] = self

    def init_config(self, app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith('S3_'):
                app.config.setdefault(k, getattr(config, k))

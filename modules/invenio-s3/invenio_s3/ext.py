# -*- coding: utf-8 -*-
#
# Copyright (C) 2018, 2019 Esteban J. G. Gabancho.
#
# Invenio-S3 is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""S3 file storage support for Invenio."""

from __future__ import absolute_import, print_function

import warnings

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

    # @cached_property
    def init_s3fs_info(self, location):
        """Gather all the information needed to start the S3FSFileSystem."""
        if 'S3_ACCCESS_KEY_ID' in current_app.config:
            current_app.config['S3_ACCESS_KEY_ID'] = current_app.config[
                'S3_ACCCESS_KEY_ID']
            warnings.warn(
                'Key S3_ACCCESS_KEY_ID contained a typo and has been '
                'corrected to S3_ACCESS_KEY_ID, support for the '
                'flawed version will be removed.',
                DeprecationWarning
            )

        if 'S3_SECRECT_ACCESS_KEY' in current_app.config:
            current_app.config['S3_SECRET_ACCESS_KEY'] = current_app.config[
                'S3_SECRECT_ACCESS_KEY']
            warnings.warn(
                'Key S3_SECRECT_ACCESS_KEY contained a typo and has been '
                'corrected to S3_SECRET_ACCESS_KEY, support for the '
                'flawed version will be removed.',
                DeprecationWarning
            )

        info = dict(
            key=current_app.config.get('S3_ACCESS_KEY_ID', ''),
            secret=current_app.config.get('S3_SECRET_ACCESS_KEY', ''),
            client_kwargs={},
            config_kwargs={
                's3': {
                    'addressing_style': 'path',
                },
                'signature_version': current_app.config.get(
                    'S3_SIGNATURE_VERSION', 's3v4'
                ),
            },
        )

        s3_endpoint = current_app.config.get('S3_ENDPOINT_URL', None)
        if s3_endpoint:
            info['client_kwargs']['endpoint_url'] = s3_endpoint

        region_name = current_app.config.get('S3_REGION_NAME', None)
        if region_name:
            info['client_kwargs']['region_name'] = region_name

        if location.type == current_app.config.get('S3_LOCATION_TYPE_S3_PATH_VALUE') or \
            location.type == current_app.config.get('S3_LOCATION_TYPE_S3_VIRTUAL_HOST_VALUE'):
            info['key'] = location.access_key
            info['secret'] = location.secret_key
            info['client_kwargs']['endpoint_url'] = location.s3_endpoint_url
            region_name = location.s3_region_name
            if region_name:
                info['client_kwargs']['region_name'] = region_name
            info['config_kwargs']['signature_version'] = location.s3_signature_version

        print(info)

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

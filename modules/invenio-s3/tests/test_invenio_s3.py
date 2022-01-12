# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Esteban J. G. Gabancho.
#
# Invenio-S3 is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Module tests."""

from __future__ import absolute_import, print_function

from invenio_s3 import InvenioS3


def test_version():
    """Test version import."""
    from invenio_s3 import __version__
    assert __version__


def test_init(base_app, location):
    """Test extension initialization."""
    assert 'invenio-s3' in base_app.extensions

    with base_app.app_context():
        base_app.config['S3_ENDPOINT_URL'] = 'https://example.com:1234'
        s3_connection_info = base_app.extensions['invenio-s3'].init_s3f3_info
        assert s3_connection_info['client_kwargs'][
            'endpoint_url'] == 'https://example.com:1234'

# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Esteban J. G. Gabancho.
#
# Invenio-S3 is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Module tests."""

from __future__ import absolute_import, print_function

from invenio_files_rest.models import Location
from invenio_s3 import InvenioS3


def test_version():
    """Test version import."""
    from invenio_s3 import __version__
    assert __version__


# .tox/c1/bin/pytest --cov=invenio_s3 tests/test_invenio_s3.py::test_init -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-s3/.tox/c1/tmp
def test_init(base_app, location, database):
    """Test extension initialization."""
    assert 'invenio-s3' in base_app.extensions

    default_location = Location.query.filter_by(default=True).first()
    default_location.type = ''
    database.session.commit()

    with base_app.app_context():
        base_app.config['S3_ENDPOINT_URL'] = 'https://example.com:1234'
        s3_connection_info = base_app.extensions['invenio-s3'].init_s3f3_info
        assert s3_connection_info['client_kwargs'][
            'endpoint_url'] == 'https://example.com:1234'


def test_init2(location, database):
    """Test extension initialization."""
    default_location = Location.query.filter_by(default=True).first()
    default_location.type = 's3'
    default_location.access_key = 'accesskey'
    default_location.secret_key = 'secretkey'
    default_location.s3_endpoint_url = 'https://example.com:5678'
    database.session.commit()

    invenio_s3 = InvenioS3()
    s3_connection_info = invenio_s3.init_s3f3_info
    assert s3_connection_info['key'] == 'accesskey'
    assert s3_connection_info['secret'] == 'secretkey'
    assert s3_connection_info['client_kwargs'][
        'endpoint_url'] == 'https://example.com:5678'
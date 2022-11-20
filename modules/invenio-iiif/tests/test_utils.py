# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test of image opener."""

from __future__ import absolute_import, print_function

import pytest
from flask_iiif import iiif_image_url
from six.moves.urllib.parse import quote

from invenio_iiif.utils import iiif_image_key, ui_iiif_image_url


@pytest.fixture(scope='module')
def app_config(app_config):
    app_config.update({
        'IIIF_API_PREFIX': '/api/iiif/',
        'IIIF_UI_URL': '/api/iiif/',
    })
    return app_config


def test_iiif_image_key(image_object):
    """Test retrieval of image."""
    key = u'{}:{}:{}'.format(
        image_object.bucket_id,
        image_object.version_id,
        image_object.key,
    )
    assert key == iiif_image_key(image_object)
    assert key == iiif_image_key(dict(
        bucket=image_object.bucket_id,
        version_id=image_object.version_id,
        key=image_object.key,
    ))


def test_ui_iiif_image_url(appctx, image_object):
    """Test retrieval of image info."""
    assert iiif_image_url(uuid=iiif_image_key(image_object)).endswith(
        ui_iiif_image_url(image_object)
    )

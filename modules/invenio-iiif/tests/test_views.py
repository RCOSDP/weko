# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test of image opener."""

from __future__ import absolute_import, print_function

from flask import url_for
from flask_iiif.utils import iiif_image_url


def test_get_image(base_client, image_object, image_uuid):
    """Test retrieval of image."""
    res = base_client.get(iiif_image_url(uuid=image_uuid, size='200,200'))
    assert res.status_code == 200
    assert res.content_type == 'image/png'


def test_image_info(base_client, image_object, image_uuid):
    """Test retrieval of image info."""
    res = base_client.get(
        url_for('iiifimageinfo', version='v2', uuid=image_uuid))
    assert res.status_code == 200
    assert res.content_type == 'application/json'


def test_get_restricted_image(base_client, image_object, image_uuid):
    """Test retrieval of image."""
    image_url = iiif_image_url(uuid=image_uuid, size='200,200')
    # First request with deny (cache miss) fails
    assert base_client.get(
        image_url,
        headers={'Authorization': 'deny'}
    ).status_code == 404
    # First request with allow (cache miss) succeeds
    assert base_client.get(image_url).status_code == 200
    # Second request with deny (cache hit) also fails
    assert base_client.get(
        image_url,
        headers={'Authorization': 'deny'}
    ).status_code == 404


def test_get_restricted_image_info(base_client, image_object, image_uuid):
    """Test retrieval of image info."""
    info_url = url_for('iiifimageinfo', version='v2', uuid=image_uuid)
    # First request with deny (cache miss) fails
    assert base_client.get(
        info_url,
        headers={'Authorization': 'deny'}
    ).status_code == 404
    # First request with allow (cache miss) pass
    assert base_client.get(info_url).status_code == 200
    # Second request with deny (cache hit) fails
    assert base_client.get(
        info_url,
        headers={'Authorization': 'deny'}
    ).status_code == 404

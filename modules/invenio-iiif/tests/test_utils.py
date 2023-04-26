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

# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_utils.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp


@pytest.fixture(scope='module')
def app_config(app_config):
    app_config.update({
        'IIIF_API_PREFIX': '/api/iiif/',
        'IIIF_UI_URL': '/api/iiif/',
    })
    return app_config

# def iiif_image_key(obj):
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_utils.py::test_iiif_image_key -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
def test_iiif_image_key(image_object):
    """Test retrieval of image."""
    key = u'{}:{}:{}'.format(
        image_object.bucket_id,
        image_object.version_id,
        image_object.key,
    )
    #assert key == iiif_image_key(image_object)
    #assert key == iiif_image_key(dict(
    #    bucket=image_object.bucket_id,
    #    version_id=image_object.version_id,
    #    key=image_object.key,
    #))
    
    # obj = ObjectVersion
    result = iiif_image_key(image_object)
    assert result == key
    
    # obj != ObjectVersion
    data = {"bucket":image_object.bucket_id,"version_id":image_object.version_id,"key":image_object.key}
    result = iiif_image_key(data)
    assert result == key


#def ui_iiif_image_url(obj, version='v2', region='full', size='full',
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_utils.py::test_ui_iiif_image_url -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
def test_ui_iiif_image_url(app, image_object):
    """Test retrieval of image info."""
    version="v1"
    region="full"
    size="full"
    rotation=90
    quality="default"
    image_format="png"
    test = u"/api/iiif/v1/{}/full/full/90/default.png".format(quote(iiif_image_key(image_object).encode("utf8"),safe=":"))
    
    result = ui_iiif_image_url(image_object,version,region,size,rotation,quality,image_format)
    assert result == test


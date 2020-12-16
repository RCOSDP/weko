# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test of image opener."""

from __future__ import absolute_import, print_function

from invenio_iiif.previewer import can_preview, preview, previewable_extensions
from invenio_iiif.utils import ui_iiif_image_url


class MockPreviewFile(object):
    """Mock of a preview file object."""
    def __init__(self, obj, ext):
        self.file = obj
        self.ext = '.{}'.format(ext)

    def has_extensions(self, *exts):
        """Mock of testing if a file object has a specific extension."""
        return self.ext in exts


def test_previewable_extensions():
    """Test extension requirements."""
    assert previewable_extensions == ['jpg', 'jpeg', 'png', 'tif', 'tiff']


def test_can_preview():
    """Test can preview."""
    for e in previewable_extensions:
        assert can_preview(MockPreviewFile(None, e))
    assert not can_preview(MockPreviewFile(None, 'txt'))


def test_preview(image_object):
    """Test preview."""
    assert ui_iiif_image_url(image_object, size='750,', image_format='jpg') \
        in preview(MockPreviewFile(image_object, 'jpg'))
    assert ui_iiif_image_url(image_object, size='750,', image_format='png') \
        in preview(MockPreviewFile(image_object, 'png'))

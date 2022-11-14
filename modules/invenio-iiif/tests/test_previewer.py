# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test of image opener."""

from __future__ import absolute_import, print_function

from flask import make_response, current_app
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

#def preview(file):
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_previewer.py::test_can_preview -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
def test_can_preview():
    """Test can preview."""
    for e in previewable_extensions:
        assert can_preview(MockPreviewFile(None, e))
    assert not can_preview(MockPreviewFile(None, 'txt'))

#def preview(file):
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_previewer.py::test_preview -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
def test_preview(client,image_object,mocker):
    """Test preview."""
    url = "/api/iiif/v2/test.png/full/750,/0/default.jpg"
    mocker.patch("invenio_iiif.previewer.ui_iiif_image_url",return_value=url)
    mock_render = mocker.patch("invenio_iiif.previewer.render_template",return_value=make_response())
    file = MockPreviewFile(image_object,"jpg")
    result = preview(file)
    assert result.status_code == 200
    mock_render.assert_called_with(
        "invenio_iiif/preview.html",
        file=file,
        file_url=url
    )
    
    current_app.config.update(
        IIIF_PREVIEWER_PARAMS={
            'size': '750,',
            'image_format': 'jpg'
        }
    )
    mock_render = mocker.patch("invenio_iiif.previewer.render_template",return_value=make_response())
    file = MockPreviewFile(image_object,"jpg")
    result = preview(file)
    assert result.status_code == 200
    mock_render.assert_called_with(
        "invenio_iiif/preview.html",
        file=file,
        file_url=url
    )

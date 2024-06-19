# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""IIIF image previewer."""

from __future__ import absolute_import, print_function

from copy import deepcopy

from flask import Blueprint, current_app, render_template

from .utils import ui_iiif_image_url

previewable_extensions = ['jpg', 'jpeg', 'png', 'tif', 'tiff']

blueprint = Blueprint(
    'invenio_iiif',
    __name__,
    template_folder='templates',
)
"""Blueprint to allow loading of templates."""


def can_preview(file):
    """Determine if the given file can be previewed by its extension.

    :param file: The file to be previewed.
    :returns: Boolean
    """
    supported_extensions = ('.jpg', '.jpeg', '.png', '.tif', '.tiff')
    return file.has_extensions(*supported_extensions)


def preview(file):
    """Render appropriate template with embed flag.

    .. note::
        Any non .png image is treated as .jpg

    :param file: The file to be previewed.
    :returns: Template with the preview of the provided file.
    """
    params = deepcopy(current_app.config['IIIF_PREVIEWER_PARAMS'])
    if 'image_format' not in params:
        params['image_format'] = \
            'png' if file.has_extensions('.png') else 'jpg'
    return render_template(
        current_app.config['IIIF_PREVIEW_TEMPLATE'],
        file=file,
        file_url=ui_iiif_image_url(
            file.file,
            **params
        )
    )

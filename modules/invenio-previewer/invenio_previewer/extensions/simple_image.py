# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Previews simple image files."""

from flask import current_app, render_template

from ..proxies import current_previewer

previewable_extensions = ["jpg", "jpeg", "png", "gif"]


def validate(file):
    """Validate a simple image file."""
    max_file_size = current_app.config.get(
        "PREVIEWER_MAX_IMAGE_SIZE_BYTES", 0.5 * 1024 * 1024
    )
    return file.size <= max_file_size


def can_preview(file):
    """Determine if the given file can be previewed."""
    supported_extensions = (".jpg", ".jpeg", ".png", ".gif")
    return file.has_extensions(*supported_extensions) and validate(file)


def preview(file):
    """Render the appropriate template with embed flag."""
    return render_template(
        "invenio_previewer/simple_image.html",
        file=file,
        js_bundles=current_previewer.js_bundles,
        css_bundles=current_previewer.css_bundles + ["simple_image_css.css"],
    )

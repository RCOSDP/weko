# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Default rendering returning a default web page."""

from flask import render_template

from ..proxies import current_previewer

previewable_extensions = []


def can_preview(file):
    """Return if file type can be previewed."""
    return True


def preview(file):
    """Return the appropriate template and passes the file and embed flag."""
    return render_template(
        "invenio_previewer/default.html",
        file=file,
        js_bundles=current_previewer.js_bundles,
        css_bundles=current_previewer.css_bundles,
    )

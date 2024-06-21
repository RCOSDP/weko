# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""PDF previewer based on pdf.js."""

from flask import render_template

from ..proxies import current_previewer

previewable_extensions = ["pdf", "pdfa"]


def can_preview(file):
    """Check if file can be previewed."""
    return file.has_extensions(".pdf", ".pdfa")


def preview(file):
    """Preview file."""
    return render_template(
        "invenio_previewer/pdfjs.html",
        file=file,
        html_tags='dir="ltr" mozdisallowselectionprint moznomarginboxes',
        css_bundles=["pdfjs_css.css"],
        js_bundles=current_previewer.js_bundles + ["pdfjs_js.js", "fullscreen_js.js"],
    )

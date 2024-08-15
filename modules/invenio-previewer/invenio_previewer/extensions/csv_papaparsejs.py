# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Render a CSV file using Papaparse."""

from flask import current_app, render_template

from ..proxies import current_previewer

previewable_extensions = ["csv", "dsv"]


def can_preview(file):
    """Determine if the given file can be previewed."""
    return file.is_local() and file.has_extensions(".csv", ".dsv")


def preview(file):
    """Render the appropriate template with embed flag."""
    return render_template(
        "invenio_previewer/csv_bar.html",
        file=file,
        js_bundles=current_previewer.js_bundles + ["papaparse_csv.js"],
        css_bundles=current_previewer.css_bundles,
    )

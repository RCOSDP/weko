# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
# Copyright (C) 2021 Northwestern University.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Jupyter Notebook previewer."""

import os

import nbformat
from flask import current_app, render_template
from invenio_i18n import gettext as _
from nbconvert import HTMLExporter
from traitlets.config import Config

from ..proxies import current_previewer

previewable_extensions = ["ipynb"]

# relative paths to the extra CSS of the default `lab` theme
NBCONVERT_THEME_LAB_EXTRA_CSS = [
    os.path.join("nbconvert", "templates", "lab", "static", "index.css"),
    os.path.join("nbconvert", "templates", "lab", "static", "theme-light.css"),
]


def render(file):
    """Generate the result HTML."""
    with file.open() as fp:
        content = fp.read()
    try:
        notebook = nbformat.reads(content.decode("utf-8"), as_version=4)
    except nbformat.reader.NotJSONError:
        return _("Error: Not a ipynb/json file"), {}

    c = Config()
    c.HTMLExporter.preprocessors = ["nbconvert.preprocessors.sanitize.SanitizeHTML"]
    c.SanitizeHTML.tags = current_app.config.get("ALLOWED_HTML_TAGS", [])
    c.SanitizeHTML.attributes = current_app.config.get("ALLOWED_HTML_ATTRS", {})
    c.SanitizeHTML.strip = True
    html_exporter = HTMLExporter(config=c, embed_images=True)
    html_exporter.template_file = "base"
    body, resources = html_exporter.from_notebook_node(notebook)
    return body, resources


def can_preview(file):
    """Determine if file can be previewed."""
    return file.is_local() and file.has_extensions(".ipynb")


def preview(file):
    """Render the IPython Notebook."""
    body, resources = render(file)
    default_jupyter_nb_style = ""
    if "inlining" in resources:
        default_jupyter_nb_style += resources["inlining"]["css"][0]
    # the include_css func will load extra CSS from disk
    if "include_css" in resources:
        fn = resources["include_css"]
        for extra_css_path in NBCONVERT_THEME_LAB_EXTRA_CSS:
            default_jupyter_nb_style += fn(extra_css_path)
    return render_template(
        "invenio_previewer/ipynb.html",
        file=file,
        content=body,
        inline_style=default_jupyter_nb_style,
        js_bundles=current_previewer.js_bundles,
        css_bundles=current_previewer.css_bundles,
    )
